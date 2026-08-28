"""Interactive Premier League match-outcome classification project."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _premier_league_shared import (  # noqa: E402
    data_source_note,
    demo_match_data,
    league_header,
    match_csv_template,
    read_uploaded_csv,
)

SRC = Path(__file__).resolve().parents[1] / "ml" / "src"
sys.path.insert(0, str(SRC))
from goal_ai.premier_league import (  # noqa: E402
    FootballDataClient,
    FootballDataError,
    build_match_features,
    match_probabilities,
    next_match_features,
    train_match_outcome_model,
)

league_header(
    "Match outcome predictor",
    "Use historical form and home advantage to predict a home win, draw, or away win with a random forest classifier.",
)

if "pl_api_matches" not in st.session_state:
    st.session_state.pl_api_matches = None

with st.expander("Connect match data", expanded=True):
    source_tab, upload_tab = st.tabs(["football-data.org", "Upload CSV"])
    with source_tab:
        default_key = os.getenv("FOOTBALL_DATA_API_KEY", "")
        api_key = st.text_input("API key", value=default_key, type="password", help="Sent only to api.football-data.org.")
        current_year = pd.Timestamp.now().year
        seasons = st.multiselect("Season start years", list(range(current_year - 6, current_year + 1)), default=list(range(current_year - 3, current_year)))
        if st.button("Fetch completed Premier League matches", type="primary"):
            try:
                with st.spinner("Fetching season history..."):
                    st.session_state.pl_api_matches = FootballDataClient(api_key).premier_league_matches(seasons)
                st.success(f"Loaded {len(st.session_state.pl_api_matches):,} completed matches.")
            except (ValueError, FootballDataError) as exc:
                st.error(str(exc))
    with upload_tab:
        uploaded = st.file_uploader("Upload historical matches", type="csv", key="matches_csv")
        st.download_button("Download CSV template", match_csv_template(), "premier_league_matches_template.csv", "text/csv")
        st.caption("Required: date, home_team, away_team, home_goals, away_goals. Rows must be chronological completed matches.")

uploaded_data = read_uploaded_csv(uploaded)
if uploaded_data is not None:
    matches = uploaded_data
    source_name = uploaded.name
elif st.session_state.pl_api_matches is not None and not st.session_state.pl_api_matches.empty:
    matches = st.session_state.pl_api_matches
    source_name = "football-data.org"
else:
    matches = demo_match_data()
    source_name = None
data_source_note(source_name is None, source_name)

try:
    trained = train_match_outcome_model(matches)
    featured = build_match_features(matches)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

summary = st.columns(3)
summary[0].metric("Holdout accuracy", f"{trained.metrics['accuracy']:.1%}")
summary[1].metric("Training matches", f"{int(trained.metrics['training_rows']):,}")
summary[2].metric("Test matches", f"{int(trained.metrics['test_rows']):,}")

st.subheader("Predict the next fixture")
teams = sorted(set(matches["home_team"].dropna()) | set(matches["away_team"].dropna()))
home_col, away_col = st.columns(2)
with home_col:
    home_team = st.selectbox("Home team", teams, index=0)
with away_col:
    away_options = [team for team in teams if team != home_team]
    away_team = st.selectbox("Away team", away_options, index=min(1, len(away_options) - 1))

feature_row = next_match_features(featured, home_team, away_team, trained.features)
probabilities = match_probabilities(trained, feature_row)
winner = probabilities.index[0]
st.success(f"Model call: **{winner}** · {probabilities.iloc[0]:.1%} confidence")
prob_cols = st.columns(len(probabilities))
for column, (label, probability) in zip(prob_cols, probabilities.items()):
    column.metric(label, f"{probability:.1%}")

st.subheader("Recent test predictions")
st.dataframe(trained.predictions.tail(30), hide_index=True, width="stretch", column_config={
    "correct": st.column_config.CheckboxColumn("Correct")
})

with st.expander("Feature and model notes"):
    st.markdown(
        "The default API workflow uses rolling goals scored, goals conceded, recent points, and home advantage. "
        "All rolling values are calculated before each match to avoid target leakage. When an uploaded CSV contains "
        "home_shots, away_shots, home_possession, and away_possession, their rolling features are included automatically; "
        "football-data.org's standard match response does not include those fields. "
        "The holdout is the newest 20% of matches, which is closer to how upcoming-fixture testing works than a random split."
    )
