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
    "premier-league": ("en.1", {
        "AFC Bournemouth": "Bournemouth", "Arsenal FC": "Arsenal", "Aston Villa FC": "Aston Villa",
        "Brentford FC": "Brentford", "Brighton & Hove Albion FC": "Brighton", "Burnley FC": "Burnley",
        "Chelsea FC": "Chelsea", "Coventry City FC": "Coventry", "Crystal Palace FC": "Crystal Palace",
        "Everton FC": "Everton", "Fulham FC": "Fulham", "Hull City AFC": "Hull",
        "Ipswich Town FC": "Ipswich", "Leeds United FC": "Leeds", "Leicester City FC": "Leicester",
        "Liverpool FC": "Liverpool", "Luton Town FC": "Luton", "Manchester City FC": "Man City",
        "Manchester United FC": "Man United", "Newcastle United FC": "Newcastle",
        "Nottingham Forest FC": "Nott'm Forest", "Sheffield United FC": "Sheffield United",
        "Southampton FC": "Southampton", "Sunderland AFC": "Sunderland",
        "Tottenham Hotspur FC": "Tottenham", "West Ham United FC": "West Ham",
        "Wolverhampton Wanderers FC": "Wolves", "Watford FC": "Watford", "Norwich City FC": "Norwich",
    }),
    "bundesliga": ("de.1", {
        "1. FC Heidenheim 1846": "Heidenheim", "1. FC Köln": "FC Koln", "1. FC Union Berlin": "Union Berlin",
        "1. FSV Mainz 05": "Mainz", "Arminia Bielefeld": "Bielefeld", "Bayer 04 Leverkusen": "Leverkusen",
        "Borussia Dortmund": "Dortmund", "Borussia Mönchengladbach": "M'gladbach",
        "Eintracht Frankfurt": "Ein Frankfurt", "FC Augsburg": "Augsburg", "FC Bayern München": "Bayern Munich",
        "FC Schalke 04": "Schalke 04", "FC St. Pauli 1910": "St Pauli", "Hamburger SV": "Hamburg",
        "Hertha BSC": "Hertha", "Holstein Kiel": "Holstein Kiel", "RB Leipzig": "RB Leipzig",
        "SC Freiburg": "Freiburg", "SC Paderborn 07": "Paderborn", "SV 07 Elversberg": "Elversberg",
        "SV Darmstadt 98": "Darmstadt", "SV Werder Bremen": "Werder Bremen",
        "SpVgg Greuther Fürth 1903": "Greuther Furth", "TSG 1899 Hoffenheim": "Hoffenheim",
        "VfB Stuttgart": "Stuttgart", "VfL Bochum 1848": "Bochum", "VfL Wolfsburg": "Wolfsburg",
    }),
    "serie-a": ("it.1", {
        "AC Milan": "Milan", "AC Monza": "Monza", "AC Pisa 1909": "Pisa", "ACF Fiorentina": "Fiorentina",
        "AS Roma": "Roma", "Atalanta BC": "Atalanta", "Bologna FC 1909": "Bologna", "Cagliari Calcio": "Cagliari",
        "Como 1907": "Como", "Empoli FC": "Empoli", "FC Internazionale Milano": "Inter",
        "Frosinone Calcio": "Frosinone", "Genoa CFC": "Genoa", "Hellas Verona FC": "Verona",
        "Juventus FC": "Juventus", "Parma Calcio 1913": "Parma", "SS Lazio": "Lazio", "SSC Napoli": "Napoli",
        "Spezia Calcio": "Spezia", "Torino FC": "Torino", "UC Sampdoria": "Sampdoria", "US Cremonese": "Cremonese",
        "US Lecce": "Lecce", "US Salernitana 1919": "Salernitana", "US Sassuolo Calcio": "Sassuolo",
        "Udinese Calcio": "Udinese", "Venezia FC": "Venezia",
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
