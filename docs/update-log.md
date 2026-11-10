# Data and model update log

Scheduled refreshes work on one competition per day and never the same one two days running. The rotation is:

1. La Liga
2. Champions League
3. Premier League
4. Bundesliga
5. Serie A

Each run reads the last entry below, takes the next competition in the list, and appends a new entry. Newest entry last.

## What a refresh covers

| Area | Source | Reachable from the scheduled environment |
| --- | --- | --- |
| Completed matches with shots | football-data.co.uk | No (host blocked by the environment's network policy) |
| Completed matches, scores only | OpenFootball `football.json` on GitHub | Yes |
| UCL matches | OpenFootball `champions-league` on GitHub | Yes |
| Player seasons and valuations | Pinned Transfermarkt/FBref snapshots (`docs/player-source-manifest.json`) | Not refreshed; pinned and audited by design |
| Fixtures, rosters | football-data.org (token) | No |
| Injuries | No club-injury dataset exists in the project; only World Cup news sentiment in `src/live.py` | Not applicable |

## Entries

### 2026-11-10 — La Liga

- **Matches:** added the 2026-27 season to `data/analytics/la_liga_matches.csv`: 69 completed fixtures, 15 August to 20 September 2026, from OpenFootball (scores only; shots empty). The feed had nothing newer on the run date, so results after 20 September are still missing. The five earlier seasons are unchanged. The name map was checked against the installed 2024-25 and 2025-26 seasons: 750 shared fixtures, no score or date differences.
- **Teams:** the current-season list is now the 2026-27 division. In: Deportivo La Coruña, Málaga, Racing Santander. Out: Girona, Mallorca, Oviedo.
- **Elo model (`data/club`, `models/la_liga_model.joblib`):** history extended from 2023-24 to 20 September 2026 (829 matches added), features and state rebuilt, model retrained. Held-out seasons 2025-26 and 2026-27 (449 matches): accuracy 52.8%, log loss 0.966, Elo-favourite baseline 50.8%. Top Elo: Barcelona 1960, Real Madrid 1850, Atlético 1750, Betis 1743.
- **Workspace match model (`models/workspaces/la-liga_match.*`):** retrained on 1,852 matches. The held-out season is now 2026-27 with only 61 matches, so its accuracy (45.9%, baseline 42.6%) is a small-sample figure and not comparable with the previous full-season 49.6%. Rolling shot features are empty for every current team until shot data is available, so current predictions rest on form and goals.
- **Not changed:** player valuations and scouting profiles (pinned snapshots), fixtures, the other competitions.
- **Code:** `src/projects/openfootball.py` (new), fallback in `src/projects/refresh_data.py`, season top-up in `src/fetch_club_results.py`, stable same-day ordering in `src/club_features.py`, two new tests.
- **To get shots and results after 20 September:** allow `www.football-data.co.uk` in the environment's network settings; the next La Liga refresh then replaces the scores-only rows with full records.

Next in rotation: **Champions League**.
