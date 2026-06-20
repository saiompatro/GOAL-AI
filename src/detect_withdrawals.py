"""Detect players who have withdrawn from the World Cup after squad registration.

No squad API tracks injury withdrawals (football-data.org still lists Wataru
Endo after his foot injury / retirement). This scans live news for each squad
player and writes data/withdrawals.json for the players confidently reported
OUT of the tournament. squad_strength.py then excludes them and promotes the
next-best player, so ratings and key-player lists self-correct.

Conservative by design: a player is listed only when >=2 distinct headlines
match strong "out of the World Cup" phrasing (see sentiment.is_withdrawn).
Scans the top TOP_N players per team (by club strength x caps) -- the ones that
move ratings and actually get news coverage. Run on demand / periodically.
"""
import os
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from sentiment import is_withdrawn

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
TOP_N = 16
OUT = os.path.join(DATA, "withdrawals.json")


def main():
    df = pd.read_csv(os.path.join(DATA, "squads_rated.csv"))
    df["w"] = df["club_elo"] * (1 + df["caps"].clip(0, 100) / 100)
    targets = []
    for team, g in df.groupby("team"):
        for r in g.sort_values("w", ascending=False).head(TOP_N).itertuples():
            targets.append((team, r.player))
    print(f"scanning {len(targets)} players across {df.team.nunique()} teams...")

    found = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(is_withdrawn, p, t): (t, p) for t, p in targets}
        done = 0
        for f in as_completed(futs):
            t, p = futs[f]
            done += 1
            try:
                withdrawn, n, evidence = f.result()
            except Exception:
                continue
            if withdrawn:
                found[f"{t}|{p}"] = {"team": t, "player": p, "headlines": n,
                                     "evidence": evidence}
                print(f"  WITHDRAWN: {p} ({t}) -- {n} headlines: {evidence}")

    json.dump(found, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\n{len(found)} withdrawals written to {OUT}")
    print("next: python squad_strength.py   (re-rate excluding withdrawn players)")


if __name__ == "__main__":
    main()
