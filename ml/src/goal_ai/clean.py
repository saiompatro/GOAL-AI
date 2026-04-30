"""Cleaning and normalization."""
from __future__ import annotations

import pandas as pd


TEAM_ALIASES = {
    "USA": "United States",
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "Ivory Coast": "Côte d'Ivoire",
    "Czech Republic": "Czechia",
}


def _canon(name: str) -> str:
    if not isinstance(name, str):
        return name
    return TEAM_ALIASES.get(name.strip(), name.strip())


def clean_matches(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_team", "away_team", "home_score", "away_score"])
    df["home_team"] = df["home_team"].map(_canon)
    df["away_team"] = df["away_team"].map(_canon)
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["neutral"] = df["neutral"].astype(bool) if "neutral" in df.columns else False
    df["tournament"] = df.get("tournament", "Friendly").fillna("Friendly")
    df["result"] = df.apply(
        lambda r: "H" if r.home_score > r.away_score else ("A" if r.home_score < r.away_score else "D"),
        axis=1,
    )
    df = df.sort_values("date").reset_index(drop=True)
    return df


def _first_existing(df: pd.DataFrame, candidates: list[str], default: str = "") -> pd.Series:
    for candidate in candidates:
        if candidate in df.columns:
            return df[candidate]
    return pd.Series([default] * len(df), index=df.index)


def _numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _primary_position(raw_value: str) -> str:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return "MF"
    return raw_value.split(",")[0].strip()


def _pos_group(position: str) -> str:
    if position == "GK":
        return "GK"
    if position in {"CB", "LB", "RB", "LWB", "RWB", "DF"}:
        return "DF"
    if position in {"CDM", "CM", "CAM", "LM", "RM", "MF"}:
        return "MF"
    return "FW"


def clean_players(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize detailed player rows from FIFA-style sources."""
    if df.empty:
        return pd.DataFrame(columns=[
            "player_name", "short_name", "team", "club_name", "positions", "primary_position", "pos_group",
            "overall", "potential", "age", "height_cm", "weight_kg", "preferred_foot",
            "international_reputation", "value_eur", "wage_eur", "pace", "shooting", "passing",
            "dribbling", "defending", "physic",
        ])

    df = df.copy()
    df.columns = [str(column).strip().lower() for column in df.columns]
    out = pd.DataFrame(index=df.index)
    out["player_name"] = _first_existing(df, ["long_name", "name", "player_name", "full_name"]).astype(str).str.strip()
    out["short_name"] = _first_existing(df, ["short_name", "known_as", "player_short_name"]).astype(str).str.strip()
    if "player_id" in df.columns:
        out["player_id"] = df["player_id"].astype(str)
    if "player_wikipedia_link" in df.columns:
        out["player_wikipedia_link"] = df["player_wikipedia_link"].astype(str)
    out["team"] = _first_existing(df, ["nationality_name", "nationality", "country", "team"]).map(_canon)
    out["club_name"] = _first_existing(df, ["club_name", "club", "club_team", "team_name"]).astype(str).str.strip()
    out["positions"] = _first_existing(df, ["player_positions", "position", "positions"]).astype(str).str.strip()
    out["primary_position"] = out["positions"].map(_primary_position)
    out["pos_group"] = out["primary_position"].map(_pos_group)

    out["pace"] = _numeric(_first_existing(df, ["pace"]), 0)
    out["shooting"] = _numeric(_first_existing(df, ["shooting"]), 0)
    out["passing"] = _numeric(_first_existing(df, ["passing"]), 0)
    out["dribbling"] = _numeric(_first_existing(df, ["dribbling"]), 0)
    out["defending"] = _numeric(_first_existing(df, ["defending"]), 0)
    physic_raw = _first_existing(df, ["physic", "physicality"])
    if physic_raw.astype(str).str.len().gt(0).any():
        out["physic"] = _numeric(physic_raw, 0)
    else:
        physical_parts = [
            _numeric(_first_existing(df, ["strength"]), 0),
            _numeric(_first_existing(df, ["stamina"]), 0),
            _numeric(_first_existing(df, ["jumping"]), 0),
        ]
        out["physic"] = pd.concat(physical_parts, axis=1).mean(axis=1)

    raw_overall = pd.to_numeric(_first_existing(df, ["overall", "rating"]), errors="coerce")
    derived_overall = (
        pd.concat(
            [out["pace"], out["shooting"], out["passing"], out["dribbling"], out["defending"], out["physic"]],
            axis=1,
        )
        .replace(0, pd.NA)
        .mean(axis=1)
        .fillna(0)
    )
    out["overall"] = raw_overall.fillna(derived_overall).astype(float)

    potential_raw = pd.to_numeric(_first_existing(df, ["potential"]), errors="coerce")
    out["potential"] = potential_raw.fillna(out["overall"]).astype(float)
    out["age"] = _numeric(_first_existing(df, ["age"]), 0)
    out["height_cm"] = _numeric(_first_existing(df, ["height_cm", "height"]), 0)
    out["weight_kg"] = _numeric(_first_existing(df, ["weight_kg", "weight"]), 0)
    out["preferred_foot"] = _first_existing(df, ["preferred_foot", "foot"]).astype(str).str.strip()
    out["international_reputation"] = _numeric(_first_existing(df, ["international_reputation"]), 0)
    out["value_eur"] = _numeric(_first_existing(df, ["value_eur", "value"]), 0)
    out["wage_eur"] = _numeric(_first_existing(df, ["wage_eur", "wage", "salary"]), 0)
    for optional in ["appearances", "starts", "goals", "sendings_off"]:
        if optional in df.columns:
            out[optional] = _numeric(df[optional], 0)

    out = out.dropna(subset=["team", "player_name"])
    out = out[(out["team"].astype(str).str.len() > 0) & (out["player_name"].astype(str).str.len() > 0)]
    out = out[out["overall"] > 0]
    out = out.sort_values(["team", "overall", "potential"], ascending=[True, False, False])
    dedupe_key = ["player_id"] if "player_id" in out.columns else ["team", "player_name"]
    out = out.drop_duplicates(subset=dedupe_key, keep="first").reset_index(drop=True)
    return out


def aggregate_players(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate FIFA player rows into per-nationality squad-strength features."""
    if df.empty:
        return pd.DataFrame(columns=[
            "team", "squad_mean", "top11_mean", "star3_mean", "att_mean", "mid_mean", "def_mean",
            "potential_mean", "potential_top11_mean", "value_mean_eur", "value_top11_eur",
            "wage_mean_eur", "age_mean", "height_mean", "international_reputation_mean",
            "dribbling_mean", "physic_mean",
        ])
    df = df.copy()
    out = []
    for team, g in df.groupby("team"):
        top = g.sort_values("overall", ascending=False)
        top11 = top.head(11)["overall"].mean()
        star3 = top.head(3)["overall"].mean()
        att = g[g["pos_group"] == "FW"]["overall"].mean()
        mid = g[g["pos_group"] == "MF"]["overall"].mean()
        dfn = g[g["pos_group"] == "DF"]["overall"].mean()
        out.append({
            "team": team,
            "squad_mean": g["overall"].mean(),
            "top11_mean": top11,
            "star3_mean": star3,
            "att_mean": att,
            "mid_mean": mid,
            "def_mean": dfn,
            "potential_mean": g["potential"].mean(),
            "potential_top11_mean": top.head(11)["potential"].mean(),
            "value_mean_eur": g["value_eur"].mean(),
            "value_top11_eur": top.head(11)["value_eur"].mean(),
            "wage_mean_eur": g["wage_eur"].mean(),
            "age_mean": g["age"].mean(),
            "height_mean": g["height_cm"].mean(),
            "international_reputation_mean": g["international_reputation"].mean(),
            "dribbling_mean": g["dribbling"].mean(),
            "physic_mean": g["physic"].mean(),
        })
    return pd.DataFrame(out).fillna(0.0)
