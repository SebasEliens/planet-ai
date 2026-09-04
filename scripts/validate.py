"""Validate the ``kb/`` bundle before it is built or merged.

Checks: frontmatter schema, event/entity link resolution, slug/date consistency,
no ``[[wikilinks]]``, and — against ``origin/main`` when available — that no existing
event file was modified or deleted (append-only).

Run: ``uv run python -m scripts.validate``  (exit 1 on any error)
"""

from __future__ import annotations

import re
import subprocess
import sys

from scripts.kb import (
    REPO_ROOT,
    event_kinds,
    load_entities,
    load_events,
    load_taxonomy,
    theme_ids,
)

WIKILINK = re.compile(r"\[\[[^\]]+\]\]")


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def check_immutability(errors: list[str]) -> None:
    """Fail if any existing kb/events/** file was modified or deleted vs origin/main."""
    _git("fetch", "--quiet", "origin", "main")
    base = _git("merge-base", "HEAD", "origin/main")
    if not base:
        print("  (immutability: no origin/main to compare against — skipped)")
        return
    changed = _git("diff", "--name-only", "--diff-filter=MD", base, "HEAD", "--", "kb/events")
    if changed:
        for line in changed.splitlines():
            errors.append(f"immutable event file changed/deleted: {line}")


def main() -> int:
    tax = load_taxonomy()
    themes = theme_ids(tax)
    kinds = event_kinds(tax)
    entity_refs = {e.ref for e in load_entities()}
    events = load_events()
    errors: list[str] = []
    seen_slugs: set[str] = set()

    for ent in load_entities():
        if not ent.type:
            errors.append(f"{ent.rel}: missing frontmatter `type`")
        if not ent.title:
            errors.append(f"{ent.rel}: missing `title`")
        if WIKILINK.search(ent.body):
            errors.append(f"{ent.rel}: contains [[wikilink]] — use Markdown links")

    for e in events:
        loc = e.rel
        if e.meta.get("type") != "Event":
            errors.append(f"{loc}: frontmatter `type` must be `Event`")
        if e.kind not in kinds:
            errors.append(f"{loc}: kind {e.kind!r} not in taxonomy.event_kinds")
        if not e.title:
            errors.append(f"{loc}: missing `title`")
        if not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", e.date):
            errors.append(f"{loc}: `date` must be YYYY-MM or YYYY-MM-DD (got {e.date!r})")
        elif not e.slug.startswith(e.date):
            errors.append(f"{loc}: filename must start with the event `date` ({e.date})")
        if e.date[:4] and e.year != e.date[:4]:
            errors.append(f"{loc}: year directory {e.year!r} != date year {e.date[:4]!r}")
        if e.slug in seen_slugs:
            errors.append(f"{loc}: duplicate event slug {e.slug!r}")
        seen_slugs.add(e.slug)
        if not e.themes:
            errors.append(f"{loc}: `themes` is empty")
        for t in e.themes:
            if t not in themes:
                errors.append(f"{loc}: theme {t!r} not in taxonomy")
        if not e.sources:
            errors.append(f"{loc}: needs at least one source")
        for s in e.sources:
            if not str(s.get("resource", "")).strip():
                errors.append(f"{loc}: a source is missing `resource`")
        for ref in e.entities:
            if ref not in entity_refs:
                errors.append(f"{loc}: entity {ref!r} has no page under kb/entities/")
        if WIKILINK.search(e.body):
            errors.append(f"{loc}: contains [[wikilink]] — use Markdown links")

    check_immutability(errors)

    if errors:
        print(f"\n✗ {len(errors)} problem(s):")
        for msg in errors:
            print(f"  - {msg}")
        return 1
    print(f"✓ {len(events)} events, {len(entity_refs)} entities — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
