import os
import requests
import pandas as pd
import json
from typing import Dict, List

DATA_DIR = "data/raw"
os.makedirs(DATA_DIR, exist_ok=True)
SEASON = "20242025"
MAX_GAMES = None  # change to None to get a full season of games
TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD",
    "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS",
    "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH"
]
BASE_URL = "https://api-web.nhle.com/v1"

# convert a MM:SS formatted string to seconds
def toi_to_seconds(toi_str: str) -> int:
    try:
        mins, secs = map(int, toi_str.split(":"))
        return mins * 60 + secs
    except Exception:
        return 0

def fetch_schedule(team_abbrev: str, season: str) -> List[Dict]:
    url = f"{BASE_URL}/club-schedule-season/{team_abbrev}/{season}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data.get("games", [])

def fetch_boxscore(game_id: str) -> Dict:
    url = f"{BASE_URL}/gamecenter/{game_id}/boxscore"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def parse_player_stats(game: Dict, game_data: Dict, player_map: Dict[int, str]) -> List[Dict]:
    game_id = game.get("id")
    game_date = game.get("gameDate")
    home_team = game.get("homeTeam", {}).get("abbrev")
    away_team = game.get("awayTeam", {}).get("abbrev")
    season = game.get("season")
    game_type = game.get("gameType")
    players = []
    stats_root = game_data.get("playerByGameStats", {})

    for side in ["homeTeam", "awayTeam"]:
        team = stats_root.get(side, {})
        team_abbrev = game.get(f"{side}", {}).get("abbrev")
        opponent = home_team if side == "awayTeam" else away_team

        for group in ["forwards", "defense", "goalies"]:
            for p in team.get(group, []):
                player_id = p.get("playerId")
                name = p.get("name", {}).get("default", "")
                # store the mapping if it's not already saved
                if player_id and name and player_id not in player_map:
                    player_map[player_id] = name
                toi_str = p.get("toi", "0:00")
                players.append({
                    "gameId": game_id,
                    "date": game_date,
                    "season": season,
                    "gameType": game_type,
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "isHome": (side == "homeTeam"),
                    "playerId": player_id,
                    "team": team_abbrev,
                    "opponent": opponent,
                    # stats
                    "goals": p.get("goals", 0),
                    "assists": p.get("assists", 0),
                    "points": p.get("points", 0),
                    "shots": p.get("sog", 0),
                    "ppGoals": p.get("powerPlayGoals", 0),
                    "shGoals": p.get("shorthandedGoals", 0),
                    "hits": p.get("hits", 0),
                    "blocked": p.get("blockedShots", 0),
                    "faceoffPct": p.get("faceoffWinningPctg", 0.0),
                    "timeOnIce": toi_to_seconds(toi_str),
                })
    return players

def main():
    all_rows = []
    seen_games = set()
    game_count = 0
    player_map = {}

    for team in TEAMS:
        print(f"Fetching schedule for {team}...")
        games = fetch_schedule(team, SEASON)

        for g in games:
            game_id = g.get("id")
            game_type = g.get("gameType")
            # include only regular season games: gameType == 2
            if game_type != 2:
                continue
            if game_id in seen_games:
                continue
            seen_games.add(game_id)
            game_count += 1
            if MAX_GAMES and game_count > MAX_GAMES:
                print("Reached MAX_GAMES limit, stopping")
                break
            try:
                box = fetch_boxscore(game_id)
                rows = parse_player_stats(g, box, player_map)
                all_rows.extend(rows)
                print(f"Processed game {game_id}, total rows: {len(all_rows)}")
            except Exception as e:
                print(f"Error fetching {game_id}: {e}")
        if MAX_GAMES and game_count >= MAX_GAMES:
            break
    # save the CSV (playerId only, not name)
    out_csv = os.path.join(DATA_DIR, f"nhl_game_logs_{SEASON}.csv")
    pd.DataFrame(all_rows).to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Saved {len(all_rows)} rows to {out_csv}")
    # save the player mapping
    with open("player_id_mapping.json", "w", encoding="utf-8") as f:
        json.dump(player_map, f, indent=2, ensure_ascii=False)
    print(f"Saved player_id_mapping.json with {len(player_map)} players")

if __name__ == "__main__":
    main()