"""
engine_simulation_manager.py
─────────────────────────────
Background simulation runner for one engine.

Architecture
────────────
When an engine is created the app calls:
    start_engine_simulation(engine_db_id, json_path, model_type, supabase)

This spawns a daemon thread that:
  1. Loads all cycles from the engine's JSON file
  2. Loads the active .h5 model for the engine's model_type
  3. Reads one cycle row every TICK_INTERVAL seconds
  4. Preprocesses the row with a rolling window buffer
  5. Once the buffer is full (window_size cycles), runs model.predict()
  6. Writes the prediction to rul_predictions (Supabase)
  7. Updates engines.current_cycle in Supabase

The Dash overview page polls rul_predictions via dcc.Interval — it never
touches this thread directly.

Multiple engines run in parallel (each in their own thread). Threads are
tracked in _RUNNING_SIMULATIONS so we don't double-start the same engine.
"""

import json
import os
import threading
import time
import traceback
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

TICK_INTERVAL    = 3          # seconds between cycles
WINDOW_SIZE      = 45         # rolling window fed to the model (cycles)
RUL_CAP          = 100        # clamp predicted RUL to this upper bound

# Sensor columns the model was trained on (CMAPSS selected sensors)
SENSOR_COLS = [
    "s2", "s3", "s4", "s7", "s8", "s9",
    "s11", "s12", "s13", "s14", "s15",
    "s17", "s20", "s21",
]
OP_COLS = [
    "operational_setting_1",
    "operational_setting_2",
    "operational_setting_3",
]
FEATURE_COLS = OP_COLS + SENSOR_COLS  # 17 features total

# Path to shared model directory
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_MODELS_DIR = os.path.join(_BASE_DIR, "data", "shared_models")

# Active simulation threads: engine_db_id → threading.Thread
_RUNNING_SIMULATIONS: dict = {}
_LOCK = threading.Lock()


# ─────────────────────────────────────────────
#  MODEL LOADER  (cached per model_type)
# ─────────────────────────────────────────────

_MODEL_CACHE: dict = {}
_MODEL_LOCK  = threading.Lock()


def _load_model(model_type: str):
    """
    Load and cache the active .h5 model for the given model_type.
    Scans data/shared_models/<model_type>/ for the most recently modified .h5.
    Returns None if no model file is found or tensorflow is unavailable.
    """
    with _MODEL_LOCK:
        if model_type in _MODEL_CACHE:
            return _MODEL_CACHE[model_type]

        model_dir = os.path.join(SHARED_MODELS_DIR, model_type)
        if not os.path.isdir(model_dir):
            print(f"[SIM] No model directory for {model_type}: {model_dir}")
            return None

        h5_files = sorted(
            [f for f in os.listdir(model_dir) if f.endswith(".h5")],
            key=lambda f: os.path.getmtime(os.path.join(model_dir, f)),
            reverse=True,
        )
        if not h5_files:
            print(f"[SIM] No .h5 model found in {model_dir}")
            return None

        model_path = os.path.join(model_dir, h5_files[0])
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(model_path, compile=False)
            _MODEL_CACHE[model_type] = model
            print(f"[SIM] Loaded model: {model_path}")
            return model
        except Exception:
            print(f"[SIM][ERROR] Failed to load model {model_path}:\n{traceback.format_exc()}")
            return None


def reload_model(model_type: str):
    """
    Force-reload the model for model_type (call after a new model is deployed).
    """
    with _MODEL_LOCK:
        _MODEL_CACHE.pop(model_type, None)
    return _load_model(model_type)


# ─────────────────────────────────────────────
#  DATA LOADER
# ─────────────────────────────────────────────

def _load_cycles(json_path: str) -> list:
    """
    Load cycle rows from the engine JSON file.
    Supports two formats:
      - List of cycle dicts (the actual format used in the project)
      - Dict with a 'cycles' key
    Returns a list sorted by 'cycle' ascending.
    """
    if not os.path.exists(json_path):
        print(f"[SIM] JSON file not found: {json_path}")
        return []
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        if isinstance(data, list):
            cycles = data
        elif isinstance(data, dict):
            cycles = data.get("cycles", [])
        else:
            cycles = []

        cycles = sorted(cycles, key=lambda r: r.get("cycle", 0))
        print(f"[SIM] Loaded {len(cycles)} cycles from {json_path}")
        return cycles
    except Exception:
        print(f"[SIM][ERROR] Failed to load {json_path}:\n{traceback.format_exc()}")
        return []


# ─────────────────────────────────────────────
#  PREPROCESSING  (inline, no external deps)
# ─────────────────────────────────────────────

def _extract_features(row: dict) -> Optional[np.ndarray]:
    """
    Flatten one cycle row into a 1-D feature vector of shape (len(FEATURE_COLS),).
    The JSON stores sensors inside a nested 'sensors' dict; op settings are top-level.
    Returns None if any feature is missing.
    """
    sensors = row.get("sensors", {})
    vec = []
    for col in FEATURE_COLS:
        if col in row:
            vec.append(float(row[col]))
        elif col in sensors:
            vec.append(float(sensors[col]))
        else:
            return None  # missing feature — skip row
    return np.array(vec, dtype=np.float32)


class _WindowBuffer:
    """
    Accumulates feature vectors for one engine.
    Once len >= WINDOW_SIZE, returns the latest window as shape (1, WINDOW_SIZE, n_features).
    Also performs per-feature min-max normalisation based on the values seen so far.
    """

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.window_size = window_size
        self.buffer: list = []          # list of 1-D np.ndarray

    def push(self, vec: np.ndarray) -> Optional[np.ndarray]:
        self.buffer.append(vec)
        if len(self.buffer) < self.window_size:
            return None

        window = np.stack(self.buffer[-self.window_size:], axis=0)  # (W, F)

        # per-feature min-max normalisation using the full history seen
        history = np.stack(self.buffer, axis=0)  # (N, F)
        mn  = history.min(axis=0)
        mx  = history.max(axis=0)
        rng = mx - mn
        rng[rng == 0] = 1.0          # avoid /0 for constant features

        window = (window - mn) / rng  # (W, F)
        return window[np.newaxis, :, :]  # (1, W, F)


# ─────────────────────────────────────────────
#  CONDITION STATUS HELPER
# ─────────────────────────────────────────────

def _get_active_model_version_id(supabase, model_type: str) -> str | None:
    """Fetch the UUID of the currently active model version for a given model_type."""
    try:
        resp = supabase.table("model_versions") \
            .select("id") \
            .eq("model_type", model_type) \
            .eq("status", "active") \
            .limit(1) \
            .execute()
        if resp.data:
            return str(resp.data[0]["id"])
    except Exception:
        print(f"[SIM][WARN] Could not fetch model_version_id for {model_type}:\n{traceback.format_exc()}")
    return None


# ─────────────────────────────────────────────
#  CONDITION STATUS HELPER
# ─────────────────────────────────────────────

def _rul_to_status(predicted_rul: float, warn_thresh: float = 62, crit_thresh: float = 30) -> str:
    if predicted_rul <= crit_thresh:
        return "critical"
    if predicted_rul <= warn_thresh:
        return "warning"
    return "healthy"


# ─────────────────────────────────────────────
#  SIMULATION THREAD
# ─────────────────────────────────────────────

def _simulation_loop(
    engine_db_id: str,
    json_path: str,
    model_type: str,
    supabase,
    stop_event: threading.Event,
):
    """
    Main loop for a single engine simulation.
    Runs in a background daemon thread.
    """
    print(f"[SIM] Starting simulation for engine {engine_db_id} | type={model_type} | file={json_path}")

    cycles = _load_cycles(json_path)
    if not cycles:
        print(f"[SIM] No cycle data for engine {engine_db_id} — simulation aborted.")
        return

    model = _load_model(model_type)
    buffer = _WindowBuffer(window_size=WINDOW_SIZE)
    _no_model_warned = False  # log "waiting for model" only once

    # Fetch active model_version_id once (re-check if model gets reloaded later)
    model_version_id = _get_active_model_version_id(supabase, model_type)

    for idx, row in enumerate(cycles):
        if stop_event.is_set():
            print(f"[SIM] Simulation stopped for engine {engine_db_id}")
            break

        cycle_num = row.get("cycle", idx + 1)
        true_rul  = row.get("true_rul", None)

        # ── Extract features ──
        vec = _extract_features(row)
        if vec is None:
            print(f"[SIM][WARN] Skipping cycle {cycle_num} — missing features")
            time.sleep(TICK_INTERVAL)
            continue

        # ── Push into window buffer ──
        X = buffer.push(vec)

        # ── Update current_cycle in engines table ──
        try:
            supabase.table("engines") \
                .update({"current_cycle": cycle_num}) \
                .eq("id", engine_db_id) \
                .execute()
        except Exception:
            print(f"[SIM][ERROR] Failed to update current_cycle:\n{traceback.format_exc()}")

        # ── Predict once window is full ──
        if X is not None:
            if model is not None:
                try:
                    pred_raw = model.predict(X, verbose=0)
                    pred_rul = float(np.squeeze(pred_raw))
                    pred_rul = max(0.0, min(float(RUL_CAP), pred_rul))
                except Exception:
                    print(f"[SIM][ERROR] model.predict failed at cycle {cycle_num}:\n{traceback.format_exc()}")
                    pred_rul = None
            else:
                pred_rul = None
                if not _no_model_warned:
                    print(f"[SIM][INFO] engine={engine_db_id} — window ready, waiting for model upload")
                    _no_model_warned = True

            if pred_rul is not None:
                new_status = _rul_to_status(pred_rul)
                fault_mode = (
                    "critical_degradation" if new_status == "critical" else
                    "moderate_degradation" if new_status == "warning" else
                    None
                )
                try:
                    row_data = {
                        "engine_id":     engine_db_id,
                        "cycle":         int(cycle_num),
                        "predicted_rul": round(pred_rul, 2),
                        "predicted_at":  datetime.now(timezone.utc).isoformat(),
                    }
                    if fault_mode:
                        row_data["fault_mode"] = fault_mode
                    if model_version_id:
                        row_data["model_version_id"] = model_version_id

                    supabase.table("rul_predictions").insert(row_data).execute()

                    supabase.table("engines") \
                        .update({"condition_status": new_status}) \
                        .eq("id", engine_db_id) \
                        .execute()

                    print(
                        f"[SIM] engine={engine_db_id} cycle={cycle_num} "
                        f"pred_rul={pred_rul:.1f} status={new_status}"
                    )
                except Exception:
                    print(f"[SIM][ERROR] Insert/update failed at cycle {cycle_num}:\n{traceback.format_exc()}")

        time.sleep(TICK_INTERVAL)

    print(f"[SIM] Simulation complete for engine {engine_db_id} (all cycles processed)")

    # Clean up registry
    with _LOCK:
        _RUNNING_SIMULATIONS.pop(engine_db_id, None)


# ─────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────

def start_engine_simulation(
    engine_db_id: str,
    json_path: str,
    model_type: str,
    supabase,
) -> bool:
    """
    Spawn a background daemon thread for this engine.
    Returns True if a new thread was started, False if one was already running.
    """
    with _LOCK:
        if engine_db_id in _RUNNING_SIMULATIONS:
            t = _RUNNING_SIMULATIONS[engine_db_id]
            if t["thread"].is_alive():
                print(f"[SIM] Simulation already running for engine {engine_db_id}")
                return False
            # Thread finished — allow restart
            del _RUNNING_SIMULATIONS[engine_db_id]

        stop_event = threading.Event()
        thread = threading.Thread(
            target=_simulation_loop,
            args=(engine_db_id, json_path, model_type, supabase, stop_event),
            daemon=True,
            name=f"sim-{engine_db_id}",
        )
        _RUNNING_SIMULATIONS[engine_db_id] = {"thread": thread, "stop": stop_event}
        thread.start()
        print(f"[SIM] Spawned simulation thread for engine {engine_db_id}")
        return True


def stop_engine_simulation(engine_db_id: str):
    """Signal the simulation thread for this engine to stop gracefully."""
    with _LOCK:
        entry = _RUNNING_SIMULATIONS.get(engine_db_id)
    if entry:
        entry["stop"].set()
        print(f"[SIM] Stop signal sent to engine {engine_db_id}")


def is_running(engine_db_id: str) -> bool:
    with _LOCK:
        entry = _RUNNING_SIMULATIONS.get(engine_db_id)
    return entry is not None and entry["thread"].is_alive()


def active_simulations() -> list:
    with _LOCK:
        return [eid for eid, e in _RUNNING_SIMULATIONS.items() if e["thread"].is_alive()]


def resume_all_simulations(supabase):
    """
    Called once at app startup. Fetches every engine from Supabase that has a
    JSON data file on disk and starts a simulation thread for it if one isn't
    already running.
    """
    import json as _json
    from data_utils import BASE_DATA_DIR

    try:
        resp = supabase.table("engines") \
            .select("id, engine_id, model_type, organization_id") \
            .execute()
        engines = resp.data or []
    except Exception:
        print(f"[SIM][ERROR] resume_all_simulations — failed to fetch engines:\n{traceback.format_exc()}")
        return

    # Build a set of valid UUIDs so we only start threads for engines that exist
    valid_ids = {str(eng.get("id")) for eng in engines if eng.get("id")}

    for eng in engines:
        engine_db_id = str(eng.get("id", ""))
        engine_id    = eng.get("engine_id", 0)
        model_type   = eng.get("model_type", "FD001")
        org_id       = str(eng.get("organization_id") or "")

        if not engine_db_id or engine_db_id not in valid_ids:
            continue

        # Resolve the JSON path by scanning data/ for the matching org folder
        json_path = None
        if os.path.isdir(BASE_DATA_DIR):
            for folder in os.listdir(BASE_DATA_DIR):
                if org_id and org_id in folder:
                    candidate = os.path.join(
                        BASE_DATA_DIR, folder,
                        f"engine_{str(engine_id).zfill(3)}.json"
                    )
                    if os.path.exists(candidate):
                        json_path = candidate
                        break

        if not json_path:
            print(f"[SIM] No data file found for engine {engine_db_id} — skipping resume")
            continue

        # Check the file actually has cycle data
        try:
            with open(json_path, encoding="utf-8") as f:
                d = _json.load(f)
            has_cycles = (isinstance(d, list) and len(d) > 0) or \
                         (isinstance(d, dict) and len(d.get("cycles", [])) > 0)
        except Exception:
            has_cycles = False

        if not has_cycles:
            print(f"[SIM] Data file empty for engine {engine_db_id} — skipping resume")
            continue

        start_engine_simulation(
            engine_db_id=engine_db_id,
            json_path=json_path,
            model_type=model_type,
            supabase=supabase,
        )
