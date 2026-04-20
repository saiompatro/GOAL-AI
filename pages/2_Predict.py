"""Predict — real-time fixture prediction workbench."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))


@st.cache_data
def _team_list() -> list[str]:
    path = ART / "features.parquet"
    if not path.exists():
        return []
    feats = pd.read_parquet(path, columns=["home_team", "away_team"])
    teams = sorted(set(feats["home_team"].tolist() + feats["away_team"].tolist()))
    return teams


st.title("GOAL AI — Predict")
st.caption("Select two teams and click **Predict** to get a probability breakdown.")

teams = _team_list()
if not teams:
    st.error("No feature data found. Run `python ml/scripts/run_pipeline.py` first.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    home = st.selectbox("Home team", teams, index=teams.index("Brazil") if "Brazil" in teams else 0)
with col2:
    away_default = teams.index("Argentina") if "Argentina" in teams else (1 if len(teams) > 1 else 0)
    away = st.selectbox("Away team", teams, index=away_default)

neutral = st.toggle("Neutral venue", value=False)
stage = st.text_input("Stage / Tournament", value="FIFA World Cup")

if st.button("Predict", type="primary"):
    if home == away:
        st.warning("Home and away teams must be different.")
    else:
        with st.spinner("Running model…"):
            try:
                from goal_ai.predict import predict_fixture
                result = predict_fixture(home, away, neutral=neutral, stage=stage)

                st.success(f"Prediction complete — model: **{result['chosen_model'].upper()}** (v{result['model_version']})")

                ph, pd_, pa = result["p_home"], result["p_draw"], result["p_away"]

                # Probability bar chart
                try:
                    import plotly.graph_objects as go
                    fig = go.Figure(go.Bar(
                        x=[ph, pd_, pa],
                        y=[f"{home} win", "Draw", f"{away} win"],
                        orientation="h",
                        marker_color=["#2196F3", "#9E9E9E", "#F44336"],
                        text=[f"{v:.1%}" for v in [ph, pd_, pa]],
                        textposition="auto",
                    ))
                    fig.update_layout(
                        title="Outcome probabilities",
                        xaxis=dict(range=[0, 1], tickformat=".0%"),
                        height=220,
                        margin=dict(l=10, r=10, t=40, b=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"{home} win", f"{ph:.1%}")
                    c2.metric("Draw", f"{pd_:.1%}")
                    c3.metric(f"{away} win", f"{pa:.1%}")

                st.metric("Model confidence", f"{result['confidence']:.1%}")

                # SHAP drivers
                if result.get("drivers"):
                    st.subheader("Top feature drivers (XGBoost SHAP)")
                    driver_df = pd.DataFrame(result["drivers"])
                    st.dataframe(driver_df, use_container_width=True, hide_index=True)

            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Prediction failed: {e}")
