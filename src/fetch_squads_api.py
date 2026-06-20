"""Authoritative 2026 World Cup squads from football-data.org.

Replaces the one-off Wikipedia scrape (which froze squads at announcement time
and so still listed withdrawn players like Wataru Endo). Run:

    set FOOTBALL_DATA_TOKEN=<your key>   &  python fetch_squads_api.py
    # or pass it inline:  python fetch_squads_api.py <your key>

Writes data/squads.csv (same schema as before: team, player, position, caps,
club) so the rest of the pipeline is unchanged. Caps aren't in the API, so we
preserve caps from the previous squads.csv where the player still appears, else
0. Free tier allows 10 req/min, so per-team calls are throttled.
"""
import os
import sys
import csv
import time
import re
import unicodedata
import requests

BASE = "https://api.football-data.org/v4"
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(DATA, "squads.csv")
PREV = os.path.join(DATA, "squads_wikipedia_backup.csv")  # source of club/caps

# API team names -> the canonical names used by the Elo state, geo.py and the UI
TEAM_CANON = {
    "Czechia": "Czech Republic", "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde", "Congo DR": "DR Congo",
    "IR Iran": "Iran", "Korea Republic": "South Korea",
}


def _ascii(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn")


def name_key(s):
    """Order/accent-insensitive key so 'Wataru Endo' == 'Endo Wataru'."""
    toks = re.findall(r"[a-z]+", _ascii(s).lower())
    return " ".join(sorted(toks))

POS_MAP = {"Goalkeeper": "GK", "Defence": "DF", "Midfield": "MF", "Offence": "FW",
           "Centre-Back": "DF", "Left-Back": "DF", "Right-Back": "DF",
           "Defensive Midfield": "MF", "Central Midfield": "MF",
           "Attacking Midfield": "MF", "Left Winger": "FW", "Right Winger": "FW",
           "Centre-Forward": "FW"}


def get(url, token, tries=4):
    for i in range(tries):
        r = requests.get(url, headers={"X-Auth-Token": token}, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:                       # rate limited
            time.sleep(int(r.headers.get("Retry-After", 30)) + 1)
            continue
        if r.status_code == 403:
            raise SystemExit("403 Forbidden — bad/missing API key, or your tier "
                             "does not include World Cup squads.")
        time.sleep(5)
    raise SystemExit(f"failed: {url} (last status {r.status_code})")


def load_prev():
    """Map (canonical_team, name_key) -> (caps, club) from the backup squads.
    The API lists players under their national team and omits club, so we
    carry club/caps forward for continuing players (replacements get blanks)."""
    prev = {}
    if os.path.exists(PREV):
        import pandas as pd
        for r in pd.read_csv(PREV).itertuples():
            team = TEAM_CANON.get(str(r.team), str(r.team))
            prev[(team, name_key(r.player))] = (r.caps, str(r.club))
    return prev


def main():
    from config import get_token
    token = sys.argv[1].strip() if len(sys.argv) > 1 else get_token()
    if not token:
        raise SystemExit("No API key. Pass it as an arg, set FOOTBALL_DATA_TOKEN, "
                         "or add it to the project .env file.")

    comp = get(f"{BASE}/competitions/WC/teams", token)
    teams = comp.get("teams", [])
    print(f"{len(teams)} teams in WC competition")
    prev = load_prev()
    rows, n_squad, n_new = [], 0, 0

    for t in teams:
        name = TEAM_CANON.get(t["name"], t["name"])
        squad = t.get("squad") or []
        if not squad:                                  # bulk call omitted squad -> fetch team
            squad = get(f"{BASE}/teams/{t['id']}", token).get("squad", [])
            time.sleep(6)                              # 10 req/min throttle
        if squad:
            n_squad += 1
        for p in squad:
            pname = p.get("name", "").strip()
            if not pname:
                continue
            caps, club = prev.get((name, name_key(pname)), (0, ""))
            api_club = (p.get("currentTeam") or {}).get("name", "") if isinstance(p.get("currentTeam"), dict) else ""
            if not api_club and not club:
                n_new += 1                             # replacement player, club unknown
            rows.append({
                "team": name,
                "player": pname,
                "position": POS_MAP.get(p.get("position") or "", p.get("position") or ""),
                "caps": caps,
                "club": api_club or club,
            })
        print(f"  {name:24s} {len(squad)} players")

    if n_squad == 0:
        raise SystemExit("API returned no squad data on your tier. Keep the "
                         "existing squads.csv or use the news-based detector.")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["team", "player", "position", "caps", "club"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {len(rows)} players across {n_squad} teams to {OUT}")
    if n_new:
        print(f"  ({n_new} players new vs previous list -> club unknown, median rating)")
    print("next: python squad_strength.py   (re-rate squads & key players)")


if __name__ == "__main__":
    main()
