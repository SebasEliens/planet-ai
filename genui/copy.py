"""The one place an LLM touches the front page: filling copy slots.

Given deterministic ``FrontpageStats`` (already-verified, sourced event data) and
the layout ``Selection`` chosen by ``genui.select``, ask the model for a small set of
headline/blurb strings — never new facts, never HTML. On any failure (no API key, bad
JSON, timeout, provider error) fall back to plain deterministic copy: the build must
never break because of this step. Model reached via OpenRouter so it's a config
string, not a vendor lock-in — see docs/DESIGN.md §2, AGENTS.md §2b.
"""

from __future__ import annotations

import json
import os

import openai
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from genui.select import LayoutMode, Selection
from scripts.frontpage import FrontpageStats

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-haiku-4-5"
REQUEST_TIMEOUT_SECONDS = 30
MAX_OUTPUT_TOKENS = 850


class Copy(BaseModel):
    kicker: str
    headline: str
    dek: str
    intro: str = ""
    trends_note: str = ""
    theme_blurbs: dict[str, str] = Field(default_factory=dict)


def fallback_copy(stats: FrontpageStats, selection: Selection) -> Copy:
    """Plain, factual copy with no LLM involved — used whenever generation fails."""
    if selection.mode is LayoutMode.QUIET:
        return Copy(
            kicker="Status",
            headline="Watching for the next development",
            dek=f"No new tracked events in the last {stats.window_days} days.",
            trends_note="Browse the full log below while we keep watching.",
        )
    lead = stats.recent_events[0]
    n = len(stats.recent_events)
    active_labels = [t.label for t in stats.theme_activity if t.count_window > 0]
    themes_str = ", ".join(active_labels) if active_labels else "tracked themes"
    intro = (
        f"The last {stats.window_days} days brought {n} new event{'s' if n != 1 else ''}"
        f" across {themes_str}."
    )
    return Copy(
        kicker="Recent developments",
        headline=lead.title,
        dek=lead.description or "The latest tracked developments across our themes.",
        intro=intro,
        theme_blurbs={t.id: "" for t in stats.theme_activity if t.count_window > 0},
    )


def _prompt(stats: FrontpageStats, selection: Selection) -> str:
    payload = {
        "mode": selection.mode.value,
        "window_days": stats.window_days,
        "recent_events": [
            {
                "title": e.title,
                "description": e.description,
                "kind": e.kind,
                "themes": list(e.themes),
            }
            for e in stats.recent_events[:8]
        ],
        "theme_activity": [
            {
                "id": t.id,
                "label": t.label,
                "count_window": t.count_window,
                "count_prev_window": t.count_prev_window,
            }
            for t in stats.theme_activity
            if t.count_window > 0
        ],
        "new_entities": [{"title": e.title, "type": e.type} for e in stats.new_entities],
    }
    return (
        "You are writing the front page of PlanetAI, a factual, append-only log of AI "
        "developments in climate justice, human rights, and environmental monitoring. "
        "Everything below is already verified and sourced — do not add any fact, number, "
        "or claim that is not present in it, and do not editorialise beyond what it "
        "supports. Write in a clean, slightly wry news-desk voice.\n\n"
        "Return ONLY a JSON object with exactly these keys:\n"
        '  "kicker": short eyebrow label, at most 8 words\n'
        '  "headline": front-page headline for the lead story (or the period, if quiet), '
        "at most 15 words\n"
        '  "dek": one-sentence subhead for the lead story, at most 30 words\n'
        '  "intro": 2-4 sentence editorial overview of this period as a whole — synthesise '
        "across all events and themes, do not just restate the lead story, at most 80 words\n"
        '  "trends_note": 1-2 sentence synthesis of what to watch next, at most 60 words, or '
        '"" if there is nothing to add\n'
        '  "theme_blurbs": object mapping theme id -> one-sentence blurb, only for themes '
        "present in theme_activity below\n\n"
        f"DATA:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def generate_copy(
    stats: FrontpageStats,
    selection: Selection,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> Copy:
    api_key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return fallback_copy(stats, selection)
    try:
        client = OpenAI(
            base_url=OPENROUTER_BASE_URL, api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _prompt(stats, selection)}],
            response_format={"type": "json_object"},
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.6,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("empty response content")
        return Copy.model_validate(json.loads(content))
    except (ValidationError, json.JSONDecodeError, ValueError, openai.OpenAIError) as exc:
        print(f"genui: copy generation failed, using fallback copy ({exc!r})")
        return fallback_copy(stats, selection)
