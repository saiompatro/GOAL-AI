"""Read-only Supabase helpers for the Streamlit app."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[3]


def _client():
    load_dotenv(ROOT / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
    except Exception:
        return None
    return create_client(url, key)


def is_configured() -> bool:
    return _client() is not None


def teams() -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()
    rows = client.table("teams").select("id,name,code,confederation,created_at").order("name").execute().data
    return pd.DataFrame(rows or [])


def players() -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()
    rows = client.table("players").select("*").order("overall", desc=True).limit(1000).execute().data
    if not rows:
        return pd.DataFrame()

    player_df = pd.DataFrame(rows)
    team_df = teams()
    if not team_df.empty and "team_id" in player_df.columns:
        player_df = player_df.merge(
            team_df[["id", "name"]].rename(columns={"id": "team_id", "name": "team"}),
            on="team_id",
            how="left",
        )

    player_df = player_df.rename(columns={"name": "player_name", "position": "primary_position"})
    if "attrs" in player_df.columns:
        attrs = pd.json_normalize(player_df["attrs"].apply(lambda value: value or {}))
        player_df = pd.concat([player_df.drop(columns=["attrs"]), attrs], axis=1)
    return player_df


def model_runs(limit: int = 10) -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()
    rows = (
        client.table("model_runs")
        .select("version,algo,metrics,notes,created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    return pd.DataFrame(rows or [])


def recent_predictions(limit: int = 25) -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()

    predictions_rows = (
        client.table("predictions")
        .select("id,match_id,model_version,p_home,p_draw,p_away,confidence,created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    if not predictions_rows:
        return pd.DataFrame()

    prediction_df = pd.DataFrame(predictions_rows)
    match_ids = prediction_df["match_id"].dropna().unique().tolist()
    if not match_ids:
        return prediction_df

    matches_rows = (
        client.table("matches")
        .select("id,match_date,home_id,away_id,stage,neutral")
        .in_("id", match_ids)
        .execute()
        .data
    )
    match_df = pd.DataFrame(matches_rows or [])
    team_df = teams()
    if match_df.empty or team_df.empty:
        return prediction_df

    name_by_id = team_df.set_index("id")["name"].to_dict()
    match_df["home"] = match_df["home_id"].map(name_by_id)
    match_df["away"] = match_df["away_id"].map(name_by_id)
    merged = prediction_df.merge(match_df, left_on="match_id", right_on="id", how="left", suffixes=("", "_match"))
    return merged.drop(columns=[col for col in ["id_match", "home_id", "away_id"] if col in merged.columns])
