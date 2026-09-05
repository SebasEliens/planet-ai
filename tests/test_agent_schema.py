"""`agent.schema` — the typed contracts between discovery, extraction, and storage."""

import pytest
from pydantic import ValidationError

from agent.schema import Budget, Candidate, EntityMention, EventDraft, SourceRef


def test_candidate_requires_theme_and_score() -> None:
    c = Candidate(url="https://x", title="t", theme="climate-justice", score=1.5)
    assert c.summary == ""
    assert c.published == ""


def test_event_draft_requires_at_least_one_theme_and_source() -> None:
    with pytest.raises(ValidationError):
        EventDraft(
            kind="news",
            title="t",
            description="d",
            date="2026-08-20",
            themes=[],  # empty: invalid
            sources=[SourceRef(id="a", resource="https://x", title="t")],
            body="b",
        )
    with pytest.raises(ValidationError):
        EventDraft(
            kind="news",
            title="t",
            description="d",
            date="2026-08-20",
            themes=["climate-justice"],
            sources=[],  # empty: invalid
            body="b",
        )


def test_event_draft_entities_default_to_empty() -> None:
    draft = EventDraft(
        kind="news",
        title="t",
        description="d",
        date="2026-08-20",
        themes=["climate-justice"],
        sources=[SourceRef(id="a", resource="https://x", title="t")],
        body="b",
    )
    assert draft.entities == []
    assert draft.tags == []


def test_entity_mention_description_optional() -> None:
    m = EntityMention(ref="orgs/x", title="X", type="Organization")
    assert m.description == ""


def test_budget_matches_taxonomy_shape() -> None:
    b = Budget(max_new_events=8, max_searches=40, max_usd=4.0, timeout_min=20)
    assert b.max_new_events == 8
