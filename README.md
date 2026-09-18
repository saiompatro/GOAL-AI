# GOAL AI

Football intelligence for the **Premier League, La Liga, UEFA Champions League,
Serie A, Bundesliga, Ligue 1, and 2026 FIFA World Cup**. The app opens to a
competition hub with distinct workspaces, persistent navigation, competition
colours, and responsive desktop/mobile layouts.

## What you can do

| Competition | Where in the UI | Projects |
|---|---|---|
| **FIFA World Cup 2026** | `/world-cup` | Existing match, team, and player analysis |
| **Premier League, La Liga, Champions League, Serie A, Bundesliga, Ligue 1** | `/competitions/<competition>/overview` | Dedicated Overview, Match Predictor, Transfer Values, and Player Scouting pages |

Every competition workspace contains three focused learning projects:

1. **Transfer value predictor** — linear regression from goals, assists,
   minutes, age, position, and related player statistics.
2. **Match outcome predictor** — random forest classification from recent
   form, goals for/against, home advantage and observed shots. Possession is
   included only if an imported match dataset supplies it.
3. **Player scouting system** — nearest-neighbour similarity and K-means style
   clusters, with searchable results in the main UI and a standalone Streamlit
   dashboard, per-90 profile comparison, position filters, CSV exports, and
   downloadable matplotlib charts.

### Competition workspaces

Use slugs `premier-league`, `la-liga`, `champions-league`, `serie-a`,
`bundesliga`, and `ligue-1`. Every workspace supports these deep links:

```text
/competitions/premier-league/overview
/competitions/premier-league/matches
/competitions/premier-league/transfers
/competitions/premier-league/scouting
```

The new workspace engine is in `src/projects/analytics.py`, the competition
registry in `competitions.py`, and the API in `workspace_api.py`. Each
competition has separate models and cached results. Updating an imported CSV
invalidates its model cache. The old World Cup interface and `/api/pl/*`
tutorial endpoints are retained for compatibility; the new pages use
`/api/workspaces/*`.

**Observed player data is installed.** The valuation model uses 14,695 player-season
records from Transfermarkt-derived appearances and dated market valuations, with
four or five complete seasons per competition. Premier League, La Liga, Serie A
and Bundesliga run through 2025–26; UCL and Ligue 1 run through 2024–25 because
the downloaded 2025–26 appearance tables omit matches. Targets are the first
recorded valuation strictly after the final match, within 90 days. Rows without
such a target are excluded and counted in the provenance JSON. Market valuations
are estimates, not completed transfer fees. Historical positions come from the
source player profiles, not reconstructed season-by-season roles.

Scouting has its own dataset, independent of valuation coverage. The five domestic
leagues use observed 2024–25 FBref-derived goals, assists, shots, key passes,
successful take-ons, tackles and interceptions. UCL uses observed 2024–25 goals
and assists per 90 only, explicitly labelled a basic attacking comparison.
Multiple-club rows are combined within a competition; the club with most minutes
is shown. Directories show the most recent installed season, not current squads.
There is no generated-player fallback in the competition workspaces.

Source links, dates, excluded rows and feature coverage are in
`data/analytics/*_players.json` and `*_scouting.json`. The complete research audit
is in [docs/player-data-audit.md](docs/player-data-audit.md), with pinned input
URLs and checksums in [docs/player-source-manifest.json](docs/player-source-manifest.json).

Rebuild from the audited downloads and retrain all 18 models:

```powershell
python src/projects/prepare_player_data.py --download
python src/projects/train_workspaces.py
```

Prepared CSVs and trained artifacts under `models/workspaces/` are committed, so
running the app needs no provider key or download. Artifacts are checked against
input data, implementation and dependency versions before loading. If they are
stale or incompatible, the app trains from the bundled observed CSVs instead.
`models/workspaces/training_report.json` records the held-out metrics, baseline
errors, source coverage and scouting features for each competition. Raw research
archives are ignored by Git; the build command verifies their pinned checksums
and refuses changed upstream snapshots until they are audited.

The bundled match workspaces cover 2021–22 through 2025–26 (source timestamps
and URLs are in `data/analytics/*_matches.json`). Domestic results and shots
come from [football-data.co.uk](https://www.football-data.co.uk/data.php);
753 Champions League matches come from
[OpenFootball](https://github.com/openfootball/champions-league). UCL targets
use regulation-time results, not penalty winners or extra-time scores. Finals
are marked neutral. Source data licensing/terms apply when redistributing it.

The match model holds out the newest season, trains strictly on earlier
seasons, and shows accuracy, home-win baseline, log loss, a confusion matrix,
and an audit of held-out predictions. The serving model is then refitted on
all recorded matches. Its latest-form features include the last recorded game.
Shot/possession fields are omitted when absent, never reconstructed from goals.
Transfer regression evaluates on the latest complete season. Named-player
comparisons use that held-out model, so the displayed reference target was not
used to train its estimate. Custom profiles use the model refitted on all
observations. The UI displays both model MAE and a training-median baseline.

Refresh the public match snapshots with `requests` and `pandas`:

```powershell
python src/projects/refresh_data.py all
# Or choose one competition and seasons by their starting year:
python src/projects/refresh_data.py champions-league --years 2023 2024 2025
```

Import a player-season table (use one row per player per season, position
`GK`/`DF`/`MF`/`FW`, season `YYYY-YY`, and values in EUR millions):

```text
player,team,season,position,age,minutes,goals,assists,market_value_eur_m
```

```powershell
python src/projects/refresh_data.py la-liga --players path/to/observed_players.csv --source "Provider / dataset name and date"
```

You can also download observed rosters and scorers using `requests` and
football-data.org, subject to your token's historical-season access:

```powershell
python src/projects/fetch_players.py premier-league --years 2022 2023 2024
python src/projects/fetch_players.py la-liga --years 2022 2023 2024
python src/projects/fetch_players.py champions-league --years 2022 2023 2024
```

These raw provider snapshots are saved in `data/analytics/provider_snapshots`.
They do not overwrite the player training table or invent missing minutes,
scouting statistics, or values. Join them with a complete observed source
before using the validated player import above.

Imports must include at least two seasons, 30 rows, eight outfield players
with 270+ minutes, 20 training rows, and five final-season holdout rows.
Missing, duplicate, nonfinite, and negative observations are rejected before
replacing existing data. Imports work identically for all six competitions.
Imports update valuation data and attribution; they do not replace the independent scouting table.

Upcoming fixtures are optional and never fabricated. Set `FOOTBALL_DATA_TOKEN`
in `.env`, then refresh them through the
[football-data.org v4 API](https://docs.football-data.org/general/v4/competition.html):

```powershell
python src/projects/refresh_data.py premier-league --fixtures
```

The match page displays the fetched fixture list and refresh date. Its
hypothetical match-up controls use provider-specific historical team names;
select the equivalent teams to analyse an upcoming fixture. Predictions use
the latest *loaded* history, not live form. Past fixtures are hidden.

Run the standalone multi-competition Streamlit dashboard:

```powershell
pip install -r requirements-scouting.txt
streamlit run src/projects/streamlit_scouting.py
```

Verify competition isolation, chronological features, 90-minute UCL parsing,
import validation, model outputs and chart downloads:

```powershell
python -m unittest discover -s tests -v
```

The World Cup engine returns win/draw/loss probabilities and a full scoreline
grid, plus derived goalscorer, match, and parlay markets from a feature set built
on more than 150 years of international results. Each club league runs a
separate domestic pipeline trained on more than 30 seasons of that league's
own results. See [Club leagues](#club-leagues) and [Premier League
projects](#premier-league-projects) for implementation and data details.

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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\app.py
```

Open **http://127.0.0.1:5000** for the competition hub. The six competition
workspaces train their lightweight models on first use from bundled datasets.
The original World Cup tools remain at **http://127.0.0.1:5000/world-cup**.

Stop the server with `Ctrl+C` in that terminal (or `Stop-Process -Name python`).
The port defaults to 5000; override it with:

```powershell
$env:PORT=8080
python src\app.py
```

The committed `models/fifa_model.joblib` (sklearn-only, ~1 MB) means it runs out
of the box — no training step needed. Live squad refresh and in-tournament form
need a free [football-data.org](https://www.football-data.org/client/register)
token. Copy `.env.example` to `.env` and set `FOOTBALL_DATA_TOKEN`; never commit
the populated `.env` file.

The player-scouting dashboard can also run independently:

```powershell
streamlit run src\projects\streamlit_scouting.py
```

The GPU ensemble (`models/fifa_model_ensemble.joblib`) is used automatically when
its deps (torch, catboost, xgboost, lightgbm) are installed; if they're missing or
fail to load, `predict.py` falls back to the plain model — so a fresh
`pip install -r requirements.txt` always runs without extra setup.

Retrain the World Cup baseline from the repository root:

```powershell
python src\features.py          # results.csv -> training_table.csv + current_state.json
python src\train.py             # -> models/fifa_model.joblib + metrics.json
python src\fetch_squads_api.py  # current rosters; requires the optional token
python src\squad_strength.py    # -> squad_strength.json
```

The GPU ensemble is optional: `python src\train_ensemble.py` (needs the extra deps
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
         club/     <league>_results.csv, ..._state.json per league (premier_league,
                   la_liga, serie_a, bundesliga, ligue_1 — see fetch_club_results.LEAGUES)
         players/  premier_league_players.csv (transfer-value / scouting projects)
src/     features.py (Elo+form+morale+climate), squad_strength.py, train.py,
         predict.py, sentiment.py, geo.py (venues/climate), app.py (Flask),
         fetch_club_results.py (LEAGUES registry + fetch + fit_home_advantage),
         club_features.py, train_league.py, predict_league.py (club-league models)
         projects/ transfer_value.py, match_outcome.py, player_scouting.py,
                   fetch_players.py, gen_player_data.py, streamlit_scouting.py
models/  fifa_model.joblib, metrics.json, <league>_model.joblib per league
         projects/ (transfer/outcome/scouting models, cached lazily; gitignored)
web/     index.html (front-end — Match / Team / Player / Leagues→Projects tabs)
```

## Club leagues

The competing prediction sites and repos that inspired this feature (SPI/FiveThirtyEight-
style club Elo trackers, football-data.co.uk-based Kaggle notebooks, various
odds-comparison tools) almost all cover club leagues — the World Cup happens
once every four years, but domestic league fixtures happen every week. This
was the biggest gap between this project (originally 100% international,
WC-2026-only) and the field, so it's the first thing that got closed.

**Five leagues** are live under the **Leagues** tab — the "big five" European
domestic competitions, which together also supply the bulk of UEFA Champions
League and Europa League squads: **Premier League** (England), **La Liga**
(Spain), **Serie A** (Italy), **Bundesliga** (Germany) and **Ligue 1**
(France). Independent pipeline from the World Cup model — separate data,
features and trained model per league — using the same walk-forward,
no-leakage philosophy as the international engine:

| Signal | Source |
|---|---|
| **Elo** | K=20, goal-margin multiplier, per-league home-advantage bonus (see below), computed match-by-match over 30+ seasons |
| **Form** | Points-per-game (last 5), goal difference (last 10) |
| **Attack/defense** | Opponent-adjusted EWMA of goals scored/conceded, same split as the WC model |
| **Morale** | EWMA of result vs Elo expectation |
| **Head-to-head** | Win rate and goal diff over the last 10 meetings |

The Elo home-advantage bonus is **fit per league**, not a single constant
copy-pasted onto every competition: `fetch_club_results.fit_home_advantage()`
converts each league's actual historical home-win rate into an equivalent
Elo rating bonus (400·log₁₀(s/(1−s)) where `s` is the average home result).
On the 1993-94→2023-24 results:

| League | Home-advantage (Elo pts) |
|---|---|
| Premier League | 70 *(kept at its original tuned value — see below)* |
| Ligue 1 | 73 |
| La Liga | 72 |
| Serie A | 67 |
| Bundesliga | 64 |

Premier League keeps its original eyeballed 70 rather than the ~61 the fit
implies for it, since that value is already baked into its shipped, documented
model — retuning it is bundled with a future Premier League retrain rather
than changed as a side effect of adding other leagues.

Outcome classifier + twin Poisson goal regressors (`src/train_league.py`),
same architecture as `train.py`, one model per league. On each league's own
strict 2-season holdout (2022-23 + 2023-24):

| League | Accuracy | Log-loss | Elo-favourite baseline |
|---|---|---|---|
| Premier League | 54.9% | 0.955 | 55.3% |
| La Liga | 52.9% | 0.986 | 54.5% |
| Serie A | 52.5% | 0.992 | 52.4% |
| Bundesliga | 51.3% | 1.009 | 50.5% |
| Ligue 1 | 49.6% | 1.031 | 51.7% |

Club football is far more competitively balanced than international football
(fewer lopsided squad gaps, deeper benches), so these sit close to the
accuracy ceiling reported in prediction-market literature for domestic
leagues — there's less signal to extract than a WC where a top-10 nation can
play a part-timer squad.

Data: `src/fetch_club_results.py` pulls season-by-season results (1993-94
onward) from the [footballcsv/cache.footballdata](https://github.com/footballcsv/cache.footballdata)
GitHub mirror of football-data.co.uk. `src/club_features.py` builds the
training table; `src/predict_league.py` serves predictions via
`GET /api/leagues`, `GET /api/league_team`, `POST /api/predict_league`. The
**Leagues** tab UI and the data-status/refresh panel are both driven entirely
by `fetch_club_results.LEAGUES`, so they pick up every league automatically —
no front-end changes needed to add one.

Adding another league is one new entry in `LEAGUES` (`src/fetch_club_results.py`,
with `home_adv` from `fit_home_advantage()` on that league's own results)
plus a re-run of `fetch_club_results.py` → `club_features.py` → `train_league.py` —
no other code changes.

## Legacy Premier League tutorials

The competition workspaces supersede the original standalone tutorial modules.
The World Cup interface now sends its player-project buttons to the observed-data
workspaces for the selected league. Legacy `/api/pl/*` player routes also use the
observed engine; prediction routes redirect to the corresponding workspace API
and return its response schema. Original standalone tutorial modules and their
sample CSV remain available as offline examples, but the app does not use their
generated player models or reconstructed match-statistic proxies.

The original domestic Elo pipeline still uses its older 2023–24 snapshots;
the new random-forest workspaces have separate 2025–26 snapshots. The standalone
Streamlit scouting dashboard uses the same observed engine as the web app.

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
