"""Hugging Face powered insights — offline, batch, cached to Firebase.

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


_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
_SYSTEM_PROMPT_TEAM = (
    "You are a concise football analyst. Summarize the following team statistics "
    "in one sentence of at most 40 words."
)
_SYSTEM_PROMPT_PLAYER = (
    "You are a concise football analyst. Summarize the following player statistics "
    "in one sentence of at most 35 words."
)


def _load_generator():
    try:
        from transformers import pipeline  # type: ignore
        return pipeline("text-generation", model=_MODEL_ID)
    except Exception as e:
        print(f"[hf] transformers unavailable ({e}); using template fallback")
        return None


def _generate(generator, system_prompt: str, user_text: str, fallback: str) -> str:
    if generator is None:
        return _template(fallback)
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        out = generator(messages, max_new_tokens=60, do_sample=False)
        # Chat-format pipelines return generated_text as a list of message dicts
        generated = out[0]["generated_text"]
        if isinstance(generated, list):
            return generated[-1]["content"].strip()
        return str(generated).strip()
    except Exception:
        return _template(fallback)


def summarize_teams(team_stats: Iterable[tuple[str, dict]]) -> list[dict]:
    generator = _load_generator()
    rows = []
    for team, stats in team_stats:
        block = _stat_block_team(team, stats)
        summary = _generate(generator, _SYSTEM_PROMPT_TEAM, block, block)
        rows.append({
            "entity_type": "team",
            "entity_key": team,
            "summary_text": summary,
            "model": _MODEL_ID if generator else "template",
        })
    return rows


def summarize_players(players: pd.DataFrame, limit_per_team: int = 11) -> list[dict]:
    """Generate a short insight per top-11 player per team."""
    if players.empty:
        return []
    generator = _load_generator()
    rows = []
    for team, g in players.groupby("team"):
        top = g.sort_values("overall", ascending=False).head(limit_per_team)
        for p in top.itertuples(index=False):
            block = (
                f"{p.player_name} plays for {getattr(p, 'club_name', 'Unknown club')} and represents {team}. "
                f"Position {p.primary_position}. Overall {p.overall}, potential {getattr(p,'potential',0)}, "
                f"age {getattr(p,'age',0)}, preferred foot {getattr(p,'preferred_foot','unknown')}. "
                f"Pace {getattr(p,'pace',0)}, shooting {getattr(p,'shooting',0)}, passing {getattr(p,'passing',0)}, "
                f"dribbling {getattr(p,'dribbling',0)}, defending {getattr(p,'defending',0)}, physic {getattr(p,'physic',0)}. "
                f"Market value EUR {getattr(p,'value_eur',0):.0f}, wage EUR {getattr(p,'wage_eur',0):.0f}."
            )
            summary = _generate(generator, _SYSTEM_PROMPT_PLAYER, block, block)
            rows.append({
                "entity_type": "player",
                "entity_key": p.player_name,
                "team": team,
                "summary_text": summary,
                "model": _MODEL_ID if generator else "template",
            })
    return rows
