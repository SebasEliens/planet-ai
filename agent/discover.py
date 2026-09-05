"""Deterministic candidate discovery from ``taxonomy.yaml`` seed feeds. No LLM.

Polls each theme's RSS/Atom feeds, hard-filters on taxonomy exclude-terms and the
search window, dedupes against kb/ and across feeds, and scores what's left so
``agent.research`` can work the ranked list within budget. Writes
``agent/candidates.json`` for transparency (committed with the PR) — see
docs/DESIGN.md §2b.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import feedparser
import httpx

from agent.schema import Candidate
from agent.store import known_source_urls
from scripts.kb import KB, REPO_ROOT

CANDIDATES_JSON = REPO_ROOT / "agent" / "candidates.json"
FEED_TIMEOUT_SECONDS = 15
USER_AGENT = "PlanetAI-research-agent/0.1 (+https://github.com/SebasEliens/planet-ai)"
SUMMARY_MAX_CHARS = 500


def _entry_published(entry: dict[str, Any]) -> dt.date | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return dt.date(*value[:3])
    return None


def _entry_text(entry: dict[str, Any]) -> str:
    summary = entry.get("summary", entry.get("description", ""))
    return f"{entry.get('title', '')} {summary}"


def score_candidate(
    text: str,
    include_terms: list[str],
    exclude_terms: list[str],
    published: dt.date | None,
    today: dt.date,
    window_days: int,
) -> float | None:
    """None means "drop this candidate": it matched an exclude term, or it's outside
    the search window. Otherwise a higher score means "work this one first"."""
    lower = text.lower()
    if any(term.lower() in lower for term in exclude_terms):
        return None
    if published is not None:
        days_old = (today - published).days
        if days_old > window_days or days_old < -1:  # allow a day of feed clock skew
            return None
        recency = max(0.0, (window_days - days_old) / window_days)
    else:
        recency = 0.5  # unknown publish date: neither favoured nor penalised
    keyword_hits = sum(1 for term in include_terms if term.lower() in lower)
    return round(recency + keyword_hits * 0.5, 3)


def _fetch_feed(url: str, client: httpx.Client) -> feedparser.FeedParserDict | None:
    try:
        response = client.get(url, timeout=FEED_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"agent.discover: skipping feed {url} ({exc!r})")
        return None
    parsed: feedparser.FeedParserDict = feedparser.parse(response.content)
    return parsed


def discover(
    taxonomy: dict[str, Any],
    *,
    kb_root: Path = KB,
    today: dt.date | None = None,
    client: httpx.Client | None = None,
) -> list[Candidate]:
    today = today or dt.datetime.now(dt.UTC).date()
    window_days = int(taxonomy.get("search_window_days", 90))
    known_urls = known_source_urls(kb_root)
    themes_by_id = {t["id"]: t for t in taxonomy.get("themes", [])}
    seeds: dict[str, list[str]] = taxonomy.get("seeds", {})

    seen_this_run: dict[str, Candidate] = {}
    own_client = client is None
    client = client or httpx.Client(follow_redirects=True)
    try:
        for theme_id, feed_urls in seeds.items():
            theme = themes_by_id.get(theme_id, {})
            include_terms = list(theme.get("include", []))
            exclude_terms = list(theme.get("exclude", []))
            for feed_url in feed_urls:
                parsed = _fetch_feed(feed_url, client)
                if parsed is None:
                    continue
                for entry in parsed.get("entries", []):
                    url = str(entry.get("link", "")).strip().rstrip("/")
                    if not url or url in known_urls:
                        continue
                    published = _entry_published(entry)
                    score = score_candidate(
                        _entry_text(entry),
                        include_terms,
                        exclude_terms,
                        published,
                        today,
                        window_days,
                    )
                    if score is None:
                        continue
                    existing = seen_this_run.get(url)
                    if existing is not None and existing.score >= score:
                        continue
                    seen_this_run[url] = Candidate(
                        url=url,
                        title=str(entry.get("title", "")).strip() or url,
                        summary=str(entry.get("summary", entry.get("description", "")))[
                            :SUMMARY_MAX_CHARS
                        ],
                        published=published.isoformat() if published else "",
                        theme=theme_id,
                        score=score,
                    )
    finally:
        if own_client:
            client.close()

    return sorted(seen_this_run.values(), key=lambda c: c.score, reverse=True)


def write_candidates(candidates: list[Candidate], path: Path = CANDIDATES_JSON) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [c.model_dump() for c in candidates]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
