"""FIFA World Cup 2026 host venues — stadium metadata + ground conditions.

Loads ``data/raw/wc2026_venues.csv`` (stadium, city, country, lat/lon, elevation,
capacity, roof type, surface, timezone, climate note). These feed the
weather-aware match prediction page.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
VENUES_CSV = ROOT / "data" / "raw" / "wc2026_venues.csv"
SCHEDULE_CSV = ROOT / "data" / "raw" / "wc2026_schedule.csv"


@lru_cache(maxsize=1)
def load_venues() -> pd.DataFrame:
    if not VENUES_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(VENUES_CSV)
    df["label"] = df["venue"] + " — " + df["city"] + ", " + df["country"]
    return df


def venue_names() -> list[str]:
    df = load_venues()
    return df["label"].tolist() if not df.empty else []


def get_venue(label: str) -> dict:
    """Look up a venue by its display ``label`` (or bare stadium name)."""
    df = load_venues()
    if df.empty:
        return {}
    hit = df[df["label"] == label]
    if hit.empty:
        hit = df[df["venue"] == label]
    return hit.iloc[0].to_dict() if not hit.empty else {}


@lru_cache(maxsize=1)
def load_schedule() -> pd.DataFrame:
    """Curated 2026 fixture scaffold (confirmed openers, knockout slots, final).

    ``TBD`` team entries are placeholders pending the draw — the prediction page
    pre-fills the known host/venue/date and lets the user choose the rest.
    """
    if not SCHEDULE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(SCHEDULE_CSV)


def label_for_stadium(stadium: str) -> str | None:
    """Map a bare stadium name (as used in the schedule) to its venue label."""
    df = load_venues()
    if df.empty:
        return None
    hit = df[df["venue"] == stadium]
    return hit.iloc[0]["label"] if not hit.empty else None


def altitude_band(elevation_m: float) -> str:
    if elevation_m >= 2000:
        return "extreme altitude"
    if elevation_m >= 1200:
        return "high altitude"
    if elevation_m >= 500:
        return "moderate altitude"
    return "sea level"
