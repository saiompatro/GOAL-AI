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
| Premier League matches with shots | `olbauday/FPL-Elo-Insights` on GitHub | Yes; current to the latest round |
| Current-season matches with shots, and upcoming fixtures | `oladeeayo/open-matchday` on GitHub (75 competitions, 2026-27 only, refreshed daily; non-commercial use with attribution). Mapped so far: Bundesliga | Yes; current to the latest round |
| Completed matches, scores only | OpenFootball `football.json` on GitHub | Yes, but frozen at 20 September 2026 |
| UCL matches | OpenFootball `champions-league` on GitHub | Yes, but it has no 2026-27 season yet |
| Player seasons and valuations | Pinned Transfermarkt/FBref snapshots (`docs/player-source-manifest.json`) | Not refreshed; pinned and audited by design |
| Fixtures, rosters | football-data.org (token) | No (fixtures come from open-matchday instead where it is mapped) |
| Injuries and suspensions | Premier League only: `olbauday/FPL-Elo-Insights` (`refresh_data.py premier-league --availability`). No source for the other competitions | Yes |

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

### 2026-11-12 — Bundesliga

- **Matches:** added the 2026-27 season to `data/analytics/bundesliga_matches.csv`: 36 completed fixtures (matchdays 1–4), 28 August to 20 September 2026, from OpenFootball (scores only; shots empty). The OpenFootball feed still ends on 20 September, so about seven weeks of results are missing. The five earlier seasons hold the same values as before; their shot columns are now written as integers (`11` instead of `11.0`), which is why every line of the file shows as changed. The new name map was checked against all five installed seasons: 1,530 shared fixtures, no score or date differences.
- **Teams:** the current-season list is now the 2026-27 division. In: Elversberg, Paderborn, Schalke 04. Out: Heidenheim, St Pauli, Wolfsburg.
- **Elo model (`data/club`, `models/bundesliga_model.joblib`):** history extended from 2023-24 to 20 September 2026 (648 matches added), features and state rebuilt, model retrained. Held-out seasons 2025-26 and 2026-27 (342 matches): accuracy 50.3%, log loss 1.007, Elo-favourite baseline 53.8%, always-home baseline 44.7%. On this holdout the model is 3.5 points worse than simply picking the Elo favourite; on the previous holdout (2022-23 and 2023-24) it was level with it (51.3% against 50.5%). Top Elo: Bayern Munich 2005, Dortmund 1853, Leverkusen 1762, Stuttgart 1721.
- **Workspace match model (`models/workspaces/bundesliga_match.*`):** retrained on 1,482 matches. The held-out season is now 2026-27 with only 30 matches, so its accuracy (50.0%, baseline 56.7%) is a small-sample figure and not comparable with the previous full-season 53.1%. Rolling shot features are empty for current-season rows until shot data is available.
- **Not changed:** player valuations and scouting profiles (pinned snapshots), fixtures, injuries (no club-injury dataset in the project), the other competitions.
- **Code:** Bundesliga name map in `src/projects/openfootball.py`, one new test (21 pass).
- **Still blocked:** `www.football-data.co.uk` and every other live results host. Until one is allowed in the environment's network settings, each league can only be brought up to 20 September 2026.

Next in rotation: **Serie A**.

### 2026-11-13 — Serie A

- **Matches:** added the 2026-27 season to `data/analytics/serie_a_matches.csv`: 50 completed fixtures (rounds 1–5), 22 August to 20 September 2026, from OpenFootball (scores only; shots empty). The OpenFootball feed still ends on 20 September, so about eight weeks of results are missing. The five earlier seasons are unchanged. The new name map was checked against all five installed seasons: 1,890 shared fixtures, no score or date differences (OpenFootball lacks ten 2024-25 fixtures that the installed data has).
- **Teams:** the current-season list is now the 2026-27 division. In: Frosinone, Monza, Venezia. Out: Cremonese, Pisa, Verona.
- **Elo model (`data/club`, `models/serie_a_model.joblib`):** history extended from 2023-24 to 20 September 2026 (810 matches added), features and state rebuilt, model retrained. Held-out seasons 2025-26 and 2026-27 (430 matches): accuracy 52.3%, log loss 1.006, Elo-favourite baseline 51.9%, always-home baseline 39.5%. On the previous holdout (2022-23 and 2023-24) it was 52.5% against 52.4%. Top Elo: Inter 1965, Roma 1855, Napoli 1794, Como 1792.
- **Workspace match model (`models/workspaces/serie-a_match.*`):** retrained on 1,849 matches. The held-out season is now 2026-27 with only 50 matches, so its accuracy (68.0%, baseline 44.0%) is a small-sample figure and not comparable with the previous full-season 49.6%; it predicted no draws. Rolling shot features are empty for current-season rows until shot data is available.
- **Not changed:** player valuations and scouting profiles (pinned snapshots), fixtures, injuries (no club-injury dataset in the project), the other competitions.
- **Code:** Serie A club-name map in `src/projects/openfootball.py`, one new test.
- **Still blocked:** `www.football-data.co.uk` and every other live results host; OpenFootball has no 2026-27 Champions League season. Until a results host is allowed in the environment's network settings, each league can only be brought up to 20 September 2026. All four mapped leagues and the Champions League are now at that limit, so later runs have nothing new to add until the feed resumes or a host is allowed.

Next in rotation: **La Liga**.

### 2026-11-14 — La Liga (nothing to update); every other competition checked, nothing new

- **La Liga:** no new results from any reachable source. The OpenFootball feed (`football.json` and the `espana` repository) still ends on 20 September 2026 with the same 69 fixtures already installed. `www.football-data.co.uk` is still blocked by the environment's network policy.
- **Other competitions, checked the same day as the rotation rule requires:** Premier League (50 fixtures), Bundesliga (36) and Serie A (50) are likewise unchanged upstream and end on 20 September. OpenFootball still has no 2026-27 Champions League season.
- **Changed:** nothing. No data, team list, model or code was modified; retraining on identical inputs would only rewrite timestamps.
- **Missing as of this run:** about eight weeks of 2026-27 results in all four domestic leagues, the whole 2026-27 Champions League league phase, and shot data for every 2026-27 match.
- **To unblock:** allow `www.football-data.co.uk` in the environment's network settings (domestic results with shots, current to the latest round). The Champions League additionally needs a results host, or `FOOTBALL_DATA_TOKEN` plus `api.football-data.org`.

Next in rotation: **Champions League**.

### 2026-11-15 — Champions League (nothing complete to install), then Premier League

**Champions League.** Still no usable 2026-27 season. OpenFootball `champions-league` was last updated on 2 July 2026 and has no 2026-27 folder. A new source found today, `olbauday/FPL-Elo-Insights`, carries Champions League matches, but only those involving the five English clubs: 20 of the 72 league-phase matches played so far. Installing those alone would cut the current-season team list to the English clubs and their opponents and make the held-out season a sample in which an English club plays every match, so they were not installed. Data and models are unchanged; the installed seasons still end with the 30 May 2026 final.

**Premier League.**

- **New source:** [FPL-Elo-Insights](https://github.com/olbauday/FPL-Elo-Insights) is reachable (GitHub), was updated on the run date, and has scores and total shots. Checked against the installed football-data.co.uk 2025-26 season: 380 of 380 fixtures and dates agree, 379 scores agree (it has Liverpool 0–1 Man United on 19 October 2025; football-data.co.uk has 1–2), and 98.5% of shot counts are identical, the rest within two. Its first 50 fixtures of 2026-27 match the OpenFootball scores already installed.
- **Matches:** 2026-27 in `data/analytics/premier_league_matches.csv` goes from 50 scores-only fixtures (to 20 September) to 100 fixtures with shots (gameweeks 1–10, to 8 November 2026). The 50 scores-only rows were replaced by the fuller records; the five earlier seasons are unchanged.
- **Injuries and suspensions (new):** `data/analytics/premier_league_availability.csv` lists 86 players as of gameweek 10: 59 injured, 24 doubtful, 3 suspended. Players flagged unavailable because they left their club are excluded. The match page shows the list; no model uses it.
- **Elo model (`data/club`, `models/premier_league_model.joblib`):** history extended to 8 November 2026 (50 matches added), features and state rebuilt, model retrained. Held-out seasons 2025-26 and 2026-27 (480 matches): accuracy 49.4%, log loss 1.034, Elo-favourite baseline 48.3%, always-home baseline 42.5%. Top Elo: Arsenal 1921, Man City 1842, Brighton 1771, Liverpool 1762. Largest moves since 20 September: Tottenham +60, Brighton +52, Man City −66, Man United −60.
- **Workspace match model (`models/workspaces/premier-league_match.*`):** retrained on the same 1,849 earlier matches; the 2026-27 holdout is now 95 matches: accuracy 42.1%, baseline 41.1%, log loss 1.098. It still predicts no draws. Rolling shot features are now filled for current-season rows.
- **Not changed:** player valuations and scouting profiles (pinned snapshots), fixtures, the other competitions.
- **Code:** `src/projects/fpl_insights.py` (new), fallback order and scores-only replacement in `src/projects/refresh_data.py`, `--availability`, `availability` in the workspace API, an injuries panel in `web/workspace.js`, four new tests (26 pass).
- **For later runs:** the environment's git proxy serves anonymous clones of any public GitHub repository, and `raw.githubusercontent.com` is reachable, so a maintained public repository is a workable source. None has been found yet for La Liga, the Bundesliga, Serie A or the full Champions League; those remain at 20 September 2026 (30 May 2026 for the Champions League) until one is found or `www.football-data.co.uk` is allowed in the environment's network settings.

Next in rotation: **Bundesliga**.

### 2026-11-16 — Bundesliga

- **New source:** [open-matchday](https://github.com/oladeeayo/open-matchday) is reachable (GitHub, `master` branch), was refreshed on the run date, and has scores, total shots and the remaining fixture list. It publishes 2026-27 only, so it could not be compared with an installed football-data.co.uk season the way FPL-Elo-Insights was. What was checked: its first 36 fixtures agree with the OpenFootball rows already installed on every score and date; every club has played exactly nine matches; and a news report on matchday 9 matches the resulting table (Bayern and Dortmund level on 21 points). Its terms allow non-commercial use with attribution and give no warranty; `_matches.json` records that.
- **Matches:** 2026-27 in `data/analytics/bundesliga_matches.csv` goes from 36 scores-only fixtures (to 20 September) to 81 fixtures with shots (matchdays 1–9, to 8 November 2026). The 36 scores-only rows were replaced by the fuller records; the five earlier seasons are unchanged. The league is on an international break and resumes on 20 November, so this is every match played.
- **Shot counts are higher than last season's:** 16.4 home and 14.2 away per match in these 81 fixtures, against 14.6 and 11.9 in the football-data.co.uk 2025-26 season. Whether that is the early-season sample or a different counting rule at the source is not known. The rolling shot features for current teams are therefore on a slightly different scale from the training seasons.
- **Fixtures (new):** `data/analytics/bundesliga_fixtures.json` holds the 225 remaining fixtures (matchday 10 starts with Bayern Munich v FC Koln on 20 November). The match page lists the next six and now names the feed they came from.
- **Teams:** unchanged from the 12 November refresh (18 clubs, all mapped).
- **Elo model (`data/club`, `models/bundesliga_model.joblib`):** history extended to 8 November 2026 (45 matches added), features and state rebuilt, model retrained. Held-out seasons 2025-26 and 2026-27 (387 matches): accuracy 50.6%, log loss 1.010, Elo-favourite baseline 53.7%, always-home baseline 45.2%. The model is still about three points worse than picking the Elo favourite. Top Elo: Bayern Munich 2009, Dortmund 1853, RB Leipzig 1743, Leverkusen 1734. Largest moves since 20 September: RB Leipzig +43, Werder Bremen +38, Mainz −51, Augsburg −42.
- **Workspace match model (`models/workspaces/bundesliga_match.*`):** retrained on the same 1,482 earlier matches; the 2026-27 holdout is now 75 matches: accuracy 48.0%, baseline 52.0%, log loss 1.033. It predicts no draws and is below the baseline on this sample. Rolling shot features are now filled for current-season rows.
- **Not changed:** player valuations and scouting profiles (pinned snapshots), the other competitions. No injury or suspension source exists for the Bundesliga; open-matchday has none.
- **Code:** `src/projects/open_matchday.py` (new), a list of shot-carrying fallback feeds and `--fixtures` without a token in `src/projects/refresh_data.py`, the fixture panel's source label in `web/workspace.js`, four new tests (30 pass).
- **For later runs:**
  - open-matchday also has La Liga (`ESP_1_la-liga`), Serie A (`ITA_1_serie-a`), Ligue 1 and the full Champions League (`UEFA_1_champions-league`). Each needs a club-name map in `open_matchday.LEAGUES` before `refresh_data.py <slug>` will use it; the Champions League additionally needs handling for regulation-time scores and neutral finals. That removes the 20 September limit for those competitions.
  - `club_features.py` and `train_league.py` rebuild every league when run as scripts, whatever argument is given. For one league call `club_features.build_match_table(key)` (and write the table and state) and `train_league.train_one(key)`.
  - The saved workspace models record library versions (Python 3.13.18, numpy 2.5.4, pandas 3.1.1 for the recent ones). Train with the same versions, or the saved model is treated as stale and retrained on first request. The La Liga and Champions League match models were saved under older versions and are already in that state.
  - `www.football-data.co.uk` is still blocked.

Next in rotation: **Serie A**.
