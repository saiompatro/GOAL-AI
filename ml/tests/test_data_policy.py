from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from goal_ai.data_policy import (  # noqa: E402
    DataPolicyError,
    enforce_real_player_source,
    is_rejected_source_name,
    looks_like_video_game_player_dataset,
)


def test_rejects_ea_sofifa_source_names():
    assert is_rejected_source_name("data/raw/fifa_players.csv")
    assert is_rejected_source_name("https://example.com/sofifa_complete-player-dataset.csv")
    assert is_rejected_source_name("s3://bucket/eafc-ultimate-team-ratings.csv")


def test_detects_video_game_player_rating_shape():
    columns = [
        "Name",
        "Age",
        "Club",
        "Overall",
        "Potential",
        "Pace",
        "Shooting",
        "Passing",
        "Dribbling",
        "Defending",
        "GKDiving",
        "GKHandling",
        "GKReflexes",
    ]
    assert looks_like_video_game_player_dataset(columns)


def test_allows_real_transfermarkt_like_shape(tmp_path):
    path = tmp_path / "transfermarkt_players.csv"
    columns = [
        "player_id",
        "player_name",
        "date_of_birth",
        "country_of_birth",
        "current_club_name",
        "market_value_in_eur",
        "last_season",
    ]
    enforce_real_player_source(path, columns)


def test_enforce_raises_on_rating_dump(tmp_path):
    path = tmp_path / "players.csv"
    columns = ["Name", "Overall", "Potential", "Pace", "Shooting", "Passing", "Dribbling", "Defending"]
    with pytest.raises(DataPolicyError):
        enforce_real_player_source(path, columns)
