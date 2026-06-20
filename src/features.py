"""Feature engineering over real international match results (1872-present).

Builds, per match and per team, walking forward in time (no leakage):
- Elo rating (K varies by competition importance; goal-margin multiplier)
- Form: points-per-game and goal difference over last 5 / 10 matches
- Attack/defense ratings: opponent-adjusted EWMA of goals scored/conceded
  (pi-/Berrar-rating style split of strength into scoring and conceding)
- Morale: exponentially-weighted momentum of recent results vs expectation,
  i.e. beating stronger sides lifts morale more than beating minnows
- Unbeaten streak (momentum/psychology beyond raw points)
- Head-to-head: win rate and goal diff over past meetings of the two sides
- Major-tournament experience: big-tournament matches played, decaying EWMA
- Rest days since previous match
- Venue/climate: home advantage, neutrality, travel distance, eastward jet lag
  (timezones crossed east, which research shows hurts more than westward),
  heat/humidity/altitude mismatch vs the team's home climate
"""
import os
import math
import pandas as pd
import numpy as np

from geo import COUNTRY, haversine_km

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

K_BASE = {"FIFA World Cup": 60, "FIFA World Cup qualification": 40,
          "UEFA Euro": 50, "Copa América": 50, "African Cup of Nations": 50,
          "AFC Asian Cup": 50, "CONCACAF Championship": 50, "Gold Cup": 50,
          "UEFA Nations League": 35, "Confederations Cup": 40}
DEFAULT_K = 20  # friendlies and minor tournaments


def load_centroids():
    c = pd.read_csv(os.path.join(DATA, "country_centroids.csv"))
    cen = {r.COUNTRY: (r.latitude, r.longitude) for r in c.itertuples()}
    # name fixes between datasets
    alias = {"United States": "USA", "South Korea": "Korea, South", "North Korea": "Korea, North",
             "DR Congo": "Congo DR", "Ivory Coast": "Côte d'Ivoire", "Cape Verde": "Cabo Verde"}
    for ours, theirs in alias.items():
        if theirs in cen:
            cen[ours] = cen[theirs]
    return cen


CENTROIDS = load_centroids()


def country_coords(name):
    if name in COUNTRY:
        return COUNTRY[name][0], COUNTRY[name][1]
    if name in CENTROIDS:
        return CENTROIDS[name]
    return None


def country_climate(name):
    """(temp_jun, humidity, altitude); crude latitude-based fallback."""
    if name in COUNTRY:
        _, _, t, h, a = COUNTRY[name]
        return t, h, a
    co = country_coords(name)
    if co is None:
        return 24, 1, 100
    lat = abs(co[0])
    t = 32 - 0.35 * lat          # hotter near the equator
    h = 2 if lat < 20 else 1
    return t, h, 100


def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def build_match_table(min_year=1980):
    df = pd.read_csv(os.path.join(DATA, "results.csv"))
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["home_score", "away_score"]).sort_values("date").reset_index(drop=True)

    elo, hist, last_date, morale = {}, {}, {}, {}
    att, dfn, streak, h2h, big_exp = {}, {}, {}, {}, {}
    rows = []

    def h2h_key(a, b):
        return "|".join(sorted([a, b]))

    for m in df.itertuples():
        h, a = m.home_team, m.away_team
        eh, ea = elo.get(h, 1500.0), elo.get(a, 1500.0)
        neutral = bool(m.neutral)
        home_adv = 0 if neutral else 60  # Elo home bonus

        we = expected(eh + home_adv, ea)
        gh, ga = int(m.home_score), int(m.away_score)
        res = 1.0 if gh > ga else (0.0 if gh < ga else 0.5)

        # climate/travel for both teams relative to match venue country
        vt, vh, va = country_climate(m.country)
        vco = country_coords(m.country)

        def side_feats(team, opp_elo, own_elo, is_home):
            f = hist.get(team, [])
            last5, last10 = f[-5:], f[-10:]
            ppg5 = np.mean([x[0] for x in last5]) * 3 if last5 else 1.0
            gd10 = np.mean([x[1] for x in last10]) if last10 else 0.0
            mor = morale.get(team, 0.0)
            ld = last_date.get(team)
            rest = min((m.date - ld).days, 60) if ld is not None else 30
            tt, th, ta = country_climate(team)
            tco = country_coords(team)
            travel = haversine_km(tco[0], tco[1], vco[0], vco[1]) / 1000.0 if (tco and vco) else 1.0
            # eastward timezone shift hurts more than westward (jet-lag research)
            if tco and vco:
                dlon = ((vco[1] - tco[1] + 180) % 360) - 180
                tz_east = max(0.0, dlon) / 15.0
            else:
                tz_east = 0.0
            if is_home and not neutral:
                travel, tz_east = 0.0, 0.0
            return {"elo": own_elo, "ppg5": ppg5, "gd10": gd10, "morale": mor, "rest": rest,
                    "att": att.get(team, 1.3), "dfn": dfn.get(team, 1.3),
                    "streak": min(streak.get(team, 0), 12), "exp": big_exp.get(team, 0.0),
                    "heat": max(0.0, vt - tt), "hum": max(0, vh - th),
                    "alt": max(0.0, va - ta) / 1000.0, "travel": travel, "tz_east": tz_east}

        fh, fa = side_feats(h, ea, eh, True), side_feats(a, eh, ea, False)

        # head-to-head from the home side's perspective (last 10 meetings)
        meetings = h2h.get(h2h_key(h, a), [])
        if meetings:
            pts = [(r if first == h else 1 - r) for first, r, _ in meetings[-10:]]
            gds = [(g if first == h else -g) for first, _, g in meetings[-10:]]
            h2h_rate, h2h_gd = float(np.mean(pts)), float(np.mean(gds))
        else:
            h2h_rate, h2h_gd = 0.5, 0.0

        if m.date.year >= min_year:
            rows.append({
                "date": m.date, "home_team": h, "away_team": a,
                "tournament": m.tournament, "neutral": int(neutral),
                "elo_diff": (eh + home_adv) - ea,
                "ppg5_diff": fh["ppg5"] - fa["ppg5"], "gd10_diff": fh["gd10"] - fa["gd10"],
                "morale_diff": fh["morale"] - fa["morale"], "rest_diff": fh["rest"] - fa["rest"],
                "att_vs_def": fh["att"] - fa["dfn"], "def_vs_att": fh["dfn"] - fa["att"],
                "streak_diff": fh["streak"] - fa["streak"], "exp_diff": fh["exp"] - fa["exp"],
                "h2h_rate": h2h_rate, "h2h_gd": h2h_gd,
                "heat_diff": fh["heat"] - fa["heat"], "hum_diff": fh["hum"] - fa["hum"],
                "alt_diff": fh["alt"] - fa["alt"], "travel_diff": fh["travel"] - fa["travel"],
                "tz_east_diff": fh["tz_east"] - fa["tz_east"],
                "is_wc": int("World Cup" in str(m.tournament) and "qual" not in str(m.tournament)),
                "home_goals": gh, "away_goals": ga,
                "outcome": 2 if gh > ga else (0 if gh < ga else 1),  # 2=home win,1=draw,0=away win
            })

        # ---- update state (after recording, so features are pre-match) ----
        k = next((v for key, v in K_BASE.items() if key in str(m.tournament)), DEFAULT_K)
        margin = math.log(abs(gh - ga) + 1) + 1
        delta = k * margin * (res - we)
        elo[h], elo[a] = eh + delta, ea - delta
        hist.setdefault(h, []).append((res, gh - ga))
        hist.setdefault(a, []).append((1 - res, ga - gh))
        # morale: EWMA of (result - expectation); surprises move it most
        morale[h] = 0.7 * morale.get(h, 0.0) + 0.3 * (res - we)
        morale[a] = 0.7 * morale.get(a, 0.0) + 0.3 * ((1 - res) - (1 - we))
        last_date[h] = last_date[a] = m.date
        # attack/defense: opponent-strength-adjusted EWMA of goals for/against
        adj_h = (elo.get(a, 1500) - 1500) / 800.0   # scoring vs strong opp counts more
        adj_a = (elo.get(h, 1500) - 1500) / 800.0
        att[h] = 0.85 * att.get(h, 1.3) + 0.15 * gh * (1 + adj_h)
        dfn[h] = 0.85 * dfn.get(h, 1.3) + 0.15 * ga * (1 - adj_h)
        att[a] = 0.85 * att.get(a, 1.3) + 0.15 * ga * (1 + adj_a)
        dfn[a] = 0.85 * dfn.get(a, 1.3) + 0.15 * gh * (1 - adj_a)
        streak[h] = streak.get(h, 0) + 1 if res >= 0.5 else 0
        streak[a] = streak.get(a, 0) + 1 if res <= 0.5 else 0
        is_major = k >= 40  # WC, WC qualifiers, continental championships
        big_exp[h] = 0.97 * big_exp.get(h, 0.0) + (1.0 if is_major else 0.0)
        big_exp[a] = 0.97 * big_exp.get(a, 0.0) + (1.0 if is_major else 0.0)
        h2h.setdefault(h2h_key(h, a), []).append((h, res, gh - ga))

    out = pd.DataFrame(rows)
    state = {"elo": elo, "hist": {k: v[-10:] for k, v in hist.items()},
             "morale": morale, "last_date": {k: str(v.date()) for k, v in last_date.items()},
             "att": att, "dfn": dfn, "streak": streak, "big_exp": big_exp,
             "h2h": {k: v[-10:] for k, v in h2h.items()}}
    return out, state


if __name__ == "__main__":
    table, state = build_match_table()
    table.to_csv(os.path.join(DATA, "training_table.csv"), index=False)
    import json
    json.dump(state, open(os.path.join(DATA, "current_state.json"), "w"))
    print(f"{len(table)} training matches; teams rated: {len(state['elo'])}")
    top = sorted(state["elo"].items(), key=lambda x: -x[1])[:12]
    for t, e in top:
        print(f"  {t:20s} {e:7.1f}  morale {state['morale'].get(t, 0):+.2f}")
