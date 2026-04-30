"""Read-only Firebase helpers for the Streamlit app."""
from __future__ import annotations

import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[3]


def _client():
    load_dotenv(ROOT / ".env")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        key_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        if not key_json:
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
    except Exception:
        return None


def is_configured() -> bool:
    return _client() is not None


def teams() -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()
    docs = client.collection("teams").stream()
    rows = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        rows.append(d)
    return pd.DataFrame(rows).sort_values("name") if rows else pd.DataFrame()


def players() -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()
    docs = client.collection("players").order_by("overall", direction="DESCENDING").limit(1000).stream()
    rows = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        rows.append(d)
    if not rows:
        return pd.DataFrame()

    player_df = pd.DataFrame(rows)
    # Firebase players now have team_name saved directly, but we can also merge team_df if needed.
    player_df = player_df.rename(columns={"name": "player_name", "position": "primary_position", "team_name": "team"})

    if "attrs" in player_df.columns:
        attrs = pd.json_normalize(player_df["attrs"].apply(lambda value: value or {}))
        player_df = pd.concat([player_df.drop(columns=["attrs"]), attrs], axis=1)
    return player_df


def model_runs(limit: int = 10) -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()
    docs = client.collection("model_runs").order_by("created_at", direction="DESCENDING").limit(limit).stream()
    rows = []
    for doc in docs:
        d = doc.to_dict()
        rows.append(d)
    return pd.DataFrame(rows)


def recent_predictions(limit: int = 25) -> pd.DataFrame:
    client = _client()
    if client is None:
        return pd.DataFrame()

    docs = client.collection("predictions").order_by("created_at", direction="DESCENDING").limit(limit).stream()
    predictions_rows = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        predictions_rows.append(d)

    if not predictions_rows:
        return pd.DataFrame()

    prediction_df = pd.DataFrame(predictions_rows)
    match_ids = prediction_df["match_id"].dropna().unique().tolist()
    if not match_ids:
        return prediction_df

    matches_rows = []
    # Firestore in-queries are limited to 10 items, better to fetch one by one or in batches of 10
    from firebase_admin.firestore import FieldFilter
    for i in range(0, len(match_ids), 10):
        batch_ids = match_ids[i:i+10]
        # In Firestore we can't query by id easily using in_, we get the document directly
        for m_id in batch_ids:
            m_doc = client.collection("matches").document(m_id).get()
            if m_doc.exists:
                m_dict = m_doc.to_dict()
                m_dict["id"] = m_doc.id
                matches_rows.append(m_dict)

    match_df = pd.DataFrame(matches_rows)
    team_df = teams()
    if match_df.empty or team_df.empty:
        return prediction_df

    name_by_id = team_df.set_index("id")["name"].to_dict()
    match_df["home"] = match_df["home_id"].map(name_by_id)
    match_df["away"] = match_df["away_id"].map(name_by_id)
    merged = prediction_df.merge(match_df, left_on="match_id", right_on="id", how="left", suffixes=("", "_match"))
    return merged.drop(columns=[col for col in ["id_match", "home_id", "away_id"] if col in merged.columns])
