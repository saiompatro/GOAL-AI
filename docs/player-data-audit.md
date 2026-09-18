# Player data source audit

Checked 18 September 2026. Public files were downloaded and inspected, rather than relying only on dataset descriptions. See `player-source-manifest.json` for download URLs, file sizes, SHA-256 checksums, actual CSV schemas and row counts.

## Current implementation

This audit now describes the installed competition-workspace data, rather than the earlier player-data prototype. GOAL AI serves separate Premier League, La Liga, Champions League, Serie A, Bundesliga, and Ligue 1 workspaces, each with independent match, valuation, and scouting datasets. Prepared CSVs and metadata are committed in `data/analytics/`; versioned models and the current evaluation report are committed in `models/workspaces/`.

The three workspace datasets are deliberately not joined into a single "complete" player table. Valuation coverage is driven by date-aligned historical market values, while scouting coverage is driven by observed performance fields. This prevents a player from disappearing from scouting simply because they lack a valid valuation target. Details of the routes, validation, and artifact lifecycle are in [workspaces.md](workspaces.md).

## Integration status: resolved

The original demo notice was accurate: player models fell back to generated
statistics while the match datasets were real. That fallback has now been removed
from the competition workspaces. Observed CSVs are installed and all 18 models
have been retrained. The app and Streamlit dashboard load them with per-tool
source and season labels. See `models/workspaces/training_report.json` for results.

Valuations use 14,695 observed player-seasons. Scouting has 3,585 source profiles,
of which 2,487 outfield profiles qualify after the 270-minute threshold. The five
domestic scouting datasets have seven performance fields; UCL has only observed
goals and assists and is clearly labelled as a basic comparison. UCL and Ligue 1
2025-26 appearance seasons are excluded because their match coverage is incomplete.

Audited raw inputs remain in `data/raw/player_sources/`, outside Git. Prepared
CSV snapshots, source metadata, trained models and the reproducible build/training
commands are included in the project. No API subscription or credential is needed
to use these historical snapshots.

## The two requested APIs

| Provider | Verified capabilities | Gap for this application |
| --- | --- | --- |
| [football-data.org](https://docs.football-data.org/general/v4/competition.html) | Matches, standings, squads, and a season-filtered scorers endpoint with goals, assists, penalties and appearances. The documented statistics add-on supplies match/team statistics. | Not a complete player-season scouting table; no documented historical market-value target. Scorers are a leaderboard, not guaranteed coverage of every squad member. |
| [The Odds API](https://the-odds-api.com/liveapi/guides/v4/) | Bookmaker odds, events, scores and historical odds; selected soccer player-prop markets. | Player-prop betting prices are not observed player statistics. No documented player valuations or full season performance table. Its participants endpoint explicitly does not return players on a team. |

The earlier blanket suggestion that football-data.org has no player statistics was too broad: its scorer records do include goals and assists. It still cannot independently supply every required model field.

[football-data.org pricing](https://www.football-data.org/pricing) lists a ten-season ML package at EUR29/month and a statistics add-on at EUR15/month. Entitlements must be checked with an account before assuming historical/scorer access. [Historical Odds API data](https://the-odds-api.com/historical-odds-data/) is paid-plan data; featured-market history starts in June 2020 and additional-market history, including props, in May 2023. Neither paid offering solves the missing valuation dataset.

`football-data.co.uk`, the public match CSV source already used by the project, is a different service from `football-data.org`.

## Downloaded datasets

### Transfermarkt-derived tables: best foundation for the valuation project

Source: [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets).

| Local file | Verified rows | Contents |
| --- | ---: | --- |
| `players.csv.gz` | 50,149 | Player IDs, names, birth dates, positions and profile fields |
| `appearances.csv.gz` | 1,894,350 | Player-match IDs, minutes, goals, assists, cards, historical club and competition |
| `player_valuations.csv.gz` | 656,301 | Player IDs, valuation dates and market values in euros |
| `games.csv.gz` | 88,958 | Match IDs, seasons, teams, dates and results |
| `transfers.csv.gz` | 175,165 | Transfer dates, clubs, fees where available and market-value references |

The tables join through stable player and game IDs. They contain all six project competitions: Premier League `GB1`, La Liga `ES1`, UCL `CL`, Serie A `IT1`, Bundesliga `L1`, Ligue 1 `FR1`.

The publisher explicitly says updates are paused and labels the snapshot current to 6 July 2026. The actual valuation file ends on 12 June 2026. Dates and completeness vary by table and competition; this is not a live 2026-27 feed.

Recent match coverage measured from appearance rows:

| Competition | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Premier League | 380 | 380 | 380 | 380 | 380 |
| La Liga | 380 | 380 | 380 | 380 | 380 |
| Champions League | 125 | 125 | 125 | 189 | 188 |
| Serie A | 380 | 380 | 380 | 380 | 380 |
| Bundesliga | 306 | 306 | 306 | 306 | 306 |
| Ligue 1 | 380 | 380 | 306 | 306 | 305 |

The UCL 2025-26 appearance rows stop on 6 May 2026 and omit the final. Ligue 1 2025-26 has one fewer match with appearances than the expected 306. Appearance coverage is not proof that every individual statistic is correct.

Market values are estimates, **not actual transfer fees**. The fee table contains 61,526 missing fees, 96,085 zero fees and 488 future-dated records relative to the audit date, including scheduled transactions/returns. It must not be treated as 175,165 completed paid transfers. No shots, key passes, successful dribbles, tackles or interceptions are present in the appearances table.

### FBref-derived season snapshots: player scouting

| Dataset | Downloaded rows | Finding |
| --- | ---: | --- |
| [2022-23 Big 5, Emre Guv](https://www.kaggle.com/datasets/emreguv/202223-big-5-football-leagues-player-stats) | 3,317 | 145 columns, including minutes, goals, assists, shots, passing and defending. Requires field-by-field normalization and duplicate/team-total inspection. |
| [2023-24 Big 5, Mamoun Kabbaj](https://www.kaggle.com/datasets/mamounkabbaj/2023-2024-big-5-european-soccer-player-statistics) | 2,958 | 37 columns; useful basic season stats, not a complete advanced scouting table. |
| [2024-25 Big 5, Hubert Sidorowicz](https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2024-2025) | 2,854 | 267 columns. All required performance fields exist and are non-null: minutes, goals, assists, shots, key passes, successful take-ons, tackles, interceptions. Includes 574 PL, 601 La Liga, 634 Serie A, 492 Bundesliga and 553 Ligue 1 player-club rows. |
| [2025-26 Big 5, Hubert Sidorowicz](https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2025-2026) | 2,839 | Actual full file has 102 columns, despite the description promising 250+. Key passes, successful take-ons and tackles are absent. Cannot replace the complete 2024-25 scouting snapshot. |

Counts are rows, not necessarily unique players. The 2024-25 table has 82 repeated player/competition combinations and 2025-26 has 67; multiple-club rows require proper aggregation rather than arbitrary deduplication. These datasets do not include UCL or market values.

The 2024-25 source records Saka with 25 appearances, 1,729 minutes, 6 goals, 10 assists, 66 shots, 58 key passes, 41 successful take-ons, 29 tackles and 3 interceptions. Salah's row contains 38 appearances, 29 goals and 18 assists. These are source observations, unlike the app's generated player table. Provider assist definitions must be kept consistent.

Also downloaded [worldfootballR's archived data](https://github.com/JaseZiv/worldfootballR_data): standard, shooting, passing, possession and defense RDS tables, plus its FBref-to-Transfermarkt ID crosswalk. Its latest season label is 2022-23 but that season is incomplete (Saka: 12 appearances, 992 minutes). Do not label those rows a completed 2022-23 season. Older complete seasons and the ID crosswalk remain useful after validation.

FBref announced removal of its advanced provider data on 20 January 2026. A new scraper therefore cannot be assumed to reproduce the older advanced tables. [Sports Reference announcement](https://www.sports-reference.com/blog/2026/01/fbref-stathead-data-update/). Third-party archive license labels do not themselves establish rights to redistribute the original provider's data commercially.

## UCL and an ongoing data feed

The downloaded Transfermarkt-derived data supports basic UCL player features and valuation joins. I did not verify a complete, current, freely downloadable UCL table containing every advanced scouting field. Some candidate repositories advertise several competitions but actually ship La Liga files; a Barcelona-only UCL dataset is not full tournament coverage.

[API-Football's documentation](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) describes season player statistics and per-fixture player statistics, including minutes, goals, assists, shots, passing, tackles, interceptions and dribbles. It is a better candidate for a consistent ongoing feed across the six competitions. League-season coverage and null fields still need checking through its API. No authenticated coverage test was performed.

[API-Football pricing](https://www.api-football.com/pricing) currently lists 100 requests/day free with restricted seasons, and Pro at USD19/month with 7,500 requests/day. It does not replace a verified historical market-valuation source.

Other inspected sources include [StatsBomb open data](https://github.com/hudl/open-data) and [Wyscout's 2017-18 event dataset](https://figshare.com/collections/Soccer_match_event_dataset/4415000/2). Their selective/older coverage and absence of market values make them secondary options for this project's requested scope.

## Integration rules implemented

1. Train the basic valuation model from observed appearances aggregated by player ID, competition and season, joining birth date/position and a suitably dated valuation target. Keep valuation date and feature cutoff explicit; never attach today's value to an old season as though it were contemporaneous.
2. Use the complete 2024-25 five-league snapshot for historical scouting. Join valuations using verified IDs or unambiguous, validated identity matches; report unmatched players instead of guessing. Keep scouting coverage independent of whether a player has a known valuation.
3. For UCL, expose the basic observed features until a complete advanced dataset or API feed is verified. Do not invent missing advanced fields or silently substitute domestic performance for UCL performance.
4. Retain the real match datasets already installed. Odds API prices can provide an additional benchmark or pre-match feature, with timestamps restricted to information available before kickoff.
5. Retrain, evaluate on later seasons and display precise source/season labels. The demo notice has been replaced with the provenance of the installed observed data.
