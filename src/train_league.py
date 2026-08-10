"""Train the club-league match models (outcome classifier + Poisson goal models).

Same recipe as train.py for the World Cup model, over club_features.py's
walk-forward table instead. One model per league key in fetch_club_results.LEAGUES.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import accuracy_score, log_loss

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "club")
MODELS = os.path.join(os.path.dirname(__file__), "..", "models")

FEATURES = ["elo_diff", "ppg5_diff", "gd10_diff", "morale_diff",
            "att_vs_def", "def_vs_att", "streak_diff", "h2h_rate", "h2h_gd"]


def train_one(key):
    df = pd.read_csv(os.path.join(DATA, f"{key}_training_table.csv"), parse_dates=["date"])
    X, y = df[FEATURES], df["outcome"]
    # strict time split: last 2 seasons held out
    seasons = sorted(df["season"].unique())
    test_seasons = set(seasons[-2:])
    cut = ~df["season"].isin(test_seasons)
    Xtr, ytr, Xte, yte = X[cut], y[cut], X[~cut], y[~cut]

    clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                         max_depth=4, l2_regularization=1.0,
                                         random_state=42)
    clf.fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)
    acc = accuracy_score(yte, proba.argmax(1))
    ll = log_loss(yte, proba, labels=[0, 1, 2])

    base_mode = (yte == 2).mean()
    elo_pick = np.where(Xte["elo_diff"] > 0, 2, 0)
    acc_elo = accuracy_score(yte, elo_pick)
    print(f"[{key}] test matches: {len(yte)} (seasons {sorted(test_seasons)})")
    print(f"[{key}] model accuracy {acc:.3f}   log-loss {ll:.3f}")
    print(f"[{key}] baselines: always-home {base_mode:.3f}, elo-favourite {acc_elo:.3f}")

    gh = HistGradientBoostingRegressor(loss="poisson", max_iter=250, max_depth=4,
                                       learning_rate=0.06, random_state=42)
    ga = HistGradientBoostingRegressor(loss="poisson", max_iter=250, max_depth=4,
                                       learning_rate=0.06, random_state=42)
    gh.fit(Xtr, df.loc[cut, "home_goals"])
    ga.fit(Xtr, df.loc[cut, "away_goals"])
    mae_h = np.abs(gh.predict(Xte) - df.loc[~cut, "home_goals"]).mean()
    mae_a = np.abs(ga.predict(Xte) - df.loc[~cut, "away_goals"]).mean()
    print(f"[{key}] goals MAE: home {mae_h:.2f}, away {mae_a:.2f}")

    # refit on everything for production
    clf.fit(X, y); gh.fit(X, df["home_goals"]); ga.fit(X, df["away_goals"])
    joblib.dump({"clf": clf, "goals_home": gh, "goals_away": ga, "features": FEATURES},
               os.path.join(MODELS, f"{key}_model.joblib"))
    json.dump({"test_accuracy": acc, "test_logloss": ll, "baseline_home": base_mode,
              "baseline_elo": acc_elo, "mae_home": mae_h, "mae_away": mae_a,
              "n_test": int(len(yte)), "test_seasons": sorted(test_seasons)},
              open(os.path.join(MODELS, f"{key}_metrics.json"), "w"), indent=1)
    print(f"[{key}] saved models/{key}_model.joblib\n")


def main():
    from fetch_club_results import LEAGUES
    for key in LEAGUES:
        train_one(key)


if __name__ == "__main__":
    main()
