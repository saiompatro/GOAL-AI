"""Competition registry and explicit provenance for the analytics workspaces."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "analytics"
COMPETITIONS = {
    "premier-league": dict(key="premier_league", name="Premier League", region="England", code="PL", csv="E0", color="#b7f66b", short="PL"),
    "la-liga": dict(key="la_liga", name="La Liga", region="Spain", code="PD", csv="SP1", color="#ff927c", short="LL"),
    "champions-league": dict(key="champions_league", name="Champions League", region="Europe", code="CL", csv=None, color="#94a9ff", short="UCL"),
    "serie-a": dict(key="serie_a", name="Serie A", region="Italy", code="SA", csv="I1", color="#79baff", short="SA"),
    "bundesliga": dict(key="bundesliga", name="Bundesliga", region="Germany", code="BL1", csv="D1", color="#ff8299", short="BL"),
    "ligue-1": dict(key="ligue_1", name="Ligue 1", region="France", code="FL1", csv="F1", color="#72dfcd", short="L1"),
}

def config(slug):
    if slug not in COMPETITIONS:
        raise ValueError("Unknown competition")
    return COMPETITIONS[slug]


def _player_dataset(slug, kind):
    path = DATA / f"{config(slug)['key']}_{kind}.csv"
    meta = path.with_suffix(".json")
    if not path.exists() or not meta.exists():
        raise ValueError("Observed player data is missing. Run src/projects/prepare_player_data.py --download.")
    return pd.read_csv(path), json.loads(meta.read_text(encoding="utf-8"))


def players(slug):
    """Observed season statistics with date-aligned market valuations."""
    return _player_dataset(slug, "players")


def scout_players(slug):
    """Independent scouting coverage, including players without a valuation."""
    return _player_dataset(slug, "scouting")


def latest_snapshot(df):
    """Only participants in the most recent installed season, never old squads."""
    return df[df.season == df.season.max()].reset_index(drop=True)


def matches(slug):
    c = config(slug)
    path = DATA / f"{c['key']}_matches.csv"
    if path.exists():
        df = pd.read_csv(path)
        meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    else:
        path = ROOT / "data/club" / f"{c['key']}_results.csv"
        if not path.exists():
            raise ValueError("No match dataset installed for this competition. Run the data refresh command in README.md.")
        df = pd.read_csv(path)
        meta = {"source": "footballcsv / football-data.co.uk", "kind": "historical"}
    return df.sort_values("date", kind="stable").reset_index(drop=True), meta
