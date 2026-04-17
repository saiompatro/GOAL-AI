"""Push teams, predictions for a fixture set, HF insights, and model_runs to Supabase."""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from goal_ai import hf_insights, supabase_io
from goal_ai.predict import predict_fixture


# WC 2026 seeded top nations (illustrative, not official draw)
FIXTURE_TEAMS = [
    "Brazil","Argentina","France","Germany","Spain","England","Portugal",
    "Netherlands","Belgium","Croatia","Morocco","Japan","South Korea",
    "United States","Mexico","Uruguay",
]


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    art = ROOT / cfg["artifacts_dir"]
    metrics = json.loads((art / "metrics.json").read_text())

    # 1. Model run
    supabase_io.push_run(cfg["model_version"], metrics["chosen"], metrics["metrics"])

    # 2. Teams (upsert)
    supabase_io.push_teams(FIXTURE_TEAMS)

    # 3. Predictions for a round-robin preview (capped for demo size)
    preds = []
    for home, away in list(combinations(FIXTURE_TEAMS, 2))[:40]:
        try:
            preds.append(predict_fixture(home, away, neutral=True, stage="FIFA World Cup"))
        except Exception as e:
            print(f"skip {home} vs {away}: {e}")
    supabase_io.push_batch_predictions(preds)
    (art / "sample_predictions.json").write_text(json.dumps(preds, indent=2, default=float))

    # 4. HF insights (teams)
    feats = pd.read_parquet(art / "features.parquet")
    team_stats = []
    for team in FIXTURE_TEAMS:
        last = feats[(feats.home_team == team) | (feats.away_team == team)].tail(1)
        if last.empty:
            continue
        r = last.iloc[0]
        side = "home" if r["home_team"] == team else "away"
        team_stats.append((team, {
            "elo": r[f"elo_{side}_pre"],
            "win_rate_10": r[f"{side}_win_rate_10"],
            "gf_10": r[f"{side}_gf_10"],
            "ga_10": r[f"{side}_ga_10"],
            "top11_mean": r[f"{side}_top11_mean"],
            "star3_mean": r[f"{side}_star3_mean"],
            "att_mean": r[f"{side}_att_mean"],
            "mid_mean": r[f"{side}_mid_mean"],
            "def_mean": r[f"{side}_def_mean"],
        }))
    insight_rows = hf_insights.summarize_teams(team_stats)

    # Resolve team names → ids via Supabase (or skip if offline)
    name_to_id = supabase_io.push_teams(FIXTURE_TEAMS)
    final_rows = []
    for r in insight_rows:
        tid = name_to_id.get(r["entity_key"])
        if tid:
            final_rows.append({"entity_type": "team", "entity_id": tid,
                               "summary_text": r["summary_text"], "model": r["model"]})
    if final_rows:
        supabase_io.push_insights(final_rows)

    (art / "team_insights.json").write_text(json.dumps(insight_rows, indent=2))

    print(f"Done. Pushed {len(preds)} predictions and {len(final_rows)} insights.")


if __name__ == "__main__":
    main()
