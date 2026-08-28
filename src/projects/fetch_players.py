"""Fetch Premier League player data for the player-level projects.

The real-data path. Pulls current Premier League squads (player names,
positions, ages, clubs) from the football-data.org API with the `requests`
library — the same free API the World Cup squad layer uses.

Honest note on free data: football-data.org's free tier gives rosters but not
per-player season statistics (goals/assists/shots/...) or market values. Those
need a paid stats provider (e.g. FBref/StatsBomb, Transfermarkt). So this
script pulls the *real roster* and then fills the statistical columns and the
market value from the same generative model as `gen_player_data.py`, keyed off
each real player's position and age. Point it at a richer feed and the
downstream projects (transfer_value, player_scouting) consume it unchanged.

With no token it prints how to get one and leaves the bundled sample dataset in
place, so nothing downstream breaks.

Run:  python -m projects.fetch_players        (needs FOOTBALL_DATA_TOKEN in .env)
"""
import csv
import datetime
import os

import requests

from projects.common import PLAYERS_CSV
from projects import gen_player_data as gen

API = "https://api.football-data.org/v4"
PL_CODE = "PL"  # football-data.org competition code for the Premier League


def _token():
    tok = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not tok:
        # allow a local .env without adding a hard python-dotenv dependency
        env = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        if os.path.exists(env):
            for line in open(env, encoding="utf-8"):
                if line.strip().startswith("FOOTBALL_DATA_TOKEN"):
                    tok = line.split("=", 1)[1].strip()
    return tok


def _age(dob):
    if not dob:
        return None
    try:
        d = datetime.date.fromisoformat(dob)
        t = datetime.date.today()
        return t.year - d.year - ((t.month, t.day) < (d.month, d.day))
    except ValueError:
        return None


_POS_MAP = {
    "Goalkeeper": "GK", "Defence": "DF", "Defender": "DF",
    "Midfield": "MF", "Midfielder": "MF", "Offence": "FW", "Forward": "FW",
    "Attacker": "FW", "Left-Back": "DF", "Right-Back": "DF",
    "Centre-Back": "DF", "Centre-Forward": "FW",
    "Central Midfield": "MF", "Attacking Midfield": "MF",
    "Defensive Midfield": "MF", "Left Winger": "FW", "Right Winger": "FW",
}


def fetch_rosters():
    """Real current Premier League squads from football-data.org."""
    tok = _token()
    if not tok:
        raise RuntimeError("no FOOTBALL_DATA_TOKEN")
    headers = {"X-Auth-Token": tok}
    teams = requests.get(f"{API}/competitions/{PL_CODE}/teams",
                         headers=headers, timeout=30).json().get("teams", [])
    roster = []
    for t in teams:
        for p in t.get("squad", []):
            pos = _POS_MAP.get((p.get("position") or "").strip(), "MF")
            roster.append({"player": p.get("name"), "team": t.get("name"),
                           "position": pos, "age": _age(p.get("dateOfBirth"))})
    return roster


def main():
    try:
        roster = fetch_rosters()
    except Exception as e:
        print(f"Live fetch unavailable ({e}).")
        print("Get a free token at https://www.football-data.org/client/register,")
        print("put FOOTBALL_DATA_TOKEN=... in .env, then re-run. Using the bundled")
        print("sample dataset for now (run `python -m projects.gen_player_data`).")
        if not os.path.exists(PLAYERS_CSV):
            gen.main()
        return

    # Fill stats + value from the generative model, keyed on the real roster.
    import random
    rng = random.Random(7)
    seasons = gen.SEASONS
    rows = []
    for r in roster:
        pos = r["position"]
        base_age = r["age"] or {"GK": 29, "DF": 27, "MF": 27, "FW": 26}[pos]
        quality = gen._quality(rng)
        for i, season in enumerate(seasons):
            age = base_age - (len(seasons) - 1 - i)
            arch = gen.ARCHETYPE[pos]
            minutes = int(max(500, rng.gauss(arch["base_minutes"], 500) * min(1.15, quality)))
            nineties = minutes / 90.0
            af = gen._age_factor(age)

            def stat(rate):
                per90 = max(0.0, rate * quality * af * rng.gauss(1.0, 0.18)
                            + rng.uniform(0.0, rate * 0.15))
                return round(per90 * nineties)

            g, a = stat(arch["goals90"]), stat(arch["assists90"])
            sh, kp = stat(arch["shots90"]), stat(arch["key_passes90"])
            dr = stat(arch["dribbles90"])
            tk, inn = stat(arch["tackles90"]), stat(arch["interceptions90"])
            pos_prem = {"FW": 1.35, "MF": 1.15, "DF": 0.9, "GK": 0.7}[pos]
            output = g * 2.2 + a * 1.4 + (sh + kp) * 0.15
            value = max(0.8, ((output * 1.1 + nineties * 1.6) * pos_prem
                              + max(0.0, 27 - age) * 1.4) * quality
                        * rng.uniform(0.82, 1.18) * 0.42)
            rows.append({"player": r["player"], "team": r["team"], "season": season,
                         "position": pos, "age": age, "minutes": minutes,
                         "goals": g, "assists": a, "shots": sh, "key_passes": kp,
                         "dribbles": dr, "tackles": tk, "interceptions": inn,
                         "market_value_eur_m": round(value, 1)})

    os.makedirs(os.path.dirname(PLAYERS_CSV), exist_ok=True)
    fields = ["player", "team", "season", "position", "age", "minutes", "goals",
              "assists", "shots", "key_passes", "dribbles", "tackles",
              "interceptions", "market_value_eur_m"]
    with open(PLAYERS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} player-seasons from {len(set(r['team'] for r in roster))} "
          f"real PL squads -> {PLAYERS_CSV}")


if __name__ == "__main__":
    main()
