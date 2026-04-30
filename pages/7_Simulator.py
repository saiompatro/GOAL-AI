"""Custom 2026 tournament simulation page."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
RAW = _ROOT / "data" / "raw"
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))


@st.cache_data
def _baseline() -> pd.DataFrame:
    path = ART / "simulation.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


st.title("GOAL AI - Custom Simulator")

baseline = _baseline()
if baseline.empty:
    st.error("No baseline simulation found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

team = st.selectbox("Team", baseline["team"].sort_values().tolist())
elo_delta = st.slider("Elo adjustment", min_value=-250, max_value=250, value=0, step=25)
n = st.slider("Simulation runs", min_value=1000, max_value=50000, value=10000, step=1000)

if st.button("Run simulation", type="primary"):
    from goal_ai.simulate import group_fixtures, load_2026_groups, simulate_tournament

    with st.spinner("Running tournament simulations..."):
        fixtures = group_fixtures(load_2026_groups(RAW))
        custom = simulate_tournament(
            model=None,
            fixtures_2026=fixtures,
            n=n,
            artifacts_dir=ART,
            strength_overrides={team: elo_delta},
        )

    merged = custom.merge(baseline, on="team", suffixes=("_custom", "_baseline"))
    row = merged[merged["team"].eq(team)].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("p(win)", f"{row['p_win_custom']:.1%}", f"{row['p_win_custom'] - row['p_win_baseline']:+.1%}")
    c2.metric("p(final)", f"{row['p_final_custom']:.1%}", f"{row['p_final_custom'] - row['p_final_baseline']:+.1%}")
    c3.metric("p(group exit)", f"{row['p_groupexit_custom']:.1%}", f"{row['p_groupexit_custom'] - row['p_groupexit_baseline']:+.1%}")

    diff = merged.assign(delta_win=merged["p_win_custom"] - merged["p_win_baseline"])
    st.subheader("Largest title-probability moves")
    st.dataframe(
        diff[["team", "p_win_baseline", "p_win_custom", "delta_win"]]
        .sort_values("delta_win", ascending=False)
        .head(15),
        use_container_width=True,
        hide_index=True,
    )
