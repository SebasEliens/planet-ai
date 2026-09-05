"""Read-only loaders for the ``kb/`` OKF bundle.

Shared by ``scripts.project`` (build the derived bundle) and ``scripts.validate``
(check it). Writing events/entities is the research agent's job (``agent.store``).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frontmatter
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
KB = REPO_ROOT / "kb"
EVENTS_DIR = KB / "events"
ENTITIES_DIR = KB / "entities"
TAXONOMY = REPO_ROOT / "taxonomy.yaml"


def _as_date_str(value: Any) -> str:
    """Normalise a frontmatter date (``datetime.date`` or ``str``) to ``YYYY-MM[-DD]``."""
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value).strip()


def _str_tuple(value: object) -> tuple[str, ...]:
    return tuple(str(x) for x in value) if isinstance(value, list) else ()


def _any_tuple(value: object) -> tuple[Any, ...]:
    return tuple(value) if isinstance(value, list) else ()


def rfc3339(date_str: str) -> str:
    """``2023-08`` / ``2023-08-03`` -> an RFC3339 instant (midnight UTC)."""
    parts = date_str.split("-")
    y = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 1
    d = int(parts[2]) if len(parts) > 2 else 1
    return dt.datetime(y, m, d, tzinfo=dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Event:
    path: Path
    rel: str  # bundle-relative posix path, e.g. "events/2023/2023-08-03-foo.md"
    slug: str
    year: str
    date: str
    kind: str
    title: str
    description: str
    themes: tuple[str, ...]
    entities: tuple[str, ...]
    sources: tuple[Any, ...]
    body: str
    meta: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def sort_key(self) -> tuple[str, str]:
        # pad "2023-08" so it orders next to "2023-08-01"
        return ((self.date + "-01") if len(self.date) == 7 else self.date, self.slug)


@dataclass(frozen=True)
class Entity:
    path: Path
    rel: str  # "entities/orgs/nasa.md"
    ref: str  # "orgs/nasa"
    kind: str  # "orgs"
    slug: str
    type: str  # frontmatter `type`, e.g. "Organization"
    title: str
    description: str
    body: str
    meta: dict[str, Any] = field(repr=False, default_factory=dict)


def _iter_md(root: Path) -> Iterator[Path]:
    for p in sorted(root.rglob("*.md")):
        if p.name in {"index.md", "log.md"}:
            continue
        yield p


def load_events(bundle_root: Path = KB) -> list[Event]:
    """Load events under ``bundle_root/events``. Defaults to the real kb/; pass a
    different bundle root (e.g. a tmp_path fixture) to load an isolated test bundle."""
    events: list[Event] = []
    events_dir = bundle_root / "events"
    if not events_dir.is_dir():
        return events
    for p in _iter_md(events_dir):
        post = frontmatter.load(p)
        m = post.metadata
        rel = p.relative_to(bundle_root).as_posix()
        events.append(
            Event(
                path=p,
                rel=rel,
                slug=p.stem,
                year=p.parent.name,
                date=_as_date_str(m.get("date", "")),
                kind=str(m.get("kind", "")),
                title=str(m.get("title", p.stem)),
                description=str(m.get("description", "")).strip(),
                themes=_str_tuple(m.get("themes")),
                entities=_str_tuple(m.get("entities")),
                sources=_any_tuple(m.get("sources")),
                body=post.content.strip(),
                meta=dict(m),
            )
        )
    events.sort(key=lambda e: e.sort_key, reverse=True)
    return events


def load_entities(bundle_root: Path = KB) -> list[Entity]:
    """Load entities under ``bundle_root/entities``. See ``load_events`` re: bundle_root."""
    entities: list[Entity] = []
    entities_dir = bundle_root / "entities"
    if not entities_dir.is_dir():
        return entities
    for p in _iter_md(entities_dir):
        post = frontmatter.load(p)
        m = post.metadata
        kind = p.parent.name
        entities.append(
            Entity(
                path=p,
                rel=p.relative_to(bundle_root).as_posix(),
                ref=f"{kind}/{p.stem}",
                kind=kind,
                slug=p.stem,
                type=str(m.get("type", "")),
                title=str(m.get("title", p.stem)),
                description=str(m.get("description", "")).strip(),
                body=post.content.strip(),
                meta=dict(m),
            )
        )
    return entities


def load_taxonomy() -> dict[str, Any]:
    with TAXONOMY.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


def theme_ids(taxonomy: dict[str, Any]) -> set[str]:
    return {t["id"] for t in taxonomy.get("themes", [])}


def theme_labels(taxonomy: dict[str, Any]) -> dict[str, str]:
    return {t["id"]: t.get("label", t["id"]) for t in taxonomy.get("themes", [])}


def event_kinds(taxonomy: dict[str, Any]) -> set[str]:
    return set(taxonomy.get("event_kinds", []))


def load_site_config() -> dict[str, Any]:
    cfg_path = KB / ".kiso" / "configuration.yaml"
    if not cfg_path.is_file():
        return {}
    with cfg_path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}
    return data


def base_url() -> str:
    site = load_site_config().get("site", {})
    url = str(site.get("baseUrl", "")).strip()
    return url if url.endswith("/") or not url else url + "/"
