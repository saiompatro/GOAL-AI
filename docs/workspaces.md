# Competition workspace reference

This guide describes the competition workspaces introduced in the current GOAL AI application: Premier League, La Liga, Champions League, Serie A, Bundesliga, and Ligue 1. It supplements the [README](../README.md) and the [player data audit](player-data-audit.md).

## Architecture

\`src/app.py\` registers the \`workspace\` Flask blueprint from \`src/projects/workspace_api.py\`. The blueprint serves the shared workspace UI and exposes data and model routes. \`src/projects/competitions.py\` is the single competition registry; every workspace maps to a separate data prefix, model cache entry, and artifact set.

\`\`\`text
browser workspace
    -> /api/workspaces/<competition>/...
    -> registry + prepared data under data/analytics/
    -> validated artifact under models/workspaces/ or local rebuild
    -> JSON, CSV, or PNG response
\`\`\`

The original World Cup page remains at \`/world-cup\`. The root path is now the competition hub. Older \`/api/pl/*\` routes are retained as Premier League compatibility endpoints and delegate to the observed-data workspace models.

## Routes

### Browser routes

| Route | Purpose |
| --- | --- |
| \`/\` | Competition hub |
| \`/world-cup\` | Existing World Cup interface |
| \`/competitions/<slug>\` | Workspace overview |
| \`/competitions/<slug>/overview\` | Overview |
| \`/competitions/<slug>/matches\` | Match predictor |
| \`/competitions/<slug>/transfers\` | Transfer-value predictor |
| \`/competitions/<slug>/scouting\` | Player scouting |

### Workspace API

| Route | Method | Purpose |
| --- | --- | --- |
| \`/api/workspaces\` | GET | Competition registry and display metadata |
| \`/api/workspaces/<slug>\` | GET | Overview data, current installed player snapshots, six-game form summary, teams, source metadata, and optional future fixtures |
| \`/api/workspaces/<slug>/transfer?player=<name>\` | GET | Held-out estimate for a listed player |
| \`/api/workspaces/<slug>/transfer\` | POST | Custom profile estimate; send numeric model fields and \`position\` |
| \`/api/workspaces/<slug>/scouting?player=<name>&k=8&position=MF\` | GET | Similar players, clusters, per-90 values, and an export URL |
| \`/api/workspaces/<slug>/scouting.csv?...\` | GET | CSV matching the filtered scouting result |
| \`/api/workspaces/<slug>/match\` | POST | Match probabilities; send \`home\`, \`away\`, and optional boolean \`neutral\` |
| \`/api/workspaces/<slug>/plot/<kind>.png\` | GET | \`match\`, \`transfer\`, or \`scouting\` chart |

Unknown competitions and invalid input return a JSON error with HTTP 400. Unknown browser pages return HTTP 404.

## Dataset contract

Each competition has three independent datasets in \`data/analytics/\`:

| Suffix | Contents | Metadata |
| --- | --- | --- |
| \`_matches.csv\` | Completed match history | \`_matches.json\` |
| \`_players.csv\` | Observed player-season statistics with dated valuation target | \`_players.json\` |
| \`_scouting.csv\` | Observed scouting profile snapshot | \`_scouting.json\` |

The companion JSON records source, source URL, scope, seasons, features, retrieval time, and applicable caveats. The application fails clearly if the observed player or scouting CSV and metadata are missing; it never fabricates a player fallback.

### Valuation inputs

Prepared valuation datasets have a stable player identifier plus \`player\`, \`team\`, \`season\`, \`position\`, \`age\`, \`minutes\`, \`goals\`, \`assists\`, \`feature_cutoff\`, \`valuation_date\`, and \`market_value_eur_m\`. The valuation date must follow the feature cutoff and be at most 90 days later. A value is a market valuation estimate—not a transfer fee.

### Scouting inputs

Scouting uses the latest installed season and only outfield players with at least 270 minutes. Domestic leagues use goals, assists, shots, key passes, dribbles, tackles, and interceptions per 90. UCL exposes only goals and assists per 90; consumers should treat its results as basic attacking comparison rather than a full cross-position scouting model.

## Model behaviour

### Transfer values

The transfer model is a linear regression over standardised numeric features and one-hot position. It chronologically holds out the most recent complete season. Named players are estimated by that holdout model, avoiding use of the displayed reference valuation as a training target. For what-if submissions, the all-data refit is used. Results include MAE and the training-median baseline, so model performance has context.

### Match outcomes

The match model is a random forest classifier. Features are constructed in match-date order and use only prior results: rolling form, goal difference, goals scored/conceded, home/neutral context, and observed shots (plus possession only when the imported source contains it). The newest season is held out for evaluation; the serving model is then refit on recorded history. No missing feature is inferred from a scoreline.

UCL extra-time and penalty outcomes are converted to regulation-time targets. Finals are labelled neutral. The returned metrics include accuracy, log loss, home-win baseline, a confusion matrix, and train/test time boundaries.

### Scouting

Profiles are converted to per-90 rates, standardised, grouped using K-means, and queried with nearest neighbours. \`k\` changes only how many of the same ordered matches are returned. Position filtering is applied to results and is also preserved by the CSV export.

## Artifact safety and rebuilds

\`src/projects/model_store.py\` persists a valuation, match, and scouting artifact for every competition. Its signature covers relevant CSV/JSON input timestamps, the workspace implementation, and dependency versions. When the signature does not match, the artifact is rejected and the model is rebuilt from prepared files. This keeps an old artifact from silently serving after a data refresh or implementation change.

Run the following after an audited player-data rebuild, or whenever you want to materialise new artifacts rather than waiting for first use:

\`\`\`powershell
python src/projects/train_workspaces.py
\`\`\`

The resulting \`models/workspaces/training_report.json\` is the canonical summary of current training metrics and source coverage.

## Operations

Refresh completed matches for all competitions or a selected subset:

\`\`\`powershell
python src/projects/refresh_data.py all
python src/projects/refresh_data.py premier-league --years 2023 2024 2025
\`\`\`

Use a football-data.org token only for optional fixtures and roster/scorer snapshots. These commands do not create player statistics or market values:

\`\`\`powershell
python src/projects/refresh_data.py serie-a --fixtures
python src/projects/fetch_players.py serie-a --years 2023 2024
\`\`\`

To replace one valuation dataset, use the validated player importer and state the source. Imports require complete core columns, nonnegative finite values, unique player-seasons, two or more seasons, and sufficient train/holdout and scouting-eligible rows.

\`\`\`powershell
python src/projects/refresh_data.py bundesliga --players path/to/observed.csv --source "Provider and date"
\`\`\`

## Verification

Run the workspace tests from the repository root:

\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

They cover deep links, isolation between competitions, chronological feature generation, data provenance, import validation, exports, chart generation, UCL score handling, stale artifact rejection, and compatibility endpoints.

