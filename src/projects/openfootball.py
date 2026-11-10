"""Scores-only domestic results from the OpenFootball football.json mirror.

Used when football-data.co.uk has not been (or cannot be) downloaded for a
season. The feed has full-time scores only: no shots or possession, so those
columns stay empty for rows that come from here and are never estimated.

Team names are mapped to the football-data.co.uk spellings already used in
data/analytics and data/club. An unmapped club raises instead of silently
creating a second identity for the same team.
"""
import requests

BASE = "https://raw.githubusercontent.com/openfootball/football.json/master"

# competition slug -> (football.json file stem, {openfootball name: dataset name})
LEAGUES = {
    "la-liga": ("es.1", {
        "Athletic Club": "Ath Bilbao", "CA Osasuna": "Osasuna", "CD Leganés": "Leganes",
        "Club Atlético de Madrid": "Ath Madrid", "Deportivo Alavés": "Alaves", "Elche CF": "Elche",
        "FC Barcelona": "Barcelona", "Getafe CF": "Getafe", "Girona FC": "Girona",
        "Levante UD": "Levante", "Málaga CF": "Malaga", "RC Celta de Vigo": "Celta",
        "RC Deportivo La Coruña": "La Coruna", "RCD Espanyol de Barcelona": "Espanol",
        "RCD Mallorca": "Mallorca", "Rayo Vallecano de Madrid": "Vallecano",
        "Real Betis Balompié": "Betis", "Real Madrid CF": "Real Madrid", "Real Oviedo": "Oviedo",
        "Real Racing Club de Santander": "Santander", "Real Sociedad de Fútbol": "Sociedad",
        "Real Valladolid CF": "Valladolid", "Sevilla FC": "Sevilla", "UD Las Palmas": "Las Palmas",
        "Valencia CF": "Valencia", "Villarreal CF": "Villarreal",
        "Cádiz CF": "Cadiz", "Granada CF": "Granada", "UD Almería": "Almeria",
    }),
}


def season_url(slug, year):
    return f"{BASE}/{year}-{str(year + 1)[-2:]}/{LEAGUES[slug][0]}.json"


def _full_time(score):
    """Full-time goals, or None for an unplayed fixture.

    Played games appear as {"ft": [h, a], ...} or as a bare [h, a] list.
    """
    if isinstance(score, dict):
        score = score.get("ft")
    if isinstance(score, (list, tuple)) and len(score) == 2 and all(isinstance(g, int) for g in score):
        return score
    return None


def parse_season(slug, year, payload):
    names = LEAGUES[slug][1]
    season = f"{year}-{str(year + 1)[-2:]}"
    rows = []
    for match in payload["matches"]:
        ft = _full_time(match.get("score"))
        if ft is None:
            continue
        unknown = [t for t in (match["team1"], match["team2"]) if t not in names]
        if unknown:
            raise ValueError(f"Unmapped OpenFootball club for {slug}: {', '.join(unknown)}")
        rows.append(dict(date=match["date"], season=season, home_team=names[match["team1"]],
                         away_team=names[match["team2"]], home_score=ft[0], away_score=ft[1], neutral=0))
    return rows


def fetch_season(slug, year):
    """Completed matches for one season as dataset rows (empty list if none played)."""
    if slug not in LEAGUES:
        raise ValueError(f"No OpenFootball mapping for {slug}")
    r = requests.get(season_url(slug, year), timeout=30)
    r.raise_for_status()
    return parse_season(slug, year, r.json())
