"""Bracket odds from the 2026 Monte Carlo simulation."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))


@st.cache_data
def _load_simulation() -> pd.DataFrame:
    path = ART / "simulation.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


st.title("GOAL AI - 2026 Bracket")

sim = _load_simulation()
if sim.empty:
    st.error("No simulation artifact found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

leader = sim.sort_values("p_win", ascending=False).head(8)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Teams", len(sim))
c2.metric("Champion sum", f"{sim['p_win'].sum():.3f}")
c3.metric("Favorite", leader.iloc[0]["team"])
c4.metric("Favorite p(win)", f"{leader.iloc[0]['p_win']:.1%}")

st.subheader("Title Race")
st.bar_chart(leader.set_index("team")["p_win"])

st.subheader("Round Probabilities")
st.caption("Column legend: p_win = champion probability, p_final = reaches final, p_semi = reaches semi-final, p_quarter = reaches quarter-final, p_groupexit = exits in group stage.")
display = sim.copy()
for col in ["p_win", "p_final", "p_semi", "p_quarter", "p_groupexit"]:
    display[col] = display[col].map(lambda x: f"{x:.1%}")
st.dataframe(display, use_container_width=True, hide_index=True)
