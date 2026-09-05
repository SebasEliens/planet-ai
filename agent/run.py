"""Entry point: discover -> research (within budget) -> a PR-ready summary.

Run: ``uv run python -m agent.run``. Depth (light/standard/deep) comes from
``$PLANETAI_DEPTH``, falling back to ``taxonomy.yaml``'s ``depth_default``. Needs
``OPENROUTER_API_KEY``; without it, discovery still runs (and still writes
``agent/candidates.json``) but no events are extracted or written.
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

from agent import discover, research
from agent.schema import Budget
from scripts.kb import REPO_ROOT, load_taxonomy

SUMMARY_PATH = REPO_ROOT / "agent" / "run-summary.md"
PR_TITLE_PATH = REPO_ROOT / "agent" / "pr-title.txt"
DEFAULT_MODEL = "anthropic/claude-sonnet-5"


def resolve_budget(taxonomy: dict[str, object], depth: str) -> tuple[str, Budget]:
    budgets = taxonomy.get("budgets", {})
    assert isinstance(budgets, dict)
    if depth not in budgets:
        depth = str(taxonomy.get("depth_default", "standard"))
    return depth, Budget.model_validate(budgets[depth])


def write_summary(result: research.RunResult, depth: str, path: Path = SUMMARY_PATH) -> None:
    lines = [f"# Research run — {dt.datetime.now(dt.UTC):%Y-%m-%d} ({depth})", ""]
    if not result.written:
        lines.append("No new in-scope events found this run.")
    else:
        lines.append(f"{len(result.written)} new event(s):")
        lines.append("")
        for w in result.written:
            rel = w.path.relative_to(REPO_ROOT)
            lines.append(f"- **{w.title}** ({w.kind}) — `{rel}` — <{w.url}>")
            for ref in w.new_entity_refs:
                lines.append(f"  - new entity stub: `{ref}`")
    lines.append("")
    lines.append(
        f"Candidates considered: {result.candidates_considered} · "
        f"pages fetched: {result.fetches_used}"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pr_title(result: research.RunResult) -> str:
    """Matches the PR-title convention in AGENTS.md §2a: `events: <theme> — <n> new (<date>)`."""
    date = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    if not result.written:
        return f"events: no new events ({date})"
    theme_ids = list(dict.fromkeys(t for w in result.written for t in w.themes))
    label = theme_ids[0] if len(theme_ids) == 1 else f"{len(theme_ids)} themes"
    return f"events: {label} — {len(result.written)} new ({date})"


def main() -> None:
    taxonomy = load_taxonomy()
    requested_depth = os.environ.get(
        "PLANETAI_DEPTH", str(taxonomy.get("depth_default", "standard"))
    )
    depth, budget = resolve_budget(taxonomy, requested_depth)
    model_cfg = taxonomy.get("model", {})
    model = (
        model_cfg.get("extract", DEFAULT_MODEL) if isinstance(model_cfg, dict) else DEFAULT_MODEL
    )
    api_key = os.environ.get("OPENROUTER_API_KEY")

    candidates = discover.discover(taxonomy)
    discover.write_candidates(candidates)
    print(f"agent.run: {len(candidates)} candidate(s) after scoring/dedupe")

    if not api_key:
        print("agent.run: OPENROUTER_API_KEY not set — skipping extraction")
        result = research.RunResult()
    else:
        result = research.research(
            candidates, taxonomy, budget=budget, model=model, api_key=api_key
        )

    write_summary(result, depth)
    PR_TITLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PR_TITLE_PATH.write_text(pr_title(result) + "\n", encoding="utf-8")
    print(f"agent.run: wrote {len(result.written)} event(s)")


if __name__ == "__main__":
    main()
