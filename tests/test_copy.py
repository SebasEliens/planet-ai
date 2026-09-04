"""`genui.copy` — the LLM copy pass, with fallback so it never breaks the build.

No live network calls: the OpenAI client is stubbed via monkeypatch throughout.
"""

import json
from types import SimpleNamespace

from genui import copy as copy_mod
from genui.select import LayoutMode, Selection
from scripts.frontpage import EventBrief, FrontpageStats

STATS = FrontpageStats(
    generated_at="2026-09-04T00:00:00Z",
    window_days=30,
    total_events=3,
    total_entities=2,
    recent_events=(
        EventBrief(
            rel="events/2026/a.md",
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


def _stub_response(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _install(monkeypatch, content: str | None) -> None:
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: _stub_response(content))
        )
    )
    monkeypatch.setattr(copy_mod, "OpenAI", lambda **kwargs: client)


def test_no_api_key_uses_fallback_without_network(monkeypatch) -> None:
    def boom(**kwargs):  # pragma: no cover - must never be called
        raise AssertionError("OpenAI() should not be constructed without an api key")

    monkeypatch.setattr(copy_mod, "OpenAI", boom)
    selection = Selection(LayoutMode.HEADLINE, "climate-justice")
    result = copy_mod.generate_copy(STATS, selection, api_key="")
    assert result == copy_mod.fallback_copy(STATS, selection)


def test_valid_response_is_used(monkeypatch) -> None:
    valid = json.dumps(
        {
            "kicker": "K",
            "headline": "H",
            "dek": "D",
            "trends_note": "T",
            "theme_blurbs": {"climate-justice": "B"},
        }
    )
    _install(monkeypatch, valid)
    selection = Selection(LayoutMode.HEADLINE, "climate-justice")
    result = copy_mod.generate_copy(STATS, selection, api_key="fake")
    assert result.headline == "H"
    assert result.theme_blurbs == {"climate-justice": "B"}


def test_malformed_json_falls_back(monkeypatch) -> None:
    _install(monkeypatch, "not json")
    selection = Selection(LayoutMode.HEADLINE, "climate-justice")
    result = copy_mod.generate_copy(STATS, selection, api_key="fake")
    assert result == copy_mod.fallback_copy(STATS, selection)


def test_missing_required_field_falls_back(monkeypatch) -> None:
    _install(monkeypatch, json.dumps({"headline": "H", "dek": "D"}))  # no "kicker"
    selection = Selection(LayoutMode.HEADLINE, "climate-justice")
    result = copy_mod.generate_copy(STATS, selection, api_key="fake")
    assert result == copy_mod.fallback_copy(STATS, selection)


def test_empty_content_falls_back(monkeypatch) -> None:
    _install(monkeypatch, None)
    selection = Selection(LayoutMode.HEADLINE, "climate-justice")
    result = copy_mod.generate_copy(STATS, selection, api_key="fake")
    assert result == copy_mod.fallback_copy(STATS, selection)


def test_quiet_fallback_mentions_window() -> None:
    selection = Selection(LayoutMode.QUIET, "neutral")
    result = copy_mod.fallback_copy(QUIET_STATS, selection)
    assert "30" in result.dek
