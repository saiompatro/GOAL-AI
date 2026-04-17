"""On-demand inference for a single fixture.

Usage:
    python -m goal_ai.predict --home Brazil --away Argentina [--neutral] [--stage "FIFA World Cup"]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

from .features import FEATURE_COLUMNS


def _load_config() -> dict:
    return yaml.safe_load((Path(__file__).resolve().parents[2] / "config.yaml").read_text())


def _latest_row(feats: pd.DataFrame, team: str, side: str) -> dict:
    col = f"{side}_team"
    recent = feats[feats[col] == team].tail(1)
    if recent.empty:
        # fallback to any match involving the team
        any_m = feats[(feats["home_team"] == team) | (feats["away_team"] == team)].tail(1)
        if any_m.empty:
            return {}
        return any_m.iloc[0].to_dict()
    return recent.iloc[0].to_dict()


def build_fixture_row(feats: pd.DataFrame, home: str, away: str,
                      neutral: bool = True, stage: str = "FIFA World Cup") -> np.ndarray:
    """Assemble a feature vector for an unplayed fixture from most-recent team state."""
    h = _latest_row(feats, home, "home")
    a = _latest_row(feats, away, "away")

    def get(d, key, default=0.0):
        return float(d.get(key, default)) if d else default

    row = {
        "elo_home_pre": get(h, "elo_home_pre", 1500.0),
        "elo_away_pre": get(a, "elo_away_pre", 1500.0),
    }
    row["elo_diff"] = row["elo_home_pre"] - row["elo_away_pre"]
    for w in (5, 10):
        for k in (f"win_rate_{w}", f"gf_{w}", f"ga_{w}", f"gd_{w}"):
            row[f"home_{k}"] = get(h, f"home_{k}")
            row[f"away_{k}"] = get(a, f"away_{k}")
    row["h2h_home_wr"] = 0.5
    row["h2h_avg_gd"] = 0.0
    row["h2h_n"] = 0
    row["rest_home"] = 7
    row["rest_away"] = 7
    stage_l = stage.lower()
    row["is_wc"] = int("world cup" in stage_l and "qualif" not in stage_l)
    row["is_wc_qual"] = int("qualif" in stage_l)
    row["is_friendly"] = int("friendly" in stage_l)
    row["is_continental"] = int(any(s in stage_l for s in ("euro", "copa", "afcon", "asian cup", "gold cup")))
    row["neutral"] = int(neutral)
    for col in ("squad_mean","top11_mean","star3_mean","att_mean","mid_mean","def_mean"):
        row[f"home_{col}"] = get(h, f"home_{col}", 70.0)
        row[f"away_{col}"] = get(a, f"away_{col}", 70.0)
        row[f"{col}_diff"] = row[f"home_{col}"] - row[f"away_{col}"]
    return np.array([row[c] for c in FEATURE_COLUMNS], dtype=float)


def predict_fixture(home: str, away: str, neutral: bool = True, stage: str = "FIFA World Cup") -> dict:
    cfg = _load_config()
    art = Path(__file__).resolve().parents[2] / cfg["artifacts_dir"]
    feats = pd.read_parquet(art / "features.parquet") if (art / "features.parquet").exists() else None
    if feats is None:
        raise RuntimeError("Run the pipeline first: `python scripts/run_pipeline.py`")

    x = build_fixture_row(feats, home, away, neutral, stage)

    chosen = json.loads((art / "metrics.json").read_text())["chosen"]
    if chosen == "stack":
        xgb_m = joblib.load(art / "xgb.joblib")
        lgbm_m = joblib.load(art / "lgbm.joblib")
        meta = joblib.load(art / "stack_meta.joblib")
        # NN probs
        import torch
        import torch.nn.functional as F
        from .train import FFN
        state = __import__("torch").load(art / "nn.pt", map_location="cpu", weights_only=False)
        model = FFN(state["in_dim"], state["hidden"], state["dropout"])
        model.load_state_dict(state["state_dict"])
        model.eval()
        Xs = state["scaler"].transform(x.reshape(1, -1))
        with __import__("torch").no_grad():
            nn_p = F.softmax(model(__import__("torch").tensor(Xs, dtype=__import__("torch").float32)), dim=1).numpy()
        stacked = np.hstack([xgb_m.predict_proba(x.reshape(1, -1)),
                              lgbm_m.predict_proba(x.reshape(1, -1)),
                              nn_p])
        probs = meta.predict_proba(stacked)[0]
    else:
        model = joblib.load(art / f"{chosen}.joblib")
        probs = model.predict_proba(x.reshape(1, -1))[0]

    # SHAP drivers from XGB (always available)
    from .explain import build_explainer, top_drivers
    xgb_m = joblib.load(art / "xgb.joblib")
    drivers = top_drivers(build_explainer(xgb_m), x, k=5)

    p_home, p_draw, p_away = map(float, probs)
    confidence = float(max(probs))
    return {
        "home": home, "away": away, "neutral": neutral, "stage": stage,
        "model_version": json.loads((art / "metrics.json").read_text())["version"],
        "chosen_model": chosen,
        "p_home": p_home, "p_draw": p_draw, "p_away": p_away,
        "confidence": confidence, "drivers": drivers,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", required=True)
    ap.add_argument("--away", required=True)
    ap.add_argument("--neutral", action="store_true")
    ap.add_argument("--stage", default="FIFA World Cup")
    ap.add_argument("--push", action="store_true", help="Push result to Supabase")
    args = ap.parse_args()
    out = predict_fixture(args.home, args.away, args.neutral, args.stage)
    print(json.dumps(out, indent=2))
    if args.push:
        from .supabase_io import push_single_prediction
        push_single_prediction(out)


if __name__ == "__main__":
    main()
