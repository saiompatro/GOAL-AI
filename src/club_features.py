"""Feature engineering for club-league matches (e.g. Premier League).

Same walk-forward, no-leakage approach as features.py for internationals, cut
down to the signals that carry over to a single domestic league played by
club sides every week: Elo (with goal-margin multiplier), recent form,
morale, unbeaten streak, an attack/defense split and head-to-head. There's no
climate/travel/jet-lag layer here — league fixtures are domestic, so that
signal international teams need doesn't apply.

One model is trained per league (see LEAGUES in fetch_club_results.py); this
module is parameterised by league key so a second league (La Liga, Serie A,
...) is just another data/club/<key>_results.csv away.
"""
import os
import math
import pandas as pd
import numpy as np

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "club")

HOME_ADV = 70   # Elo home-advantage bonus; club football runs stronger than internationals'
K = 20


def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def build_match_table(league_key):
    path = os.path.join(DATA, f"{league_key}_results.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    elo, hist, morale, att, dfn, streak, h2h = {}, {}, {}, {}, {}, {}, {}
    rows = []

    def h2h_key(a, b):
        return "|".join(sorted([a, b]))

    for m in df.itertuples():
        h, a = m.home_team, m.away_team
        eh, ea = elo.get(h, 1500.0), elo.get(a, 1500.0)

        we = expected(eh + HOME_ADV, ea)
        gh, ga = int(m.home_score), int(m.away_score)
        res = 1.0 if gh > ga else (0.0 if gh < ga else 0.5)

        def side_feats(team):
            f = hist.get(team, [])
            last5, last10 = f[-5:], f[-10:]
            ppg5 = np.mean([x[0] for x in last5]) * 3 if last5 else 1.0
            gd10 = np.mean([x[1] for x in last10]) if last10 else 0.0
            return {"ppg5": ppg5, "gd10": gd10, "morale": morale.get(team, 0.0),
                    "att": att.get(team, 1.3), "dfn": dfn.get(team, 1.3),
                    "streak": min(streak.get(team, 0), 12)}

        fh, fa = side_feats(h), side_feats(a)

        meetings = h2h.get(h2h_key(h, a), [])
        if meetings:
            pts = [(r if first == h else 1 - r) for first, r, _ in meetings[-10:]]
            gds = [(g if first == h else -g) for first, _, g in meetings[-10:]]
            h2h_rate, h2h_gd = float(np.mean(pts)), float(np.mean(gds))
        else:
            h2h_rate, h2h_gd = 0.5, 0.0

        rows.append({
            "date": m.date, "season": m.season, "home_team": h, "away_team": a,
            "elo_diff": (eh + HOME_ADV) - ea,
            "ppg5_diff": fh["ppg5"] - fa["ppg5"], "gd10_diff": fh["gd10"] - fa["gd10"],
            "morale_diff": fh["morale"] - fa["morale"],
            "att_vs_def": fh["att"] - fa["dfn"], "def_vs_att": fh["dfn"] - fa["att"],
            "streak_diff": fh["streak"] - fa["streak"],
            "h2h_rate": h2h_rate, "h2h_gd": h2h_gd,
            "home_goals": gh, "away_goals": ga,
            "outcome": 2 if gh > ga else (0 if gh < ga else 1),  # 2=home win,1=draw,0=away win
        })

        # ---- update state (after recording, so features are pre-match) ----
        margin = math.log(abs(gh - ga) + 1) + 1
        delta = K * margin * (res - we)
        elo[h], elo[a] = eh + delta, ea - delta
        hist.setdefault(h, []).append((res, gh - ga))
        hist.setdefault(a, []).append((1 - res, ga - gh))
        morale[h] = 0.7 * morale.get(h, 0.0) + 0.3 * (res - we)
        morale[a] = 0.7 * morale.get(a, 0.0) + 0.3 * ((1 - res) - (1 - we))
        adj_h = (elo.get(a, 1500) - 1500) / 800.0
        adj_a = (elo.get(h, 1500) - 1500) / 800.0
        att[h] = 0.85 * att.get(h, 1.3) + 0.15 * gh * (1 + adj_h)
        dfn[h] = 0.85 * dfn.get(h, 1.3) + 0.15 * ga * (1 - adj_h)
        att[a] = 0.85 * att.get(a, 1.3) + 0.15 * ga * (1 + adj_a)
        dfn[a] = 0.85 * dfn.get(a, 1.3) + 0.15 * gh * (1 - adj_a)
        streak[h] = streak.get(h, 0) + 1 if res >= 0.5 else 0
        streak[a] = streak.get(a, 0) + 1 if res <= 0.5 else 0
        h2h.setdefault(h2h_key(h, a), []).append((h, res, gh - ga))

    out = pd.DataFrame(rows)
    # teams active in the most recent season -> what the UI should offer
    current_teams = sorted(set(df[df["season"] == df["season"].iloc[-1]]["home_team"]))
    state = {"elo": elo, "hist": {k: v[-10:] for k, v in hist.items()},
             "morale": morale, "att": att, "dfn": dfn, "streak": streak,
             "h2h": {k: v[-10:] for k, v in h2h.items()},
             "current_teams": current_teams, "current_season": df["season"].iloc[-1]}
    return out, state


def main():
    from fetch_club_results import LEAGUES
    for key in LEAGUES:
        table, state = build_match_table(key)
        table.to_csv(os.path.join(DATA, f"{key}_training_table.csv"), index=False)
        import json
        json.dump(state, open(os.path.join(DATA, f"{key}_state.json"), "w"))
        print(f"{key}: {len(table)} training matches; {len(state['current_teams'])} current-season teams")
        top = sorted(state["elo"].items(), key=lambda x: -x[1])[:8]
        for t, e in top:
            print(f"  {t:20s} {e:7.1f}")


if __name__ == "__main__":
    main()
