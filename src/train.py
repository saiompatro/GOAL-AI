"""Train the match prediction models.

- Outcome model: gradient-boosted classifier over P(home win / draw / away win)
- Scoreline model: two Poisson gradient boosters for expected goals each side
Evaluation uses a strict time split (train < 2022-01-01 <= test) so every test
match is predicted only from information available before it was played.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import accuracy_score, log_loss

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
MODELS = os.path.join(os.path.dirname(__file__), "..", "models")

FEATURES = ["elo_diff", "ppg5_diff", "gd10_diff", "morale_diff", "rest_diff",
            "att_vs_def", "def_vs_att", "streak_diff", "exp_diff",
            "h2h_rate", "h2h_gd", "tz_east_diff",
            "heat_diff", "hum_diff", "alt_diff", "travel_diff", "neutral", "is_wc"]


def main():
    df = pd.read_csv(os.path.join(DATA, "training_table.csv"), parse_dates=["date"])
    X, y = df[FEATURES], df["outcome"]
    cut = df["date"] < "2022-01-01"
    Xtr, ytr, Xte, yte = X[cut], y[cut], X[~cut], y[~cut]

    clf = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06,
                                         max_depth=4, l2_regularization=1.0,
                                         random_state=42)
    clf.fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)
    acc = accuracy_score(yte, proba.argmax(1))
    ll = log_loss(yte, proba, labels=[0, 1, 2])

    # baselines on the same test window
    base_mode = (yte == 2).mean()                       # always predict home win
    elo_pick = np.where(Xte["elo_diff"] > 0, 2, 0)      # pick the Elo favourite
    acc_elo = accuracy_score(yte, elo_pick)
    print(f"test matches: {len(yte)} (2022 -> mid-2026)")
    print(f"model     accuracy {acc:.3f}   log-loss {ll:.3f}")
    print(f"baselines: always-home {base_mode:.3f}, elo-favourite {acc_elo:.3f}")

    # goal models (Poisson)
    gh = HistGradientBoostingRegressor(loss="poisson", max_iter=300, max_depth=4,
                                       learning_rate=0.06, random_state=42)
    ga = HistGradientBoostingRegressor(loss="poisson", max_iter=300, max_depth=4,
                                       learning_rate=0.06, random_state=42)
    gh.fit(Xtr, df.loc[cut, "home_goals"])
    ga.fit(Xtr, df.loc[cut, "away_goals"])
    mae_h = np.abs(gh.predict(Xte) - df.loc[~cut, "home_goals"]).mean()
    mae_a = np.abs(ga.predict(Xte) - df.loc[~cut, "away_goals"]).mean()
    print(f"goals MAE: home {mae_h:.2f}, away {mae_a:.2f}")

    # refit on everything for production
    clf.fit(X, y); gh.fit(X, df["home_goals"]); ga.fit(X, df["away_goals"])
    joblib.dump({"clf": clf, "goals_home": gh, "goals_away": ga,
                 "features": FEATURES}, os.path.join(MODELS, "fifa_model.joblib"))

    imp = {}
    from sklearn.inspection import permutation_importance
    r = permutation_importance(clf, Xte, yte, n_repeats=3, random_state=0)
    for f, v in sorted(zip(FEATURES, r.importances_mean), key=lambda x: -x[1]):
        imp[f] = round(float(v), 4)
        print(f"  importance {f:12s} {v:+.4f}")
    json.dump({"test_accuracy": acc, "test_logloss": ll, "baseline_home": base_mode,
               "baseline_elo": acc_elo, "mae_home": mae_h, "mae_away": mae_a,
               "n_test": int(len(yte)), "importance": imp},
              open(os.path.join(MODELS, "metrics.json"), "w"), indent=1)
    print("saved models/fifa_model.joblib")


if __name__ == "__main__":
    main()
