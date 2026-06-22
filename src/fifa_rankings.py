"""Official FIFA/Coca-Cola Men's World Ranking — a separate, recognizable "power
ranking" factor shown alongside the model's Elo in the Team and Player tabs.

FIFA ranks national teams only (there is no per-player FIFA ranking) and updates
the list ~4x a year, so the data ships as a curated snapshot (data/fifa_rankings.json)
loaded once at import — NOT scraped per request. get() returns {"rank", "points"}
or None; missing teams (historical/non-FIFA sides in the Elo set, or nations FIFA
hasn't published a point total for) degrade to None and the UI hides the tile.

`python src/fifa_rankings.py` does a best-effort refresh from Wikipedia's current
table and falls back to the shipped snapshot on any error, so it always works offline.
# ponytail: snapshot is the source of truth; FIFA updates quarterly, no live fetch.
"""
import os
import re
import json
import unicodedata

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
SNAPSHOT = os.path.join(DATA, "fifa_rankings.json")

# FIFA / press spellings that differ from the app's canonical team names. Keys and
# values are normalised before lookup, so casing/accents here don't matter.
ALIASES = {
    "usa": "United States", "korea republic": "South Korea", "ir iran": "Iran",
    "turkiye": "Turkey", "czechia": "Czech Republic", "congo dr": "DR Congo",
    "cote divoire": "Ivory Coast", "republic of korea": "South Korea",
}

_by_norm = {}   # normalised name -> {"rank", "points"}
_updated = None


def _norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load(path=SNAPSHOT):
    """(Re)read the snapshot into the in-memory lookup. Fails soft to empty."""
    global _by_norm, _updated
    _by_norm, _updated = {}, None
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return _by_norm
    _updated = doc.get("_updated")
    for team, rec in doc.get("rankings", {}).items():
        _by_norm[_norm(team)] = {"rank": rec.get("rank"), "points": rec.get("points")}
    for alias, canonical in ALIASES.items():
        rec = _by_norm.get(_norm(canonical))
        if rec is not None:
            _by_norm.setdefault(_norm(alias), rec)
    return _by_norm


def get(team):
    """{'rank': int, 'points': float|None} for a team, or None if FIFA-unranked here."""
    return _by_norm.get(_norm(team))


load()


def _refresh():
    """Best-effort: pull the current top-20 (with points) off Wikipedia and merge
    into the snapshot, preserving existing rank-only entries. Never destructive —
    on any failure the shipped snapshot is left untouched."""
    import urllib.request
    url = "https://en.wikipedia.org/wiki/FIFA_Men%27s_World_Ranking"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fifa-predictor/1.0"})
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"[fifa_rankings] fetch failed ({e}); keeping shipped snapshot")
        return False
    # Wikipedia's ranking table rows look like: <td>1</td> ... >Argentina</a> ... <td>1877.27</td>
    rows = re.findall(r"<td[^>]*>\s*(\d{1,3})\s*</td>.*?title=\"[^\"]*\">([A-Za-z .'-]+)</a>.*?<td[^>]*>\s*([0-9]{3,4}\.\d+)",
                      html, re.S)
    if len(rows) < 10:
        print("[fifa_rankings] table not recognised; keeping shipped snapshot")
        return False
    doc = json.load(open(SNAPSHOT, encoding="utf-8"))
    ranks = doc["rankings"]
    canon = {_norm(k): k for k in ranks}
    canon.update({_norm(a): c for a, c in ALIASES.items()})
    n = 0
    for rk, name, pts in rows:
        key = canon.get(_norm(name))
        if key and key in ranks:
            ranks[key] = {"rank": int(rk), "points": float(pts)}
            n += 1
    json.dump(doc, open(SNAPSHOT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[fifa_rankings] refreshed {n} teams from Wikipedia")
    return True


if __name__ == "__main__":
    _refresh()
    load()
    print(f"loaded {len(_by_norm)} entries (snapshot {_updated})")
    for t in ("Brazil", "United States", "USA", "Türkiye", "Catalonia"):
        print(f"  {t:>16} -> {get(t)}")
    assert get("Brazil") and get("Brazil")["rank"] == 6
    assert get("USA") == get("United States")          # alias resolves
    assert get("Türkiye") == get("Turkey")             # accent + alias
    assert get("Catalonia") is None                    # non-FIFA side -> None
    print("self-check OK")
