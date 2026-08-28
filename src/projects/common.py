"""Shared paths, schema and data loading for the Premier League projects.

Three self-contained projects live under this package, each a small end-to-end
machine-learning study on Premier League data:

    1. transfer_value  — linear model: player stats -> market/transfer value
    2. match_outcome   — random-forest / XGBoost: match features -> win/draw/loss
    3. player_scouting — nearest-neighbours + K-means: similar players & styles

They all read from bundled data so they run with no API token; see
`fetch_players.py` / `gen_player_data.py` for how the player table is produced,
and `../fetch_club_results.py` for the match-results table (shared with the
club-league match predictor).
"""
import os

_HERE = os.path.dirname(__file__)
BASE = os.path.abspath(os.path.join(_HERE, "..", ".."))

DATA = os.path.join(BASE, "data")
PLAYERS_CSV = os.path.join(DATA, "players", "premier_league_players.csv")
CLUB_RESULTS_CSV = os.path.join(DATA, "club", "premier_league_results.csv")
MODELS_DIR = os.path.join(BASE, "models", "projects")

# Player-stat features used by the transfer-value and scouting projects.
FEATURE_COLUMNS = ["age", "minutes", "goals", "assists", "shots",
                   "key_passes", "dribbles", "tackles", "interceptions"]

# The subset that describes *playing style* (rate-like, position-revealing),
# used for player-similarity in the scouting project.
STYLE_COLUMNS = ["goals", "assists", "shots", "key_passes",
                 "dribbles", "tackles", "interceptions"]


def load_players():
    """Return the player-season table as a pandas DataFrame.

    Falls back to generating the bundled sample dataset the first time if it is
    missing, so a fresh clone works without a separate build step.
    """
    import pandas as pd
    if not os.path.exists(PLAYERS_CSV):
        from projects import gen_player_data
        gen_player_data.main()
    return pd.read_csv(PLAYERS_CSV)


def latest_player_seasons(df):
    """One row per player: their most recent season in the table."""
    order = {s: i for i, s in enumerate(sorted(df["season"].unique()))}
    df = df.assign(_o=df["season"].map(order))
    idx = df.sort_values("_o").groupby("player")["_o"].idxmax()
    return df.loc[idx].drop(columns="_o").reset_index(drop=True)
