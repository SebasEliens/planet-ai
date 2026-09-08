"""`scripts.project` turns kb/ into a Kiso-ready bundle + Atom feed."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts import project
from scripts.kb import Event, rfc3339

ATOM = "{http://www.w3.org/2005/Atom}"


def test_rfc3339() -> None:
    assert rfc3339("2023-08-03") == "2023-08-03T00:00:00Z"
    assert rfc3339("2023-08") == "2023-08-01T00:00:00Z"


def test_iso_date_pads_fuzzy_month() -> None:
    def _ev(date: str) -> Event:
        return Event(
            path=Path("x.md"),
            rel="events/x.md",
            slug="x",
            year=date[:4],
            date=date,
            kind="news",
            title="X",
            description="d",
            themes=(),
            entities=(),
            sources=(),
            body="b",
        )

    assert _ev("2026-01").iso_date == "2026-01-01"
    assert _ev("2026-01-09").iso_date == "2026-01-09"


def test_log_headings_are_iso_dates() -> None:
    # Kiso rejects a bare YYYY-MM in a log heading (INVALID_LOG_DATE_FORMAT).
    project.main()
    log = (project.OUT / "log.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", log, re.MULTILINE)
    assert headings
    for h in headings:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", h), f"non-ISO log heading: {h!r}"


def test_project_builds_bundle() -> None:
    project.main()
    out = project.OUT

    assert (out / "index.md").is_file()
    assert (out / "log.md").is_file()
    assert (out / ".kiso" / "configuration.yaml").is_file()

    prithvi = (out / "entities" / "projects" / "prithvi.md").read_text(encoding="utf-8")
    assert "## Timeline" in prithvi
    assert "2023-08-03-prithvi-geospatial-model-open-sourced.md" in prithvi
    assert "description:" in prithvi  # original frontmatter preserved

    tree = ET.parse(project.FEED)
    entries = tree.findall(f"{ATOM}entry")
    assert entries, "feed has no entries"
    titles = [e.findtext(f"{ATOM}title") for e in entries]
    assert any(t and "Prithvi" in t for t in titles)


def test_no_timeline_marker_leaks() -> None:
    project.main()
    for md in project.OUT.rglob("*.md"):
        assert project.TIMELINE_MARKER not in md.read_text(encoding="utf-8")
