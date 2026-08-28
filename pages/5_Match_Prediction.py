"""Match Analysis + Predictor - venue and weather aware probabilities."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _shared import canonical_team, index_of, load_features  # noqa: E402

SRC = Path(__file__).resolve().parents[1] / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from goal_ai import venues as venue_mod  # noqa: E402
from goal_ai import weather as weather_mod  # noqa: E402
from goal_ai.match_context import adjust  # noqa: E402

st.title("Match Analysis + Predictor")
st.caption("Analyze a FIFA 2026 fixture with real match history, host venue metadata, and weather context.")

feats = load_features()
if feats.empty:
    st.error("No feature data found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

teams = sorted(set(feats["home_team"].apply(canonical_team)) | set(feats["away_team"].apply(canonical_team)))
venue_labels = venue_mod.venue_names()

with st.expander("Data sources in this view", expanded=False):
    st.markdown(
        "- Match-history features: real international results and historical World Cup records.\n"
        "- Player/team strength: derived from real roster and event data, not EA/SOFIFA ratings.\n"
        "- Venue context: curated FIFA 2026 host-stadium metadata.\n"
        "- Weather: Open-Meteo forecast or climatology fallback."
    )

prefill: dict[str, str] = {}
sched = venue_mod.load_schedule()
if not sched.empty:
    rowmap = {}
    for row in sched.itertuples(index=False):
        label = f"Match {row.match_no} | {row.date} | {row.stage}: {row.home} v {row.away} @ {row.venue}"
        rowmap[label] = row
    pick = st.selectbox("Prefill from the 2026 schedule", ["Pick manually"] + list(rowmap))
    if pick in rowmap:
        row = rowmap[pick]
        prefill = {
            "home": canonical_team(row.home),
            "away": canonical_team(row.away),
            "venue": venue_mod.label_for_stadium(row.venue) or "",
            "date": str(row.date),
        }
        st.caption("For undrawn or placeholder teams, keep the venue/date and choose the teams manually.")


def _team_idx(key: str, fallback: str, fb_pos: int = 0) -> int:
    value = prefill.get(key)
    fallback_idx = index_of(teams, fallback, fb_pos)
    return index_of(teams, value, fallback_idx) if value in teams else fallback_idx


def _date_default() -> date:
    try:
        return date.fromisoformat(prefill["date"]) if prefill.get("date") else date(2026, 6, 11)
    except Exception:  # noqa: BLE001
        return date(2026, 6, 11)


c1, c2 = st.columns(2)
with c1:
    home = st.selectbox("Home / first team", teams, index=_team_idx("home", "Mexico"))
with c2:
    away = st.selectbox("Away / second team", teams, index=_team_idx("away", "Brazil", 1))

c3, c4 = st.columns(2)
with c3:
    venue_idx = index_of(venue_labels, prefill["venue"]) if prefill.get("venue") in venue_labels else 0
    venue_label = st.selectbox("FIFA 2026 stadium", venue_labels, index=venue_idx) if venue_labels else None
with c4:
    match_date = st.date_input("Match date", value=_date_default(), min_value=date(2026, 1, 1))

stage = st.selectbox(
    "Stage",
    ["FIFA World Cup", "FIFA World Cup - Knockout", "Friendly", "FIFA World Cup Qualifier"],
    index=0,
)

go_btn = st.button("Analyze and predict", type="primary")

if go_btn:
    if home == away:
        st.warning("Pick two different teams.")
        st.stop()
    venue = venue_mod.get_venue(venue_label) if venue_label else {}

    with st.spinner("Running model and loading match-day context..."):
        try:
            from goal_ai.predict import predict_fixture

            base = predict_fixture(home, away, neutral=True, stage=stage)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Prediction failed: {exc}")
            st.stop()

        weather = {"source": "unavailable"}
        if venue:
            weather = weather_mod.match_day_weather(float(venue["lat"]), float(venue["lon"]), match_date)

        result = adjust(base, home, away, venue, weather, host_country=venue.get("country"))

    if venue:
        st.subheader(f"{venue['venue']} - {venue['city']}, {venue['country']}")
        v = st.columns(4)
        v[0].metric("Roof", str(venue.get("roof", "-")).title())
        v[1].metric("Surface", str(venue.get("surface", "-")).title())
        v[2].metric("Elevation", f"{venue.get('elevation_m', 0):.0f} m")
        v[3].metric("Capacity", f"{venue.get('capacity', 0):,.0f}")
        st.caption(venue.get("climate_note", ""))

    st.subheader(f"Weather context - {match_date:%d %b %Y}")
    if weather.get("source") == "unavailable":
        st.info("Weather data unavailable. The prediction uses venue conditions only.")
    else:
        w = st.columns(4)
        w[0].metric("Temp", f"{weather['temp_c']:.0f} C")
        w[1].metric("Rain", f"{weather['precip_mm']:.0f} mm")
        w[2].metric("Wind", f"{weather['wind_kmh']:.0f} km/h")
        w[3].metric("Humidity", f"{weather['humidity']:.0f}%")
        st.caption(f"{weather['summary']} | source: {weather['source']}")

    st.subheader("Outcome probability")
    ph, pdr, pa = result.p_home, result.p_draw, result.p_away
    try:
        import plotly.graph_objects as go

        fig = go.Figure(go.Bar(
            x=[ph, pdr, pa],
            y=[f"{home} win", "Draw", f"{away} win"],
            orientation="h",
            marker_color=["#2e7d32", "#9e9e9e", "#1565c0"],
            text=[f"{value:.1%}" for value in (ph, pdr, pa)],
            textposition="auto",
        ))
        fig.update_layout(xaxis=dict(range=[0, 1], tickformat=".0%"), height=220, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    except ImportError:
        cols = st.columns(3)
        cols[0].metric(f"{home} win", f"{ph:.1%}")
        cols[1].metric("Draw", f"{pdr:.1%}")
        cols[2].metric(f"{away} win", f"{pa:.1%}")

    winner = max(((ph, home), (pdr, "Draw"), (pa, away)))
    o = st.columns(2)
    o[0].metric("Most likely result", winner[1], f"{winner[0]:.0%}")
    o[1].metric("Projected scoreline", f"{home} {result.likely_score} {away}", f"xG {result.xg_home}-{result.xg_away}")

    st.subheader("Why the prediction moved")
    baseline = (
        f"Model baseline, neutral: {home} {base['p_home']:.0%} | "
        f"Draw {base['p_draw']:.0%} | {away} {base['p_away']:.0%}"
    )
    st.caption(baseline)
    if result.factors:
        for factor in result.factors:
            st.markdown(f"- {factor}")
    else:
        st.markdown("- No notable venue or weather effects. Baseline model probabilities used.")

    st.caption(
        f"Base model: {base.get('chosen_model', '?').upper()} "
        f"(v{base.get('model_version', '?')}). Condition adjustments are bounded."
    )
