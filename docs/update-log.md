# Data and model update log

Scheduled refreshes work on one competition per day and never the same one two days running. The rotation is:

1. La Liga
2. Champions League
3. Premier League
4. Bundesliga
5. Serie A

Each run reads the last entry below, takes the next competition in the list, and appends a new entry. Newest entry last. If the competition whose turn it is has no new data from any reachable source, the run records that and moves on to the next one the same day.

## What a refresh covers

| Area | Source | Reachable from the scheduled environment |
| --- | --- | --- |
| Completed matches with shots | football-data.co.uk | No (host blocked by the environment's network policy) |
| Completed matches, scores only | OpenFootball `football.json` on GitHub | Yes |
| UCL matches | OpenFootball `champions-league` on GitHub | Yes, but it has no 2026-27 season yet |
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

### 2026-11-11 — Champions League (nothing to update), then Premier League

**Champions League.** No 2026-27 data could be obtained. OpenFootball `champions-league` was last updated on 2 July 2026 and has no `2026-27` folder; every other results host tried (uefa.com, Wikipedia, football-data.org, ESPN, and others) is blocked by the environment's network policy. The installed five seasons (753 matches, through the 30 May 2026 final) were compared with the current OpenFootball files: no differences. Data and models are unchanged. Web search shows the 2026-27 league phase has reached matchday 4 (3–4 November 2026), but search snippets are not a source the dataset can be built from, so nothing was entered by hand.

**Premier League.**

- **Matches:** added the 2026-27 season to `data/analytics/premier_league_matches.csv`: 50 completed fixtures, 21 August to 20 September 2026, from OpenFootball (scores only; shots empty). The OpenFootball feed itself stopped updating on 22 September 2026, so results after 20 September are missing for every domestic league, not only this one. The five earlier seasons are unchanged. The new name map was checked against all five installed seasons: 1,900 shared fixtures, no score or date differences.
- **Teams:** the current-season list is now the 2026-27 division. In: Coventry, Hull, Ipswich. Out: Burnley, West Ham, Wolves.
- **Elo model (`data/club`, `models/premier_league_model.joblib`):** history extended from 2023-24 to 20 September 2026 (810 matches added), features and state rebuilt, model retrained. Held-out seasons 2025-26 and 2026-27 (430 matches): accuracy 49.1%, log loss 1.035, Elo-favourite baseline 48.1%, always-home baseline 41.9%. The previous figures (54.6% on 2022-23 and 2023-24) were for a different holdout and are not comparable. Top Elo: Man City 1908, Arsenal 1889, Liverpool 1744, Man United 1738.
- **Workspace match model (`models/workspaces/premier-league_match.*`):** retrained on 1,849 matches. The held-out season is now 2026-27 with only 45 matches, so its accuracy (37.8%, baseline 33.3%) is a small-sample figure and not comparable with the previous full-season 45.9%. Rolling shot features are empty for current-season rows until shot data is available.
- **Not changed:** player valuations and scouting profiles (pinned snapshots), fixtures, injuries (no club-injury dataset in the project), the other competitions.
- **Code:** Premier League name map in `src/projects/openfootball.py`, one new test, and a README paragraph that the previous run had garbled is restored.
- **What would unblock real updates:** allow `www.football-data.co.uk` (domestic results with shots, current to the latest round) and a UCL results host in the environment's network settings. Until then each league can only be brought up to 20 September 2026.

Next in rotation: **Bundesliga**.
