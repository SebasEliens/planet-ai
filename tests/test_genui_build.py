"""`genui.build` — layout rendering. No live network calls in this file."""

from genui import build
from genui import copy as copy_mod
from genui.select import LayoutMode, Selection
from scripts import project
from scripts.frontpage import EventBrief, FrontpageStats, load

HEADLINE_STATS = FrontpageStats(
    generated_at="2026-09-04T00:00:00Z",
    window_days=30,
    total_events=3,
    total_entities=2,
    recent_events=(
        EventBrief(
            rel="events/2026/2026-09-01-a.md",
            date="2026-09-01",
            kind="news",
            title="A thing happened",
            description="It happened.",
            themes=("climate-justice",),
            entities=(),
            score=5,
        ),
    ),
    theme_activity=(),
    new_entities=(),
    job_openings=None,
)
QUIET_STATS = FrontpageStats(
    generated_at="2026-09-04T00:00:00Z",
    window_days=30,
    total_events=1,
    total_entities=1,
    recent_events=(),
    theme_activity=(),
    new_entities=(),
    job_openings=None,
)
HEADLINE_COPY = copy_mod.Copy(kicker="K", headline="A headline", dek="A dek.", trends_note="")


def test_href_converts_md_to_html() -> None:
    assert build._href("events/2026/foo.md") == "events/2026/foo.html"
    assert build._href("feed.xml") == "feed.xml"


def test_truncate_adds_ellipsis_only_when_needed() -> None:
    assert build._truncate("short", 10) == "short"
    assert build._truncate("a very long string indeed", 10) == "a very lo…"


def test_render_headline_mode() -> None:
    selection = Selection(LayoutMode.HEADLINE, "climate-justice")
    html = build.render(HEADLINE_STATS, selection, HEADLINE_COPY)
    assert "<title>PlanetAI — A headline</title>" in html
    assert 'data-accent="climate-justice"' in html
    assert "events/2026/2026-09-01-a.html" in html
    assert "A dek." in html


def test_render_quiet_mode() -> None:
    cp = copy_mod.fallback_copy(QUIET_STATS, Selection(LayoutMode.QUIET, "neutral"))
    html = build.render(QUIET_STATS, Selection(LayoutMode.QUIET, "neutral"), cp)
    assert 'data-accent="neutral"' in html
    assert "Browse the full log" in html


def test_render_escapes_untrusted_looking_copy() -> None:
    cp = copy_mod.Copy(kicker="K", headline="<script>1</script>", dek="D", trends_note="")
    html = build.render(HEADLINE_STATS, Selection(LayoutMode.HEADLINE, "climate-justice"), cp)
    assert "<script>1</script>" not in html
    assert "&lt;script&gt;" in html


def test_main_runs_end_to_end(monkeypatch, tmp_path) -> None:
    """project -> build/frontpage.json -> genui.build.main(), copy call stubbed out
    so this never hits the network regardless of which layout mode gets chosen."""
    project.main()
    load()  # sanity: build/frontpage.json is readable
    monkeypatch.setattr(
        copy_mod, "generate_copy", lambda *a, **kw: copy_mod.Copy(kicker="K", headline="H", dek="D")
    )

    out = tmp_path / "index.html"
    monkeypatch.setattr(build, "OUT", out)
    build.main()

    assert out.is_file()
    html = out.read_text(encoding="utf-8")
    assert "<html" in html and "PlanetAI" in html
