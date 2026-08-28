"""Fetch additional open FIFA / international-football data (no API keys needed).

Pulls from public, no-auth sources and drops them under ``data/raw/``. Run:

    python ml/scripts/fetch_fifa_data.py

Sources requiring credentials (Kaggle, X/Twitter, Reddit, football-data.org,
API-Football) are documented in ``docs/research.md`` and intentionally not
auto-fetched here — add your token there and extend ``EXTRA_SOURCES``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
EXTERNAL = RAW / "external"

# (url, destination relative to data/raw) — public, no auth.
SOURCES: list[tuple[str, str]] = [
    # martj42 — international results 1872→present (the canonical open dataset)
    ("https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
     "results.csv"),
    ("https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv",
     "goalscorers.csv"),
    ("https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv",
     "shootouts.csv"),
    ("https://raw.githubusercontent.com/martj42/international_results/master/former_names.csv",
     "former_names.csv"),
    # StatsBomb open data — index of free event-data competitions (incl. World Cups)
    ("https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json",
     "external/statsbomb_competitions.json"),
    # openfootball — public-domain 2026 World Cup fixtures/schedule (feeds build_schedule.py)
    ("https://raw.githubusercontent.com/openfootball/world-cup.json/master/2026/worldcup.json",
     "openfootball_wc2026.json"),
]


def fetch(url: str, dest: Path) -> tuple[bool, str]:
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return True, f"{len(r.content):,} bytes"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def main() -> int:
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    ok = 0
    print("Fetching open FIFA / international-football data…\n")
    for url, rel in SOURCES:
        dest = RAW / rel
        success, info = fetch(url, dest)
        flag = "OK " if success else "FAIL"
        print(f"[{flag}] {rel:42s} {info}")
        ok += int(success)
    print(f"\n{ok}/{len(SOURCES)} sources fetched into {RAW}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
