"""
generate_shap_signatures.py
────────────────────────────
One-time (or post-retraining) script that builds the reference SHAP importance
signatures used by the degradation pattern matching pipeline.

For each C-MAPSS dataset (FD001–FD004), it:
  1. Fetches all rul_predictions rows for engines of that model_type where
     predicted_rul ≤ warn_threshold  (the "degraded phase").
  2. Parses the stored shap_values JSON per row.
  3. Computes mean |SHAP| and std |SHAP| over all degraded-phase samples.
  4. Writes the result to  data/shap_signatures.json.

The inference code (engine_simulation_manager.py) loads that JSON file at
startup.  Re-run this script after every model retrain so the signatures
stay in sync.

Usage
─────
    python generate_shap_signatures.py

Requires SUPABASE_URL and SUPABASE_KEY to be set in the environment (or .env).
"""

import json
import os
import sys
from pathlib import Path

import numpy as np

# ── Load .env if present ──────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Sensor ordering must match SENSOR_SHORT in engine_simulation_manager.py ──
SENSORS = [
    "T24", "T30", "T50", "P30", "Nf",  "Nc",
    "Ps30", "phi", "NRf", "NRc", "BPR", "htBleed", "W31", "W32",
]

# Fault-mode label per dataset
FAULT_MODE = {
    "FD001": "HPC Degradation",
    "FD002": "HPC Degradation",
    "FD003": "HPC + Fan Degradation",
    "FD004": "HPC + Fan Degradation",
}

# Comparison group: single-condition vs. multi-condition
CONDITION_GROUP = {
    "FD001": "single",
    "FD002": "multi",
    "FD003": "single",
    "FD004": "multi",
}

OUTPUT_PATH = Path(__file__).parent / "data" / "shap_signatures.json"
MIN_SAMPLES = 10   # warn if fewer degraded-phase rows are found


def _vec_from_shap(parsed: list[dict]) -> np.ndarray | None:
    """Convert a shap_data list to a 14-dim numpy vector (|score| per sensor)."""
    if not parsed:
        return None
    shap_map = {d["sensor"]: abs(d["score"]) for d in parsed if "sensor" in d and "score" in d}
    if not shap_map:
        return None
    return np.array([shap_map.get(s, 0.0) for s in SENSORS], dtype=np.float64)


def generate_signatures(supabase_url: str, supabase_key: str,
                        warn_threshold: float = 62.0,
                        output_path: Path = OUTPUT_PATH) -> dict:
    """
    Build and save SHAP importance signatures for all four datasets.

    Parameters
    ----------
    supabase_url   : Supabase project URL
    supabase_key   : Supabase service-role key
    warn_threshold : RUL value below which a prediction is counted as degraded-phase
    output_path    : Where to write the JSON signature file

    Returns
    -------
    signatures dict (same structure as what is written to disk)
    """
    from supabase import create_client
    sb = create_client(supabase_url, supabase_key)

    signatures: dict = {}

    for dataset in ("FD001", "FD002", "FD003", "FD004"):
        print(f"\n[SIG] Processing {dataset}...")

        # ── Step 1: find all engine IDs for this dataset ──────────────────────
        eng_resp = sb.table("engines") \
            .select("id") \
            .eq("model_type", dataset) \
            .execute()
        engine_ids = [r["id"] for r in (eng_resp.data or [])]
        if not engine_ids:
            print(f"[SIG][WARN] No engines found for {dataset} — skipping.")
            continue

        # ── Step 2: fetch degraded-phase predictions (batch, 1 000 rows max) ──
        # Supabase default page size is 1 000; paginate if needed.
        all_rows: list = []
        offset = 0
        PAGE = 1000
        while True:
            resp = (
                sb.table("rul_predictions")
                  .select("shap_values, predicted_rul")
                  .in_("engine_id", engine_ids)
                  .lte("predicted_rul", warn_threshold)
                  .range(offset, offset + PAGE - 1)
                  .execute()
            )
            batch = resp.data or []
            all_rows.extend(batch)
            if len(batch) < PAGE:
                break
            offset += PAGE

        print(f"[SIG] {dataset}: {len(all_rows)} degraded-phase rows fetched "
              f"(predicted_rul ≤ {warn_threshold})")

        # ── Step 3: parse SHAP vectors ────────────────────────────────────────
        shap_vecs: list[np.ndarray] = []
        skipped = 0
        for row in all_rows:
            sv = row.get("shap_values")
            if not sv:
                skipped += 1
                continue
            try:
                parsed = json.loads(sv) if isinstance(sv, str) else sv
            except Exception:
                skipped += 1
                continue
            vec = _vec_from_shap(parsed)
            if vec is not None:
                shap_vecs.append(vec)
            else:
                skipped += 1

        if skipped:
            print(f"[SIG][WARN] {dataset}: {skipped} rows skipped (missing/malformed shap_values)")

        if len(shap_vecs) < MIN_SAMPLES:
            print(f"[SIG][WARN] {dataset}: only {len(shap_vecs)} valid samples "
                  f"(need ≥ {MIN_SAMPLES}). Signature may be unreliable.")
            if not shap_vecs:
                print(f"[SIG][WARN] {dataset}: no samples — skipping this dataset.")
                continue

        # ── Step 4: compute statistics ────────────────────────────────────────
        arr = np.stack(shap_vecs)          # (N, 14)
        mean_vec = arr.mean(axis=0)        # (14,)
        std_vec  = arr.std(axis=0)         # (14,)

        # Build readable sensor ranking (1 = most important)
        rank_order = np.argsort(-mean_vec)
        sensor_ranks = {SENSORS[i]: int(np.where(rank_order == i)[0][0]) + 1
                        for i in range(len(SENSORS))}

        signatures[dataset] = {
            "mean_abs_shap":  {s: round(float(mean_vec[i]),  6) for i, s in enumerate(SENSORS)},
            "std_abs_shap":   {s: round(float(std_vec[i]),   6) for i, s in enumerate(SENSORS)},
            "sensor_ranks":   sensor_ranks,
            "n_samples":      len(shap_vecs),
            "rul_threshold":  warn_threshold,
            "fault_mode":     FAULT_MODE[dataset],
            "condition_group": CONDITION_GROUP[dataset],
        }

        print(f"[SIG] {dataset} signature built from {len(shap_vecs)} samples.")
        print(f"      Top 5 sensors: "
              + ", ".join(SENSORS[i] for i in rank_order[:5]))

    if not signatures:
        print("[SIG][ERROR] No signatures generated. Check that rul_predictions "
              "contains rows with shap_values.")
        return {}

    # ── Step 5: write to disk ─────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(signatures, f, indent=2)
    print(f"\n[SIG] Signatures written to {output_path}")
    print(f"      Datasets included: {list(signatures.keys())}")

    return signatures


# ─────────────────────────────────────────────────────────────────────────────
#  CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        print("[SIG][ERROR] SUPABASE_URL and SUPABASE_KEY must be set in the environment.")
        sys.exit(1)

    # Optional: override warn_threshold via CLI arg
    thresh = float(sys.argv[1]) if len(sys.argv) > 1 else 62.0

    generate_signatures(url, key, warn_threshold=thresh)
