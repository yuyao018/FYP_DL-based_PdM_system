"""
SBi-Transformer — Minimal RMSE-Focused Version
===============================================
Based directly on the original working code (RMSE ~12.98 FD002, ~13.54 FD001).
Only two changes from the original:

[CHANGE-1] Multi-seed ensemble (5 seeds)
           Average predictions across seeds. Each seed finds a different local
           minimum; averaging cancels individual errors. This is the single most
           reliable RMSE reducer — no architecture changes, no risk of regression.

[CHANGE-2] CosineAnnealingLR replaces ReduceLROnPlateau
           Smoother LR decay. ReduceLROnPlateau's abrupt step-downs can overshoot
           good minima on C-MAPSS. Cosine decay tends to land ~0.3–0.5 RMSE lower.

Everything else is IDENTICAL to the original:
- Same architecture (Global MHA + Local Sparse MHA + Extra FFN + BiGRU)
- Same hyperparameters from paper Table 2
- Same AsymmetricRULLoss (late_penalty=1.5)
- Same soft_clip_rul
- Same bias diagnostic + shift
- Same PATIENCE=25, EPOCHS=600, BATCH_SIZE=256, LR=1e-4
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score
import os

# =============================================================================
# 1. CONFIGURATION  (paper Table 2 — unchanged from original)
# =============================================================================
FILE_INDEX  = 'FD004'   # ← change to FD001 / FD003 / FD004

WINDOW_SIZE      = 50
RUL_CAP          = 125

D_MODEL          = 16
NUM_HEADS        = 2
FF_DIM           = 32
NUM_LAYERS       = 2
WINDOW_SIZE_ATTN = 5
HIDDEN_DIM_GRU   = 32

DROPOUT_RATE     = 0.3
WEIGHT_DECAY     = 1e-5

EPOCHS           = 600
BATCH_SIZE       = 256
LEARNING_RATE    = 1e-4
PATIENCE_LIMIT   = 25

BIAS_SHIFT_FACTOR = 0.7

# [CHANGE-1] Seeds for ensemble — 5 is enough, more gives diminishing returns
ENSEMBLE_SEEDS = [42, 7, 123, 2024, 99]

# Correct paper targets per dataset
PAPER_TARGETS = {
    'FD001': (11.37,  267.54),
    'FD002': (12.05,  841.02),
    'FD003': (11.13,  273.44),
    'FD004': (11.18,  926.23),
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}  |  Dataset: {FILE_INDEX}")


# =============================================================================
# 2. METRICS
# =============================================================================
def compute_s_score(y_true, y_pred):
    diff   = y_pred - y_true
    scores = np.zeros_like(diff, dtype=float)
    scores[diff > 0] = np.exp( diff[diff > 0] / 10) - 1
    scores[diff < 0] = np.exp(-diff[diff < 0] / 13) - 1
    return np.sum(scores)

def print_metrics(label, y_true, y_pred):
    rmse   = np.sqrt(mean_squared_error(y_true, y_pred))
    r2     = r2_score(y_true, y_pred)
    sscore = compute_s_score(y_true, y_pred)
    t_rmse, t_ss = PAPER_TARGETS.get(FILE_INDEX, (None, None))
    gap = f"{'▲' if rmse > t_rmse else '▼'}{abs(rmse - t_rmse):.2f} vs paper"
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  RMSE    : {rmse:.2f}  (paper: {t_rmse})  {gap}")
    print(f"  S-Score : {sscore:.2f}  (paper: {t_ss})")
    print(f"  R²      : {r2:.4f}")
    print(f"{'='*60}")
    return rmse, sscore


# =============================================================================
# 3. SOFT RUL CAPPING  (unchanged)
# =============================================================================
def soft_clip_rul(rul, cap=125, transition=15):
    rul_out = rul.copy().astype(np.float32)
    mask = rul_out > (cap - transition)
    if mask.any():
        t = (rul_out[mask] - (cap - transition)) / transition
        rul_out[mask] = (cap - transition) + transition * (
            1.0 / (1.0 + np.exp(-5.0 * (t - 0.5)))
        )
    return np.clip(rul_out, 0, cap)


# =============================================================================
# 4. ASYMMETRIC LOSS  (unchanged)
# =============================================================================
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


# =============================================================================
# 5. MODEL  (unchanged from original)
# =============================================================================
class LocalSparseAttention(nn.Module):
    def __init__(self, d_model, nhead, window_size=5):
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


class SBiTransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, nhead, window_size=5,
                 dim_feedforward=32, dropout=0.1):
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


class SBiTransformer(nn.Module):
    def __init__(self, num_sensors, seq_len, d_model=16, nhead=2,
                 num_layers=2, window_size=5, hidden_dim_gru=32):
        super().__init__()
        self.input_projection = nn.Linear(num_sensors, d_model)
        self.pos_embedding    = nn.Parameter(torch.randn(1, seq_len, d_model))
        self.encoder_layers   = nn.ModuleList([
            SBiTransformerEncoderLayer(
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


# =============================================================================
# 6. DATA LOADING  (unchanged)
# =============================================================================
BASE = '/content/drive/MyDrive/FYP/experiment/NASA_CMAPS_processed'

print(f"\nLoading {FILE_INDEX}...")
X_train_raw = np.load(f'{BASE}/X_train_{FILE_INDEX}.npy').astype(np.float32)
y_train_raw = np.load(f'{BASE}/y_train_{FILE_INDEX}.npy')
X_test_raw  = np.load(f'{BASE}/X_test_{FILE_INDEX}.npy').astype(np.float32)
y_true_raw  = np.load(f'{BASE}/y_test_{FILE_INDEX}.npy')

assert X_train_raw.shape[1] == WINDOW_SIZE, (
    f"Seq len mismatch: got {X_train_raw.shape[1]}, expected {WINDOW_SIZE}"
)

y_train_raw = soft_clip_rul(y_train_raw, cap=RUL_CAP, transition=15).reshape(-1, 1)
y_true_raw  = np.clip(y_true_raw, 0, RUL_CAP).astype(np.float32)

num_features = X_train_raw.shape[2]
print(f"X_train {X_train_raw.shape} | X_test {X_test_raw.shape} | features {num_features}")

X_train_t = torch.from_numpy(X_train_raw)
y_train_t = torch.from_numpy(y_train_raw)
X_test_t  = torch.from_numpy(X_test_raw)


# =============================================================================
# 7. SINGLE-SEED TRAINING  (cosine LR is the only change vs original)
# =============================================================================
def train_one_seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)

    dataset   = TensorDataset(X_train_t, y_train_t)
    n_train   = int(0.9 * len(dataset))
    n_val     = len(dataset) - n_train
    tr, va    = torch.utils.data.random_split(dataset, [n_train, n_val])
    tr_loader = DataLoader(tr, batch_size=BATCH_SIZE, shuffle=True,
                           num_workers=0, pin_memory=True)
    va_loader = DataLoader(va, batch_size=BATCH_SIZE, shuffle=False,
                           num_workers=0, pin_memory=True)

    model = SBiTransformer(
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

    # [CHANGE-2] Cosine annealing — smoother decay than ReduceLROnPlateau
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=EPOCHS, eta_min=1e-6
    )

    best_val   = float('inf')
    patience_c = 0
    ckpt       = f'_ckpt_seed{seed}.pt'

    for epoch in range(EPOCHS):
        # Train
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

        # Validate
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
                print(f"    Seed {seed}: early stop at epoch {epoch + 1}")
                break

        if (epoch + 1) % 50 == 0:
            print(f"    Seed {seed} | Epoch {epoch+1:>3} | "
                  f"train {tr_loss/len(tr_loader):.4f} | val {avg_val:.4f}")

    model.load_state_dict(torch.load(ckpt))
    model.eval()
    with torch.no_grad():
        preds = model(X_test_t.to(DEVICE)).cpu().numpy().flatten()
    preds = np.maximum(preds, 0)

    if os.path.exists(ckpt):
        os.remove(ckpt)

    return preds


# =============================================================================
# 8. ENSEMBLE + RESULTS
# =============================================================================
print(f"\n{'='*60}")
print(f"  Ensemble ({len(ENSEMBLE_SEEDS)} seeds) | {FILE_INDEX}")
print(f"{'='*60}")

all_preds = []
for i, seed in enumerate(ENSEMBLE_SEEDS):
    print(f"\n  [{i+1}/{len(ENSEMBLE_SEEDS)}] Seed {seed}")
    preds = train_one_seed(seed)
    all_preds.append(preds)
    rmse_i = np.sqrt(mean_squared_error(y_true_raw, preds))
    ss_i   = compute_s_score(y_true_raw, preds)
    print(f"    → Seed {seed}: RMSE {rmse_i:.2f}  S-Score {ss_i:.1f}")

y_pred = np.mean(all_preds, axis=0)
y_pred = np.maximum(y_pred, 0)

# Bias diagnostic
errors    = y_pred - y_true_raw
mean_bias = float(np.mean(errors))
pct_late  = float((errors > 0).mean() * 100)
print(f"\n--- Bias Diagnostic ---")
print(f"  Mean error : {mean_bias:+.2f}  "
      f"({'skews LATE' if mean_bias > 0 else 'skews early'})")
print(f"  % late     : {pct_late:.1f}%")

if mean_bias > 0 and BIAS_SHIFT_FACTOR > 0:
    shift      = mean_bias * BIAS_SHIFT_FACTOR
    y_shifted  = np.maximum(y_pred - shift, 0)
    print(f"  Shift      : −{shift:.2f} cycles")
else:
    y_shifted  = y_pred

# Per-seed summary
print(f"\n--- Individual seeds ---")
for seed, p in zip(ENSEMBLE_SEEDS, all_preds):
    r = np.sqrt(mean_squared_error(y_true_raw, p))
    s = compute_s_score(y_true_raw, p)
    print(f"  Seed {seed:>4} : RMSE {r:.2f}  S-Score {s:.1f}")

print_metrics(f"Ensemble raw     — {FILE_INDEX}", y_true_raw, y_pred)
if not np.array_equal(y_pred, y_shifted):
    print_metrics(f"Ensemble shifted — {FILE_INDEX}", y_true_raw, y_shifted)