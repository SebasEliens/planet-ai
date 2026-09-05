"""Fetch, verify, and write — one candidate at a time, within budget.

For each ranked candidate: fetch the article, ask ``agent.llm`` to judge scope and
extract a structured ``EventDraft`` (``None`` if it isn't a genuine in-scope event),
dedupe once more, resolve entity refs, and write via ``agent.store``. Stops cleanly
when the budget (new events / fetches / wall-clock) is exhausted.
"""

from __future__ import annotations

import datetime as dt
import re
import time
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import Any

import httpx

from agent import llm, store
from agent.discover import USER_AGENT
from agent.schema import Budget, Candidate, EventDraft
from scripts.kb import KB, event_kinds, theme_labels

ARTICLE_TIMEOUT_SECONDS = 20
ARTICLE_MAX_BYTES = 2_000_000

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _html_to_text(html: str) -> str:
    html = _SCRIPT_STYLE_RE.sub(" ", html)
    text = unescape(_TAG_RE.sub(" ", html))
    return _WS_RE.sub(" ", text).strip()


def fetch_article(url: str, client: httpx.Client) -> str | None:
    try:
        response = client.get(
            url, timeout=ARTICLE_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"agent.research: fetch failed {url} ({exc!r})")
        return None
    if len(response.content) > ARTICLE_MAX_BYTES:
        print(f"agent.research: skipping {url} (too large)")
        return None
    return _html_to_text(response.text)


@dataclass(frozen=True)
class WrittenEvent:
    path: Path
    title: str
    url: str
    kind: str
    themes: tuple[str, ...]
    new_entity_refs: tuple[str, ...]


@dataclass
class RunResult:
    written: list[WrittenEvent] = field(default_factory=list)
    candidates_considered: int = 0
    fetches_used: int = 0


def _write_draft(draft: EventDraft, model: str, kb_root: Path) -> WrittenEvent | None:
    known_titles = store.known_entity_titles(kb_root)
    known_refs = store.known_entity_refs(kb_root)
    entity_refs: list[str] = []
    new_refs: list[str] = []
    for mention in draft.entities:
        ref = store.resolve_entity_ref(mention, known_titles, known_refs)
        entity_refs.append(ref)
        if ref not in known_refs:
            store.write_entity_stub(mention, ref, draft.themes, kb_root)
            known_refs.add(ref)
            known_titles[mention.title.strip().lower()] = ref
            new_refs.append(ref)

    try:
        path = store.write_event(draft, model, entity_refs, kb_root)
    except FileExistsError as exc:
        print(f"agent.research: {exc}")
        return None

    source_url = draft.sources[0].resource if draft.sources else ""
    return WrittenEvent(
        path=path,
        title=draft.title,
        url=source_url,
        kind=draft.kind,
        themes=tuple(draft.themes),
        new_entity_refs=tuple(new_refs),
    )


def research(
    candidates: list[Candidate],
    taxonomy: dict[str, Any],
    *,
    budget: Budget,
    model: str,
    api_key: str | None,
    kb_root: Path = KB,
    client: httpx.Client | None = None,
    today: dt.date | None = None,
) -> RunResult:
    today = today or dt.datetime.now(dt.UTC).date()
    labels = theme_labels(taxonomy)
    themes_by_id = {t["id"]: t for t in taxonomy.get("themes", [])}
    kinds = sorted(event_kinds(taxonomy))

    result = RunResult()
    deadline = time.monotonic() + budget.timeout_min * 60
    own_client = client is None
    client = client or httpx.Client(follow_redirects=True)
    try:
        for candidate in candidates:
            if len(result.written) >= budget.max_new_events:
                break
            if result.fetches_used >= budget.max_searches:
                break
            if time.monotonic() >= deadline:
                break

            result.candidates_considered += 1
            article_text = fetch_article(candidate.url, client)
            result.fetches_used += 1
            if not article_text:
                continue
            if candidate.url.rstrip("/") in store.known_source_urls(kb_root):
                continue  # written earlier this run, or since discovery ran

            theme = themes_by_id.get(candidate.theme, {})
            existing_entities = [
                {"ref": ref, "title": title}
                for title, ref in store.known_entity_titles(kb_root).items()
            ]
            draft = llm.extract_event(
                candidate,
                article_text,
                theme_id=candidate.theme,
                theme_label=labels.get(candidate.theme, candidate.theme),
                all_theme_ids=list(themes_by_id),
                include_terms=list(theme.get("include", [])),
                exclude_terms=list(theme.get("exclude", [])),
                event_kinds=kinds,
                existing_entities=existing_entities,
                today=today.isoformat(),
                model=model,
                api_key=api_key,
            )
            if draft is None:
                continue

            written = _write_draft(draft, model, kb_root)
            if written is not None:
                result.written.append(written)
    finally:
        if own_client:
            client.close()
    return result
