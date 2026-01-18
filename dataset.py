import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import StandardScaler

# safe scaler
class SafeStandardScaler(StandardScaler):
    def transform(self, X, copy=None):
        X = super().transform(X, copy)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        return X
    def fit_transform(self, X, y=None):
        X = super().fit_transform(X, y)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        return X

class HockeyDataset(Dataset):
    def __init__(self, csv_file, seq_len=5, target_cols=None):
        # load and ensure proper ordering by player/date so sequences are adjacent per each player
        self.df = pd.read_csv(csv_file, parse_dates=["date"])
        self.df = self.df.sort_values(["playerId", "date"]).reset_index(drop=True)
        # get numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        # default base player stat targets (don't select rolling/team/opp cols as targets)
        DEFAULT_TARGET_BASES = [
            "goals", "assists", "points", "shots", "ppGoals",
            "shGoals", "hits", "blocked", "faceoffPct", "timeOnIce"
        ]
        id_cols = {"playerId", "gameId", "season"}
        # if the explicit target_cols are provided, use them (filtered to numeric & present).
        if target_cols is not None:
            candidate_targets = [c for c in target_cols if c in numeric_cols]
        else:
            # prefer the base stat names, fall back to numeric columns that don't look like team/opp/rolling features
            candidate_targets = [c for c in numeric_cols if c in DEFAULT_TARGET_BASES]
            if not candidate_targets:
                candidate_targets = [
                    c for c in numeric_cols
                    if not any(tok in c for tok in ["_roll", "team_", "opp_"]) and c not in id_cols
                ]
        # drop all targets with no variance or all NaN
        self.target_cols = [
            c for c in candidate_targets
            if c in self.df.columns and self.df[c].dropna().nunique() > 1
        ]
        if not self.target_cols:
            raise ValueError(
                "no valid target columns were found :( numeric_cols=%s. "
                "passing explicit target_cols to HockeyDataset if needed" % (numeric_cols,)
            )
        # feature columns = all numeric except targets and identifier columns, remove constant columns
        self.feature_cols = [
            c for c in numeric_cols
            if c not in self.target_cols and c not in id_cols and self.df[c].dropna().nunique() > 1
        ]
        if not self.feature_cols:
            raise ValueError(
                "no valid feature columns found :( after excluding targets and ids there aren't any numeric features "
                "targets selected: %s. numeric cols: %s" % (self.target_cols, numeric_cols)
            )
        # store the sequence length
        self.seq_len = seq_len
        # normalization scalers — use SafeStandardScaler to avoid NaN/inf issues
        self.feature_scaler = SafeStandardScaler()
        self.target_scaler = SafeStandardScaler()
        # replace NaNs with 0 before fitting the scalers (scikit-learn doesn't like NaNs in fit)
        self.df[self.feature_cols] = self.df[self.feature_cols].fillna(0.0)
        self.df[self.target_cols] = self.df[self.target_cols].fillna(0.0)
        # fit the scalers and replace in-place with the scaled values
        self.df[self.feature_cols] = self.feature_scaler.fit_transform(self.df[self.feature_cols])
        self.df[self.target_cols] = self.target_scaler.fit_transform(self.df[self.target_cols])
    def __len__(self):
        return len(self.df)
    def __getitem__(self, idx):
        # grab sequence ending at idx (since df is sorted by playerId/date, sequences are per-player)
        start = max(0, idx - self.seq_len + 1)
        end = idx + 1
        seq_features = self.df[self.feature_cols].iloc[start:end].values
        seq_targets = self.df[self.target_cols].iloc[end - 1].values
        # pad if the sequence is shorter than seq_len
        if len(seq_features) < self.seq_len:
            pad = np.zeros((self.seq_len - len(seq_features), len(self.feature_cols)))
            seq_features = np.vstack([pad, seq_features])
        return (
            torch.tensor(seq_features, dtype=torch.float32),
            torch.tensor(seq_targets, dtype=torch.float32),
        )
    def get_scalers(self):
        return {"features": self.feature_scaler, "targets": self.target_scaler}
    def get_target_cols(self):
        return self.target_cols