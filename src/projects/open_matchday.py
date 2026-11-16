"""Current-season results with shot counts, and upcoming fixtures, from open-matchday.

https://github.com/oladeeayo/open-matchday compiles one results file and one
fixtures file per competition for the season in progress and refreshes them
daily. It is read from raw.githubusercontent.com, so it stays reachable where
football-data.co.uk is not, and unlike the OpenFootball mirror it carries total
shots for both sides. It publishes the 2026-27 season only, so it cannot be
checked against an earlier installed season; a refresh instead stops if it
disagrees with a score that is already installed.

Its terms (DISCLAIMER.md in that repository) allow non-commercial use with
attribution and give no warranty of accuracy.

Each row is in the spelling of whichever upstream provider supplied it, so the
name map holds every spelling seen and also accepts the football-data.co.uk
names used in data/analytics and data/club. An unknown club raises instead of
silently creating a second identity for a team.
"""
from datetime import timedelta
from io import StringIO

import pandas as pd
import requests

REPO = "https://github.com/oladeeayo/open-matchday"
BASE = "https://raw.githubusercontent.com/oladeeayo/open-matchday/master/data"
LABEL = "open-matchday"
TERMS = "open-matchday data is free for non-commercial use with attribution and comes without warranty."
FIRST_YEAR = 2026  # only the season in progress is published

# competition slug -> (data folder, {source spelling: dataset name})
LEAGUES = {
    "bundesliga": ("GER_1_bundesliga", {
        "1. FC Köln": "FC Koln", "1. FC Union Berlin": "Union Berlin", "1. FSV Mainz 05": "Mainz",
        "Bayer 04 Leverkusen": "Leverkusen", "Borussia Dortmund": "Dortmund",
        "Borussia Mönchengladbach": "M'gladbach", "Eintracht Frankfurt": "Ein Frankfurt",
        "FC Augsburg": "Augsburg", "FC Bayern München": "Bayern Munich", "FC Schalke 04": "Schalke 04",
        "Hamburger SV": "Hamburg", "RB Leipzig": "RB Leipzig", "SC Freiburg": "Freiburg",
        "SC Paderborn 07": "Paderborn", "SV 07 Elversberg": "Elversberg", "SV Werder Bremen": "Werder Bremen",
        "TSG Hoffenheim": "Hoffenheim", "VfB Stuttgart": "Stuttgart",
    }),
}


def _code(year):
    return f"{year % 100:02}{(year + 1) % 100:02}"


def season_url(slug, year):
    """Browsable folder for one competition, recorded as the dataset's source URL."""
    return f"{REPO}/tree/master/data/{LEAGUES[slug][0]}"


def file_url(slug, year, kind):
    return f"{BASE}/{LEAGUES[slug][0]}/{kind}_{_code(year)}.csv"


def _namer(slug):
    names = LEAGUES[slug][1]
    known = set(names.values())

    def name(raw):
        raw = str(raw).strip()
        if raw in names:
            return names[raw]
        if raw in known:  # a row supplied by football-data.co.uk already has the dataset spelling
            return raw
        raise ValueError(f"Unmapped open-matchday club for {slug}: {raw}")
    return name


def parse_results(slug, year, frame):
    """Finished matches as dataset rows; shots stay empty where the source has none."""
    name = _namer(slug)
    season = f"{year}-{str(year + 1)[-2:]}"
    rows = []
    for match in frame.to_dict("records"):
        if pd.isna(match.get("ft_home")) or pd.isna(match.get("ft_away")):
            raise ValueError(f"open-matchday result without a score: {match.get('home')} v {match.get('away')}")
        row = dict(date=pd.Timestamp(match["date"]).strftime("%Y-%m-%d"), season=season,
                   home_team=name(match["home"]), away_team=name(match["away"]),
                   home_score=int(match["ft_home"]), away_score=int(match["ft_away"]), neutral=0)
        shots = [match.get("home_shots"), match.get("away_shots")]
        row["home_shots"], row["away_shots"] = (None, None) if any(pd.isna(s) for s in shots) else map(int, shots)
        rows.append(row)
    pairs = [(r["home_team"], r["away_team"]) for r in rows]
    if len(set(pairs)) != len(pairs):
        raise ValueError(f"open-matchday lists a {slug} fixture twice")
    return rows


def parse_fixtures(slug, frame):
    """Unplayed matches in the shape the workspace fixture panel reads (utcDate, homeTeam, awayTeam).

    The source gives kick-off times at a fixed UTC+1; a missing time is placed
    at the end of the day so the fixture is not dropped before it is played.
    """
    name = _namer(slug)
    matches = []
    for match in frame.to_dict("records"):
        time = match.get("time")
        if pd.isna(time) or not str(time).strip():
            kickoff = pd.Timestamp(f"{match['date']} 23:59")
        else:
            kickoff = pd.Timestamp(f"{match['date']} {str(time).strip()}") - timedelta(hours=1)
        matches.append(dict(utcDate=kickoff.strftime("%Y-%m-%dT%H:%M:%SZ"), matchday=int(match["gw"]),
                            homeTeam={"name": name(match["home"])}, awayTeam={"name": name(match["away"])}))
    matches.sort(key=lambda m: m["utcDate"])
    return matches


def _read(slug, year, kind):
    """One published file as a frame, or None when the season is not published."""
    if slug not in LEAGUES:
        raise ValueError(f"No open-matchday mapping for {slug}")
    r = requests.get(file_url(slug, year, kind), timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))


def fetch_season(slug, year):
    """Completed matches for one season as dataset rows (empty list if the season is not published)."""
    frame = _read(slug, year, "results")
    return [] if frame is None else parse_results(slug, year, frame)


def fetch_fixtures(slug, year):
    frame = _read(slug, year, "fixtures")
    return [] if frame is None else parse_fixtures(slug, frame)
