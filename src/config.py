"""Lightweight .env loader (no external dependency).

Reads <project root>/.env into the environment on import, so scripts can pick up
secrets like FOOTBALL_DATA_TOKEN without pasting them on the command line.
A token passed explicitly as a CLI arg still takes precedence.
"""
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load_env():
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()


def get_token():
    return os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()


def get_apifootball_key():
    """API-Football (api-sports.io) key — enables live WC match statistics
    (shots, shots on target, possession, xG) in recent_stats.py. Optional."""
    return os.environ.get("API_FOOTBALL_KEY", "").strip()
