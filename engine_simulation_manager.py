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
from pathlib import Path
import threading
import time
import traceback
from datetime import datetime, timezone
from typing import Callable, Optional

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

TICK_INTERVAL    = 3          # seconds between cycles
RUL_CAP          = 100        # clamp predicted RUL — matches training rul_cap in model metadata

# Per-dataset window sizes (must match training)
WINDOW_SIZES = {
    "FD001": 45,
    "FD002": 35,
    "FD003": 45,
    "FD004": 35,
}
WINDOW_SIZE = 45  # default fallback

# Per-dataset: whether to include operational setting columns as features
# FD001/FD003: single operating condition → 14 sensors only
# FD002/FD004: multiple operating conditions → 14 sensors + 3 OS = 17 features
INCLUDE_OS = {
    "FD001": False,
    "FD002": True,
    "FD003": False,
    "FD004": True,
}

# Number of KMeans clusters for per-cluster normalization
N_CLUSTERS = {
    "FD001": 1,
    "FD002": 6,
    "FD003": 1,
    "FD004": 6,
}

# Sensor columns the model was trained on (CMAPSS selected sensors)
SENSOR_COLS = [
    "s2", "s3", "s4", "s7", "s8", "s9",
    "s11", "s12", "s13", "s14", "s15",
    "s17", "s20", "s21",
]
# Operational setting columns (used for FD002/FD004)
OP_COLS = [
    "operational_setting_1",
    "operational_setting_2",
    "operational_setting_3",
]
FEATURE_COLS = SENSOR_COLS          # 14 sensor features only (FD001/FD003)
BASE_FEATURE_COLS = FEATURE_COLS    # alias used by _extract_raw_sensors

# Path to shared model directory (local dev) or temp cache (deployment)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCAL_MODELS_DIR = os.path.join(_BASE_DIR, "data", "shared_models")
if os.path.isdir(_LOCAL_MODELS_DIR):
    SHARED_MODELS_DIR = _LOCAL_MODELS_DIR
else:
    import tempfile as _tf
    SHARED_MODELS_DIR = os.path.join(_tf.gettempdir(), "pdm_cache", "models")
    os.makedirs(SHARED_MODELS_DIR, exist_ok=True)

# Active simulation threads: engine_db_id → threading.Thread
_RUNNING_SIMULATIONS: dict = {}
_LOCK = threading.Lock()

# Ring buffer of raw sensor rows per engine — read by sensor_trends.py
# { engine_db_id: deque of row dicts (max 500 rows) }
from collections import deque
_SENSOR_BUFFER: dict = {}
_SENSOR_LOCK   = threading.Lock()
SENSOR_BUFFER_MAX = 500   # keep last 500 cycles per engine


# ─────────────────────────────────────────────
#  SUPABASE RETRY HELPER
# ─────────────────────────────────────────────

def _supabase_execute(build_query: Callable, retries: int = 3, base_delay: float = 2.0):
    """
    Execute a Supabase query with retry on transient network errors.

    ``build_query`` is a zero-argument callable that builds *and* executes the
    query (i.e. it must call .execute() internally and return the response).

    Retries on httpx.ReadError / httpcore.ReadError (WinError 10035 and similar
    transient socket failures that are common on Windows with HTTP/2).
    Other exceptions are re-raised immediately.
    """
    # Import lazily so the module loads even if httpx/httpcore aren't installed yet
    try:
        import httpx
        import httpcore
        _transient_exc = (httpx.ReadError, httpx.ConnectError, httpcore.ReadError, httpcore.ConnectError)
    except ImportError:
        _transient_exc = (OSError,)

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return build_query()
        except _transient_exc as exc:
            last_exc = exc
            delay = base_delay * attempt
            print(f"[SIM][WARN] Transient network error (attempt {attempt}/{retries}), "
                  f"retrying in {delay:.0f}s — {type(exc).__name__}: {exc}")
            time.sleep(delay)
        except Exception:
            raise  # non-transient errors bubble up immediately

    # All retries exhausted
    raise last_exc  # type: ignore[misc]


def get_sensor_history(engine_db_id: str) -> list:
    """Return a list of raw row dicts for the given engine (oldest first)."""
    with _SENSOR_LOCK:
        buf = _SENSOR_BUFFER.get(engine_db_id)
        return list(buf) if buf else []


def _push_sensor_row(engine_db_id: str, row: dict):
    with _SENSOR_LOCK:
        if engine_db_id not in _SENSOR_BUFFER:
            _SENSOR_BUFFER[engine_db_id] = deque(maxlen=SENSOR_BUFFER_MAX)
        _SENSOR_BUFFER[engine_db_id].append(row)


# ─────────────────────────────────────────────
#  MODEL ARCHITECTURE  (Transformer-BiGRU)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  MODEL ARCHITECTURE  (exact copy of train.py SBiTransformer)
# ─────────────────────────────────────────────

def _load_state_dict_from_h5(path: str) -> dict:
    """Read a flat PyTorch state-dict stored in an HDF5 file under 'weights/'."""
    import h5py
    import torch
    state_dict = {}
    with h5py.File(path, "r") as f:
        weights_grp = f["weights"]
        def _visit(name, obj):
            if isinstance(obj, h5py.Dataset):
                state_dict[name] = torch.tensor(obj[()])
        weights_grp.visititems(_visit)
    return state_dict


def _build_model(num_features: int, d_model: int, num_heads: int, num_layers: int,
                 ff_dim: int, hidden_dim_gru: int, dropout: float,
                 window_attn: int, seq_len: int):
    """
    Build the SBiTransformer architecture exactly as defined in train.py.
    Returns an nn.Module with a .predict(X) convenience method.
    """
    import torch
    import torch.nn as nn

    class LocalSparseAttention(nn.Module):
        def __init__(self):
            super().__init__()
            self.window_size = window_attn
            self.mha = nn.MultiheadAttention(d_model, num_heads, batch_first=True)

        def _local_mask(self, seq_len, device):
            mask = torch.full((seq_len, seq_len), float('-inf'), device=device)
            for i in range(seq_len):
                s = max(0, i - self.window_size)
                e = min(seq_len, i + self.window_size + 1)
                mask[i, s:e] = 0.0
            return mask

        def forward(self, x):
            mask = self._local_mask(x.size(1), x.device)
            out, _ = self.mha(x, x, x, attn_mask=mask)
            return out

    class EncoderLayer(nn.Module):
        def __init__(self):
            super().__init__()
            self.global_attn       = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
            self.norm1             = nn.LayerNorm(d_model)
            self.local_sparse_attn = LocalSparseAttention()
            self.norm2             = nn.LayerNorm(d_model)
            self.ffn1 = nn.Sequential(
                nn.Linear(d_model, ff_dim), nn.ReLU(),
                nn.Dropout(dropout), nn.Linear(ff_dim, d_model),
            )
            self.ffn2 = nn.Sequential(
                nn.Linear(d_model, ff_dim), nn.ReLU(),
                nn.Dropout(dropout), nn.Linear(ff_dim, d_model),
            )
            self.norm3   = nn.LayerNorm(d_model)
            self.dropout = nn.Dropout(dropout)

        def forward(self, x):
            a1, _ = self.global_attn(x, x, x)
            x = self.norm1(x + self.dropout(a1))
            a2 = self.local_sparse_attn(x)
            x = self.norm2(x + self.dropout(a2))
            f1 = self.ffn1(x)
            f2 = self.ffn2(x + self.dropout(f1))
            return self.norm3(x + self.dropout(f2))

    class SBiTransformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.input_projection = nn.Linear(num_features, d_model)
            self.pos_embedding    = nn.Parameter(torch.randn(1, seq_len, d_model))
            self.encoder_layers   = nn.ModuleList([EncoderLayer() for _ in range(num_layers)])
            self.bigru = nn.GRU(
                d_model, hidden_dim_gru,
                num_layers=1, batch_first=True, bidirectional=True,
            )
            self.regressor = nn.Sequential(
                nn.Linear(hidden_dim_gru * 2, 64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, 1),
            )

        def forward(self, src):
            x = self.input_projection(src) + self.pos_embedding
            for layer in self.encoder_layers:
                x = layer(x)
            gru_out, _ = self.bigru(x)
            return self.regressor(gru_out[:, -1, :])

        def predict(self, X: np.ndarray, verbose=0) -> np.ndarray:
            with torch.no_grad():
                out = self(torch.tensor(X, dtype=torch.float32))
            return out.numpy()

    return SBiTransformer()


# ─────────────────────────────────────────────
#  MODEL LOADER  (cached per model_type)
# ─────────────────────────────────────────────

_MODEL_CACHE:  dict = {}
_SCALER_CACHE: dict = {}   # model_type → (mean: np.ndarray | None, std: np.ndarray | None)
_CLUSTER_CACHE: dict = {}  # model_type → (centroids, cluster_means, cluster_stds) | (None, None, None)
_BIAS_CACHE: dict = {}     # model_type → float (bias_shift from training)
_MODEL_LOCK  = threading.Lock()


def _load_model(model_type: str, supabase=None):
    """
    Load and cache the active model for the given model_type.
    First checks the model_versions table for the active version's stored_filename.
    Falls back to the most recently modified .h5 in the model directory.
    If no local files exist, downloads from Supabase Storage.
    Returns None if no model file is found or loading fails.
    """
    with _MODEL_LOCK:
        if model_type in _MODEL_CACHE:
            return _MODEL_CACHE[model_type]

        model_dir = os.path.join(SHARED_MODELS_DIR, model_type)
        os.makedirs(model_dir, exist_ok=True)

        # Try to find the active model file from database
        model_path = None
        active_filename = None
        if supabase:
            try:
                resp = supabase.table("model_versions") \
                    .select("id, filename") \
                    .eq("model_type", model_type) \
                    .eq("status", "active") \
                    .limit(1) \
                    .execute()
                if resp.data:
                    row = resp.data[0]
                    active_filename = row.get("filename")
                    if active_filename:
                        candidate = os.path.join(model_dir, active_filename)
                        if os.path.exists(candidate):
                            model_path = candidate
                            print(f"[SIM] Using active model from DB: {active_filename}")
            except Exception:
                pass

        # Fallback: most recently modified .h5 on local disk
        if not model_path:
            h5_files = sorted(
                [f for f in os.listdir(model_dir) if f.endswith(".h5")],
                key=lambda f: os.path.getmtime(os.path.join(model_dir, f)),
                reverse=True,
            )
            if h5_files:
                model_path = os.path.join(model_dir, h5_files[0])
                print(f"[SIM] Using most recent model file: {h5_files[0]}")

        # Fallback: download from Supabase Storage
        if not model_path:
            try:
                from storage_utils import download_model_file, list_model_files
                # Try active filename first, then any available file
                fname_to_try = active_filename or None
                if fname_to_try:
                    model_path = download_model_file(model_type, fname_to_try, model_dir)
                if not model_path:
                    available = list_model_files(model_type)
                    for fname in reversed(available):  # most recent last
                        model_path = download_model_file(model_type, fname, model_dir)
                        if model_path:
                            break
            except Exception as e:
                print(f"[SIM] Storage download failed: {e}")

        if not model_path:
            print(f"[SIM] No .h5 model found for {model_type}")
            return None

        try:
            import h5py
            import torch
            import torch.nn as nn

            # ── Read metadata ──
            with h5py.File(model_path, "r") as f:
                meta        = f["metadata"]
                num_features    = int(meta.attrs.get("num_features",    14))
                d_model         = int(meta.attrs.get("d_model",         32))
                num_heads       = int(meta.attrs.get("num_heads",        2))
                num_layers      = int(meta.attrs.get("num_layers",       2))
                ff_dim          = int(meta.attrs.get("ff_dim",          128))
                hidden_dim_gru  = int(meta.attrs.get("hidden_dim_gru",  32))
                dropout         = float(meta.attrs.get("dropout",        0.3))
                window_size_meta= int(meta.attrs.get("window_size",      45))

                # ── Read scaler stats if saved ──
                scaler_mean = None
                scaler_std  = None
                if "scaler" in f:
                    scaler_mean = f["scaler/mean"][()].astype(np.float32)
                    scaler_std  = f["scaler/std"][()].astype(np.float32)
                    print(f"[SIM] Loaded scaler stats from {model_path}")

                # ── Read cluster artifacts if saved (FD002/FD004) ──
                kmeans_centroids = None
                cluster_means = None
                cluster_stds = None
                if "cluster" in f:
                    cl = f["cluster"]
                    if "centroids" in cl:
                        kmeans_centroids = cl["centroids"][()].astype(np.float32)
                    if "means" in cl:
                        cluster_means = cl["means"][()].astype(np.float32)
                    if "stds" in cl:
                        cluster_stds = cl["stds"][()].astype(np.float32)
                    print(f"[SIM] Loaded cluster normalization: "
                          f"{kmeans_centroids.shape[0]} clusters from {model_path}")

            # ── Build model architecture (exact train.py SBiTransformer) ──
            model = _build_model(
                num_features   = num_features,
                d_model        = d_model,
                num_heads      = num_heads,
                num_layers     = num_layers,
                ff_dim         = ff_dim,
                hidden_dim_gru = hidden_dim_gru,
                dropout        = dropout,
                window_attn    = int(meta.attrs.get("window_attn", 5)),
                seq_len        = window_size_meta,
            )

            # ── Load weights with strict=True to catch any mismatch ──
            try:
                state_dict = _load_state_dict_from_h5(model_path)
                print(f"[SIM] Loaded state_dict keys: {len(state_dict)} | model params: {len(list(model.state_dict().keys()))}")
                model.load_state_dict(state_dict, strict=True)
            except Exception as _load_err:
                print(f"[SIM][ERROR] load_state_dict failed: {type(_load_err).__name__}: {_load_err}")
                # Try with strict=False as fallback
                try:
                    model.load_state_dict(state_dict, strict=False)
                    print(f"[SIM][WARN] Loaded model with strict=False (some keys may be missing)")
                except Exception as _load_err2:
                    print(f"[SIM][ERROR] Even strict=False failed: {_load_err2}")
                    return None
            model.eval()

            _MODEL_CACHE[model_type] = model
            print(f"[SIM] Loaded PyTorch model: {model_path} "
                  f"(features={num_features}, window={window_size_meta})")

            # Cache scaler stats alongside the model (None if not in h5)
            _SCALER_CACHE[model_type] = (scaler_mean, scaler_std)
            # Cache cluster normalization info
            _CLUSTER_CACHE[model_type] = (kmeans_centroids, cluster_means, cluster_stds)
            # Cache bias shift (for test-time correction)
            with h5py.File(model_path, "r") as _f:
                _bias_shift = float(_f["metadata"].attrs.get("bias_shift", 0.0))
            _BIAS_CACHE[model_type] = _bias_shift
            if _bias_shift != 0:
                print(f"[SIM] Bias shift for {model_type}: {_bias_shift}")

            return model

        except Exception:
            print(f"[SIM][ERROR] Failed to load model {model_path}:\n{traceback.format_exc()}")
            return None


def reload_model(model_type: str, supabase=None):
    """
    Force-reload the model for model_type (call after a new model is deployed).
    """
    with _MODEL_LOCK:
        _MODEL_CACHE.pop(model_type, None)
        _SCALER_CACHE.pop(model_type, None)
        _CLUSTER_CACHE.pop(model_type, None)
    return _load_model(model_type, supabase=supabase)


# ─────────────────────────────────────────────
#  DATA LOADER
# ─────────────────────────────────────────────

def _load_cycles(json_path: str) -> list:
    """
    Load cycle rows from the engine JSON file.
    If the file doesn't exist locally, attempts to download from Supabase Storage.
    Supports two formats:
      - List of cycle dicts (the actual format used in the project)
      - Dict with a 'cycles' key
    Returns a list sorted by 'cycle' ascending.
    """
    # If file doesn't exist locally, try downloading from storage
    if not os.path.exists(json_path):
        try:
            from storage_utils import download_engine_json
            # Derive storage path from local path
            # e.g. "data/engines/FD004/engine_test_42.json" → "FD004/engine_test_42.json"
            # or "data/abc_sdn.../engine_xxx.json" → "orgs/abc_sdn.../engine_xxx.json"
            parts = Path(json_path).parts
            if "engines" in parts:
                idx = parts.index("engines")
                storage_path = "/".join(parts[idx + 1:])
            else:
                # Organization folder: data/<org_folder>/engine_xxx.json
                data_idx = None
                for i, p in enumerate(parts):
                    if p == "data":
                        data_idx = i
                        break
                if data_idx is not None and data_idx + 1 < len(parts):
                    storage_path = "orgs/" + "/".join(parts[data_idx + 1:])
                else:
                    storage_path = parts[-1]

            downloaded = download_engine_json(storage_path, local_fallback=json_path)
            if downloaded:
                json_path = downloaded
            else:
                print(f"[SIM] JSON file not found locally or in storage: {json_path}")
                return []
        except Exception as e:
            print(f"[SIM] JSON file not found: {json_path} (storage fallback failed: {e})")
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
#  PREPROCESSING
# ─────────────────────────────────────────────

def _extract_raw_sensors(row: dict, include_os: bool = False) -> Optional[np.ndarray]:
    """
    Extract sensor values from one row dict.
    If include_os=True (FD002/FD004), also extracts 3 operational settings → 17 features.
    Otherwise returns 14 sensor features only (FD001/FD003).
    Returns None if any required value is missing.
    """
    sensors = row.get("sensors", {})
    vec = []
    for col in SENSOR_COLS:
        if col in sensors:
            vec.append(float(sensors[col]))
        elif col in row:
            vec.append(float(row[col]))
        else:
            return None

    if include_os:
        for col in OP_COLS:
            if col in sensors:
                vec.append(float(sensors[col]))
            elif col in row:
                vec.append(float(row[col]))
            else:
                # OS columns might be at top level of the row dict
                vec.append(0.0)  # default if missing

    return np.array(vec, dtype=np.float32)  # shape (14,) or (17,)


class _WindowBuffer:
    """
    Accumulates raw sensor vectors (14-D for FD001/FD003, 17-D for FD002/FD004).
    Once >= window_size rows are buffered, produces the model input tensor:

      FD001/FD003: (1, W, 42) → [z_raw(14) | roll_mean(14) | roll_std(14)]
      FD002/FD004: (1, W, 51) → [z_raw(17) | roll_mean(17) | roll_std(17)]

    Pipeline:
      1. Z-score using scaler stats (global for FD001/FD003, per-cluster for FD002/FD004)
      2. Compute rolling mean and std (window=5)
      3. Concatenate [z_raw | roll_mean | roll_std]

    For FD002/FD004 with per-cluster normalization:
      - Uses KMeans centroids to assign the current OS reading to a cluster
      - Applies the cluster-specific scaler stats
    """
    ROLLING = 5

    def __init__(self, window_size: int = WINDOW_SIZE,
                 scaler_mean: Optional[np.ndarray] = None,
                 scaler_std:  Optional[np.ndarray] = None,
                 num_features: int = 14,
                 kmeans_centroids: Optional[np.ndarray] = None,
                 cluster_means: Optional[np.ndarray] = None,
                 cluster_stds: Optional[np.ndarray] = None):
        self.window_size = window_size
        self.num_features = num_features
        self.buffer: list = []

        # Global scaler
        if scaler_mean is not None and scaler_std is not None:
            self._mean = scaler_mean.astype(np.float32)
            _std = scaler_std.astype(np.float32).copy()
            _std[_std == 0] = 1.0
            self._std = _std
        else:
            self._mean = np.zeros(num_features, dtype=np.float32)
            self._std  = np.ones(num_features, dtype=np.float32)

        # Per-cluster normalization (FD002/FD004)
        self._centroids = kmeans_centroids
        self._cl_means = cluster_means
        self._cl_stds = cluster_stds
        self._use_cluster = (kmeans_centroids is not None and
                             cluster_means is not None and
                             cluster_stds is not None)

    def _assign_cluster(self, os_values: np.ndarray) -> int:
        """Assign OS values to nearest KMeans centroid."""
        dists = np.linalg.norm(self._centroids - os_values, axis=1)
        return int(np.argmin(dists))

    def push(self, vec: np.ndarray) -> Optional[np.ndarray]:
        """vec: shape (n_features,) → returns (1, W, n_features*3) or None if buffer not full."""
        self.buffer.append(vec)
        if len(self.buffer) < self.window_size:
            return None

        history = np.stack(self.buffer, axis=0)  # (N, n_features)

        # ── Step 1: z-score the full history ──
        if self._use_cluster:
            # Per-cluster normalization: OS columns are the last 3 features
            hist_z = np.zeros_like(history)
            for t in range(len(history)):
                os_vals = history[t, -3:]  # last 3 cols = OS
                cid = self._assign_cluster(os_vals)
                c_mean = self._cl_means[cid]
                c_std = self._cl_stds[cid].copy()
                c_std[c_std == 0] = 1.0
                hist_z[t] = (history[t] - c_mean) / c_std
        elif np.all(self._mean == 0) and np.all(self._std == 1):
            # No saved scaler — use all accumulated data for normalization
            adapt_mean = history.mean(axis=0)
            adapt_std = history.std(axis=0)
            adapt_std[adapt_std == 0] = 1.0
            hist_z = (history - adapt_mean) / adapt_std
        else:
            hist_z = (history - self._mean) / self._std  # (N, n_features)

        # ── Step 2: extract the current window ──
        win_z = hist_z[-self.window_size:]  # (W, n_features)

        # ── Step 3: rolling mean/std WITHIN the window only (matches training) ──
        roll_mean = np.zeros_like(win_z)
        roll_std  = np.zeros_like(win_z)
        for t in range(self.window_size):
            start = max(0, t - self.ROLLING + 1)
            chunk = win_z[start : t + 1]  # only look within the window
            roll_mean[t] = chunk.mean(axis=0)
            roll_std[t]  = chunk.std(axis=0) if len(chunk) > 1 else 0.0

        # ── Step 4: concatenate → (W, n_features*3) ──
        features = np.concatenate([win_z, roll_mean, roll_std], axis=1)

        return features[np.newaxis, :, :]  # (1, W, n_features*3)


# ─────────────────────────────────────────────
#  FEATURE IMPORTANCE (gradient-based attribution)
# ─────────────────────────────────────────────

# Human-readable labels for the 14 CMAPSS sensors, in SENSOR_COLS order:
#   s2, s3, s4, s7, s8, s9, s11, s12, s13, s14, s15, s17, s20, s21
# Reference: CMAPSS dataset sensor table (S-number → symbol mapping)
SENSOR_LABELS = [
    "T24 (LPC outlet temp)",       # s2  = S2  → T24
    "T30 (HPC outlet temp)",       # s3  = S3  → T30
    "T50 (LPT outlet temp)",       # s4  = S4  → T50
    "P30 (HPC outlet pres)",       # s7  = S7  → P30
    "Nf (Fan speed)",              # s8  = S8  → Nf
    "Nc (Core speed)",             # s9  = S9  → Nc
    "Ps30 (HPC static pres)",      # s11 = S11 → Ps30
    "phi (Fuel flow / Ps30)",      # s12 = S12 → phi
    "NRf (Corrected fan spd)",     # s13 = S13 → NRf
    "NRc (Corrected core spd)",    # s14 = S14 → NRc
    "BPR (Bypass ratio)",          # s15 = S15 → BPR
    "htBleed (Bleed enthalpy)",    # s17 = S17 → htBleed
    "W31 (HPT coolant bleed)",     # s20 = S20 → W31
    "W32 (LPT coolant bleed)",     # s21 = S21 → W32
]
# Short display names — used in SHAP chart y-axis labels
SENSOR_SHORT = [
    "T24",      # s2
    "T30",      # s3
    "T50",      # s4
    "P30",      # s7
    "Nf",       # s8
    "Nc",       # s9
    "Ps30",     # s11
    "phi",      # s12
    "NRf",      # s13
    "NRc",      # s14
    "BPR",      # s15
    "htBleed",  # s17
    "W31",      # s20
    "W32",      # s21
]


def _compute_feature_importance(model, X: np.ndarray) -> list[dict]:
    """
    Compute per-sensor importance scores using input × gradient attribution.

    X: numpy array shape (1, W, 42) — the same tensor fed to model.predict()
       Features are ordered [raw(14) | roll_mean(14) | roll_std(14)]

    Returns a list of dicts sorted by |score| descending:
        [{"sensor": "T30", "score": -0.38}, ...]

    Only the raw sensor block (first 14 columns) is attributed — rolling
    features carry the same signal so aggregating the raw block is sufficient
    and avoids triple-counting.
    """
    try:
        import torch

        t = torch.tensor(X, dtype=torch.float32, requires_grad=True)
        output = model(t)           # calls SBiTransformer.forward() directly
        output.backward()           # backprop to get dOutput/dInput

        # grad shape: (1, W, 42) — take mean over time axis, raw block only
        grad = t.grad.detach().numpy()[0]   # (W, 42)
        raw_grad = grad[:, :14]             # (W, 14)

        # Input × gradient attribution (mean over time window)
        inp_raw = X[0, :, :14]             # (W, 14)
        attr = (inp_raw * raw_grad).mean(axis=0)   # (14,)

        # Normalise so the largest absolute value = 1
        max_abs = np.abs(attr).max()
        if max_abs > 0:
            attr = attr / max_abs

        result = [
            {"sensor": SENSOR_SHORT[i], "score": round(float(attr[i]), 4)}
            for i in range(14)
        ]
        # Sort by absolute contribution descending
        result.sort(key=lambda x: abs(x["score"]), reverse=True)
        return result

    except Exception:
        print(f"[SIM][WARN] SHAP attribution failed: {traceback.format_exc(limit=2)}")
        return []

# How often (in simulation cycles) each thread re-fetches thresholds from
# Supabase so that changes saved on the Alert Thresholds page take effect
# without restarting running simulations.
THRESHOLD_REFRESH_CYCLES = 10

# ─────────────────────────────────────────────
#  DEGRADATION TYPE DETECTION (Rule-based + SHAP)
# ─────────────────────────────────────────────

# Sensor groups for fault isolation
_HPC_SENSORS = {"T30", "P30", "phi", "Ps30", "htBleed", "T24"}
_FAN_SENSORS = {"Nf", "NRf", "BPR", "Nc", "NRc"}


def _detect_degradation_type(model_type: str, shap_data: list, pred_rul: float,
                              warn_thresh: float) -> str | None:
    """
    Determine degradation fault mode using SHAP-based confidence scoring.

    Logic:
    - For each candidate fault mode, compute a confidence score based on how
      well the SHAP sign pattern matches the expected sensor signature.
    - Report the fault mode with the highest confidence, as long as it exceeds
      a minimum confidence threshold (30%).
    - This allows early degradation detection BEFORE RUL drops to warning level.

    FD001/FD003 → only HPC degradation possible (check HPC confidence)
    FD002/FD004 → HPC, Fan, or both; pick whichever has highest confidence

    Returns: "HPC Degradation", "Fan Degradation", "HPC + Fan Degradation", or None
    """
    if not shap_data:
        # No SHAP data yet — can't determine fault mode
        return None

    MIN_CONFIDENCE = 0.30  # minimum confidence to report a fault mode

    # Expected SHAP sign patterns per fault mode (negative = drives RUL down)
    hpc_expected = {"T30": -1, "P30": -1, "phi": -1, "Ps30": -1, "htBleed": -1, "T24": -1}
    fan_expected = {"Nf": -1, "NRf": -1, "BPR": -1, "Nc": -1, "NRc": -1}

    def _compute_confidence(expected_signs: dict) -> float:
        """Compute confidence for a given fault signature against current SHAP data."""
        shap_map = {s["sensor"]: s["score"] for s in shap_data}
        weighted_matches = 0.0
        total_weight = 0.0
        for sensor, expected_sign in expected_signs.items():
            score = shap_map.get(sensor, 0.0)
            magnitude = abs(score)
            total_weight += magnitude
            if magnitude > 0.01:
                actual_sign = -1 if score < 0 else 1
                if actual_sign == expected_sign:
                    weighted_matches += magnitude
        if total_weight == 0:
            return 0.0
        return weighted_matches / total_weight

    if model_type in ("FD001", "FD003"):
        # Only HPC fault possible — check confidence
        hpc_conf = _compute_confidence(hpc_expected)
        if hpc_conf >= MIN_CONFIDENCE:
            return "HPC Degradation"
        return None

    if model_type in ("FD002", "FD004"):
        # Both fault modes possible — compute confidence for each
        hpc_conf = _compute_confidence(hpc_expected)
        fan_conf = _compute_confidence(fan_expected)
        combined_expected = {**hpc_expected, **fan_expected}
        combined_conf = _compute_confidence(combined_expected)

        # Pick the highest confidence mode
        best_conf = max(hpc_conf, fan_conf, combined_conf)
        if best_conf < MIN_CONFIDENCE:
            return None

        if combined_conf >= hpc_conf and combined_conf >= fan_conf and hpc_conf >= 0.25 and fan_conf >= 0.25:
            return "HPC + Fan Degradation"
        elif hpc_conf >= fan_conf:
            return "HPC Degradation"
        else:
            return "Fan Degradation"

    return None

def _fetch_thresholds(supabase) -> tuple[float, float]:
    """
    Return (warn_thresh, crit_thresh) from the alert_thresholds table.
    Falls back to hardcoded defaults if the table is unavailable.
    """
    try:
        resp = _supabase_execute(
            lambda: supabase.table("alert_thresholds")
                .select("warning_threshold, critical_threshold")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
        )
        if resp.data:
            warn = float(resp.data[0].get("warning_threshold", 62))
            crit = float(resp.data[0].get("critical_threshold", 30))
            return warn, crit
    except Exception:
        print(f"[SIM][WARN] Could not fetch alert_thresholds, using defaults: {traceback.format_exc(limit=2)}")
    return 62.0, 30.0


# ─────────────────────────────────────────────
#  MODEL VERSION HELPER
# ─────────────────────────────────────────────

def _get_active_model_version_id(supabase, model_type: str) -> str | None:
    """Fetch the UUID of the currently active model version for a given model_type."""
    try:
        resp = _supabase_execute(
            lambda: supabase.table("model_versions")
                .select("id")
                .eq("model_type", model_type)
                .eq("status", "active")
                .limit(1)
                .execute()
        )
        if resp.data:
            return str(resp.data[0]["id"])
    except Exception:
        print(f"[SIM][WARN] Could not fetch model_version_id for {model_type}: {traceback.format_exc(limit=2)}")
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

    model = _load_model(model_type, supabase=supabase)
    scaler_mean, scaler_std = _SCALER_CACHE.get(model_type, (None, None))
    km_centroids, cl_means, cl_stds = _CLUSTER_CACHE.get(model_type, (None, None, None))
    _include_os = INCLUDE_OS.get(model_type, False)
    _num_features = 17 if _include_os else 14
    _win_size = WINDOW_SIZES.get(model_type, WINDOW_SIZE)
    buffer = _WindowBuffer(window_size=_win_size,
                           scaler_mean=scaler_mean,
                           scaler_std=scaler_std,
                           num_features=_num_features,
                           kmeans_centroids=km_centroids,
                           cluster_means=cl_means,
                           cluster_stds=cl_stds)
    _no_model_warned = False  # log "waiting for model" only once

    # Fetch active model_version_id once (re-check if model gets reloaded later)
    model_version_id = _get_active_model_version_id(supabase, model_type)

    # Fetch thresholds from alert_thresholds table; refreshed every THRESHOLD_REFRESH_CYCLES
    warn_thresh, crit_thresh = _fetch_thresholds(supabase)
    print(f"[SIM] engine={engine_db_id} thresholds: warn={warn_thresh} crit={crit_thresh}")

    # ── Resume from last saved cycle (skip already-processed cycles) ──────────
    resume_from_cycle = 0
    try:
        eng_resp = supabase.table("engines") \
            .select("current_cycle") \
            .eq("id", engine_db_id) \
            .single() \
            .execute()
        if eng_resp.data and eng_resp.data.get("current_cycle"):
            resume_from_cycle = int(eng_resp.data["current_cycle"])
            print(f"[SIM] engine={engine_db_id} resuming from cycle {resume_from_cycle}")
    except Exception:
        pass  # start from the beginning if we can't read the saved cycle

    # Fast-forward: replay raw sensor rows silently up to resume_from_cycle
    # so the window buffer has valid history for prediction.
    # No sleep, no Supabase writes — pure buffer warm-up.
    if resume_from_cycle > 0:
        for row in cycles:
            cycle_num = row.get("cycle", 0)
            if cycle_num > resume_from_cycle:
                break
            vec = _extract_raw_sensors(row, include_os=_include_os)
            if vec is not None:
                _push_sensor_row(engine_db_id, row)
                buffer.push(vec)
        print(f"[SIM] engine={engine_db_id} buffer warmed up to cycle {resume_from_cycle}")

    # ── EMA smoothing removed — raw predictions are now accurate after rolling stats fix ──

    for idx, row in enumerate(cycles):
        cycle_num = row.get("cycle", idx + 1)

        # Skip cycles already processed before this restart
        if cycle_num <= resume_from_cycle:
            continue

        if stop_event.is_set():
            print(f"[SIM] Simulation stopped for engine {engine_db_id}")
            break

        true_rul = row.get("true_rul", None)

        # ── Periodically refresh thresholds so admin changes take effect live ──
        if idx % THRESHOLD_REFRESH_CYCLES == 0 and idx > 0:
            new_warn, new_crit = _fetch_thresholds(supabase)
            if (new_warn, new_crit) != (warn_thresh, crit_thresh):
                warn_thresh, crit_thresh = new_warn, new_crit
                print(f"[SIM] engine={engine_db_id} thresholds updated: warn={warn_thresh} crit={crit_thresh}")

        # ── Extract features ──
        vec = _extract_raw_sensors(row, include_os=_include_os)
        if vec is None:
            print(f"[SIM][WARN] Skipping cycle {cycle_num} — missing features")
            time.sleep(TICK_INTERVAL)
            continue

        # ── Push raw row into sensor ring buffer ──
        _push_sensor_row(engine_db_id, row)

        # ── Push into window buffer ──
        X = buffer.push(vec)

        # ── Update current_cycle in engines table ──
        try:
            _supabase_execute(
                lambda _c=cycle_num: supabase.table("engines")
                    .update({"current_cycle": _c})
                    .eq("id", engine_db_id)
                    .execute()
            )
        except Exception:
            print(f"[SIM][ERROR] Failed to update current_cycle:\n{traceback.format_exc(limit=2)}")

        # ── Predict once window is full ──
        if X is not None:
            # Check if model was reloaded (e.g. after new deploy)
            _current_model = _MODEL_CACHE.get(model_type)
            if _current_model is not None and _current_model is not model:
                model = _current_model
                # Rebuild buffer with new scaler/cluster info
                scaler_mean, scaler_std = _SCALER_CACHE.get(model_type, (None, None))
                km_centroids, cl_means, cl_stds = _CLUSTER_CACHE.get(model_type, (None, None, None))
                old_buffer_data = buffer.buffer  # preserve accumulated raw data
                buffer = _WindowBuffer(
                    window_size=_win_size,
                    scaler_mean=scaler_mean, scaler_std=scaler_std,
                    num_features=_num_features,
                    kmeans_centroids=km_centroids,
                    cluster_means=cl_means, cluster_stds=cl_stds,
                )
                buffer.buffer = old_buffer_data
                # Re-compute X with new normalization
                X = buffer.push(buffer.buffer[-1]) if buffer.buffer else None
                print(f"[SIM] Hot-reloaded model for engine {engine_db_id}")
                if X is None:
                    time.sleep(TICK_INTERVAL)
                    continue

            if model is not None:
                try:
                    pred_raw = model.predict(X, verbose=0)
                    pred_rul = float(np.squeeze(pred_raw))
                    # Apply bias correction if stored in model metadata
                    _bias = _BIAS_CACHE.get(model_type, 0.0)
                    pred_rul = pred_rul - _bias
                    pred_rul = max(0.0, min(float(RUL_CAP), pred_rul))
                    # Compute feature importance on the same window
                    shap_data = _compute_feature_importance(model, X)
                except Exception:
                    print(f"[SIM][ERROR] model.predict failed at cycle {cycle_num}:\n{traceback.format_exc()}")
                    pred_rul = None
                    shap_data = []
            else:
                pred_rul  = None
                shap_data = []
                if not _no_model_warned:
                    print(f"[SIM][INFO] engine={engine_db_id} — window ready, waiting for model upload")
                    _no_model_warned = True

            if pred_rul is not None:
                new_status = _rul_to_status(pred_rul, warn_thresh=warn_thresh, crit_thresh=crit_thresh)
                fault_mode = (
                    "critical_degradation" if new_status == "critical" else
                    "moderate_degradation" if new_status == "warning" else
                    None
                )

                # Detect specific degradation type via model_type + SHAP
                degradation_type = _detect_degradation_type(
                    model_type, shap_data, pred_rul, warn_thresh
                )

                try:
                    import json as _json
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
                    if shap_data:
                        row_data["shap_values"] = _json.dumps(shap_data)

                    # Use default-arg capture to avoid late-binding closure issues
                    _supabase_execute(
                        lambda _d=row_data: supabase.table("rul_predictions").insert(_d).execute()
                    )
                    _eng_update = {"condition_status": new_status}
                    if degradation_type:
                        _eng_update["degradation_type"] = degradation_type
                    _supabase_execute(
                        lambda _u=_eng_update: supabase.table("engines")
                            .update(_u)
                            .eq("id", engine_db_id)
                            .execute()
                    )

                    # ── Fire email alert if threshold crossed ──
                    try:
                        from email_notifications import check_and_send_threshold_alert
                        # Resolve human-readable engine number for the email subject
                        _eng_num = engine_db_id  # fallback
                        try:
                            _er = supabase.table("engines").select("engine_id").eq("id", engine_db_id).single().execute()
                            if _er.data:
                                _eng_num = str(_er.data.get("engine_id", engine_db_id))
                        except Exception:
                            pass
                        check_and_send_threshold_alert(
                            supabase=supabase,
                            engine_db_id=engine_db_id,
                            engine_display_id=_eng_num,
                            pred_rul=pred_rul,
                            warn_thresh=int(warn_thresh),
                            crit_thresh=int(crit_thresh),
                        )
                    except Exception:
                        print(f"[SIM][WARN] Email alert check failed:\n{traceback.format_exc(limit=2)}")

                    print(
                        f"[SIM] engine={engine_db_id} cycle={cycle_num} "
                        f"pred_rul={pred_rul:.1f} status={new_status}"
                    )
                except Exception:
                    print(f"[SIM][ERROR] Insert/update failed at cycle {cycle_num}:\n{traceback.format_exc(limit=2)}")

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
        _RUNNING_SIMULATIONS[engine_db_id] = {"thread": thread, "stop": stop_event, "model_type": model_type}
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


def get_engine_model_type(engine_db_id: str) -> str | None:
    """Get the model_type for a running or completed simulation."""
    with _LOCK:
        entry = _RUNNING_SIMULATIONS.get(engine_db_id)
    if entry:
        return entry.get("model_type")
    return None


def active_simulations() -> list:
    with _LOCK:
        return [eid for eid, e in _RUNNING_SIMULATIONS.items() if e["thread"].is_alive()]


def resume_all_simulations(supabase):
    """
    Called once at app startup. Fetches every engine from Supabase that has a
    JSON data file (local or in Supabase Storage) and starts a simulation thread
    for it if one isn't already running.
    """
    import json as _json
    from data_utils import BASE_DATA_DIR, get_org_folder

    print("[SIM] resume_all_simulations starting...")

    try:
        resp = supabase.table("engines") \
            .select("id, engine_id, model_type, organization_id") \
            .execute()
        engines = resp.data or []
        print(f"[SIM] Found {len(engines)} engines in database")
    except Exception:
        print(f"[SIM][ERROR] resume_all_simulations — failed to fetch engines:\n{traceback.format_exc()}")
        return

    # Also fetch org names for storage path resolution
    org_names = {}
    try:
        org_resp = supabase.table("organizations").select("id, name").execute()
        for o in (org_resp.data or []):
            org_names[str(o["id"])] = o.get("name", "unknown")
        print(f"[SIM] Loaded {len(org_names)} organization names")
    except Exception:
        pass

    for eng in engines:
        engine_db_id = str(eng.get("id", ""))
        engine_id    = eng.get("engine_id", 0)
        model_type   = eng.get("model_type", "FD001")
        org_id       = str(eng.get("organization_id") or "")

        if not engine_db_id:
            continue

        # ── Check if this engine has already finished all its cycles ──
        current_cycle = 0
        try:
            cc_resp = supabase.table("engines") \
                .select("current_cycle") \
                .eq("id", engine_db_id) \
                .single() \
                .execute()
            if cc_resp.data and cc_resp.data.get("current_cycle"):
                current_cycle = int(cc_resp.data["current_cycle"])
        except Exception:
            pass

        # ── Try to resolve the JSON file path ──
        json_path = None

        # 1. Try Supabase Storage first (works on Render and local)
        try:
            from storage_utils import download_engine_json
            # Try org-specific path
            if org_id and org_id in org_names:
                _org_name = org_names[org_id].strip().lower().replace(" ", "_").replace("/", "_")
                org_folder = f"{_org_name}_{org_id}"
                storage_path = f"orgs/{org_folder}/engine_{engine_db_id}.json"
                result = download_engine_json(storage_path)
                if result:
                    json_path = result

            # Try model_type template folder
            if not json_path:
                storage_path = f"{model_type}/engine_test_{engine_id}.json"
                result = download_engine_json(storage_path)
                if result:
                    json_path = result
        except Exception as e:
            print(f"[SIM] Storage download failed for engine {engine_db_id}: {e}")

        # 2. Fallback: try local disk (for development only)
        if not json_path and os.path.isdir(BASE_DATA_DIR) and org_id:
            for folder in os.listdir(BASE_DATA_DIR):
                if org_id in folder:
                    candidate = os.path.join(BASE_DATA_DIR, folder, f"engine_{engine_db_id}.json")
                    if os.path.exists(candidate):
                        json_path = candidate
                        break

        if not json_path:
            print(f"[SIM] No data file found for engine {engine_db_id} — skipping resume")
            continue

        # Check total cycles to see if already complete
        try:
            with open(json_path, encoding="utf-8") as f:
                d = _json.load(f)
            if isinstance(d, list):
                total_cycles = len(d)
            elif isinstance(d, dict):
                total_cycles = len(d.get("cycles", []))
            else:
                total_cycles = 0
        except Exception:
            total_cycles = 0

        if total_cycles == 0:
            print(f"[SIM] Data file empty for engine {engine_db_id} — skipping resume")
            continue

        if current_cycle >= total_cycles:
            print(f"[SIM] Engine {engine_db_id} already completed all {total_cycles} cycles — skipping resume")
            # Still pre-load sensor rows into the ring buffer for display
            try:
                cycles_data = _json.loads(open(json_path).read()) if isinstance(d, str) else d
                if isinstance(cycles_data, dict):
                    cycles_data = cycles_data.get("cycles", [])
                for row in cycles_data:
                    _push_sensor_row(engine_db_id, row)
                print(f"[SIM] Pre-loaded {len(cycles_data)} sensor rows for completed engine {engine_db_id}")
            except Exception:
                pass
            continue

        # ── Start simulation thread ──
        start_engine_simulation(
            engine_db_id=engine_db_id,
            json_path=json_path,
            model_type=model_type,
            supabase=supabase,
        )
