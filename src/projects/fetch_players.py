"""Fetch observed football-data.org roster/scorer snapshots without invented stats.

Run: python src/projects/fetch_players.py la-liga --years 2022 2023 2024
These raw snapshots do not include the complete model inputs or market values.
Import a complete licensed player-season CSV with refresh_data.py --players.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from projects.competitions import COMPETITIONS, DATA, config

API = "https://api.football-data.org/v4"
PL_CODE = "PL"


def _token():
    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        env = Path(__file__).resolve().parents[2] / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition("=")
                if separator and key.strip() == "FOOTBALL_DATA_TOKEN":
                    token = value.strip().strip("\"'")
                    break
    return token


def _age(dob):
    if not dob:
        return None
    d = datetime.date.fromisoformat(dob)
    today = datetime.date.today()
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))


def fetch_resource(code, resource, season=None):
    token = _token()
    if not token:
        raise ValueError("Set FOOTBALL_DATA_TOKEN in .env to fetch football-data.org snapshots")
    response = requests.get(f"{API}/competitions/{code}/{resource}",
                            params={"season": season} if season is not None else {},
                            headers={"X-Auth-Token": token}, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_rosters(competition=PL_CODE, season=None):
    """Return provider roster observations; season stats are never fabricated."""
    payload = fetch_resource(competition, "teams", season)
    return [{"player": p.get("name"), "team": team.get("name"),
             "position": p.get("position"), "date_of_birth": p.get("dateOfBirth"),
             "provider_player_id": p.get("id")}
            for team in payload.get("teams", []) for p in team.get("squad", [])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition", nargs="?", default="premier-league", choices=COMPETITIONS)
    parser.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2024])
    args = parser.parse_args()
    c = config(args.competition)
    folder = DATA / "provider_snapshots"
    folder.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        for resource in ("teams", "scorers"):
            try:
                payload = fetch_resource(c["code"], resource, year)
            except (ValueError, requests.RequestException) as error:
                # Never overwrite a valid snapshot after an auth/rate-limit failure.
                print(f"Could not fetch {args.competition} {year} {resource}: {error}")
                return 1
            path = folder / f"{c['key']}_{year}_{resource}.json"
            path.write_text(json.dumps({"source": "football-data.org", "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "payload": payload}, indent=2), encoding="utf-8")
            print(f"Saved observed {year} {resource}: {path.name}")
    print("Snapshots saved. These do not supply minutes, all scouting stats, or market values.")
    print("Import complete observed player data with refresh_data.py --players; existing demo data was not overwritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
