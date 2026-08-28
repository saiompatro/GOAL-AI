# FIFA Data Sources

GOAL AI is FIFA / international-football focused. Club and league data can be
used only as real-life player context for national-team analysis; EA Sports FC,
SOFIFA, FUTBIN, FUTWIZ, and other video-game rating data are out of scope.

## Bundled / auto-fetched

Run `python ml/scripts/fetch_fifa_data.py` to download these no-credential
sources into `data/raw/`:

| Source | Files | Notes |
| --- | --- | --- |
| [martj42/international_results](https://github.com/martj42/international_results) | `results.csv`, `goalscorers.csv`, `shootouts.csv`, `former_names.csv` | International matches 1872-present, scorers, penalty shootouts |
| [jfjelstul/worldcup](https://github.com/jfjelstul/worldcup) | `data/raw/external_repos/jfjelstul_worldcup/...` | Full World Cup DB: matches, squads, player appearances, goals, bookings, stadiums, awards |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | `external/statsbomb_competitions.json` | Index of free real event data, including historic World Cups |
| [openfootball/world-cup.json](https://github.com/openfootball/world-cup.json) | `openfootball_wc2026.json` -> `wc2026_schedule.csv` | Public-domain 2026 fixture list; `ml/scripts/build_schedule.py` maps each match to a host venue |
| WC 2026 host venues, curated from FIFA/public stadium sources | `wc2026_venues.csv` | 16 stadiums: lat/lon, elevation, roof, surface, capacity, climate |
| [Open-Meteo](https://open-meteo.com/) | live API | Free weather forecast and historical archive; powers match-day weather |

## Candidate real-player extensions

- **Transfermarkt-derived datasets**: use for player identity, club, nationality,
  appearances, market values, transfer history, and national-team metadata.
- **FBref-derived player-stat datasets**: use for club/league season form, but
  verify current availability and terms because public FBref coverage has changed.
- **Official FIFA squad pages**: use for World Cup 2026 rosters once FIFA publishes
  the verified final list.
- **StatsBomb Open Data**: use for real event/player involvement data where the
  competitions are available.

## Explicitly rejected

- `data/raw/fifa_players.csv` and any replacement with the same EA/SOFIFA shape.
- Kaggle datasets titled like "FIFA 23/24/25 complete player dataset" or "EA Sports
  FC player ratings".
- Any file with video-game-only rating columns as the source of truth for real
  players: `overall`, `potential`, `pace`, `shooting`, `passing`, `dribbling`,
  `defending`, `physic`, `skill_moves`, `weak_foot`, or similar, unless the values
  are clearly derived inside this project from real match/roster facts.

## Match prediction methodology

The Match Prediction page combines:

1. A trained base model (`predict_fixture`) producing venue-neutral outcome probabilities.
2. A bounded ground-and-weather adjustment layer (`match_context.adjust`) for host
   advantage, altitude, roof, heat/humidity, rain, and wind.
3. Open-Meteo match-day weather: live forecast within about 16 days, otherwise a
   multi-year climatology for the same calendar day.

For a Claude Code implementation roadmap, see
[`data/FIFA_2026_REAL_DATASET_ROADMAP.md`](../data/FIFA_2026_REAL_DATASET_ROADMAP.md).
