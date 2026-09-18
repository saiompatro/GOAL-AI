"""Retrain, evaluate and persist all six competition workspaces.

Run: python src/projects/train_workspaces.py
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from projects import analytics, competitions as db, model_store


def train_all():
    report = {"trained_at": datetime.now(timezone.utc).isoformat(), "competitions": {}}
    model_store.RETRAIN = True
    try:
        analytics._player_model.cache_clear()
        analytics._scout_model.cache_clear()
        analytics._match_model.cache_clear()
        for slug in db.COMPETITIONS:
            valuation = analytics.player_model(slug)
            scouting = analytics.scout_model(slug)
            match = analytics.match_model(slug)
            for kind, bundle in (("valuation", valuation), ("scouting", scouting), ("match", match)):
                model_store.save(slug, kind, bundle)
            report["competitions"][slug] = {
                "valuation": valuation["metrics"], "valuation_source": valuation["provenance"],
                "scouting": {"season": str(scouting["latest"].season.max()), "profiles": len(scouting["outfield"]),
                             "features": scouting["features"], "source": scouting["provenance"]},
                "match": match["metrics"]}
            print(f"{slug}: valuation MAE EUR{valuation['metrics']['mae_eur_m']}m, "
                  f"R2 {valuation['metrics']['r2']}; scouting {len(scouting['outfield'])}; "
                  f"match accuracy {match['metrics']['accuracy']:.1%}", flush=True)
        (model_store.DIRECTORY / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    finally:
        model_store.RETRAIN = False
    return report


if __name__ == "__main__":
    train_all()
