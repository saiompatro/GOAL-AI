"""Dashboard — model stats panel + recent fixture table."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve paths
_ROOT = Path(__file__).resolve().parents[1]
ART = _ROOT / "ml" / "artifacts"
sys.path.insert(0, str(_ROOT / "ml" / "src"))


@st.cache_data
def _load_metrics() -> dict:
    path = ART / "metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@st.cache_data
def _load_features() -> pd.DataFrame:
    path = ART / "features.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


st.title("GOAL AI — Dashboard")

metrics = _load_metrics()
feats = _load_features()

# ── Model summary ────────────────────────────────────────────────────────────
if metrics:
    chosen = metrics.get("chosen", "—")
    version = metrics.get("version", "—")
    m = metrics.get("metrics", {}).get(chosen, {})
    test = m.get("test", {})

    st.subheader("Model summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Chosen model", chosen.upper())
    c2.metric("Version", version)
    c3.metric("Test log-loss", f"{test.get('log_loss', float('nan')):.4f}")
    c4.metric("Test accuracy", f"{test.get('accuracy', float('nan')):.1%}")

    # Comparison table
    st.subheader("All models — test metrics")
    rows = []
    for name, mv in metrics.get("metrics", {}).items():
        t = mv.get("test", {})
        rows.append({
            "model": name,
            "log-loss": round(t.get("log_loss", float("nan")), 4),
            "brier": round(t.get("brier", float("nan")), 4),
            "macro-F1": round(t.get("macro_f1", float("nan")), 3),
            "accuracy": f"{t.get('accuracy', float('nan')):.1%}",
            "chosen": "✓" if name == chosen else "",
        })
    st.dataframe(pd.DataFrame(rows).set_index("model"), use_container_width=True)
else:
    st.warning("No metrics.json found. Run `python ml/scripts/run_pipeline.py` first.")

# ── Recent fixtures ───────────────────────────────────────────────────────────
if not feats.empty:
    st.subheader("Recent fixtures")
    display_cols = [c for c in ["date", "home_team", "away_team", "home_score",
                                 "away_score", "result", "tournament",
                                 "elo_home_pre", "elo_away_pre", "elo_diff"] if c in feats.columns]
    recent = feats[display_cols].tail(50).sort_values("date", ascending=False)
    st.dataframe(recent, use_container_width=True, hide_index=True)
else:
    st.info("features.parquet not found. Run the pipeline to generate it.")
