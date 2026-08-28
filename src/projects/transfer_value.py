"""Project 1 — Transfer value predictor.

Pull player statistics from recent Premier League seasons, train a linear model
to predict a player's market/transfer value from their own stats (goals,
assists, minutes, age, position ...), then plug in any player and see what the
model thinks they are worth versus their actual value.

A really simple way to see how machine learning turns player statistics into a
usable prediction.

Tech stack: requests (data), pandas, scikit-learn, matplotlib.

CLI:
    python -m projects.transfer_value            # train, report, save model
    python -m projects.transfer_value --plot     # + predicted-vs-actual scatter
"""
import os

from projects.common import (FEATURE_COLUMNS, MODELS_DIR, load_players,
                             latest_player_seasons)

MODEL_PATH = os.path.join(MODELS_DIR, "transfer_value.joblib")


def _build_matrix(df):
    """Feature matrix X (numeric stats + one-hot position) and target y (value)."""
    import pandas as pd
    X = df[FEATURE_COLUMNS].copy()
    pos = pd.get_dummies(df["position"], prefix="pos")
    X = pd.concat([X, pos], axis=1)
    y = df["market_value_eur_m"].astype(float)
    return X, y


def train(save=True):
    """Train the linear regression and report held-out performance."""
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    import joblib

    df = load_players()
    X, y = _build_matrix(df)
    feature_names = list(X.columns)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=0)
    model = make_pipeline(StandardScaler(), LinearRegression())
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    metrics = {
        "mae_eur_m": round(float(mean_absolute_error(y_te, pred)), 2),
        "r2": round(float(r2_score(y_te, pred)), 3),
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
    }

    # refit on everything for the served model
    model.fit(X, y)
    bundle = {"model": model, "features": feature_names, "metrics": metrics}
    if save:
        os.makedirs(MODELS_DIR, exist_ok=True)
        joblib.dump(bundle, MODEL_PATH)
    return bundle


_bundle = None


def _get():
    global _bundle
    if _bundle is None:
        import joblib
        if os.path.exists(MODEL_PATH):
            _bundle = joblib.load(MODEL_PATH)
        else:
            _bundle = train(save=True)
    return _bundle


def reload():
    global _bundle
    _bundle = None


def list_players():
    """Player directory (latest season) for the UI dropdown."""
    df = latest_player_seasons(load_players())
    df = df.sort_values("market_value_eur_m", ascending=False)
    return [{"player": r.player, "team": r.team, "position": r.position,
             "value": float(r.market_value_eur_m)} for r in df.itertuples()]


def _predict_row(stat_row):
    """stat_row: dict with FEATURE_COLUMNS + position. Returns predicted value."""
    import pandas as pd
    bundle = _get()
    X = pd.DataFrame([stat_row])
    X = X.reindex(columns=[c for c in FEATURE_COLUMNS], fill_value=0)
    pos = pd.get_dummies(pd.Series([stat_row.get("position", "MF")]), prefix="pos")
    X = pd.concat([X.reset_index(drop=True), pos.reset_index(drop=True)], axis=1)
    X = X.reindex(columns=bundle["features"], fill_value=0)
    return float(bundle["model"].predict(X)[0])


def predict_player(name):
    """Model value vs actual for a named player (latest season)."""
    df = latest_player_seasons(load_players())
    row = df[df["player"].str.lower() == str(name).lower()]
    if row.empty:
        return {"error": f"unknown player '{name}'"}
    r = row.iloc[0]
    stat = {c: float(r[c]) for c in FEATURE_COLUMNS}
    stat["position"] = r["position"]
    predicted = _predict_row(stat)
    actual = float(r["market_value_eur_m"])
    return {
        "player": r["player"], "team": r["team"], "season": r["season"],
        "position": r["position"],
        "stats": {c: (int(r[c]) if c != "age" else int(r[c])) for c in FEATURE_COLUMNS},
        "predicted_value_eur_m": round(predicted, 1),
        "actual_value_eur_m": round(actual, 1),
        "residual_eur_m": round(predicted - actual, 1),
        "verdict": ("model sees upside" if predicted > actual * 1.12 else
                    "model sees overprice" if predicted < actual * 0.88 else
                    "roughly fair"),
        "metrics": _get()["metrics"],
    }


def predict_custom(stat_row):
    """Predict value for an arbitrary stat line (what-if)."""
    clean = {c: float(stat_row.get(c, 0) or 0) for c in FEATURE_COLUMNS}
    clean["position"] = stat_row.get("position", "MF")
    return {"predicted_value_eur_m": round(_predict_row(clean), 1),
            "input": clean, "metrics": _get()["metrics"]}


def coefficients():
    """What the linear model learned — signed weight per (standardised) feature."""
    bundle = _get()
    lr = bundle["model"].named_steps["linearregression"]
    pairs = sorted(zip(bundle["features"], lr.coef_),
                   key=lambda p: -abs(p[1]))
    return [{"feature": f, "weight": round(float(w), 2)} for f, w in pairs]


def plot(path=None):
    """Predicted vs actual scatter over all player-seasons."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    df = load_players()
    X, y = _build_matrix(df)
    bundle = _get()
    X = X.reindex(columns=bundle["features"], fill_value=0)
    pred = bundle["model"].predict(X)
    path = path or os.path.join(MODELS_DIR, "transfer_value_fit.png")
    plt.figure(figsize=(6, 6))
    plt.scatter(y, pred, alpha=0.5, s=18)
    lim = max(y.max(), pred.max()) * 1.05
    plt.plot([0, lim], [0, lim], "k--", lw=1)
    plt.xlabel("Actual value (€m)"); plt.ylabel("Predicted value (€m)")
    plt.title("Transfer value — predicted vs actual")
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close()
    return path


def main():
    import sys
    b = train(save=True)
    print("Transfer-value model trained.")
    print("  metrics:", b["metrics"])
    print("  top weights:")
    for c in coefficients()[:6]:
        print(f"    {c['feature']:<16} {c['weight']:+.2f}")
    if "--plot" in sys.argv:
        print("  wrote", plot())


if __name__ == "__main__":
    main()
