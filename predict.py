import sys
import json
import torch
import pandas as pd
import numpy as np
import argparse
from dataset import HockeyDataset
from model import HockeyLSTM

SEQ_LEN = 5
CSV_FILE = "data/processed/nhl_game_logs_processed_20242025.csv"
MODEL_PATH = "models/lstm_model.pth"

def _to_py(val):
    # convert numpy scalars/arrays to regular python types
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, (np.floating, np.float32, np.float64)):
        return float(val)
    if isinstance(val, (np.integer, np.int32, np.int64)):
        return int(val)
    return val

def predict_player(player_id: int):
    dataset = HockeyDataset(CSV_FILE, seq_len=SEQ_LEN)
    scalers = dataset.get_scalers()
    target_scaler = scalers["targets"]
    TARGET_COLS = dataset.get_target_cols()
    # make sure the player_id type matches df
    df = dataset.df
    if "playerId" not in df.columns:
        raise KeyError("playerId column not in dataframe")
    player_games = df[df["playerId"] == player_id].sort_values("date")
    if len(player_games) < SEQ_LEN:
        raise ValueError(f"not enough games for player {player_id}")
    feature_cols = dataset.feature_cols
    last_seq = player_games[feature_cols].values[-SEQ_LEN:]

    X = torch.tensor(last_seq, dtype=torch.float32).unsqueeze(0)

    model = HockeyLSTM(input_dim=X.shape[2], output_dim=len(TARGET_COLS))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
    model.eval()

    with torch.no_grad():
        pred_scaled = model(X).cpu().numpy()
        pred_real = target_scaler.inverse_transform(pred_scaled)
        pred_real = np.clip(pred_real, 0.0, None)

    # build a regular python dict of floats
    preds = {}
    pred_row = np.atleast_2d(pred_real)[-1]
    for i, col in enumerate(TARGET_COLS):
        preds[col] = float(pred_row[i])
    return {"player_id": int(player_id), "predictions": preds}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict next-game stats for an NHL player")
    parser.add_argument("player_id", type=int, help="NHL Player ID (int)")
    args = parser.parse_args()
    try:
        out = predict_player(args.player_id)
        print(json.dumps(out, indent=2))
        sys.exit(0)
    except Exception as e:
        # ensure JSON is printed
        err = {"error": str(e)}
        print(json.dumps(err, indent=2))
        # write a traceback to stderr just in case
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)