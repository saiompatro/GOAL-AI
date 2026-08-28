# FIFA 2026 Real Dataset Roadmap

Last verified: 2026-05-31

This project must use real football data only. Do not use EA Sports FC, SOFIFA,
FUTBIN, FUTWIZ, Ultimate Team, Career Mode, or any other video-game player data.

## Straight Answer

There is no complete real-life FIFA World Cup 2026 match-event/player-performance
dataset yet because the tournament starts on 2026-06-11. As of 2026-05-31, real
2026 data that can be used safely is schedule, venue/stadium, qualified-team,
provisional squad, club/league player form, and historical football data.

Official final 26-player squad lists are due to FIFA on 2026-06-01 and FIFA has
stated the verified final list is announced on 2026-06-02. Until then, treat
team-announced squads as provisional. Live 2026 match events, lineups, xG, and
player stats will require a commercial/live API during the tournament or a later
open release.

## Local Data Policy

Removed/rejected:

- `data/raw/fifa_players.csv`: EA-style player rating table with video-game
  attributes such as Crossing, Finishing, GKDiving, etc.
- Any Kaggle or GitHub dataset titled like "FIFA 23/24/25 complete player dataset"
  or "EA Sports FC player ratings".
- Any synthetic/demo football data.

Kept/approved:

- `data/raw/results.csv`
- `data/raw/goalscorers.csv`
- `data/raw/shootouts.csv`
- `data/raw/former_names.csv`
- `data/raw/openfootball_wc2026.json`
- `data/raw/wc2026_schedule.csv`
- `data/raw/wc2026_venues.csv`
- `data/raw/external/statsbomb_competitions.json`
- `data/raw/external_repos/jfjelstul_worldcup/`

Generated artifacts in `ml/artifacts/players.parquet` are currently derived from
the real `jfjelstul/worldcup` database, not EA data. The fields named `overall`,
`pace`, `shooting`, etc. are project-derived compatibility indices from real World
Cup appearances/goals/bookings, not video-game ratings. Future work should rename
these to `derived_overall_index`, `derived_attacking_index`, etc.

## Source Priority

Use sources in this order:

1. Official FIFA pages for 2026 schedule, venues, host cities, capacities, squad
   announcements, and final squads.
2. Open real football repositories with clear provenance and license.
3. Kaggle mirrors only when the source is real football data and the license is
   usable.
4. Commercial APIs only for live 2026 match events/player stats that do not exist
   openly yet.
5. Social platforms only for discovery, not as source-of-truth data.

## Core 2026 World Cup Data

| Need | Source | Status | Access | Target file/table | Implementation notes |
| --- | --- | --- | --- | --- | --- |
| Official match schedule | FIFA schedule page: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums | Real, current | Web page | `data/raw/wc2026_schedule.csv` | Use as authority for match numbers, dates, local kickoffs, stages, venues. Cross-check existing `openfootball_wc2026.json`. |
| Open schedule JSON | openfootball `worldcup.json`: https://github.com/openfootball/worldcup.json | Real schedule; public domain | Raw GitHub JSON | `data/raw/openfootball_wc2026.json` | Existing `ml/scripts/build_schedule.py` already consumes this. Validate against FIFA before model use. |
| Normalized schedule/SQLite | Kaggle: https://www.kaggle.com/datasets/areezvisram12/fifa-world-cup-2026-match-data-unofficial | Useful but unofficial | Kaggle API | Optional `data/raw/external/kaggle_wc2026_schedule/` | Convenience copy only. Do not let it override FIFA/openfootball. |
| Venues and stadium metadata | FIFA stadium address/capacity FAQ: https://gpcustomersupportfwc2026.tickets.fifa.com/hc/en-gb/articles/28784010437021-2-What-are-the-official-addresses-stadium-capacities-and-maps-of-the-FIFA-World-Cup-2026-stadiums | Official | Web page | `data/raw/wc2026_venues.csv` | Existing CSV has coordinates, roof, surface, elevation, climate. Reconcile capacities with FIFA's current net capacities. |
| Qualified teams | FIFA qualified teams page: https://www.fifa.com/en/articles/world-cup-2026-who-has-qualified | Official | Web page | `data/raw/wc2026_qualified_teams.csv` | Add if team list is needed independently of schedule. |
| Official squads | FIFA squad announcements page: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/all-world-cup-squad-announcements | Provisional until 2026-06-02 | Web page | `data/raw/fifa_2026_squads.csv` | Build after final lists. Columns: team, player_name, position, birth_date, club, shirt_number, source_url, final_or_provisional. |

## Historical International Match Data

| Need | Source | Status | Access | Target file/table | Implementation notes |
| --- | --- | --- | --- | --- | --- |
| International results | `martj42/international_results`: https://github.com/martj42/international_results | Real, maintained | Raw GitHub CSV | `data/raw/results.csv` | Current primary match-history base. Includes friendlies, qualifiers, tournaments. |
| Goalscorers/shootouts | `martj42/international_results` | Real, maintained | Raw GitHub CSV | `data/raw/goalscorers.csv`, `data/raw/shootouts.csv` | Use for scorer features and penalty history. |
| World Cup database | `jfjelstul/worldcup`: https://github.com/jfjelstul/worldcup | Real historical WC DB through 2022 men's / 2019 women's | Git clone / vendored | `data/raw/external_repos/jfjelstul_worldcup/` | Already vendored. Best open source for historical World Cup players, squads, stadiums, matches, goals, bookings, substitutions. |
| DataHub World Cup mirror | https://datahub.io/football/worldcup | Derived from Fjelstul | Download | Optional | Use only if easier than vendored Fjelstul; respect CC-BY-SA. |
| StatsBomb Open Data | https://github.com/statsbomb/open-data | Real event data; historic competitions | GitHub JSON | `data/raw/external/statsbomb_*` | Use for event-level modeling from available World Cups and other competitions. No 2026 live data guarantee. |

## Real Player Data Sources

| Need | Source | Status | Access | Target file/table | Implementation notes |
| --- | --- | --- | --- | --- | --- |
| Player identity, clubs, national teams, appearances, valuations | `dcaribou/transfermarkt-datasets`: https://github.com/dcaribou/transfermarkt-datasets | Real Transfermarkt-derived data; updated pipeline | GitHub/Kaggle/DuckDB | `data/raw/transfermarkt/` | Best non-EA player base. Join on player name, nationality, club, DOB; store source IDs. Check license/terms before redistribution. |
| Large Transfermarkt datalake | `salimt/football-datasets`: https://github.com/salimt/football-datasets | Real Transfermarkt-derived data | GitHub/Kaggle | Optional `data/raw/transfermarkt_salimt/` | Broad coverage; use only if license and fields fit better than dcaribou. |
| Big 5 player stats 2024-25 | Kaggle FBref-derived: https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2024-2025/data | Real club player stats | Kaggle API | `data/raw/fbref_players_2024_2025.csv` | Strong recent form signal for La Liga, Premier League, Bundesliga, Serie A, Ligue 1 players. Not a complete World Cup roster source. |
| Football Data Warehouse | Kaggle: https://www.kaggle.com/datasets/conalhenderson/football-data-warehouse | Real Transfermarkt + FBref top 5 leagues | Kaggle API | Optional | Useful for 2018-2025 club form. Verify schema and license. |
| On-demand real player stats | `worldfootballR`: https://jaseziv.r-universe.dev/worldfootballR/doc/manual.html | R package for FBref, Transfermarkt, Understat, FotMob | R scripts | `scripts/fetch_worldfootballr_players.R` output CSV | Good when direct CSV datasets are insufficient. Must respect rate limits and site terms. |
| Official 2026 final squads | FIFA squad pages | Real once verified | Web | `data/raw/fifa_2026_squads.csv` | Use this to select player pools; enrich with Transfermarkt/FBref stats. |

Recommended player pipeline:

1. Fetch official FIFA final squads after 2026-06-02.
2. Normalize player names, DOB, nationality, position, club, and FIFA source URL.
3. Join to Transfermarkt player IDs using exact DOB + fuzzy name + nationality.
4. Join club/league recent form from FBref/Transfermarkt-derived data.
5. Produce `data/processed/real_player_pool.parquet`.
6. Derive model features with clear `derived_` prefixes; never import EA ratings.

## Club And League Match Data

| Need | Source | Status | Access | Target file/table | Implementation notes |
| --- | --- | --- | --- | --- | --- |
| Club match results/stat lines | football-data.co.uk: https://www.football-data.co.uk/data | Real club results and match stats | CSV/Excel | `data/raw/club_results/` | Covers major European leagues and odds; no rich player data. Useful for team/club context. |
| OpenFootball league data | https://github.com/openfootball | Real fixture/result text datasets | GitHub | Optional | Useful for simple fixture/result coverage; not player-level. |
| football-data.org | https://www.football-data.org/ | Real API | API token | Optional | Fixtures, standings, lineups depending plan. Free tier limited. |
| API-Football | https://www.api-football.com/ | Real API | API key | Optional | Broad coverage; check cost/rate/rights before relying on it. |

## Live 2026 Match/Event Data

Open, complete 2026 event data is not available yet. During the tournament, use
one of these only if the project accepts API keys/costs/licensing:

| Source | URL | Likely coverage | Caution |
| --- | --- | --- | --- |
| BALLDONTLIE FIFA API | https://fifa.balldontlie.io/ | Teams, stadiums, players, rosters, matches, standings, lineups, events, stats, odds | Verify pricing, uptime, rights, and exact 2026 coverage. |
| Statorium World Cup API | https://statorium.com/fifa-world-cup-2026-api | Fixtures, squads/player data, live data | Commercial terms. |
| TheStatsAPI World Cup | https://www.thestatsapi.com/world-cup | Fixtures, scores, xG, player stats, odds | Commercial terms. |
| SportsDataIO | https://sportsdata.io/ | Soccer/world soccer API | Commercial terms. LinkedIn mentions are marketing, not dataset proof. |
| football-data.org | https://www.football-data.org/ | Fixtures/results/standings | May not expose player events. |

If using any live API, persist raw responses in `data/raw/api_snapshots/<provider>/`
with timestamps so results are reproducible.

## Social Platform Search Outcome

I checked web-indexed results for X, Reddit, Instagram, LinkedIn, Kaggle, and
GitHub. The useful discoveries came from Kaggle/GitHub and a few Reddit posts
that link back to Kaggle. LinkedIn results were mostly vendor announcements and
marketing posts. I did not find a reliable Instagram or X dataset download that
should be used as project data.

Do not scrape social posts for player/match facts. Social sources can be used only
to discover a dataset, then the dataset must be validated from its actual source.

## Target Schemas

### `data/raw/fifa_2026_squads.csv`

Required columns:

- `team`
- `player_name`
- `position`
- `shirt_number`
- `birth_date`
- `club`
- `club_country`
- `source_url`
- `source_published_at`
- `squad_status` (`provisional` or `final`)
- `fetched_at_utc`

### `data/processed/real_player_pool.parquet`

Required columns:

- `player_id_project`
- `team`
- `player_name`
- `birth_date`
- `nationality`
- `position_group`
- `club`
- `league`
- `minutes_2024_2025`
- `goals_2024_2025`
- `assists_2024_2025`
- `cards_2024_2025`
- `market_value_eur`
- `international_caps`
- `international_goals`
- `source_priority`
- `source_urls`

### `data/processed/real_team_strength.parquet`

Required columns:

- `team`
- `squad_minutes_recent`
- `squad_goals_recent`
- `squad_assists_recent`
- `squad_market_value_eur`
- `starter_minutes_recent`
- `keeper_minutes_recent`
- `defender_minutes_recent`
- `midfielder_minutes_recent`
- `forward_minutes_recent`
- `derived_team_strength_index`
- `source_urls`

### `data/raw/wc2026_match_events.csv`

Only create after games are played or from a licensed live provider.

Required columns:

- `match_id`
- `provider`
- `event_id`
- `event_time`
- `period`
- `team`
- `player_name`
- `event_type`
- `x`
- `y`
- `outcome`
- `raw_payload_path`
- `fetched_at_utc`

## Validation Gates

Add these checks before any new dataset is accepted:

1. Reject files named `fifa_players.csv`, `sofifa*.csv`, `eafc*.csv`, `fut*.csv`,
   or any source URL containing `sofifa`, `futbin`, `futwiz`, `ea.com/games`,
   `easports`, `ultimate-team`, or `career-mode`.
2. Reject player datasets where `overall`, `potential`, `pace`, `shooting`,
   `passing`, `dribbling`, `defending`, or `physic` are imported source columns.
   If the project derives these from real data, rename them to `derived_*`.
3. Require `source_url`, `license`, `fetched_at_utc`, and `source_owner` in a
   manifest for every raw dataset.
4. Require official FIFA confirmation before marking squads as `final`.
5. Require match dates to be historical before accepting event/player performance
   data as real 2026 match data.
6. Keep raw downloads immutable; write normalized outputs to `data/processed/`.

## Claude Code Implementation Checklist

1. Add `scripts/fetch_fifa_2026_squads.py` after 2026-06-02.
2. Add `scripts/fetch_transfermarkt_players.py` or a Kaggle/DuckDB import for
   `dcaribou/transfermarkt-datasets`.
3. Add `scripts/validate_real_data_sources.py` implementing the validation gates.
4. Rename model/player columns from EA-style names to `derived_*` names.
5. Build `data/processed/real_player_pool.parquet` by joining FIFA squads to
   Transfermarkt/FBref real stats.
6. Rebuild `ml/artifacts/player_team_aggregates.parquet` from the real player pool.
7. Add tests proving that EA/SOFIFA-shaped files are rejected.
8. Re-run the pipeline and compare model metrics before replacing artifacts.

## Source URLs

- FIFA schedule: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums
- FIFA venue capacities/addresses: https://gpcustomersupportfwc2026.tickets.fifa.com/hc/en-gb/articles/28784010437021-2-What-are-the-official-addresses-stadium-capacities-and-maps-of-the-FIFA-World-Cup-2026-stadiums
- FIFA squad announcements: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/all-world-cup-squad-announcements
- openfootball World Cup JSON: https://github.com/openfootball/worldcup.json
- martj42 international results: https://github.com/martj42/international_results
- Fjelstul World Cup database: https://github.com/jfjelstul/worldcup
- StatsBomb Open Data: https://github.com/statsbomb/open-data
- dcaribou Transfermarkt datasets: https://github.com/dcaribou/transfermarkt-datasets
- salimt football datasets: https://github.com/salimt/football-datasets
- FBref-derived Kaggle player stats: https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2024-2025/data
- football-data.co.uk: https://www.football-data.co.uk/data
- worldfootballR manual: https://jaseziv.r-universe.dev/worldfootballR/doc/manual.html
