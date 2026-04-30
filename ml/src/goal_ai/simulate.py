"""Monte Carlo tournament simulation for the 48-team 2026 format."""
from __future__ import annotations

import itertools
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROUND_COLUMNS = ["team", "p_win", "p_final", "p_semi", "p_quarter", "p_groupexit"]


def load_2026_groups(raw_dir: str | Path) -> dict[str, list[str]]:
    """Load 2026 group teams from the mirrored reference repositories."""
    raw_dir = Path(raw_dir)
    candidates = [
        raw_dir / "external_repos" / "zvizdo_fifa-wc-2026-simulation" / "data" / "wc_2026_teams.json",
        raw_dir / "external_repos" / "PoolJinez_WORLDCUP-Tournament-2026" / "data" / "grupos_2026.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "groups" in data:
            return {
                group: [team["name"] for team in teams]
                for group, teams in data["groups"].items()
            }
        return {
            group.replace("Grupo ", ""): [team["Team"] for team in teams]
            for group, teams in data.items()
        }
    raise FileNotFoundError("No 2026 group source found under data/raw/external_repos.")


def group_fixtures(groups: dict[str, list[str]]) -> pd.DataFrame:
    rows = []
    for group, teams in groups.items():
        for home, away in itertools.combinations(teams, 2):
            rows.append({"group": group, "home_team": home, "away_team": away, "stage": "group"})
    return pd.DataFrame(rows)


def _team_strengths(fixtures_2026: pd.DataFrame, artifacts_dir: Path | None = None) -> dict[str, dict[str, float]]:
    teams = sorted(set(fixtures_2026["home_team"]) | set(fixtures_2026["away_team"]))
    defaults = {team: {"elo": 1500.0, "gf": 1.25, "ga": 1.25} for team in teams}
    if artifacts_dir is None:
        return defaults
    features_path = artifacts_dir / "features.parquet"
    if not features_path.exists():
        return defaults
    feats = pd.read_parquet(features_path)
    for team in teams:
        rows = feats[(feats["home_team"].eq(team)) | (feats["away_team"].eq(team))]
        if rows.empty:
            continue
        last = rows.tail(1).iloc[0]
        if last["home_team"] == team:
            elo = float(last.get("elo_home_pre", 1500.0))
            gf = float(last.get("home_gf_10", 1.25) or 1.25)
            ga = float(last.get("home_ga_10", 1.25) or 1.25)
        else:
            elo = float(last.get("elo_away_pre", 1500.0))
            gf = float(last.get("away_gf_10", 1.25) or 1.25)
            ga = float(last.get("away_ga_10", 1.25) or 1.25)
        defaults[team] = {"elo": elo, "gf": max(0.35, gf), "ga": max(0.35, ga)}
    return defaults


def _expected_goals(home: str, away: str, strengths: dict[str, dict[str, float]]) -> tuple[float, float]:
    h = strengths[home]
    a = strengths[away]
    elo_delta = (h["elo"] - a["elo"]) / 400.0
    base_home = 1.28 + 0.34 * elo_delta + 0.18 * (h["gf"] - a["ga"])
    base_away = 1.18 - 0.34 * elo_delta + 0.18 * (a["gf"] - h["ga"])
    return float(np.clip(base_home, 0.2, 4.5)), float(np.clip(base_away, 0.2, 4.5))


def _sample_match(
    home: str,
    away: str,
    strengths: dict[str, dict[str, float]],
    rng: np.random.Generator,
    knockout: bool = False,
) -> tuple[int, int, str]:
    lam_home, lam_away = _expected_goals(home, away, strengths)
    hg = int(rng.poisson(lam_home))
    ag = int(rng.poisson(lam_away))
    if hg > ag:
        return hg, ag, home
    if ag > hg:
        return hg, ag, away
    if not knockout:
        return hg, ag, "draw"
    p_home = 1.0 / (1.0 + 10 ** ((strengths[away]["elo"] - strengths[home]["elo"]) / 400.0))
    return hg, ag, home if rng.random() < p_home else away


def _group_table(teams: list[str]) -> dict[str, dict[str, int]]:
    return {team: {"pts": 0, "gf": 0, "ga": 0, "gd": 0, "wins": 0} for team in teams}


def _rank_table(table: dict[str, dict[str, int]], rng: np.random.Generator) -> list[str]:
    return sorted(
        table,
        key=lambda team: (
            table[team]["pts"],
            table[team]["gd"],
            table[team]["gf"],
            table[team]["wins"],
            rng.random(),
        ),
        reverse=True,
    )


def _simulate_once(
    groups: dict[str, list[str]],
    strengths: dict[str, dict[str, float]],
    rng: np.random.Generator,
) -> dict[str, str]:
    stage = {team: "groupexit" for teams in groups.values() for team in teams}
    third_place: list[tuple[str, dict[str, int]]] = []
    qualifiers: list[str] = []

    for teams in groups.values():
        table = _group_table(teams)
        for home, away in itertools.combinations(teams, 2):
            hg, ag, winner = _sample_match(home, away, strengths, rng)
            table[home]["gf"] += hg
            table[home]["ga"] += ag
            table[away]["gf"] += ag
            table[away]["ga"] += hg
            table[home]["gd"] = table[home]["gf"] - table[home]["ga"]
            table[away]["gd"] = table[away]["gf"] - table[away]["ga"]
            if winner == "draw":
                table[home]["pts"] += 1
                table[away]["pts"] += 1
            elif winner == home:
                table[home]["pts"] += 3
                table[home]["wins"] += 1
            else:
                table[away]["pts"] += 3
                table[away]["wins"] += 1
        ranked = _rank_table(table, rng)
        qualifiers.extend(ranked[:2])
        third_place.append((ranked[2], table[ranked[2]]))

    third_ranked = sorted(
        third_place,
        key=lambda item: (item[1]["pts"], item[1]["gd"], item[1]["gf"], item[1]["wins"], rng.random()),
        reverse=True,
    )
    qualifiers.extend([team for team, _ in third_ranked[:8]])

    bracket = qualifiers[:32]
    rng.shuffle(bracket)
    for team in bracket:
        stage[team] = "round32"

    current = bracket
    for label in ["round16", "quarter", "semi", "final"]:
        winners = []
        for home, away in zip(current[0::2], current[1::2]):
            _, _, winner = _sample_match(home, away, strengths, rng, knockout=True)
            winners.append(winner)
        for winner in winners:
            stage[winner] = label
        current = winners
    finalist_a, finalist_b = current
    _, _, champion = _sample_match(finalist_a, finalist_b, strengths, rng, knockout=True)
    stage[champion] = "win"
    return stage


def simulate_tournament(
    model: Any,
    fixtures_2026: pd.DataFrame,
    n: int = 100_000,
    random_state: int = 42,
    artifacts_dir: str | Path | None = None,
    strength_overrides: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Simulate a tournament and return round-reaching probabilities.

    `model` is accepted for the public contract; the current scoreline sampler
    uses precomputed Elo/form features from `artifacts_dir` when available.
    """
    if {"home_team", "away_team"} - set(fixtures_2026.columns):
        fixtures_2026 = fixtures_2026.rename(columns={"home": "home_team", "away": "away_team"})
    groups = {
        group: sorted(set(g["home_team"]) | set(g["away_team"]))
        for group, g in fixtures_2026.groupby(fixtures_2026.get("group", pd.Series(["A"] * len(fixtures_2026))))
    }
    strengths = _team_strengths(fixtures_2026, Path(artifacts_dir) if artifacts_dir else None)
    for team, elo_delta in (strength_overrides or {}).items():
        if team in strengths:
            strengths[team]["elo"] += float(elo_delta)
    rng = np.random.default_rng(random_state)
    counts = defaultdict(lambda: defaultdict(int))

    for _ in range(n):
        stages = _simulate_once(groups, strengths, rng)
        for team, reached in stages.items():
            if reached != "groupexit":
                counts[team]["advanced"] += 1
            if reached in {"quarter", "semi", "final", "win"}:
                counts[team]["quarter"] += 1
            if reached in {"semi", "final", "win"}:
                counts[team]["semi"] += 1
            if reached in {"final", "win"}:
                counts[team]["final"] += 1
            if reached == "win":
                counts[team]["win"] += 1

    teams = sorted(strengths)
    out = pd.DataFrame(
        {
            "team": teams,
            "p_win": [counts[t]["win"] / n for t in teams],
            "p_final": [counts[t]["final"] / n for t in teams],
            "p_semi": [counts[t]["semi"] / n for t in teams],
            "p_quarter": [counts[t]["quarter"] / n for t in teams],
            "p_groupexit": [1.0 - counts[t]["advanced"] / n for t in teams],
        }
    )
    return out[ROUND_COLUMNS].sort_values("p_win", ascending=False).reset_index(drop=True)


def build_baseline_simulation(
    raw_dir: str | Path,
    artifacts_dir: str | Path,
    n: int = 100_000,
    random_state: int = 42,
) -> pd.DataFrame:
    groups = load_2026_groups(raw_dir)
    fixtures = group_fixtures(groups)
    sim = simulate_tournament(
        model=None,
        fixtures_2026=fixtures,
        n=n,
        random_state=random_state,
        artifacts_dir=artifacts_dir,
    )
    out_path = Path(artifacts_dir) / "simulation.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sim.to_parquet(out_path, index=False)
    return sim
