# World Cup 2026 Match Predictor

Predicts FIFA World Cup match outcomes (win/draw/loss probabilities + most likely
scorelines) from **real football results only** — no video-game data or ratings.

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

**Team strength** blends two real-results signals:

1. **International Elo (70%)** — computed over 48,000+ international matches since
   1872 (`data/results.csv`, the open martj42 dataset). K-factor scales with
   competition importance (World Cup > qualifiers > friendlies) and goal margin.
2. **Squad club strength (30%)** — the player layer. Squads come from the
   football-data.org API (`fetch_squads_api.py`, authoritative current rosters),
   then a live news scan (`detect_withdrawals.py`) removes players confirmed OUT
   of the tournament after registration — no squad API tracks injury
   withdrawals, so e.g. Wataru Endo (foot injury, retired mid-tournament) is
   dropped and the next-best player promoted. Each player is mapped to his club, and
   each club's Elo from clubelo.com (built from Premier League, Bundesliga, La Liga,
   UCL and every other European competition's actual results) proxies the level the
   player performs at weekly. Caps-weighted, best-XI-weighted mean per team; strong
   non-European clubs (Flamengo, Al-Hilal, Club América…) use curated continental-
   performance estimates.

**Context features** per match:

- **Form**: points-per-game (last 5), goal difference (last 10), unbeaten streak
- **Attack/defense ratings**: opponent-strength-adjusted EWMA of goals scored and
  conceded (pi-/Berrar-rating style split — literature shows rating splits beat
  plain Elo when fed to gradient-boosted trees)
- **Head-to-head**: win rate and goal difference over the sides' last 10 meetings
  (2nd most important feature after Elo in held-out testing)
- **Major-tournament experience**: decaying count of WC/continental matches played
- **Morale**: exponentially-weighted momentum of results *vs expectation* (beating a
  stronger side lifts morale more), plus **live news sentiment** pulled from
  Google News headlines and scored with a football lexicon (`src/sentiment.py`)
- **Key-player sentiment** (`src/live.py`): each team's 8 most important players
  (ranked by club Elo x international caps — for Brazil this surfaces Casemiro,
  Alisson, Vinícius, Neymar, Raphinha...) get individual live news fetches on
  every prediction. Injury-related headlines are detected and weigh in extra
  negatively. Composite = 40% general team news + 60% importance-weighted players.
- **Injuries panel** (UI, below Key players): every injured key player found in live
  news, with how central they are to the team (importance label + weight) and when
  the injury was first reported (from the news publication date).
- **Data status & refresh** (UI, "⚙ Data status & refresh" button): checks every
  pipeline artifact (model, squads, withdrawals, squad ratings, in-tournament form)
  and shows fresh 🟢 / stale 🟡 / missing 🔴 with ages. One click runs the
  tournament refresh (fetch squads → rate → detect withdrawals → re-rate → fetch
  form) as background subprocesses, streams step progress, then hot-reloads the
  data in memory so predictions use it immediately — no server restart.
  Endpoints: `GET /api/status`, `POST /api/refresh`.
- **Sentiment-priority layer** (`src/predict.py`): user-configurable. In "high"
  mode (default) a full sentiment split shifts win log-odds by more than a
  1-standard-deviation Elo edge (~250 pts), so live sentiment outweighs Elo while
  Elo still works underneath; "normal" makes it secondary; "off" is stats-only.
  This layer is a stated prior, not a fitted parameter — no historical news
  archive exists for 37k past matches, so it cannot be trained; the UI shows
  before/after probabilities for transparency.
- **In-tournament form** (`src/tournament_form.py`) — **the single heaviest
  win-prediction factor, but only once it is meaningful.** How a team is actually
  doing in the *current* World Cup (results + goals per game, from the live
  football-data.org match feed) dominates the prediction: a full form gap shifts
  win log-odds more than sentiment or Elo. Per design it is **ignored entirely
  until both teams have played ≥ 5 World Cup matches** (i.e. from the
  quarter-finals in the 2026 format), since a 1–2 game sample is noise. Possession
  and assists need a paid stats API (the free tier is scores only) and slot in
  automatically if a key is configured. Refresh during the tournament with
  `python tournament_form.py` (the football-data.org token is read from the
  gitignored `.env`; or pass it as an argument).
- **Recent World Cup form** (`src/recent_stats.py`) — the last two weeks of WC 2026
  matches, per team and per player, shown in the Team/Player tabs and folded into the
  model as a bounded secondary nudge (`RSTATS_K`). With an optional
  [API-Football](https://www.api-football.com/) key in `.env` (`API_FOOTBALL_KEY`)
  it carries real **shots, shots on target, possession and xG**; without a key it
  falls back to the live scores already on hand (goal-difference form), and the
  shot/possession/xG tiles read as “—”. Rebuilt on the data-refresh.
- **Live base-rating updates** (`src/live_ratings.py`) — **the part that makes the
  model usable mid-tournament.** The offline `current_state.json` (Elo, form,
  morale, head-to-head, attack/defence) is frozen at the pre-tournament build.
  Every finished World Cup match (same football-data.org feed, cached to
  `data/wc_matches.json`) is folded into those ratings at load time using the
  *exact* update math from `features.py` (K=60, goal-margin multiplier, identical
  EWMA coefficients). So a group-stage thrashing immediately moves a team's Elo,
  morale and form — unlike the tournament-form layer above, which stays gated to
  the quarter-finals. Idempotent (re-applying results never double-counts) and
  fail-soft (no results yet → plain pre-tournament ratings). Each prediction
  reports how many matches were folded in (`live_ratings` in the response).
- **Live data on every prediction** (`src/live.py`): each Predict click fetches,
  in parallel and uncached — (1) the venue's *current* temperature and relative
  humidity from Open-Meteo, (2) fresh Google News headlines + sentiment for both
  teams, (3) headlines about the venue. Live weather replaces the static June
  averages (manual overrides still win); falls back to climate averages offline,
  and the response flags which values were live.
- **Stadium & weather**: all 16 real 2026 venues with altitude, roof, June heat and
  humidity. The model uses *mismatch* features — how much hotter/more humid/higher
  the venue is than what each team's home country is used to (e.g. Norway suffers at
  a 34 °C Monterrey afternoon kickoff; Mexico doesn't), plus travel distance, rest
  days, and **eastward jet lag** (timezones crossed eastward — sports-science studies
  find eastward travel impairs performance more than westward)
- **Home advantage / neutrality** and World Cup flag

**Models** (`models/fifa_model_ensemble.joblib`, preferred when present; falls
back to `fifa_model.joblib`):
- Production classifier: probability-averaged ensemble of five members —
  Optuna-tuned LightGBM, XGBoost (GPU), CatBoost (GPU), a seed-ensembled
  PyTorch MLP (GPU), and the original HistGradientBoosting model.
  Outcome of a deliberate complexity study: LR-stacking and individual tuned
  models were also evaluated; simple probability averaging gave the best
  held-out log-loss. TabPFN-2.5 (tabular foundation model) is wired in but
  requires a Prior Labs license token (`TABPFN_TOKEN`) to activate.
- Two Poisson HistGradientBoosting regressors → expected goals → scoreline grid
- Retrain: `python train.py` (single model), `python train_ensemble.py` (ensemble)

**Player & betting markets** (`src/scorers.py`): from each match's expected goals
the engine derives, for the prediction response and UI:
- **Anytime goalscorer** — real data: each squad player's international goals
  (`data/goalscorers.csv`) over his caps give a regularised goals/game rate
  (shrinkage keeps small samples honest); the team's expected goals are shared out
  in proportion, so P(score) = 1 − e^(−player_λ). Penalty takers are flagged from
  who historically took penalties.
- **Anytime assist** — *estimated*, clearly labelled: the free dataset has **no
  assist data**, so this is a heuristic from position + experience + goal
  involvement, not a measured rate.
- **Derived match markets** — Over/Under 1.5/2.5/3.5, both-teams-to-score, clean
  sheets, win-to-nil, double chance — all exact under the model's independent-
  Poisson goals assumption (same one behind the scoreline grid).
- **Parlays** — ~9 same-game combinations (scorer doubles, result + Over 2.5,
  result + BTTS, Over 2.5 + BTTS, double chance + Over 1.5, win-to-nil, star
  scorer + Over 2.5, …). Legs are multiplied assuming independence; real SGPs are
  correlated, so they're a guide, not a price.

## Honest evaluation (strict time split, train <2022, test 2022→Jun 2026)

| metric | value |
|---|---|
| 3-way accuracy (4,541 matches) | **60.1%** |
| log-loss | **0.871** |
| always-pick-home baseline | 47.8% |
| pick-Elo-favourite baseline | 59.5% |

(Adding the research-driven features — H2H, attack/defense splits, jet lag, streak,
tournament experience — improved accuracy from 59.6% and log-loss from 0.880.)

Ensemble study (same split): the 5-member average reached **log-loss 0.8713 /
59.9% accuracy** vs 0.8720 / 60.1% for the single tuned model — better
calibrated probabilities, accuracy difference within noise (±0.7pp). All
differences are small because ~60% / 0.87 is near the irreducible noise ceiling
for 3-way football outcomes; further gains require better *information*
(lineups, injuries, market data), not more parameters.

The classifier's edge over raw Elo is mostly in calibrated probabilities and draw
handling (log-loss), not headline accuracy — typical for football, where ~60% is
near the practical ceiling for 3-way prediction.

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

## Why no "accuracy boost" was forced in

The headline ~60% / 0.871 log-loss is near the irreducible noise floor for 3-way
football outcomes. Before shipping any change, candidate improvements were
**measured on the strict 2022→2026 time split**: probability calibration
(isotonic / temperature — temperature came out at T≈0.98, i.e. the model is
already calibrated), recency sample-weighting, extra regularization, and several
derived features (draw-proximity `|elo_diff|`, `elo×is_wc`, …). Every one left
log-loss flat or slightly worse, so none were added — adding them would only
overfit test noise. Genuine gains require new *information*, not more model:
the highest-value, lowest-overfit-risk next step is a **market-odds feature**
(bookmaker closing prices are the strongest known single predictor).

## Data sources & attribution

- **International results** (`data/results.csv`, `goalscorers.csv`, `shootouts.csv`):
  [martj42/international_results](https://github.com/martj42/international_results) (CC0).
- **Club Elo ratings** (`data/clubelo_latest.csv`): [clubelo.com](http://clubelo.com).
- **Squads & live results**: [football-data.org](https://www.football-data.org) API.
- **Live weather**: [Open-Meteo](https://open-meteo.com).
- **News headlines**: Google News RSS.

These are used under their respective terms for a non-commercial research/demo
project; please review each source's terms before any other use.

## License

Code is released under the [MIT License](LICENSE). Third-party datasets retain
their own licenses (see above).
