"""Interactive Premier League similarity and clustering scouting project."""
from __future__ import annotations

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
from goal_ai.premier_league import SCOUTING_FEATURES, clean_player_data, scout_similar_players  # noqa: E402

league_header(
    "Player scouting system",
    "Search for a player, compare their statistical style with the nearest matches, and discover broader playing-style clusters.",
)

with st.expander("Load player statistics", expanded=True):
    uploaded = st.file_uploader("Upload player scouting data", type="csv", key="scouting_csv")
    st.download_button("Download CSV template", player_csv_template(), "premier_league_scouting_template.csv", "text/csv")
    st.caption("Required: player, goals, assists, passes, shots, dribbles, defensive_actions. Team and position are recommended.")

uploaded_data = read_uploaded_csv(uploaded)
data = clean_player_data(uploaded_data if uploaded_data is not None else demo_player_data())
data_source_note(uploaded_data is None, uploaded.name if uploaded else None)

players = sorted(data["player"].dropna().astype(str).unique())
default_player = "Bukayo Saka" if "Bukayo Saka" in players else players[0]
selected = st.selectbox("Search for a player", players, index=players.index(default_player))
neighbour_count = st.slider("Statistical matches", 3, 10, 6)

try:
    matches, clusters = scout_similar_players(data, selected, neighbour_count)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

selected_row = data[data["player"].astype(str) == selected].iloc[0]
profile = pd.DataFrame({"metric": SCOUTING_FEATURES, selected: [float(selected_row[column]) for column in SCOUTING_FEATURES]})

left, right = st.columns([1, 1.4], gap="large")
with left:
    st.subheader("Selected profile")
    meta = st.columns(2)
    meta[0].metric("Team", str(selected_row.get("team", "—")))
    meta[1].metric("Position", str(selected_row.get("position", "—")))
    st.dataframe(profile, hide_index=True, width="stretch")

with right:
    st.subheader("Closest statistical matches")
    chart = matches.set_index("player")["similarity"].sort_values()
    st.bar_chart(chart, horizontal=True, color="#7c3aed")

table_columns = [column for column in ["player", "team", "position", "similarity", *SCOUTING_FEATURES] if column in matches.columns]
st.dataframe(matches[table_columns], hide_index=True, width="stretch", column_config={
    "similarity": st.column_config.ProgressColumn("Similarity", min_value=0, max_value=100, format="%.1f%%")
})

st.subheader("Playing-style clusters")
selected_cluster = int(clusters.loc[clusters["player"] == selected, "style_cluster"].iloc[0])
st.caption(f"{selected} belongs to style cluster {selected_cluster}. Clusters are recalculated for the loaded player pool.")
st.dataframe(clusters, hide_index=True, width="stretch", column_config={
    "is_selected": st.column_config.CheckboxColumn("Selected")
})

with st.expander("How similarity is calculated"):
    st.markdown(
        "The six scouting features are standardized so high-volume statistics do not dominate. "
        "Nearest-neighbour distance finds the closest profiles; K-means independently groups the complete pool into playing styles. "
        "For fair comparisons, upload per-90 statistics or filter the dataset to players with similar minutes and positions before training."
    )
