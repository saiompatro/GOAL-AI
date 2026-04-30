"""Players — per-team player roster + attribute radar."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))

try:
    from goal_ai import live_data
    from goal_ai.world_cup import canonical_team, is_qualified_2026, qualified_teams_present
except Exception:
    live_data = None
    canonical_team = None
    is_qualified_2026 = None
    qualified_teams_present = None


@st.cache_data
def _load_players() -> pd.DataFrame:
    path = ART / "players.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data
def _load_team_agg() -> pd.DataFrame:
    path = ART / "player_team_aggregates.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


st.title("GOAL AI — Players")

players = _load_players()
team_agg = _load_team_agg()
if live_data and live_data.is_configured():
    live_players = live_data.players()
    if not live_players.empty:
        players = live_players
        st.caption("Live backend: Firebase rosters")

if players.empty:
    st.error("No player data found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

invalid_values = {"", "n/a", "na", "not applicable", "unknown", "none", "null"}
for col in ["team", "player_name", "primary_position"]:
    if col in players.columns:
        values = players[col].astype("string").str.strip()
        players = players[values.notna() & ~values.str.lower().isin(invalid_values)]

if canonical_team:
    players = players.assign(team=players["team"].apply(canonical_team))

if is_qualified_2026:
    players = players[players["team"].apply(is_qualified_2026)]

if players.empty:
    st.error("No current 2026 qualified-team player data found.")
    st.stop()

team_names = players["team"].dropna().unique().tolist()
teams = qualified_teams_present(set(team_names)) if qualified_teams_present else sorted(team_names)
team = st.selectbox("Select team", teams, index=teams.index("Brazil") if "Brazil" in teams else 0)

roster = players[players["team"] == team].sort_values("overall", ascending=False)

if roster.empty:
    st.warning(f"No roster rows found for {team}.")
    st.stop()

# ── Team aggregate stats ───────────────────────────────────────────────────────
if not team_agg.empty and team in team_agg["team"].values:
    agg = team_agg[team_agg["team"] == team].iloc[0]
    st.subheader(f"Squad strength — {team}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Squad mean", f"{agg.get('squad_mean', 0):.1f}")
    c2.metric("Top-11 mean", f"{agg.get('top11_mean', 0):.1f}")
    c3.metric("Star-3 mean", f"{agg.get('star3_mean', 0):.1f}")
    c4.metric("Players", len(roster))

# ── Radar chart for top player ─────────────────────────────────────────────────
attr_cols = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]
available_attrs = [c for c in attr_cols if c in roster.columns]

if not roster.empty and available_attrs:
    st.subheader("Attribute radar — top players")
    n_players = min(5, len(roster))
    selected_players = st.multiselect(
        "Compare players (up to 5)",
        roster["player_name"].tolist(),
        default=roster["player_name"].tolist()[:min(3, len(roster))],
    )
    if selected_players:
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            for _, row in roster[roster["player_name"].isin(selected_players)].iterrows():
                values = [float(row.get(a, 0) or 0) for a in available_attrs]
                values.append(values[0])  # close the polygon
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=available_attrs + [available_attrs[0]],
                    fill="toself",
                    name=row["player_name"],
                ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for radar charts: `pip install plotly`")

# ── Full roster table ──────────────────────────────────────────────────────────
st.subheader(f"Full roster — {team}")
display_cols = [c for c in ["player_name", "primary_position", "overall", "potential",
                              "age", "preferred_foot", "club_name",
                              "pace", "shooting", "passing", "dribbling", "defending", "physic",
                              "value_eur", "wage_eur"] if c in roster.columns]
display_roster = roster[display_cols].replace(
    to_replace=r"(?i)^\s*(not applicable|n/a|na|unknown|null|none)\s*$",
    value="",
    regex=True,
)
st.dataframe(display_roster, use_container_width=True, hide_index=True)
