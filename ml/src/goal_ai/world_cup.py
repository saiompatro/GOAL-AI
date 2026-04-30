"""World Cup 2026 team helpers used by the Streamlit UI."""
from __future__ import annotations


QUALIFIED_2026_TEAMS = [
    "United States",
    "Canada",
    "Mexico",
    "Japan",
    "New Zealand",
    "Iran",
    "Argentina",
    "Uzbekistan",
    "South Korea",
    "Jordan",
    "Australia",
    "Brazil",
    "Ecuador",
    "Uruguay",
    "Colombia",
    "Paraguay",
    "Morocco",
    "Tunisia",
    "Egypt",
    "Algeria",
    "Ghana",
    "Cape Verde",
    "Qatar",
    "Saudi Arabia",
    "Côte d'Ivoire",
    "Senegal",
    "South Africa",
    "England",
    "France",
    "Croatia",
    "Portugal",
    "Norway",
    "Germany",
    "Netherlands",
    "Switzerland",
    "Scotland",
    "Spain",
    "Austria",
    "Belgium",
    "Panama",
    "Curaçao",
    "Haiti",
    "Bosnia and Herzegovina",
    "Sweden",
    "Türkiye",
    "Czechia",
    "DR Congo",
    "Iraq",
]


_ALIASES = {
    "curacao": "Curaçao",
    "curaçao": "Curaçao",
    "ivory coast": "Côte d'Ivoire",
    "cote d'ivoire": "Côte d'Ivoire",
    "côte d'ivoire": "Côte d'Ivoire",
    "turkey": "Türkiye",
    "turkiye": "Türkiye",
    "türkiye": "Türkiye",
    "usa": "United States",
    "united states": "United States",
    "korea republic": "South Korea",
    "south korea": "South Korea",
    "congo dr": "DR Congo",
    "dr congo": "DR Congo",
    "democratic republic of congo": "DR Congo",
}


def canonical_team(name: object) -> str:
    text = str(name or "").strip()
    return _ALIASES.get(text.lower(), text)


def is_qualified_2026(name: object) -> bool:
    return canonical_team(name) in QUALIFIED_2026_TEAMS


def qualified_teams_present(names: list[str] | set[str]) -> list[str]:
    available = {canonical_team(name) for name in names if is_qualified_2026(name)}
    return [team for team in QUALIFIED_2026_TEAMS if team in available]
