"""Recent World Cup 2026 form — the last two weeks of live matches.

"Recent" means the games played this week and last week of the 2026 World Cup
(a rolling WINDOW_DAYS window over the live results), aggregated per team and
shown in the Team tab, then folded into the match model as a bounded post-model
nudge (predict.py, RSTATS_K).

Source: the live WC 2026 scores the app already has (data/wc_matches.json,
populated by tournament_form.py from the free football-data.org feed) — matches,
goals for/against and a goal-difference form score. Shots/possession/xG need a
paid stats feed and are not collected; those fields stay null and the UI hides the
tiles — never fabricated.

Ships as a curated snapshot (data/recent_stats.json) loaded once at import — NOT
fetched per request. `python src/recent_stats.py` rebuilds it from wc_matches.json
and leaves the shipped snapshot untouched on any failure.
# ponytail: snapshot is the source of truth; rebuilt on the data-refresh, no live fetch.
"""
import os
import re
import json
import math
import unicodedata
from datetime import date, timedelta

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SNAPSHOT = os.path.join(DATA, "recent_stats.json")
WC_MATCHES = os.path.join(DATA, "wc_matches.json")

WINDOW_DAYS = 14          # "this week and last week"
SHRINK_M = 2.0            # pulls 1-2 match samples toward 0 so one blowout can't dominate
XGD_SCALE = 1.0          # xG diff/match that maps to form ~0.76 (tanh)
GD_SCALE = 1.5           # goal diff/match scale for the no-xG baseline

# feed / press spellings -> the app's canonical team names.
ALIASES = {"usa": "United States", "korea republic": "South Korea",
           "ir iran": "Iran", "iran": "Iran", "turkiye": "Turkey", "turkey": "Turkey",
           "czechia": "Czech Republic", "côte d ivoire": "Ivory Coast",
           "cote d ivoire": "Ivory Coast", "republic of ireland": "Ireland"}

_team = {}          # normalised team -> aggregate dict
_meta = {}


def _norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s.lower())).strip()


def _tkey(s):
    return _norm(s).replace(" ", "")


def _canon(name):
    """Map a feed's team name to the app's canonical spelling."""
    return ALIASES.get(_norm(name), name)


def load(path=SNAPSHOT):
    """(Re)read the snapshot into the in-memory lookups. Fails soft to empty."""
    global _team, _meta
    _team, _meta = {}, {}
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return
    _meta = {k: doc.get(k) for k in ("_updated", "_window", "_source", "_advanced", "_competitions")}
    for team, rec in doc.get("teams", {}).items():
        _team[_tkey(team)] = rec
    for alias, canon in ALIASES.items():
        ck = _tkey(canon)
        if ck in _team:
            _team.setdefault(_tkey(alias), _team[ck])


def _form_score(rec):
    """[-1, 1] recent-form signal, shrunk for small samples. xG-difference based
    when xG is present, else goal-difference based (the baseline)."""
    n = rec.get("matches", 0)
    if not n:
        return 0.0
    if rec.get("xg_for") is not None and rec.get("xg_against") is not None:
        diff_pm, scale = (rec["xg_for"] - rec["xg_against"]) / n, XGD_SCALE
    else:
        diff_pm, scale = (rec["goals"] - rec["ga"]) / n, GD_SCALE
    return round(math.tanh(diff_pm / scale) * (n / (n + SHRINK_M)), 3)


def _div(a, b, nd=1):
    return round(a / b, nd) if (a is not None and b) else None


def _per_match(rec):
    """Add per-match rates + form score to a raw team aggregate (handles nulls)."""
    n = max(rec["matches"], 1)
    out = dict(rec)
    out["goals_pm"] = round(rec["goals"] / n, 2)
    out["ga_pm"] = round(rec["ga"] / n, 2)
    out["shots_pm"] = _div(rec.get("shots"), n)
    out["sot_pm"] = _div(rec.get("sot"), n)
    out["sot_pct"] = (round(100 * rec["sot"] / rec["shots"]) if rec.get("shots") else None)
    out["possession"] = rec.get("possession")
    out["xg_for_pm"] = _div(rec.get("xg_for"), n, 2)
    out["xg_against_pm"] = _div(rec.get("xg_against"), n, 2)
    out["xg_diff_pm"] = (round((rec["xg_for"] - rec["xg_against"]) / n, 2)
                         if rec.get("xg_for") is not None and rec.get("xg_against") is not None else None)
    out["form_score"] = _form_score(rec)
    return out


def get_team(team):
    """Recent WC aggregate + per-match rates for a team, or None if not in the window."""
    rec = _team.get(_tkey(team))
    return _per_match(rec) if rec else None


def form_score(team):
    """[-1, 1] recent-form signal for the model nudge, or None if not in the window."""
    rec = _team.get(_tkey(team))
    return _form_score(rec) if rec else None


def meta():
    return _meta


load()


# ----------------------------------------------------------------------------- build

def _empty():
    return {"matches": 0, "goals": 0, "ga": 0, "shots": 0, "sot": 0, "shot_n": 0,
            "poss_sum": 0.0, "poss_n": 0, "xgf_sum": 0.0, "xgf_n": 0,
            "xga_sum": 0.0, "xga_n": 0}


def _finalize(raw):
    """Collapse accumulators into the stored per-team record (nulls when absent)."""
    out = {}
    for team, t in raw.items():
        out[team] = {
            "matches": t["matches"], "goals": t["goals"], "ga": t["ga"],
            "shots": t["shots"] if t["shot_n"] else None,
            "sot": min(t["sot"], t["shots"]) if t["shot_n"] else None,
            "possession": round(t["poss_sum"] / t["poss_n"]) if t["poss_n"] else None,
            "xg_for": round(t["xgf_sum"], 2) if t["xgf_n"] else None,
            "xg_against": round(t["xga_sum"], 2) if t["xga_n"] else None,
        }
    return out


def _window(dates):
    ref = max(dates)
    return ref - timedelta(days=WINDOW_DAYS), ref


def _build_from_scores():
    """Baseline: WC 2026 window from the live scores we already have. No advanced stats."""
    ms = json.load(open(WC_MATCHES, encoding="utf-8"))
    ds = [date.fromisoformat(m["date"]) for m in ms]
    if not ds:
        return None
    cutoff, ref = _window(ds)
    raw = {}
    for m in ms:
        if date.fromisoformat(m["date"]) < cutoff:
            continue
        gh, ga = m.get("home_goals"), m.get("away_goals")
        if gh is None or ga is None:
            continue
        for team, gf, gaa in ((_canon(m["home"]), gh, ga), (_canon(m["away"]), ga, gh)):
            t = raw.setdefault(team, _empty())
            t["matches"] += 1
            t["goals"] += gf
            t["ga"] += gaa
    return {"teams": _finalize(raw), "players": {}, "advanced": False,
            "window": [cutoff.isoformat(), ref.isoformat()],
            "source": "live WC 2026 scores (data/wc_matches.json)",
            "competitions": [f"FIFA World Cup 2026 (last {WINDOW_DAYS} days)"]}


def _refresh():
    """Rebuild the snapshot for the WC 2026 window from the live scores. Never
    destructive — keeps the shipped snapshot on any failure."""
    built = _build_from_scores()
    if built is None:
        print("[recent_stats] no WC data available; keeping shipped snapshot")
        return False
    doc = {"_updated": date.today().isoformat(), "_window": built["window"],
           "_source": built["source"], "_advanced": built["advanced"],
           "_competitions": built["competitions"],
           "teams": dict(sorted(built["teams"].items())), "players": built["players"]}
    json.dump(doc, open(SNAPSHOT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[recent_stats] wrote {len(doc['teams'])} teams, {len(doc['players'])} players "
          f"(advanced={built['advanced']}, window {built['window'][0]}..{built['window'][1]})")
    return True


if __name__ == "__main__":
    import sys
    if "--no-fetch" not in sys.argv:
        _refresh()
    load()
    print(f"loaded {len(_team)} teams "
          f"(window {_meta.get('_window')})")
    for t in ("Brazil", "Germany", "United States"):
        r = get_team(t)
        print(f"  {t:>14} -> {None if not r else {k: r[k] for k in ('matches','goals','ga','shots','possession','xg_for_pm','form_score')}}")
    if _team:
        any_team = next(iter(_team.values()))
        assert -1.0 <= _form_score(any_team) <= 1.0
        assert get_team("Atlantis") is None
        for r in _team.values():
            assert r["sot"] is None or (r["shots"] and 0 <= r["sot"] <= r["shots"])
        print("self-check OK")
