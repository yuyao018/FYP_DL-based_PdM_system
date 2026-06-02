"""
data_preprocessing.py
=====================
Data preprocessing for SBi-Transformer (BiGRU variant) — all 4 C-MAPSS subsets.
Reference: 2026_A transformer-based method for aircraft engine RUL prediction
           integrating dual-layer attention with BiLSTM.pdf

Pipeline:
  1. Z-Score normalisation                               (paper Eq. 1)
       FD001 / FD003 → single global scaler  (1 operating condition)
       FD002 / FD004 → per-cluster scaler    (6 operating conditions)
  2. Piecewise-linear RUL labelling, cap = 125
  3. Sliding-window sequence generation, window = 45    (paper Table 2)
  4. Save .npy artefacts consumed by sbi_transformer_bigru.py

Why FD001/FD003 skip clustering
────────────────────────────────
FD001 and FD003 each have exactly 1 operating condition.  Running KMeans on
a uniform operating-condition space partitions the data arbitrarily — the 6
clusters have no physical meaning and each cluster's scaler is fitted on a
random ~1/6 slice of the data, producing noisier normalisation statistics
than a single scaler fitted on all rows.  The correct approach is one global
StandardScaler fitted on all training rows, applied to all test rows.

FD002 and FD004 have 6 distinct operating regimes.  Sensor readings shift
significantly between regimes, so a global scaler produces badly scaled
inputs (a sensor reading of 500 in condition A vs 5000 in condition B would
both map to the same normalised range).  Per-cluster normalisation corrects
for this before the model sees the data.
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# =============================================================================
# 1. SHARED CONFIGURATION
# =============================================================================
RUL_CAP     = 125
WINDOW_SIZE = 50   # must match model's WINDOW_SIZE

# Set True  → 14 sensors + 3 OS cols = 17 features  (paper Table 2 input_size=17)
# Set False → 14 sensors only = 14 features
INCLUDE_OS_COLS = True

RAW_DATA_DIR = '/content/drive/MyDrive/FYP/experiment/NASA_CMAPS'
OUTPUT_DIR   = '/content/drive/MyDrive/FYP/experiment/NASA_CMAPS_processed'

COLS = (
    ['unit_nr', 'time_cycles', 'os_1', 'os_2', 'os_3'] +
    [f's_{i}' for i in range(1, 22)]
)
OS_COLS = ['os_1', 'os_2', 'os_3']

# 14 sensors with strong degradation correlation (standard CMAPSS selection)
SENSOR_COLS = [
    's_2', 's_3', 's_4', 's_6', 's_7', 's_8', 's_9', 's_11',
    's_12', 's_13', 's_15', 's_17', 's_20', 's_21'
]
FEAT_COLS = SENSOR_COLS + OS_COLS if INCLUDE_OS_COLS else SENSOR_COLS

# Per-dataset settings — drives which normalisation path each dataset takes
#   n_clusters=1  → global single-scaler path  (FD001, FD003)
#   n_clusters=6  → per-cluster path           (FD002, FD004)
DATASET_CONFIG = {
    'FD001': {'n_clusters': 1, 'label': '1 op. condition  → global scaler'},
    'FD002': {'n_clusters': 6, 'label': '6 op. conditions → per-cluster scaler'},
    'FD003': {'n_clusters': 1, 'label': '1 op. condition  → global scaler'},
    'FD004': {'n_clusters': 6, 'label': '6 op. conditions → per-cluster scaler'},
}

# Datasets to process — edit this list to run only a subset
DATASETS = ['FD001', 'FD002', 'FD003', 'FD004']


# =============================================================================
# 2. HELPER FUNCTIONS
# =============================================================================

def label_rul(train_df, rul_cap):
    """
    Piecewise-linear RUL: reverse countdown from max cycle per engine,
    capped at rul_cap.  Soft-clip smoothing is applied later inside the
    model training script — do NOT double-apply it here.
    """
    train_df   = train_df.copy()
    max_cycles = train_df.groupby('unit_nr')['time_cycles'].transform('max')
    train_df['RUL'] = (max_cycles - train_df['time_cycles']).clip(upper=rul_cap)
    return train_df


def global_zscore_normalize(train_df, test_df, feat_cols):
    """
    Single StandardScaler fitted on ALL training rows, applied to test rows.

    Used for FD001 / FD003 (1 operating condition).
    Fitting on the full training set gives the most statistically stable
    mean and std estimates — no artificial partitioning needed.
    """
    train_df = train_df.copy()
    test_df  = test_df.copy()
    scaler   = StandardScaler()
    train_df[feat_cols] = scaler.fit_transform(train_df[feat_cols])
    test_df[feat_cols]  = scaler.transform(test_df[feat_cols])
    return train_df, test_df


def cluster_zscore_normalize(train_df, test_df, feat_cols, n_clusters):
    """
    KMeans clustering on OS columns, then one StandardScaler per cluster.

    Used for FD002 / FD004 (6 operating conditions).
    Scaler is FIT on training rows for each cluster, APPLIED to matching
    test rows — prevents data leakage across the train/test split.

    The '_cluster' column is a temporary helper and is NOT included in
    feat_cols — it is dropped by the caller after normalisation.
    """
    train_df = train_df.copy()
    test_df  = test_df.copy()

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    train_df['_cluster'] = kmeans.fit_predict(train_df[OS_COLS])
    test_df['_cluster']  = kmeans.predict(test_df[OS_COLS])

    scalers = {}
    for cid in range(n_clusters):
        tr_mask = train_df['_cluster'] == cid
        if tr_mask.sum() == 0:
            continue
        scaler = StandardScaler()
        train_df.loc[tr_mask, feat_cols] = scaler.fit_transform(
            train_df.loc[tr_mask, feat_cols]
        )
        scalers[cid] = scaler

    for cid, scaler in scalers.items():
        te_mask = test_df['_cluster'] == cid
        if te_mask.sum() == 0:
            continue
        test_df.loc[te_mask, feat_cols] = scaler.transform(
            test_df.loc[te_mask, feat_cols]
        )

    train_df.drop(columns=['_cluster'], inplace=True)
    test_df.drop(columns=['_cluster'],  inplace=True)
    return train_df, test_df


def create_train_sequences(df, window_size, feat_cols):
    """
    Sliding-window sequence generation for training.
    Each sample: X shape (window_size, n_features), y = RUL at final timestep.
    Engines shorter than window_size are skipped (they are too short to yield
    a meaningful degradation trajectory at this resolution).
    """
    X, y = [], []
    for uid in df['unit_nr'].unique():
        unit   = df[df['unit_nr'] == uid]
        data   = unit[feat_cols].values
        labels = unit['RUL'].values
        if len(unit) < window_size:
            continue
        for i in range(len(unit) - window_size + 1):
            X.append(data[i:i + window_size])
            y.append(labels[i + window_size - 1])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def extract_test_sequences(df, window_size, feat_cols):
    """
    Extracts the LAST window_size timesteps per test engine.
    Engines shorter than window_size are zero-padded at the front —
    this is rare in C-MAPSS but handled defensively.
    """
    X_test = []
    for uid in df['unit_nr'].unique():
        unit = df[df['unit_nr'] == uid]
        data = unit[feat_cols].values
        if len(unit) >= window_size:
            X_test.append(data[-window_size:])
        else:
            pad = np.zeros(
                (window_size - len(unit), len(feat_cols)), dtype=np.float32
            )
            X_test.append(np.vstack([pad, data]))
    return np.array(X_test, dtype=np.float32)


# =============================================================================
# 3. MAIN PIPELINE
# =============================================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)

for ds in DATASETS:
    cfg = DATASET_CONFIG[ds]
    n_clusters = cfg['n_clusters']

    print(f'\n{"="*55}')
    print(f'  Preprocessing {ds}  ({cfg["label"]})')
    print(f'{"="*55}')

    # ── Load ────────────────────────────────────────────────────────────────
    train_df = pd.read_csv(
        f'{RAW_DATA_DIR}/train_{ds}.txt', sep=r'\s+', header=None, names=COLS
    )
    test_df = pd.read_csv(
        f'{RAW_DATA_DIR}/test_{ds}.txt', sep=r'\s+', header=None, names=COLS
    )
    rul_df = pd.read_csv(
        f'{RAW_DATA_DIR}/RUL_{ds}.txt', sep=r'\s+', header=None, names=['RUL']
    )

    # ── RUL labelling ───────────────────────────────────────────────────────
    train_df = label_rul(train_df, RUL_CAP)

    # ── Normalisation — branching on operating-condition count ──────────────
    if n_clusters == 1:
        # FD001, FD003: single global scaler
        train_df, test_df = global_zscore_normalize(train_df, test_df, FEAT_COLS)
    else:
        # FD002, FD004: per-cluster scaler
        train_df, test_df = cluster_zscore_normalize(
            train_df, test_df, FEAT_COLS, n_clusters
        )

    # ── Sequence generation ─────────────────────────────────────────────────
    X_train, y_train = create_train_sequences(train_df, WINDOW_SIZE, FEAT_COLS)
    X_test           = extract_test_sequences(test_df,  WINDOW_SIZE, FEAT_COLS)
    y_test           = rul_df['RUL'].values.clip(0, RUL_CAP).astype(np.float32)

    # ── Save ────────────────────────────────────────────────────────────────
    np.save(f'{OUTPUT_DIR}/X_train_{ds}.npy', X_train)
    np.save(f'{OUTPUT_DIR}/y_train_{ds}.npy', y_train)
    np.save(f'{OUTPUT_DIR}/X_test_{ds}.npy',  X_test)
    np.save(f'{OUTPUT_DIR}/y_test_{ds}.npy',  y_test)

    print(f'  Features   : {len(FEAT_COLS)}'
          f'  ({len(SENSOR_COLS)} sensors'
          f'{" + 3 OS cols" if INCLUDE_OS_COLS else ""})')
    print(f'  Window size: {WINDOW_SIZE}')
    print(f'  X_train    : {X_train.shape}')
    print(f'  y_train    : {y_train.shape}'
          f'  RUL range [{y_train.min():.0f}, {y_train.max():.0f}]')
    print(f'  X_test     : {X_test.shape}')
    print(f'  y_test     : {y_test.shape}'
          f'  RUL range [{y_test.min():.0f}, {y_test.max():.0f}]')

print(f'\n{"="*55}')
print('  Preprocessing complete.')
print(f'  Model expects: WINDOW_SIZE={WINDOW_SIZE},'
      f' num_features={len(FEAT_COLS)}')
print(f'{"="*55}')