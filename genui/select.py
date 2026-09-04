"""Deterministic layout + accent selection for the front page.

Pure function over ``FrontpageStats`` — no LLM. This is what makes the page's design
respond to "the latest results": which template renders and which theme colours the
page are both decided by data shape, not by the model. See docs/DESIGN.md §4.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from scripts.frontpage import FrontpageStats

# If the lead story's score beats the runner-up by at least this much, it gets the
# single-story HEADLINE treatment instead of being folded into a DIGEST grid.
HEADLINE_SCORE_GAP = 2.0

NEUTRAL_ACCENT = "neutral"


class LayoutMode(StrEnum):
    HEADLINE = "headline"
    DIGEST = "digest"
    QUIET = "quiet"


@dataclass(frozen=True)
class Selection:
    mode: LayoutMode
    accent: str  # a taxonomy theme id, or NEUTRAL_ACCENT


def _dominant_theme(stats: FrontpageStats) -> str:
    active = [t for t in stats.theme_activity if t.count_window > 0]
    return active[0].id if active else NEUTRAL_ACCENT


def choose(stats: FrontpageStats) -> Selection:
    events = stats.recent_events  # pre-sorted by score, descending
    if not events:
        return Selection(mode=LayoutMode.QUIET, accent=_dominant_theme(stats))

    top = events[0]
    runner_up_score = events[1].score if len(events) > 1 else 0.0
    is_single_story = len(events) == 1 or (top.score - runner_up_score) >= HEADLINE_SCORE_GAP

    if is_single_story:
        accent = top.themes[0] if top.themes else _dominant_theme(stats)
        return Selection(mode=LayoutMode.HEADLINE, accent=accent)

    return Selection(mode=LayoutMode.DIGEST, accent=_dominant_theme(stats))
