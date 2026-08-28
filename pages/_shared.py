"""Shared data loaders + helpers for the GOAL AI pages."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "ml" / "artifacts"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SRC = ROOT / "ml" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from goal_ai.world_cup import canonical_team, qualified_teams_present, is_qualified_2026
except Exception:  # pragma: no cover - defensive
    def canonical_team(x):  # type: ignore
        return x

    def qualified_teams_present(present):  # type: ignore
        return sorted(present) if present else []

    def is_qualified_2026(x):  # type: ignore
        return True

_INVALID = {"", "n/a", "na", "not applicable", "unknown", "none", "null"}
ELIGIBLE_PLAYER_FILES = [
    PROCESSED / "wc2026_matchday_players.parquet",
    PROCESSED / "wc2026_matchday_players.csv",
    PROCESSED / "fifa_2026_squads.parquet",
    PROCESSED / "fifa_2026_squads.csv",
    RAW / "wc2026_matchday_players.csv",
    RAW / "fifa_2026_squads.csv",
]
MATCHDAY_ROLE_VALUES = {
    "starter",
    "starting",
    "starting_xi",
    "starting xi",
    "xi",
    "sub",
    "subs",
    "substitute",
    "substitutes",
    "bench",
}
SQUAD_STATUS_VALUES = {
    "called_up",
    "eligible",
    "final",
    "final_squad",
    "official",
    "official_squad",
    "preliminary",
    "preliminary_squad",
    "provisional",
    "provisional_squad",
    "squad",
}
PLAYER_EMPTY_MESSAGE = (
    "No eligible FIFA 2026 player pool is loaded yet. Add a real file at "
    "`data/raw/wc2026_matchday_players.csv` for matchday starting XI + substitutes, "
    "or another approved 2026 file with `matchday_role`, starter-substitute, or official squad fields. "
    "Historical World Cup rosters are intentionally not used for player analysis."
)


def _first_col(df: pd.DataFrame, candidates: list[str], default: object = "") -> pd.Series:
    for column in candidates:
        if column in df.columns:
            return df[column]
    return pd.Series([default] * len(df), index=df.index)


def _read_player_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _player_source_signature() -> tuple[str, int, int] | None:
    path = next((candidate for candidate in ELIGIBLE_PLAYER_FILES if candidate.exists()), None)
    if path is None:
        return None
    stat = path.stat()
    return str(path), stat.st_mtime_ns, stat.st_size


def _eligible_rows(df: pd.DataFrame) -> pd.Series:
    role = _first_col(df, ["matchday_role", "role", "lineup_role", "player_role"], "").astype("string").str.strip().str.lower()
    if role.notna().any() and role.fillna("").ne("").any():
        return role.isin(MATCHDAY_ROLE_VALUES)

    squad_status = _first_col(df, ["squad_status", "status", "selection_status"], "").astype("string").str.strip().str.lower()
    if squad_status.notna().any() and squad_status.fillna("").ne("").any():
        return squad_status.isin(SQUAD_STATUS_VALUES)

    starter = _first_col(df, ["is_starter", "starter", "starting_xi"], False).astype(str).str.lower().isin({"true", "1", "yes", "y"})
    sub = _first_col(df, ["is_substitute", "substitute", "bench"], False).astype(str).str.lower().isin({"true", "1", "yes", "y"})
    if starter.any() or sub.any():
        return starter | sub

    return pd.Series([False] * len(df), index=df.index)


def _normalize_eligible_players(df: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(column).strip().lower() for column in df.columns]
    if df.empty:
        return pd.DataFrame()
    df = df[_eligible_rows(df)].copy()
    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame(index=df.index)
    out["player_name"] = _first_col(df, ["player_name", "name", "full_name", "long_name"]).astype(str).str.strip()
    out["short_name"] = _first_col(df, ["short_name", "known_as", "player_name", "name"], "").astype(str).str.strip()
    out["team"] = _first_col(df, ["team", "national_team", "nationality_name", "nationality", "country"]).map(canonical_team)
    out["club_name"] = _first_col(df, ["club", "club_name", "current_club", "club_team"], "World Cup squad").astype(str).str.strip()
    out["positions"] = _first_col(df, ["position", "positions", "player_positions"], "").astype(str).str.strip()
    out["primary_position"] = out["positions"].str.split(",").str[0].str.strip().replace("", "MF")
    out["matchday_role"] = _first_col(df, ["matchday_role", "role", "lineup_role", "player_role", "squad_status", "status"], "eligible").astype(str).str.strip()

    numeric_map = {
        "overall": ["derived_strength", "overall", "rating"],
        "potential": ["derived_potential", "potential"],
        "age": ["age"],
        "appearances": ["appearances", "caps", "matches", "apps"],
        "starts": ["starts"],
        "goals": ["goals", "international_goals"],
        "assists": ["assists"],
        "minutes": ["minutes", "minutes_played"],
        "sendings_off": ["sendings_off", "red_cards"],
        "value_eur": ["value_eur", "market_value_eur", "market_value_in_eur"],
        "wage_eur": ["wage_eur", "wage"],
    }
    for target, candidates in numeric_map.items():
        out[target] = pd.to_numeric(_first_col(df, candidates, 0.0), errors="coerce").fillna(0.0).astype(float)

    for column in ATTR_COLS:
        out[column] = (
            pd.to_numeric(_first_col(df, [column, f"derived_{column}_index"], 0.0), errors="coerce")
            .fillna(0.0)
            .astype(float)
        )

    missing_strength = out["overall"].eq(0)
    if missing_strength.any():
        out.loc[missing_strength, "overall"] = (
            55
            + out.loc[missing_strength, "appearances"].clip(0, 50) * 0.4
            + out.loc[missing_strength, "starts"].clip(0, 50) * 0.25
            + out.loc[missing_strength, "goals"].clip(0, 20) * 0.9
            + out.loc[missing_strength, "minutes"].clip(0, 4500) / 450
        ).clip(35, 92)
    out["potential"] = out["potential"].where(out["potential"].gt(0), out["overall"])

    missing_profile = out[ATTR_COLS].sum(axis=1).eq(0)
    for column in ATTR_COLS:
        out.loc[missing_profile, column] = out.loc[missing_profile, "overall"]

    out["source_file"] = str(source_path.relative_to(ROOT))
    out = out.dropna(subset=["team", "player_name"])
    out = out[
        out["team"].astype(str).str.strip().ne("")
        & out["player_name"].astype(str).str.strip().ne("")
        & ~out["team"].astype(str).str.lower().isin(_INVALID)
        & ~out["player_name"].astype(str).str.lower().isin(_INVALID)
    ]
    return out.drop_duplicates(subset=["team", "player_name"], keep="first").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _load_players_from_source(path_str: str, _mtime_ns: int, _size: int) -> pd.DataFrame:
    path = Path(path_str)
    df = _normalize_eligible_players(_read_player_file(path), path)
    for col in ("team", "player_name", "primary_position"):
        if col in df.columns:
            vals = df[col].astype("string").str.strip()
            df = df[vals.notna() & ~vals.str.lower().isin(_INVALID)]
    if "team" in df.columns:
        df = df.assign(team=df["team"].apply(canonical_team))
    return df


def load_players() -> pd.DataFrame:
    signature = _player_source_signature()
    if signature is None:
        return pd.DataFrame()
    return _load_players_from_source(*signature)


@st.cache_data(show_spinner=False)
def load_features() -> pd.DataFrame:
    path = ART / "features.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def _load_team_agg_from_source(path_str: str, mtime_ns: int, size: int) -> pd.DataFrame:
    players = _load_players_from_source(path_str, mtime_ns, size)
    if players.empty:
        return pd.DataFrame()
    rows = []
    for team, group in players.groupby("team"):
        top = group.sort_values("overall", ascending=False)
        pos = group.assign(pos_group=group["primary_position"].replace("", "MF").str.upper().str[:1])
        rows.append({
            "team": team,
            "squad_mean": group["overall"].mean(),
            "top11_mean": top.head(11)["overall"].mean(),
            "star3_mean": top.head(3)["overall"].mean(),
            "att_mean": pos[pos["pos_group"].eq("F")]["overall"].mean(),
            "mid_mean": pos[pos["pos_group"].eq("M")]["overall"].mean(),
            "def_mean": pos[pos["pos_group"].isin(["D", "G"])]["overall"].mean(),
        })
    return pd.DataFrame(rows).fillna(0.0)


def load_team_agg() -> pd.DataFrame:
    signature = _player_source_signature()
    if signature is None:
        return pd.DataFrame()
    return _load_team_agg_from_source(*signature)


def player_team_list(players: pd.DataFrame, qualified_only: bool = True) -> list[str]:
    if players.empty or "team" not in players.columns:
        return []
    names = players["team"].dropna().unique().tolist()
    if qualified_only:
        present = qualified_teams_present(set(names))
        if present:
            return present
    return sorted(set(names))


def team_match_list(feats: pd.DataFrame, qualified_only: bool = True) -> list[str]:
    if feats.empty:
        return []
    present = set(feats["home_team"].apply(canonical_team)) | set(feats["away_team"].apply(canonical_team))
    if qualified_only:
        q = qualified_teams_present(present)
        if q:
            return q
    return sorted(present)


def index_of(options: list[str], target: str, default: int = 0) -> int:
    return options.index(target) if target in options else default


PROFILE_INDEX_COLS = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]
ATTR_COLS = PROFILE_INDEX_COLS

PROFILE_INDEX_LABELS = {
    "pace": "Tempo index",
    "shooting": "Scoring index",
    "passing": "Distribution index",
    "dribbling": "Ball-carrying index",
    "defending": "Defensive index",
    "physic": "Physical index",
}

REAL_DATA_NOTE = (
    "Player profiles are derived from real roster/event data in the World Cup database "
    "and approved real-football sources. They are not EA Sports FC or SOFIFA ratings."
)


def profile_label(column: str) -> str:
    return PROFILE_INDEX_LABELS.get(column, column.replace("_", " ").title())
