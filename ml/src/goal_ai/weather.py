"""Match-day weather for a venue via the free Open-Meteo API (no API key).

- Within the forecast horizon (~16 days) we use the live forecast endpoint.
- Beyond it (e.g. a 2026 fixture seen from today) we fall back to a
  climatology estimate built from the historical archive for the same
  calendar day across recent years.

Every function degrades gracefully: if the network is unavailable the caller
gets ``source="unavailable"`` and can still render the rest of the page.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_TIMEOUT = 15


def _describe(temp_c: float, precip_mm: float, wind_kmh: float, humidity: float) -> str:
    parts = []
    if temp_c >= 32:
        parts.append("very hot")
    elif temp_c >= 27:
        parts.append("hot")
    elif temp_c >= 18:
        parts.append("mild")
    elif temp_c >= 10:
        parts.append("cool")
    else:
        parts.append("cold")
    if humidity >= 75:
        parts.append("humid")
    if precip_mm >= 5:
        parts.append("wet (rain likely)")
    elif precip_mm >= 1:
        parts.append("light showers")
    else:
        parts.append("dry")
    if wind_kmh >= 30:
        parts.append("windy")
    return ", ".join(parts)


_DAILY = "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"


def _mean_humidity(payload: dict) -> float:
    vals = [h for h in payload.get("hourly", {}).get("relative_humidity_2m", []) if h is not None]
    return round(sum(vals) / len(vals), 1) if vals else 70.0


def _query(url: str, lat: float, lon: float, target: date) -> dict | None:
    r = requests.get(
        url,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": _DAILY,
            "hourly": "relative_humidity_2m",
            "start_date": target.isoformat(),
            "end_date": target.isoformat(),
            "timezone": "auto",
        },
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def _forecast(lat: float, lon: float, target: date) -> dict | None:
    try:
        payload = _query(FORECAST_URL, lat, lon, target)
        d = payload.get("daily", {})
        if not d.get("time"):
            return None
        tmax = d["temperature_2m_max"][0]
        tmin = d["temperature_2m_min"][0]
        return {
            "source": "forecast",
            "temp_c": round((tmax + tmin) / 2, 1),
            "temp_max_c": tmax,
            "temp_min_c": tmin,
            "precip_mm": d["precipitation_sum"][0] or 0.0,
            "wind_kmh": d["wind_speed_10m_max"][0] or 0.0,
            "humidity": _mean_humidity(payload),
        }
    except Exception:
        return None


def _climatology(lat: float, lon: float, target: date, years: int = 5) -> dict | None:
    """Average the same calendar day over the last few archived years."""
    samples = []
    for back in range(1, years + 1):
        try:
            day = target.replace(year=target.year - back)
        except ValueError:  # Feb 29 etc.
            day = target.replace(year=target.year - back, day=28)
        try:
            payload = _query(ARCHIVE_URL, lat, lon, day)
            d = payload.get("daily", {})
            if d.get("time") and d["temperature_2m_max"][0] is not None:
                samples.append({
                    "tmax": d["temperature_2m_max"][0],
                    "tmin": d["temperature_2m_min"][0],
                    "precip": d["precipitation_sum"][0] or 0.0,
                    "wind": d["wind_speed_10m_max"][0] or 0.0,
                    "hum": _mean_humidity(payload),
                })
        except Exception:
            continue
    if not samples:
        return None
    n = len(samples)
    tmax = sum(s["tmax"] for s in samples) / n
    tmin = sum(s["tmin"] for s in samples) / n
    return {
        "source": f"climatology ({n}-yr avg)",
        "temp_c": round((tmax + tmin) / 2, 1),
        "temp_max_c": round(tmax, 1),
        "temp_min_c": round(tmin, 1),
        "precip_mm": round(sum(s["precip"] for s in samples) / n, 1),
        "wind_kmh": round(sum(s["wind"] for s in samples) / n, 1),
        "humidity": round(sum(s["hum"] for s in samples) / n, 1),
    }


def match_day_weather(lat: float, lon: float, target: date) -> dict:
    """Best-available weather for ``target`` at (lat, lon)."""
    today = date.today()
    horizon = today + timedelta(days=15)
    out = None
    if today <= target <= horizon:
        out = _forecast(lat, lon, target)
    if out is None:
        out = _climatology(lat, lon, target)
    if out is None:
        return {"source": "unavailable", "temp_c": None, "precip_mm": None,
                "wind_kmh": None, "humidity": None, "summary": "Weather data unavailable (offline)"}
    out["summary"] = _describe(out["temp_c"], out["precip_mm"], out["wind_kmh"], out["humidity"])
    return out
