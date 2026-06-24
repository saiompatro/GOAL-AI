"""Leak-free backtest of the match model against the live WC 2026 results.

For each finished match (in date order) we predict using ONLY the matches played
before it, folded into the base ratings exactly as the live app does. The recent-
form and in-tournament-form layers are switched off, because both are computed
from these same results — leaving them on would let the model peek at the answer.
Reports accuracy + log-loss vs the actual outcomes, with a per-match table.

# ponytail: one-off analysis script, not wired into the app; run directly.
"""
import os
import json
import math
import tempfile

import numpy as np

import predict
import live_ratings
import recent_stats

base = json.load(open(os.path.join(predict.BASE, "data", "current_state.json"), encoding="utf-8"))
matches = sorted((m for m in json.load(open(live_ratings.WC_MATCHES, encoding="utf-8"))
                  if m.get("home_goals") is not None and m.get("away_goals") is not None),
                 key=lambda m: (m["date"], m["home"]))

# disable layers that would leak same-match info
predict._tform = {}
recent_stats._team = {}


def res(gh, ga):
    return "H" if gh > ga else ("A" if ga > gh else "D")


def set_state(prefix):
    """Fold only the prior matches into the base ratings, like live_ratings does."""
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(prefix, f)
    f.close()
    s, _ = live_ratings.apply_live_results(base, path=f.name)
    os.unlink(f.name)
    predict._state = s
    pairs = [(sv, s["elo"][t]) for t, sv in predict._squad.items() if t in s["elo"]]
    predict._a, predict._b = np.polyfit([p[0] for p in pairs], [p[1] for p in pairs], 1)


ll = correct = chalk = n = 0
rows = []
for i, m in enumerate(matches):
    gh, ga = int(m["home_goals"]), int(m["away_goals"])
    set_state(matches[:i])                       # only matches strictly before this one
    r = predict.predict(m["home"], m["away"], neutral=True, is_wc=True)
    p = r["prob"]
    probs = {"H": p["home_win"], "D": p["draw"], "A": p["away_win"]}
    act, pred = res(gh, ga), max(probs, key=probs.get)
    fav = "H" if r["ratings"]["home_effective"] >= r["ratings"]["away_effective"] else "A"
    ll += -math.log(max(probs[act], 1e-12))
    correct += pred == act
    chalk += fav == act
    n += 1
    eg = r["expected_goals"]
    rows.append((m["date"], m["home"], m["away"], f"{gh}-{ga}", act, pred,
                 probs[act], f"{eg['home']:.1f}-{eg['away']:.1f}", pred == act))

print(f"{'date':<11}{'match':<34}{'res':>5}{'pred':>5}{'p(act)':>8}{'xG':>9}  ok")
print("-" * 78)
for d, h, a, sc, act, pred, pa, eg, ok in rows:
    print(f"{d:<11}{(h+' v '+a):<28}{sc:>6}{act:>5}{pred:>5}{pa:>8.2f}{eg:>9}  {'Y' if ok else '.'}")
print("-" * 78)
print(f"matches:           {n}")
print(f"model accuracy:    {correct/n:.3f}  ({correct}/{n})")
print(f"  rating-favorite: {chalk/n:.3f}  ({chalk}/{n})  [pick higher effective-Elo, no draws]")
print(f"model log-loss:    {ll/n:.3f}   [held-out training set was 0.871]")
