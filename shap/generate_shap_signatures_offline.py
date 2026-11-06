"""Generate auditable GradientExplainer reference signatures from C-MAPSS TRAIN data.

Run --help for options. No database access; existing signatures are never overwritten.
Uses the local true_shap_analysis model loader and engine_simulation_manager window
preprocessor. Outputs raw-model-output attributions (before RUL clipping/bias).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("FD001", "FD002", "FD003", "FD004")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fold_features(values, width):
    """Sum time and raw/mean/std blocks, retaining operational settings for QA."""
    import numpy as np
    values = np.asarray(values)
    if values.ndim != 3 or values.shape[2] != 3 * width:
        raise ValueError(f"Unexpected attribution shape {values.shape}; expected (N,W,{3*width})")
    return values.reshape(values.shape[0], values.shape[1], 3, width).sum(axis=(1, 2))


def summarize(sensor_values, names):
    import numpy as np
    values = np.asarray(sensor_values, dtype=float)
    if values.ndim != 2 or values.shape[1] != len(names) or not len(values):
        raise ValueError("Expected a nonempty sample-by-sensor matrix")
    if not np.isfinite(values).all():
        raise ValueError("Non-finite SHAP values")
    magnitudes = np.abs(values)
    means, stds = magnitudes.mean(axis=0), magnitudes.std(axis=0)
    order = np.argsort(-means, kind="stable")
    ranks = {names[int(i)]: rank + 1 for rank, i in enumerate(order)}
    return {
        "mean_abs_shap": dict(zip(names, map(float, means))),
        "std_abs_shap": dict(zip(names, map(float, stds))),
        "sensor_ranks": ranks,
        "n_samples": len(values),
    }


def explain_checked(explainer, x, predictions, baseline, width, *, nsamples, max_nsamples, seed, atol, rtol):
    """Retry only failed windows at increasing budgets, never relax tolerances."""
    import numpy as np
    folded = np.zeros((len(x), width), dtype=float)
    used = np.zeros(len(x), dtype=int)
    residual = np.full(len(x), np.inf)
    tolerance = atol + rtol * np.maximum(np.abs(predictions), abs(baseline))
    pending = np.arange(len(x))
    budget = nsamples
    history = []
    while len(pending):
        values = explainer.shap_values(x[pending.tolist()], nsamples=budget, rseed=seed)
        if isinstance(values, list):
            if len(values) != 1:
                raise ValueError("Expected one RUL model output")
            values = values[0]
        values = np.asarray(values)
        if values.ndim == 4 and values.shape[-1] == 1:
            values = values[..., 0]
        expected = (len(pending), *tuple(x.shape[1:]))
        if values.shape != expected or not np.isfinite(values).all():
            raise ValueError(f"Invalid SHAP result: {values.shape} vs {expected}")
        folded[pending] = fold_features(values, width)
        used[pending] = budget
        residual[pending] = predictions[pending] - baseline - folded[pending].sum(axis=1)
        history.append({"nsamples": budget, "window_indices": pending.tolist(),
                        "residuals": residual[pending].tolist()})
        pending = np.flatnonzero(np.abs(residual) > tolerance)
        if not len(pending) or budget >= max_nsamples:
            break
        budget = min(budget * 4, max_nsamples)
        print(f"  Retrying {len(pending)} window(s) with nsamples={budget}", flush=True)
    return folded, residual, used, history


def collect_reference(args, dataset, model_path, allowed_ids):
    import h5py
    import numpy as np
    from true_shap_analysis import load_model_from_path
    from engine_simulation_manager import _WindowBuffer, SENSOR_COLS

    source = args.data_dir / f"train_{dataset}.txt"
    data = np.loadtxt(source)
    if data.ndim != 2 or data.shape[1] != 26 or not np.isfinite(data).all():
        raise ValueError(f"{source}: expected finite C-MAPSS rows with 26 columns")
    available = sorted(set(data[:, 0].astype(int)))
    selected = available if allowed_ids is None else sorted(set(allowed_ids))
    if not selected or set(selected) - set(available):
        raise ValueError(f"{dataset}: empty or unknown engine IDs in manifest")
    if args.max_engines:
        selected = selected[:args.max_engines]

    with h5py.File(model_path, "r") as f:
        total_features = int(f["metadata"].attrs["num_features"])
        if total_features not in (42, 51):
            raise ValueError(f"Expected 42 or 51 engineered model features, got {total_features}")
        width = total_features // 3
        if int(f["metadata"].attrs.get("rolling_window", 5)) != 5:
            raise ValueError("Saved rolling window differs from the reused preprocessor")
        has_global = "scaler/mean" in f and "scaler/std" in f
        has_cluster = all(k in f for k in ("cluster/centroids", "cluster/means", "cluster/stds"))
    if width not in (14, 17):
        raise ValueError(f"Unsupported base-feature count: {width}")
    if not (has_global or has_cluster):
        raise ValueError("Model has no saved normalization parameters; refusing adaptive scaling")
    model, mean, std, centroids, cluster_mean, cluster_std, window = load_model_from_path(str(model_path))
    sensor_indices = [4 + int(s[1:]) for s in SENSOR_COLS]
    columns = sensor_indices + ([2, 3, 4] if width == 17 else [])
    windows, records, skipped = [], [], []
    for engine_id in selected:
        rows = data[data[:, 0] == engine_id]
        rows = rows[np.argsort(rows[:, 1])]
        if not np.array_equal(rows[:, 1], np.arange(1, len(rows) + 1)):
            raise ValueError(f"{dataset} engine {engine_id}: cycles must be contiguous from 1")
        eligible = np.arange(window - 1, len(rows))
        if args.phase == "degraded":
            eligible = eligible[(len(rows) - rows[eligible, 1]) <= args.rul_threshold]
        if not len(eligible):
            skipped.append(int(engine_id))
            continue
        indices = eligible[np.linspace(0, len(eligible) - 1,
                                      min(args.windows_per_engine, len(eligible)), dtype=int)]
        raw = rows[:, columns].astype(np.float32)
        for index in indices:
            buffer = _WindowBuffer(window_size=window, scaler_mean=mean, scaler_std=std,
                                   num_features=width, kmeans_centroids=centroids,
                                   cluster_means=cluster_mean, cluster_stds=cluster_std)
            # Identical accumulated history to sequential push(), but preprocess only
            # selected windows instead of recomputing every earlier cycle.
            buffer.buffer = list(raw[:index])
            x = buffer.push(raw[index])
            if x is None or not np.isfinite(x).all():
                raise ValueError(f"Invalid window for {dataset}/{engine_id}/{index+1}")
            windows.append(x[0])
            records.append({"engine_id": int(engine_id), "cycle": int(rows[index, 1]),
                            "true_rul": int(len(rows) - rows[index, 1])})
    if not windows:
        raise ValueError(f"No eligible training windows for {dataset}")
    return model, np.stack(windows), records, width, source, selected, skipped


def generate_dataset(args, dataset, allowed_ids):
    import numpy as np
    import torch
    import shap
    from engine_simulation_manager import SENSOR_SHORT

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    model_path = args.model_dir / f"transformer_bigru_{dataset}.h5"
    model, pool, records, width, source, selected, skipped = collect_reference(args, dataset, model_path, allowed_ids)
    rng = np.random.default_rng(args.seed)
    permutation = rng.permutation(len(pool))
    background_records = []
    # background = np.zeros_like(pool[:1])
    # candidates = permutation
    if args.background == "zero":
        background = np.zeros_like(pool[:1])
        candidates = permutation
    else:
        if len(pool) <= args.background_size:
            raise ValueError("Not enough windows for disjoint background and foreground")
        bg_ids = permutation[:args.background_size]
        background = pool[bg_ids]
        background_records = [records[int(i)] for i in bg_ids]
        candidates = permutation[args.background_size:]
    foreground_ids = candidates[:args.max_samples] if args.max_samples else candidates
    foreground = pool[foreground_ids]
    foreground_records = [records[int(i)] for i in foreground_ids]
    model.eval()
    bg_tensor = torch.from_numpy(background)
    with torch.no_grad():
        baseline = float(model(bg_tensor).mean().item())
    explainer = shap.GradientExplainer(model, bg_tensor)
    folded_batches, predictions, residuals, sample_budgets, retry_history = [], [], [], [], []
    for start in range(0, len(foreground), args.batch_size):
        x = torch.from_numpy(foreground[start:start + args.batch_size])
        with torch.no_grad():
            pred = model(x).numpy().reshape(-1)
        if len(pred) != len(x) or not np.isfinite(pred).all():
            raise ValueError("Expected one finite prediction per window")
        folded, errors, used, history = explain_checked(explainer, x, pred, baseline, width, nsamples=args.nsamples,
            max_nsamples=args.max_nsamples, seed=args.seed + start, atol=args.check_atol, rtol=args.check_rtol)
        residuals.extend(errors.tolist())
        sample_budgets.extend(used.tolist())
        retry_history.append({"batch_start": start, "attempts": history})
        predictions.extend(pred.tolist())
        folded_batches.append(folded)
        print(f"{dataset}: explained {min(start+args.batch_size,len(foreground))}/{len(foreground)}", flush=True)
    folded = np.concatenate(folded_batches)
    residual = np.asarray(residuals)
    tolerance = args.check_atol + args.check_rtol * np.maximum(np.abs(predictions), abs(baseline))
    passed = bool(np.all(np.abs(residual) <= tolerance))
    if not passed:
        diagnostic_path = args.output.with_name(args.output.stem + f".{dataset}.failure.json")
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        with diagnostic_path.open("w", encoding="utf-8") as f:
            json.dump({"dataset": dataset, "model_sha256": sha256(model_path), "baseline_prediction": baseline, "windows": foreground_records,
                       "predictions": predictions, "residuals": residuals, "tolerances": tolerance.tolist(), "nsamples_per_window": sample_budgets,
                       "retry_history": retry_history}, f, indent=2, allow_nan=False)
        raise ValueError(f"{dataset}: SHAP reconstruction failed: max error={np.abs(residual).max():.4f}."f"Failed windows retried up to {args.max_nsamples} samples."
                         f"Diagnostics saved to {diagnostic_path}; no signature written.")
    result = summarize(folded[:, :14], SENSOR_SHORT)
    result.update({
        "rul_threshold": args.rul_threshold if args.phase == "degraded" else None,
        "fault_mode": "HPC Degradation" if dataset in ("FD001", "FD002") else "HPC + Fan Degradation",
        "condition_group": "single" if dataset in ("FD001", "FD003") else "multi",
        "provenance": {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "method": "shap.GradientExplainer / Expected Gradients", "shap_version": shap.__version__,
            "torch_version": torch.__version__, "numpy_version": np.__version__,
            "split": "train", "source_file": str(source.resolve()), "source_sha256": sha256(source),
            "model_file": str(model_path.resolve()), "model_sha256": sha256(model_path),
            "code_sha256": {name: sha256(Path(__file__).parent / name) for name in
                              (Path(__file__).name, "true_shap_analysis.py", "engine_simulation_manager.py")},
            "selected_engine_ids": list(map(int, selected)), "skipped_engine_ids": skipped,
            "foreground_windows": foreground_records, "background_windows": background_records,
            "background": args.background, "background_size": len(background),
            "phase": args.phase, "phase_selection": "true RUL from training trajectory end",
            "output_space": "raw model output, before bias correction and clipping",
            "aggregation": "sum time and raw/rolling-mean/rolling-std contributions; first 14 sensors",
            "weighting": "equal weight per selected foreground window; population std (ddof=0)",
            "seed": args.seed, "nsamples": args.nsamples, "max_nsamples": args.max_nsamples,
            "nsamples_per_window": sample_budgets, "window_size": int(pool.shape[1]),
            "base_feature_count": width, "windows_per_engine_cap": args.windows_per_engine,
            "candidate_windows": len(pool), "max_samples": args.max_samples,
            "baseline_prediction": baseline,
            "reconstruction": {"passed": passed, "mean_absolute_error": float(np.abs(residual).mean()),
                               "max_absolute_error": float(np.abs(residual).max()),
                               "atol": args.check_atol, "rtol": args.check_rtol,
                               "includes_operational_settings": True},
        },
    })
    audit = {"windows": foreground_records, "predictions": predictions,
             "baseline_prediction": baseline, "sensor_shap": folded[:, :14].tolist(),
             "operational_setting_shap": folded[:, 14:].tolist(), "residuals": residuals,
             "nsamples_per_window": sample_budgets, "retry_history": retry_history}
    return result, audit


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datasets", nargs="+", choices=DATASETS, default=list(DATASETS))
    p.add_argument("--data-dir", type=Path, default=ROOT / "0. NASA_CMAPS")
    p.add_argument("--model-dir", type=Path, default=Path(__file__).parent)
    p.add_argument("--output", type=Path, default=ROOT / "simulation_preparation/verified_signatures/shap_signatures_full_life.json")
    p.add_argument("--engine-manifest", type=Path, help='Optional JSON mapping each dataset to TRAIN engine IDs, e.g. {"FD001": [1,2]}')
    p.add_argument("--phase", choices=("degraded", "all"), default="all",
                   help="Explain windows from all eligible life stages (default), or only degraded-stage windows")
    p.add_argument("--rul-threshold", type=float, default=62.0, help="TRUE training RUL cutoff; not predicted RUL")
    p.add_argument("--background", choices=("zero", "sampled"), default="zero",
                   help="zero matches the monitoring code's default; sampled uses disjoint reference windows")
    p.add_argument("--background-size", type=int, default=50)
    p.add_argument("--windows-per-engine", type=int, default=10)
    p.add_argument("--max-samples", type=int, default=400, help="Foreground cap; 0 uses all candidate windows")
    p.add_argument("--max-engines", type=int, default=0, help="Smoke-test cap; 0 selects all reference engines")
    p.add_argument("--nsamples", type=int, default=200)
    p.add_argument("--max-nsamples", type=int, default=12800,
                   help="Retry failing windows with 4x samples up to this cap")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--check-atol", type=float, default=5.0, help="Reconstruction absolute tolerance in raw RUL units")
    p.add_argument("--check-rtol", type=float, default=0.05)
    args = p.parse_args()
    if args.max_nsamples < args.nsamples:
        p.error("--max-nsamples must be at least --nsamples")
    for key in ("background_size", "windows_per_engine", "nsamples", "batch_size"):
        if getattr(args, key) < 1:
            p.error(f"--{key.replace('_','-')} must be positive")
    for key in ("max_samples", "max_engines", "rul_threshold", "check_atol", "check_rtol"):
        if getattr(args, key) < 0:
            p.error(f"--{key.replace('_','-')} cannot be negative")
    return args


def main():
    args = parse_args()
    audit_path = args.output.with_suffix(".audit.json")
    if args.output.exists() or audit_path.exists():
        raise SystemExit("Output or audit file exists. Choose a new --output path.")
    manifest = json.loads(args.engine_manifest.read_text()) if args.engine_manifest else None
    signatures, audits = {}, {}
    for dataset in dict.fromkeys(args.datasets):
        if manifest is not None and dataset not in manifest:
            raise ValueError(f"Manifest must explicitly list reference engines for {dataset}")
        signatures[dataset], audits[dataset] = generate_dataset(
            args, dataset, None if manifest is None else manifest[dataset])
    # Only save after every requested dataset passes numerical checks.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("x", encoding="utf-8") as f:
        json.dump(audits, f, indent=2, allow_nan=False)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(signatures, f, indent=2, allow_nan=False)
    print(f"Saved signatures: {args.output.resolve()}\nSaved audit: {audit_path.resolve()}")


if __name__ == "__main__":
    main()
