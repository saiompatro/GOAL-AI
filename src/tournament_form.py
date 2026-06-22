"""Current-World-Cup performance per team — the heaviest win-prediction factor,
but only once a team has played enough of the tournament to be meaningful.

How a team is doing IN the current World Cup is the strongest signal available,
so when active it outweighs Elo, squad and sentiment. Per requirement it is
IGNORED entirely until a team has played >= MIN_MATCHES (5) World Cup matches
(i.e. from the quarter-finals onward in the 2026 format).

Source: football-data.org WC matches (free tier = scores/goals; no possession or
assists). The metric therefore uses results + goals, which are the core "form"
signals anyway. Possession/assists slot in automatically if a richer feed is
configured later (see add_advanced_stats()).

Run:  python tournament_form.py <football-data-token>
Writes data/tournament_form.json, consumed at prediction time by predict.py.
"""
import os
import sys
import json
import requests

from fetch_squads_api import TEAM_CANON

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(DATA, "tournament_form.json")
WC_MATCHES = os.path.join(DATA, "wc_matches.json")  # raw finished results -> live_ratings.py
BASE = "https://api.football-data.org/v4"
MIN_MATCHES = 5


def canon(name):
    return TEAM_CANON.get(name, name)


def fetch_wc_matches(token):
    r = requests.get(f"{BASE}/competitions/WC/matches",
                     headers={"X-Auth-Token": token}, timeout=30)
    r.raise_for_status()
    return [m for m in r.json().get("matches", []) if m.get("status") == "FINISHED"]


def form_score(ppg, gd_pg):
    """Normalise results+goals form to roughly [-1, 1] (0 = average team)."""
    pts_term = 0.6 * (ppg - 1.5) / 1.5
    gd_term = 0.4 * max(-1.0, min(1.0, gd_pg / 2.5))
    return round(max(-1.0, min(1.0, pts_term + gd_term)), 3)


def compute(matches):
    agg = {}
    for m in matches:
        h, a = canon(m["homeTeam"]["name"]), canon(m["awayTeam"]["name"])
        ft = m.get("score", {}).get("fullTime", {})
        gh, ga = ft.get("home"), ft.get("away")
        if gh is None or ga is None:
            continue
        winner = m.get("score", {}).get("winner")  # respects penalty-shootout result
        for team, gf, gaa, won in ((h, gh, ga, winner == "HOME_TEAM"),
                                   (a, ga, gh, winner == "AWAY_TEAM")):
            d = agg.setdefault(team, {"matches": 0, "pts": 0, "gf": 0, "ga": 0})
            d["matches"] += 1
            d["gf"] += gf
            d["ga"] += gaa
            d["pts"] += 3 if won else (1 if winner == "DRAW" else 0)

    out = {}
    for team, d in agg.items():
        n = d["matches"]
        ppg = d["pts"] / n
        gd_pg = (d["gf"] - d["ga"]) / n
        out[team] = {
            "matches": n, "ppg": round(ppg, 2),
            "gf_pg": round(d["gf"] / n, 2), "ga_pg": round(d["ga"] / n, 2),
            "gd_pg": round(gd_pg, 2),
            "possession": None, "assists_pg": None,  # filled only by a paid feed
            "form_score": form_score(ppg, gd_pg),
            "eligible": n >= MIN_MATCHES,
        }
    return out


def main():
    from config import get_token
    token = sys.argv[1].strip() if len(sys.argv) > 1 else get_token()
    if not token:
        raise SystemExit("No API key. Pass it as an arg, set FOOTBALL_DATA_TOKEN, "
                         "or add it to the project .env file.")
    matches = fetch_wc_matches(token)
    form = compute(matches)
    json.dump(form, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    # raw finished results, folded into live Elo/form/morale by live_ratings.py
    records = []
    for m in matches:
        ft = m.get("score", {}).get("fullTime", {})
        gh, ga = ft.get("home"), ft.get("away")
        if gh is None or ga is None:
            continue
        records.append({"date": (m.get("utcDate") or "")[:10],
                        "home": canon(m["homeTeam"]["name"]), "away": canon(m["awayTeam"]["name"]),
                        "home_goals": int(gh), "away_goals": int(ga)})
    json.dump(records, open(WC_MATCHES, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    elig = [t for t, v in form.items() if v["eligible"]]
    print(f"{len(matches)} finished WC matches -> form for {len(form)} teams")
    print(f"eligible (>= {MIN_MATCHES} matches): {len(elig)} -> {', '.join(elig) or 'none yet'}")
    for t, v in sorted(form.items(), key=lambda x: -x[1]["form_score"])[:8]:
        print(f"  {t:18s} {v['matches']}m  ppg {v['ppg']}  gd/g {v['gd_pg']:+.2f}  "
              f"form {v['form_score']:+.2f}{'  [ACTIVE]' if v['eligible'] else ''}")


if __name__ == "__main__":
    main()
