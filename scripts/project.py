"""Project ``kb/`` into a derived OKF bundle Kiso can build.

Reads the immutable event log + entity pages and writes ``build/okf/``:
copies events, fills each entity's ``<!-- timeline -->``, generates ``index.md``
per directory plus per-theme pages and a root ``log.md``, and emits
``build/feed.xml`` (Atom). ``kb/`` stays minimal; ``build/`` is disposable.

Run: ``uv run python -m scripts.project``
"""

from __future__ import annotations

import shutil
from pathlib import Path
from xml.sax.saxutils import escape

from scripts.kb import (
    KB,
    REPO_ROOT,
    Entity,
    Event,
    base_url,
    load_entities,
    load_events,
    load_site_config,
    load_taxonomy,
    rfc3339,
    theme_labels,
)

BUILD = REPO_ROOT / "build"
OUT = BUILD / "okf"
FEED = BUILD / "feed.xml"
FEED_SIZE = 50
TIMELINE_MARKER = "<!-- timeline -->"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _timeline_lines(entity: Entity, events: list[Event], depth: int) -> str:
    up = "../" * depth
    rows = [e for e in events if entity.ref in e.entities]
    if not rows:
        return "_No events recorded yet._"
    return "\n".join(f"- **{e.date}** — [{e.title}]({up}{e.rel}) · {e.kind}" for e in rows)


def build_entities(entities: list[Entity], events: list[Event]) -> None:
    for ent in entities:
        depth = len(Path(ent.rel).parts) - 1  # entities/<kind>/<slug>.md -> 2
        timeline = f"## Timeline\n\n{_timeline_lines(ent, events, depth)}"
        raw = ent.path.read_text(encoding="utf-8")
        text = (
            raw.replace(TIMELINE_MARKER, timeline)
            if TIMELINE_MARKER in raw
            else f"{raw.rstrip()}\n\n{timeline}\n"
        )
        _write(OUT / ent.rel, text)


def copy_events(events: list[Event]) -> None:
    for e in events:
        dest = OUT / e.rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(e.path, dest)


def _index(title: str, items: list[tuple[str, str]]) -> str:
    lines = [f"# {title}", ""]
    lines += [f"* [{label}]({href})" for href, label in items]
    return "\n".join(lines)


def build_indexes(events: list[Event], entities: list[Entity], labels: dict[str, str]) -> None:
    years = sorted({e.year for e in events}, reverse=True)
    kinds = sorted({en.kind for en in entities})

    _write(
        OUT / "index.md",
        _index(
            "PlanetAI",
            [
                ("log.md", "Latest developments (log)"),
                ("themes/index.md", "By theme"),
                ("events/index.md", "All events by year"),
                ("entities/index.md", "Projects, organisations & topics"),
            ],
        ),
    )

    _write(
        OUT / "events" / "index.md", _index("Events by year", [(f"{y}/index.md", y) for y in years])
    )
    for y in years:
        rows = [e for e in events if e.year == y]
        _write(
            OUT / "events" / y / "index.md",
            _index(y, [(Path(e.rel).name, f"{e.date} — {e.title}") for e in rows]),
        )

    _write(
        OUT / "entities" / "index.md",
        _index("Entities", [(f"{k}/index.md", k.capitalize()) for k in kinds]),
    )
    for k in kinds:
        ents = sorted((en for en in entities if en.kind == k), key=lambda en: en.title.lower())
        _write(
            OUT / "entities" / k / "index.md",
            _index(k.capitalize(), [(f"{en.slug}.md", en.title) for en in ents]),
        )

    used = [tid for tid in labels if any(tid in e.themes for e in events)]
    _write(
        OUT / "themes" / "index.md",
        _index("Themes", [(f"{tid}.md", labels[tid]) for tid in used]),
    )
    for tid in used:
        rows = [e for e in events if tid in e.themes]
        body = "\n".join(f"- **{e.date}** — [{e.title}](../{e.rel}) · {e.kind}" for e in rows)
        _write(
            OUT / "themes" / f"{tid}.md",
            f"---\ntype: Topic\ntitle: {labels[tid]}\n---\n\n# {labels[tid]}\n\n{body}\n",
        )


def build_log(events: list[Event]) -> None:
    lines = [
        "---",
        "type: Log",
        "title: PlanetAI — development log",
        "---",
        "",
        "# Development log",
        "",
    ]
    current = ""
    for e in events:
        if e.date != current:
            lines += ["", f"## {e.date}", ""]
            current = e.date
        lines.append(f"- **{e.kind}** — [{e.title}]({e.rel})")
    _write(OUT / "log.md", "\n".join(lines))


def build_feed(events: list[Event]) -> None:
    site = load_site_config().get("site", {})
    root = base_url() or "https://example.invalid/"
    recent = events[:FEED_SIZE]
    updated = rfc3339(recent[0].date) if recent else rfc3339("1970-01-01")
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"<title>{escape(str(site.get('name', 'PlanetAI')))}</title>",
        f'<link href="{escape(root)}"/>',
        f'<link rel="self" href="{escape(root)}feed.xml"/>',
        f"<id>{escape(root)}</id>",
        f"<updated>{updated}</updated>",
    ]
    for e in recent:
        url = f"{root}{e.rel[:-3]}.html"
        parts += [
            "<entry>",
            f"<title>{escape(e.title)}</title>",
            f'<link href="{escape(url)}"/>',
            f"<id>{escape(url)}</id>",
            f"<updated>{rfc3339(e.date)}</updated>",
            f'<category term="{escape(e.kind)}"/>',
            f"<summary>{escape(e.description or e.title)}</summary>",
            "</entry>",
        ]
    parts.append("</feed>")
    _write(FEED, "\n".join(parts))


def main() -> None:
    events = load_events()
    entities = load_entities()
    labels = theme_labels(load_taxonomy())

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    kiso_src = KB / ".kiso"
    if kiso_src.is_dir():
        shutil.copytree(kiso_src, OUT / ".kiso")

    copy_events(events)
    build_entities(entities, events)
    build_indexes(events, entities, labels)
    build_log(events)
    build_feed(events)

    print(
        f"projected {len(events)} events, {len(entities)} entities -> {OUT.relative_to(REPO_ROOT)}"
    )
    print(f"wrote {FEED.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
