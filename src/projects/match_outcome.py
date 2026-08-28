"""Project 2 — Match outcome predictor.

Take historical Premier League match data and give the model features like
goals scored, goals conceded, shots, possession, home-field advantage and
recent form, then train a random-forest / XGBoost classifier to predict whether
the home team will win, draw or lose. Backtest it on a held-out span of seasons
and see how often it actually gets the result right.

Tech stack: pandas, scikit-learn, XGBoost (optional — falls back to
GradientBoosting if not installed), matplotlib.

The bundled data (data/club/premier_league_results.csv) has final scores only,
so shots and possession are reconstructed as rolling per-team proxies (a team
that scores and concedes at a certain rate shoots / holds the ball roughly
accordingly) — the model still learns from real, dated match outcomes with no
lookahead. Swap in a richer feed (e.g. football-data.co.uk shots/possession
columns) and the same feature names carry through.

CLI:
    python -m projects.match_outcome            # train + walk-forward backtest
    python -m projects.match_outcome --plot     # + confusion matrix
"""
import os

from projects.common import CLUB_RESULTS_CSV, MODELS_DIR

MODEL_PATH = os.path.join(MODELS_DIR, "match_outcome.joblib")

FEATURES = [
    "home_form_ppg", "away_form_ppg",
    "home_gf_avg", "home_ga_avg", "away_gf_avg", "away_ga_avg",
    "home_shots_avg", "away_shots_avg",
    "home_poss_avg", "away_poss_avg",
    "form_ppg_diff", "gd_form_diff", "home_advantage",
]
CLASSES = ["home_win", "draw", "away_win"]


def _result(hs, as_):
    return "home_win" if hs > as_ else ("draw" if hs == as_ else "away_win")


def build_features(window=6):
    """Walk the season chronologically, building pre-match rolling features for
    each team so nothing leaks from the match being predicted."""
    import pandas as pd
    from collections import defaultdict, deque

    df = pd.read_csv(CLUB_RESULTS_CSV).sort_values("date").reset_index(drop=True)
    hist = defaultdict(lambda: {"pts": deque(maxlen=window), "gf": deque(maxlen=window),
                                "ga": deque(maxlen=window)})
    rows = []
    for r in df.itertuples():
        h, a = hist[r.home_team], hist[r.away_team]

        def agg(d, key, default):
            return sum(d[key]) / len(d[key]) if d[key] else default

        h_ppg, a_ppg = agg(h, "pts", 1.3), agg(a, "pts", 1.3)
        h_gf, h_ga = agg(h, "gf", 1.3), agg(h, "ga", 1.3)
        a_gf, a_ga = agg(a, "gf", 1.3), agg(a, "ga", 1.3)
        # shots / possession proxies from scoring rates (real feeds slot in here)
        h_shots, a_shots = 8 + h_gf * 3.2 + h_ga * 0.6, 8 + a_gf * 3.2 + a_ga * 0.6
        h_poss = 50 + (h_gf - h_ga) * 4 - (a_gf - a_ga) * 4
        a_poss = 100 - h_poss

        if h["pts"] and a["pts"]:  # only rows with real history become training data
            rows.append({
                "date": r.date, "season": r.season,
                "home_team": r.home_team, "away_team": r.away_team,
                "home_form_ppg": h_ppg, "away_form_ppg": a_ppg,
                "home_gf_avg": h_gf, "home_ga_avg": h_ga,
                "away_gf_avg": a_gf, "away_ga_avg": a_ga,
                "home_shots_avg": h_shots, "away_shots_avg": a_shots,
                "home_poss_avg": h_poss, "away_poss_avg": a_poss,
                "form_ppg_diff": h_ppg - a_ppg,
                "gd_form_diff": (h_gf - h_ga) - (a_gf - a_ga),
                "home_advantage": 1.0,
                "result": _result(r.home_score, r.away_score),
            })

        pts_h = 3 if r.home_score > r.away_score else (1 if r.home_score == r.away_score else 0)
        h["pts"].append(pts_h); h["gf"].append(r.home_score); h["ga"].append(r.away_score)
        a["pts"].append(3 - pts_h if pts_h != 1 else 1)
        a["gf"].append(r.away_score); a["ga"].append(r.home_score)
    return pd.DataFrame(rows)


def _make_classifier():
    """XGBoost if available, else sklearn GradientBoosting — same interface."""
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, eval_metric="mlogloss",
            tree_method="hist", random_state=0), "xgboost"
    except Exception:
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(
            n_estimators=400, max_depth=12, min_samples_leaf=8,
            random_state=0, n_jobs=-1), "random_forest"


def train(save=True, test_seasons=("2022-23", "2023-24")):
    """Train and evaluate with a strict season holdout (no lookahead)."""
    from sklearn.metrics import accuracy_score, log_loss
    import numpy as np
    import joblib

    data = build_features()
    label_ix = {c: i for i, c in enumerate(CLASSES)}
    y = data["result"].map(label_ix).values
    X = data[FEATURES].values

    is_test = data["season"].isin(test_seasons).values
    clf, backend = _make_classifier()
    clf.fit(X[~is_test], y[~is_test])
    proba = clf.predict_proba(X[is_test])
    pred = proba.argmax(axis=1)
    y_te = y[is_test]

    # baseline: always predict home win
    base_acc = float((y_te == label_ix["home_win"]).mean())
    metrics = {
        "backend": backend,
        "accuracy": round(float(accuracy_score(y_te, pred)), 3),
        "log_loss": round(float(log_loss(y_te, proba, labels=[0, 1, 2])), 3),
        "home_win_baseline": round(base_acc, 3),
        "n_train": int((~is_test).sum()), "n_test": int(is_test.sum()),
        "test_seasons": list(test_seasons),
    }

    # refit on everything for serving
    clf, _ = _make_classifier()
    clf.fit(X, y)
    bundle = {"clf": clf, "features": FEATURES, "classes": CLASSES,
              "metrics": metrics, "table": data}
    if save:
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump({k: v for k, v in bundle.items() if k != "table"}, MODEL_PATH)
    return bundle


_bundle = None


def _get():
    global _bundle
    if _bundle is None:
        _bundle = train(save=True)  # cheap enough; keeps the table in memory too
    return _bundle


def reload():
    global _bundle
    _bundle = None


def teams():
    """Teams present in the most recent season of the data."""
    b = _get()
    tbl = b["table"]
    last = sorted(tbl["season"].unique())[-1]
    ts = sorted(set(tbl[tbl["season"] == last]["home_team"]))
    return {"season": last, "teams": ts}


def _latest_team_row(tbl, team):
    rows = tbl[(tbl["home_team"] == team) | (tbl["away_team"] == team)]
    if rows.empty:
        return None
    return rows.iloc[-1]


def predict(home, away):
    """Predict W/D/L for a hypothetical fixture using each team's latest form."""
    b = _get()
    tbl = b["table"]
    hr, ar = _latest_team_row(tbl, home), _latest_team_row(tbl, away)
    if hr is None or ar is None:
        return {"error": "unknown team(s) for the current season"}

    def side(row, team):
        if row["home_team"] == team:
            return dict(ppg=row["home_form_ppg"], gf=row["home_gf_avg"],
                        ga=row["home_ga_avg"], shots=row["home_shots_avg"],
                        poss=row["home_poss_avg"])
        return dict(ppg=row["away_form_ppg"], gf=row["away_gf_avg"],
                    ga=row["away_ga_avg"], shots=row["away_shots_avg"],
                    poss=row["away_poss_avg"])

    h, a = side(hr, home), side(ar, away)
    feat = {
        "home_form_ppg": h["ppg"], "away_form_ppg": a["ppg"],
        "home_gf_avg": h["gf"], "home_ga_avg": h["ga"],
        "away_gf_avg": a["gf"], "away_ga_avg": a["ga"],
        "home_shots_avg": h["shots"], "away_shots_avg": a["shots"],
        "home_poss_avg": h["poss"], "away_poss_avg": a["poss"],
        "form_ppg_diff": h["ppg"] - a["ppg"],
        "gd_form_diff": (h["gf"] - h["ga"]) - (a["gf"] - a["ga"]),
        "home_advantage": 1.0,
    }
    import numpy as np
    X = np.array([[feat[c] for c in FEATURES]])
    proba = b["clf"].predict_proba(X)[0]
    prob = {CLASSES[i]: round(float(proba[i]), 3) for i in range(3)}
    pick = max(prob, key=prob.get)
    return {
        "home": home, "away": away, "prob": prob, "pick": pick,
        "features": {k: round(float(v), 2) for k, v in feat.items()},
        "metrics": b["metrics"],
    }


def feature_importance():
    b = _get()
    clf = b["clf"]
    imp = getattr(clf, "feature_importances_", None)
    if imp is None:
        return []
    pairs = sorted(zip(FEATURES, imp), key=lambda p: -p[1])
    return [{"feature": f, "importance": round(float(w), 3)} for f, w in pairs]


def plot(path=None):
    """Confusion matrix on the holdout seasons."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix
    import numpy as np
    b = train(save=False)
    data = b["table"]
    label_ix = {c: i for i, c in enumerate(CLASSES)}
    is_test = data["season"].isin(b["metrics"]["test_seasons"]).values
    y = data["result"].map(label_ix).values[is_test]
    pred = b["clf"].predict(data[FEATURES].values[is_test])
    cm = confusion_matrix(y, pred, labels=[0, 1, 2])
    path = path or os.path.join(MODELS_DIR, "match_outcome_cm.png")
    plt.figure(figsize=(5, 5))
    plt.imshow(cm, cmap="Blues")
    plt.xticks(range(3), CLASSES, rotation=30); plt.yticks(range(3), CLASSES)
    for i in range(3):
        for j in range(3):
            plt.text(j, i, cm[i, j], ha="center", va="center")
    plt.xlabel("Predicted"); plt.ylabel("Actual")
    plt.title("Match outcome — confusion matrix"); plt.tight_layout()
    plt.savefig(path, dpi=110); plt.close()
    return path


def main():
    import sys
    b = train(save=True)
    m = b["metrics"]
    print(f"Match-outcome model ({m['backend']}) trained.")
    print(f"  holdout {m['test_seasons']}: accuracy {m['accuracy']:.3f} "
          f"(home-win baseline {m['home_win_baseline']:.3f}), "
          f"log-loss {m['log_loss']:.3f}")
    print("  top features:")
    for f in feature_importance()[:6]:
        print(f"    {f['feature']:<16} {f['importance']:.3f}")
    if "--plot" in sys.argv:
        print("  wrote", plot())


if __name__ == "__main__":
    main()
