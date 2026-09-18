"""Local, versioned model artifacts; stale artifacts fall back to retraining."""
import hashlib
import json
import platform

import joblib
import numpy
import pandas
import sklearn

from projects import competitions as db

DIRECTORY = db.ROOT / "models/workspaces"
RETRAIN = False


def signature(slug, kind):
    dataset = {"valuation": "players", "scouting": "scouting", "match": "matches"}[kind]
    path = db.DATA / f"{db.config(slug)['key']}_{dataset}.csv"
    files = [path, path.with_suffix(".json")]
    files += [db.ROOT / "src/projects" / name for name in
              ("analytics.py", "competitions.py", "common.py", "player_scouting.py", "model_store.py")]
    # Git may convert text line endings on Windows; that does not change a model input.
    checksums = {str(p.relative_to(db.ROOT)).replace("\\", "/"):
                 hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in files}
    versions = {"python": platform.python_version(), "sklearn": sklearn.__version__,
                "numpy": numpy.__version__, "pandas": pandas.__version__}
    return {"inputs": checksums, "versions": versions}


def load(slug, kind):
    if RETRAIN:
        return None
    path = DIRECTORY / f"{slug}_{kind}.joblib"
    stamp = path.with_suffix(".json")
    if not path.exists() or not stamp.exists():
        return None
    try:
        saved = json.loads(stamp.read_text(encoding="utf-8"))
        valid = saved["signature"] == signature(slug, kind)
        valid = valid and saved["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError, KeyError):
        return None
    if not valid:
        return None
    # Artifacts are trusted project files, never user-uploaded pickles.
    return joblib.load(path)


def save(slug, kind, bundle):
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = DIRECTORY / f"{slug}_{kind}.joblib"
    tmp = path.with_suffix(".tmp")
    joblib.dump(bundle, tmp, compress=3)
    tmp.replace(path)
    path.with_suffix(".json").write_text(json.dumps({"signature": signature(slug, kind),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, indent=2), encoding="utf-8")
