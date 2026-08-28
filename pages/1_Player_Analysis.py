"""Player Analysis - single-player real-data profile."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import (  # noqa: E402
    ATTR_COLS,
    REAL_DATA_NOTE,
    PLAYER_EMPTY_MESSAGE,
    index_of,
    load_players,
    player_team_list,
    profile_label,
)


def _num(row: pd.Series, key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    return float(value) if pd.notna(value) else default


def _int_metric(row: pd.Series, key: str) -> str:
    value = row.get(key)
    return f"{int(value):,}" if pd.notna(value) and float(value) else "-"


st.title("Player Analysis")
st.caption("Real player profile from World Cup rosters/events and approved football sources.")
st.info(REAL_DATA_NOTE)

players = load_players()
if players.empty:
    st.warning(PLAYER_EMPTY_MESSAGE)
    st.stop()

teams = player_team_list(players)
if not teams:
    st.error("No eligible teams found in the player data.")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    team = st.selectbox("Team", teams, index=index_of(teams, "Argentina"))

roster = players[players["team"] == team].sort_values("overall", ascending=False)
with c2:
    names = roster["player_name"].tolist()
    player_name = st.selectbox("Player", names) if names else None

if not player_name:
    st.warning(f"No players found for {team}.")
    st.stop()

p = roster[roster["player_name"] == player_name].iloc[0]

st.subheader(player_name)
m = st.columns(5)
m[0].metric("Derived strength", f"{_num(p, 'overall'):.1f}")
m[1].metric("WC appearances", _int_metric(p, "appearances"))
m[2].metric("WC starts", _int_metric(p, "starts"))
m[3].metric("WC goals", _int_metric(p, "goals"))
m[4].metric("Position", str(p.get("primary_position", "-")))

m2 = st.columns(4)
m2[0].metric("Team", str(p.get("team", "-")))
m2[1].metric("Club/source", str(p.get("club_name", "-")))
m2[2].metric("Age at 2026 WC", f"{_num(p, 'age'):.0f}" if _num(p, "age") else "-")
m2[3].metric("Discipline", f"{_num(p, 'sendings_off'):.0f} send-offs" if _num(p, "sendings_off") else "-")

if _num(p, "value_eur") or _num(p, "wage_eur"):
    v = st.columns(2)
    v[0].metric("Market value", f"EUR {_num(p, 'value_eur'):,.0f}" if _num(p, "value_eur") else "-")
    v[1].metric("Wage", f"EUR {_num(p, 'wage_eur'):,.0f}" if _num(p, "wage_eur") else "-")

avail = [column for column in ATTR_COLS if column in roster.columns]
if avail:
    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Derived profile indices**")
        try:
            import plotly.graph_objects as go

            vals = [float(p.get(column, 0) or 0) for column in avail]
            labels = [profile_label(column) for column in avail]
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=labels + [labels[0]],
                fill="toself",
                name=player_name,
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                height=360,
                margin=dict(l=30, r=30, t=20, b=20),
            )
            st.plotly_chart(fig, width="stretch")
        except ImportError:
            st.bar_chart(pd.Series({profile_label(column): float(p.get(column, 0) or 0) for column in avail}))

    with right:
        st.markdown("**Percentile vs eligible player pool**")
        rows = []
        for column in avail:
            series = pd.to_numeric(players[column], errors="coerce").dropna()
            value = float(p.get(column, 0) or 0)
            percentile = float((series < value).mean() * 100) if len(series) else 0.0
            rows.append({
                "Profile index": profile_label(column),
                "Value": round(value),
                "Percentile": round(percentile),
            })
        pdf = pd.DataFrame(rows)
        st.dataframe(
            pdf,
            hide_index=True,
            width="stretch",
            column_config={
                "Percentile": st.column_config.ProgressColumn(
                    "Percentile", min_value=0, max_value=100, format="%d%%"
                )
            },
        )

st.subheader(f"Squad ranking - {team}")
rank_cols = [
    column
    for column in [
        "player_name",
        "primary_position",
        "overall",
        "appearances",
        "starts",
        "goals",
        "age",
        "club_name",
    ]
    if column in roster.columns
]
ranked = roster[rank_cols].rename(columns={"overall": "derived_strength"}).reset_index(drop=True)
ranked.index += 1
st.dataframe(ranked, width="stretch")
