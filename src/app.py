"""Flask API + front-end for the FIFA World Cup prediction model."""
import os
import sys
import json
import time
import threading
import subprocess
from flask import Flask, request, jsonify, send_from_directory

from geo import VENUES

SRC = os.path.dirname(__file__)
ROOT = os.path.join(SRC, "..")
WEB = os.path.join(ROOT, "web")
app = Flask(__name__, static_folder=None)

_eng = None
_league_eng = None

# Pipeline artifacts: file produced, the script that makes it, and how long
# before it should be considered stale (None = make-once, never stale by age).
ARTIFACTS = [
    {"key": "results", "path": "data/results.csv", "label": "Historical match results",
     "producer": "(download)", "max_age_h": None},
    {"key": "training_table", "path": "data/training_table.csv", "label": "Training feature table",
     "producer": "features.py", "max_age_h": None},
    {"key": "model", "path": "models/fifa_model.joblib", "label": "Trained model",
     "producer": "train.py", "max_age_h": None},
    {"key": "ensemble", "path": "models/fifa_model_ensemble.joblib", "label": "Ensemble model (GPU)",
     "producer": "train_ensemble.py", "max_age_h": None, "optional": True},
    {"key": "squads", "path": "data/squads.csv", "label": "World Cup squads",
     "producer": "fetch_squads_api.py", "max_age_h": 48},
    {"key": "withdrawals", "path": "data/withdrawals.json", "label": "Injury withdrawals",
     "producer": "detect_withdrawals.py", "max_age_h": 24},
    {"key": "squad_strength", "path": "data/squad_strength.json", "label": "Squad strength ratings",
     "producer": "squad_strength.py", "max_age_h": 48},
    {"key": "tournament_form", "path": "data/tournament_form.json", "label": "In-tournament form",
     "producer": "tournament_form.py", "max_age_h": 12},
    {"key": "wc_matches", "path": "data/wc_matches.json", "label": "Live WC results (folded into ratings)",
     "producer": "tournament_form.py", "max_age_h": 12, "optional": True},
    {"key": "fifa_rankings", "path": "data/fifa_rankings.json", "label": "FIFA World Ranking snapshot",
     "producer": "fifa_rankings.py", "max_age_h": None, "optional": True},
    {"key": "recent_stats", "path": "data/recent_stats.json", "label": "Recent WC 2026 form (goal-difference)",
     "producer": "recent_stats.py", "max_age_h": 12, "optional": True},
    {"key": "premier_league_results", "path": "data/club/premier_league_results.csv",
     "label": "Premier League historical results", "producer": "fetch_club_results.py",
     "max_age_h": None, "optional": True},
    {"key": "premier_league_model", "path": "models/premier_league_model.joblib",
     "label": "Premier League model", "producer": "train_league.py",
     "max_age_h": None, "optional": True},
    {"key": "la_liga_results", "path": "data/club/la_liga_results.csv",
     "label": "La Liga historical results", "producer": "fetch_club_results.py",
     "max_age_h": None, "optional": True},
    {"key": "la_liga_model", "path": "models/la_liga_model.joblib",
     "label": "La Liga model", "producer": "train_league.py",
     "max_age_h": None, "optional": True},
    {"key": "pl_players", "path": "data/players/premier_league_players.csv",
     "label": "Premier League player stats (transfer-value / scouting projects)",
     "producer": "projects/fetch_players.py", "max_age_h": None, "optional": True},
]

# Tournament-refresh sequence (ordered; squad_strength runs twice — once to feed
# the withdrawal scan, once to apply its result).
REFRESH_STEPS = [
    ("Fetch current squads", "fetch_squads_api.py"),
    ("Rate squads", "squad_strength.py"),
    ("Detect injury withdrawals", "detect_withdrawals.py"),
    ("Re-rate excluding withdrawn players", "squad_strength.py"),
    ("Fetch in-tournament form", "tournament_form.py"),
    ("Aggregate recent WC shooting form", "recent_stats.py"),
]

_refresh = {"running": False, "steps": [], "started": None, "finished": None, "error": None}
_refresh_lock = threading.Lock()


def eng():
    """Lazy-load the model so the server binds its port immediately
    (torch + ensemble take ~15s to import)."""
    global _eng
    if _eng is None:
        import predict
        _eng = predict
    return _eng


def league_eng():
    global _league_eng
    if _league_eng is None:
        import predict_league
        _league_eng = predict_league
    return _league_eng


# --- Premier League projects (transfer value / match outcome / scouting) ---
_pl_projects = {}


def pl_project(name):
    """Lazy-import a Premier League project module (trains on first use)."""
    if name not in _pl_projects:
        mod = __import__(f"projects.{name}", fromlist=["_"])
        _pl_projects[name] = mod
    return _pl_projects[name]


@app.route("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.route("/api/teams")
def teams():
    e = eng()
    wc = sorted(e._squad.keys())
    others = sorted(t for t in e._state["elo"] if t not in e._squad
                    and e._state["elo"][t] > 1600)
    return jsonify({"world_cup": wc, "others": others})


@app.route("/api/team/<team>")
def team(team):
    return jsonify(eng().team_analysis(team))


@app.route("/api/player")
def player():
    return jsonify(eng().player_analysis(request.args.get("team", ""),
                                         request.args.get("name", "")))


@app.route("/api/venues")
def venues():
    return jsonify([{"name": k, "city": v[0], "altitude": v[3], "roof": v[4],
                     "temp": v[5]} for k, v in VENUES.items()])


@app.route("/api/leagues")
def leagues():
    return jsonify(league_eng().available_leagues())


@app.route("/api/league_team")
def league_team():
    return jsonify(league_eng().team_analysis(
        request.args.get("league", ""), request.args.get("team", "")))


@app.route("/api/predict_league", methods=["POST"])
def api_predict_league():
    q = request.get_json(force=True)
    res = league_eng().predict(q["league"], q["home"], q["away"],
                               neutral=bool(q.get("neutral", False)))
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)


@app.route("/api/pl/projects")
def pl_projects_list():
    """Metadata for the Premier League project sub-tabs."""
    return jsonify([
        {"key": "transfer_value", "name": "Transfer value predictor",
         "blurb": "Linear model: player stats → market value. Plug in a player "
                  "and see what the model thinks they're worth vs their actual value.",
         "stack": ["requests", "pandas", "scikit-learn", "matplotlib"]},
        {"key": "match_outcome", "name": "Match outcome predictor",
         "blurb": "Random-forest / XGBoost on match features (form, goals, shots, "
                  "possession, home advantage) → win / draw / loss.",
         "stack": ["pandas", "scikit-learn", "XGBoost", "matplotlib"]},
        {"key": "player_scouting", "name": "Player scouting system",
         "blurb": "Nearest-neighbour similarity + K-means style clusters. Search a "
                  "player, see their closest statistical matches.",
         "stack": ["pandas", "scikit-learn", "matplotlib", "streamlit"]},
    ])


@app.route("/api/pl/transfer/players")
def pl_transfer_players():
    return jsonify(pl_project("transfer_value").list_players())


@app.route("/api/pl/transfer/predict")
def pl_transfer_predict():
    return jsonify(pl_project("transfer_value").predict_player(request.args.get("player", "")))


@app.route("/api/pl/transfer/coefficients")
def pl_transfer_coefficients():
    return jsonify(pl_project("transfer_value").coefficients())


@app.route("/api/pl/transfer/custom", methods=["POST"])
def pl_transfer_custom():
    return jsonify(pl_project("transfer_value").predict_custom(request.get_json(force=True)))


@app.route("/api/pl/outcome/teams")
def pl_outcome_teams():
    return jsonify(pl_project("match_outcome").teams())


@app.route("/api/pl/outcome/predict")
def pl_outcome_predict():
    res = pl_project("match_outcome").predict(request.args.get("home", ""),
                                              request.args.get("away", ""))
    return (jsonify(res), 400) if "error" in res else jsonify(res)


@app.route("/api/pl/outcome/importance")
def pl_outcome_importance():
    return jsonify(pl_project("match_outcome").feature_importance())


@app.route("/api/pl/scouting/players")
def pl_scouting_players():
    return jsonify(pl_project("player_scouting").list_players())


@app.route("/api/pl/scouting/similar")
def pl_scouting_similar():
    res = pl_project("player_scouting").similar(request.args.get("player", ""))
    return (jsonify(res), 400) if "error" in res else jsonify(res)


@app.route("/api/pl/scouting/clusters")
def pl_scouting_clusters():
    return jsonify(pl_project("player_scouting").clusters())


@app.route("/api/sentiment/<team>")
def sentiment(team):
    from sentiment import team_sentiment
    s, heads = team_sentiment(team)
    return jsonify({"team": team, "sentiment": s, "headlines": heads[:8]})


@app.route("/api/predict", methods=["POST"])
def api_predict():
    q = request.get_json(force=True)
    home, away, venue = q["home"], q["away"], q.get("venue") or None

    # live data, fetched fresh on every click (manual overrides win if given)
    from live import gather
    lat, lon = (VENUES[venue][1], VENUES[venue][2]) if venue in VENUES else (None, None)
    lv = gather(home, away, venue, lat, lon)
    w = lv["weather"]
    temp = q.get("temp") or (w["temp_c"] if w else None)
    humidity = q.get("humidity") or (w["humidity_class"] if w else None)

    res = eng().predict(
        home, away, venue=venue,
        neutral=bool(q.get("neutral", True)),
        is_wc=bool(q.get("is_wc", True)),
        temp=temp, humidity=humidity,
        sentiment_home=lv["sentiment"]["home"],
        sentiment_away=lv["sentiment"]["away"],
        sentiment_mode=q.get("sentiment_mode", "high"),
    )
    res["live"] = {
        "weather_live": w is not None,
        "weather": w,
        "sentiment": lv["sentiment"],
        "breakdown": lv["breakdown"],
        "injuries": lv["injuries"],
        "headlines": lv["headlines"],
    }
    return jsonify(res)


def _artifact_status():
    now = time.time()
    items, any_stale, any_missing = [], False, False
    for a in ARTIFACTS:
        fp = os.path.join(ROOT, a["path"])
        exists = os.path.exists(fp)
        age_h = (now - os.path.getmtime(fp)) / 3600 if exists else None
        if not exists:
            state = "missing"
        elif a["max_age_h"] is not None and age_h > a["max_age_h"]:
            state = "stale"
        else:
            state = "ok"
        if state == "missing" and not a.get("optional"):
            any_missing = True
        if state == "stale":
            any_stale = True
        items.append({**{k: a[k] for k in ("key", "label", "producer", "max_age_h")},
                      "exists": exists, "state": state,
                      "age_hours": round(age_h, 1) if age_h is not None else None,
                      "optional": a.get("optional", False)})
    return {"artifacts": items, "any_stale": any_stale, "any_missing": any_missing}


@app.route("/api/status")
def status():
    return jsonify({**_artifact_status(), "refresh": _refresh})


def _run_refresh():
    steps = [{"name": n, "script": s, "state": "pending", "tail": ""} for n, s in REFRESH_STEPS]
    with _refresh_lock:
        _refresh.update(running=True, steps=steps, started=time.time(),
                        finished=None, error=None)
    try:
        for st in steps:
            st["state"] = "running"
            p = subprocess.run([sys.executable, st["script"]], cwd=SRC,
                               capture_output=True, text=True, timeout=900)
            out = (p.stdout or "") + (p.stderr or "")
            st["tail"] = "\n".join(out.strip().splitlines()[-4:])
            if p.returncode != 0:
                st["state"] = "failed"
                raise RuntimeError(f"{st['script']} exited {p.returncode}")
            st["state"] = "done"
        # hot-reload in-memory data so predictions use the fresh files
        eng().reload()
        import live
        live.reload()
    except Exception as e:
        with _refresh_lock:
            _refresh["error"] = str(e)
    finally:
        with _refresh_lock:
            _refresh.update(running=False, finished=time.time())


@app.route("/api/refresh", methods=["POST"])
def refresh():
    with _refresh_lock:
        if _refresh["running"]:
            return jsonify({"started": False, "reason": "already running"}), 409
    threading.Thread(target=_run_refresh, daemon=True).start()
    return jsonify({"started": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False,
            threaded=True)
