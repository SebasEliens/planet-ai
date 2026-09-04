"""Front-page build.

Loads the deterministic stats ``scripts.project`` wrote (``build/frontpage.json``),
picks a layout deterministically (``genui.select`` — no LLM), asks the model for copy
only (``genui.copy`` — falls back to plain deterministic copy on any failure, so this
step can never break the build), and renders one of a small set of Jinja2 layouts to
``site/index.html``, overwriting Kiso's generated index. See docs/DESIGN.md §4.

Run: ``uv run python -m genui.build``
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from genui import copy as copy_mod
from genui.select import Selection, choose
from scripts.frontpage import FRONTPAGE_JSON, EntityBrief, EventBrief, FrontpageStats, load
from scripts.kb import REPO_ROOT, load_taxonomy

REPO_URL = "https://github.com/SebasEliens/planet-ai"
LAYOUTS_DIR = Path(__file__).parent / "layouts"
OUT = REPO_ROOT / "site" / "index.html"

_TRUNCATE_LIMITS = {"kicker": 80, "headline": 160, "dek": 260, "trends_note": 420}


def _href(rel: str) -> str:
    return f"{rel[:-3]}.html" if rel.endswith(".md") else rel


def _event_view(e: EventBrief) -> dict[str, Any]:
    return {
        "title": e.title,
        "date": e.date,
        "kind": e.kind,
        "description": e.description,
        "href": _href(e.rel),
    }


def _entity_view(e: EntityBrief) -> dict[str, str]:
    return {"title": e.title, "href": f"entities/{e.ref}.html"}


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _copy_context(cp: copy_mod.Copy) -> dict[str, Any]:
    return {
        "kicker": _truncate(cp.kicker, _TRUNCATE_LIMITS["kicker"]) or "PlanetAI",
        "headline": _truncate(cp.headline, _TRUNCATE_LIMITS["headline"]) or "PlanetAI",
        "dek": _truncate(cp.dek, _TRUNCATE_LIMITS["dek"]),
        "trends_note": _truncate(cp.trends_note, _TRUNCATE_LIMITS["trends_note"]),
        "theme_blurbs": cp.theme_blurbs,
    }


def render(stats: FrontpageStats, selection: Selection, cp: copy_mod.Copy) -> str:
    env = Environment(
        loader=FileSystemLoader(LAYOUTS_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(f"{selection.mode.value}.html")
    events = [_event_view(e) for e in stats.recent_events]
    jobs = stats.job_openings

    context: dict[str, Any] = {
        "stats": stats,
        "copy": _copy_context(cp),
        "accent": selection.accent,
        "lead": events[0] if events else None,
        "others": events[1:6],
        "events": events,
        "new_entities": [_entity_view(e) for e in stats.new_entities],
        "job_openings": {"title": jobs.title, "href": _href(jobs.rel)} if jobs else None,
        "repo_url": REPO_URL,
    }
    return template.render(**context)


def main() -> None:
    stats = load(FRONTPAGE_JSON)
    selection = choose(stats)
    model = load_taxonomy().get("model", {}).get("genui", copy_mod.DEFAULT_MODEL)
    cp = copy_mod.generate_copy(stats, selection, model=model)
    html = render(stats, selection, cp)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(
        f"genui: mode={selection.mode.value} accent={selection.accent} "
        f"-> wrote {OUT} ({len(html):,} bytes)"
    )


if __name__ == "__main__":
    main()
