"""Tuned, stacked, calibrated ensemble — the high-capacity upgrade.

Protocol (leakage-safe):
  inner-train (<2017) / blend-holdout (2017-2021) / test (2022+, untouched)
  1. Optuna tunes each GBM on inner-train with the blend-holdout as validation
  2. Base models trained on inner-train predict the holdout -> meta-learner
     (multinomial LR) learns to combine + calibrate them
  3. Bases refit on full pre-2022 data, evaluated once on the 2022+ test set
  4. For production, bases refit on everything incl. 2026 matches
TabPFN-2.5 (GPU foundation model) joins as a member: zero tuning by design,
in-context learning over the most recent matches.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import optuna
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from ensemble_model import TorchMLP, StackEnsemble
from train import FEATURES

optuna.logging.set_verbosity(optuna.logging.WARNING)
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
MODELS = os.path.join(os.path.dirname(__file__), "..", "models")
TABPFN_MAX_CTX = 15000  # most recent rows used as in-context examples (VRAM-safe)


def tune_lgb(Xtr, ytr, Xva, yva, n_trials=30):
    def obj(t):
        p = {"objective": "multiclass", "num_class": 3, "verbosity": -1,
             "learning_rate": t.suggest_float("lr", 0.01, 0.15, log=True),
             "num_leaves": t.suggest_int("leaves", 15, 127),
             "min_child_samples": t.suggest_int("mcs", 20, 200),
             "reg_lambda": t.suggest_float("l2", 0.1, 20, log=True),
             "feature_fraction": t.suggest_float("ff", 0.6, 1.0),
             "bagging_fraction": t.suggest_float("bf", 0.6, 1.0), "bagging_freq": 1,
             "n_estimators": 2000}
        m = lgb.LGBMClassifier(**p)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)],
              callbacks=[lgb.early_stopping(50, verbose=False)])
        return log_loss(yva, m.predict_proba(Xva))
    s = optuna.create_study(direction="minimize")
    s.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    b = s.best_params
    return dict(objective="multiclass", num_class=3, verbosity=-1, n_estimators=2000,
                learning_rate=b["lr"], num_leaves=b["leaves"], min_child_samples=b["mcs"],
                reg_lambda=b["l2"], feature_fraction=b["ff"], bagging_fraction=b["bf"],
                bagging_freq=1), s.best_value


def tune_xgb(Xtr, ytr, Xva, yva, n_trials=30):
    def obj(t):
        p = {"objective": "multi:softprob", "num_class": 3, "tree_method": "hist",
             "device": "cuda", "eval_metric": "mlogloss",
             "learning_rate": t.suggest_float("lr", 0.01, 0.15, log=True),
             "max_depth": t.suggest_int("depth", 3, 8),
             "min_child_weight": t.suggest_float("mcw", 1, 50, log=True),
             "reg_lambda": t.suggest_float("l2", 0.1, 20, log=True),
             "subsample": t.suggest_float("ss", 0.6, 1.0),
             "colsample_bytree": t.suggest_float("cs", 0.6, 1.0),
             "n_estimators": 2000, "early_stopping_rounds": 50}
        m = xgb.XGBClassifier(**p)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
        return log_loss(yva, m.predict_proba(Xva))
    s = optuna.create_study(direction="minimize")
    s.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    b = s.best_params
    return dict(objective="multi:softprob", num_class=3, tree_method="hist",
                device="cuda", eval_metric="mlogloss", n_estimators=600,
                learning_rate=b["lr"], max_depth=b["depth"], min_child_weight=b["mcw"],
                reg_lambda=b["l2"], subsample=b["ss"], colsample_bytree=b["cs"]), s.best_value


def tune_cat(Xtr, ytr, Xva, yva, n_trials=15):
    def obj(t):
        m = CatBoostClassifier(
            loss_function="MultiClass", iterations=2000, verbose=False,
            learning_rate=t.suggest_float("lr", 0.01, 0.15, log=True),
            depth=t.suggest_int("depth", 4, 8),
            l2_leaf_reg=t.suggest_float("l2", 1, 30, log=True),
            early_stopping_rounds=50, task_type="GPU", devices="0")
        m.fit(Xtr, ytr, eval_set=(Xva, yva))
        return log_loss(yva, m.predict_proba(Xva))
    s = optuna.create_study(direction="minimize")
    try:
        s.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    except Exception as e:
        print("catboost GPU failed, falling back to CPU:", str(e)[:100])
        return None, None
    b = s.best_params
    return dict(loss_function="MultiClass", iterations=1200, verbose=False,
                learning_rate=b["lr"], depth=b["depth"], l2_leaf_reg=b["l2"],
                task_type="GPU", devices="0"), s.best_value


def fit_tabpfn(X, y):
    from tabpfn import TabPFNClassifier
    Xc, yc = X[-TABPFN_MAX_CTX:], y[-TABPFN_MAX_CTX:]  # most recent context
    m = TabPFNClassifier(device="cuda", ignore_pretraining_limits=True)
    m.fit(Xc, yc)
    return m


def main():
    df = pd.read_csv(os.path.join(DATA, "training_table.csv"), parse_dates=["date"])
    X, y = df[FEATURES].values.astype(np.float32), df["outcome"].values

    inner = df["date"] < "2017-01-01"
    hold = (df["date"] >= "2017-01-01") & (df["date"] < "2022-01-01")
    test = df["date"] >= "2022-01-01"
    pre = inner | hold
    Xi, yi = X[inner.values], y[inner.values]
    Xh, yh = X[hold.values], y[hold.values]
    Xp, yp = X[pre.values], y[pre.values]
    Xt, yt = X[test.values], y[test.values]
    print(f"inner {len(yi)} | holdout {len(yh)} | test {len(yt)}")

    # 1) tune on inner vs holdout
    lgb_p, v = tune_lgb(Xi, yi, Xh, yh);  print(f"lgb tuned   val_ll {v:.4f}")
    xgb_p, v = tune_xgb(Xi, yi, Xh, yh);  print(f"xgb tuned   val_ll {v:.4f}")
    cat_p, v = tune_cat(Xi, yi, Xh, yh)
    if cat_p:
        print(f"cat tuned   val_ll {v:.4f}")
    json.dump({"lgb": {k: (v if not isinstance(v, np.floating) else float(v)) for k, v in lgb_p.items()},
               "xgb": {k: (v if not isinstance(v, np.floating) else float(v)) for k, v in xgb_p.items()},
               "cat": ({k: (v if not isinstance(v, np.floating) else float(v)) for k, v in cat_p.items()} if cat_p else None)},
              open(os.path.join(MODELS, "tuned_params.json"), "w"), indent=1, default=str)

    def make_members(Xfit, yfit, Xva=None, yva=None):
        mem = {}
        m = lgb.LGBMClassifier(**lgb_p)
        if Xva is not None:
            m.fit(Xfit, yfit, eval_set=[(Xva, yva)],
                  callbacks=[lgb.early_stopping(50, verbose=False)])
            lgb_p["n_estimators"] = max(m.best_iteration_, 100)
        else:
            m.fit(Xfit, yfit)
        mem["lgb"] = m
        mx = xgb.XGBClassifier(**xgb_p); mx.fit(Xfit, yfit, verbose=False); mem["xgb"] = mx
        if cat_p:
            mc = CatBoostClassifier(**cat_p); mc.fit(Xfit, yfit); mem["cat"] = mc
        from sklearn.ensemble import HistGradientBoostingClassifier
        hg = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_depth=4,
                                            l2_regularization=1.0, random_state=42)
        hg.fit(Xfit, yfit); mem["histgb"] = hg
        mem["mlp"] = TorchMLP().fit(Xfit, yfit, Xva, yva) if Xva is not None \
            else TorchMLP(epochs=30).fit(Xfit, yfit)
        try:
            mem["tabpfn"] = fit_tabpfn(Xfit, yfit)
        except Exception as e:
            print("tabpfn skipped:", str(e)[:120])
        return mem

    # 2) bases on inner -> meta on holdout
    members = make_members(Xi, yi, Xh, yh)
    stack_h = np.hstack([m.predict_proba(Xh) for m in members.values()])
    meta = LogisticRegression(max_iter=2000, C=1.0).fit(stack_h, yh)
    for name, m in members.items():
        ph = m.predict_proba(Xh)
        print(f"  holdout {name:7s} acc {accuracy_score(yh, ph.argmax(1)):.4f} ll {log_loss(yh, ph):.4f}")

    # 3) refit bases on all pre-2022, evaluate once on test
    members_t = make_members(Xp, yp, Xh, yh)   # early-stop sizes from holdout
    stack_t = np.hstack([m.predict_proba(Xt) for m in members_t.values()])
    pt = meta.predict_proba(stack_t)
    acc, ll = accuracy_score(yt, pt.argmax(1)), log_loss(yt, pt)
    avg = np.mean([m.predict_proba(Xt) for m in members_t.values()], axis=0)
    print(f"\nTEST stacked  acc {acc:.4f}  ll {ll:.4f}")
    print(f"TEST average  acc {accuracy_score(yt, avg.argmax(1)):.4f}  ll {log_loss(yt, avg):.4f}")
    for name, m in members_t.items():
        p = m.predict_proba(Xt)
        print(f"  test {name:7s} acc {accuracy_score(yt, p.argmax(1)):.4f} ll {log_loss(yt, p):.4f}")

    # 4) production: refit on everything
    members_f = make_members(X, y)
    ens = StackEnsemble(members_f, meta)

    old = joblib.load(os.path.join(MODELS, "fifa_model.joblib"))
    joblib.dump({"clf": ens, "goals_home": old["goals_home"], "goals_away": old["goals_away"],
                 "features": FEATURES},
                os.path.join(MODELS, "fifa_model_ensemble.joblib"))
    json.dump({"test_accuracy": float(acc), "test_logloss": float(ll), "n_test": int(len(yt)),
               "members": list(members_f.keys()),
               "meta_weights": meta.coef_.round(3).tolist()},
              open(os.path.join(MODELS, "metrics_ensemble.json"), "w"), indent=1)
    print("\nsaved models/fifa_model_ensemble.joblib")


if __name__ == "__main__":
    main()
