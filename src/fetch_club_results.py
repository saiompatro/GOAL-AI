"""Fetch historical club-league match results for the league predictor.

Pulls season-by-season results from the footballcsv/cache.footballdata GitHub
mirror of football-data.co.uk (results back to 1993-94, updated ~weekly) and
writes one consolidated CSV per league to data/club/<key>_results.csv.

Add a league by adding an entry to LEAGUES — `code` is the footballcsv file
stem for that competition (see footballcsv/cache.footballdata's README for
the full list: eng.1 Premier League, es.1 La Liga, it.1 Serie A, de.1
Bundesliga, fr.1 Ligue 1, ...).
"""
import os
import csv
import datetime
import time
import requests

BASE = "https://raw.githubusercontent.com/footballcsv/cache.footballdata/master"
FIRST_SEASON = 1993
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "club")

LEAGUES = {
    "premier_league": {"name": "Premier League", "country": "England", "code": "eng.1"},
    "la_liga": {"name": "La Liga", "country": "Spain", "code": "es.1"},
}


def season_label(start_year):
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _get_with_retries(url, attempts=3, timeout=30):
    """GET with a few retries — the footballcsv mirror occasionally 404s on a
    season that exists (transient), so a single failed request shouldn't be
    treated as "season not in the mirror"."""
    last = None
    for i in range(attempts):
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r
        last = r
        if i < attempts - 1:
            time.sleep(1.5 * (i + 1))
    return last


def fetch_league(code):
    """All available season files for a footballcsv league code, oldest first."""
    rows = []
    this_year = datetime.date.today().year
    for year in range(FIRST_SEASON, this_year + 1):
        season = season_label(year)
        r = _get_with_retries(f"{BASE}/{season}/{code}.csv")
        if r.status_code != 200:
            continue
        for row in csv.DictReader(r.text.splitlines()):
            ft = (row.get("FT") or "").strip()
            if "-" not in ft:
                continue  # postponed / unplayed
            hg, ag = ft.split("-", 1)
            try:
                hg, ag = int(hg), int(ag)
            except ValueError:
                continue
            date = datetime.datetime.strptime(row["Date"].strip(), "%a %b %d %Y").date()
            rows.append({"date": date.isoformat(), "season": season,
                        "home_team": row["Team 1"].strip(), "away_team": row["Team 2"].strip(),
                        "home_score": hg, "away_score": ag})
    rows.sort(key=lambda r: r["date"])
    return rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for key, info in LEAGUES.items():
        rows = fetch_league(info["code"])
        if not rows:
            print(f"{info['name']}: no data fetched, skipping")
            continue
        seasons_fetched = {r["season"] for r in rows}
        first_year = int(rows[0]["season"][:4])
        expected = {season_label(y) for y in range(first_year, datetime.date.today().year + 1)}
        gaps = sorted(expected - seasons_fetched)
        if gaps:
            print(f"{info['name']}: WARNING missing seasons after retries: {gaps}")
        out = os.path.join(OUT_DIR, f"{key}_results.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "season", "home_team", "away_team",
                                              "home_score", "away_score"])
            w.writeheader()
            w.writerows(rows)
        seasons = sorted({r["season"] for r in rows})
        print(f"{info['name']}: {len(rows)} matches, seasons {seasons[0]}..{seasons[-1]} -> {out}")


if __name__ == "__main__":
    main()
