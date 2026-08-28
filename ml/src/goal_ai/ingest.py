"""Dataset ingestion.

Downloads no-auth real football match data when needed; otherwise expects CSVs
already present in the raw data directory. Player data must come from real match,
roster, club, or league sources. EA Sports / SOFIFA / video-game rating datasets
are intentionally excluded.
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from .data_policy import DataPolicyError, enforce_real_player_source, is_rejected_source_name
from .ingest_jfjelstul import load_raw as load_jfjelstul_raw
from .ingest_jfjelstul import repo_available as jfjelstul_available

KAGGLE_DATASETS = {
    "results": "martj42/international-football-results-from-1872-to-2017",
}

PUBLIC_DATASET_URLS = {
    "results": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
}


def _try_kaggle_download(raw_dir: Path) -> None:
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi  # type: ignore
    except Exception:
        return
    try:
        api = KaggleApi()
        api.authenticate()
        for slug in KAGGLE_DATASETS.values():
            api.dataset_download_files(slug, path=str(raw_dir), unzip=True, quiet=False)
    except Exception as e:
        print(f"[ingest] Kaggle download skipped: {e}")


def _try_public_download(raw_dir: Path) -> None:
    targets = {
        raw_dir / "results.csv": PUBLIC_DATASET_URLS["results"],
    }
    for target, url in targets.items():
        if target.exists():
            continue
        try:
            print(f"[ingest] Downloading public dataset: {target.name}")
            urlretrieve(url, target)
        except Exception as e:
            print(f"[ingest] Public download skipped for {target.name}: {e}")


def _find_real_player_file(raw_dir: Path) -> Path | None:
    """Return an approved real-player data file, never an EA/SOFIFA dump."""
    candidates = [
        raw_dir / "players.csv",
        raw_dir / "transfermarkt_players.csv",
        raw_dir / "fbref_players.csv",
        raw_dir / "worldcup_squads.csv",
    ]
    for path in candidates:
        if not path.exists():
            continue
        if is_rejected_source_name(path):
            raise DataPolicyError(f"Rejected player source {path}: source name is not real-football data")
        header = pd.read_csv(path, nrows=0).columns
        enforce_real_player_source(path, header)
        return path
    return None


def load_raw(raw_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    results_path = raw_dir / "results.csv"

    if jfjelstul_available(raw_dir):
        print("[ingest] Using vendored jfjelstul/worldcup as primary World Cup source.")
        jf_matches, jf_players = load_jfjelstul_raw(raw_dir)
        auxiliary_matches = pd.DataFrame()
        if results_path.exists():
            legacy = pd.read_csv(results_path)
            tournament = legacy.get("tournament", pd.Series([""] * len(legacy))).astype(str).str.lower()
            auxiliary_matches = legacy[~tournament.eq("fifa world cup")].copy()
        matches = pd.concat([auxiliary_matches, jf_matches], ignore_index=True, sort=False)
        return matches, jf_players

    if not results_path.exists():
        _try_kaggle_download(raw_dir)

    if not results_path.exists():
        _try_public_download(raw_dir)

    if not results_path.exists():
        raise FileNotFoundError(
            f"No real match dataset found at {results_path}. Run ml/scripts/fetch_fifa_data.py "
            "or provide a real results.csv source."
        )

    matches = pd.read_csv(results_path)
    players_path = _find_real_player_file(raw_dir)
    players = pd.read_csv(players_path) if players_path else pd.DataFrame()
    return matches, players
