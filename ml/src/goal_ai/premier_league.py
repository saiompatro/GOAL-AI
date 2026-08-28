"""Reusable data and modelling helpers for the Premier League project lab.

The module deliberately keeps Streamlit out of the modelling layer so every
project can be tested from Python and reused in notebooks or scheduled jobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
import requests
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
PLAYER_VALUE_FEATURES = ["goals", "assists", "minutes", "age"]
PLAYER_VALUE_REQUIRED = ["player", "position", *PLAYER_VALUE_FEATURES, "market_value_eur"]
SCOUTING_FEATURES = [
    "goals",
    "assists",
    "passes",
    "shots",
    "dribbles",
    "defensive_actions",
]
MATCH_MODEL_FEATURES = [
    "home_goals_for",
    "home_goals_against",
    "home_form_points",
    "away_goals_for",
    "away_goals_against",
    "away_form_points",
    "home_advantage",
]
OPTIONAL_MATCH_FEATURES = [
    "home_shots_for",
    "home_shots_against",
    "away_shots_for",
    "away_shots_against",
    "home_possession",
    "away_possession",
]


class FootballDataError(RuntimeError):
    """Raised when football-data.org cannot return usable data."""


@dataclass
class TrainedModel:
    model: Any
    metrics: dict[str, float]
    predictions: pd.DataFrame
    features: list[str]


class FootballDataClient:
    """Small requests-based client for football-data.org's Premier League API."""

    def __init__(self, api_key: str, timeout: int = 30) -> None:
        if not api_key.strip():
            raise ValueError("A football-data.org API key is required.")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": api_key.strip()})

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"{FOOTBALL_DATA_BASE_URL}/{path.lstrip('/')}",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = getattr(exc.response, "text", "") if exc.response is not None else str(exc)
            raise FootballDataError(f"football-data.org request failed: {detail[:240]}") from exc
        payload = response.json()
        if not isinstance(payload, dict):
            raise FootballDataError("football-data.org returned an unexpected response.")
        return payload

    def premier_league_matches(self, seasons: Iterable[int]) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for season in seasons:
            payload = self._get("competitions/PL/matches", {"season": int(season), "status": "FINISHED"})
            frame = parse_football_data_matches(payload, int(season))
            if not frame.empty:
                frames.append(frame)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def premier_league_squads(self) -> pd.DataFrame:
        payload = self._get("competitions/PL/teams")
        rows: list[dict[str, Any]] = []
        for team in payload.get("teams", []):
            for player in team.get("squad", []) or []:
                rows.append({
                    "player": player.get("name"),
                    "position": player.get("position"),
                    "date_of_birth": player.get("dateOfBirth"),
                    "nationality": player.get("nationality"),
                    "team": team.get("name"),
                })
        return pd.DataFrame(rows)


def parse_football_data_matches(payload: dict[str, Any], season: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for match in payload.get("matches", []):
        full_time = match.get("score", {}).get("fullTime", {}) or {}
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")
        if home_goals is None or away_goals is None:
            continue
        rows.append({
            "date": match.get("utcDate"),
            "season": season,
            "matchday": match.get("matchday"),
            "home_team": match.get("homeTeam", {}).get("name"),
            "away_team": match.get("awayTeam", {}).get("name"),
            "home_goals": int(home_goals),
            "away_goals": int(away_goals),
        })
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
        frame = frame.dropna(subset=["date", "home_team", "away_team"]).sort_values("date")
    return frame.reset_index(drop=True)


def _validate_columns(data: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def clean_player_data(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize common column aliases used by public football CSV datasets."""
    aliases = {
        "name": "player",
        "player_name": "player",
        "minutes_played": "minutes",
        "value_eur": "market_value_eur",
        "market_value": "market_value_eur",
        "passing": "passes",
        "key_passes": "passes",
        "tackles_interceptions": "defensive_actions",
    }
    out = data.copy()
    out.columns = [str(column).strip().lower().replace(" ", "_") for column in out.columns]
    out = out.rename(columns={old: new for old, new in aliases.items() if old in out.columns and new not in out.columns})
    for column in set(PLAYER_VALUE_FEATURES + SCOUTING_FEATURES + ["market_value_eur"]):
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def train_transfer_value_model(data: pd.DataFrame, random_state: int = 42) -> TrainedModel:
    data = clean_player_data(data)
    _validate_columns(data, PLAYER_VALUE_REQUIRED)
    usable = data.dropna(subset=PLAYER_VALUE_REQUIRED).copy()
    if len(usable) < 12:
        raise ValueError("At least 12 complete player rows are required to train and evaluate the model.")

    preprocessor = ColumnTransformer([
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), PLAYER_VALUE_FEATURES),
        ("position", OneHotEncoder(handle_unknown="ignore"), ["position"]),
    ])
    pipeline = Pipeline([
        ("prepare", preprocessor),
        ("model", LinearRegression()),
    ])
    train, test = train_test_split(usable, test_size=0.25, random_state=random_state)
    pipeline.fit(train[[*PLAYER_VALUE_FEATURES, "position"]], train["market_value_eur"])
    predicted = np.maximum(0.0, pipeline.predict(test[[*PLAYER_VALUE_FEATURES, "position"]]))
    comparison = test[["player", "market_value_eur"]].copy()
    comparison["predicted_value_eur"] = predicted
    comparison["difference_eur"] = comparison["predicted_value_eur"] - comparison["market_value_eur"]
    metrics = {
        "mae_eur": float(mean_absolute_error(comparison["market_value_eur"], predicted)),
        "r2": float(r2_score(comparison["market_value_eur"], predicted)) if len(test) > 1 else 0.0,
        "training_rows": float(len(train)),
        "test_rows": float(len(test)),
    }
    return TrainedModel(pipeline, metrics, comparison.sort_values("market_value_eur"), [*PLAYER_VALUE_FEATURES, "position"])


def predict_transfer_value(trained: TrainedModel, player: dict[str, Any]) -> float:
    row = pd.DataFrame([player])
    return max(0.0, float(trained.model.predict(row[trained.features])[0]))


def build_match_features(matches: pd.DataFrame, form_window: int = 5) -> pd.DataFrame:
    """Create strictly pre-match rolling features to avoid result leakage."""
    required = ["date", "home_team", "away_team", "home_goals", "away_goals"]
    _validate_columns(matches, required)
    ordered = matches.copy()
    ordered["date"] = pd.to_datetime(ordered["date"], utc=True, errors="coerce")
    ordered = ordered.dropna(subset=required).sort_values("date").reset_index(drop=True)
    history: dict[str, list[dict[str, float]]] = {}
    rows: list[dict[str, Any]] = []
    has_shots = {"home_shots", "away_shots"}.issubset(ordered.columns)
    has_possession = {"home_possession", "away_possession"}.issubset(ordered.columns)

    def recent(team: str) -> dict[str, float]:
        games = history.get(team, [])[-form_window:]
        if not games:
            return {key: 0.0 for key in ["goals_for", "goals_against", "points", "shots_for", "shots_against", "possession"]}
        return {
            key: float(np.nanmean([game[key] for game in games]))
            for key in games[0]
        }

    for _, match in ordered.iterrows():
        home, away = str(match["home_team"]), str(match["away_team"])
        home_recent = recent(home)
        away_recent = recent(away)
        home_goals, away_goals = float(match["home_goals"]), float(match["away_goals"])
        result = "Home win" if home_goals > away_goals else "Away win" if away_goals > home_goals else "Draw"
        rows.append({
            **match.to_dict(),
            "home_goals_for": home_recent["goals_for"],
            "home_goals_against": home_recent["goals_against"],
            "home_form_points": home_recent["points"],
            "away_goals_for": away_recent["goals_for"],
            "away_goals_against": away_recent["goals_against"],
            "away_form_points": away_recent["points"],
            "home_advantage": 1.0,
            "result": result,
        })
        if has_shots:
            rows[-1].update({
                "home_shots_for": home_recent["shots_for"],
                "home_shots_against": home_recent["shots_against"],
                "away_shots_for": away_recent["shots_for"],
                "away_shots_against": away_recent["shots_against"],
            })
        if has_possession:
            rows[-1].update({
                "home_possession": home_recent["possession"],
                "away_possession": away_recent["possession"],
            })
        home_result_points = 3.0 if home_goals > away_goals else 1.0 if home_goals == away_goals else 0.0
        away_result_points = 3.0 if away_goals > home_goals else 1.0 if home_goals == away_goals else 0.0
        home_history = {"goals_for": home_goals, "goals_against": away_goals, "points": home_result_points}
        away_history = {"goals_for": away_goals, "goals_against": home_goals, "points": away_result_points}
        if has_shots:
            home_history.update({"shots_for": float(match["home_shots"]), "shots_against": float(match["away_shots"])})
            away_history.update({"shots_for": float(match["away_shots"]), "shots_against": float(match["home_shots"])})
        else:
            home_history.update({"shots_for": 0.0, "shots_against": 0.0})
            away_history.update({"shots_for": 0.0, "shots_against": 0.0})
        home_history["possession"] = float(match["home_possession"]) if has_possession else 0.0
        away_history["possession"] = float(match["away_possession"]) if has_possession else 0.0
        history.setdefault(home, []).append(home_history)
        history.setdefault(away, []).append(away_history)
    return pd.DataFrame(rows)


def train_match_outcome_model(matches: pd.DataFrame, random_state: int = 42) -> TrainedModel:
    featured = build_match_features(matches)
    if len(featured) < 40:
        raise ValueError("At least 40 completed matches are required to train and evaluate the model.")
    split = max(1, int(len(featured) * 0.8))
    train, test = featured.iloc[:split], featured.iloc[split:]
    features = MATCH_MODEL_FEATURES + [column for column in OPTIONAL_MATCH_FEATURES if column in featured.columns]
    model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(
            n_estimators=350,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            random_state=random_state,
        )),
    ])
    model.fit(train[features], train["result"])
    predicted = model.predict(test[features])
    comparison = test[["date", "home_team", "away_team", "result"]].copy()
    comparison["prediction"] = predicted
    comparison["correct"] = comparison["result"] == comparison["prediction"]
    return TrainedModel(
        model,
        {"accuracy": float(accuracy_score(comparison["result"], predicted)), "training_rows": float(len(train)), "test_rows": float(len(test))},
        comparison,
        features,
    )


def next_match_features(
    featured: pd.DataFrame,
    home_team: str,
    away_team: str,
    features: list[str] | None = None,
) -> pd.DataFrame:
    """Build a next-fixture row from each team's most recent pre-match feature state."""
    if featured.empty:
        raise ValueError("No match history is available.")

    def team_state(team: str) -> tuple[float, float, float]:
        games = featured[(featured["home_team"] == team) | (featured["away_team"] == team)].tail(5)
        values: list[tuple[float, float, float]] = []
        for _, game in games.iterrows():
            if game["home_team"] == team:
                scored, conceded = float(game["home_goals"]), float(game["away_goals"])
            else:
                scored, conceded = float(game["away_goals"]), float(game["home_goals"])
            points = 3.0 if scored > conceded else 1.0 if scored == conceded else 0.0
            values.append((scored, conceded, points))
        return tuple(np.asarray(values).mean(axis=0)) if values else (0.0, 0.0, 0.0)  # type: ignore[return-value]

    home = team_state(home_team)
    away = team_state(away_team)
    row = dict(zip(MATCH_MODEL_FEATURES, [*home, *away, 1.0]))
    requested = features or MATCH_MODEL_FEATURES

    def recent_optional(team: str, home_column: str, away_column: str) -> float:
        games = featured[(featured["home_team"] == team) | (featured["away_team"] == team)].tail(5)
        values = [game[home_column] if game["home_team"] == team else game[away_column] for _, game in games.iterrows()]
        return float(pd.to_numeric(pd.Series(values), errors="coerce").mean()) if values else 0.0

    optional_sources = {
        "home_shots_for": (home_team, "home_shots", "away_shots"),
        "home_shots_against": (home_team, "away_shots", "home_shots"),
        "away_shots_for": (away_team, "home_shots", "away_shots"),
        "away_shots_against": (away_team, "away_shots", "home_shots"),
        "home_possession": (home_team, "home_possession", "away_possession"),
        "away_possession": (away_team, "home_possession", "away_possession"),
    }
    for feature in requested:
        if feature in optional_sources:
            team, home_column, away_column = optional_sources[feature]
            row[feature] = recent_optional(team, home_column, away_column)
    return pd.DataFrame([row])


def match_probabilities(trained: TrainedModel, feature_row: pd.DataFrame) -> pd.Series:
    probabilities = trained.model.predict_proba(feature_row[trained.features])[0]
    classes = trained.model.classes_
    return pd.Series(probabilities, index=classes).sort_values(ascending=False)


def scout_similar_players(data: pd.DataFrame, player: str, neighbours: int = 6) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = clean_player_data(data)
    _validate_columns(data, ["player", *SCOUTING_FEATURES])
    usable = data.dropna(subset=["player", *SCOUTING_FEATURES]).drop_duplicates("player").reset_index(drop=True)
    if len(usable) < 8:
        raise ValueError("At least 8 complete player rows are required for scouting.")
    if player not in usable["player"].values:
        raise ValueError(f"Player not found: {player}")

    scaled = StandardScaler().fit_transform(usable[SCOUTING_FEATURES])
    index = int(usable.index[usable["player"] == player][0])
    count = min(neighbours + 1, len(usable))
    finder = NearestNeighbors(n_neighbors=count, metric="euclidean").fit(scaled)
    distances, indices = finder.kneighbors(scaled[[index]])
    matches = usable.iloc[indices[0]].copy()
    matches["similarity"] = 100.0 / (1.0 + distances[0])
    matches = matches[matches["player"] != player].head(neighbours)

    cluster_count = min(6, max(2, int(np.sqrt(len(usable) / 2))))
    clusters = KMeans(n_clusters=cluster_count, n_init=20, random_state=42).fit_predict(scaled)
    clustered = usable[["player"] + (["team", "position"] if {"team", "position"}.issubset(usable.columns) else [])].copy()
    clustered["style_cluster"] = clusters + 1
    clustered["is_selected"] = clustered["player"].eq(player)
    return matches.reset_index(drop=True), clustered.sort_values(["style_cluster", "player"])
