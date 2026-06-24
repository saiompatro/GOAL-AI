"""Player-level goalscorer (real data) and assist (estimated) predictions.

Goalscorers are grounded in real results: each squad player's international goals
(`data/goalscorers.csv`, the open martj42 dataset) over his appearances (`caps`)
give a regularised goals-per-game rate. The match model's expected goals for each
team (the Poisson lambda from predict.py) are then distributed across the squad in
proportion to those rates, and P(player scores >=1) = 1 - exp(-player_lambda).

Assists are NOT in the free dataset (goalscorers.csv has no assist column), so the
assist numbers are an explicit *estimate* from position + experience + goal
involvement, clearly flagged as such. Don't read them as measured rates.

Shrinkage (SHRINK) regularises small samples: a striker with 2 goals in 3 caps is
pulled toward the mean instead of being treated as a 0.67-per-game machine — this
keeps the picks honest and avoids overfitting to a handful of appearances.
"""
import os
import re
import json
import math
import unicodedata
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SHRINK = 6                  # pseudo-appearances pulling rare scorers toward 0
ASSIST_FRACTION = 0.75      # ~3 in 4 goals are assisted; scales estimated assists
POS_CREATE = {"FW": 1.0, "MF": 0.85, "DF": 0.30, "GK": 0.0}  # assist propensity by position
TSTATS = os.path.join(DATA, "player_tournament_stats.json")
WC_SHRINK = 3               # pseudo-matches damping a tiny WC sample
TFORM_W = 0.5               # how hard current-WC scoring form bends a player's scorer share

_goals = _squads = _tstats = None


def _norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z ]", " ", s.lower()).strip()


def _load():
    global _goals, _squads, _tstats
    g = pd.read_csv(os.path.join(DATA, "goalscorers.csv"))
    g = g[~g["own_goal"].fillna(False)]
    g["n"], g["tn"] = g["scorer"].map(_norm), g["team"].map(_norm)
    goals = g.groupby(["tn", "n"]).size().rename("goals")
    pens = g[g["penalty"].fillna(False)].groupby(["tn", "n"]).size().rename("pens")
    _goals = pd.concat([goals, pens], axis=1).fillna(0)
    _squads = pd.read_csv(os.path.join(DATA, "squads_rated.csv"))
    _tstats = json.load(open(TSTATS, encoding="utf-8")) if os.path.exists(TSTATS) else {}


def tournament_stats(team, player):
    """Hand-maintained current-tournament stats for a key starter, or None.
    Returns {"wc": {...}, "other": {...}} with goals/assists/shots/shots_on_target
    (any may be null = not available). See data/player_tournament_stats.json."""
    return (_tstats.get(team) or {}).get(player)


_load()


def reload():
    _load()


def _team_players(team):
    """Per-player goals/pens/caps/position/regularised rate for a team's squad."""
    s = _squads[_squads["team"] == team]
    tn = _norm(team)
    rows = []
    for r in s.itertuples():
        n = _norm(r.player)
        goals = int(_goals["goals"].get((tn, n), 0)) if (tn, n) in _goals.index else 0
        pens = int(_goals["pens"].get((tn, n), 0)) if (tn, n) in _goals.index else 0
        caps = int(pd.to_numeric(r.caps, errors="coerce") or 0)
        apps = max(caps, goals, 1)
        intl_rate = goals / (apps + SHRINK)                  # regularised career goals/game
        # bend the scorer share toward how the player is actually scoring in this WC.
        # distribution in predict_match is relative within the squad, so this lifts an
        # in-form scorer's anytime-scorer/parlay odds. Display rate stays intl_rate.
        rate = intl_rate
        ts = tournament_stats(team, r.player)
        wc = (ts or {}).get("wc")
        if wc and wc.get("matches") and wc.get("goals") is not None:
            wc_rate = wc["goals"] / (wc["matches"] + WC_SHRINK)
            rate = intl_rate + TFORM_W * wc_rate
        rows.append({"player": r.player, "position": str(r.position), "caps": caps,
                     "goals": goals, "pens": pens, "rate": rate, "intl_rate": intl_rate,
                     "wc": wc})
    return rows


def match_markets(lam_h, lam_a, prob):
    """Derived match-level betting markets, exact under the model's independent-
    Poisson goals assumption (the same one behind the scoreline grid)."""
    e = math.exp
    L = lam_h + lam_a
    p0, p1, p2 = e(-L), e(-L) * L, e(-L) * L ** 2 / 2
    m = {
        "over_1_5": 1 - p0 - p1,
        "over_2_5": 1 - p0 - p1 - p2,
        "over_3_5": 1 - p0 - p1 - p2 - e(-L) * L ** 3 / 6,
        "under_2_5": p0 + p1 + p2,
        "btts": (1 - e(-lam_h)) * (1 - e(-lam_a)),
        "btts_no": 1 - (1 - e(-lam_h)) * (1 - e(-lam_a)),
        "home_clean_sheet": e(-lam_a),
        "away_clean_sheet": e(-lam_h),
        "home_win_to_nil": (1 - e(-lam_h)) * e(-lam_a),
        "away_win_to_nil": (1 - e(-lam_a)) * e(-lam_h),
    }
    if prob:
        m["dc_home_or_draw"] = prob["home_win"] + prob["draw"]
        m["dc_away_or_draw"] = prob["away_win"] + prob["draw"]
        m["dc_either_team"] = prob["home_win"] + prob["away_win"]
    return {k: round(v, 3) for k, v in m.items()}


def predict_match(home, away, lam_h, lam_a, prob=None, top_n=6):
    """Goalscorer (real) + assist (estimated) lists for both teams, plus parlays.
    lam_h/lam_a are the match model's expected goals; prob is the win/draw/loss dict."""
    out = {"available": False}
    if _squads[_squads["team"].isin([home, away])].empty:
        out["note"] = "player markets need World Cup squad data for both teams"
        return out

    def side(team, lam):
        ps = _team_players(team)
        tot_rate = sum(p["rate"] for p in ps)
        pen_taker = max(ps, key=lambda p: p["pens"])["player"] if any(p["pens"] for p in ps) else None
        # assist estimate weight: position propensity x experience x slight goal involvement
        for p in ps:
            exp_factor = 0.5 + min(p["caps"], 80) / 80 * 0.5
            p["awt"] = POS_CREATE.get(p["position"], 0.4) * exp_factor * (1 + 0.02 * p["goals"])
        tot_awt = sum(p["awt"] for p in ps) or 1.0
        exp_assists = lam * ASSIST_FRACTION
        scorers, assisters = [], []
        for p in ps:
            p_score = 1 - math.exp(-(lam * p["rate"] / tot_rate)) if tot_rate else 0.0
            p_assist = 1 - math.exp(-(exp_assists * p["awt"] / tot_awt))
            if p["rate"] > 0:
                scorers.append({"player": p["player"], "position": p["position"],
                                "goals_intl": p["goals"], "caps": p["caps"],
                                "p_score": round(p_score, 3),
                                "penalty_taker": p["player"] == pen_taker,
                                "wc": p.get("wc")})  # current-tournament form, if tracked
            assisters.append({"player": p["player"], "position": p["position"],
                              "caps": p["caps"], "p_assist": round(p_assist, 3)})
        scorers.sort(key=lambda x: -x["p_score"])
        assisters.sort(key=lambda x: -x["p_assist"])
        return scorers[:top_n], assisters[:top_n], pen_taker

    hs, ha, h_pen = side(home, lam_h)
    as_, aa, a_pen = side(away, lam_a)

    # derived match markets + betting parlays. Legs are multiplied assuming
    # independence; real same-game parlays are correlated, so treat as a guide.
    mk = match_markets(lam_h, lam_a, prob) if prob else {}
    fav = home if (prob and prob["home_win"] >= prob["away_win"]) else (away if prob else None)
    fav_p = prob[("home_win" if fav == home else "away_win")] if prob else 0.0
    fav_top = (hs[0] if fav == home else as_[0]) if (hs and as_ and fav) else (hs[0] if hs else None)
    fav_cs = mk.get("home_clean_sheet" if fav == home else "away_clean_sheet", 0.0)
    fav_dc = mk.get("dc_home_or_draw" if fav == home else "dc_away_or_draw", 0.0)

    def add(parlays, name, legs, p):
        if p and p > 0:
            parlays.append({"name": name, "legs": legs, "p": round(p, 3)})

    parlays = []
    if hs and as_:
        add(parlays, "Anytime scorer double",
            [f"{hs[0]['player']} ({home}) to score", f"{as_[0]['player']} ({away}) to score"],
            hs[0]["p_score"] * as_[0]["p_score"])
    if fav_top and fav:
        add(parlays, "Scorer + match result",
            [f"{fav_top['player']} to score", f"{fav} to win"], fav_top["p_score"] * fav_p)
    if hs and ha:
        assister = next((a for a in ha if a["player"] != hs[0]["player"]), None)
        if assister:
            add(parlays, "Scorer + assist (estimated)",
                [f"{hs[0]['player']} ({home}) to score",
                 f"{assister['player']} ({home}) to assist (est.)"],
                hs[0]["p_score"] * assister["p_assist"])
    if mk and fav:
        add(parlays, "Result + Over 2.5 goals",
            [f"{fav} to win", "Over 2.5 goals"], fav_p * mk["over_2_5"])
        add(parlays, "Result + both teams to score",
            [f"{fav} to win", "Both teams to score"], fav_p * mk["btts"])
        add(parlays, "Over 2.5 + both teams to score",
            ["Over 2.5 goals", "Both teams to score"], mk["over_2_5"] * mk["btts"])
        add(parlays, "Double chance + Over 1.5",
            [f"{fav} or draw", "Over 1.5 goals"], fav_dc * mk["over_1_5"])
        add(parlays, "Win to nil",
            [f"{fav} to win", f"{away if fav == home else home} not to score"],
            mk["home_win_to_nil" if fav == home else "away_win_to_nil"])
    if fav_top and mk and fav:
        add(parlays, "Star scorer + Over 2.5",
            [f"{fav_top['player']} to score", "Over 2.5 goals"], fav_top["p_score"] * mk["over_2_5"])

    return {
        "available": True,
        "p_any_goal": round(1 - math.exp(-(lam_h + lam_a)), 3),
        "penalty_takers": {"home": h_pen, "away": a_pen},
        "scorers": {"home": hs, "away": as_},
        "assists_estimated": {"home": ha, "away": aa},
        "assist_note": "Estimated from position + experience + goal involvement — "
                       "the free dataset has no assist data, so treat as a heuristic.",
        "match_markets": mk,
        "parlays": parlays,
    }


if __name__ == "__main__":
    # self-check: a player scoring in the current WC must outrank his career rate
    # in the squad's scorer distribution (so parlays reflect tournament form).
    ps = {p["player"]: p for p in _team_players("Argentina")}
    messi = ps.get("Lionel Messi")
    if messi and messi.get("wc") and messi["wc"].get("goals"):
        assert messi["rate"] > messi["intl_rate"], "WC form should lift scorer share"
        print(f"OK: Messi rate {messi['rate']:.3f} > career {messi['intl_rate']:.3f} "
              f"(WC {messi['wc']['goals']}g/{messi['wc']['matches']}m)")
    else:
        print("No WC stats loaded for Messi — check data/player_tournament_stats.json")
    tracked = [(t, p) for t, ps in (_tstats or {}).items() if t != "_meta" for p in ps]
    print(f"\n{len(tracked)} tracked players across {len({t for t, _ in tracked})} teams:")
    for team, player in tracked:
        wc = (_tstats[team][player].get("wc") or {})
        print(f"  {team:13s} {player:20s} WC "
              f"g={wc.get('goals')} a={wc.get('assists')} "
              f"sh={wc.get('shots')} sot={wc.get('shots_on_target')}")
