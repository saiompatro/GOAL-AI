"""Interactive Premier League transfer-value regression project."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _premier_league_shared import (  # noqa: E402
    data_source_note,
    demo_player_data,
    league_header,
    player_csv_template,
    read_uploaded_csv,
)

SRC = Path(__file__).resolve().parents[1] / "ml" / "src"
sys.path.insert(0, str(SRC))
from goal_ai.premier_league import (  # noqa: E402
    FootballDataClient,
    FootballDataError,
    PLAYER_VALUE_FEATURES,
    predict_transfer_value,
    train_transfer_value_model,
)

league_header(
    "Transfer value predictor",
    "Train a linear model on goals, assists, minutes played, age, and position; then compare its estimate with the recorded market value.",
)

with st.expander("Data format and source", expanded=True):
    upload_tab, squad_tab = st.tabs(["Upload player statistics", "football-data.org squads"])
    with upload_tab:
        uploaded = st.file_uploader("Upload multi-season player statistics", type="csv", key="value_csv")
        st.download_button("Download CSV template", player_csv_template(), "premier_league_players_template.csv", "text/csv")
        st.caption(
            "Required: player, position, goals, assists, minutes, age, market_value_eur. "
            "Use one row per player-season or an aggregated multi-season row."
        )
    with squad_tab:
        squad_key = st.text_input("API key", value=os.getenv("FOOTBALL_DATA_API_KEY", ""), type="password", key="value_api_key")
        if st.button("Fetch current Premier League squad catalogue"):
            try:
                with st.spinner("Fetching squad metadata..."):
                    st.session_state.pl_squads = FootballDataClient(squad_key).premier_league_squads()
            except (ValueError, FootballDataError) as exc:
                st.error(str(exc))
        if "pl_squads" in st.session_state and not st.session_state.pl_squads.empty:
            st.dataframe(st.session_state.pl_squads, hide_index=True, width="stretch")
            st.download_button(
                "Download squad catalogue",
                st.session_state.pl_squads.to_csv(index=False).encode("utf-8"),
                "football_data_pl_squads.csv",
                "text/csv",
            )
        st.caption("The standard API supplies names, teams, positions, birth dates, and nationality—not goals, assists, minutes, or market values. Join this catalogue to a licensed statistics source before training.")

uploaded_data = read_uploaded_csv(uploaded)
data = uploaded_data if uploaded_data is not None else demo_player_data()
data_source_note(uploaded_data is None, uploaded.name if uploaded else None)

try:
    trained = train_transfer_value_model(data)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

metric_cols = st.columns(3)
metric_cols[0].metric("Mean absolute error", f"€{trained.metrics['mae_eur'] / 1_000_000:.2f}m")
metric_cols[1].metric("Test R²", f"{trained.metrics['r2']:.2f}")
metric_cols[2].metric("Players used", f"{int(trained.metrics['training_rows'] + trained.metrics['test_rows'])}")

left, right = st.columns([1, 1], gap="large")
with left:
    st.subheader("Plug in a player")
    player_names = sorted(data["player"].dropna().astype(str).unique())
    selected = st.selectbox("Start from player", player_names)
    selected_row = data[data["player"].astype(str) == selected].iloc[0]
    position_options = sorted(data["position"].dropna().astype(str).unique())
    position = st.selectbox("Position", position_options, index=position_options.index(str(selected_row["position"])))
    goals, assists = st.columns(2)
    with goals:
        goal_value = st.number_input("Goals", 0, 60, int(selected_row["goals"]))
    with assists:
        assist_value = st.number_input("Assists", 0, 40, int(selected_row["assists"]))
    minutes, age = st.columns(2)
    with minutes:
        minute_value = st.number_input("Minutes", 0, 5000, int(selected_row["minutes"]), step=90)
    with age:
        age_value = st.number_input("Age", 16, 45, int(selected_row["age"]))
    estimate = predict_transfer_value(trained, {
        "goals": goal_value,
        "assists": assist_value,
        "minutes": minute_value,
        "age": age_value,
        "position": position,
    })
    st.metric("Model estimate", f"€{estimate / 1_000_000:.2f}m")
    if "market_value_eur" in selected_row:
        st.caption(f"Recorded value in this dataset: €{float(selected_row['market_value_eur']) / 1_000_000:.2f}m")

with right:
    st.subheader("Predicted vs actual")
    chart = trained.predictions.set_index("player")[["market_value_eur", "predicted_value_eur"]]
    st.bar_chart(chart, color=["#7c3aed", "#22c55e"])

st.subheader("Holdout results")
display = trained.predictions.rename(columns={
    "player": "Player",
    "market_value_eur": "Actual value",
    "predicted_value_eur": "Predicted value",
    "difference_eur": "Difference",
})
st.dataframe(display, hide_index=True, width="stretch", column_config={
    column: st.column_config.NumberColumn(column, format="€%.0f")
    for column in ["Actual value", "Predicted value", "Difference"]
})

with st.expander("How this project works"):
    st.markdown(
        "1. `pandas` cleans the player-season table.\n"
        "2. `scikit-learn` scales numeric features and one-hot encodes position.\n"
        "3. Linear regression learns a market-value estimate.\n"
        "4. A held-out test set reports MAE and R²; the chart replaces a static matplotlib comparison in the live app."
    )
