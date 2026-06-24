# World Cup 2026 Match Predictor

A match-outcome engine for the 2026 World Cup. It returns win/draw/loss
probabilities and a full scoreline grid, plus derived goalscorer, match and
parlay markets, from a feature set built on 150+ years of international results.

Team strength fuses an international Elo computed over 48,000+ matches since 1872
with a club-level squad rating (each player mapped to his club's clubelo.com
rating), then layers in form, head-to-head, tournament experience, morale, live
news sentiment, jet lag and venue-climate mismatch. The outcome classifier is a
probability-averaged ensemble of five members — Optuna-tuned LightGBM,
GPU XGBoost, GPU CatBoost, a seed-ensembled PyTorch MLP and HistGradientBoosting —
with twin Poisson regressors driving the scoreline grid. Ratings update live from
the in-tournament match feed, so a group-stage result moves a team's Elo, form and
morale immediately.

On a strict time split (train <2022, test 2022→Jun 2026, 4,541 matches) it scores
**60.1% three-way accuracy / 0.871 log-loss**, against a 59.5% Elo-favourite
baseline — near the practical ceiling for three-way football prediction.

## Quick start

```powershell
pip install -r requirements.txt   # from the repo root
cd src
python app.py                     # starts the server; leave it running
```

Then open **http://127.0.0.1:5000** in a browser and predict a match.

Stop the server with `Ctrl+C` in that terminal (or `Stop-Process -Name python`).
The port defaults to 5000; override with `$env:PORT=8080; python app.py`.

The committed `models/fifa_model.joblib` (sklearn-only, ~1 MB) means it runs out
of the box — no training step needed. Live squad refresh and in-tournament form
need a free [football-data.org](https://www.football-data.org/client/register)
token: copy `.env.example` to `.env` and fill in `FOOTBALL_DATA_TOKEN`.

The GPU ensemble (`models/fifa_model_ensemble.joblib`) is used automatically when
its deps (torch, catboost, xgboost, lightgbm) are installed; if they're missing or
fail to load, `predict.py` falls back to the plain model — so a fresh
`pip install -r requirements.txt` always runs without extra setup.

Retrain from scratch (in `src/`):

```powershell
python features.py          # results.csv -> training_table.csv + current_state.json
python train.py             # -> models/fifa_model.joblib + metrics.json
python fetch_squads_api.py  # current rosters (needs token; or fetch_squads.py for Wikipedia)
python squad_strength.py    # -> squad_strength.json
```

The GPU ensemble is optional: `python train_ensemble.py` (needs the extra deps
listed in `requirements.txt`). `predict.py` uses it automatically if present and
otherwise falls back to the single model.

## How a prediction is made

### Team strength

Two real-results signals, blended 70 / 30:

| Weight | Signal | Source |
|---|---|---|
| **70%** | International Elo | 48,000+ internationals since 1872 (`data/results.csv`, martj42). K-factor scales with competition importance (World Cup > qualifiers > friendlies) and goal margin. |
| **30%** | Squad club strength | Each player → his club → that club's clubelo.com rating, a proxy for the level he plays at weekly. Caps- and best-XI-weighted per team. |

The squad layer pulls authoritative rosters from the football-data.org API
(`fetch_squads_api.py`), then a live news scan (`detect_withdrawals.py`) drops
players confirmed OUT after registration — no squad API tracks injury
withdrawals, so e.g. Wataru Endo (foot injury) is removed and the next-best
player promoted. clubelo.com is Europe-only, so strong non-European clubs
(Flamengo, Al-Hilal, Club América…) use curated continental-performance estimates.

### Model features (per match)

The trained inputs to the classifier:

| Feature | What it measures |
|---|---|
| **Form** | Points-per-game (last 5), goal difference (last 10), unbeaten streak |
| **Attack / defense** | Opponent-adjusted EWMA of goals scored and conceded — a pi-/Berrar-style rating split (literature shows splits beat plain Elo when fed to gradient-boosted trees) |
| **Head-to-head** | Win rate and goal difference over the last 10 meetings — the 2nd most important feature after Elo in held-out testing |
| **Tournament experience** | Decaying count of WC / continental matches played |
| **Morale** | EWMA momentum of results *vs expectation* — beating a stronger side lifts it more |
| **Stadium & weather** | All 16 venues' altitude, roof and June heat/humidity, used as a *mismatch* vs each team's home climate (Norway suffers in a 34 °C Monterrey kickoff; Mexico doesn't), plus travel distance, rest days and **eastward jet lag** (eastward travel impairs performance more than westward) |
| **Home advantage** | Home / neutral flag and a World Cup flag |

### Live layers (recomputed at request or load time)

Beyond the trained features, several layers refresh from live data:

- **Live fetch on every Predict** (`src/live.py`) — in parallel and uncached: the
  venue's *current* temperature and humidity (Open-Meteo, replacing static June
  averages), fresh Google News headlines + sentiment for both teams, and venue
  headlines. Falls back to climate averages offline; the response flags which
  values were live.
- **Key-player sentiment** (`src/live.py`) — each team's 8 most important players
  (ranked by club Elo × caps; for Brazil this surfaces Casemiro, Alisson,
  Vinícius, Neymar, Raphinha…) get individual news fetches, with injury headlines
  weighted extra-negative. Composite = 40% team news + 60% importance-weighted
  players.
- **Live base-rating updates** (`src/live_ratings.py`) — *what makes the model
  usable mid-tournament.* The frozen pre-tournament `current_state.json` (Elo,
  form, morale, H2H, attack/defence) is updated at load time by folding in every
  finished WC match (cached to `data/wc_matches.json`) using the *exact* math from
  `features.py` (K=60, goal-margin multiplier, identical EWMA coefficients). A
  group-stage thrashing moves Elo, morale and form immediately. Idempotent and
  fail-soft; each prediction reports how many matches were folded in.
- **In-tournament form** (`src/tournament_form.py`) — **the single heaviest win
  factor, but gated.** How a team is doing in the *current* WC (results +
  goals/game from the live feed) dominates: a full form gap shifts win log-odds
  more than sentiment or Elo. Ignored entirely until both teams have played
  **≥ 5 WC matches** (the quarter-finals in the 2026 format), since 1–2 games is
  noise. Possession/assists slot in automatically with a paid stats key.
- **Recent WC form** (`src/recent_stats.py`) — the last two weeks of WC 2026
  matches per team (shown in the Team tab), folded in as a bounded secondary nudge
  (`RSTATS_K`). Built from the live WC scores already on hand
  (`data/wc_matches.json`, free football-data.org feed) as a goal-difference form
  score — no extra key or paid stats feed required.
- **Sentiment-priority layer** (`src/predict.py`) — user-configurable: `high`
  (default) lets a full sentiment split shift win log-odds by more than a 1-SD Elo
  edge (~250 pts), so live sentiment outweighs Elo while Elo still works
  underneath; `normal` makes it secondary; `off` is stats-only. It's a stated
  prior, not a fitted parameter — there's no news archive for 37k past matches to
  train on — and the UI shows before/after probabilities.

The UI adds an **Injuries panel** (every injured key player found in live news,
their importance, and when the injury was first reported) and a **Data status &
refresh** panel (`GET /api/status`, `POST /api/refresh`): it checks every pipeline
artifact and shows fresh 🟢 / stale 🟡 / missing 🔴 with ages, then on one click
runs the refresh chain (fetch squads → rate → detect withdrawals → re-rate → fetch
form) as background subprocesses, streams progress, and hot-reloads data in
memory — no restart.

### Models

`models/fifa_model_ensemble.joblib` is preferred when present; otherwise
`predict.py` falls back to `fifa_model.joblib`.

**Outcome classifier** — a probability-averaged ensemble of five members:

| Member | Tuning | Device |
|---|---|---|
| LightGBM | Optuna | CPU |
| XGBoost | Optuna | GPU |
| CatBoost | Optuna | GPU |
| PyTorch MLP | seed-ensembled | GPU |
| HistGradientBoosting | baseline | CPU |

Plain probability averaging won a deliberate complexity study — LR-stacking and
individual tuned models were also evaluated and gave worse held-out log-loss.
TabPFN-2.5 (tabular foundation model) is wired in but needs a Prior Labs token
(`TABPFN_TOKEN`).

**Scoreline** — two Poisson HistGradientBoosting regressors → expected goals → a
scoreline probability grid.

Retrain: `python train.py` (single), `python train_ensemble.py` (ensemble).

### Player & betting markets

Derived from each match's expected goals (`src/scorers.py`):

| Market | Basis | Real / estimated |
|---|---|---|
| **Anytime goalscorer** | Player international goals/caps → regularised rate (shrinkage keeps small samples honest); team xG shared in proportion, P(score) = 1 − e^(−λ). Penalty takers flagged from history. | Real |
| **Anytime assist** | Heuristic from position + experience + goal involvement — the free dataset has no assist data | Estimated (labelled) |
| **Match markets** | Over/Under 1.5/2.5/3.5, BTTS, clean sheets, win-to-nil, double chance — exact under the independent-Poisson assumption behind the scoreline grid | Real |
| **Parlays** | ~9 same-game combos (scorer doubles, result + Over 2.5, result + BTTS, …); legs multiplied assuming independence | Guide, not a price |

## Performance

Strict time split — train < 2022, test 2022 → Jun 2026 (4,541 test matches):

| Metric | Model | Baseline |
|---|---|---|
| 3-way accuracy | **60.1%** | 59.5% Elo favourite · 47.8% always-home |
| log-loss | **0.871** | — |

Research-driven features (H2H, attack/defense splits, jet lag, streak, tournament
experience) lifted accuracy from 59.6% and log-loss from 0.880.

**Ensemble vs single model** (same split): the 5-member average reached log-loss
0.8713 / 59.9% accuracy vs 0.8720 / 60.1% for the single tuned model — better-
calibrated probabilities, accuracy difference within noise (±0.7pp). The
classifier's edge over raw Elo is mostly in calibration and draw handling
(log-loss), not headline accuracy. ~60% / 0.87 is near the irreducible noise
ceiling for 3-way football; further gains need better *information* (lineups,
injuries, market odds), not more parameters.

## Why no "accuracy boost" was forced in

Before shipping any change, candidate improvements were **measured on the strict
2022→2026 split**: probability calibration (isotonic / temperature — temperature
came out at T≈0.98, i.e. already calibrated), recency sample-weighting, extra
regularization, and derived features (draw-proximity `|elo_diff|`, `elo×is_wc`, …).
Every one left log-loss flat or slightly worse, so none were added — they would
only overfit test noise. Genuine gains require new *information*, not more model;
the highest-value, lowest-overfit-risk next step is a **market-odds feature**
(bookmaker closing prices are the strongest known single predictor).

## Files

```
data/    results.csv (1872–2026 internationals), squads.csv, clubelo_latest.csv,
         training_table.csv, current_state.json, squad_strength.json
src/     features.py (Elo+form+morale+climate), squad_strength.py, train.py,
         predict.py, sentiment.py, geo.py (venues/climate), app.py (Flask)
models/  fifa_model.joblib, metrics.json
web/     index.html (front-end)
```

## Known limitations

- ClubElo covers Europe only; ~23% of players (MLS, Liga MX, Saudi, Asian, African
  leagues) use curated or median club ratings.
- Climate table covers the 48 qualified nations precisely; other countries fall back
  to latitude-based estimates.
- News sentiment is a simple lexicon over headlines — directional, not deep NLP.
- Squad data is a snapshot (June 2026); rerun `fetch_squads_api.py` +
  `squad_strength.py` after injuries/replacements.

## Data sources & attribution

| Data | Source | Terms |
|---|---|---|
| International results, scorers, shootouts | [martj42/international_results](https://github.com/martj42/international_results) | CC0 |
| Club Elo ratings (`clubelo_latest.csv`) | [clubelo.com](http://clubelo.com) | site terms |
| Squads & live results | [football-data.org](https://www.football-data.org) API | API terms |
| Live weather | [Open-Meteo](https://open-meteo.com) | site terms |
| News headlines | Google News RSS | — |

Used under their respective terms for a non-commercial research/demo project;
review each source's terms before any other use.

## License

Code is released under the [MIT License](LICENSE). Third-party datasets retain
their own licenses (see above).
