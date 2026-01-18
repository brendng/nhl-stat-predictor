import os
import json
import time
import requests
from typing import Any, Dict

BASE_URL = "https://api-web.nhle.com/v1"
MAPPING_PATH = "player_id_mapping.json"
BACKUP_PATH = MAPPING_PATH + ".bak"
SLEEP_BETWEEN = 0.08  # seconds between requests
TIMEOUT = 8  # seconds for HTTP requests

def unwrap_name_val(val: Any) -> str:
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        for key in ("default", "fullName", "displayName", "en", "value"):
            v = val.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""

def fetch_landing(session: requests.Session, pid: int) -> Dict:
    url = f"{BASE_URL}/player/{pid}/landing"
    try:
        r = session.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        first = unwrap_name_val(data.get("firstName") or data.get("first") or data.get("givenName"))
        last = unwrap_name_val(data.get("lastName") or data.get("last") or data.get("familyName"))
        if first or last:
            full = " ".join([p for p in (first, last) if p]).strip()
        else:
            full = unwrap_name_val(data.get("fullName") or data.get("displayName") or data.get("name"))
        team = data.get("currentTeamAbbrev") or (data.get("currentTeam") or {}).get("abbrev") or None
        return {"id": pid, "fullName": full or "", "team": team}
    except Exception:
        return {"id": pid, "fullName": "", "team": None}

def load_mapping(path: str) -> Dict[int, Dict]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return {int(k): {"shortName": v} for k, v in data.items()}
    elif isinstance(data, list):
        out = {}
        for item in data:
            pid = int(item.get("id") or item.get("playerId"))
            out[pid] = item
        return out
    else:
        raise RuntimeError("unexpected player_id_mapping.json format")

def main():
    if not os.path.exists(MAPPING_PATH):
        print("player_id_mapping.json not found")
        return
    mapping = load_mapping(MAPPING_PATH)
    session = requests.Session()
    session.headers.update({"User-Agent": "nhl-stat-predictor/upgrade-simple/1.0"})
    upgraded = {}
    total = len(mapping)
    i = 0
    for pid in sorted(mapping.keys()):
        i += 1
        short = mapping[pid].get("shortName") or mapping[pid].get("fullName") or ""
        print(f"[{i}/{total}] {pid} -> fetching landing (current: '{short}')")
        landing = fetch_landing(session, pid)
        # if landing has no fullName, preserve existing short as fullName
        full = landing.get("fullName") or short or ""
        team = landing.get("team") or mapping[pid].get("team") or None
        upgraded[pid] = {"id": int(pid), "fullName": full, "team": team}
        time.sleep(SLEEP_BETWEEN)
    # backup original and write new list format
    try:
        if os.path.exists(MAPPING_PATH):
            os.replace(MAPPING_PATH, BACKUP_PATH)
            print(f"backed up the original mapping to {BACKUP_PATH}")
    except Exception:
        pass
    out_list = [upgraded[pid] for pid in sorted(upgraded.keys())]
    with open(MAPPING_PATH, "w", encoding="utf-8") as fh:
        json.dump(out_list, fh, indent=2, ensure_ascii=False)
    print(f"outputted the updated mapping with {len(out_list)} players to {MAPPING_PATH}")

if __name__ == "__main__":
    main()