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
from goal_ai.clean import clean_matches, clean_players, aggregate_players
from goal_ai.features import build_features
from goal_ai.train import train_all, save_artifacts
from goal_ai.evaluate import confusion_png, reliability_png, write_model_card
from goal_ai.explain import build_explainer, global_summary_png
from goal_ai.simulate import build_baseline_simulation


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    art = ROOT / cfg["artifacts_dir"]
    art.mkdir(parents=True, exist_ok=True)

    print("[1/7] Ingest")
    raw_matches, raw_players = load_raw(ROOT.parent / "data" / "raw")

    print("[2/7] Clean")
    matches = clean_matches(raw_matches)
    players = clean_players(raw_players)
    players_agg = aggregate_players(players)
    players.to_parquet(art / "players.parquet", index=False)
    players_agg.to_parquet(art / "player_team_aggregates.parquet", index=False)

    print(f"[3/7] Features ({len(matches)} matches)")
    feats = build_features(matches, players_agg, cfg)
    feats.to_parquet(art / "features.parquet", index=False)

    print("[4/7] Train + compare")
    results = train_all(feats, cfg)
    save_artifacts(results, art, cfg["model_version"])

    print(f"[5/7] Evaluate (chosen={results['chosen']})")
    split = results["split"]
    probs_test = results["test_probs"][results["chosen"]]
    confusion_png(split.y_test, probs_test, art / "confusion_matrix.png",
                  f"Confusion — {results['chosen']}")
    reliability_png(split.y_test, probs_test, art / "reliability.png",
                     f"Reliability — {results['chosen']}")
    write_model_card(results, art / "model_card.md", cfg["model_version"])

    print("[6/7] SHAP")
    sample = split.X_test[: min(500, len(split.X_test))]
    global_summary_png(build_explainer(joblib.load(art / "xgb.joblib")),
                       sample, art / "shap_summary.png")

    print("[7/7] 2026 Monte Carlo simulation")
    sim_n = int(cfg.get("simulation", {}).get("n", 100_000))
    simulation = build_baseline_simulation(ROOT.parent / "data" / "raw", art, n=sim_n)
    from goal_ai.predict import predict_fixture
    sample_fixtures = [("Brazil", "Argentina"), ("France", "Germany"), ("United States", "Mexico")]
    samples = []
    for home, away in sample_fixtures:
        try:
            samples.append(predict_fixture(home, away, neutral=True, stage="FIFA World Cup"))
        except Exception as exc:
            samples.append({"home": home, "away": away, "error": str(exc)})
    (art / "sample_predictions.json").write_text(json.dumps(samples, indent=2, default=float))

    print("\nDone.")
    print(json.dumps({"chosen": results["chosen"],
                      "test_metrics": results["metrics"][results["chosen"]]["test"],
                      "simulation_teams": len(simulation),
                      "simulation_champion_probability_sum": float(simulation["p_win"].sum())},
                     indent=2, default=float))


if __name__ == "__main__":
    main()
