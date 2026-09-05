"""OpenRouter client: the one place an LLM judges scope and extracts a structured
event from a fetched article.

Returns ``None`` whenever the candidate isn't a genuine, verifiable, in-scope event —
the caller simply skips it and moves to the next candidate. The model never writes a
file directly; it only returns JSON that ``agent.store`` may turn into one. Model is a
config string via OpenRouter, not a vendor lock-in — see docs/DESIGN.md §2.
"""

from __future__ import annotations

import json

import openai
from openai import OpenAI
from pydantic import ValidationError

from agent.schema import Candidate, EventDraft

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
REQUEST_TIMEOUT_SECONDS = 60
MAX_OUTPUT_TOKENS = 2500
MAX_ARTICLE_CHARS = 8000


def _prompt(
    candidate: Candidate,
    article_text: str,
    *,
    theme_id: str,
    theme_label: str,
    all_theme_ids: list[str],
    include_terms: list[str],
    exclude_terms: list[str],
    event_kinds: list[str],
    existing_entities: list[dict[str, str]],
    today: str,
) -> str:
    context = {
        "today": today,
        "candidate_url": candidate.url,
        "candidate_title": candidate.title,
        "feed_summary": candidate.summary,
        "theme_id": theme_id,
        "theme_label": theme_label,
        "all_theme_ids": all_theme_ids,
        "in_scope_examples": include_terms,
        "out_of_scope_examples": exclude_terms,
        "allowed_kinds": event_kinds,
        "existing_entities": existing_entities[:300],
        "article_text": article_text[:MAX_ARTICLE_CHARS],
    }
    return (
        "You are the research step of PlanetAI, an append-only, sourced log of AI "
        "developments in climate justice, human rights, and environmental monitoring. "
        "You are given one candidate article and its fetched text. Decide whether it "
        "describes a genuine, dated, in-scope factual event (a paper, project launch or "
        "update, report, funding, policy or legal move, dataset/benchmark, or notable "
        "news) for the theme below — not opinion, not speculation, not a product page "
        "with no news content.\n\n"
        "Rules:\n"
        "- Use ONLY facts present in article_text. Never invent a detail, date, or number.\n"
        "- Write description/body in your OWN WORDS — do not closely track the source's "
        "sentence structure. Never copy the headline or an abstract verbatim.\n"
        "- At most one short quote (<=25 words) anywhere, only if the exact wording matters, "
        "and mark it as a quote.\n"
        "- `date` is when the event happened (as reported), never `today`. Use YYYY-MM-DD, "
        "or YYYY-MM only if the day is genuinely unclear from the article.\n"
        "- `kind` must be one of allowed_kinds.\n"
        '- `themes` MUST be taxonomy theme IDs (the short slug form, e.g. "theme_id" '
        "above) chosen from all_theme_ids — never the human-readable label. Normally just "
        '["theme_id"]; add another id from all_theme_ids only if the article clearly also '
        "concerns that theme.\n"
        "- For `entities` (actors/projects/tech mentioned): if an entity's name matches one "
        "in existing_entities (by ref or title), reuse that exact ref and leave description "
        'empty. Otherwise invent a ref as "<kind-dir>/<slug>" '
        "(kind-dir one of projects/orgs/tech/topics/places) and give a one-sentence "
        "factual description.\n"
        "- `sources` must include an entry for the candidate_url with a real title; you may "
        "add more if the article cites other primary sources with their own URLs.\n"
        "- If this is not a genuine in-scope dated event, respond with exactly "
        '{"in_scope": false} and nothing else.\n\n'
        "Return ONLY a JSON object. If in scope:\n"
        '{"in_scope": true, "kind": "...", "title": "...", "description": "...", '
        '"date": "YYYY-MM-DD", "themes": ["theme_id"], '
        '"entities": [{"ref": "...", "title": "...", "type": "Project|Organization|'
        'Technology|Topic|Place", "description": ""}], "tags": ["..."], '
        '"sources": [{"id": "...", "resource": "...", "title": "...", "author": "...", '
        '"last_modified": "YYYY-MM-DD"}], "body": "2-5 factual sentences with [^id] '
        'citations"}\n\n'
        f"DATA:\n{json.dumps(context, ensure_ascii=False)}"
    )


def extract_event(
    candidate: Candidate,
    article_text: str,
    *,
    theme_id: str,
    theme_label: str,
    all_theme_ids: list[str],
    include_terms: list[str],
    exclude_terms: list[str],
    event_kinds: list[str],
    existing_entities: list[dict[str, str]],
    today: str,
    model: str,
    api_key: str | None,
) -> EventDraft | None:
    if not api_key:
        return None
    try:
        client = OpenAI(
            base_url=OPENROUTER_BASE_URL, api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": _prompt(
                        candidate,
                        article_text,
                        theme_id=theme_id,
                        theme_label=theme_label,
                        all_theme_ids=all_theme_ids,
                        include_terms=include_terms,
                        exclude_terms=exclude_terms,
                        event_kinds=event_kinds,
                        existing_entities=existing_entities,
                        today=today,
                    ),
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            return None
        data = json.loads(content)
        if not data.get("in_scope"):
            return None

        # Never trust the model to reproduce the URL byte-for-byte: we already know it
        # exactly, so the candidate's own URL always wins for the primary source.
        sources = data.get("sources") or []
        if sources:
            sources[0]["resource"] = candidate.url
        else:
            sources = [{"id": "primary", "resource": candidate.url, "title": candidate.title}]
        data["sources"] = sources

        # Defence in depth against the model writing a theme label instead of an id.
        valid_ids = set(all_theme_ids)
        themes = [t for t in data.get("themes", []) if t in valid_ids]
        data["themes"] = themes or [theme_id]

        return EventDraft.model_validate(data)
    except (ValidationError, json.JSONDecodeError, ValueError, openai.OpenAIError) as exc:
        print(f"agent: extraction failed for {candidate.url} ({exc!r})")
        return None
