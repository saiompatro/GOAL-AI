"""Ground- and weather-aware adjustment layer on top of the base match model.

``predict_fixture`` (in :mod:`goal_ai.predict`) returns venue-neutral outcome
probabilities from the trained models. This module tilts those probabilities
using the **specific football ground**, its **conditions** (altitude, roof,
surface) and the **predicted weather** for the match day, and derives an
expected scoreline. Every adjustment is transparent: ``factors`` explains
exactly what moved the numbers and by how much.

The adjustments are deliberately modest and bounded so the trained model stays
the dominant signal; conditions act as a tie-breaking / context layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Nations comfortable at altitude (Andean / high-plateau footballing nations).
_ALTITUDE_NATIONS = {"Mexico", "Bolivia", "Ecuador", "Colombia", "Peru"}

# Bounds keep conditions from overwhelming the trained model.
_MAX_TILT = 0.12      # max swing between the two teams
_MAX_DRAW_PULL = 0.15  # max mass pulled into the draw


@dataclass
class ContextResult:
    p_home: float
    p_draw: float
    p_away: float
    xg_home: float
    xg_away: float
    likely_score: str
    factors: list[str] = field(default_factory=list)


def _roof_open(venue: dict) -> bool:
    """Whether weather actually reaches the pitch (open roof / open sides)."""
    return str(venue.get("roof", "open")).lower() == "open"


def adjust(base: dict, home: str, away: str, venue: dict, weather: dict,
           host_country: str | None = None) -> ContextResult:
    p_home = float(base["p_home"])
    p_draw = float(base["p_draw"])
    p_away = float(base["p_away"])

    tilt = 0.0          # positive favours home, negative favours away
    draw_pull = 0.0     # extra randomness → mass into the draw
    factors: list[str] = []

    elevation = float(venue.get("elevation_m", 0) or 0)
    roof_open = _roof_open(venue)
    venue_country = venue.get("country")

    # ── Host-nation advantage (playing at home in the host country) ──────────
    for team, sign in ((home, +1), (away, -1)):
        if host_country and team == venue_country == host_country:
            tilt += sign * 0.06
            factors.append(f"Host advantage: {team} playing at home in {host_country} (+6% tilt)")

    # ── Altitude ────────────────────────────────────────────────────────────
    if elevation >= 1200:
        band = "extreme" if elevation >= 2000 else "high"
        home_accl = home in _ALTITUDE_NATIONS
        away_accl = away in _ALTITUDE_NATIONS
        if home_accl and not away_accl:
            tilt += 0.05
            draw_pull += 0.01
            factors.append(f"{band.title()} altitude ({elevation:.0f} m): {home} acclimatised, "
                           f"{away} not (+5% tilt to {home})")
        elif away_accl and not home_accl:
            tilt -= 0.05
            draw_pull += 0.01
            factors.append(f"{band.title()} altitude ({elevation:.0f} m): {away} acclimatised, "
                           f"{home} not (+5% tilt to {away})")
        else:
            draw_pull += 0.03
            factors.append(f"{band.title()} altitude ({elevation:.0f} m): both sides tire — "
                           f"more level, draw more likely")

    # ── Weather (only bites if it reaches the pitch) ─────────────────────────
    temp = weather.get("temp_c")
    precip = weather.get("precip_mm")
    wind = weather.get("wind_kmh")
    humidity = weather.get("humidity")
    goal_damp = 1.0  # multiplier on expected goals

    if not roof_open:
        factors.append(f"{venue.get('roof', 'covered').title()} roof: weather impact on play minimised")
    elif weather.get("source") == "unavailable":
        factors.append("Weather unavailable — conditions not factored")
    else:
        if temp is not None and temp >= 30:
            sev = 0.05 if temp >= 34 else 0.035
            draw_pull += sev
            goal_damp *= 0.92
            extra = " + high humidity" if (humidity or 0) >= 75 else ""
            factors.append(f"Heat {temp:.0f}°C{extra}: slower tempo, the favourite's edge shrinks")
        if precip is not None and precip >= 5:
            draw_pull += 0.05
            goal_damp *= 0.93
            factors.append(f"Wet pitch (~{precip:.0f} mm rain): unpredictable bounce, draw more likely")
        elif precip is not None and precip >= 1:
            draw_pull += 0.02
            factors.append(f"Light showers (~{precip:.0f} mm): slightly more random")
        if wind is not None and wind >= 30:
            draw_pull += 0.02
            goal_damp *= 0.96
            factors.append(f"Strong wind ({wind:.0f} km/h): harder to control long play")

    # ── Apply bounded tilt (move mass between home and away) ─────────────────
    tilt = max(-_MAX_TILT, min(_MAX_TILT, tilt))
    if tilt > 0:
        shift = tilt * p_away
        p_home += shift
        p_away -= shift
    elif tilt < 0:
        shift = -tilt * p_home
        p_away += shift
        p_home -= shift

    # ── Apply bounded draw pull (mass from both winners into the draw) ────────
    draw_pull = max(0.0, min(_MAX_DRAW_PULL, draw_pull))
    if draw_pull > 0:
        take_h = draw_pull * p_home
        take_a = draw_pull * p_away
        p_home -= take_h
        p_away -= take_a
        p_draw += take_h + take_a

    # Renormalise defensively.
    total = p_home + p_draw + p_away
    p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

    # ── Expected scoreline (transparent Poisson-style heuristic) ─────────────
    supremacy = p_home - p_away
    base_goals = 1.45
    xg_home = max(0.3, (base_goals + 1.2 * supremacy) * goal_damp)
    xg_away = max(0.3, (base_goals - 1.2 * supremacy) * goal_damp)
    likely = f"{round(xg_home)}–{round(xg_away)}"

    return ContextResult(
        p_home=p_home, p_draw=p_draw, p_away=p_away,
        xg_home=round(xg_home, 2), xg_away=round(xg_away, 2),
        likely_score=likely, factors=factors,
    )
