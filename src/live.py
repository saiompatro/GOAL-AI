"""Live data fetched at prediction time — nothing cached, nothing stored.

- Current venue weather (temperature, relative humidity) from Open-Meteo
  (free, keyless). RH% is mapped onto the model's 0/1/2 humidity class.
- Fresh news headlines for both teams and the venue via Google News RSS,
  scored for sentiment (see sentiment.py).
All fetches run in parallel and fail soft: if a source is unreachable the
model falls back to long-term climate averages / neutral sentiment, and the
response says which values are live vs fallback.
"""
import os
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from sentiment import team_sentiment, news_headlines, player_report

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
N_KEY = 8          # key players tracked per team
W_PLAYERS = 0.6    # composite: key-player news outweighs general team news

def _load_squads():
    df = pd.read_csv(os.path.join(DATA, "squads_rated.csv"))
    df["w"] = df["club_elo"] * (1 + df["caps"].clip(0, 100) / 100)
    return df


_squads = _load_squads()


def reload():
    """Re-read rated squads so key players reflect a fresh pipeline run."""
    global _squads
    _squads = _load_squads()


def key_players(team, n=N_KEY):
    """Most important players: club level x international experience."""
    g = _squads[_squads["team"] == team].sort_values("w", ascending=False).head(n)
    tot = g["w"].sum()
    return [(r.player, r.w / tot) for r in g.itertuples()]


def importance_label(weight, rank):
    """Plain-English read on how central a player is to the team."""
    if rank == 0 or weight >= 0.16:
        return "Talisman / first-choice"
    if weight >= 0.13:
        return "Core starter"
    if weight >= 0.11:
        return "Regular starter"
    return "Squad rotation"


def submit_composite(team, ex):
    """Kick off all news fetches for a team without blocking."""
    f_team = ex.submit(team_sentiment, team, 20)
    f_players = [(p, w, ex.submit(player_report, p, team))
                 for p, w in key_players(team)]
    return f_team, f_players


def collect_composite(team, f_team, f_players):
    """Blend of general team news + weighted key-player news; also collect injuries."""
    s_team, heads = f_team.result()
    players, injuries, s_players = [], [], 0.0
    for rank, (p, w, f) in enumerate(f_players):
        rep = f.result()
        s = rep["sentiment"]
        s_players += w * s
        injured = rep["injury_talk"]
        players.append({"player": p, "weight": round(w, 2), "sentiment": round(s, 2),
                        "injury_talk": bool(injured), "headlines": rep["headlines"][:2]})
        if injured:
            injuries.append({
                "team": team, "player": p, "weight": round(w, 2),
                "importance": importance_label(w, rank),
                "injury_date": rep["injury_date"],
                "headline": rep["injury_headline"],
            })
    composite = (1 - W_PLAYERS) * s_team + W_PLAYERS * s_players
    return {"composite": round(composite, 3), "team_news": round(s_team, 3),
            "players": players, "injuries": injuries, "headlines": heads[:6]}


def live_weather(lat, lon):
    """Current temperature (C) and humidity class at coordinates, or None."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m"},
            timeout=8).json()["current"]
        temp = float(r["temperature_2m"])
        rh = float(r["relative_humidity_2m"])
        hum_class = 0 if rh < 45 else (1 if rh <= 70 else 2)
        return {"temp_c": temp, "rh_pct": rh, "humidity_class": hum_class}
    except Exception:
        return None


def gather(home, away, venue_name, lat, lon):
    """Fetch weather + team/key-player/venue news concurrently (one click)."""
    city = venue_name.split("(")[-1].rstrip(")") if venue_name else None
    with ThreadPoolExecutor(max_workers=24) as ex:
        f_w = ex.submit(live_weather, lat, lon) if lat is not None else None
        f_v = ex.submit(news_headlines, f'"{city}" world cup 2026 stadium', 6) if city else None
        sub_h, sub_a = submit_composite(home, ex), submit_composite(away, ex)
        ch, ca = collect_composite(home, *sub_h), collect_composite(away, *sub_a)
        weather = f_w.result() if f_w else None
        venue_heads = (f_v.result() if f_v else []) or []
    # injuries sorted by player importance (most important first)
    injuries = sorted(ch["injuries"] + ca["injuries"], key=lambda x: -x["weight"])
    return {
        "weather": weather,
        "sentiment": {"home": ch["composite"], "away": ca["composite"]},
        "breakdown": {"home": ch, "away": ca},
        "injuries": injuries,
        "headlines": {"home": ch["headlines"], "away": ca["headlines"],
                      "venue": venue_heads},
    }
