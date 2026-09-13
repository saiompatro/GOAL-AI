"""Fetch historical club-league match results for the league predictor.

Pulls season-by-season results from the footballcsv/cache.footballdata GitHub
mirror of football-data.co.uk (results back to 1993-94, updated ~weekly) and
writes one consolidated CSV per league to data/club/<key>_results.csv.

Add a league by adding an entry to LEAGUES — `code` is the footballcsv file
stem for that competition (see footballcsv/cache.footballdata's README for
the full list: eng.1 Premier League, es.1 La Liga, it.1 Serie A, de.1
Bundesliga, fr.1 Ligue 1, ...).

`home_adv` is a per-league Elo constant (the home-advantage rating bonus),
fit once with `fit_home_advantage()` below from that league's own results
and hardcoded here, rather than reusing the Premier League's eyeballed
70 for every league — the historical home-win rate that implies genuinely
differs by league (e.g. Ligue 1 and La Liga run several points stronger
than the Bundesliga in this data).
"""
import os
import csv
import math
import datetime
import requests

BASE = "https://raw.githubusercontent.com/footballcsv/cache.footballdata/master"
FIRST_SEASON = 1993
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "club")

LEAGUES = {
    # premier_league keeps its original eyeballed 70/20 (baked into the
    # already-trained, documented model); fit_home_advantage() on its own
    # results actually comes out at ~61 — left as-is here to avoid silently
    # changing a shipped model's behaviour, but worth revisiting together
    # with a retrain if the Premier League model is ever retuned.
    "premier_league": {"name": "Premier League", "country": "England", "code": "eng.1",
                       "home_adv": 70, "k": 20},
    # home_adv below is fit_home_advantage() over each league's full results
    # history (see that function) — not eyeballed, since home-field strength
    # genuinely differs by league/country.
    "la_liga": {"name": "La Liga", "country": "Spain", "code": "es.1",
               "home_adv": 72, "k": 20},
    "serie_a": {"name": "Serie A", "country": "Italy", "code": "it.1",
               "home_adv": 67, "k": 20},
    "bundesliga": {"name": "Bundesliga", "country": "Germany", "code": "de.1",
                   "home_adv": 64, "k": 20},
    "ligue_1": {"name": "Ligue 1", "country": "France", "code": "fr.1",
               "home_adv": 73, "k": 20},
}


def season_label(start_year):
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def fetch_league(code):
    """All available season files for a footballcsv league code, oldest first."""
    rows = []
    this_year = datetime.date.today().year
    for year in range(FIRST_SEASON, this_year + 1):
        season = season_label(year)
        r = requests.get(f"{BASE}/{season}/{code}.csv", timeout=30)
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


def fit_home_advantage(rows):
    """Empirical Elo home-advantage bonus implied by a league's raw results,
    independent of the per-match ML model: if home and away sides were equal
    strength on average, home_score (win=1/draw=0.5/loss=0, averaged over all
    matches) is exactly the Elo win-expectancy of `home_adv` rating points at
    zero rating difference, so home_adv = 400 * log10(s / (1 - s)).
    Used once per new league to seed LEAGUES[...]['home_adv'] instead of
    reusing the Premier League's constant for every competition.
    """
    s = sum((1.0 if r["home_score"] > r["away_score"] else
             0.5 if r["home_score"] == r["away_score"] else 0.0) for r in rows) / len(rows)
    s = min(max(s, 0.01), 0.99)
    return 400 * math.log10(s / (1 - s))


def main():
    import sys
    os.makedirs(OUT_DIR, exist_ok=True)
    keys = sys.argv[1:] or list(LEAGUES.keys())
    for key in keys:
        info = LEAGUES[key]
        rows = fetch_league(info["code"])
        if not rows:
            print(f"{info['name']}: no data fetched, skipping")
            continue
        out = os.path.join(OUT_DIR, f"{key}_results.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "season", "home_team", "away_team",
                                              "home_score", "away_score"])
            w.writeheader()
            w.writerows(rows)
        seasons = sorted({r["season"] for r in rows})
        print(f"{info['name']}: {len(rows)} matches, seasons {seasons[0]}..{seasons[-1]} -> {out}"
              f"  (fit home_adv={fit_home_advantage(rows):.1f})")


if __name__ == "__main__":
    main()
