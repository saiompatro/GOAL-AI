"""Betting-odds feature extraction.

Integrates bookmaker market odds from adamgbor/club-football-match-data-2000-2025
(Kaggle) as three calibrated implied-probability features.

Integration point: call `load_odds` and pass the result into `build_features` via
the `feats` concat in features.py (lines 140-143). The three columns
`implied_home_win`, `implied_draw`, `implied_away_win` are then available as
features alongside Elo and form signals.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


# Expected column names in the raw odds CSV (adjust if source schema differs)
_ODD_COLS = {
    "home": ["B365H", "BWH", "IWH", "PSH", "WHH", "VCH"],
    "draw": ["B365D", "BWD", "IWD", "PSD", "WHD", "VCD"],
    "away": ["B365A", "BWA", "IWA", "PSA", "WHA", "VCA"],
}


def _first_col(df: pd.DataFrame, candidates: list[str]) -> pd.Series | None:
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
    return None


def implied_probs(df: pd.DataFrame) -> pd.DataFrame:
    """Convert raw bookmaker odds to implied probabilities (overround-normalised).

    Args:
        df: Raw odds DataFrame with at least one column from each of the
            home / draw / away candidate lists.

    Returns:
        DataFrame with columns ``implied_home_win``, ``implied_draw``,
        ``implied_away_win`` (NaN where odds are missing).
    """
    oh = _first_col(df, _ODD_COLS["home"])
    od = _first_col(df, _ODD_COLS["draw"])
    oa = _first_col(df, _ODD_COLS["away"])

    if oh is None or od is None or oa is None:
        n = len(df)
        return pd.DataFrame({
            "implied_home_win": [float("nan")] * n,
            "implied_draw": [float("nan")] * n,
            "implied_away_win": [float("nan")] * n,
        })

    raw_h = 1.0 / oh
    raw_d = 1.0 / od
    raw_a = 1.0 / oa
    total = raw_h + raw_d + raw_a

    return pd.DataFrame({
        "implied_home_win": raw_h / total,
        "implied_draw": raw_d / total,
        "implied_away_win": raw_a / total,
    })


def load_odds(raw_dir: str | Path) -> pd.DataFrame:
    """Load and merge all odds CSVs found under *raw_dir*.

    Looks for files matching ``*odds*.csv`` or the Kaggle dataset slug output
    ``club-football-match-data-*.csv``. Returns an empty DataFrame if nothing
    is found so the pipeline degrades gracefully.

    The returned DataFrame has columns:
        date, home_team, away_team, implied_home_win, implied_draw, implied_away_win
    """
    raw_dir = Path(raw_dir)
    patterns = ["*odds*.csv", "club-football-match-data*.csv", "*match_data*.csv"]
    files: list[Path] = []
    for pat in patterns:
        files.extend(raw_dir.glob(pat))

    if not files:
        print("[odds] No odds files found — odds features will be NaN")
        return pd.DataFrame(columns=["date", "home_team", "away_team",
                                     "implied_home_win", "implied_draw", "implied_away_win"])

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            # Normalise date column
            date_col = next((c for c in df.columns if c.lower() in ("date", "match_date")), None)
            home_col = next((c for c in df.columns if c.lower() in ("home_team", "hometeam", "home")), None)
            away_col = next((c for c in df.columns if c.lower() in ("away_team", "awayteam", "away")), None)
            if not all([date_col, home_col, away_col]):
                continue
            probs = implied_probs(df)
            sub = pd.DataFrame({
                "date": pd.to_datetime(df[date_col], errors="coerce"),
                "home_team": df[home_col].astype(str).str.strip(),
                "away_team": df[away_col].astype(str).str.strip(),
            })
            frames.append(pd.concat([sub, probs], axis=1))
        except Exception as e:
            print(f"[odds] Skipping {f.name}: {e}")

    if not frames:
        return pd.DataFrame(columns=["date", "home_team", "away_team",
                                     "implied_home_win", "implied_draw", "implied_away_win"])

    return pd.concat(frames, ignore_index=True).dropna(subset=["date"])
