"""Bootstrap local artifacts for a fresh GOAL AI clone."""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ML = ROOT / "ml"
ART = ML / "artifacts"


REQUIRED = [
    "features.parquet",
    "metrics.json",
    "players.parquet",
    "player_team_aggregates.parquet",
    "simulation.parquet",
]


def main() -> int:
    missing = [name for name in REQUIRED if not (ART / name).exists()]
    if not missing:
        print("Artifacts already present.")
        return 0

    print("Missing artifacts:")
    for name in missing:
        print(f"  - {name}")
    print("\nRun `python ml/scripts/run_pipeline.py` to rebuild them from data/raw.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
