"""Append-only writers on top of ``scripts.kb``. Never touches an existing file.

Everything the research agent writes goes through here: it's the one place that turns
a verified ``EventDraft`` into files on disk, and the one place that decides whether a
mentioned entity needs a new stub page or already has one. See AGENTS.md §2a.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

import yaml

from agent.schema import ENTITY_KIND_DIRS, EntityMention, EventDraft
from scripts.kb import KB, load_entities, load_events

SLUG_MAX_LEN = 70


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = re.sub(r"-{2,}", "-", text)
    if len(text) > SLUG_MAX_LEN:
        # trim to the last whole word so we don't cut off mid-token
        text = text[:SLUG_MAX_LEN].rsplit("-", 1)[0]
    return text or "untitled"


def known_source_urls(kb_root: Path = KB) -> set[str]:
    urls: set[str] = set()
    for e in load_events(kb_root):
        for s in e.sources:
            resource = s.get("resource") if isinstance(s, dict) else None
            if resource:
                urls.add(str(resource).rstrip("/"))
    return urls


def known_entity_titles(kb_root: Path = KB) -> dict[str, str]:
    """Lowercased title -> ref, for matching a mention against an existing entity."""
    return {en.title.strip().lower(): en.ref for en in load_entities(kb_root)}


def known_entity_refs(kb_root: Path = KB) -> set[str]:
    return {en.ref for en in load_entities(kb_root)}


def resolve_entity_ref(
    mention: EntityMention, known_titles: dict[str, str], known_refs: set[str]
) -> str:
    """The ref to actually use for this mention: reuse an existing entity if the model's
    guess matches one (by ref or by title), otherwise a fresh, slugified ref."""
    if mention.ref in known_refs:
        return mention.ref
    by_title = known_titles.get(mention.title.strip().lower())
    if by_title:
        return by_title
    kind_dir = ENTITY_KIND_DIRS.get(mention.type, "topics")
    return f"{kind_dir}/{slugify(mention.title)}"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix, parent, n = path.stem, path.suffix, path.parent, 2
    while (parent / f"{stem}-{n}{suffix}").exists():
        n += 1
    return parent / f"{stem}-{n}{suffix}"


def _write_frontmatter(path: Path, fm: dict[str, Any], body: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    yaml_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=100)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{yaml_text}---\n\n{body.strip()}\n", encoding="utf-8")


def event_path(draft: EventDraft, kb_root: Path = KB) -> Path:
    year = draft.date[:4]
    slug = f"{draft.date}-{slugify(draft.title)}"
    return _unique_path(kb_root / "events" / year / f"{slug}.md")


def write_event(draft: EventDraft, model: str, entity_refs: list[str], kb_root: Path = KB) -> Path:
    """Write the immutable event file. Caller resolves ``entity_refs`` first (see
    ``resolve_entity_ref``) so the frontmatter always points at real entity pages."""
    path = event_path(draft, kb_root)
    fm = {
        "type": "Event",
        "kind": draft.kind,
        "title": draft.title,
        "description": draft.description,
        "date": draft.date,
        "themes": draft.themes,
        "entities": entity_refs,
        "tags": draft.tags,
        "generated": {
            "by": f"planetai/openrouter:{model}",
            "at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "status": "stable",
        "sources": [s.model_dump(exclude_defaults=True) for s in draft.sources],
    }
    _write_frontmatter(path, fm, draft.body)
    return path


def write_entity_stub(
    mention: EntityMention, ref: str, themes: list[str], kb_root: Path = KB
) -> Path:
    kind_dir, slug = ref.split("/", 1)
    path = kb_root / "entities" / kind_dir / f"{slug}.md"
    description = mention.description.strip()
    intro = (
        description
        or f"{mention.title} — entity page created automatically from a linked event; "
        "a fuller description can be added later."
    )
    fm = {
        "type": mention.type,
        "title": mention.title,
        "description": description,
        "themes": themes,
        "tags": [],
    }
    _write_frontmatter(path, fm, f"{intro}\n\n<!-- timeline -->")
    return path
