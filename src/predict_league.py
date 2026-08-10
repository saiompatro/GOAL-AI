"""Prediction engine for club-league matches (Premier League, and any league
added to fetch_club_results.LEAGUES). Same shape of output as predict.py's
World Cup engine (prob / expected_goals / top_scorelines / match markets) so
the front-end can reuse its rendering, but the ratings come from
club_features.py's domestic-league Elo/form/morale/h2h instead of
international Elo + squad club-strength.
"""
import os
import json
import math
import joblib

from fetch_club_results import LEAGUES
from club_features import HOME_ADV

BASE = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(BASE, "data", "club")
MODELS = os.path.join(BASE, "models")

_state = {}
_models = {}


def _load():
    for key in LEAGUES:
        spath = os.path.join(DATA, f"{key}_state.json")
        mpath = os.path.join(MODELS, f"{key}_model.joblib")
        if os.path.exists(spath) and os.path.exists(mpath):
            _state[key] = json.load(open(spath, encoding="utf-8"))
            _models[key] = joblib.load(mpath)


_load()


def reload():
    _load()


def available_leagues():
    return [{"key": key, "name": info["name"], "country": info["country"],
            "teams": _state[key]["current_teams"], "season": _state[key]["current_season"]}
            for key, info in LEAGUES.items() if key in _state]


def team_analysis(league_key, team):
    st = _state.get(league_key)
    if not st or team not in st["elo"]:
        return {"error": f"unknown team '{team}' for league '{league_key}'"}
    hist = st["hist"].get(team, [])
    results = [("W" if r > 0.5 else ("D" if r == 0.5 else "L")) for r, _ in hist]
    return {"team": team, "league": league_key, "elo": round(st["elo"][team], 1),
           "morale": round(st["morale"].get(team, 0.0), 3),
           "attack": round(st["att"].get(team, 1.3), 2),
           "defense": round(st["dfn"].get(team, 1.3), 2),
           "streak": st["streak"].get(team, 0),
           "recent_form": results[-10:]}


def predict(league_key, home, away, neutral=False):
    st = _state.get(league_key)
    model = _models.get(league_key)
    if st is None or model is None:
        return {"error": f"unknown or unready league '{league_key}'"}
    if home not in st["elo"] or away not in st["elo"]:
        return {"error": f"unknown team for league '{league_key}'"}

    eh, ea = st["elo"][home], st["elo"][away]
    home_adv = 0 if neutral else HOME_ADV
    hist = st["hist"]

    def feats(team):
        f = hist.get(team, [])
        last5, last10 = f[-5:], f[-10:]
        ppg5 = (sum(x[0] for x in last5) / len(last5)) * 3 if last5 else 1.0
        gd10 = (sum(x[1] for x in last10) / len(last10)) if last10 else 0.0
        return ppg5, gd10

    ppg5_h, gd10_h = feats(home)
    ppg5_a, gd10_a = feats(away)

    def h2h_key(a, b):
        return "|".join(sorted([a, b]))
    meetings = st["h2h"].get(h2h_key(home, away), [])
    if meetings:
        pts = [(r if first == home else 1 - r) for first, r, _ in meetings[-10:]]
        gds = [(g if first == home else -g) for first, _, g in meetings[-10:]]
        h2h_rate, h2h_gd = sum(pts) / len(pts), sum(gds) / len(gds)
    else:
        h2h_rate, h2h_gd = 0.5, 0.0

    row = {
        "elo_diff": (eh + home_adv) - ea,
        "ppg5_diff": ppg5_h - ppg5_a, "gd10_diff": gd10_h - gd10_a,
        "morale_diff": st["morale"].get(home, 0.0) - st["morale"].get(away, 0.0),
        "att_vs_def": st["att"].get(home, 1.3) - st["dfn"].get(away, 1.3),
        "def_vs_att": st["dfn"].get(home, 1.3) - st["att"].get(away, 1.3),
        "streak_diff": min(st["streak"].get(home, 0), 12) - min(st["streak"].get(away, 0), 12),
        "h2h_rate": h2h_rate, "h2h_gd": h2h_gd,
    }
    import pandas as pd
    X = pd.DataFrame([row])[model["features"]]
    p_away, p_draw, p_home = model["clf"].predict_proba(X)[0]
    lam_h = max(0.15, float(model["goals_home"].predict(X)[0]))
    lam_a = max(0.15, float(model["goals_away"].predict(X)[0]))

    def pois(lam, k):
        return math.exp(-lam) * lam ** k / math.factorial(k)
    grid = [(i, j, pois(lam_h, i) * pois(lam_a, j)) for i in range(7) for j in range(7)]
    grid.sort(key=lambda g: -g[2])

    final_prob = {"home_win": float(p_home), "draw": float(p_draw), "away_win": float(p_away)}
    import scorers
    match_markets = scorers.match_markets(lam_h, lam_a, final_prob)

    return {
        "league": league_key, "home": home, "away": away,
        "prob": {"home_win": round(float(p_home), 3), "draw": round(float(p_draw), 3),
                "away_win": round(float(p_away), 3)},
        "expected_goals": {"home": round(lam_h, 2), "away": round(lam_a, 2)},
        "top_scorelines": [{"score": f"{i}-{j}", "p": round(p, 3)} for i, j, p in grid[:5]],
        "match_markets": match_markets,
        "ratings": {"home_elo": round(eh, 1), "away_elo": round(ea, 1)},
        "form": {"home": {"ppg5": round(ppg5_h, 2), "gd10": round(gd10_h, 2)},
                "away": {"ppg5": round(ppg5_a, 2), "gd10": round(gd10_a, 2)}},
        "h2h": {"home_win_rate": round(h2h_rate, 2), "avg_goal_diff": round(h2h_gd, 2),
               "meetings": len(meetings)},
    }
