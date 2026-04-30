"""Push ML artifacts + predictions to Firebase. Gracefully no-ops if creds absent."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd


def _client():
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    # Firebase relies on FIREBASE_SERVICE_ACCOUNT_KEY or GOOGLE_APPLICATION_CREDENTIALS
    # We will assume GOOGLE_APPLICATION_CREDENTIALS or initialized via a key json.
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        # Check if we have FIREBASE_SERVICE_ACCOUNT_KEY as string
        key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        if not key_json:
            print("[firebase] creds missing — skipping push")
            return None
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            if cred_path:
                cred = credentials.Certificate(cred_path)
            else:
                cred_dict = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY"))
                cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"[firebase] client missing or error: {e}")
        return None


def push_run(version: str, algo: str, metrics: dict, notes: str = "") -> None:
    c = _client()
    if not c:
        return
    from firebase_admin import firestore

    c.collection("model_runs").add({
        "version": version, "algo": algo, "metrics": metrics, "notes": notes,
        "created_at": firestore.SERVER_TIMESTAMP
    })


def push_teams(teams: list[str]) -> dict[str, str]:
    """Upsert teams, return name→id map. Returns {} if offline."""
    c = _client()
    if not c:
        return {}
    name_to_id = {}
    for t in teams:
        # Search if exists
        docs = c.collection("teams").where("name", "==", t).limit(1).stream()
        found = False
        for doc in docs:
            name_to_id[t] = doc.id
            found = True
        if not found:
            _, ref = c.collection("teams").add({"name": t})
            name_to_id[t] = ref.id
    return name_to_id


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
            docs = c.collection("players").where("team_id", "==", team_id).stream()
            for doc in docs:
                doc.reference.delete()

    batch = c.batch()
    mapping = {}
    for r in trimmed.itertuples(index=False):
        team_id = name_to_id.get(r.team)
        if not team_id:
            continue
        
        doc_ref = c.collection("players").document()
        batch.set(doc_ref, {
            "team_id": team_id,
            "team_name": r.team,
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
        mapping[(r.team, r.player_name)] = doc_ref.id
    
    # Commit batch
    batch.commit()
    return mapping


def push_single_prediction(pred: dict) -> None:
    c = _client()
    if not c:
        return
    name_to_id = push_teams([pred["home"], pred["away"]])
    
    from firebase_admin import firestore
    
    _, match_ref = c.collection("matches").add({
        "match_date": __import__("datetime").date.today().isoformat(),
        "home_id": name_to_id.get(pred["home"]),
        "away_id": name_to_id.get(pred["away"]),
        "stage": pred.get("stage"),
        "neutral": pred.get("neutral", True),
    })

    c.collection("predictions").add({
        "match_id": match_ref.id,
        "model_version": pred["model_version"],
        "p_home": pred["p_home"],
        "p_draw": pred["p_draw"],
        "p_away": pred["p_away"],
        "confidence": pred["confidence"],
        "shap": pred["drivers"],
        "created_at": firestore.SERVER_TIMESTAMP,
    })


def push_batch_predictions(preds: list[dict]) -> None:
    for p in preds:
        push_single_prediction(p)


def push_insights(rows: list[dict], replace_entity_type: str | None = None) -> None:
    c = _client()
    if not c:
        return
    if replace_entity_type:
        docs = c.collection("insights").where("entity_type", "==", replace_entity_type).stream()
        for doc in docs:
            doc.reference.delete()
    
    batch = c.batch()
    for row in rows:
        doc_ref = c.collection("insights").document()
        batch.set(doc_ref, row)
    batch.commit()
