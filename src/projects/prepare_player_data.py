"""Build observed valuation and scouting snapshots from the audited downloads.

Run: python src/projects/prepare_player_data.py [--download]
The pinned manifest checksums prevent silent changes to the training inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from projects.competitions import ROOT, config
from projects.refresh_data import write_dataset

CODES = {"premier-league": "GB1", "la-liga": "ES1", "champions-league": "CL",
         "serie-a": "IT1", "bundesliga": "L1", "ligue-1": "FR1"}
BASIC = ["age", "minutes", "goals", "assists"]
STYLE = ["goals", "assists", "shots", "key_passes", "dribbles", "tackles", "interceptions"]
SOURCE = "Transfermarkt via dcaribou/transfermarkt-datasets"
SOURCE_URL = "https://github.com/dcaribou/transfermarkt-datasets"
FBREF_URL = "https://www.kaggle.com/datasets/hubertsidorowicz/football-players-stats-2024-2025"
REQUIRED = {"players.csv.gz", "appearances.csv.gz", "games.csv.gz",
            "player_valuations.csv.gz", "fbref_2024_25.zip"}


def inputs(download=False):
    manifest = json.loads((ROOT / "docs/player-source-manifest.json").read_text(encoding="utf-8"))
    paths = {}
    for entry in manifest["files"]:
        path = ROOT / entry["local_path"]
        if path.name not in REQUIRED:
            continue
        if not path.exists() and download:
            response = requests.get(entry["download_url"], timeout=120)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != entry["sha256"]:
                raise ValueError(f"Source changed: {path.name}. Audit the new snapshot before importing it.")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        if not path.exists():
            raise ValueError(f"Missing {path.name}; rerun with --download")
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch: {path.name}")
        paths[path.name] = path
    return paths


def expected_games(slug, year):
    if slug == "champions-league":
        return 189 if year >= 2024 else 125
    return 306 if slug == "bundesliga" or (slug == "ligue-1" and year >= 2023) else 380


def attach_values(stats, valuations):
    """First observed value strictly after the feature cutoff, within 90 days.

    Backward joins would label a full-season feature row with a value assessed
    before some of those matches occurred. Missing targets remain missing.
    """
    return pd.merge_asof(
        stats.sort_values("feature_cutoff"), valuations.sort_values("valuation_date"),
        left_on="feature_cutoff", right_on="valuation_date", by="player_id",
        direction="forward", allow_exact_matches=False, tolerance=pd.Timedelta(days=90))


def unique_labels(df, identity):
    """Keep identities separate if two people share a display name."""
    counts = df.groupby("player")[identity].nunique()
    ambiguous = set(counts[counts > 1].index)
    df.loc[df.player.isin(ambiguous), "player"] = df.loc[df.player.isin(ambiguous)].apply(
        lambda r: f"{r.player} ({r[identity]})", axis=1)
    return df


def build(download=False):
    paths = inputs(download)
    profiles = pd.read_csv(paths["players.csv.gz"], usecols=["player_id", "name", "date_of_birth", "position"])
    profiles = profiles.rename(columns={"name": "player"})
    profiles["date_of_birth"] = pd.to_datetime(profiles.date_of_birth)
    profiles["position"] = profiles.position.map({"Goalkeeper": "GK", "Defender": "DF", "Midfield": "MF", "Attack": "FW"})
    games = pd.read_csv(paths["games.csv.gz"], usecols=["game_id", "competition_id", "season", "date", "home_club_id", "away_club_id", "home_club_name", "away_club_name"])
    games = games[games.competition_id.isin(CODES.values()) & games.season.between(2021, 2025)]
    apps = pd.read_csv(paths["appearances.csv.gz"], usecols=["game_id", "player_id", "player_club_id", "goals", "assists", "minutes_played"])
    apps = apps.merge(games, on="game_id", validate="many_to_one")
    observed = apps[["minutes_played", "goals", "assists"]].to_numpy(dtype=float)
    if not np.isfinite(observed).all() or (observed < 0).any():
        raise ValueError("Missing/invalid appearance statistics must be resolved before aggregation")
    if not ((apps.player_club_id == apps.home_club_id) | (apps.player_club_id == apps.away_club_id)).all():
        raise ValueError("Appearance club does not match the fixture clubs")
    apps["team"] = np.where(apps.player_club_id == apps.home_club_id, apps.home_club_name, apps.away_club_name)
    apps["date"] = pd.to_datetime(apps.date)
    values = pd.read_csv(paths["player_valuations.csv.gz"], usecols=["player_id", "date", "market_value_in_eur"])
    values = values.rename(columns={"date": "valuation_date"})
    values["valuation_date"] = pd.to_datetime(values.valuation_date)
    if values.duplicated(["player_id", "valuation_date"]).any():
        raise ValueError("Ambiguous dated valuation records")
    values["market_value_eur_m"] = values.market_value_in_eur / 1e6
    values = values[["player_id", "valuation_date", "market_value_eur_m"]]
    all_basic = {}
    for slug, code in CODES.items():
        data = apps[apps.competition_id == code]
        counts = data.groupby("season").game_id.nunique()
        years = [int(y) for y, count in counts.items() if count == expected_games(slug, y)]
        excluded = {str(y): int(n) for y, n in counts.items() if y not in years}
        data = data[data.season.isin(years)]
        cutoffs = data.groupby("season").date.max()
        totals = data.groupby(["player_id", "season"], as_index=False).agg(
            minutes=("minutes_played", "sum"), goals=("goals", "sum"), assists=("assists", "sum"))
        # Club assignment is historical; a summer transfer must not relabel old performances.
        teams = data.groupby(["player_id", "season", "team"], as_index=False).minutes_played.sum()
        teams = teams.sort_values(["minutes_played", "team"]).drop_duplicates(["player_id", "season"], keep="last")
        totals = totals.merge(teams[["player_id", "season", "team"]], on=["player_id", "season"], validate="one_to_one")
        totals = totals.merge(profiles, on="player_id", validate="many_to_one")
        totals["feature_cutoff"] = totals.season.map(cutoffs)
        birth = totals.date_of_birth
        totals["age"] = totals.feature_cutoff.dt.year - birth.dt.year - (
            (totals.feature_cutoff.dt.month < birth.dt.month) |
            ((totals.feature_cutoff.dt.month == birth.dt.month) & (totals.feature_cutoff.dt.day < birth.dt.day))).astype(int)
        totals = totals.dropna(subset=["player", "position", "date_of_birth", *BASIC])
        totals = totals[totals.minutes.gt(0) & totals.age.between(14, 50)]
        totals = unique_labels(totals, "player_id")
        totals["season"] = totals.season.map(lambda y: f"{y}-{str(y+1)[-2:]}")
        all_basic[slug] = totals.copy()
        labelled = attach_values(totals, values).dropna(subset=["market_value_eur_m", "valuation_date"])
        labelled = labelled[labelled.market_value_eur_m.gt(0)]
        excluded_targets = len(totals) - len(labelled)
        for col in ["feature_cutoff", "valuation_date"]:
            labelled[col] = labelled[col].dt.strftime("%Y-%m-%d")
        out = labelled[["player_id", "player", "team", "season", "position", *BASIC,
                        "feature_cutoff", "valuation_date", "market_value_eur_m"]].sort_values(["season", "player_id"])
        first, last = out.season.min(), out.season.max()
        write_dataset(slug, "players", out, {"kind": "observed", "source": SOURCE,
            "source_url": SOURCE_URL, "features": BASIC, "seasons": sorted(out.season.unique()),
            "target": "First recorded market valuation within 90 days after the season's final match",
            "excluded_without_target": excluded_targets, "excluded_incomplete_seasons": excluded,
            "note": f"Observed {first}–{last} season statistics and dated market valuations. Values are estimates, not transfer fees. Historical clubs; not current squads."})

    # Scouting does not require a known valuation, so unmatched valuations never hide a player.
    with zipfile.ZipFile(paths["fbref_2024_25.zip"]) as archive:
        rich = pd.read_csv(archive.open("players_data-2024_2025.csv"))
    rich = rich.rename(columns={"Player": "player", "Squad": "team", "Age": "age", "Min": "minutes", "Gls": "goals",
        "Ast": "assists", "Sh": "shots", "KP": "key_passes", "Succ": "dribbles", "Tkl": "tackles", "Int": "interceptions"}).copy()
    rich["position"] = rich.Pos.str.split(",").str[0]
    rich["season"] = "2024-25"
    for slug in CODES:
        if slug == "champions-league":
            scout = all_basic[slug]
            scout = scout[scout.season == "2024-25"].copy()
            cols = ["goals", "assists"]
            meta = {"kind": "observed", "source": SOURCE, "source_url": SOURCE_URL,
                "note": "Observed 2024–25 UCL performances. Basic comparison uses goals and assists per 90 only; advanced scouting metrics are unavailable. Historical clubs, not current squads.",
                "scope": "basic"}
        else:
            subset = rich[rich.Comp.str.endswith(config(slug)["name"])].copy()
            # Same name, birth year and nation identify source player-club rows. Reject ambiguity.
            keys = ["player", "Born", "Nation"]
            if subset.duplicated([*keys, "team"]).any() or subset.team.str.contains(r"\d+ (?:Squads|Teams)", regex=True).any():
                raise ValueError(f"Unexpected aggregate/duplicate rows in {slug}")
            lead = subset.sort_values(["minutes", "team"]).drop_duplicates(keys, keep="last")
            totals = subset.groupby(keys, as_index=False)[["minutes", *STYLE]].sum(min_count=1)
            scout = lead[[*keys, "team", "season", "age", "position"]].merge(totals, on=keys, validate="one_to_one")
            scout["source_player_id"] = scout.player + ":" + scout.Born.astype(str) + ":" + scout.Nation
            scout = unique_labels(scout, "source_player_id")
            cols = STYLE
            meta = {"kind": "observed", "source": "FBref via Hubert Sidorowicz · 2024–25 Big Five snapshot",
                "source_url": FBREF_URL, "scope": "advanced",
                "note": "Observed 2024–25 season statistics. Seven per-90 scouting measures; historical clubs, not current squads. Multiple clubs are combined within this competition; the primary club is shown."}
        scout = scout[["player", "team", "season", "position", "age", "minutes", *cols]].copy()
        numeric = scout[["age", "minutes", *cols]]
        if not np.isfinite(numeric.to_numpy(dtype=float)).all() or (numeric < 0).any().any():
            raise ValueError(f"Missing or invalid scouting observations in {slug}")
        meta.update(features=cols, seasons=["2024-25"])
        write_dataset(slug, "scouting", scout.sort_values("player"), meta)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download missing inputs from the audited manifest")
    build(parser.parse_args().download)
