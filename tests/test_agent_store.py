"""`agent.store` — append-only writers, dedupe helpers, entity-ref resolution."""

from pathlib import Path

import pytest

from agent import store
from agent.schema import EntityMention, EventDraft, SourceRef
from scripts.kb import load_entities, load_events


def _kb(tmp_path: Path) -> Path:
    kb = tmp_path / "kb"
    (kb / "events").mkdir(parents=True)
    (kb / "entities").mkdir(parents=True)
    return kb


def _draft(**overrides: object) -> EventDraft:
    defaults: dict[str, object] = {
        "kind": "project-launch",
        "title": "FooProject launches an open flood-risk model",
        "description": "One sentence factual summary.",
        "date": "2026-08-20",
        "themes": ["climate-justice"],
        "entities": [EntityMention(ref="orgs/fooorg", title="FooOrg", type="Organization")],
        "tags": ["flood"],
        "sources": [SourceRef(id="a", resource="https://example.com/a", title="Source A")],
        "body": "FooOrg launched a model.[^a]",
    }
    defaults.update(overrides)
    return EventDraft(**defaults)  # type: ignore[arg-type]


def test_slugify() -> None:
    assert (
        store.slugify("FooProject launches an Open Model!") == "fooproject-launches-an-open-model"
    )
    assert store.slugify("  ---  ") == "untitled"


def test_write_event_roundtrips_through_kb_loader(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    (kb / "entities" / "orgs").mkdir(parents=True)
    store.write_entity_stub(
        EntityMention(ref="orgs/fooorg", title="FooOrg", type="Organization"),
        "orgs/fooorg",
        ["climate-justice"],
        kb,
    )
    path = store.write_event(_draft(), "anthropic/claude-sonnet-5", ["orgs/fooorg"], kb)

    expected = "2026-08-20-fooproject-launches-an-open-flood-risk-model.md"
    assert path == kb / "events" / "2026" / expected
    events = load_events(kb)
    assert len(events) == 1
    e = events[0]
    assert e.kind == "project-launch"
    assert e.date == "2026-08-20"
    assert e.entities == ("orgs/fooorg",)
    assert e.sources[0]["resource"] == "https://example.com/a"

    entities = load_entities(kb)
    assert [en.ref for en in entities] == ["orgs/fooorg"]


def test_write_event_twice_gets_a_disambiguated_path_not_an_overwrite(tmp_path: Path) -> None:
    """Same date+title colliding (two distinct events) gets a `-2` suffix rather than
    silently overwriting the first one."""
    kb = _kb(tmp_path)
    first = store.write_event(_draft(), "m", [], kb)
    second = store.write_event(_draft(), "m", [], kb)
    assert first != second
    assert second.name.endswith("-2.md")
    assert first.is_file() and second.is_file()


def test_write_entity_stub_refuses_to_overwrite_an_existing_entity(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    mention = EntityMention(ref="orgs/foo", title="Foo", type="Organization")
    store.write_entity_stub(mention, "orgs/foo", [], kb)
    with pytest.raises(FileExistsError):
        store.write_entity_stub(mention, "orgs/foo", [], kb)


def test_known_source_urls_strips_trailing_slash(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    store.write_event(
        _draft(sources=[SourceRef(id="a", resource="https://example.com/a/", title="A")]),
        "m",
        [],
        kb,
    )
    assert "https://example.com/a" in store.known_source_urls(kb)


def test_resolve_entity_ref_reuses_existing_ref() -> None:
    mention = EntityMention(ref="orgs/foo-org", title="FooOrg", type="Organization")
    assert store.resolve_entity_ref(mention, {}, {"orgs/foo-org"}) == "orgs/foo-org"


def test_resolve_entity_ref_reuses_by_title_even_if_model_guessed_a_different_slug() -> None:
    mention = EntityMention(
        ref="orgs/national-aeronautics-and-space-administration", title="NASA", type="Organization"
    )
    known_titles = {"nasa": "orgs/nasa"}
    assert store.resolve_entity_ref(mention, known_titles, {"orgs/nasa"}) == "orgs/nasa"


def test_resolve_entity_ref_creates_fresh_ref_for_new_entity() -> None:
    mention = EntityMention(ref="ignored", title="Brand New Org", type="Organization")
    assert store.resolve_entity_ref(mention, {}, set()) == "orgs/brand-new-org"


def test_write_entity_stub_uses_model_description_when_present(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    mention = EntityMention(
        ref="orgs/foo", title="Foo", type="Organization", description="Foo is a real org."
    )
    path = store.write_entity_stub(mention, "orgs/foo", ["climate-justice"], kb)
    text = path.read_text(encoding="utf-8")
    assert "Foo is a real org." in text
    assert "<!-- timeline -->" in text
    assert "description: Foo is a real org." in text
    assert "climate-justice" in text
