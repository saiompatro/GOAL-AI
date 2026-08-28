"""Team Head to Head - compare two national teams."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import PLAYER_EMPTY_MESSAGE, canonical_team, index_of, load_features, load_team_agg, team_match_list  # noqa: E402

st.title("Team Head to Head")
st.caption("Compare form, squad-derived indices, and the all-time real match record.")

feats = load_features()
if feats.empty:
    st.error("No feature data found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

teams = team_match_list(feats)
if not teams:
    st.error("No eligible teams found in the feature data.")
    st.stop()

home_names = feats["home_team"].apply(canonical_team)
away_names = feats["away_team"].apply(canonical_team)

c1, c2 = st.columns(2)
with c1:
    t1 = st.selectbox("Team A", teams, index=index_of(teams, "Brazil"))
with c2:
    t2 = st.selectbox("Team B", teams, index=index_of(teams, "Argentina", 1))

if t1 == t2:
    st.warning("Pick two different teams.")
    st.stop()


def latest_state(team: str) -> dict:
    home = feats[home_names == team][["date", "elo_home_pre", "home_win_rate_5", "home_gf_5", "home_ga_5"]].rename(
        columns={"elo_home_pre": "elo", "home_win_rate_5": "wr", "home_gf_5": "gf", "home_ga_5": "ga"}
    )
    away = feats[away_names == team][["date", "elo_away_pre", "away_win_rate_5", "away_gf_5", "away_ga_5"]].rename(
        columns={"elo_away_pre": "elo", "away_win_rate_5": "wr", "away_gf_5": "gf", "away_ga_5": "ga"}
    )
    both = pd.concat([home, away]).sort_values("date")
    return both.tail(1).iloc[0].to_dict() if not both.empty else {}


agg = load_team_agg()


def agg_of(team: str) -> dict:
    row = agg[agg["team"] == team] if not agg.empty else pd.DataFrame()
    return row.iloc[0].to_dict() if not row.empty else {}


def cmp_row(label: str, va: object, vb: object, fmt: str = "{:.0f}", lower_is_better: bool = False) -> dict:
    va = float(va or 0)
    vb = float(vb or 0)
    if lower_is_better:
        edge = "A" if va and (not vb or va < vb) else ("B" if vb and (not va or vb < va) else "=")
    else:
        edge = "A" if va > vb else ("B" if vb > va else "=")
    return {t1: fmt.format(va), "Metric": label, t2: fmt.format(vb), "Edge": edge}


s1, s2 = latest_state(t1), latest_state(t2)
a1, a2 = agg_of(t1), agg_of(t2)

st.subheader(f"{t1} vs {t2}")
rows = [
    cmp_row("Current Elo", s1.get("elo"), s2.get("elo")),
    cmp_row("Win rate, last 5", (s1.get("wr") or 0) * 100, (s2.get("wr") or 0) * 100, "{:.0f}%"),
    cmp_row("Goals for, last 5", s1.get("gf"), s2.get("gf"), "{:.2f}"),
    cmp_row("Goals against, last 5", s1.get("ga"), s2.get("ga"), "{:.2f}", lower_is_better=True),
]
if a1 and a2:
    rows += [
        cmp_row("Squad strength index", a1.get("squad_mean"), a2.get("squad_mean"), "{:.1f}"),
        cmp_row("Top-11 index", a1.get("top11_mean"), a2.get("top11_mean"), "{:.1f}"),
        cmp_row("Star-3 index", a1.get("star3_mean"), a2.get("star3_mean"), "{:.1f}"),
    ]
st.dataframe(pd.DataFrame(rows)[[t1, "Metric", t2, "Edge"]], hide_index=True, width="stretch")
if a1 and a2:
    st.caption("Squad indices are calculated only from eligible World Cup starters/substitutes or official squad players.")
else:
    st.info(PLAYER_EMPTY_MESSAGE)

st.subheader("All-time meetings")
mask = ((home_names == t1) & (away_names == t2)) | ((home_names == t2) & (away_names == t1))
meets = feats[mask].copy()
if meets.empty:
    st.info(f"No recorded meetings between {t1} and {t2} in the dataset.")
else:
    meets["hn"] = home_names[mask]
    meets["an"] = away_names[mask]
    t1_w = t2_w = draws = t1_gf = t2_gf = 0
    for row in meets.itertuples(index=False):
        home_score, away_score = getattr(row, "home_score", 0), getattr(row, "away_score", 0)
        if row.hn == t1:
            t1_gf += home_score
            t2_gf += away_score
        else:
            t1_gf += away_score
            t2_gf += home_score
        if row.result == "D":
            draws += 1
        elif (row.result == "H" and row.hn == t1) or (row.result == "A" and row.an == t1):
            t1_w += 1
        else:
            t2_w += 1

    m = st.columns(5)
    m[0].metric("Meetings", len(meets))
    m[1].metric(f"{t1} wins", t1_w)
    m[2].metric("Draws", draws)
    m[3].metric(f"{t2} wins", t2_w)
    m[4].metric("Goals", f"{t1_gf}-{t2_gf}")

    if t1_w > t2_w:
        st.success(f"{t1} has the historical edge ({t1_w}-{draws}-{t2_w}).")
    elif t2_w > t1_w:
        st.success(f"{t2} has the historical edge ({t2_w}-{draws}-{t1_w}).")
    else:
        st.info(f"Honors even historically ({t1_w}-{draws}-{t2_w}).")

    show = [
        column
        for column in ["date", "home_team", "away_team", "home_score", "away_score", "result", "tournament"]
        if column in meets.columns
    ]
    st.dataframe(meets[show].sort_values("date", ascending=False).head(30), width="stretch", hide_index=True)

st.caption("For a venue- and weather-aware probability, use Match Analysis + Predictor.")
