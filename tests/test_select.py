"""`genui.select` — deterministic layout + accent choice from FrontpageStats."""

from genui.select import LayoutMode, choose
from scripts.frontpage import EventBrief, FrontpageStats, ThemeActivity

BASE = {
    "generated_at": "2026-09-04T00:00:00Z",
    "window_days": 30,
    "total_events": 10,
    "total_entities": 5,
    "new_entities": (),
    "job_openings": None,
}


def _event(rel: str, score: float, themes: tuple[str, ...] = ("climate-justice",)) -> EventBrief:
    return EventBrief(
        rel=rel,
        date="2026-09-01",
        kind="news",
        title=rel,
        description="",
        themes=themes,
        entities=(),
        score=score,
    )


def test_no_recent_events_is_quiet() -> None:
    stats = FrontpageStats(recent_events=(), theme_activity=(), **BASE)
    sel = choose(stats)
    assert sel.mode is LayoutMode.QUIET


def test_single_event_is_headline() -> None:
    stats = FrontpageStats(recent_events=(_event("a", 5),), theme_activity=(), **BASE)
    sel = choose(stats)
    assert sel.mode is LayoutMode.HEADLINE
    assert sel.accent == "climate-justice"


def test_dominant_story_is_headline() -> None:
    events = (_event("a", 10, ("ai-human-rights",)), _event("b", 2), _event("c", 1))
    stats = FrontpageStats(recent_events=events, theme_activity=(), **BASE)
    sel = choose(stats)
    assert sel.mode is LayoutMode.HEADLINE
    assert sel.accent == "ai-human-rights"


def test_close_scores_is_digest_with_dominant_theme_accent() -> None:
    events = (_event("a", 3), _event("b", 2.5), _event("c", 2))
    # theme_activity is a contract from compute_stats: sorted by count_window, descending.
    activity = (
        ThemeActivity(
            id="climate-justice", label="Climate Justice", count_window=2, count_prev_window=1
        ),
        ThemeActivity(
            id="ai-human-rights", label="AI & Human Rights", count_window=1, count_prev_window=0
        ),
    )
    stats = FrontpageStats(recent_events=events, theme_activity=activity, **BASE)
    sel = choose(stats)
    assert sel.mode is LayoutMode.DIGEST
    assert sel.accent == "climate-justice"  # first entry per the sorted-by-compute_stats contract


def test_quiet_falls_back_to_neutral_when_no_activity() -> None:
    stats = FrontpageStats(recent_events=(), theme_activity=(), **BASE)
    assert choose(stats).accent == "neutral"
