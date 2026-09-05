"""`agent.run` — budget resolution and the PR-title convention (AGENTS.md §2a)."""

from pathlib import Path

from agent import run
from agent.research import RunResult, WrittenEvent

TAXONOMY = {
    "budgets": {
        "light": {"max_new_events": 4, "max_searches": 15, "max_usd": 1.5, "timeout_min": 12},
        "standard": {"max_new_events": 8, "max_searches": 40, "max_usd": 4.0, "timeout_min": 20},
    },
    "depth_default": "standard",
}


def _written(title: str, themes: tuple[str, ...]) -> WrittenEvent:
    return WrittenEvent(
        path=Path("kb/events/2026/x.md"),
        title=title,
        url="https://x",
        kind="news",
        themes=themes,
        new_entity_refs=(),
    )


def test_resolve_budget_uses_requested_depth() -> None:
    depth, budget = run.resolve_budget(TAXONOMY, "light")
    assert depth == "light"
    assert budget.max_new_events == 4


def test_resolve_budget_falls_back_to_default_for_unknown_depth() -> None:
    depth, budget = run.resolve_budget(TAXONOMY, "")  # e.g. an unset workflow_dispatch input
    assert depth == "standard"
    assert budget.max_new_events == 8


def test_pr_title_no_events() -> None:
    title = run.pr_title(RunResult())
    assert title.startswith("events: no new events (")


def test_pr_title_single_theme() -> None:
    result = RunResult(
        written=[_written("A", ("climate-justice",)), _written("B", ("climate-justice",))]
    )
    title = run.pr_title(result)
    assert title.startswith("events: climate-justice — 2 new (")


def test_pr_title_multiple_themes() -> None:
    result = RunResult(
        written=[_written("A", ("climate-justice",)), _written("B", ("ai-human-rights",))]
    )
    title = run.pr_title(result)
    assert title.startswith("events: 2 themes — 2 new (")
