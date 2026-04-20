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
| lr         | 0.8386 | 0.1638 | 0.473 | 0.8837 | 0.1731 | 0.449 | 0.598 |
| xgb        | 0.8389 | 0.1639 | 0.490 | 0.8872 | 0.1735 | 0.467 | 0.599 |
| lgbm       | 0.8551 | 0.1670 | 0.491 | 0.9114 | 0.1772 | 0.472 | 0.591 |
| nn         | 0.8359 | 0.1635 | 0.467 | 0.8839 | 0.1729 | 0.447 | 0.601 |
| stack      | 0.8311 | 0.1620 | 0.484 | 0.8813 | 0.1727 | 0.460 | 0.602 |

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
