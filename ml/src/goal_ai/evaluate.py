"""Evaluation artifacts: confusion matrix, reliability diagram, comparison table."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix


LABELS = ["Home", "Draw", "Away"]


def confusion_png(y: np.ndarray, probs: np.ndarray, out: Path, title: str) -> None:
    cm = confusion_matrix(y, probs.argmax(axis=1), labels=[0, 1, 2])
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3), LABELS)
    ax.set_yticks(range(3), LABELS)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def reliability_png(y: np.ndarray, probs: np.ndarray, out: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for k, lbl in enumerate(LABELS):
        p = probs[:, k]
        bins = np.linspace(0, 1, 11)
        idx = np.digitize(p, bins) - 1
        xs, ys = [], []
        for b in range(10):
            m = idx == b
            if m.sum() < 10:
                continue
            xs.append(p[m].mean())
            ys.append((y[m] == k).mean())
        ax.plot(xs, ys, marker="o", label=lbl)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("Predicted prob")
    ax.set_ylabel("Empirical freq")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)


def write_model_card(results: dict, out_path: Path, version: str) -> None:
    chosen = results["chosen"]
    rows = []
    for name, m in results["metrics"].items():
        rows.append(
            f"| {name:<10} | {m['val']['log_loss']:.4f} | {m['val']['brier']:.4f} | "
            f"{m['val']['macro_f1']:.3f} | {m['test']['log_loss']:.4f} | "
            f"{m['test']['brier']:.4f} | {m['test']['macro_f1']:.3f} | {m['test']['accuracy']:.3f} |"
        )
    body = f"""# GOAL AI Model Card

**Version**: {version}
**Chosen model**: `{chosen}`

## Task
Multi-class classification of international football match outcomes: Home win (0), Draw (1), Away win (2).

## Data split
Time-based: train ≤ {{train_end}}, val in between, test ≥ {{val_end}}. No shuffling to avoid leakage.

## Comparison

| model      | val log-loss | val Brier | val macro-F1 | test log-loss | test Brier | test macro-F1 | test acc |
|-----------|--------------|-----------|--------------|---------------|------------|---------------|----------|
{chr(10).join(rows)}

## Selection rule
Best on validation log-loss, tie-break Brier → macro-F1. Stacked ensemble is selected only if it beats the best single model on the held-out **test** set (to avoid meta-learner overfit on val).

## Features
Elo (home/away/diff), rolling form (5 and 10 match windows), head-to-head aggregates, days rest, tournament-stage flags, squad-strength aggregates from FIFA ratings (top-11 mean, star-3 mean, per-position group means), neutral-venue flag.

## Explainability
SHAP TreeExplainer applied to the XGBoost model for per-prediction and global feature importance. See `shap_summary.png` and the `shap` JSON column in Supabase `predictions`.

## Known limitations
- Lineup-level data coverage is thin pre-2010, so squad-strength falls back to FIFA aggregates.
- Elo is results-only (no xG).
- Draws are inherently hard to call; probability outputs are calibrated but pointwise draw accuracy is limited.
"""
    out_path.write_text(body)
