# GOAL AI — Research Notes

## 1. Datasets (selected)

### Core match history
- **`martj42/international-football-results-from-1872-to-2017`** (Kaggle, continuously updated through 2024+)
  - ~45k international matches. Columns: date, home_team, away_team, home_score, away_score, tournament, city, country, neutral.
  - Chosen because: canonical, clean, long history → enables Elo and form features.

### Tournament context
- **`abecklas/fifa-world-cup`** — WC-specific matches, stages, venues.
  - Chosen for tournament-stage flags and host-advantage features.

### Player / squad strength
- **`stefanoleone992/fifa-23-complete-player-dataset`** (and FIFA 15–24 variants)
  - Player overall, positions, attributes, club + nationality.
  - Chosen because: only reliable public per-player rating with wide international coverage. Used to compute squad-strength and star-power features keyed on `nationality`.

### Elo reference
- **eloratings.net export (scraped snapshot)** — used as validation signal, not primary feature.
  - We compute our own Elo from the match history to avoid dependency; eloratings used to sanity-check.

### Rejected / weak alternatives
- **StatsBomb open-data** — excellent event data, but very limited international coverage; rejected for scope.
- **Understat** — domestic leagues only.
- **Sofascore / Transfermarkt scrapes** — ToS risk, skipped.
- **Single WC-only datasets** — too little data to train a stable classifier; used as context only.

### Reference notebook
- `sarazahran1/world-cup-2026-match-predictor` (Kaggle) — borrowed feature ideas (rolling form windows, rank diffs). Not the modeling approach (basic).

## 2. Models (selected)

### Final stack
1. **XGBoost multi-class classifier** — primary.
   - Strong on tabular, fast, native handling of missing values, SHAP-friendly.
2. **LightGBM** — secondary comparison; often competitive with XGB.
3. **PyTorch feed-forward NN** (2 hidden layers, dropout, batch-norm) — captures non-linearities XGB may miss; calibrated with temperature scaling.
4. **Stacked ensemble**: XGB + LGBM + NN out-of-fold predictions → Logistic Regression meta-learner.

### Baseline (for comparison only)
- **Multinomial Logistic Regression** on a small feature set. Required by spec as benchmark.

### Selection rule
Pick final model by **validation log-loss** and **Brier score** (proper scoring rules for probabilistic forecasting), tie-break on **macro-F1**. Calibrate the chosen model (Isotonic if enough data, else Platt).

### Rejected
- **Deep sequence models (LSTM/Transformer on match history)** — data volume is marginal per team (~200–400 matches), likely to overfit vs XGB. Revisit if we add club-match data.
- **Pure Poisson / Dixon-Coles goal models** — strong classical baseline but less flexible with rich features; kept out of scope for v1.

## 3. Hugging Face usage (justified)

- **`sshleifer/distilbart-cnn-12-6`** — summarize pre-assembled stat blocks into readable insights on the Players/Teams pages. Small, CPU-runnable.
- **`sentence-transformers/all-MiniLM-L6-v2`** — player-similarity embeddings ("players like X") for the Players page.
- Not used: large generative LLMs (hallucination risk on specific player facts without grounding).

Rule: HF runs offline as a batch job; outputs cached in Supabase `insights` table. Never on the prediction hot path.

## 4. Feature engineering

| Feature | Source | Notes |
|---|---|---|
| Elo pre-match (home, away, diff) | Computed rolling over match history | K=30, home-advantage bonus +65 |
| Form last N=5,10 (W%, GF, GA, GD) | Match history | Per-team, per-side-adjusted |
| Head-to-head last 5 meetings | Match history | Win rate, avg GD |
| Days rest | Match history dates | Capped at 30 |
| Tournament stage | WC dataset | One-hot: group, R16, QF, SF, Final, Friendly, Qualifier |
| Neutral venue | Match history | Bool |
| Home advantage | Match history | Bool (home != neutral) |
| Squad rating mean (top-11) | FIFA player ratings | Grouped by nationality, most recent year |
| Attack/Mid/Def mean | FIFA player ratings | By position group |
| Star power (top-3 overall mean) | FIFA player ratings | Differentiator for top teams |
| Confederation | Teams table | One-hot |

## 5. Evaluation plan

- Time-based split: train ≤ 2018, val 2019–2021, test 2022+ (includes WC 2022).
- Metrics: log-loss, Brier, macro-F1, accuracy, confusion matrix, reliability diagram.
- Explainability: SHAP summary + per-prediction top-k drivers.
- Output: `ml/artifacts/metrics.json`, `ml/artifacts/confusion_matrix.png`, `ml/artifacts/shap_summary.png`.
