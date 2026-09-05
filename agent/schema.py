"""Typed records the research agent passes between discovery, extraction, and storage.

``Candidate`` is produced deterministically by ``agent.discover`` (no LLM). ``EventDraft``
is what ``agent.llm`` must return from a single candidate — the *only* LLM-authored
shape in the pipeline, validated before anything is written to disk. See AGENTS.md §2a.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# Entity frontmatter `type` -> the kb/entities/<kind>/ directory it lives under.
ENTITY_KIND_DIRS: dict[str, str] = {
    "Project": "projects",
    "Organization": "orgs",
    "Technology": "tech",
    "Topic": "topics",
    "Place": "places",
}


class Candidate(BaseModel):
    """One discovered item, ranked, before verification or extraction."""

    url: str
    title: str
    summary: str = ""
    published: str = ""  # ISO date if the feed provided one, else ""
    theme: str
    score: float


class SourceRef(BaseModel):
    id: str
    resource: str
    title: str
    author: str = ""
    last_modified: str = ""


class EntityMention(BaseModel):
    ref: str  # "<kind-dir>/<slug>" — reuse an existing ref when the entity is known
    title: str
    type: str  # one of ENTITY_KIND_DIRS
    description: str = ""  # one factual sentence; only used when this entity is new


class Budget(BaseModel):
    """One depth tier from ``taxonomy.yaml``'s ``budgets`` — the run stops cleanly
    once any limit is hit. See AGENTS.md §2a rule 7."""

    max_new_events: int
    max_searches: int  # network fetches (article pages), not literal search queries
    max_usd: float  # informational for now; no per-token cost metering yet
    timeout_min: int


class EventDraft(BaseModel):
    """The model's structured output for one candidate. ``None`` (not this type) means
    the model judged the candidate out of scope, unverifiable, or not a real event."""

    kind: str
    title: str
    description: str
    date: str  # YYYY-MM-DD, or YYYY-MM if the day is genuinely unclear
    themes: list[str] = Field(min_length=1)
    entities: list[EntityMention] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(min_length=1)
    body: str
