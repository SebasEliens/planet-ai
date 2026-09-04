"""Deterministic stats for the generative front page.

Pure code, no LLM: computes ``FrontpageStats`` from the projected event/entity data
and (de)serialises ``build/frontpage.json``. ``scripts.project`` writes it; ``genui``
reads it and is the only place an LLM enters the picture (copy only — see
``genui.copy``). "Recent" is windowed on the event's ``date`` (when it happened), not
when it was added to the log — see docs/DESIGN.md's "living map of trends" framing.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.kb import REPO_ROOT, Entity, Event, theme_labels

WINDOW_DAYS = 30
FRONTPAGE_JSON = REPO_ROOT / "build" / "frontpage.json"


def _event_date(e: Event) -> dt.date | None:
    parts = e.date.split("-")
    try:
        y = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 1
        d = int(parts[2]) if len(parts) > 2 else 1
        return dt.date(y, m, d)
    except (ValueError, IndexError):
        return None


def _score(e: Event) -> float:
    """Lead-story score: more corroborating sources and linked entities rank higher."""
    return 2 * len(e.sources) + len(e.entities)


@dataclass(frozen=True)
class EventBrief:
    rel: str
    date: str
    kind: str
    title: str
    description: str
    themes: tuple[str, ...]
    entities: tuple[str, ...]
    score: float


@dataclass(frozen=True)
class ThemeActivity:
    id: str
    label: str
    count_window: int
    count_prev_window: int


@dataclass(frozen=True)
class EntityBrief:
    ref: str
    title: str
    type: str


@dataclass(frozen=True)
class JobOpenings:
    rel: str
    date: str
    title: str


@dataclass(frozen=True)
class FrontpageStats:
    generated_at: str
    window_days: int
    total_events: int
    total_entities: int
    recent_events: tuple[EventBrief, ...]  # sorted by score, descending
    theme_activity: tuple[ThemeActivity, ...]  # sorted by count_window, descending
    new_entities: tuple[EntityBrief, ...]
    job_openings: JobOpenings | None


def compute_stats(
    events: list[Event],
    entities: list[Entity],
    taxonomy: dict[str, Any],
    *,
    now: dt.datetime | None = None,
    window_days: int = WINDOW_DAYS,
) -> FrontpageStats:
    now = now or dt.datetime.now(dt.UTC)
    today = now.date()
    window_start = today - dt.timedelta(days=window_days)
    prev_start = today - dt.timedelta(days=2 * window_days)
    prev_end = window_start - dt.timedelta(days=1)

    def dated(subset: list[Event], start: dt.date, end: dt.date) -> list[Event]:
        out = []
        for e in subset:
            d = _event_date(e)
            if d is not None and start <= d <= end:
                out.append(e)
        return out

    recent = dated(events, window_start, today)
    prev = dated(events, prev_start, prev_end)
    recent_sorted = sorted(recent, key=_score, reverse=True)

    briefs = tuple(
        EventBrief(
            rel=e.rel,
            date=e.date,
            kind=e.kind,
            title=e.title,
            description=e.description,
            themes=e.themes,
            entities=e.entities,
            score=_score(e),
        )
        for e in recent_sorted
    )

    labels = theme_labels(taxonomy)
    activity = [
        ThemeActivity(
            id=tid,
            label=label,
            count_window=sum(1 for e in recent if tid in e.themes),
            count_prev_window=sum(1 for e in prev if tid in e.themes),
        )
        for tid, label in labels.items()
    ]
    activity.sort(key=lambda t: t.count_window, reverse=True)

    # Proxy for "new this period": entities referenced only by events in the window.
    # (kb/ carries no entity creation timestamp; good enough for a front-page signal.)
    recent_refs = {ref for e in recent for ref in e.entities}
    new_entities = tuple(
        EntityBrief(ref=en.ref, title=en.title, type=en.type)
        for en in entities
        if en.ref in recent_refs
    )

    latest_jobs = next((e for e in events if e.kind == "job-openings"), None)
    job_openings = (
        JobOpenings(rel=latest_jobs.rel, date=latest_jobs.date, title=latest_jobs.title)
        if latest_jobs
        else None
    )

    return FrontpageStats(
        generated_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        window_days=window_days,
        total_events=len(events),
        total_entities=len(entities),
        recent_events=briefs,
        theme_activity=tuple(activity),
        new_entities=new_entities,
        job_openings=job_openings,
    )


def to_json(stats: FrontpageStats) -> dict[str, Any]:
    return asdict(stats)


def from_json(data: dict[str, Any]) -> FrontpageStats:
    jobs = data.get("job_openings")
    return FrontpageStats(
        generated_at=data["generated_at"],
        window_days=data["window_days"],
        total_events=data["total_events"],
        total_entities=data["total_entities"],
        recent_events=tuple(
            EventBrief(
                rel=e["rel"],
                date=e["date"],
                kind=e["kind"],
                title=e["title"],
                description=e["description"],
                themes=tuple(e["themes"]),
                entities=tuple(e["entities"]),
                score=e["score"],
            )
            for e in data["recent_events"]
        ),
        theme_activity=tuple(ThemeActivity(**t) for t in data["theme_activity"]),
        new_entities=tuple(EntityBrief(**e) for e in data["new_entities"]),
        job_openings=JobOpenings(**jobs) if jobs else None,
    )


def write(stats: FrontpageStats, path: Path = FRONTPAGE_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_json(stats), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def load(path: Path = FRONTPAGE_JSON) -> FrontpageStats:
    return from_json(json.loads(path.read_text(encoding="utf-8")))
