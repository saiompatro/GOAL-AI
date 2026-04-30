"""Dataset ingestion.

Downloads via the Kaggle API if available; otherwise expects CSVs already present
in the raw data directory. Synthesizes a small dataset if nothing is found so the
pipeline can still run end-to-end in a demo environment.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.request import urlretrieve
import numpy as np
import pandas as pd

from .ingest_jfjelstul import load_raw as load_jfjelstul_raw
from .ingest_jfjelstul import repo_available as jfjelstul_available

KAGGLE_DATASETS = {
    "results": "martj42/international-football-results-from-1872-to-2017",
    "players": "stefanoleone992/fifa-23-complete-player-dataset",
    # Extended match features: Elo, form, player-level data, updated Dec 2025
    "features_ext": "lchikry/international-football-match-features-and-statistics",
}

PUBLIC_DATASET_URLS = {
    "results": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
    "players": "https://gist.githubusercontent.com/Imagio/5623926ff3dbe74b1d2d9d38e58e06c9/raw/football_players.csv",
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _try_public_download(raw_dir: Path) -> None:
    targets = {
        raw_dir / "results.csv": PUBLIC_DATASET_URLS["results"],
        raw_dir / "fifa_players.csv": PUBLIC_DATASET_URLS["players"],
    }
    for target, url in targets.items():
        if target.exists():
            continue
        try:
            print(f"[ingest] Downloading public dataset: {target.name}")
            urlretrieve(url, target)
            if "gist.githubusercontent.com" in url:
                print(
                    f"[ingest] WARNING: {target.name} downloaded from an unverified Gist URL "
                    f"(SHA-256: {_sha256(target)[:16]}…). "
                    "Verify the hash against a trusted source before using in production."
                )
        except Exception as e:
            print(f"[ingest] Public download skipped for {target.name}: {e}")


def _synthesize(raw_dir: Path) -> None:
    """Generate a small synthetic dataset so the pipeline runs without Kaggle access."""
    print("[ingest] No real data found — synthesizing demo dataset.")
    rng = np.random.default_rng(42)
    teams = [
        "Brazil","Argentina","France","Germany","Spain","England","Portugal",
        "Netherlands","Belgium","Croatia","Morocco","Japan","South Korea",
        "United States","Mexico","Uruguay","Italy","Denmark","Switzerland","Poland",
    ]
    strengths = {t: rng.normal(0, 1) for t in teams}
    rows = []
    start = pd.Timestamp("2008-01-01")
    for i in range(6000):
        h, a = rng.choice(teams, size=2, replace=False)
        mu_h = 1.4 + 0.6 * (strengths[h] - strengths[a]) + 0.25  # home advantage
        mu_a = 1.2 + 0.6 * (strengths[a] - strengths[h])
        hs = int(rng.poisson(max(0.2, mu_h)))
        as_ = int(rng.poisson(max(0.2, mu_a)))
        rows.append({
            "date": (start + pd.Timedelta(days=i)).strftime("%Y-%m-%d"),
            "home_team": h,
            "away_team": a,
            "home_score": hs,
            "away_score": as_,
            "tournament": rng.choice(["Friendly","FIFA World Cup qualification","UEFA Euro qualification","FIFA World Cup","Copa America"]),
            "city": "N/A",
            "country": h,
            "neutral": bool(rng.random() < 0.15),
        })
    df = pd.DataFrame(rows)
    df.to_csv(raw_dir / "results.csv", index=False)

    # Synthetic player ratings
    prows = []
    for t in teams:
        base = 70 + 10 * (strengths[t] + 1)
        for i in range(30):
            pos = rng.choice(["GK","DF","MF","FW"], p=[0.1,0.35,0.35,0.2])
            overall = int(np.clip(rng.normal(base, 5), 55, 94))
            prows.append({
                "short_name": f"{t[:3]}_P{i}",
                "long_name": f"{t} Player {i}",
                "nationality_name": t,
                "player_positions": pos,
                "overall": overall,
                "pace": int(np.clip(rng.normal(overall, 6), 40, 99)),
                "shooting": int(np.clip(rng.normal(overall, 6), 40, 99)),
                "passing": int(np.clip(rng.normal(overall, 6), 40, 99)),
                "defending": int(np.clip(rng.normal(overall, 6), 40, 99)),
            })
    pd.DataFrame(prows).to_csv(raw_dir / "fifa_players.csv", index=False)


def load_raw(raw_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    results_path = raw_dir / "results.csv"
    players_path = raw_dir / "fifa_players.csv"

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

    if not results_path.exists() or not players_path.exists():
        _try_kaggle_download(raw_dir)

    if not results_path.exists() or not players_path.exists():
        _try_public_download(raw_dir)

    if not results_path.exists():
        _synthesize(raw_dir)

    matches = pd.read_csv(raw_dir / "results.csv")
    # Some FIFA dumps are named differently; try a few
    if not players_path.exists():
        for cand in raw_dir.glob("*player*.csv"):
            players_path = cand
            break
    players = pd.read_csv(players_path) if players_path.exists() else pd.DataFrame()
    return matches, players
