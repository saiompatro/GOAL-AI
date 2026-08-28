"""Build data/raw/wc2026_schedule.csv from the openfootball 2026 World Cup JSON.

Source: https://github.com/openfootball/world-cup.json (public domain, no key).
The JSON is a flat list of 104 matches with fields: round, date, time, team1,
team2, group, ground (a city string). We map each ``ground`` city onto the
stadium names used in ``wc2026_venues.csv`` so the prediction page can pull
ground conditions + match-day weather.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "raw" / "openfootball_wc2026.json"
OUT = ROOT / "data" / "raw" / "wc2026_schedule.csv"

# openfootball "ground" city string -> our stadium name (wc2026_venues.csv)
CITY_TO_STADIUM = {
    "mexico city": "Estadio Azteca",
    "guadalajara": "Estadio Akron", "guadalajara (zapopan)": "Estadio Akron", "zapopan": "Estadio Akron",
    "monterrey": "Estadio BBVA", "monterrey (guadalupe)": "Estadio BBVA", "guadalupe": "Estadio BBVA",
    "toronto": "BMO Field", "vancouver": "BC Place",
    "new york": "MetLife Stadium", "new york new jersey": "MetLife Stadium",
    "new york/new jersey": "MetLife Stadium", "new york/new jersey (east rutherford)": "MetLife Stadium",
    "east rutherford": "MetLife Stadium",
    "dallas": "AT&T Stadium", "dallas (arlington)": "AT&T Stadium", "arlington": "AT&T Stadium",
    "houston": "NRG Stadium", "atlanta": "Mercedes-Benz Stadium",
    "philadelphia": "Lincoln Financial Field",
    "san francisco": "Levi's Stadium", "san francisco bay area": "Levi's Stadium",
    "san francisco bay area (santa clara)": "Levi's Stadium", "bay area": "Levi's Stadium",
    "santa clara": "Levi's Stadium",
    "seattle": "Lumen Field",
    "los angeles": "SoFi Stadium", "los angeles (inglewood)": "SoFi Stadium", "inglewood": "SoFi Stadium",
    "boston": "Gillette Stadium", "boston (foxborough)": "Gillette Stadium", "foxborough": "Gillette Stadium",
    "miami": "Hard Rock Stadium", "miami (miami gardens)": "Hard Rock Stadium", "miami gardens": "Hard Rock Stadium",
    "kansas city": "Arrowhead Stadium",
}


def _team(x) -> str:
    if isinstance(x, dict):
        return x.get("name") or x.get("code") or "TBD"
    return str(x).strip() if x else "TBD"


def _stadium(ground: str) -> str:
    g = str(ground or "").strip().lower()
    if g in CITY_TO_STADIUM:
        return CITY_TO_STADIUM[g]
    # strip a parenthetical and retry on the base city
    base = g.split("(")[0].strip()
    return CITY_TO_STADIUM.get(base, "")


def main() -> int:
    if not SRC.exists():
        print(f"Missing {SRC}. Run `python ml/scripts/fetch_fifa_data.py` first.")
        return 1

    data = json.loads(SRC.read_text(encoding="utf-8"))
    matches = data.get("matches", [])
    rows, unmapped = [], set()
    for i, m in enumerate(matches, start=1):
        ground = m.get("ground", "")
        stad = _stadium(ground)
        if not stad and ground:
            unmapped.add(ground)
        rows.append({
            "match_no": m.get("num", i),
            "date": m.get("date", ""),
            "stage": m.get("group") or m.get("round", ""),
            "home": _team(m.get("team1")),
            "away": _team(m.get("team2")),
            "venue": stad,
            "kickoff_local": m.get("time", ""),
        })

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["match_no", "date", "stage", "home", "away",
                                          "venue", "kickoff_local"])
        w.writeheader()
        w.writerows(rows)

    mapped = sum(1 for r in rows if r["venue"])
    print(f"Wrote {len(rows)} fixtures -> {OUT}  ({mapped} venue-mapped)")
    if unmapped:
        print("Unmapped ground strings (add to CITY_TO_STADIUM):", sorted(unmapped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
