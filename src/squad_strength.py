"""Player-level squad strength from real club football results.

Each 2026 World Cup player is mapped to his club; the club's Elo rating (built
by clubelo.com from domestic league + UEFA/continental results — actual matches,
no video-game ratings) proxies the level the player performs at week to week.

Team squad strength = caps-weighted mean of player club Elos, with a small
top-heavy weighting (your best XI matters more than squad player #26).
"""
import os
import re
import json
import difflib
import unicodedata
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

ALIAS = {
    "manchester city": "man city", "manchester united": "man united",
    "tottenham hotspur": "tottenham", "wolverhampton wanderers": "wolves",
    "newcastle united": "newcastle", "west ham united": "west ham",
    "brighton & hove albion": "brighton", "nottingham forest": "forest",
    "bayern munich": "bayern", "borussia dortmund": "dortmund",
    "bayer leverkusen": "leverkusen", "borussia monchengladbach": "gladbach",
    "eintracht frankfurt": "frankfurt", "rb leipzig": "leipzig",
    "paris saint-germain": "paris sg", "olympique de marseille": "marseille",
    "olympique lyonnais": "lyon", "as monaco": "monaco",
    "atletico madrid": "atletico", "real sociedad": "sociedad",
    "athletic bilbao": "bilbao", "real betis": "betis",
    "inter milan": "inter", "ac milan": "milan", "internazionale": "inter",
    "as roma": "roma", "ss lazio": "lazio", "ssc napoli": "napoli",
    "juventus": "juventus", "sporting cp": "sporting", "fc porto": "porto",
    "sl benfica": "benfica", "psv eindhoven": "psv", "afc ajax": "ajax",
    "al hilal": "al-hilal", "al nassr": "al-nassr", "al ahli": "al-ahli",
    "al ittihad": "al-ittihad", "slavia prague": "slavia praha",
    "sparta prague": "sparta praha", "viktoria plzen": "plzen",
    "red star belgrade": "crvena zvezda", "istanbul basaksehir": "basaksehir",
    "dinamo zagreb": "dinamo zagreb", "fenerbahce": "fenerbahce",
}


# Strong clubs outside ClubElo's European coverage. Estimates anchored to how
# these sides perform in continental competition (Libertadores, AFC/CAF CL,
# Club World Cup) relative to European opposition — real results, nothing else.
EXTRA_ELO = {
    "flamengo": 1800, "palmeiras": 1790, "river plate": 1740, "boca juniors": 1720,
    "botafogo": 1740, "fluminense": 1700, "atletico mineiro": 1700, "sao paulo": 1690,
    "gremio": 1670, "internacional": 1670, "corinthians": 1680, "cruzeiro": 1670,
    "al-hilal": 1700, "al-nassr": 1640, "al-ahli": 1640, "al-ittihad": 1630,
    "al-qadsiah": 1560, "al ahly": 1600, "zamalek": 1540, "pyramids": 1560,
    "mamelodi sundowns": 1580, "orlando pirates": 1520, "kaizer chiefs": 1480,
    "esteghlal": 1520, "persepolis": 1530, "sepahan": 1490, "tractor": 1490,
    "al-sadd": 1540, "al-duhail": 1530, "al-gharafa": 1490, "al-rayyan": 1480,
    "al-hussein": 1430, "al-faisaly": 1420, "al-wehdat": 1410,
    "guadalajara": 1600, "america": 1640, "club america": 1640, "monterrey": 1620,
    "tigres uanl": 1620, "cruz azul": 1600, "toluca": 1590, "pumas unam": 1550,
    "inter miami": 1560, "la galaxy": 1520, "lafc": 1560, "seattle sounders": 1520,
    "columbus crew": 1520, "philadelphia union": 1500, "fc cincinnati": 1510,
    "urawa red diamonds": 1560, "vissel kobe": 1560, "kawasaki frontale": 1550,
    "ulsan hd": 1560, "jeonbuk hyundai motors": 1550, "johor darul tazim": 1450,
    "al-ain": 1540, "al-shabab": 1540, "al-ettifaq": 1530, "nasaf": 1450,
    "pakhtakor": 1460, "navbahor": 1430, "colo-colo": 1600, "penarol": 1620,
    "nacional": 1610, "olimpia": 1560, "libertad": 1570, "cerro porteno": 1560,
    "independiente del valle": 1660, "ldu quito": 1650, "barcelona sc": 1570,
    "atletico nacional": 1620, "millonarios": 1560, "racing": 1700, "lanus": 1640,
    "td": 1500,
}

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s):
    s = strip_accents(str(s)).lower()
    s = re.sub(r"\[.*?\]|\(.*?\)", "", s)
    s = re.sub(r"\b(fc|cf|afc|sc|ac|cd|club|de|deportivo|1\.|ssc|sl|as|ss|cp|sv|vfb|vfl|tsg|fsv)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def build():
    squads = pd.read_csv(os.path.join(DATA, "squads.csv"))

    # drop players confirmed withdrawn from the tournament (see detect_withdrawals.py)
    wpath = os.path.join(DATA, "withdrawals.json")
    if os.path.exists(wpath):
        wd = json.load(open(wpath, encoding="utf-8"))
        withdrawn = {(v["team"], v["player"]) for v in wd.values()}
        before = len(squads)
        squads = squads[~squads.apply(lambda r: (r["team"], r["player"]) in withdrawn, axis=1)]
        if before != len(squads):
            print(f"excluded {before - len(squads)} withdrawn player(s): "
                  + ", ".join(f"{p} ({t})" for t, p in withdrawn))

    elo = pd.read_csv(os.path.join(DATA, "clubelo_latest.csv"))
    elo["n"] = elo["Club"].map(norm)
    lookup = dict(zip(elo["n"], elo["Elo"]))
    names = list(lookup.keys())
    median_elo = float(elo["Elo"].median())

    def club_elo(club):
        n = norm(club)
        n = ALIAS.get(n, n)
        if n in lookup:
            return lookup[n], "exact"
        if n in EXTRA_ELO:
            return EXTRA_ELO[n], "curated"
        cand = difflib.get_close_matches(n, names, n=1, cutoff=0.85)
        if cand:
            return lookup[cand[0]], "fuzzy"
        # token containment (e.g. "real madrid cf" vs "real madrid")
        toks = set(n.split())
        for cn in names:
            if toks and (toks <= set(cn.split()) or set(cn.split()) <= toks):
                return lookup[cn], "token"
        return median_elo, "unmatched"  # club outside ClubElo coverage -> league-median proxy

    squads["caps"] = pd.to_numeric(squads["caps"], errors="coerce").fillna(0)
    res = squads.apply(lambda r: club_elo(r["club"]), axis=1)
    squads["club_elo"] = [x[0] for x in res]
    squads["match_type"] = [x[1] for x in res]

    matched = (squads["match_type"] != "unmatched").mean()
    print(f"club match rate: {matched:.1%} of {len(squads)} players")

    ratings = {}
    for team, g in squads.groupby("team"):
        g = g.sort_values("club_elo", ascending=False).reset_index(drop=True)
        w_rank = pd.Series([1.5 if i < 11 else 1.0 for i in range(len(g))])  # best XI weighted up
        w_caps = 1.0 + (g["caps"].clip(0, 100) / 100.0)                       # experience
        w = w_rank * w_caps
        ratings[team] = float((g["club_elo"] * w).sum() / w.sum())

    squads.to_csv(os.path.join(DATA, "squads_rated.csv"), index=False)
    json.dump(ratings, open(os.path.join(DATA, "squad_strength.json"), "w"), indent=1)
    for t, r in sorted(ratings.items(), key=lambda x: -x[1])[:12]:
        print(f"  {t:20s} squad club-Elo {r:7.1f}")
    return ratings


if __name__ == "__main__":
    build()
