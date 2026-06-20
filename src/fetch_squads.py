"""Fetch 2026 FIFA World Cup squads from Wikipedia.

Produces data/squads.csv with: team, player, position, age, caps, club, club_country.
This is the player layer: each player's strength is later proxied by his club's
Elo rating (built from real league/UCL results), weighted by caps and position.
"""
import re
import os
import sys
import csv
import requests

URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "squads.csv")

html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (research)"}, timeout=60).text

try:
    import pandas as pd
    from io import StringIO
    tables = pd.read_html(StringIO(html))
except Exception as e:
    print("read_html failed:", e)
    sys.exit(1)

# Team names appear as h3 headings in document order; squad tables follow each.
team_headings = re.findall(r'<h3[^>]*>(?:<[^>]+>)*([^<]+?)(?:<[^>]+>)*</h3>', html)
team_headings = [t.strip() for t in team_headings if t.strip() and "edit" not in t.lower()]

rows = []
ti = 0
squad_tables = [t for t in tables if "Player" in t.columns and "Pos." in "".join(map(str, t.columns))
                or ("Player" in t.columns and any("Club" in str(c) for c in t.columns))]
print(f"found {len(squad_tables)} squad-like tables, {len(team_headings)} headings")

for t in squad_tables:
    team = team_headings[ti] if ti < len(team_headings) else f"team_{ti}"
    ti += 1
    cols = {str(c).lower(): c for c in t.columns}
    def col(*names):
        for n in names:
            for k, orig in cols.items():
                if n in k:
                    return orig
        return None
    c_player, c_pos, c_caps, c_club, c_dob = col("player"), col("pos"), col("caps"), col("club"), col("date of birth", "age")
    for _, r in t.iterrows():
        player = str(r.get(c_player, "")).strip()
        if not player or player.lower() == "nan":
            continue
        club_raw = str(r.get(c_club, "")).strip()
        rows.append({
            "team": team,
            "player": re.sub(r"\(.*?\)", "", player).strip(" *"),
            "position": re.sub(r"^\d+", "", str(r.get(c_pos, ""))).strip(),
            "caps": re.sub(r"\D", "", str(r.get(c_caps, "0")))[:3] or "0",
            "club": club_raw,
        })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["team", "player", "position", "caps", "club"])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} players to {OUT}")
teams = sorted({r['team'] for r in rows})
print(f"{len(teams)} teams:", ", ".join(teams[:60]))
