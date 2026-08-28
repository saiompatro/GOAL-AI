"""Real-football data policy checks.

GOAL AI accepts real match, roster, club, league, stadium, and weather data.
EA Sports FC / SOFIFA / FUT-style player rating dumps are rejected before they
can enter the pipeline.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

REJECTED_SOURCE_TOKENS = {
    "fifa_players",
    "sofifa",
    "eafc",
    "ea_fc",
    "ea-sports-fc",
    "easports",
    "futbin",
    "futwiz",
    "ultimate_team",
    "ultimate-team",
    "career_mode",
    "career-mode",
    "complete-player-dataset",
}

VIDEO_GAME_RATING_COLUMNS = {
    "overall",
    "potential",
    "pace",
    "shooting",
    "passing",
    "dribbling",
    "defending",
    "physic",
    "skillmoves",
    "skill_moves",
    "weakfoot",
    "weak_foot",
    "crossing",
    "finishing",
    "headingaccuracy",
    "heading_accuracy",
    "shortpassing",
    "short_passing",
    "volleys",
    "curve",
    "fkaccuracy",
    "fk_accuracy",
    "longpassing",
    "long_passing",
    "ballcontrol",
    "ball_control",
    "acceleration",
    "sprintspeed",
    "sprint_speed",
    "agility",
    "reactions",
    "balance",
    "shotpower",
    "shot_power",
    "jumping",
    "stamina",
    "strength",
    "longshots",
    "long_shots",
    "aggression",
    "interceptions",
    "positioning",
    "vision",
    "penalties",
    "composure",
    "marking",
    "standingtackle",
    "standing_tackle",
    "slidingtackle",
    "sliding_tackle",
    "gkdiving",
    "gk_diving",
    "gkhandling",
    "gk_handling",
    "gkkicking",
    "gk_kicking",
    "gkpositioning",
    "gk_positioning",
    "gkreflexes",
    "gk_reflexes",
}

APPROVED_RAW_PATH_MARKERS = {
    "results.csv",
    "goalscorers.csv",
    "shootouts.csv",
    "former_names.csv",
    "openfootball_wc2026.json",
    "wc2026_schedule.csv",
    "wc2026_venues.csv",
    "wc2026_matchday_players.csv",
    "fifa_2026_squads.csv",
    "statsbomb_competitions.json",
    "jfjelstul_worldcup",
    "SOURCE_MANIFEST.md",
}


class DataPolicyError(ValueError):
    """Raised when a raw source violates the real-football-only policy."""


def normalize_token(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def rejected_source_tokens(path_or_url: object) -> list[str]:
    text = normalize_token(path_or_url).replace("\\", "/")
    return sorted(token for token in REJECTED_SOURCE_TOKENS if token in text)


def is_rejected_source_name(path_or_url: object) -> bool:
    return bool(rejected_source_tokens(path_or_url))


def video_game_rating_columns(columns: Iterable[object]) -> set[str]:
    normalized = {normalize_token(column) for column in columns}
    return normalized & VIDEO_GAME_RATING_COLUMNS


def looks_like_video_game_player_dataset(columns: Iterable[object]) -> bool:
    hits = video_game_rating_columns(columns)
    keeper_hits = {col for col in hits if col.startswith("gk")}
    core_hits = hits & {
        "overall",
        "potential",
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physic",
    }
    return len(hits) >= 8 or len(core_hits) >= 5 or len(keeper_hits) >= 3


def approved_raw_path(path: Path) -> bool:
    text = str(path).replace("\\", "/")
    return any(marker in text for marker in APPROVED_RAW_PATH_MARKERS)


def enforce_real_player_source(path: Path, columns: Iterable[object]) -> None:
    rejected = rejected_source_tokens(path)
    if rejected:
        raise DataPolicyError(f"Rejected player source {path}: source name contains {', '.join(rejected)}")
    if looks_like_video_game_player_dataset(columns):
        hits = ", ".join(sorted(video_game_rating_columns(columns))[:12])
        raise DataPolicyError(f"Rejected player source {path}: EA/SOFIFA-style columns detected ({hits})")
