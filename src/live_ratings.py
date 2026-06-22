"""Fold finished World Cup matches into the base ratings, live.

`current_state.json` is frozen at the last offline `features.py` build (pre-
tournament). As group- and knockout-stage games finish, their results should
immediately move each team's Elo, form, morale, head-to-head and attack/defence
ratings -- which is exactly what Elo is for, and unlike the gated tournament-form
layer it carries real signal from the very first match. This applies those updates
on top of the frozen state at load time, so every prediction reflects the latest
results, not just the >=5-match form layer.

Source: `data/wc_matches.json` (written by tournament_form.py from the
football-data.org feed -- no extra API call). Fails soft: if the file is missing
or empty, the base state is returned unchanged.

The per-match update mirrors `features.build_match_table` exactly -- same K_BASE
constant and same EWMA coefficients (0.7/0.3 morale, 0.85/0.15 attack-defence,
0.97 experience) -- with World Cup games treated as neutral-venue (no home bonus).
Matches already inside the frozen build (date <= its cutoff) are skipped so a later
results.csv rebuild can't double-count them.
"""
import os
import json
import copy
import math
from datetime import date

from features import expected, K_BASE

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
WC_MATCHES = os.path.join(DATA, "wc_matches.json")
WC_K = K_BASE["FIFA World Cup"]  # 60


def _apply(s, h, a, gh, ga, dstr):
    """Mutate state dict s with one finished, neutral-venue match h vs a (gh-ga)."""
    elo = s["elo"]
    eh, ea = elo.get(h, 1500.0), elo.get(a, 1500.0)
    we = expected(eh, ea)                       # neutral venue -> no home bonus
    res = 1.0 if gh > ga else (0.0 if gh < ga else 0.5)
    delta = WC_K * (math.log(abs(gh - ga) + 1) + 1) * (res - we)
    elo[h], elo[a] = eh + delta, ea - delta

    hist = s["hist"]
    hist.setdefault(h, []).append([res, gh - ga]);     hist[h][:] = hist[h][-10:]
    hist.setdefault(a, []).append([1 - res, ga - gh]); hist[a][:] = hist[a][-10:]

    mor = s["morale"]
    mor[h] = 0.7 * mor.get(h, 0.0) + 0.3 * (res - we)
    mor[a] = 0.7 * mor.get(a, 0.0) + 0.3 * ((1 - res) - (1 - we))

    adj_h, adj_a = (elo[a] - 1500) / 800.0, (elo[h] - 1500) / 800.0
    att, dfn = s["att"], s["dfn"]
    att[h] = 0.85 * att.get(h, 1.3) + 0.15 * gh * (1 + adj_h)
    dfn[h] = 0.85 * dfn.get(h, 1.3) + 0.15 * ga * (1 - adj_h)
    att[a] = 0.85 * att.get(a, 1.3) + 0.15 * ga * (1 + adj_a)
    dfn[a] = 0.85 * dfn.get(a, 1.3) + 0.15 * gh * (1 - adj_a)

    st = s["streak"]
    st[h] = st.get(h, 0) + 1 if res >= 0.5 else 0
    st[a] = st.get(a, 0) + 1 if res <= 0.5 else 0

    be = s["big_exp"]
    be[h] = 0.97 * be.get(h, 0.0) + 1.0
    be[a] = 0.97 * be.get(a, 0.0) + 1.0

    key = "|".join(sorted([h, a]))
    s["h2h"].setdefault(key, []).append([h, res, gh - ga]); s["h2h"][key][:] = s["h2h"][key][-10:]
    s["last_date"][h] = s["last_date"][a] = dstr


def apply_live_results(state, path=WC_MATCHES):
    """Return (updated_state_copy, info). Non-mutating: the input state is copied.
    info = {"applied": n, "through": last_date or None}."""
    info = {"applied": 0, "through": None}
    if not os.path.exists(path):
        return state, info
    try:
        matches = json.load(open(path, encoding="utf-8"))
    except Exception:
        return state, info
    if not matches:
        return state, info

    s = copy.deepcopy(state)
    cutoff = max((date.fromisoformat(d) for d in s["last_date"].values()), default=date.min)
    for m in sorted(matches, key=lambda x: x.get("date", "")):
        try:
            if date.fromisoformat(m["date"]) <= cutoff:   # already in the frozen base
                continue
            _apply(s, m["home"], m["away"], int(m["home_goals"]), int(m["away_goals"]), m["date"])
        except (KeyError, ValueError, TypeError):
            continue
        info["applied"] += 1
        info["through"] = m["date"]
    return s, info
