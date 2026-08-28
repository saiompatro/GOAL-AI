"""Validate that raw project data follows the real-football-only policy."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from goal_ai.data_policy import (  # noqa: E402
    DataPolicyError,
    approved_raw_path,
    enforce_real_player_source,
    is_rejected_source_name,
    looks_like_video_game_player_dataset,
)

PLAYER_CANDIDATE_NAMES = {
    "players.csv",
    "transfermarkt_players.csv",
    "fbref_players.csv",
    "worldcup_squads.csv",
}


def _csv_columns(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    raw = root / "data" / "raw"

    if not raw.exists():
        errors.append(f"Missing raw data directory: {raw}")
        return errors, warnings

    for path in raw.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if is_rejected_source_name(path):
            errors.append(f"Rejected source name: {rel}")
            continue
        if path.suffix.lower() == ".csv":
            try:
                columns = _csv_columns(path)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Could not inspect {rel}: {exc}")
                continue
            if path.name in PLAYER_CANDIDATE_NAMES:
                try:
                    enforce_real_player_source(path, columns)
                except DataPolicyError as exc:
                    errors.append(str(exc))
            elif looks_like_video_game_player_dataset(columns):
                errors.append(f"EA/SOFIFA-style rating columns detected in raw CSV: {rel}")
        if not approved_raw_path(path):
            warnings.append(f"Raw file is not in the approved source allow-list: {rel}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    errors, warnings = validate(ROOT)
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, indent=2))
    else:
        if warnings:
            print("Warnings:")
            for item in warnings:
                print(f"  - {item}")
        if errors:
            print("Errors:")
            for item in errors:
                print(f"  - {item}")
        if not errors:
            print("Real data source validation passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
