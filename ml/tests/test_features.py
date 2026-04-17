import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from goal_ai.clean import clean_matches, aggregate_players
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
    pa = pd.DataFrame(columns=["team","squad_mean","top11_mean","star3_mean",
                                "att_mean","mid_mean","def_mean"])
    cfg = {"features": {"form_windows": [5, 10], "h2h_last_n": 5,
                        "elo": {"start": 1500, "k": 30, "home_advantage": 65}}}
    feats = build_features(df, pa, cfg)
    # First row: no prior history → form stats are zeros
    assert feats.iloc[0]["home_win_rate_5"] == 0.0
    assert feats.iloc[0]["elo_home_pre"] == 1500.0
    assert "y" in feats.columns
    assert set(feats["y"].unique()).issubset({0, 1, 2})
