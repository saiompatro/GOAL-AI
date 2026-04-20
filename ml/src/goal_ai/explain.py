"""SHAP-based explainability for the XGBoost model."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shap

from .features import FEATURE_COLUMNS


def build_explainer(xgb_model):
    return shap.TreeExplainer(xgb_model)


def global_summary_png(explainer, X_sample: np.ndarray, out: Path) -> None:
    sv = explainer.shap_values(X_sample)
    # Multi-class: list of arrays. Aggregate mean |shap| across classes.
    if isinstance(sv, list):
        mean_abs = np.mean([np.abs(s).mean(axis=0) for s in sv], axis=0)
    else:
        mean_abs = np.abs(sv).mean(axis=0)
        if mean_abs.ndim == 2:
            mean_abs = mean_abs.mean(axis=1)
    order = np.argsort(mean_abs)[-15:]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh([FEATURE_COLUMNS[i] for i in order], mean_abs[order])
    ax.set_xlabel("mean(|SHAP|)")
    ax.set_title("Top 15 features (global)")
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def top_drivers(explainer, x_row: np.ndarray, k: int = 5) -> list[dict]:
    """Return top-k features pushing the home-win class for a single row."""
    sv = explainer.shap_values(x_row.reshape(1, -1))
    if isinstance(sv, list):
        arr = sv[0][0]              # class 0 = Home win
    else:
        arr = sv[0] if sv.ndim == 2 else sv[0, :, 0]
    order = np.argsort(-np.abs(arr))[:k]
    return [
        {"feature": FEATURE_COLUMNS[i], "value": float(x_row[i]), "shap": float(arr[i])}
        for i in order
    ]
