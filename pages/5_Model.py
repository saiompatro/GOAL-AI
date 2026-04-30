"""Model — model card, SHAP plots, reliability diagram."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))

try:
    from goal_ai import live_data
except Exception:
    live_data = None

st.title("GOAL AI — Model Card")

if live_data and live_data.is_configured():
    runs = live_data.model_runs(limit=10)
    if not runs.empty:
        st.subheader("Firebase model run history")
        display = runs.copy()
        if "metrics" in display.columns:
            display["metrics"] = display["metrics"].apply(lambda value: json.dumps(value)[:160])
        st.dataframe(display, use_container_width=True, hide_index=True)

# ── Model card markdown ────────────────────────────────────────────────────────
card_path = ART / "model_card.md"
if card_path.exists():
    st.markdown(card_path.read_text(encoding="utf-8"))
else:
    st.warning("model_card.md not found. Run the pipeline to generate it.")

st.divider()

# ── Visualisations ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    shap_path = ART / "shap_summary.png"
    if shap_path.exists():
        st.subheader("SHAP feature importance")
        st.image(str(shap_path), use_container_width=True)
    else:
        st.info("shap_summary.png not found.")

with col2:
    rel_path = ART / "reliability.png"
    if rel_path.exists():
        st.subheader("Reliability diagram")
        st.image(str(rel_path), use_container_width=True)
    else:
        st.info("reliability.png not found.")

cm_path = ART / "confusion_matrix.png"
if cm_path.exists():
    st.subheader("Confusion matrix")
    st.image(str(cm_path), use_container_width=True)
else:
    st.info("confusion_matrix.png not found.")

# ── Raw metrics JSON ───────────────────────────────────────────────────────────
metrics_path = ART / "metrics.json"
if metrics_path.exists():
    with st.expander("Raw metrics.json"):
        st.json(json.loads(metrics_path.read_text()))
