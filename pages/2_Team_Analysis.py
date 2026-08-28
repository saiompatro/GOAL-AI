"""Team Analysis - national-team real-data profile."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import PLAYER_EMPTY_MESSAGE, canonical_team, index_of, load_features, load_team_agg, team_match_list  # noqa: E402

st.title("Team Analysis")
st.caption("Elo trajectory, recent form, squad-derived indices, and real match history.")

feats = load_features()
if feats.empty:
    st.error("No feature data found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

teams = team_match_list(feats)
if not teams:
    st.error("No eligible teams found in the feature data.")
    st.stop()

team = st.selectbox("Team", teams, index=index_of(teams, "Brazil"))

home_names = feats["home_team"].apply(canonical_team)
away_names = feats["away_team"].apply(canonical_team)

home_m = feats[home_names == team][["date", "elo_home_pre", "home_win_rate_5", "home_gf_5", "home_ga_5"]].rename(
    columns={"elo_home_pre": "elo", "home_win_rate_5": "win_rate_5", "home_gf_5": "gf_5", "home_ga_5": "ga_5"}
)
away_m = feats[away_names == team][["date", "elo_away_pre", "away_win_rate_5", "away_gf_5", "away_ga_5"]].rename(
    columns={"elo_away_pre": "elo", "away_win_rate_5": "win_rate_5", "away_gf_5": "gf_5", "away_ga_5": "ga_5"}
)
team_df = pd.concat([home_m, away_m]).sort_values("date").reset_index(drop=True)
if team_df.empty:
    st.warning(f"No matches found for {team}.")
    st.stop()

latest = team_df.tail(1).iloc[0]
agg = load_team_agg()
team_agg = agg[agg["team"] == team] if not agg.empty else pd.DataFrame()

st.subheader("Current snapshot")
m = st.columns(4)
m[0].metric("Current Elo", f"{latest['elo']:.0f}")
m[1].metric("Win rate, last 5", f"{latest['win_rate_5']:.0%}")
m[2].metric("Goals for, last 5", f"{latest['gf_5']:.2f}")
m[3].metric("Goals against, last 5", f"{latest['ga_5']:.2f}")

if not team_agg.empty:
    a = team_agg.iloc[0]
    m2 = st.columns(4)
    m2[0].metric("Squad strength index", f"{a.get('squad_mean', 0):.1f}")
    m2[1].metric("Top-11 index", f"{a.get('top11_mean', 0):.1f}")
    m2[2].metric("Star-3 index", f"{a.get('star3_mean', 0):.1f}")
    m2[3].metric("Attack / defense", f"{a.get('att_mean', 0):.0f} / {a.get('def_mean', 0):.0f}")
    st.caption("Squad indices are calculated only from eligible World Cup starters/substitutes or official squad players.")
else:
    st.info(PLAYER_EMPTY_MESSAGE)

st.subheader(f"Elo history - {team}")
try:
    import plotly.express as px

    fig = px.line(team_df, x="date", y="elo", labels={"elo": "Elo", "date": "Date"})
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
except ImportError:
    st.line_chart(team_df.set_index("date")["elo"])

st.subheader("Recent form trend")
trend_cols = [column for column in ["win_rate_5", "gf_5", "ga_5"] if column in team_df.columns]
try:
    import plotly.express as px

    fig2 = px.line(
        team_df.tail(40),
        x="date",
        y=trend_cols,
        labels={"value": "Value", "date": "Date", "variable": "Metric"},
    )
    fig2.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, width="stretch")
except ImportError:
    st.line_chart(team_df.set_index("date")[trend_cols].tail(40))

st.subheader("Recent matches")
st.caption("Result: H = home win, D = draw, A = away win.")
hist_cols = [column for column in ["date", "home_team", "away_team", "result", "tournament"] if column in feats.columns]
recent = feats[(home_names == team) | (away_names == team)][hist_cols].sort_values("date", ascending=False).head(25)
st.dataframe(recent, width="stretch", hide_index=True)
