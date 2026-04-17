"""Hugging Face powered insights — offline, batch, cached to Supabase.

Uses a small summarization model to turn structured stat blocks into short
natural-language insights for teams and players. Kept deliberately lightweight;
if transformers isn't installed, falls back to a template so the pipeline still
produces `insights` rows.
"""
from __future__ import annotations

import textwrap
from typing import Iterable

import pandas as pd


def _stat_block_team(team: str, stats: dict) -> str:
    return textwrap.dedent(f"""
    Team: {team}. Elo {stats.get('elo', 0):.0f}. Form last 10 win rate {stats.get('win_rate_10', 0):.0%},
    goals for {stats.get('gf_10', 0):.2f}/game, goals against {stats.get('ga_10', 0):.2f}/game.
    Squad top-11 average rating {stats.get('top11_mean', 0):.1f}, star-3 {stats.get('star3_mean', 0):.1f}.
    Attack {stats.get('att_mean', 0):.1f}, midfield {stats.get('mid_mean', 0):.1f}, defence {stats.get('def_mean', 0):.1f}.
    """).strip()


def _template(text: str) -> str:
    # Extractive-style compression so we always have something reasonable.
    return " ".join(text.split())[:240]


def _load_summarizer():
    try:
        from transformers import pipeline  # type: ignore
        return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    except Exception as e:
        print(f"[hf] transformers unavailable ({e}); using template fallback")
        return None


def summarize_teams(team_stats: Iterable[tuple[str, dict]]) -> list[dict]:
    summarizer = _load_summarizer()
    rows = []
    for team, stats in team_stats:
        block = _stat_block_team(team, stats)
        if summarizer is None:
            summary = _template(block)
        else:
            try:
                out = summarizer(block, max_length=60, min_length=20, do_sample=False)
                summary = out[0]["summary_text"].strip()
            except Exception:
                summary = _template(block)
        rows.append({
            "entity_type": "team",
            "entity_key": team,
            "summary_text": summary,
            "model": "distilbart-cnn-12-6" if summarizer else "template",
        })
    return rows


def summarize_players(players: pd.DataFrame, limit_per_team: int = 11) -> list[dict]:
    """Generate a short insight per top-11 player per team."""
    if players.empty:
        return []
    summarizer = _load_summarizer()
    rows = []
    for team, g in players.groupby("nationality_name"):
        top = g.sort_values("overall", ascending=False).head(limit_per_team)
        for p in top.itertuples(index=False):
            block = (
                f"{p.long_name}, nationality {p.nationality_name}, position {p.player_positions}. "
                f"Overall rating {p.overall}. Pace {getattr(p,'pace',0)}, shooting {getattr(p,'shooting',0)}, "
                f"passing {getattr(p,'passing',0)}, defending {getattr(p,'defending',0)}."
            )
            if summarizer is None:
                summary = _template(block)
            else:
                try:
                    out = summarizer(block, max_length=50, min_length=15, do_sample=False)
                    summary = out[0]["summary_text"].strip()
                except Exception:
                    summary = _template(block)
            rows.append({
                "entity_type": "player",
                "entity_key": p.long_name,
                "team": team,
                "summary_text": summary,
                "model": "distilbart-cnn-12-6" if summarizer else "template",
            })
    return rows
