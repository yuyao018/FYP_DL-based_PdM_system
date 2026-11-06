import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import h5py
import os

# 1. CONFIGURATION
FILE_INDEX  = 'FD004'   # FD001 / FD002 / FD003 / FD004

WINDOW_SIZE      = 35
RUL_CAP          = 100

D_MODEL          = 16
NUM_HEADS        = 1
FF_DIM           = 32
NUM_LAYERS       = 2
WINDOW_SIZE_ATTN = 5
HIDDEN_DIM_GRU   = 64

DROPOUT_RATE     = 0.3
WEIGHT_DECAY     = 1e-5

EPOCHS           = 600  # FD001 & FD003 200 / FD002 & FD004 600
BATCH_SIZE       = 256
LEARNING_RATE    = 1e-4
PATIENCE_LIMIT   = 25

BIAS_SHIFT_FACTOR = 0.7

SEED = 1  # single fixed seed

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}  |  Dataset: {FILE_INDEX}")

# 2. H5 SAVE / LOAD
def save_model_h5(model, filepath, metadata=None, scaler_mean=None, scaler_std=None,
                  kmeans_centroids=None, cluster_means=None, cluster_stds=None):
    """Save model weights, hyperparameters, scaler stats, and cluster info to a single .h5 file."""
    with h5py.File(filepath, 'w') as f:
        grp = f.create_group('weights')
        for name, tensor in model.state_dict().items():
            grp.create_dataset(name, data=tensor.cpu().numpy())
        if metadata:
            meta = f.create_group('metadata')
            for k, v in metadata.items():
                meta.attrs[k] = v
        # Save scaler statistics so inference can reproduce exact normalisation
        if scaler_mean is not None and scaler_std is not None:
            sc_grp = f.create_group('scaler')
            sc_grp.create_dataset('mean', data=scaler_mean)
            sc_grp.create_dataset('std',  data=scaler_std)
        # Save per-cluster normalization artifacts for FD002/FD004
        if kmeans_centroids is not None:
            cl_grp = f.create_group('cluster')
            cl_grp.create_dataset('centroids', data=kmeans_centroids)
            if cluster_means is not None:
                cl_grp.create_dataset('means', data=cluster_means)
            if cluster_stds is not None:
                cl_grp.create_dataset('stds', data=cluster_stds)
    print(f"  Saved → {filepath}")


# 3. METRICS
def compute_s_score(y_true, y_pred):
    diff   = y_pred - y_true
    scores = np.zeros_like(diff, dtype=float)
    scores[diff > 0] = np.exp( diff[diff > 0] / 10) - 1
    scores[diff < 0] = np.exp(-diff[diff < 0] / 13) - 1
    return np.sum(scores)

def print_metrics(label, y_true, y_pred):
    rmse   = np.sqrt(mean_squared_error(y_true, y_pred))
    sscore = compute_s_score(y_true, y_pred)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  RMSE    : {rmse:.2f}")
    print(f"  S-Score : {sscore:.2f}")
    print(f"{'='*60}")
    return rmse, sscore


# 4. SOFT RUL CAPPING
def soft_clip_rul(rul, cap, transition=15):
    rul_out = rul.copy().astype(np.float32)
    mask = rul_out > (cap - transition)
    if mask.any():
        t = (rul_out[mask] - (cap - transition)) / transition
        rul_out[mask] = (cap - transition) + transition * (
            1.0 / (1.0 + np.exp(-5.0 * (t - 0.5)))
        )
    return np.clip(rul_out, 0, cap)


# 5. ASYMMETRIC LOSS
class AsymmetricRULLoss(nn.Module):
    def __init__(self, late_penalty=1.5):
        super().__init__()
        self.late_penalty = late_penalty

    def forward(self, pred, target):
        diff = pred - target
        loss = torch.where(
            diff > 0,
            self.late_penalty * diff ** 2,
            diff ** 2
        )
        return loss.mean()


# 6. MODEL
class LocalSparseAttention(nn.Module):
    def __init__(self, d_model, nhead, window_size):
        super().__init__()
        self.window_size = window_size
        self.mha = nn.MultiheadAttention(
            embed_dim=d_model, num_heads=nhead, batch_first=True
        )

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


class TransformerBiGRUEncoderLayer(nn.Module):
    def __init__(self, d_model, nhead, window_size, dim_feedforward, dropout):
        super().__init__()
        self.global_attn = nn.MultiheadAttention(
            embed_dim=d_model, num_heads=nhead, batch_first=True
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.local_sparse_attn = LocalSparseAttention(d_model, nhead, window_size)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn1 = nn.Sequential(
            nn.Linear(d_model, dim_feedforward), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(dim_feedforward, d_model),
        )
        self.ffn2 = nn.Sequential(
            nn.Linear(d_model, dim_feedforward), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(dim_feedforward, d_model),
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


class TransformerBiGRU(nn.Module):
    def __init__(self, num_sensors, seq_len, d_model, nhead, num_layers, window_size, hidden_dim_gru):
        super().__init__()
        self.input_projection = nn.Linear(num_sensors, d_model)
        self.pos_embedding    = nn.Parameter(torch.randn(1, seq_len, d_model))
        self.encoder_layers   = nn.ModuleList([
            TransformerBiGRUEncoderLayer(
                d_model, nhead, window_size,
                dim_feedforward=FF_DIM,
                dropout=DROPOUT_RATE,
            )
            for _ in range(num_layers)
        ])
        self.bigru = nn.GRU(
            input_size=d_model, hidden_size=hidden_dim_gru,
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


# 7. DATA LOADING  (with feature engineering)
ROLLING_WINDOW = 5

BASE = '/content/drive/MyDrive/FYP/experiment/NASA_CMAPS_processed'

def engineer_features(X_data):
    """
    Appends rolling mean and rolling std across ALL sensors.
    Returns shape (samples, window_size, F * 3).
    """
    samples, T, F = X_data.shape
    roll_mean = np.zeros_like(X_data)
    roll_std  = np.zeros_like(X_data)
    for t in range(T):
        start = max(0, t - ROLLING_WINDOW + 1)
        window = X_data[:, start:t + 1, :]
        roll_mean[:, t, :] = window.mean(axis=1)
        roll_std[:, t, :]  = window.std(axis=1)
    return np.concatenate([X_data, roll_mean, roll_std], axis=2).astype(np.float32)


print(f"\nLoading {FILE_INDEX}...")
X_train_raw = np.load(f'{BASE}/X_train_{FILE_INDEX}.npy').astype(np.float32)
y_train_raw = np.load(f'{BASE}/y_train_{FILE_INDEX}.npy')
X_test_raw  = np.load(f'{BASE}/X_test_{FILE_INDEX}.npy').astype(np.float32)
y_true_raw  = np.load(f'{BASE}/y_test_{FILE_INDEX}.npy')

# Load scaler stats saved by preprocessing.py (FD001/FD003 only)
_sc_mean_path = f'{BASE}/scaler_mean_{FILE_INDEX}.npy'
_sc_std_path  = f'{BASE}/scaler_std_{FILE_INDEX}.npy'
SCALER_MEAN = np.load(_sc_mean_path) if os.path.exists(_sc_mean_path) else None
SCALER_STD  = np.load(_sc_std_path)  if os.path.exists(_sc_std_path)  else None
if SCALER_MEAN is not None:
    print(f"Scaler mean loaded: {np.round(SCALER_MEAN, 4).tolist()}")
    print(f"Scaler std  loaded: {np.round(SCALER_STD, 4).tolist()}")
else:
    print("WARNING: No scaler stats found — inference normalisation will be approximate.")

print("Sensor Min Values:", X_train_raw.min(axis=(0,1)))
print("Sensor Max Values:", X_train_raw.max(axis=(0,1)))
print("Target Max Label :", y_train_raw.max())

assert X_train_raw.shape[1] == WINDOW_SIZE, (
    f"Seq len mismatch: got {X_train_raw.shape[1]}, expected {WINDOW_SIZE}"
)

print(f"Raw shapes: X_train {X_train_raw.shape} | X_test {X_test_raw.shape}")

print(f"Adding rolling mean & rolling std (window={ROLLING_WINDOW})...")
X_train_raw = engineer_features(X_train_raw)
X_test_raw  = engineer_features(X_test_raw)

y_train_raw = soft_clip_rul(y_train_raw, cap=RUL_CAP, transition=15).reshape(-1, 1)
y_true_raw  = np.clip(y_true_raw, 0, RUL_CAP).astype(np.float32)

num_features = X_train_raw.shape[2]
print(f"Final shapes: X_train {X_train_raw.shape} | X_test {X_test_raw.shape} | features {num_features}")

X_train_t = torch.from_numpy(X_train_raw)
y_train_t = torch.from_numpy(y_train_raw)
X_test_t  = torch.from_numpy(X_test_raw)


# 8. TRAINING
def train(seed=SEED):
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)

    dataset = TensorDataset(X_train_t, y_train_t)
    n_train = int(0.9 * len(dataset))
    n_val   = len(dataset) - n_train
    tr, va  = torch.utils.data.random_split(dataset, [n_train, n_val])
    tr_loader = DataLoader(tr, batch_size=BATCH_SIZE, shuffle=True,
                           num_workers=0, pin_memory=True)
    va_loader = DataLoader(va, batch_size=BATCH_SIZE, shuffle=False,
                           num_workers=0, pin_memory=True)

    model = TransformerBiGRU(
        num_sensors    = num_features,
        seq_len        = WINDOW_SIZE,
        d_model        = D_MODEL,
        nhead          = NUM_HEADS,
        num_layers     = NUM_LAYERS,
        window_size    = WINDOW_SIZE_ATTN,
        hidden_dim_gru = HIDDEN_DIM_GRU,
    ).to(DEVICE)

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    criterion = AsymmetricRULLoss(late_penalty=1.5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=EPOCHS, eta_min=1e-6
    )

    best_val   = float('inf')
    patience_c = 0
    ckpt       = f'_ckpt_{FILE_INDEX}.pt'

    for epoch in range(EPOCHS):
        model.train()
        tr_loss = 0.0
        for bx, by in tr_loader:
            bx, by = bx.to(DEVICE), by.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            tr_loss += loss.item()

        scheduler.step()

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for bx, by in va_loader:
                bx, by = bx.to(DEVICE), by.to(DEVICE)
                val_loss += criterion(model(bx), by).item()

        avg_val = val_loss / len(va_loader)

        if avg_val < best_val:
            best_val   = avg_val
            torch.save(model.state_dict(), ckpt)
            patience_c = 0
        else:
            patience_c += 1
            if patience_c >= PATIENCE_LIMIT:
                print(f"  Early stop at epoch {epoch + 1}")
                break

        if (epoch + 1) % 50 == 0:
            print(f"  Epoch {epoch+1:>3} | train {tr_loss/len(tr_loader):.4f} | val {avg_val:.4f}")

    # Restore best checkpoint
    model.load_state_dict(torch.load(ckpt))
    model.eval()

    # [CHANGE-2] Save to .h5 with scaler stats embedded
    h5_path = os.path.join(BASE, f'transformer_bigru_{FILE_INDEX}.h5')

    # Load cluster artifacts if they exist (FD002/FD004)
    _km_centroids = None
    _cl_means = None
    _cl_stds = None
    _km_path = f'{BASE}/kmeans_centroids_{FILE_INDEX}.npy'
    _cm_path = f'{BASE}/cluster_means_{FILE_INDEX}.npy'
    _cs_path = f'{BASE}/cluster_stds_{FILE_INDEX}.npy'
    if os.path.exists(_km_path):
        _km_centroids = np.load(_km_path)
        print(f"  Cluster centroids loaded: {_km_centroids.shape}")
    if os.path.exists(_cm_path):
        _cl_means = np.load(_cm_path)
    if os.path.exists(_cs_path):
        _cl_stds = np.load(_cs_path)

    save_model_h5(model, h5_path,
        metadata={
            'dataset':        FILE_INDEX,
            'seed':           seed,
            'window_size':    WINDOW_SIZE,
            'rul_cap':        RUL_CAP,
            'rolling_window': ROLLING_WINDOW,
            'd_model':        D_MODEL,
            'num_heads':      NUM_HEADS,
            'ff_dim':         FF_DIM,
            'num_layers':     NUM_LAYERS,
            'window_attn':    WINDOW_SIZE_ATTN,
            'hidden_dim_gru': HIDDEN_DIM_GRU,
            'dropout':        DROPOUT_RATE,
            'num_features':   num_features,
            'bias_shift':     BIAS_SHIFT_FACTOR,
        },
        scaler_mean=SCALER_MEAN,
        scaler_std=SCALER_STD,
        kmeans_centroids=_km_centroids,
        cluster_means=_cl_means,
        cluster_stds=_cl_stds,
    )

    with torch.no_grad():
        preds = model(X_test_t.to(DEVICE)).cpu().numpy().flatten()
    preds = np.maximum(preds, 0)

    if os.path.exists(ckpt):
        os.remove(ckpt)

    return preds


# 9. RUN + RESULTS
print(f"\n{'='*60}")
print(f"  {FILE_INDEX}")
print(f"{'='*60}")

y_pred = train()

# Bias diagnostic
errors    = y_pred - y_true_raw
mean_bias = float(np.mean(errors))
pct_late  = float((errors > 0).mean() * 100)
print(f"\n--- Bias Diagnostic ---")
print(f"  Mean error : {mean_bias:+.2f}  "
      f"({'skews LATE' if mean_bias > 0 else 'skews early'})")
print(f"  % late     : {pct_late:.1f}%")

if mean_bias > 0 and BIAS_SHIFT_FACTOR > 0:
    shift     = mean_bias * BIAS_SHIFT_FACTOR
    y_shifted = np.maximum(y_pred - shift, 0)
    print(f"  Shift      : −{shift:.2f} cycles")
else:
    y_shifted = y_pred

print_metrics(f"{FILE_INDEX} raw",     y_true_raw, y_pred)
if not np.array_equal(y_pred, y_shifted):
    print_metrics(f"{FILE_INDEX} shifted", y_true_raw, y_shifted)
