# GOAL AI

GOAL AI is a local football-intelligence application for the 2026 FIFA World Cup and six European competition workspaces: Premier League, La Liga, UEFA Champions League, Serie A, Bundesliga, and Ligue 1.

Each competition workspace combines observed historical data with three separate tools: match-outcome prediction, player market-value estimation, and player-style scouting. The World Cup experience remains available separately at \`/world-cup\`.

> **Scope.** GOAL AI is an analysis and research tool. Model output is not a guarantee of a match result, player value, or transfer fee.

## Start here

The committed data snapshots and workspace artifacts let the application run without an API key or a data download.

\`\`\`powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python src\\app.py
\`\`\`

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The home page is the competition hub; [http://127.0.0.1:5000/world-cup](http://127.0.0.1:5000/world-cup) opens the World Cup interface. Set \`PORT\` before starting the application to use another local port.

\`\`\`powershell
$env:PORT=8080
python src\\app.py
\`\`\`

## Competition workspaces

Every workspace has an Overview, Match Predictor, Transfer Values, and Player Scouting page. Replace the slug in the paths below to open any competition.

\`\`\`text
/competitions/premier-league/overview
/competitions/premier-league/matches
/competitions/premier-league/transfers
/competitions/premier-league/scouting
\`\`\`

| Slug | Competition | Region |
| --- | --- | --- |
| \`premier-league\` | Premier League | England |
| \`la-liga\` | La Liga | Spain |
| \`champions-league\` | Champions League | Europe |
| \`serie-a\` | Serie A | Italy |
| \`bundesliga\` | Bundesliga | Germany |
| \`ligue-1\` | Ligue 1 | France |

### What each tool does

| Tool | Method | Data and output |
| --- | --- | --- |
| Match Predictor | Random forest classifier | Pre-match rolling form, goals for/against, home/neutral venue, and observed shots where supplied. Returns home/draw/away probabilities and held-out metrics. |
| Transfer Values | Linear regression | Age, minutes, goals, assists, and position. Returns a market-value estimate, reference value when available, comparable history, and held-out error. |
| Player Scouting | Standardised per-90 profiles, nearest neighbours, and K-means clusters | Finds similar outfield players and style groups. Domestic leagues use seven observed performance measures; UCL is an explicitly basic goals-and-assists comparison. |

The downloadable charts and scouting CSV are generated from the same filtered results shown in the interface. See [workspace reference](docs/workspaces.md) for API routes, validation behaviour, and model lifecycle details.

## Data and limitations

The application deliberately keeps the three workspace datasets independent:

- **Matches:** five recent seasons (2021-22 through 2025-26) from [football-data.co.uk](https://www.football-data.co.uk/data.php) for domestic leagues and [OpenFootball](https://github.com/openfootball/champions-league) for UCL. UCL targets are regulation-time scores; finals are neutral.
- **Valuations:** 14,695 observed player-season records from [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets). The target is the first recorded market valuation one to 90 days after the season's final match. A market valuation is an estimate, not a completed transfer fee.
- **Scouting:** observed 2024-25 FBref-derived Big Five snapshots for domestic leagues. The seven domestic per-90 features are goals, assists, shots, key passes, successful take-ons, tackles, and interceptions. UCL has only goals and assists per 90 and is labelled accordingly.

The newest complete valuation season is 2025-26 for Premier League, La Liga, Serie A, and Bundesliga. UCL and Ligue 1 valuation data end at 2024-25 because the available 2025-26 appearance coverage was incomplete. Workspace player directories show the most recent installed historical season, not a live squad.

All prepared data carry source, season, and feature metadata in \`data/analytics/*_{players,scouting,matches}.json\`. The detailed audit, pinned input URLs, checksums, schemas, and provenance rules are in [docs/player-data-audit.md](docs/player-data-audit.md) and [docs/player-source-manifest.json](docs/player-source-manifest.json).

## Evaluation and model lifecycle

Workspace evaluations are chronological. Transfer models hold out the most recent complete season; match models hold out the newest match season and train only on preceding results. Player-specific transfer estimates use the held-out model, so the displayed reference target was not used to estimate that player. Custom transfer scenarios use a model refitted on all observations.

Pre-trained workspace artifacts are stored in \`models/workspaces/\`. Before an artifact is loaded, its input-data signature, relevant implementation files, and dependency versions are checked. An outdated or incompatible artifact is ignored and rebuilt from the bundled observed CSVs. The current metrics, baselines, provenance, and feature coverage are recorded in \`models/workspaces/training_report.json\`.

## Refresh and rebuild

### Recreate the audited player datasets and workspace models

Raw research inputs are intentionally not committed. After obtaining the audited downloads, rebuild the prepared observed snapshots and all workspace artifacts from the repository root:

\`\`\`powershell
python src/projects/prepare_player_data.py --download
python src/projects/train_workspaces.py
\`\`\`

The preparation command verifies pinned checksums and refuses unexpected upstream snapshots. Do not replace a source file or silently change a checksum without updating the audit and manifest.

### Refresh match history

\`\`\`powershell
python src/projects/refresh_data.py all
python src/projects/refresh_data.py champions-league --years 2023 2024 2025
\`\`\`

Refreshing match data changes the corresponding input signature, so the next workspace request retrains that match model (or rerun \`train_workspaces.py\` to write an updated artifact immediately).

### Import a valuation table

Imports replace only one competition's valuation dataset; they never generate statistics or replace its independent scouting dataset. Provide attribution and at least two seasons of valid observed rows.

\`\`\`text
player,team,season,position,age,minutes,goals,assists,market_value_eur_m
\`\`\`

\`\`\`powershell
python src/projects/refresh_data.py la-liga --players path/to/players.csv --source "Provider and retrieval date"
\`\`\`

The importer rejects missing, duplicate, non-finite, negative, or undersized datasets. It requires at least 30 player-seasons, eight players, two seasons, 20 training rows, five final-season holdout rows, and eight eligible outfield profiles in the most recent season.

### Optional fixtures and roster snapshots

An optional \`FOOTBALL_DATA_TOKEN\` enables fixture refreshes and roster/scorer downloads from football-data.org. Copy \`.env.example\` to \`.env\`, add the token, and keep \`.env\` uncommitted.

\`\`\`powershell
python src/projects/refresh_data.py premier-league --fixtures
python src/projects/fetch_players.py premier-league --years 2022 2023 2024
\`\`\`

Fixtures are displayed only when fetched; they are never fabricated. Provider roster snapshots are saved separately and do not overwrite validated valuation or scouting inputs.

## World Cup experience

The World Cup portion has its own model and data pipeline. It combines international Elo, squad club-strength ratings, recent form, tournament experience, venue and climate effects, and optional live information. The committed \`models/fifa_model.joblib\` runs with the core requirements.

\`\`\`powershell
python src\\features.py
python src\\train.py
\`\`\`

Live squad refresh, withdrawals, and in-tournament form require the optional football-data.org token. The GPU ensemble is optional; install its documented dependencies before running \`python src\\train_ensemble.py\`.

## Standalone scouting dashboard

\`\`\`powershell
pip install -r requirements-scouting.txt
streamlit run src/projects/streamlit_scouting.py
\`\`\`

## Test

\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

The workspace suite checks competition isolation, chronological feature construction, observed-data provenance, imports, output probabilities, CSV and chart exports, UCL regulation-time parsing, and compatibility routes.

## Repository map

| Path | Purpose |
| --- | --- |
| \`src/app.py\` | Flask application, World Cup routes, and legacy compatibility routes |
| \`src/projects/\` | Competition registry, data preparation, workspace API, models, refresh utilities, and Streamlit dashboard |
| \`web/\` | Competition-hub and workspace interface assets |
| \`data/analytics/\` | Prepared match, valuation, scouting, metadata, and optional fixture snapshots |
| \`models/workspaces/\` | Versioned workspace artifacts and training report |
| \`docs/\` | Data audit, source manifest, and workspace reference |
| \`tests/test_workspaces.py\` | End-to-end and behavioural workspace tests |

## License

This project is released under the [MIT License](LICENSE). Third-party source data remain subject to their respective licences and terms of use.
