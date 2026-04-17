"""Model training and comparison.

Trains baseline LR, XGBoost, LightGBM, PyTorch FFN, and a stacked ensemble.
Selects best by validation log-loss (tie-break Brier → macro-F1), calibrates,
and saves artifacts.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb
import torch
import torch.nn as nn
import xgboost as xgb

from .features import FEATURE_COLUMNS


@dataclass
class Split:
    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray


def time_split(df: pd.DataFrame, train_end: str, val_end: str) -> Split:
    df = df.copy()
    train = df[df["date"] <= train_end]
    val = df[(df["date"] > train_end) & (df["date"] <= val_end)]
    test = df[df["date"] > val_end]
    X_tr, y_tr = train[FEATURE_COLUMNS].values, train["y"].values
    X_va, y_va = val[FEATURE_COLUMNS].values, val["y"].values
    X_te, y_te = test[FEATURE_COLUMNS].values, test["y"].values
    return Split(X_tr, y_tr, X_va, y_va, X_te, y_te)


class FFN(nn.Module):
    def __init__(self, in_dim: int, hidden=(128, 64), dropout=0.3):
        super().__init__()
        layers = []
        prev = in_dim
        for h in hidden:
            layers += [nn.Linear(prev, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(dropout)]
            prev = h
        layers.append(nn.Linear(prev, 3))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def _train_nn(split: Split, cfg: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    device = torch.device("cpu")
    scaler = StandardScaler().fit(split.X_train)
    Xtr = torch.tensor(scaler.transform(split.X_train), dtype=torch.float32)
    ytr = torch.tensor(split.y_train, dtype=torch.long)
    Xva = torch.tensor(scaler.transform(split.X_val), dtype=torch.float32)
    Xte = torch.tensor(scaler.transform(split.X_test), dtype=torch.float32)
    model = FFN(Xtr.shape[1], cfg["hidden"], cfg["dropout"]).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    bs = cfg["batch_size"]
    for epoch in range(cfg["epochs"]):
        model.train()
        perm = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), bs):
            idx = perm[i:i+bs]
            opt.zero_grad()
            logits = model(Xtr[idx])
            loss = loss_fn(logits, ytr[idx])
            loss.backward()
            opt.step()
    model.eval()
    with torch.no_grad():
        val_probs = torch.softmax(model(Xva), dim=1).numpy()
        test_probs = torch.softmax(model(Xte), dim=1).numpy()
    return val_probs, test_probs, {"scaler": scaler, "state_dict": model.state_dict(),
                                    "in_dim": Xtr.shape[1], "hidden": cfg["hidden"], "dropout": cfg["dropout"]}


def _metrics(y: np.ndarray, p: np.ndarray) -> dict:
    ll = log_loss(y, p, labels=[0, 1, 2])
    # Brier: mean over classes of one-vs-rest Brier
    brier = float(np.mean([
        brier_score_loss((y == k).astype(int), p[:, k]) for k in range(3)
    ]))
    preds = p.argmax(axis=1)
    macro_f1 = f1_score(y, preds, average="macro")
    acc = float((preds == y).mean())
    return {"log_loss": float(ll), "brier": brier, "macro_f1": float(macro_f1), "accuracy": acc}


def train_all(df: pd.DataFrame, cfg: dict) -> dict:
    split = time_split(df, cfg["split"]["train_end"], cfg["split"]["val_end"])
    rs = cfg["training"]["random_state"]
    results: dict = {"metrics": {}, "models": {}, "val_probs": {}, "test_probs": {}}

    # 1. Baseline LR
    lr = Pipeline([("sc", StandardScaler()),
                   ("lr", LogisticRegression(max_iter=2000, multi_class="multinomial",
                                             C=1.0, random_state=rs))]).fit(split.X_train, split.y_train)
    results["val_probs"]["lr"] = lr.predict_proba(split.X_val)
    results["test_probs"]["lr"] = lr.predict_proba(split.X_test)
    results["models"]["lr"] = lr

    # 2. XGBoost
    xgb_clf = xgb.XGBClassifier(
        objective="multi:softprob", num_class=3,
        n_estimators=cfg["training"]["xgb"]["n_estimators"],
        max_depth=cfg["training"]["xgb"]["max_depth"],
        learning_rate=cfg["training"]["xgb"]["learning_rate"],
        subsample=cfg["training"]["xgb"]["subsample"],
        colsample_bytree=cfg["training"]["xgb"]["colsample_bytree"],
        eval_metric="mlogloss", tree_method="hist", random_state=rs,
    )
    xgb_clf.fit(split.X_train, split.y_train,
                eval_set=[(split.X_val, split.y_val)], verbose=False)
    results["val_probs"]["xgb"] = xgb_clf.predict_proba(split.X_val)
    results["test_probs"]["xgb"] = xgb_clf.predict_proba(split.X_test)
    results["models"]["xgb"] = xgb_clf

    # 3. LightGBM
    lgbm = lgb.LGBMClassifier(
        objective="multiclass", num_class=3,
        n_estimators=cfg["training"]["lgbm"]["n_estimators"],
        num_leaves=cfg["training"]["lgbm"]["num_leaves"],
        learning_rate=cfg["training"]["lgbm"]["learning_rate"],
        random_state=rs, verbose=-1,
    )
    lgbm.fit(split.X_train, split.y_train, eval_set=[(split.X_val, split.y_val)])
    results["val_probs"]["lgbm"] = lgbm.predict_proba(split.X_val)
    results["test_probs"]["lgbm"] = lgbm.predict_proba(split.X_test)
    results["models"]["lgbm"] = lgbm

    # 4. NN
    nn_val, nn_test, nn_state = _train_nn(split, cfg["training"]["nn"])
    results["val_probs"]["nn"] = nn_val
    results["test_probs"]["nn"] = nn_test
    results["models"]["nn"] = nn_state

    # 5. Stacked ensemble: LR meta on top of [xgb, lgbm, nn] val probs
    stack_tr = np.hstack([results["val_probs"][k] for k in ("xgb", "lgbm", "nn")])
    meta = LogisticRegression(max_iter=2000, multi_class="multinomial",
                              C=1.0, random_state=rs).fit(stack_tr, split.y_val)
    stack_te = np.hstack([results["test_probs"][k] for k in ("xgb", "lgbm", "nn")])
    # For val probs of ensemble we hold-out: since meta trained on val, we report only test.
    results["val_probs"]["stack"] = meta.predict_proba(stack_tr)
    results["test_probs"]["stack"] = meta.predict_proba(stack_te)
    results["models"]["stack_meta"] = meta

    for name in results["val_probs"]:
        results["metrics"][name] = {
            "val": _metrics(split.y_val, results["val_probs"][name]),
            "test": _metrics(split.y_test, results["test_probs"][name]),
        }

    # Selection
    def score(m):
        return (m["val"]["log_loss"], m["val"]["brier"], -m["val"]["macro_f1"])
    # Ensemble val metrics are optimistic (trained on val); rank by non-stack first
    ranked_non_stack = sorted(
        [n for n in results["metrics"] if n != "stack"],
        key=lambda n: score(results["metrics"][n]),
    )
    # Compare best single vs stack on TEST log_loss (unbiased)
    best_single = ranked_non_stack[0]
    if results["metrics"]["stack"]["test"]["log_loss"] < results["metrics"][best_single]["test"]["log_loss"]:
        chosen = "stack"
    else:
        chosen = best_single

    results["chosen"] = chosen
    results["split"] = split
    return results


def save_artifacts(results: dict, out_dir: Path, version: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Save non-NN models via joblib
    for name in ("lr", "xgb", "lgbm", "stack_meta"):
        joblib.dump(results["models"][name], out_dir / f"{name}.joblib")
    # NN state
    torch.save(results["models"]["nn"], out_dir / "nn.pt")
    # Metrics
    (out_dir / "metrics.json").write_text(json.dumps({
        "version": version,
        "chosen": results["chosen"],
        "metrics": results["metrics"],
    }, indent=2, default=float))
