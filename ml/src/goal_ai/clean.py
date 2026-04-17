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
    df["neutral"] = df.get("neutral", False).astype(bool)
    df["tournament"] = df.get("tournament", "Friendly").fillna("Friendly")
    df["result"] = df.apply(
        lambda r: "H" if r.home_score > r.away_score else ("A" if r.home_score < r.away_score else "D"),
        axis=1,
    )
    df = df.sort_values("date").reset_index(drop=True)
    return df


def aggregate_players(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate FIFA player rows into per-nationality squad-strength features."""
    if df.empty:
        return pd.DataFrame(columns=["team", "squad_mean", "top11_mean", "star3_mean",
                                      "att_mean", "mid_mean", "def_mean"])
    df = df.copy()
    df["nationality_name"] = df["nationality_name"].map(_canon)
    pos = df["player_positions"].fillna("").str.split(",").str[0].str.strip()
    df["pos_group"] = pos.map(
        lambda p: "GK" if p == "GK" else ("DF" if p in {"CB","LB","RB","LWB","RWB"} else ("MF" if p in {"CDM","CM","CAM","LM","RM"} else "FW"))
    )
    out = []
    for team, g in df.groupby("nationality_name"):
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
        })
    return pd.DataFrame(out).fillna(0.0)
