import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from dataset import HockeyDataset
from model import HockeyLSTM

BATCH_SIZE = 64
EPOCHS = 20
LR = 1e-3
SEQ_LEN = 5
CSV_FILE = "data/processed/nhl_game_logs_processed_20242025.csv"
# loss weights, bigger weight = more important
LOSS_WEIGHTS = {
    "goals": 2.0,
    "assists": 2.0,
    "points": 2.0,
    "shots": 1.5,
    "hits": 1.5,
    "blocked": 1.5,
    # other weights are defaulted to 1.0
}

# device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# data
train_dataset = HockeyDataset(CSV_FILE, seq_len=SEQ_LEN)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

scalers = train_dataset.get_scalers()
target_scaler = scalers["targets"]
TARGET_COLS = train_dataset.get_target_cols()

print(f"training on targets: {TARGET_COLS}")

# model
input_dim = train_dataset[0][0].shape[1]
output_dim = len(TARGET_COLS)
model = HockeyLSTM(input_dim, output_dim).to(device)

optimizer = optim.Adam(model.parameters(), lr=LR)

# weighted loss
loss_weights = torch.tensor([LOSS_WEIGHTS.get(col, 1.0) for col in TARGET_COLS],
                            dtype=torch.float32).to(device)

def weighted_mse_loss(preds, targets, weights):
    # preds, targets: (batch, out_dim); weights: (out_dim,)
    se = (preds - targets) ** 2
    weighted = se * weights
    return weighted.mean()

# training loop
for epoch in range(EPOCHS):
    model.train()
    epoch_loss = 0
    for features, targets in train_loader:
        features = features.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        outputs = model(features)

        loss = weighted_mse_loss(outputs, targets, loss_weights)
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    avg_loss = epoch_loss / len(train_loader)

    # evaluate it in terms of real stats
    model.eval()
    with torch.no_grad():
        all_preds, all_targets = [], []
        for features, targets in train_loader:
            features = features.to(device)
            outputs = model(features)

            preds = outputs.detach().cpu().numpy()
            targs = targets.numpy()

            preds_real = target_scaler.inverse_transform(preds)
            targs_real = target_scaler.inverse_transform(targs)

            all_preds.append(preds_real)
            all_targets.append(targs_real)

        all_preds = np.vstack(all_preds)
        all_targets = np.vstack(all_targets)

        mae_per_stat = np.mean(np.abs(all_preds - all_targets), axis=0)

    print(f"\nepoch {epoch+1}/{EPOCHS} | weighted loss (normalized): {avg_loss:.4f}")
    for col, mae in zip(TARGET_COLS, mae_per_stat):
        print(f"  MAE {col:10s}: {mae:.3f}")

# save the model
torch.save(model.state_dict(), "models/lstm_model.pth")
print("done, model saved to models/lstm_model.pth")