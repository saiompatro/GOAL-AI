"""Push ML artifacts + predictions to Supabase. Gracefully no-ops if creds absent."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd


def _client():
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        print("[supabase] creds missing — skipping push")
        return None
    try:
        from supabase import create_client
    except Exception as e:
        print(f"[supabase] client missing: {e}")
        return None
    return create_client(url, key)


def push_run(version: str, algo: str, metrics: dict, notes: str = "") -> None:
    c = _client()
    if not c:
        return
    c.table("model_runs").insert({
        "version": version, "algo": algo, "metrics": metrics, "notes": notes
    }).execute()


def push_teams(teams: list[str]) -> dict[str, str]:
    """Upsert teams, return name→id map. Returns {} if offline."""
    c = _client()
    if not c:
        return {}
    rows = [{"name": t} for t in teams]
    c.table("teams").upsert(rows, on_conflict="name").execute()
    res = c.table("teams").select("id,name").execute()
    return {r["name"]: r["id"] for r in res.data}


def push_players(players: pd.DataFrame, limit_per_team: int = 18) -> dict[tuple[str, str], str]:
    """Replace player rows for the given teams, return (team, player_name) -> id."""
    c = _client()
    if not c or players.empty:
        return {}

    trimmed = (
        players.sort_values(["team", "overall", "potential"], ascending=[True, False, False])
        .groupby("team", group_keys=False)
        .head(limit_per_team)
        .reset_index(drop=True)
    )
    name_to_id = push_teams(trimmed["team"].dropna().unique().tolist())

    for team_name in trimmed["team"].dropna().unique():
        team_id = name_to_id.get(team_name)
        if team_id:
            c.table("players").delete().eq("team_id", team_id).execute()

    rows = []
    for r in trimmed.itertuples(index=False):
        team_id = name_to_id.get(r.team)
        if not team_id:
            continue
        rows.append({
            "team_id": team_id,
            "name": r.player_name,
            "position": r.primary_position,
            "overall": int(r.overall),
            "club_name": getattr(r, "club_name", None),
            "age": int(getattr(r, "age", 0) or 0),
            "potential": int(getattr(r, "potential", 0) or 0),
            "preferred_foot": getattr(r, "preferred_foot", None),
            "value_eur": float(getattr(r, "value_eur", 0.0) or 0.0),
            "wage_eur": float(getattr(r, "wage_eur", 0.0) or 0.0),
            "attrs": {
                "pace": int(getattr(r, "pace", 0) or 0),
                "shooting": int(getattr(r, "shooting", 0) or 0),
                "passing": int(getattr(r, "passing", 0) or 0),
                "dribbling": int(getattr(r, "dribbling", 0) or 0),
                "defending": int(getattr(r, "defending", 0) or 0),
                "physic": int(getattr(r, "physic", 0) or 0),
                "height_cm": float(getattr(r, "height_cm", 0.0) or 0.0),
                "weight_kg": float(getattr(r, "weight_kg", 0.0) or 0.0),
                "international_reputation": float(getattr(r, "international_reputation", 0.0) or 0.0),
            },
        })

    if rows:
        c.table("players").insert(rows).execute()

    res = c.table("players").select("id,name,team_id,teams(name)").execute()
    mapping: dict[tuple[str, str], str] = {}
    for row in res.data:
        team_name = row.get("teams", {}).get("name") if isinstance(row.get("teams"), dict) else None
        player_name = row.get("name")
        player_id = row.get("id")
        if team_name and player_name and player_id:
            mapping[(team_name, player_name)] = player_id
    return mapping


def push_single_prediction(pred: dict) -> None:
    c = _client()
    if not c:
        return
    name_to_id = push_teams([pred["home"], pred["away"]])
    # Create a placeholder match row
    result = c.table("matches").insert({
        "match_date": __import__("datetime").date.today().isoformat(),
        "home_id": name_to_id.get(pred["home"]),
        "away_id": name_to_id.get(pred["away"]),
        "stage": pred.get("stage"),
        "neutral": pred.get("neutral", True),
    }).execute()
    if not result.data:
        print("[supabase] insert returned no data — skipping prediction push")
        return
    match = result.data[0]
    c.table("predictions").insert({
        "match_id": match["id"],
        "model_version": pred["model_version"],
        "p_home": pred["p_home"],
        "p_draw": pred["p_draw"],
        "p_away": pred["p_away"],
        "confidence": pred["confidence"],
        "shap": pred["drivers"],
    }).execute()


def push_batch_predictions(preds: list[dict]) -> None:
    for p in preds:
        push_single_prediction(p)


def push_insights(rows: list[dict], replace_entity_type: str | None = None) -> None:
    c = _client()
    if not c:
        return
    if replace_entity_type:
        c.table("insights").delete().eq("entity_type", replace_entity_type).execute()
    c.table("insights").insert(rows).execute()
