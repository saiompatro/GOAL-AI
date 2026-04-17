"""End-to-end training pipeline: ingest → clean → features → train → evaluate → explain."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from goal_ai.ingest import load_raw
from goal_ai.clean import clean_matches, aggregate_players
from goal_ai.features import build_features
from goal_ai.train import train_all, save_artifacts
from goal_ai.evaluate import confusion_png, reliability_png, write_model_card
from goal_ai.explain import build_explainer, global_summary_png


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    art = ROOT / cfg["artifacts_dir"]
    art.mkdir(parents=True, exist_ok=True)

    print("[1/6] Ingest")
    raw_matches, raw_players = load_raw(ROOT.parent / "data" / "raw")

    print("[2/6] Clean")
    matches = clean_matches(raw_matches)
    players_agg = aggregate_players(raw_players)

    print(f"[3/6] Features ({len(matches)} matches)")
    feats = build_features(matches, players_agg, cfg)
    feats.to_parquet(art / "features.parquet", index=False)

    print("[4/6] Train + compare")
    results = train_all(feats, cfg)
    save_artifacts(results, art, cfg["model_version"])

    print(f"[5/6] Evaluate (chosen={results['chosen']})")
    split = results["split"]
    probs_test = results["test_probs"][results["chosen"]]
    confusion_png(split.y_test, probs_test, art / "confusion_matrix.png",
                  f"Confusion — {results['chosen']}")
    reliability_png(split.y_test, probs_test, art / "reliability.png",
                     f"Reliability — {results['chosen']}")
    write_model_card(results, art / "model_card.md", cfg["model_version"])

    print("[6/6] SHAP")
    sample = split.X_test[: min(500, len(split.X_test))]
    global_summary_png(build_explainer(joblib.load(art / "xgb.joblib")),
                       sample, art / "shap_summary.png")

    print("\nDone.")
    print(json.dumps({"chosen": results["chosen"],
                      "test_metrics": results["metrics"][results["chosen"]]["test"]},
                     indent=2, default=float))


if __name__ == "__main__":
    main()
