"""`agent.research` — orchestration: fetch, extract, dedupe, write, respect budget.

No live network: `fetch_article` and `agent.llm.extract_event` are stubbed.
"""

from pathlib import Path

from agent import llm, research
from agent.schema import Budget, Candidate, EntityMention, EventDraft, SourceRef

TAXONOMY = {
    "themes": [{"id": "climate-justice", "label": "Climate Justice", "include": [], "exclude": []}],
}


def _kb(tmp_path: Path) -> Path:
    kb = tmp_path / "kb"
    (kb / "events").mkdir(parents=True)
    (kb / "entities").mkdir(parents=True)
    return kb


def _candidate(n: int) -> Candidate:
    return Candidate(
        url=f"https://example.com/{n}", title=f"Story {n}", theme="climate-justice", score=1.0
    )


def _draft(n: int, entity_ref: str = "orgs/foo", entity_title: str = "Foo") -> EventDraft:
    return EventDraft(
        kind="news",
        title=f"Story {n} happened",
        description="d",
        date="2026-08-20",
        themes=["climate-justice"],
        entities=[
            EntityMention(
                ref=entity_ref, title=entity_title, type="Organization", description="Foo org."
            )
        ],
        sources=[SourceRef(id="a", resource=f"https://example.com/{n}", title=f"Story {n}")],
        body="b",
    )


def _budget(**overrides: object) -> Budget:
    defaults = {"max_new_events": 10, "max_searches": 10, "max_usd": 100.0, "timeout_min": 10}
    defaults.update(overrides)
    return Budget(**defaults)  # type: ignore[arg-type]


def test_writes_events_and_skips_out_of_scope(tmp_path, monkeypatch) -> None:
    kb = _kb(tmp_path)
    candidates = [_candidate(1), _candidate(2)]
    drafts = {1: _draft(1), 2: None}

    monkeypatch.setattr(research, "fetch_article", lambda url, client: "article text")
    monkeypatch.setattr(
        llm, "extract_event", lambda candidate, *a, **kw: drafts[int(candidate.url[-1])]
    )

    result = research.research(
        candidates, TAXONOMY, budget=_budget(), model="m", api_key="k", kb_root=kb
    )

    assert [w.title for w in result.written] == ["Story 1 happened"]
    assert result.candidates_considered == 2
    assert result.fetches_used == 2


def test_stops_at_max_new_events(tmp_path, monkeypatch) -> None:
    kb = _kb(tmp_path)
    candidates = [_candidate(1), _candidate(2), _candidate(3)]

    monkeypatch.setattr(research, "fetch_article", lambda url, client: "article text")
    monkeypatch.setattr(
        llm, "extract_event", lambda candidate, *a, **kw: _draft(int(candidate.url[-1]))
    )

    result = research.research(
        candidates, TAXONOMY, budget=_budget(max_new_events=1), model="m", api_key="k", kb_root=kb
    )

    assert len(result.written) == 1
    assert result.candidates_considered == 1  # loop stopped before touching candidate 2


def test_skips_candidate_when_fetch_fails(tmp_path, monkeypatch) -> None:
    kb = _kb(tmp_path)
    called = []
    monkeypatch.setattr(research, "fetch_article", lambda url, client: None)
    monkeypatch.setattr(llm, "extract_event", lambda *a, **kw: called.append(1) or None)

    result = research.research(
        [_candidate(1)], TAXONOMY, budget=_budget(), model="m", api_key="k", kb_root=kb
    )

    assert result.written == []
    assert called == []  # never even asked the model — no article text to give it


def test_reuses_entity_stub_created_earlier_in_the_same_run(tmp_path, monkeypatch) -> None:
    kb = _kb(tmp_path)
    candidates = [_candidate(1), _candidate(2)]

    monkeypatch.setattr(research, "fetch_article", lambda url, client: "article text")
    monkeypatch.setattr(
        llm,
        "extract_event",
        lambda candidate, *a, **kw: _draft(int(candidate.url[-1]), entity_ref="orgs/wrong-guess"),
    )

    result = research.research(
        candidates, TAXONOMY, budget=_budget(), model="m", api_key="k", kb_root=kb
    )

    assert len(result.written) == 2
    # both events reused the same entity ref (matched by title "Foo"), and only one
    # stub was created for it
    assert result.written[0].new_entity_refs == ("orgs/foo",)
    assert result.written[1].new_entity_refs == ()
    assert (kb / "entities" / "orgs" / "foo.md").is_file()
