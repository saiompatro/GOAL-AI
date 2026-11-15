"""Premier League results with shot counts from the FPL-Elo-Insights repository.

https://github.com/olbauday/FPL-Elo-Insights publishes one matches.csv per
gameweek and refreshes twice a day. It is read from raw.githubusercontent.com,
so it stays reachable where football-data.co.uk is not, and unlike the
OpenFootball mirror it carries total shots for both sides.

Checked against the installed football-data.co.uk 2025-26 season: all 380
fixtures and dates agree, 379 scores agree, and 98.5% of shot counts are
identical (the rest differ by one or two).

Clubs are identified by their Premier League team code and mapped to the
football-data.co.uk spellings used in data/analytics and data/club. An unknown
code raises instead of silently creating a second identity for a club.
"""
from io import StringIO
from urllib.parse import quote

import pandas as pd
import requests

REPO = "https://github.com/olbauday/FPL-Elo-Insights"
BASE = "https://raw.githubusercontent.com/olbauday/FPL-Elo-Insights/main/data"
LABEL = "FPL-Elo-Insights"
FIRST_YEAR = 2025  # earliest season published in the per-tournament layout
GAMEWEEKS = range(1, 39)

# competition slug -> (tournament folder, {Premier League team code: dataset name})
LEAGUES = {
    "premier-league": ("Premier League", {
        1: "Man United", 2: "Leeds", 3: "Arsenal", 4: "Newcastle", 6: "Tottenham", 7: "Aston Villa",
        8: "Chelsea", 9: "Coventry", 11: "Everton", 14: "Liverpool", 17: "Nott'm Forest", 21: "West Ham",
        31: "Crystal Palace", 36: "Brighton", 39: "Wolves", 40: "Ipswich", 43: "Man City", 54: "Fulham",
        56: "Sunderland", 88: "Hull", 90: "Burnley", 91: "Bournemouth", 94: "Brentford",
    }),
}


def season_folder(year):
    return f"{year}-{year + 1}"


def season_url(slug, year):
    """Browsable folder for one season, recorded as the dataset's source URL."""
    return f"{REPO}/tree/main/data/{season_folder(year)}/By%20Tournament/{quote(LEAGUES[slug][0])}"


def gameweek_url(slug, year, gameweek):
    return f"{BASE}/{season_folder(year)}/By%20Tournament/{quote(LEAGUES[slug][0])}/GW{gameweek}/matches.csv"


def parse_matches(slug, year, frame):
    """Finished matches of one gameweek file as dataset rows."""
    names = LEAGUES[slug][1]
    season = f"{year}-{str(year + 1)[-2:]}"
    rows = []
    for match in frame.to_dict("records"):
        if str(match.get("finished")).strip().lower() != "true":
            continue
        values = [match.get(col) for col in ("home_team", "away_team", "home_score", "away_score")]
        if any(pd.isna(v) for v in values):
            raise ValueError(f"Finished {slug} match without teams or score: {match.get('match_id')}")
        home, away = int(values[0]), int(values[1])
        unknown = [code for code in (home, away) if code not in names]
        if unknown:
            raise ValueError(f"Unmapped team code for {slug}: {unknown} in {match.get('match_id')}")
        # football-data.co.uk dates are UK-local; kick-off times here are UTC.
        date = pd.Timestamp(match["kickoff_time"], tz="UTC").tz_convert("Europe/London").strftime("%Y-%m-%d")
        row = dict(date=date, season=season, home_team=names[home], away_team=names[away],
                   home_score=int(values[2]), away_score=int(values[3]), neutral=0)
        shots = [match.get("home_total_shots"), match.get("away_total_shots")]
        # A match whose statistics are not processed yet keeps empty shots; nothing is estimated.
        row["home_shots"], row["away_shots"] = (None, None) if any(pd.isna(s) for s in shots) else map(int, shots)
        rows.append(row)
    return rows


def fetch_season(slug, year):
    """Completed matches for one season as dataset rows (empty list if the season is not published)."""
    if slug not in LEAGUES:
        raise ValueError(f"No FPL-Elo-Insights mapping for {slug}")
    rows = []
    for gameweek in GAMEWEEKS:
        r = requests.get(gameweek_url(slug, year, gameweek), timeout=30)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        rows += parse_matches(slug, year, pd.read_csv(StringIO(r.text)))
    return rows


STATUS = {"i": "injured", "d": "doubtful", "s": "suspended"}
POSITIONS = {"Goalkeeper": "GK", "Defender": "DF", "Midfielder": "MF", "Forward": "FW"}


def parse_availability(slug, stats, players):
    """(rows, gameweek): injured, doubtful and suspended players at the latest published gameweek.

    Status and news are the Premier League's own availability flags as
    republished by the source. Players flagged unavailable because they left
    the club are not an injury record and are left out.
    """
    names = LEAGUES[slug][1]
    gameweek = int(stats.gw.max())
    latest = stats[(stats.gw == gameweek) & stats.status.isin(STATUS)]
    merged = latest.merge(players, left_on="id", right_on="player_id", suffixes=("", "_player"))
    if len(merged) != len(latest):
        raise ValueError(f"{slug}: {len(latest) - len(merged)} flagged players are missing from players.csv")
    rows = []
    for p in merged.to_dict("records"):
        code = int(p["team_code"])
        if code not in names:
            raise ValueError(f"Unmapped team code for {slug}: {code} ({p['web_name']})")
        chance = p.get("chance_of_playing_next_round")
        rows.append(dict(player=p["web_name"], full_name=f"{p['first_name']} {p['second_name']}", team=names[code],
                         position=POSITIONS[p["position"]], status=STATUS[p["status"]],
                         chance_of_playing=None if pd.isna(chance) else int(chance),
                         news="" if pd.isna(p.get("news")) else str(p["news"]).strip(),
                         minutes=int(p["minutes"])))
    rows.sort(key=lambda r: (r["team"], r["status"], r["player"]))
    return rows, gameweek


def availability_urls(year):
    return [f"{BASE}/{season_folder(year)}/{name}.csv" for name in ("playerstats", "players")]


def fetch_availability(slug, year):
    if slug not in LEAGUES:
        raise ValueError(f"No FPL-Elo-Insights availability feed for {slug}")
    frames = []
    for url in availability_urls(year):
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        frames.append(pd.read_csv(StringIO(r.text)))
    return parse_availability(slug, *frames)
