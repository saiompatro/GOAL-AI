"""Ingestion helpers for the vendored jfjelstul/worldcup repository."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def default_repo_path(raw_dir: str | Path) -> Path:
    return Path(raw_dir) / "external_repos" / "jfjelstul_worldcup"


def repo_available(raw_dir: str | Path) -> bool:
    repo = default_repo_path(raw_dir)
    return (repo / "data-csv" / "matches.csv").exists()


def load_matches(repo_dir: str | Path) -> pd.DataFrame:
    """Return jfjelstul World Cup matches in GOAL AI's canonical schema."""
    repo_dir = Path(repo_dir)
    path = repo_dir / "data-csv" / "matches.csv"
    df = pd.read_csv(path)
    df = df[df["tournament_name"].str.contains("Men's World Cup", na=False)].copy()
    out = pd.DataFrame(
        {
            "date": df["match_date"],
            "home_team": df["home_team_name"],
            "away_team": df["away_team_name"],
            "home_score": df["home_team_score"],
            "away_score": df["away_team_score"],
            "tournament": df["tournament_name"],
            "city": df["city_name"],
            "country": df["country_name"],
        }
    )
    out["neutral"] = ~(
        out["country"].astype(str).eq(out["home_team"].astype(str))
        | out["country"].astype(str).eq(out["away_team"].astype(str))
    )
    return out


def load_players(repo_dir: str | Path) -> pd.DataFrame:
    """Return the 10,401-player roster with derived FIFA-style columns.

    jfjelstul is a historical roster/event database, not a ratings feed. The
    derived `overall` field is intentionally conservative and experience-based
    so existing squad-strength features can consume the roster without pretending
    it is a FIFA video-game rating.
    """
    repo_dir = Path(repo_dir)
    players = pd.read_csv(repo_dir / "data-csv" / "players.csv")
    squads = pd.read_csv(repo_dir / "data-csv" / "squads.csv")
    appearances = pd.read_csv(repo_dir / "data-csv" / "player_appearances.csv")
    goals = pd.read_csv(repo_dir / "data-csv" / "goals.csv")
    bookings = pd.read_csv(repo_dir / "data-csv" / "bookings.csv")

    mens_tournaments = squads["tournament_name"].str.contains("Men's World Cup", na=False)
    squads = squads[mens_tournaments].copy()

    latest_squad = (
        squads.assign(year=squads["tournament_name"].str.extract(r"(\d{4})").astype(float))
        .sort_values(["player_id", "year"])
        .groupby("player_id", as_index=False)
        .tail(1)
        .set_index("player_id")
    )
    app_counts = appearances.groupby("player_id").size().rename("appearances")
    starter_counts = appearances.groupby("player_id")["starter"].sum().rename("starts")
    goal_counts = goals.groupby("player_id").size().rename("goals")
    card_counts = bookings.groupby("player_id")["sending_off"].sum().rename("sendings_off")

    out = players.copy()
    out["player_name"] = (
        out["given_name"].fillna("").astype(str).str.strip()
        + " "
        + out["family_name"].fillna("").astype(str).str.strip()
    ).str.strip()
    out.loc[out["player_name"].eq(""), "player_name"] = out["family_name"]
    out["short_name"] = out["player_name"]
    out["nationality_name"] = out["player_id"].map(latest_squad["team_name"]).fillna("Unknown")
    out["club_name"] = "World Cup roster"
    position_fallback = pd.Series(
        np.select(
            [out["goal_keeper"].eq(1), out["defender"].eq(1), out["midfielder"].eq(1), out["forward"].eq(1)],
            ["GK", "DF", "MF", "FW"],
            default="MF",
        ),
        index=out.index,
    )
    out["player_positions"] = out["player_id"].map(latest_squad["position_code"]).fillna(position_fallback)
    out["appearances"] = out["player_id"].map(app_counts).fillna(0).astype(float)
    out["starts"] = out["player_id"].map(starter_counts).fillna(0).astype(float)
    out["goals"] = out["player_id"].map(goal_counts).fillna(0).astype(float)
    out["sendings_off"] = out["player_id"].map(card_counts).fillna(0).astype(float)
    out["birth_date"] = pd.to_datetime(out["birth_date"], errors="coerce")
    out["age"] = ((pd.Timestamp("2026-06-11") - out["birth_date"]).dt.days / 365.25).clip(16, 55)

    experience = np.log1p(out["appearances"]) * 4.0 + np.log1p(out["starts"]) * 2.0
    attacking = np.log1p(out["goals"]) * 3.0 + out["forward"].astype(float) * 3.0
    discipline = out["sendings_off"].clip(0, 3) * 1.5
    out["overall"] = (62.0 + experience + attacking - discipline).clip(45, 88)
    out["potential"] = out["overall"]
    out["pace"] = (out["overall"] + np.where(out["forward"].eq(1), 4, 0)).clip(40, 90)
    out["shooting"] = (out["overall"] + np.where(out["forward"].eq(1), 5, -2)).clip(35, 90)
    out["passing"] = (out["overall"] + np.where(out["midfielder"].eq(1), 4, 0)).clip(35, 90)
    out["dribbling"] = (out["overall"] + np.where(out["forward"].eq(1) | out["midfielder"].eq(1), 2, -1)).clip(35, 90)
    out["defending"] = (out["overall"] + np.where(out["defender"].eq(1) | out["goal_keeper"].eq(1), 5, -5)).clip(30, 90)
    out["physic"] = (out["overall"] + np.where(out["defender"].eq(1), 3, 0)).clip(35, 90)
    out["height_cm"] = 0
    out["weight_kg"] = 0
    out["preferred_foot"] = ""
    out["international_reputation"] = out["count_tournaments"].clip(0, 5)
    out["value_eur"] = 0
    out["wage_eur"] = 0
    return out[
        [
            "player_name",
            "short_name",
            "nationality_name",
            "club_name",
            "player_positions",
            "overall",
            "potential",
            "age",
            "height_cm",
            "weight_kg",
            "preferred_foot",
            "international_reputation",
            "value_eur",
            "wage_eur",
            "pace",
            "shooting",
            "passing",
            "dribbling",
            "defending",
            "physic",
            "appearances",
            "starts",
            "goals",
            "sendings_off",
            "player_id",
            "player_wikipedia_link",
        ]
    ]


def load_raw(raw_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    repo = default_repo_path(raw_dir)
    return load_matches(repo), load_players(repo)
