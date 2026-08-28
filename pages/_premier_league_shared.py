"""Shared UI and clearly-labelled starter data for Premier League projects."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def league_header(project: str, description: str) -> None:
    st.caption("PREMIER LEAGUE  /  ML PROJECT LAB")
    st.title(project)
    st.markdown(description)


def data_source_note(using_demo: bool, uploaded_name: str | None = None) -> None:
    if uploaded_name:
        st.success(f"Using data source: `{uploaded_name}`")
    elif using_demo:
        st.info(
            "Using generated starter data so the workflow is immediately interactive. "
            "It is illustrative—not a source of real player valuations or match claims. "
            "Upload a real CSV or connect football-data.org for analysis you can act on."
        )


def read_uploaded_csv(uploaded_file) -> pd.DataFrame | None:
    if uploaded_file is None:
        return None
    return pd.read_csv(io.BytesIO(uploaded_file.getvalue()))


@st.cache_data(show_spinner=False)
def demo_player_data(rows: int = 72) -> pd.DataFrame:
    rng = np.random.default_rng(27)
    positions = np.array(["Goalkeeper", "Defence", "Midfield", "Offence"])
    clubs = np.array([
        "North London FC", "Mersey Athletic", "Manchester Blues", "West London FC",
        "Birmingham Lions", "Tyneside United", "South Coast FC", "East London Athletic",
    ])
    player_positions = rng.choice(positions, size=rows, p=[0.1, 0.32, 0.34, 0.24])
    minutes = rng.integers(420, 3421, rows)
    age = rng.integers(18, 35, rows)
    attack_factor = np.where(player_positions == "Offence", 1.0, np.where(player_positions == "Midfield", 0.65, 0.22))
    goals = np.maximum(0, rng.poisson(2 + attack_factor * minutes / 330)).astype(int)
    assists = np.maximum(0, rng.poisson(1 + attack_factor * minutes / 520)).astype(int)
    passes = np.maximum(80, (minutes * rng.uniform(0.28, 0.7, rows))).astype(int)
    shots = np.maximum(2, (goals * rng.uniform(3.2, 5.6, rows) + rng.normal(8, 4, rows))).astype(int)
    dribbles = np.maximum(1, (minutes / 90 * rng.uniform(0.3, 2.4, rows) * attack_factor)).astype(int)
    defensive_actions = np.maximum(1, (minutes / 90 * rng.uniform(0.5, 3.1, rows) * (1.2 - attack_factor))).astype(int)
    age_curve = np.maximum(0, 28 - np.abs(age - 25) * 1.5)
    value = (
        750_000 + goals * 1_650_000 + assists * 1_150_000 + minutes * 3_000
        + age_curve * 700_000 + rng.normal(0, 3_000_000, rows)
    ).clip(300_000, 125_000_000)
    return pd.DataFrame({
        "player": [f"Starter Player {index + 1:02d}" for index in range(rows)],
        "team": clubs[np.arange(rows) % len(clubs)],
        "position": player_positions,
        "goals": goals,
        "assists": assists,
        "minutes": minutes,
        "age": age,
        "passes": passes,
        "shots": shots,
        "dribbles": dribbles,
        "defensive_actions": defensive_actions,
        "market_value_eur": value.round(-4),
    })


@st.cache_data(show_spinner=False)
def demo_match_data(match_count: int = 260) -> pd.DataFrame:
    rng = np.random.default_rng(81)
    teams = np.array([
        "Arsenal", "Aston Villa", "Brighton", "Chelsea", "Everton", "Liverpool",
        "Manchester City", "Manchester United", "Newcastle United", "Tottenham Hotspur",
    ])
    strength = dict(zip(teams, [1.45, 1.05, 0.98, 1.22, 0.84, 1.48, 1.55, 1.16, 1.12, 1.24]))
    rows = []
    date = pd.Timestamp("2022-08-05", tz="UTC")
    for index in range(match_count):
        home_index = index % len(teams)
        away_index = (index * 3 + index // len(teams) + 1) % len(teams)
        if away_index == home_index:
            away_index = (away_index + 1) % len(teams)
        home, away = teams[home_index], teams[away_index]
        home_goals = int(rng.poisson(max(0.25, strength[home] * 1.22 - strength[away] * 0.24)))
        away_goals = int(rng.poisson(max(0.2, strength[away] - strength[home] * 0.2)))
        rows.append({
            "date": date + pd.Timedelta(days=index * 2),
            "season": 2022 + min(2, index // 95),
            "home_team": home,
            "away_team": away,
            "home_goals": home_goals,
            "away_goals": away_goals,
        })
    return pd.DataFrame(rows)


def player_csv_template() -> bytes:
    return demo_player_data(12).head(2).to_csv(index=False).encode("utf-8")


def match_csv_template() -> bytes:
    template = demo_match_data(4).head(2).copy()
    template["home_shots"] = [14, 9]
    template["away_shots"] = [8, 12]
    template["home_possession"] = [57.2, 46.4]
    template["away_possession"] = [42.8, 53.6]
    return template.to_csv(index=False).encode("utf-8")
