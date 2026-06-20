"""Match prediction engine.

Effective team rating blends two real-results signals:
  70% international Elo (from 150 yrs of national-team matches)
  30% squad club strength (players' club Elo from league/UEFA results),
      rescaled onto the international Elo scale across the 48 WC squads.
Features then add form, morale (momentum + optional live news sentiment),
rest, and venue climate mismatches before the trained GBMs produce
P(win/draw/loss) and a Poisson scoreline distribution.
"""
import os
import json
import math
import joblib
import numpy as np
import pandas as pd
from datetime import date

from geo import COUNTRY, VENUES, haversine_km
from features import country_climate, country_coords

BASE = os.path.join(os.path.dirname(__file__), "..")
# Serving stability: four ML runtimes share this process, and inference runs in
# Flask worker threads. Duplicate OpenMP runtimes / CUDA-in-thread inference
# cause hard native crashes, so allow the duplicate and keep inference on CPU.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "4")
import ensemble_model  # noqa: F401  (needed to unpickle StackEnsemble/TorchMLP)
_ens_path = os.path.join(BASE, "models", "fifa_model_ensemble.joblib")
if os.path.exists(_ens_path):
    _model = joblib.load(_ens_path)
    if hasattr(_model["clf"], "members"):
        for _name, _m in _model["clf"].members.items():
            if _name == "xgb":
                _m.set_params(device="cpu", n_jobs=1)
            elif _name == "lgb":
                _m.set_params(n_jobs=1)
else:
    _model = joblib.load(os.path.join(BASE, "models", "fifa_model.joblib"))
SQUAD_W = 0.30
_state = _squad = _tform = None
_a = _b = None


def _load_data():
    """(Re)load the data artifacts produced by the offline pipeline. Called at
    import and again by reload() after the data-refresh button reruns scripts."""
    global _state, _squad, _tform, _a, _b
    _state = json.load(open(os.path.join(BASE, "data", "current_state.json")))
    _squad = json.load(open(os.path.join(BASE, "data", "squad_strength.json")))
    tpath = os.path.join(BASE, "data", "tournament_form.json")
    _tform = json.load(open(tpath, encoding="utf-8")) if os.path.exists(tpath) else {}
    # rescale squad club-Elo onto international Elo scale (least squares over WC teams)
    pairs = [(s, _state["elo"][t]) for t, s in _squad.items() if t in _state["elo"]]
    sx = np.array([p[0] for p in pairs]); sy = np.array([p[1] for p in pairs])
    _a, _b = np.polyfit(sx, sy, 1)


_load_data()


def reload():
    """Re-read data files so a running server picks up a fresh pipeline run."""
    _load_data()


def effective_elo(team):
    elo = _state["elo"].get(team, 1500.0)
    if team in _squad:
        squad_scaled = _a * _squad[team] + _b
        return (1 - SQUAD_W) * elo + SQUAD_W * squad_scaled
    return elo


def _form(team):
    h = _state["hist"].get(team, [])
    last5, last10 = h[-5:], h[-10:]
    ppg5 = (sum(x[0] for x in last5) / len(last5) * 3) if last5 else 1.0
    gd10 = (sum(x[1] for x in last10) / len(last10)) if last10 else 0.0
    return ppg5, gd10


def _rest(team, match_date=None):
    ld = _state["last_date"].get(team)
    if not ld:
        return 30
    d = (match_date or date.today()) - date.fromisoformat(ld)
    return min(max(d.days, 0), 60)


# Sentiment-priority layer: how strongly live news sentiment shifts the final
# probabilities, applied on top of the trained model (which keeps Elo, form,
# climate etc.). Calibration anchor: a 1-SD Elo edge (~250 pts) is worth ~1.45
# in log-odds of winning. In "high" mode a full sentiment split (+1 vs -1)
# shifts log-odds by 2*0.85 = 1.7 -- MORE than the typical Elo edge, per user
# requirement, while Elo still contributes through the model underneath.
# No retraining is possible for this layer: historical news doesn't exist for
# 37k past matches, so the weight is a stated prior, not a fitted parameter.
SENTIMENT_K = {"off": 0.0, "normal": 0.35, "high": 0.85}

# In-tournament form is the single most important factor once it is active.
# It only activates when BOTH teams have played >= 5 World Cup matches (see
# tournament_form.py). form_score is in [-1, 1], so a full gap (2.0) shifts win
# log-odds by TFORM_K * 2 = 2.4 -- larger than sentiment (1.7) and Elo (~1.45),
# i.e. how a team is actually doing in this World Cup dominates the prediction.
TFORM_K = 1.2


def predict(home, away, venue=None, neutral=True, is_wc=True,
            temp=None, humidity=None, sentiment_home=0.0, sentiment_away=0.0,
            sentiment_mode="high"):
    """venue: a key of geo.VENUES, or None = generic neutral ground."""
    if venue and venue in VENUES:
        _, vlat, vlon, valt, roof, vtemp, vhum = VENUES[venue]
    else:
        vlat, vlon, valt, roof, vtemp, vhum = 40.0, -90.0, 100, False, 26, 1
    if temp is not None:
        vtemp = float(temp)
    if humidity is not None:
        vhum = int(humidity)
    eff_temp = vtemp - (6 if roof else 0)

    def side(team, is_home):
        tt, th, ta = country_climate(team)
        tco = country_coords(team) or (45.0, 10.0)
        travel = haversine_km(tco[0], tco[1], vlat, vlon) / 1000.0
        dlon = ((vlon - tco[1] + 180) % 360) - 180
        tz_east = max(0.0, dlon) / 15.0
        if is_home and not neutral:
            travel, tz_east = 0.0, 0.0
        ppg5, gd10 = _form(team)
        return {"ppg5": ppg5, "gd10": gd10, "rest": _rest(team),
                "att": _state["att"].get(team, 1.3), "dfn": _state["dfn"].get(team, 1.3),
                "streak": min(_state["streak"].get(team, 0), 12),
                "exp": _state["big_exp"].get(team, 0.0),
                "heat": max(0.0, eff_temp - tt), "hum": max(0, vhum - th),
                "alt": max(0.0, valt - ta) / 1000.0, "travel": travel, "tz_east": tz_east}

    fh, fa = side(home, True), side(away, False)
    eh, ea = effective_elo(home), effective_elo(away)

    meetings = _state["h2h"].get("|".join(sorted([home, away])), [])
    if meetings:
        pts = [(r if first == home else 1 - r) for first, r, _ in meetings[-10:]]
        gds = [(g if first == home else -g) for first, _, g in meetings[-10:]]
        h2h_rate, h2h_gd = sum(pts) / len(pts), sum(gds) / len(gds)
    else:
        h2h_rate, h2h_gd = 0.5, 0.0
    mor_h = _state["morale"].get(home, 0.0) + 0.5 * sentiment_home
    mor_a = _state["morale"].get(away, 0.0) + 0.5 * sentiment_away
    home_adv = 0 if neutral else 60

    x = pd.DataFrame([{
        "elo_diff": (eh + home_adv) - ea,
        "ppg5_diff": fh["ppg5"] - fa["ppg5"], "gd10_diff": fh["gd10"] - fa["gd10"],
        "morale_diff": mor_h - mor_a, "rest_diff": fh["rest"] - fa["rest"],
        "att_vs_def": fh["att"] - fa["dfn"], "def_vs_att": fh["dfn"] - fa["att"],
        "streak_diff": fh["streak"] - fa["streak"], "exp_diff": fh["exp"] - fa["exp"],
        "h2h_rate": h2h_rate, "h2h_gd": h2h_gd,
        "heat_diff": fh["heat"] - fa["heat"], "hum_diff": fh["hum"] - fa["hum"],
        "alt_diff": fh["alt"] - fa["alt"], "travel_diff": fh["travel"] - fa["travel"],
        "tz_east_diff": fh["tz_east"] - fa["tz_east"],
        "neutral": int(neutral), "is_wc": int(is_wc),
    }])[_model["features"]]

    p_away, p_draw, p_home = _model["clf"].predict_proba(x)[0]
    lam_h = float(_model["goals_home"].predict(x)[0])
    lam_a = float(_model["goals_away"].predict(x)[0])

    # sentiment-priority adjustment in log-odds space
    k = SENTIMENT_K.get(sentiment_mode, SENTIMENT_K["high"])
    sdiff = float(sentiment_home) - float(sentiment_away)
    base_prob = {"home_win": round(float(p_home), 3), "draw": round(float(p_draw), 3),
                 "away_win": round(float(p_away), 3)}
    if k and sdiff:
        lg = np.log(np.array([p_away, p_draw, p_home]) + 1e-12)
        lg[2] += k * sdiff
        lg[0] -= k * sdiff
        e = np.exp(lg - lg.max())
        p_away, p_draw, p_home = e / e.sum()
        gadj = math.exp(0.2 * k * sdiff)
        lam_h *= gadj
        lam_a /= gadj

    # in-tournament form layer (dominant, only when both teams have >= 5 WC matches)
    tf_h, tf_a = _tform.get(home), _tform.get(away)
    tform_active = bool(tf_h and tf_a and tf_h.get("eligible") and tf_a.get("eligible"))
    prob_before_tform = {"home_win": round(float(p_home), 3), "draw": round(float(p_draw), 3),
                         "away_win": round(float(p_away), 3)}
    if tform_active:
        fdiff = tf_h["form_score"] - tf_a["form_score"]
        lg = np.log(np.array([p_away, p_draw, p_home]) + 1e-12)
        lg[2] += TFORM_K * fdiff
        lg[0] -= TFORM_K * fdiff
        e = np.exp(lg - lg.max())
        p_away, p_draw, p_home = e / e.sum()
        gadj = math.exp(0.25 * TFORM_K * fdiff)
        lam_h *= gadj
        lam_a /= gadj

    # Poisson scoreline grid
    def pois(lam, k):
        return math.exp(-lam) * lam ** k / math.factorial(k)
    grid = [(i, j, pois(lam_h, i) * pois(lam_a, j)) for i in range(7) for j in range(7)]
    grid.sort(key=lambda g: -g[2])

    return {
        "home": home, "away": away, "venue": venue,
        "prob": {"home_win": round(float(p_home), 3), "draw": round(float(p_draw), 3),
                 "away_win": round(float(p_away), 3)},
        "expected_goals": {"home": round(lam_h, 2), "away": round(lam_a, 2)},
        "top_scorelines": [{"score": f"{i}-{j}", "p": round(p, 3)} for i, j, p in grid[:5]],
        "ratings": {"home_intl_elo": round(_state["elo"].get(home, 1500), 1),
                    "away_intl_elo": round(_state["elo"].get(away, 1500), 1),
                    "home_effective": round(eh, 1), "away_effective": round(ea, 1),
                    "home_squad_club_elo": round(_squad.get(home, 0), 1),
                    "away_squad_club_elo": round(_squad.get(away, 0), 1)},
        "morale": {"home": round(mor_h, 3), "away": round(mor_a, 3)},
        "sentiment_layer": {"mode": sentiment_mode, "k": k,
                            "input": {"home": round(float(sentiment_home), 3),
                                      "away": round(float(sentiment_away), 3)},
                            "prob_before_sentiment": base_prob},
        "tournament_form": {
            "active": tform_active,
            "min_matches": 5,
            "prob_before": prob_before_tform if tform_active else None,
            "home": tf_h, "away": tf_a,
            "note": ("dominant factor applied" if tform_active else
                     "inactive — both teams need >= 5 World Cup matches (from the QF stage)"),
        },
        "h2h": {"meetings": len(meetings), "home_rate": round(h2h_rate, 2),
                "home_gd": round(h2h_gd, 2)},
        "form_extra": {"home_streak": fh["streak"], "away_streak": fa["streak"],
                       "home_attack": round(fh["att"], 2), "away_attack": round(fa["att"], 2),
                       "home_defense": round(fh["dfn"], 2), "away_defense": round(fa["dfn"], 2),
                       "home_jetlag_tz_east": round(fh["tz_east"], 1),
                       "away_jetlag_tz_east": round(fa["tz_east"], 1)},
        "conditions": {"temp_c": vtemp, "humidity": vhum, "altitude_m": valt,
                       "roof": bool(roof),
                       "home_heat_mismatch": round(fh["heat"], 1),
                       "away_heat_mismatch": round(fa["heat"], 1),
                       "home_travel_1000km": round(fh["travel"], 2),
                       "away_travel_1000km": round(fa["travel"], 2)},
    }


if __name__ == "__main__":
    r = predict("Mexico", "Norway", venue="Estadio Azteca (Mexico City)", neutral=False)
    print(json.dumps(r, indent=1))
