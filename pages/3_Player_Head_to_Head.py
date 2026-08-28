"""Player Head to Head - compare two real-data player profiles."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import ATTR_COLS, PLAYER_EMPTY_MESSAGE, REAL_DATA_NOTE, index_of, load_players, player_team_list, profile_label  # noqa: E402

st.title("Player Head to Head")
st.caption("Compare two players using real roster/event data and derived profile indices.")
st.info(REAL_DATA_NOTE)

players = load_players()
if players.empty:
    st.warning(PLAYER_EMPTY_MESSAGE)
    st.stop()

teams = player_team_list(players)
if not teams:
    st.error("No eligible teams found in the player data.")
    st.stop()


def pick(col, label: str, default_team: str, default_idx: int = 0) -> pd.Series | None:
    with col:
        st.markdown(f"**{label}**")
        team = st.selectbox(f"{label} team", teams, index=index_of(teams, default_team), key=f"{label}_team")
        roster = players[players["team"] == team].sort_values("overall", ascending=False)
        names = roster["player_name"].tolist()
        if not names:
            return None
        name = st.selectbox(
            f"{label} player",
            names,
            index=min(default_idx, len(names) - 1),
            key=f"{label}_player",
        )
        return roster[roster["player_name"] == name].iloc[0]


left, right = st.columns(2)
p1 = pick(left, "Player A", "Argentina")
p2 = pick(right, "Player B", "Portugal")

if p1 is None or p2 is None:
    st.stop()
if p1["player_name"] == p2["player_name"]:
    st.warning("Pick two different players.")
    st.stop()

n1, n2 = p1["player_name"], p2["player_name"]


def _num(player: pd.Series, key: str) -> float:
    value = player.get(key)
    return float(value) if pd.notna(value) else 0.0


def cmp_row(label: str, key: str, fmt: str = "{:.0f}", lower_is_better: bool = False) -> dict:
    a, b = _num(p1, key), _num(p2, key)
    a_s = fmt.format(a) if a else "-"
    b_s = fmt.format(b) if b else "-"
    if lower_is_better:
        edge = "A" if a and (not b or a < b) else ("B" if b and (not a or b < a) else "=")
    else:
        edge = "A" if a > b else ("B" if b > a else "=")
    return {n1: a_s, "Metric": label, n2: b_s, "Edge": edge}


summary = pd.DataFrame([
    cmp_row("Derived strength", "overall", "{:.1f}"),
    cmp_row("WC appearances", "appearances"),
    cmp_row("WC starts", "starts"),
    cmp_row("WC goals", "goals"),
    cmp_row("Age at 2026 WC", "age", "{:.0f}", lower_is_better=True),
])

st.subheader(f"{n1} vs {n2}")
st.dataframe(summary[[n1, "Metric", n2, "Edge"]], hide_index=True, width="stretch")

avail = [column for column in ATTR_COLS if column in players.columns]
if avail:
    st.subheader("Derived profile comparison")
    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        labels = [profile_label(column) for column in avail]
        for player, name in ((p1, n1), (p2, n2)):
            vals = [float(player.get(column, 0) or 0) for column in avail]
            fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=labels + [labels[0]], fill="toself", name=name))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=420,
            margin=dict(l=30, r=30, t=20, b=20),
        )
        st.plotly_chart(fig, width="stretch")
    except ImportError:
        cmp = pd.DataFrame(
            {
                n1: [float(p1.get(column, 0) or 0) for column in avail],
                n2: [float(p2.get(column, 0) or 0) for column in avail],
            },
            index=[profile_label(column) for column in avail],
        )
        st.bar_chart(cmp)

    diff_rows = []
    a_wins = b_wins = 0
    for column in avail:
        va, vb = float(p1.get(column, 0) or 0), float(p2.get(column, 0) or 0)
        if va > vb:
            a_wins += 1
        elif vb > va:
            b_wins += 1
        diff_rows.append({"Profile index": profile_label(column), n1: round(va), n2: round(vb), "Diff": round(va - vb)})
    st.dataframe(pd.DataFrame(diff_rows), hide_index=True, width="stretch")

    score_a = float(p1.get("overall", 0) or 0) + a_wins
    score_b = float(p2.get("overall", 0) or 0) + b_wins
    if score_a > score_b:
        st.success(f"Verdict: {n1} has the stronger real-data profile in this model view.")
    elif score_b > score_a:
        st.success(f"Verdict: {n2} has the stronger real-data profile in this model view.")
    else:
        st.info("Verdict: too close to call from the available real-data profile.")
