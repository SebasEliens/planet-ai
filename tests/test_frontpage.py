"""`scripts.frontpage` — deterministic stats for the generative front page."""

import datetime as dt
from pathlib import Path

from scripts.frontpage import compute_stats, from_json, to_json
from scripts.kb import Entity, Event

NOW = dt.datetime(2026, 9, 4, tzinfo=dt.UTC)
TAXONOMY = {
    "themes": [
        {"id": "climate-justice", "label": "Climate Justice"},
        {"id": "ai-human-rights", "label": "AI & Human Rights"},
    ]
}


def _event(
    slug: str,
    date: str,
    *,
    themes: tuple[str, ...] = (),
    entities: tuple[str, ...] = (),
    n_sources: int = 1,
    kind: str = "news",
) -> Event:
    return Event(
        path=Path(f"kb/events/{date[:4]}/{slug}.md"),
        rel=f"events/{date[:4]}/{slug}.md",
        slug=slug,
        year=date[:4],
        date=date,
        kind=kind,
        title=slug,
        description=f"{slug} description",
        themes=themes,
        entities=entities,
        sources=tuple({"resource": f"https://x/{i}"} for i in range(n_sources)),
        body="body",
    )


def _entity(ref: str, title: str = "Entity") -> Entity:
    kind, slug = ref.split("/")
    return Entity(
        path=Path(f"kb/entities/{ref}.md"),
        rel=f"entities/{ref}.md",
        ref=ref,
        kind=kind,
        slug=slug,
        type="Organization",
        title=title,
        description="",
        body="",
    )


def test_windowing_and_scoring() -> None:
    events = [
        _event(
            "2026-08-20-a",
            "2026-08-20",
            themes=("climate-justice",),
            entities=("orgs/x",),
            n_sources=2,
        ),  # 15 days ago, in window, score 2*2+1=5
        _event("2026-08-25-b", "2026-08-25", themes=("ai-human-rights",), n_sources=1),  # score 2
        _event("2023-01-01-old", "2023-01-01", themes=("climate-justice",)),  # way outside
        _event(
            "2026-07-10-prev", "2026-07-10", themes=("climate-justice",)
        ),  # 56d ago: prev window
    ]
    entities = [_entity("orgs/x", "X Org")]

    stats = compute_stats(events, entities, TAXONOMY, now=NOW, window_days=30)

    assert stats.total_events == 4
    assert [e.rel for e in stats.recent_events] == [
        "events/2026/2026-08-20-a.md",
        "events/2026/2026-08-25-b.md",
    ]
    assert stats.recent_events[0].score == 5
    assert stats.recent_events[1].score == 2

    by_id = {t.id: t for t in stats.theme_activity}
    assert by_id["climate-justice"].count_window == 1
    assert by_id["climate-justice"].count_prev_window == 1
    assert by_id["ai-human-rights"].count_window == 1
    assert by_id["ai-human-rights"].count_prev_window == 0

    assert [e.ref for e in stats.new_entities] == ["orgs/x"]
    assert stats.job_openings is None


def test_job_openings_picked_up() -> None:
    events = [_event("2026-09-jobs", "2026-09", kind="job-openings")]
    stats = compute_stats(events, [], TAXONOMY, now=NOW)
    assert stats.job_openings is not None
    assert stats.job_openings.rel == "events/2026/2026-09-jobs.md"


def test_no_recent_events_is_empty_not_crashing() -> None:
    stats = compute_stats([], [], TAXONOMY, now=NOW)
    assert stats.recent_events == ()
    assert stats.total_events == 0


def test_json_roundtrip() -> None:
    events = [
        _event("2026-08-20-a", "2026-08-20", themes=("climate-justice",), entities=("orgs/x",))
    ]
    stats = compute_stats(events, [_entity("orgs/x")], TAXONOMY, now=NOW)
    assert from_json(to_json(stats)) == stats
