import os
import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)
SEASON = "20242025"
# stats for rolling averages
PLAYER_STATS = ["goals", "assists", "points", "shots", "ppGoals",
                "shGoals", "hits", "blocked", "faceoffPct", "timeOnIce"]
TEAM_STATS = ["goals", "assists", "points", "shots", "ppGoals",
              "shGoals", "hits", "blocked"]

# add the per game team and opponent totals to every player row
def add_team_context(df: pd.DataFrame) -> pd.DataFrame:
    # team totals
    team_stats = (
        df.groupby(["gameId", "team"])[TEAM_STATS]
        .sum()
        .reset_index()
        .rename(columns={**{col: f"team_{col}" for col in TEAM_STATS}})
    )
    # opponent totals
    opp_stats = (
        df.groupby(["gameId", "opponent"])[TEAM_STATS]
        .sum()
        .reset_index()
        .rename(columns={**{col: f"opp_{col}" for col in TEAM_STATS}, "opponent": "team"})
    )
    # combine both into the player rows
    df = df.merge(team_stats, on=["gameId", "team"], how="left")
    df = df.merge(opp_stats, on=["gameId", "team"], how="left")
    return df

# calculate the rolling averages of the player stats over last X amount of games
def add_player_rolling(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    df = df.sort_values(["playerId", "date"])
    for stat in PLAYER_STATS:
        df[f"{stat}_roll{window}"] = (
            df.groupby("playerId")[stat]
            .transform(lambda x: x.shift().rolling(window, min_periods=1).mean())
        )
    return df

# calculate the rolling averages of the team and opponent stats
def add_team_rolling(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    df = df.sort_values(["team", "date"])
    # team rolling averages
    for stat in TEAM_STATS:
        col = f"team_{stat}"
        if col in df.columns:
            df[f"{col}_roll{window}"] = (
                df.groupby("team")[col]
                .transform(lambda x: x.shift().rolling(window, min_periods=1).mean())
            )
        else:
            df[f"{col}_roll{window}"] = 0.0
    # opponent rolling averages
    for stat in TEAM_STATS:
        col = f"opp_{stat}"
        if col in df.columns:
            df[f"{col}_roll{window}"] = (
                df.groupby("team")[col]
                .transform(lambda x: x.shift().rolling(window, min_periods=1).mean())
            )
        else:
            df[f"{col}_roll{window}"] = 0.0
    return df

def main():
    # define the file directories
    infile = os.path.join(RAW_DIR, f"nhl_game_logs_{SEASON}.csv")
    outfile = os.path.join(PROCESSED_DIR, f"nhl_game_logs_processed_{SEASON}.csv")

    print(f"loading {infile}")
    if not os.path.exists(infile):
        raise FileNotFoundError(f"{infile} not found")
    # make sure that date is parsed
    df = pd.read_csv(infile, parse_dates=["date"])
    print(f"raw csv rows loaded: {len(df)}")

    print("adding team and opponent context...")
    df = add_team_context(df)
    print("team and opponent columns added :)")

    print("adding player rolling averages...")
    df = add_player_rolling(df, window=5)
    print("player rolling averages added :)")

    print("adding team & opponent rolling averages...")
    df = add_team_rolling(df, window=5)
    print("team and opponent rolling averages added :)")

    print(f"saving processed file to {outfile} (rows: {len(df)})")
    df.to_csv(outfile, index=False, encoding="utf-8")
    print("done :)")

if __name__ == "__main__":
    main()