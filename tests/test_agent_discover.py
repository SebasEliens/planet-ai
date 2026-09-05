"""`agent.discover` — deterministic candidate discovery. No live network: feed fetches
go through `httpx.MockTransport`."""

import datetime as dt
from pathlib import Path

import httpx

from agent import discover
from agent.schema import EventDraft, SourceRef
from agent.store import write_event

TODAY = dt.date(2026, 9, 4)

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Test Feed</title>
<item><title>Great climate litigation win</title><link>https://example.com/1</link>
<description>A court ruled on a climate litigation case.</description>
<pubDate>Thu, 20 Aug 2026 00:00:00 GMT</pubDate></item>
<item><title>Unrelated carbon-credit market mechanics news</title><link>https://example.com/2</link>
<description>A company announced a carbon-credit market mechanics update.</description>
<pubDate>Thu, 20 Aug 2026 00:00:00 GMT</pubDate></item>
<item><title>Old news</title><link>https://example.com/3</link>
<description>Something old.</description>
<pubDate>Wed, 01 Jan 2020 00:00:00 GMT</pubDate></item>
</channel></rss>"""

TAXONOMY = {
    "search_window_days": 90,
    "themes": [
        {
            "id": "climate-justice",
            "label": "Climate Justice",
            "include": ["climate litigation"],
            "exclude": ["carbon-credit market mechanics"],
        }
    ],
    "seeds": {"climate-justice": ["https://feed.example/rss"]},
}


def _client(content: bytes = RSS, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=content)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _kb(tmp_path: Path) -> Path:
    kb = tmp_path / "kb"
    (kb / "events").mkdir(parents=True)
    (kb / "entities").mkdir(parents=True)
    return kb


def test_score_candidate_hard_filters() -> None:
    # exclude-term match: dropped regardless of anything else
    assert (
        discover.score_candidate(
            "carbon-credit market mechanics news",
            [],
            ["carbon-credit market mechanics"],
            TODAY,
            TODAY,
            90,
        )
        is None
    )
    # outside the search window: dropped
    old = TODAY - dt.timedelta(days=200)
    assert discover.score_candidate("anything", [], [], old, TODAY, 90) is None


def test_score_candidate_rewards_recency_and_keywords() -> None:
    fresh_no_keywords = discover.score_candidate("nothing relevant", [], [], TODAY, TODAY, 90)
    fresh_with_keyword = discover.score_candidate(
        "a climate litigation story", ["climate litigation"], [], TODAY, TODAY, 90
    )
    assert fresh_no_keywords is not None
    assert fresh_with_keyword is not None
    assert fresh_with_keyword > fresh_no_keywords


def test_discover_filters_excluded_and_stale_keeps_in_scope(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    candidates = discover.discover(TAXONOMY, kb_root=kb, today=TODAY, client=_client())
    assert [c.url for c in candidates] == ["https://example.com/1"]
    assert candidates[0].theme == "climate-justice"


def test_discover_dedupes_against_known_kb_sources(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    draft = EventDraft(
        kind="news",
        title="Already recorded",
        description="d",
        date="2026-08-20",
        themes=["climate-justice"],
        entities=[],
        sources=[SourceRef(id="a", resource="https://example.com/1", title="A")],
        body="b",
    )
    write_event(draft, "m", [], kb)

    candidates = discover.discover(TAXONOMY, kb_root=kb, today=TODAY, client=_client())
    assert candidates == []


def test_discover_skips_a_dead_feed_without_crashing(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    candidates = discover.discover(TAXONOMY, kb_root=kb, today=TODAY, client=_client(status=503))
    assert candidates == []


def test_write_candidates_roundtrip(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    candidates = discover.discover(TAXONOMY, kb_root=kb, today=TODAY, client=_client())
    out = tmp_path / "candidates.json"
    discover.write_candidates(candidates, out)
    assert out.is_file()
    assert "example.com/1" in out.read_text(encoding="utf-8")
