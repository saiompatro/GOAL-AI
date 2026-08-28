import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from goal_ai.premier_league import (
    MATCH_MODEL_FEATURES,
    build_match_features,
    parse_football_data_matches,
    predict_transfer_value,
    scout_similar_players,
    train_match_outcome_model,
    train_transfer_value_model,
)


def _players(rows=40):
    return pd.DataFrame({
        "player": [f"Player {i}" for i in range(rows)],
        "team": [f"Club {i % 5}" for i in range(rows)],
        "position": [["Defence", "Midfield", "Offence"][i % 3] for i in range(rows)],
        "goals": [i % 14 for i in range(rows)],
        "assists": [(i * 2) % 11 for i in range(rows)],
        "minutes": [900 + i * 47 for i in range(rows)],
        "age": [19 + i % 14 for i in range(rows)],
        "passes": [500 + i * 21 for i in range(rows)],
        "shots": [12 + i * 2 for i in range(rows)],
        "dribbles": [8 + i * 3 for i in range(rows)],
        "defensive_actions": [90 - i for i in range(rows)],
        "market_value_eur": [1_000_000 + i * 1_250_000 for i in range(rows)],
    })


def _matches(rows=80):
    teams = ["A", "B", "C", "D", "E", "F"]
    values = []
    for i in range(rows):
        home = teams[i % len(teams)]
        away = teams[(i * 2 + 1) % len(teams)]
        if home == away:
            away = teams[(teams.index(away) + 1) % len(teams)]
        values.append({
            "date": pd.Timestamp("2021-01-01", tz="UTC") + pd.Timedelta(days=i),
            "home_team": home,
            "away_team": away,
            "home_goals": (i * 3) % 5,
            "away_goals": (i * 2) % 4,
        })
    return pd.DataFrame(values)


def test_parse_football_data_matches():
    payload = {"matches": [{
        "utcDate": "2024-08-16T19:00:00Z",
        "matchday": 1,
        "homeTeam": {"name": "Home"},
        "awayTeam": {"name": "Away"},
        "score": {"fullTime": {"home": 2, "away": 1}},
    }]}
    result = parse_football_data_matches(payload, 2024)
    assert result.loc[0, "home_goals"] == 2
    assert result.loc[0, "season"] == 2024


def test_transfer_value_model_predicts_non_negative_value():
    trained = train_transfer_value_model(_players())
    prediction = predict_transfer_value(trained, {
        "goals": 10, "assists": 8, "minutes": 2500, "age": 24, "position": "Offence"
    })
    assert prediction >= 0
    assert trained.metrics["test_rows"] > 0


def test_match_features_do_not_use_current_result():
    featured = build_match_features(_matches())
    assert all(column in featured.columns for column in MATCH_MODEL_FEATURES)
    assert featured.iloc[0]["home_form_points"] == 0
    assert featured.iloc[0]["away_goals_for"] == 0
    trained = train_match_outcome_model(_matches())
    assert 0 <= trained.metrics["accuracy"] <= 1


def test_enriched_match_features_are_added_when_available():
    matches = _matches()
    matches["home_shots"] = 8 + matches.index % 9
    matches["away_shots"] = 6 + matches.index % 7
    matches["home_possession"] = 48 + matches.index % 8
    matches["away_possession"] = 52 - matches.index % 8
    trained = train_match_outcome_model(matches)
    assert "home_shots_for" in trained.features
    assert "away_possession" in trained.features


def test_scouting_excludes_selected_player_and_clusters_pool():
    matches, clusters = scout_similar_players(_players(), "Player 4", neighbours=5)
    assert "Player 4" not in matches["player"].tolist()
    assert len(matches) == 5
    assert clusters["is_selected"].sum() == 1
