# AGENTS.md

Guidance for any agent working in this repo — the scheduled research agent, the
front-page (genui) agent, and coding agents (Claude Code, etc.). Humans: see
[docs/DESIGN.md](docs/DESIGN.md) for the full design.

## What this project is

PlanetAI is an autonomous deep-research agent that maintains an **append-only,
immutable event store** about AI for climate justice, human rights, and adjacent
topics, and publishes it as a static wiki on GitHub Pages. The atomic unit is a
**dated, sourced factual event** (paper, project launch/update, report, funding,
policy, legal move, dataset/benchmark, notable news, event, job-openings snapshot).

## Core rules

1. **Events are immutable.** Never edit the body or frontmatter of an existing file
   under `kb/events/`. Corrections go in an appended `## Corrections` block (dated) or
   a follow-up event. CI enforces this.
2. **Facts, not analysis.** Record what verifiably happened, with a date and ≥1 source
   URL (with publication date). No opinion, speculation about impact, rankings, or
   endorsements.
3. **Stay in scope.** Only themes and terms in `taxonomy.yaml`. Proposed new
   scope goes in the PR description as a suggestion, never silently added.
4. **Dedupe before writing.** Check candidate events against existing event IDs and the
   linked entities' timelines. Multiple outlets on one thing = one event, many sources.
5. **Never commit to `main`.** All agent output is a pull request. `site/` is built in
   CI, never committed.
6. **Don't back-date.** `date` is when the event happened (as reported); `recorded` is
   today. Flag imprecise dates rather than guessing.
7. **Own words only.** See Copyright & sourcing below — no copied prose, abstracts,
   headlines, or media.

## Repository layout

```
taxonomy.yaml          scope config (themes, include/exclude, priorities, seeds)
kb/events/<year>/       immutable event records: <date>-<slug>.md
kb/entities/<kind>/     living context pages (actors, projects, technologies, topics, places)
kb/sources/             raw captured source material
agent/                  research agent code + prompts; candidates.json (per-run discovery list)
genui/                  front-page generator + layout shell
scripts/                discover, project (events→timelines), link/immutability checks
.github/workflows/      research.yml, publish.yml, validate.yml
docs/                   design doc, ADRs
```

## Event file format

Path: `kb/events/<year>/<YYYY-MM-DD>-<slug>.md`

```yaml
---
id: 2026-09-03-fooproject-launch
date: 2026-09-03
recorded: 2026-09-04
type: project-launch          # see event_types in taxonomy.yaml
title: "FooProject launches open flood-risk model for the Sahel"
themes: [climate-justice]
entities: ["[[fooproject]]", "[[some-university]]"]
sources:
  - url: https://…
    publisher: FooProject
    published: 2026-09-03
---

2–5 factual, sourced sentences: what happened, who, what is new. No speculation.
```

Entity pages (`kb/entities/<kind>/<slug>.md`): short factual intro + a
`<!-- timeline -->` marker that the build fills. Create a stub whenever an event links
an entity that has no page yet.

Job openings: one aggregate event per period (`type: job-openings`,
`kb/events/<year>/<YYYY-MM>-jobs.md`) listing each in-scope posting (org, role,
location, link, closing date). Immutable; next period gets its own file.

## Copyright & sourcing

Facts, dates, and events aren't copyrightable — our own-words summaries of them, plus
source links, are the safe zone. Stay inside it:

- **Write in your own words.** Not just "avoid verbatim" — don't track the source's
  sentence structure or phrasing either. Genuinely re-express.
- **Never copy** a paper abstract, figure caption, or headline. Summarize; retitle
  events yourself.
- **At most one short attributed quote per source** (≤ ~25 words), only where the exact
  wording matters. Mark it as a quote with attribution.
- **No media.** Don't embed or commit images, figures, charts, screenshots, or logos —
  link to them.
- **Select independently.** Choose events against `taxonomy.yaml`; never reproduce
  someone else's curated list or dataset wholesale.
- **Prefer official feeds/APIs** to scraping. Respect `robots.txt` and site terms of
  service — especially job boards.
- **Neutral phrasing** for anything about a person or organisation; state only what a
  source supports, and attribute it.
- **`kb/sources/` excerpts:** one sentence / ~25 words max, for verification only;
  they are excluded from the published site.

Full rationale in [docs/DESIGN.md](docs/DESIGN.md) → Legal & licensing. Not legal
advice.

## Commands

Python tooling uses [`uv`](https://docs.astral.sh/uv/) — never `pip`/`venv`.

```
uv sync                       # install dev tooling into .venv
uv run pre-commit install     # enable git hooks (first time)

uv run ruff check .           # lint          (pre-commit runs these too)
uv run ruff format .          # format
uv run mypy                   # type-check (strict)
uv run pytest                 # tests
```

Not built yet (see [TODO.md](TODO.md)) — wire in as they land:

```
uv run scripts/validate       # OKF validation + event immutability + link/ID checks
uv run scripts/project        # events → entity timelines / theme indexes / feed data
kiso-cli build --source=kb --destination=site   # local site build
```

## Pull request conventions

- One PR per research run. Title: `events: <theme> — <n> new (<date>)`.
- PR body: bullet list of events added (id + title + source), any new entity stubs,
  and any taxonomy suggestions.
- Keep diffs additive. A PR that modifies existing `kb/events/` files should fail CI;
  if it doesn't, stop and flag it.
