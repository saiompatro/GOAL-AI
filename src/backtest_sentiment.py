"""Compare sentiment modes (off / normal / high) on the live WC 2026 results.

Same leak-free setup as backtest_wc.py (each match predicted from only the matches
before it; recent-form and in-tournament-form layers off). For each match we fetch
each team's CURRENT news sentiment and predict under all three modes, so the only
thing that changes is SENTIMENT_K. Reports accuracy + log-loss per mode and how far
the probabilities actually move.

Caveat: sentiment is today's news, not the headlines as of each match date (those
don't exist), so this shows the EFFECT OF THE MODE, not a time-valid backtest.

# ponytail: one-off analysis script; run directly.
"""
import os
import json
import math
import tempfile

import numpy as np

import predict
import live_ratings
import recent_stats
import sentiment

base = json.load(open(os.path.join(predict.BASE, "data", "current_state.json"), encoding="utf-8"))
matches = sorted((m for m in json.load(open(live_ratings.WC_MATCHES, encoding="utf-8"))
                  if m.get("home_goals") is not None and m.get("away_goals") is not None),
                 key=lambda m: (m["date"], m["home"]))

predict._tform = {}                                    # disable leaking layers
recent_stats._team = {}

MODES = ["off", "normal", "high"]
_sent = {}


def sent(team):
    if team not in _sent:
        _sent[team] = sentiment.team_sentiment(team)[0]
    return _sent[team]


def res(gh, ga):
    return "H" if gh > ga else ("A" if ga > gh else "D")


def set_state(prefix):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(prefix, f)
    f.close()
    s, _ = live_ratings.apply_live_results(base, path=f.name)
    os.unlink(f.name)
    predict._state = s
    pairs = [(sv, s["elo"][t]) for t, sv in predict._squad.items() if t in s["elo"]]
    predict._a, predict._b = np.polyfit([p[0] for p in pairs], [p[1] for p in pairs], 1)


agg = {m: {"correct": 0, "ll": 0.0} for m in MODES}
move = 0.0          # avg |P(home) high - normal|
flips = 0           # predictions where the argmax pick differs high vs normal
rows = []
n = 0
print(f"fetching sentiment for ~{len({t for m in matches for t in (m['home'], m['away'])})} teams...")
for i, m in enumerate(matches):
    gh, ga = int(m["home_goals"]), int(m["away_goals"])
    set_state(matches[:i])
    sh, sa = sent(m["home"]), sent(m["away"])
    act = res(gh, ga)
    per = {}
    for mode in MODES:
        r = predict.predict(m["home"], m["away"], neutral=True, is_wc=True,
                            sentiment_home=sh, sentiment_away=sa, sentiment_mode=mode)
        p = r["prob"]
        probs = {"H": p["home_win"], "D": p["draw"], "A": p["away_win"]}
        per[mode] = probs
        agg[mode]["correct"] += max(probs, key=probs.get) == act
        agg[mode]["ll"] += -math.log(max(probs[act], 1e-12))
    move += abs(per["high"]["H"] - per["normal"]["H"])
    flips += max(per["high"], key=per["high"].get) != max(per["normal"], key=per["normal"].get)
    n += 1
    rows.append((m["date"], m["home"], m["away"], f"{gh}-{ga}", act, sh, sa,
                 per["normal"][act], per["high"][act]))

print(f"\n{'match':<34}{'res':>4}{'sHome sAway':>13}{'p(act)N':>9}{'p(act)H':>9}  Δ")
print("-" * 86)
for d, h, a, sc, act, sh, sa, pn, ph in rows:
    flag = "+" if ph > pn + 1e-9 else ("-" if ph < pn - 1e-9 else " ")
    print(f"{(h+' v '+a):<30}{sc:>5}{act:>4}{sh:>7.2f}{sa:>6.2f}{pn:>9.2f}{ph:>9.2f}  {flag}")
print("-" * 86)
print(f"matches: {n}   avg |ΔP(home)| high vs normal: {move/n:.3f}   pick flips: {flips}/{n}\n")
print(f"{'mode':>8}{'accuracy':>12}{'log-loss':>11}")
for mode in MODES:
    a = agg[mode]
    print(f"{mode:>8}{a['correct']/n:>9.3f}   {a['ll']/n:>9.3f}")
print("\n(p(act) = probability the model gave the ACTUAL result; higher = better. "
      "Δ '+' means high sentiment improved that match, '-' means it hurt.)")
