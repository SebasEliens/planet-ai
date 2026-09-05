"""`agent.llm` — scope judgment + structured extraction. No live network: the OpenAI
client is stubbed via monkeypatch throughout."""

import json
from types import SimpleNamespace

from agent import llm
from agent.schema import Candidate

CANDIDATE = Candidate(
    url="https://example.com/a",
    title="A story",
    summary="s",
    published="2026-08-20",
    theme="climate-justice",
    score=1.0,
)

VALID = {
    "in_scope": True,
    "kind": "project-launch",
    "title": "FooProject launches",
    "description": "One sentence.",
    "date": "2026-08-20",
    "themes": ["climate-justice"],
    "entities": [
        {"ref": "orgs/foo", "title": "Foo", "type": "Organization", "description": "Foo is an org."}
    ],
    "tags": ["flood"],
    "sources": [{"id": "a", "resource": "https://example.com/a", "title": "A story"}],
    "body": "FooProject launched something.[^a]",
}


def _response(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _install(monkeypatch, content: str | None) -> None:
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: _response(content))
        )
    )
    monkeypatch.setattr(llm, "OpenAI", lambda **kwargs: client)


def _extract(**overrides):
    kwargs = dict(
        candidate=CANDIDATE,
        article_text="article text",
        theme_id="climate-justice",
        theme_label="Climate Justice",
        all_theme_ids=["climate-justice", "ai-human-rights"],
        include_terms=["climate litigation"],
        exclude_terms=[],
        event_kinds=["project-launch", "news"],
        existing_entities=[],
        today="2026-09-04",
        model="anthropic/claude-sonnet-5",
        api_key="fake",
    )
    kwargs.update(overrides)
    return llm.extract_event(**kwargs)


def test_no_api_key_returns_none_without_network(monkeypatch) -> None:
    def boom(**kwargs):  # pragma: no cover
        raise AssertionError("OpenAI() should not be constructed without an api key")

    monkeypatch.setattr(llm, "OpenAI", boom)
    assert _extract(api_key=None) is None


def test_out_of_scope_returns_none(monkeypatch) -> None:
    _install(monkeypatch, json.dumps({"in_scope": False}))
    assert _extract() is None


def test_in_scope_returns_validated_draft(monkeypatch) -> None:
    _install(monkeypatch, json.dumps(VALID))
    draft = _extract()
    assert draft is not None
    assert draft.title == "FooProject launches"
    assert draft.entities[0].ref == "orgs/foo"
    assert draft.sources[0].resource == "https://example.com/a"


def test_malformed_json_returns_none(monkeypatch) -> None:
    _install(monkeypatch, "not json")
    assert _extract() is None


def test_missing_required_field_returns_none(monkeypatch) -> None:
    bad = dict(VALID)
    del bad["title"]  # required, no fallback
    _install(monkeypatch, json.dumps(bad))
    assert _extract() is None


def test_missing_sources_is_healed_from_the_known_candidate_url(monkeypatch) -> None:
    """Unlike title/date, a missing `sources` list isn't fatal: we already know the
    real URL, so it's filled in rather than throwing away an otherwise-good draft."""
    bad = dict(VALID)
    del bad["sources"]
    _install(monkeypatch, json.dumps(bad))
    draft = _extract()
    assert draft is not None
    assert draft.sources[0].resource == CANDIDATE.url


def test_empty_content_returns_none(monkeypatch) -> None:
    _install(monkeypatch, None)
    assert _extract() is None


def test_theme_label_from_the_model_falls_back_to_the_discovery_theme_id(monkeypatch) -> None:
    """The model must emit theme ids, not labels — but if it slips, don't throw away an
    otherwise-good extraction over one bad string; fall back to the theme it was found under."""
    bad = dict(VALID, themes=["Climate Justice"])  # a label, not an id
    _install(monkeypatch, json.dumps(bad))
    draft = _extract()
    assert draft is not None
    assert draft.themes == ["climate-justice"]


def test_source_url_is_always_the_real_candidate_url(monkeypatch) -> None:
    """Never trust the model to reproduce the URL byte-for-byte."""
    bad = dict(VALID)
    bad["sources"] = [{"id": "a", "resource": "example.com", "title": "A story"}]
    _install(monkeypatch, json.dumps(bad))
    draft = _extract()
    assert draft is not None
    assert draft.sources[0].resource == CANDIDATE.url
