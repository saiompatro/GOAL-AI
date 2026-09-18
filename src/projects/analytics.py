"""Isolated, cached models for each competition. No synthetic match features."""
from collections import defaultdict, deque
from functools import lru_cache
import threading

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, confusion_matrix, log_loss, mean_absolute_error, r2_score
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from projects import competitions as db
from projects import model_store
from projects.common import FEATURE_COLUMNS
from projects.player_scouting import _name_cluster

CLASSES = ["home_win", "draw", "away_win"]
_locks = {slug: threading.RLock() for slug in db.COMPETITIONS}


def version(slug, kind):
    path = db.DATA / f"{db.config(slug)['key']}_{kind}.csv"
    return tuple(p.stat().st_mtime_ns if p.exists() else 0 for p in (path, path.with_suffix(".json")))


def player_model(slug):
    with _locks[slug]:
        return _player_model(slug, version(slug, "players"))


@lru_cache(maxsize=12)
def _player_model(slug, revision):
    stored = model_store.load(slug, "valuation")
    if stored is not None:
        return stored
    df, provenance = db.players(slug)
    numeric = provenance.get("features", [c for c in FEATURE_COLUMNS if c in df])
    features = [*numeric, "position"]
    preprocess = ColumnTransformer([
        ("stats", StandardScaler(), numeric),
        ("position", OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False), ["position"]),
    ])
    model = make_pipeline(preprocess, LinearRegression())
    last = sorted(df.season.unique())[-1]
    train, test = df[df.season < last], df[df.season == last]
    if "valuation_date" in train:
        train = train[train.valuation_date < test.feature_cutoff.min()]
    if len(train) < 20 or len(test) < 5:
        raise ValueError("Not enough observed player seasons for chronological evaluation")
    model.fit(train[features], train.market_value_eur_m)
    predicted = np.maximum(0, model.predict(test[features]))
    metrics = {"mae_eur_m": round(mean_absolute_error(test.market_value_eur_m, predicted), 2),
               "r2": round(r2_score(test.market_value_eur_m, predicted), 3),
               "n_train": len(train), "n_test": len(test), "test_season": last,
               "train_end": str(train.season.max()), "method": "Linear regression",
               "baseline_mae_eur_m": round(mean_absolute_error(test.market_value_eur_m, np.full(len(test), train.market_value_eur_m.median())), 2),
               "features": features}
    evaluation = {"actual": test.market_value_eur_m.tolist(), "predicted": predicted.tolist()}
    served = clone(model).fit(df[features], df.market_value_eur_m)
    latest = db.latest_snapshot(df)
    return dict(model=served, holdout_model=model, numeric=numeric, features=features,
                metrics=metrics, evaluation=evaluation, df=df, latest=latest, provenance=provenance)


def scout_model(slug):
    with _locks[slug]:
        return _scout_model(slug, version(slug, "scouting"))


@lru_cache(maxsize=12)
def _scout_model(slug, revision):
    stored = model_store.load(slug, "scouting")
    if stored is not None:
        return stored
    df, provenance = db.scout_players(slug)
    latest = db.latest_snapshot(df)
    columns = provenance["features"]
    outfield = latest[(latest.position != "GK") & (latest.minutes >= 270)].reset_index(drop=True)
    rates = outfield[columns].div(outfield.minutes / 90, axis=0)
    scaler = StandardScaler()
    z = scaler.fit_transform(rates)
    count = min(6, len(outfield))
    cluster = KMeans(n_clusters=count, n_init=10, random_state=17).fit(z)
    def label(center):
        if len(columns) == 2:
            return "Low attacking output" if max(center) < 0 else ("Goal contribution" if center[0] > center[1] else "Assist contribution")
        return _name_cluster(center, [f"{c}_p90" for c in columns])
    names = {i: label(center) for i, center in enumerate(cluster.cluster_centers_)}
    # Cluster IDs remain unique even when multiple groups share a dominant trait.
    names = {i: f"{name} · {i + 1}" for i, name in names.items()}
    return dict(features=columns,
                df=df, latest=latest, provenance=provenance, outfield=outfield,
                rates=rates, z=z, cluster=cluster, names=names,
                neighbors=NearestNeighbors().fit(z))


def transfer(slug, name=None, custom=None):
    b = player_model(slug)
    if custom is not None:
        if not isinstance(custom, dict):
            raise ValueError("Enter a player statistics object")
        try:
            row = {c: float(custom[c]) for c in b["numeric"]}
        except (KeyError, TypeError, ValueError):
            raise ValueError("Enter every required numeric player statistic") from None
        if not all(np.isfinite(v) and v >= 0 for v in row.values()):
            raise ValueError("Statistics must be finite, nonnegative numbers")
        if not 14 <= row["age"] <= 50 or not 1 <= row["minutes"] <= 7000:
            raise ValueError("Use an age of 14–50 and minutes between 1 and 7,000")
        row["position"] = custom.get("position", "MF")
        if row["position"] not in ("GK", "DF", "MF", "FW"):
            raise ValueError("Choose a valid position")
        row.update(player="Custom player", team="What-if scenario", season="Custom")
        reference = None
    else:
        found = b["latest"][b["latest"].player == name]
        if found.empty:
            raise ValueError("Choose a player from this competition")
        row = found.iloc[0].to_dict()
        reference = float(row["market_value_eur_m"])
    estimator = b["holdout_model"] if custom is None else b["model"]
    value = max(0, float(estimator.predict(pd.DataFrame([row])[b["features"]])[0]))
    history = b["df"][b["df"].player == name].sort_values("season") if custom is None else pd.DataFrame()
    return dict(player=row["player"], team=row["team"], season=row["season"], position=row["position"],
                stats={c: float(row[c]) for c in b["numeric"]}, predicted_value=round(value, 1),
                valuation_date=row.get("valuation_date"), feature_cutoff=row.get("feature_cutoff"),
                prediction_basis="Held-out estimate" if custom is None else "Custom estimate · refitted model",
                reference_value=reference, difference=round(value - reference, 1) if reference is not None else None,
                metrics=b["metrics"], provenance=b["provenance"],
                history=history[["season", "goals", "assists", "minutes", "market_value_eur_m"]].to_dict("records") if not history.empty else [])


def scouting(slug, name, k=8, position=None):
    if not 1 <= k <= 20:
        raise ValueError("Number of matches must be between 1 and 20")
    b = scout_model(slug)
    df = b["outfield"]
    found = df.index[df.player == name]
    if len(found) == 0:
        raise ValueError("Choose an outfield player with at least 270 minutes")
    ix = int(found[0])
    distances, indices = b["neighbors"].kneighbors(b["z"][ix:ix+1], n_neighbors=len(df))
    def record(j):
        r = df.iloc[j]
        return dict(player=r.player, team=r.team, position=r.position, age=int(r.age),
                    cluster=b["names"][int(b["cluster"].labels_[j])],
                    season=r.season,
                    per90={c: round(float(b["rates"].iloc[j][c]), 2) for c in b["features"]})
    result = []
    for distance, j in zip(distances[0], indices[0]):
        if j == ix or (position and df.iloc[j].position != position):
            continue
        # A fixed distance transform: the score does not change when k changes.
        result.append({**record(j), "similarity": round(float(1 / (1 + distance / np.sqrt(len(b["features"])))), 3)})
        if len(result) == k:
            break
    groups = [{"name": b["names"][i], "size": int((b["cluster"].labels_ == i).sum())} for i in b["names"]]
    return {**record(ix), "matches": result, "clusters": groups, "features": b["features"], "provenance": b["provenance"]}


def build_match_features(df, window=6):
    """Only past observations enter training features; state includes the final game."""
    optional = [stat for stat in ("shots", "possession") if all(f"{side}_{stat}" in df and df[f"{side}_{stat}"].notna().any() for side in ("home", "away"))]
    history = defaultdict(lambda: deque(maxlen=window))
    rows = []

    def snapshot(team):
        games = history[team]
        out = {key: float(np.mean([g[key] for g in games])) if games else default
               for key, default in [("form", 1.0), ("scored", 1.3), ("conceded", 1.3)]}
        for key in optional:
            values = [g[key] for g in games if pd.notna(g.get(key))]
            out[key] = float(np.mean(values)) if values else np.nan
        return out

    def features(home, away, neutral):
        h, a = snapshot(home), snapshot(away)
        return {**{f"home_{k}": v for k, v in h.items()}, **{f"away_{k}": v for k, v in a.items()},
                "home_advantage": 0.0 if neutral else 1.0}

    df = df.sort_values("date", kind="stable")
    for r in df.to_dict("records"):
        home, away = r["home_team"], r["away_team"]
        hs, aws = r["home_score"], r["away_score"]
        target = 0 if hs > aws else 1 if hs == aws else 2
        feat = features(home, away, bool(r.get("neutral", 0)))
        if len(history[home]) >= 3 and len(history[away]) >= 3:
            rows.append({**r, **feat, "target": target})
        for team, side, gf, ga in ((home, "home", hs, aws), (away, "away", aws, hs)):
            history[team].append({"form": 3 if gf > ga else 1 if gf == ga else 0, "scored": gf, "conceded": ga,
                                  **{key: r.get(f"{side}_{key}", np.nan) for key in optional}})
    names = [f"{side}_{key}" for side in ("home", "away") for key in ("form", "scored", "conceded", *optional)] + ["home_advantage"]
    return pd.DataFrame(rows), names, {team: snapshot(team) for team in history}, history


def match_model(slug):
    with _locks[slug]:
        return _match_model(slug, version(slug, "matches"))


@lru_cache(maxsize=12)
def _match_model(slug, revision):
    stored = model_store.load(slug, "match")
    if stored is not None:
        return stored
    df, provenance = db.matches(slug)
    table, features, state, history = build_match_features(df)
    seasons = sorted(table.season.unique())
    if len(seasons) < 2:
        raise ValueError("At least two seasons are needed for chronological evaluation")
    holdout = seasons[-1]
    train, test = table[table.season < holdout], table[table.season == holdout]
    if len(train) < 30 or len(test) < 10:
        raise ValueError("Not enough history for a reliable train/test split")
    def new_model():
        return make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(
            n_estimators=160, min_samples_leaf=8, max_depth=9, random_state=17, n_jobs=2))
    clf = new_model().fit(train[features], train.target)
    pred = clf.predict(test[features])
    raw = clf.predict_proba(test[features])
    proba = np.zeros((len(test), 3))
    proba[:, clf.classes_.astype(int)] = raw
    metrics = dict(accuracy=round(accuracy_score(test.target, pred), 3),
                   baseline=round(float((test.target == 0).mean()), 3),
                   log_loss=round(log_loss(test.target, proba, labels=[0, 1, 2]), 3),
                   n_train=len(train), n_test=len(test), test_season=holdout,
                   train_end=str(train.date.max()), test_start=str(test.date.min()),
                   method="Random forest", confusion=confusion_matrix(test.target, pred, labels=[0, 1, 2]).tolist())
    audit = test[["date", "home_team", "away_team", "target"]].copy()
    audit["predicted"] = pred
    audit["correct"] = audit.target == audit.predicted
    served = new_model().fit(table[features], table.target)
    return dict(clf=served, metrics=metrics, features=features, state=state, history=dict(history),
                provenance=provenance, audit=audit.tail(15).to_dict("records"),
                importance=sorted([{"feature": f, "importance": round(float(w), 3)} for f, w in zip(features, served[-1].feature_importances_)], key=lambda x: -x["importance"]))


def outcome(slug, home, away, neutral=False):
    if home == away:
        raise ValueError("Choose two different teams")
    b = match_model(slug)
    if home not in b["state"] or away not in b["state"]:
        raise ValueError("Choose teams from this competition's match dataset")
    h, a = b["state"][home], b["state"][away]
    feat = {**{f"home_{k}": v for k, v in h.items()}, **{f"away_{k}": v for k, v in a.items()}, "home_advantage": 0.0 if neutral else 1.0}
    raw = b["clf"].predict_proba(pd.DataFrame([feat])[b["features"]])[0]
    prob = {CLASSES[int(i)]: float(p) for i, p in zip(b["clf"].classes_, raw)}
    for label in CLASSES:
        prob.setdefault(label, 0.0)
    neutral_seen = slug == "champions-league"
    return dict(home=home, away=away, prob=prob, pick=max(prob, key=prob.get), neutral=neutral,
                features={k: round(v, 2) if np.isfinite(v) else None for k, v in feat.items()},
                form={side: ["W" if g["form"] == 3 else "D" if g["form"] == 1 else "L" for g in b["history"][team]] for side, team in (("home", home), ("away", away))},
                metrics=b["metrics"], importance=b["importance"], audit=b["audit"], provenance=b["provenance"],
                note="90-minute result. Shots and possession are included only when observed in the source. " + ("Neutral venues are rare in the training sample." if neutral_seen else "Domestic history contains home fixtures only; neutral-venue effects are not learned."))
