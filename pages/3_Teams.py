"""Teams — Elo chart + rolling form per team."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))


@st.cache_data
def _load_features() -> pd.DataFrame:
    path = ART / "features.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


st.title("GOAL AI — Teams")

feats = _load_features()
if feats.empty:
    st.error("No feature data found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

all_teams = sorted(set(feats["home_team"].tolist() + feats["away_team"].tolist()))
team = st.selectbox("Select team", all_teams, index=all_teams.index("Brazil") if "Brazil" in all_teams else 0)

# Filter matches involving this team
home_m = feats[feats["home_team"] == team][["date", "elo_home_pre", "home_win_rate_5",
                                              "home_gf_5", "home_ga_5"]].rename(columns={
    "elo_home_pre": "elo",
    "home_win_rate_5": "win_rate_5",
    "home_gf_5": "gf_5",
    "home_ga_5": "ga_5",
})
away_m = feats[feats["away_team"] == team][["date", "elo_away_pre", "away_win_rate_5",
                                              "away_gf_5", "away_ga_5"]].rename(columns={
    "elo_away_pre": "elo",
    "away_win_rate_5": "win_rate_5",
    "away_gf_5": "gf_5",
    "away_ga_5": "ga_5",
})
team_df = pd.concat([home_m, away_m]).sort_values("date").reset_index(drop=True)

if team_df.empty:
    st.warning(f"No matches found for {team}.")
    st.stop()

# ── Elo chart ─────────────────────────────────────────────────────────────────
st.subheader(f"Elo rating history — {team}")
try:
    import plotly.express as px
    fig = px.line(team_df, x="date", y="elo", labels={"elo": "Elo", "date": "Date"})
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)
except ImportError:
    st.line_chart(team_df.set_index("date")["elo"])

# ── Rolling form ──────────────────────────────────────────────────────────────
st.subheader("Rolling form (last 5 matches, pre-match averages)")
latest = team_df.tail(1).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Current Elo", f"{latest['elo']:.0f}")
c2.metric("Win rate (5)", f"{latest['win_rate_5']:.1%}")
c3.metric("Goals for (5)", f"{latest['gf_5']:.2f}")
c4.metric("Goals against (5)", f"{latest['ga_5']:.2f}")

# Rolling stats trend
trend_cols = [c for c in ["win_rate_5", "gf_5", "ga_5"] if c in team_df.columns]
if trend_cols:
    try:
        import plotly.express as px
        fig2 = px.line(team_df.tail(50), x="date", y=trend_cols,
                       labels={"value": "Value", "date": "Date", "variable": "Metric"})
        fig2.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig2, use_container_width=True)
    except ImportError:
        st.line_chart(team_df.set_index("date")[trend_cols].tail(50))

# Recent match history
st.subheader("Recent matches")
history_cols = [c for c in ["date", "home_team", "away_team", "result", "tournament"] if c in feats.columns]
recent = feats[
    (feats["home_team"] == team) | (feats["away_team"] == team)
][history_cols].sort_values("date", ascending=False).head(20)
st.dataframe(recent, use_container_width=True, hide_index=True)
