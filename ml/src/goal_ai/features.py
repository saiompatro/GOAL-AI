"""Feature engineering: Elo, rolling form, head-to-head, squad strength.

All features are computed strictly from information available *before* the match,
so there is no target leakage.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd


@dataclass
class EloConfig:
    start: float = 1500.0
    k: float = 30.0
    home_advantage: float = 65.0


def _expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def compute_elo_history(matches: pd.DataFrame, cfg: EloConfig) -> pd.DataFrame:
    """Return matches with pre-match Elo columns added."""
    ratings: Dict[str, float] = defaultdict(lambda: cfg.start)
    pre_home, pre_away = [], []
    for r in matches.itertuples(index=False):
        rh = ratings[r.home_team]
        ra = ratings[r.away_team]
        ha = 0.0 if r.neutral else cfg.home_advantage
        eh = _expected(rh + ha, ra)
        # Result → actual score for home
        if r.result == "H":
            sh = 1.0
        elif r.result == "A":
            sh = 0.0
        else:
            sh = 0.5
        # Margin-of-victory multiplier (Elo-of-football style, bounded)
        gd = abs(r.home_score - r.away_score)
        mov = np.log1p(gd) * (2.2 / ((abs((rh + ha) - ra) * 0.001) + 2.2))
        delta = cfg.k * mov * (sh - eh)
        pre_home.append(rh)
        pre_away.append(ra)
        ratings[r.home_team] = rh + delta
        ratings[r.away_team] = ra - delta
    out = matches.copy()
    out["elo_home_pre"] = pre_home
    out["elo_away_pre"] = pre_away
    out["elo_diff"] = out["elo_home_pre"] - out["elo_away_pre"]
    return out, dict(ratings)


def rolling_form(matches: pd.DataFrame, windows=(5, 10)) -> pd.DataFrame:
    """Pre-match rolling stats for each team."""
    hist: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max(windows)))
    rows = []
    for r in matches.itertuples(index=False):
        entry = {}
        for team, side in [(r.home_team, "home"), (r.away_team, "away")]:
            h = list(hist[team])
            for w in windows:
                window = h[-w:]
                if window:
                    wins = sum(1 for x in window if x["result"] == "W")
                    gf = np.mean([x["gf"] for x in window])
                    ga = np.mean([x["ga"] for x in window])
                else:
                    wins, gf, ga = 0, 0.0, 0.0
                entry[f"{side}_win_rate_{w}"] = wins / max(1, len(window))
                entry[f"{side}_gf_{w}"] = gf
                entry[f"{side}_ga_{w}"] = ga
                entry[f"{side}_gd_{w}"] = gf - ga
        rows.append(entry)
        # update history (chronological)
        h_res = "W" if r.result == "H" else ("L" if r.result == "A" else "D")
        a_res = "W" if r.result == "A" else ("L" if r.result == "H" else "D")
        hist[r.home_team].append({"result": h_res, "gf": r.home_score, "ga": r.away_score})
        hist[r.away_team].append({"result": a_res, "gf": r.away_score, "ga": r.home_score})
    return pd.DataFrame(rows)


def h2h_features(matches: pd.DataFrame, last_n: int = 5) -> pd.DataFrame:
    pair_hist: Dict[Tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=last_n))
    rows = []
    for r in matches.itertuples(index=False):
        key = tuple(sorted([r.home_team, r.away_team]))
        hist = list(pair_hist[key])
        if hist:
            home_wins = sum(
                1 for x in hist
                if (x["home"] == r.home_team and x["res"] == "H")
                or (x["home"] == r.away_team and x["res"] == "A")
            )
            avg_gd = np.mean([
                (x["hs"] - x["as"]) * (1 if x["home"] == r.home_team else -1)
                for x in hist
            ])
            rows.append({"h2h_home_wr": home_wins / len(hist), "h2h_avg_gd": avg_gd, "h2h_n": len(hist)})
        else:
            rows.append({"h2h_home_wr": 0.5, "h2h_avg_gd": 0.0, "h2h_n": 0})
        pair_hist[key].append({"home": r.home_team, "res": r.result, "hs": r.home_score, "as": r.away_score})
    return pd.DataFrame(rows)


def days_rest(matches: pd.DataFrame) -> pd.DataFrame:
    last_seen: Dict[str, pd.Timestamp] = {}
    rows = []
    for r in matches.itertuples(index=False):
        rest_h = (r.date - last_seen.get(r.home_team, r.date)).days if r.home_team in last_seen else 30
        rest_a = (r.date - last_seen.get(r.away_team, r.date)).days if r.away_team in last_seen else 30
        rows.append({"rest_home": min(30, rest_h), "rest_away": min(30, rest_a)})
        last_seen[r.home_team] = r.date
        last_seen[r.away_team] = r.date
    return pd.DataFrame(rows)


def tournament_flags(matches: pd.DataFrame) -> pd.DataFrame:
    t = matches["tournament"].str.lower().fillna("")
    return pd.DataFrame({
        "is_wc": t.str.contains("world cup").astype(int) & ~t.str.contains("qualif").astype(int),
        "is_wc_qual": t.str.contains("qualif").astype(int),
        "is_friendly": t.str.contains("friendly").astype(int),
        "is_continental": t.str.contains("euro|copa|afcon|asian cup|gold cup", regex=True).astype(int),
        "neutral": matches["neutral"].astype(int),
    })


def build_features(matches: pd.DataFrame, players_agg: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    elo_cfg = EloConfig(**cfg["features"]["elo"])
    elo_df, _ = compute_elo_history(matches, elo_cfg)
    form_df = rolling_form(matches, tuple(cfg["features"]["form_windows"]))
    h2h_df = h2h_features(matches, cfg["features"]["h2h_last_n"])
    rest_df = days_rest(matches)
    tourn_df = tournament_flags(matches)

    feats = pd.concat(
        [elo_df.reset_index(drop=True), form_df, h2h_df, rest_df, tourn_df], axis=1
    )

    # Squad strength joins
    pa = players_agg.copy() if not players_agg.empty else pd.DataFrame(
        columns=["team","squad_mean","top11_mean","star3_mean","att_mean","mid_mean","def_mean"]
    )
    for side in ("home", "away"):
        merged = feats.merge(pa, left_on=f"{side}_team", right_on="team", how="left").drop(columns=["team"])
        for col in ["squad_mean","top11_mean","star3_mean","att_mean","mid_mean","def_mean"]:
            feats[f"{side}_{col}"] = merged[col].fillna(pa[col].mean() if col in pa and not pa.empty else 70.0)

    for col in ["top11_mean","star3_mean","att_mean","mid_mean","def_mean","squad_mean"]:
        feats[f"{col}_diff"] = feats[f"home_{col}"] - feats[f"away_{col}"]

    feats["y"] = feats["result"].map({"H": 0, "D": 1, "A": 2}).astype(int)
    return feats


FEATURE_COLUMNS = [
    "elo_home_pre","elo_away_pre","elo_diff",
    "home_win_rate_5","home_gf_5","home_ga_5","home_gd_5",
    "away_win_rate_5","away_gf_5","away_ga_5","away_gd_5",
    "home_win_rate_10","home_gf_10","home_ga_10","home_gd_10",
    "away_win_rate_10","away_gf_10","away_ga_10","away_gd_10",
    "h2h_home_wr","h2h_avg_gd","h2h_n",
    "rest_home","rest_away",
    "is_wc","is_wc_qual","is_friendly","is_continental","neutral",
    "home_squad_mean","home_top11_mean","home_star3_mean","home_att_mean","home_mid_mean","home_def_mean",
    "away_squad_mean","away_top11_mean","away_star3_mean","away_att_mean","away_mid_mean","away_def_mean",
    "top11_mean_diff","star3_mean_diff","att_mean_diff","mid_mean_diff","def_mean_diff","squad_mean_diff",
]
