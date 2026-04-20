import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from goal_ai.clean import clean_matches, clean_players, aggregate_players
from goal_ai.features import build_features, EloConfig, compute_elo_history


def _toy_matches():
    return pd.DataFrame([
        {"date": "2020-01-01", "home_team": "A", "away_team": "B",
         "home_score": 2, "away_score": 1, "tournament": "Friendly",
         "city": "x", "country": "A", "neutral": False},
        {"date": "2020-02-01", "home_team": "B", "away_team": "A",
         "home_score": 0, "away_score": 0, "tournament": "Friendly",
         "city": "x", "country": "B", "neutral": False},
        {"date": "2020-03-01", "home_team": "A", "away_team": "C",
         "home_score": 3, "away_score": 0, "tournament": "FIFA World Cup",
         "city": "x", "country": "D", "neutral": True},
    ])


def test_clean_assigns_result():
    df = clean_matches(_toy_matches())
    assert list(df["result"]) == ["H", "D", "H"]


def test_elo_updates_after_win():
    df = clean_matches(_toy_matches())
    out, final = compute_elo_history(df, EloConfig())
    assert final["A"] > final["B"]  # A won head-to-head
    assert out.loc[0, "elo_home_pre"] == 1500.0  # pre-match start


def test_build_features_no_leakage():
    df = clean_matches(_toy_matches())
    pa = pd.DataFrame(columns=[
        "team","squad_mean","top11_mean","star3_mean","att_mean","mid_mean","def_mean",
        "potential_mean","potential_top11_mean","value_mean_eur","value_top11_eur",
        "wage_mean_eur","age_mean","height_mean","international_reputation_mean",
        "dribbling_mean","physic_mean",
    ])
    cfg = {"features": {"form_windows": [5, 10], "h2h_last_n": 5,
                        "elo": {"start": 1500, "k": 30, "home_advantage": 65}}}
    feats = build_features(df, pa, cfg)
    # First row: no prior history → form stats are zeros
    assert feats.iloc[0]["home_win_rate_5"] == 0.0
    assert feats.iloc[0]["elo_home_pre"] == 1500.0
    assert "y" in feats.columns
    assert set(feats["y"].unique()).issubset({0, 1, 2})


def test_clean_players_and_aggregate_rich_fields():
    raw = pd.DataFrame([
        {
            "long_name": "Alpha One",
            "short_name": "A. One",
            "nationality_name": "A",
            "club_name": "Club A",
            "player_positions": "FW,ST",
            "overall": 84,
            "potential": 87,
            "age": 25,
            "height_cm": 181,
            "preferred_foot": "Right",
            "international_reputation": 2,
            "value_eur": 12000000,
            "wage_eur": 50000,
            "pace": 85,
            "shooting": 82,
            "passing": 77,
            "dribbling": 83,
            "defending": 40,
            "physic": 76,
        },
        {
            "long_name": "Alpha Two",
            "short_name": "A. Two",
            "nationality_name": "A",
            "club_name": "Club B",
            "player_positions": "MF,CM",
            "overall": 80,
            "potential": 84,
            "age": 27,
            "height_cm": 178,
            "preferred_foot": "Left",
            "international_reputation": 1,
            "value_eur": 8000000,
            "wage_eur": 40000,
            "pace": 75,
            "shooting": 70,
            "passing": 81,
            "dribbling": 79,
            "defending": 68,
            "physic": 72,
        },
    ])
    cleaned = clean_players(raw)
    agg = aggregate_players(cleaned)
    assert cleaned.loc[0, "player_name"] == "Alpha One"
    assert "club_name" in cleaned.columns
    assert agg.loc[0, "team"] == "A"
    assert agg.loc[0, "value_mean_eur"] > 0
    assert agg.loc[0, "potential_mean"] >= agg.loc[0, "squad_mean"]


def test_clean_players_handles_public_fifa_shape_without_overall():
    raw = pd.DataFrame([
        {
            "Name": "Test Star",
            "Age": 24,
            "Nationality": "Brazil",
            "Club": "Example FC",
            "Value": 45000000,
            "Wage": 180000,
            "Position": "LW",
            "Pace": 92,
            "Shooting": 84,
            "Passing": 81,
            "Dribbling": 90,
            "Defending": 42,
            "Strength": 74,
            "Stamina": 86,
            "Jumping": 79,
        }
    ])
    cleaned = clean_players(raw)
    assert len(cleaned) == 1
    assert cleaned.loc[0, "club_name"] == "Example FC"
    assert cleaned.loc[0, "overall"] > 0
    assert cleaned.loc[0, "physic"] > 0
