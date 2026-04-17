"""Push ML artifacts + predictions to Supabase. Gracefully no-ops if creds absent."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv


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


def push_single_prediction(pred: dict) -> None:
    c = _client()
    if not c:
        return
    name_to_id = push_teams([pred["home"], pred["away"]])
    # Create a placeholder match row
    match = c.table("matches").insert({
        "match_date": __import__("datetime").date.today().isoformat(),
        "home_id": name_to_id.get(pred["home"]),
        "away_id": name_to_id.get(pred["away"]),
        "stage": pred.get("stage"),
        "neutral": pred.get("neutral", True),
    }).execute().data[0]
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


def push_insights(rows: list[dict]) -> None:
    c = _client()
    if not c:
        return
    c.table("insights").insert(rows).execute()
