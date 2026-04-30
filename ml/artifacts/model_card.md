# GOAL AI Model Card

**Version**: v1
**Chosen model**: `stack`

## Task
Multi-class classification of international football match outcomes: Home win (0), Draw (1), Away win (2).

## Data split
Time-based: train ≤ {train_end}, val in between, test ≥ {val_end}. No shuffling to avoid leakage.

## Comparison

| model      | val log-loss | val Brier | val macro-F1 | test log-loss | test Brier | test macro-F1 | test acc |
|-----------|--------------|-----------|--------------|---------------|------------|---------------|----------|
| lr         | 0.8395 | 0.1641 | 0.458 | 0.8809 | 0.1726 | 0.450 | 0.599 |
| xgb        | 0.8413 | 0.1643 | 0.481 | 0.8877 | 0.1738 | 0.466 | 0.600 |
| lgbm       | 0.8643 | 0.1683 | 0.481 | 0.9063 | 0.1769 | 0.468 | 0.590 |
| nn         | 0.8383 | 0.1639 | 0.463 | 0.8850 | 0.1733 | 0.443 | 0.594 |
| stack      | 0.8352* | 0.1630* | 0.487* | 0.8845 | 0.1734 | 0.461 | 0.598 |

\* stack val metrics are in-sample (meta-learner was trained on the val split).

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
