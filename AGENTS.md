# AGENTS.md

Guidance for agents working in this repo. There are **two distinct kinds of agent**
with different jobs and different rules — read the section for the one you are:

| You are… | When | You change | Section |
|---|---|---|---|
| a **coding agent** (Claude Code, etc.) | developing the project | code, config, workflows, docs, tests | [§1](#1-coding-agents--project-development) |
| a **runtime agent** (research / publication) | inside GitHub Actions | `kb/**` (research) or `site/**` (publish) | [§2](#2-runtime-agents--github-actions) |

Humans and full design: [docs/DESIGN.md](docs/DESIGN.md).

## What this project is

PlanetAI maintains an **append-only, immutable event store** about AI for climate
justice, human rights, and a livable planet, and publishes it as a static wiki on
GitHub Pages. The atomic unit is a **dated, sourced factual event** (paper, project
launch/update, report, funding, policy, legal move, dataset/benchmark, notable news,
event, job-openings snapshot). Entity pages (actors, projects, technologies, topics)
give context and are largely projections of the event log.

## Rules for everyone

- **Never push to `main`.** It is branch-protected. All changes land via pull request
  with green CI (`lint` + `test`).
- **Stay in your lane.** A coding agent does not research or write `kb/` content; a
  runtime agent does not touch code, workflows, or dependencies.
- **Attribution.** End commit messages with
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` and PR descriptions with
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

---

## 1. Coding agents — project development

You build and maintain the pipeline: `agent/`, `genui/`, `scripts/`, workflows,
tests, config, docs. Your backlog is [TODO.md](TODO.md).

### Scope

- **Do not author `kb/` content.** No hand-written events or entity pages. Example
  data for tests goes in `tests/fixtures/`, never `kb/`.
- **Do not edit existing files under `kb/events/`** — immutability applies to you too
  (CI enforces it). Schema/format changes are made in the validator + `docs/DESIGN.md`
  + this file together, and applied to future events only.
- Secrets live in repo Actions secrets and `.env` (gitignored); never commit them.
  Keep `.env.example` in sync when you add a variable.

### Toolchain

Python tooling uses [`uv`](https://docs.astral.sh/uv/) — never `pip`/`venv`.

```
uv sync                       # install dev tooling into .venv
uv run pre-commit install     # enable git hooks (first time)

uv run ruff check .           # lint     (pre-commit runs these on commit)
uv run ruff format .          # format
uv run mypy                   # type-check (strict)
uv run pytest                 # tests

uv run python -m scripts.validate   # schema + immutability + link checks
uv run python -m scripts.project    # kb/ -> build/okf/ + build/feed.xml
uv run python -m genui.build        # placeholder front page (not wired into publish yet)
```

Local wiki preview needs the Kiso CLI (Java 21): download `kiso-cli.jar` from
[oak-invest/kiso releases](https://github.com/oak-invest/kiso/releases), then
`java -jar kiso-cli.jar build --source build/okf --destination site`.

- Target Python 3.13. Commit `uv.lock` with any dependency change. Add runtime deps
  deliberately (they run in CI on every scheduled job) — prefer the stdlib.
- All of `ruff check`, `ruff format --check`, `mypy`, `pytest` must pass before a PR.

### Workflow

- Branch, commit small, open a PR. One logical change per PR.
- When a change is notable, update [CHANGELOG.md](CHANGELOG.md) (`[Unreleased]`) and
  tick / add items in [TODO.md](TODO.md) in the same PR.
- Changing event/entity schema, the immutability rule, or the taxonomy shape means
  updating **together**: `scripts/kb.py` + `scripts/validate.py`, `docs/DESIGN.md`,
  this file, and any affected fixtures.

---

## 2. Runtime agents — GitHub Actions

Two runtimes, defined in `.github/workflows/`. Neither may modify code, workflows,
`pyproject.toml`, or `taxonomy.yaml`.

### 2a. Research agent — `research.yml`

Discovers in-scope factual events, verifies them, and opens a PR appending event
records. Touches **only** `kb/**` and `agent/candidates.json`.

1. **Events are immutable.** Never edit the body or frontmatter of an existing file
   under `kb/events/`. Corrections go in an appended `## Corrections` block (dated) or
   a follow-up event. CI enforces this.
2. **Facts, not analysis.** Record what verifiably happened, with a date and ≥1 source
   URL (with publication date). No opinion, impact speculation, rankings, or
   endorsements.
3. **Stay in scope.** Only themes and terms in `taxonomy.yaml`. Proposed new scope
   goes in the PR description as a suggestion, never added by the agent.
4. **Dedupe before writing.** Check candidates against existing event IDs and the
   linked entities' timelines. Multiple outlets on one thing = one event, many sources.
5. **Don't back-date.** `date` is when the event happened (as reported); `generated.at`
   is now. Use `YYYY-MM` when the day is unknown rather than guessing one.
6. **Own words only** — see [Copyright & sourcing](#copyright--sourcing).
7. **Respect the run budget** (max searches / new files / tokens / wall-clock from
   `taxonomy.yaml` + workflow inputs). Stop cleanly when hit.

**PR conventions**

- One PR per run. Title: `events: <theme> — <n> new (<date>)`.
- Body: bullet list of events added (id + title + source), new entity stubs, and any
  taxonomy suggestions.
- Diffs are additive. A PR that modifies existing `kb/events/` files must fail CI; if
  it doesn't, stop and flag it.

### 2b. Publication agents — `publish.yml`

Run on merge to `main`; build and deploy the site. **Never open a PR, never write to
`kb/`, never commit `site/`** (it is a build artifact).

- **`scripts/validate`** then **`scripts/project`** (deterministic code, not models):
  validate the bundle, then write `build/okf/` (events copied, entity `<!-- timeline -->`
  filled, `index.md`/`log.md`/theme pages generated) + `build/feed.xml`.
- **Kiso** builds `build/okf/` → `site/`. `build/` and `site/` are artifacts — never
  committed.
- **GenUI agent** (*not wired into `publish.yml` yet*) will compose `site/index.html`
  from the projected recent-events data. It curates copy; it adds no facts; a failed
  generation must not break the build (fall back to Kiso's own index). Copyright &
  sourcing still applies — link out, don't paste third-party prose or media.

### Event file format

Path: `kb/events/<year>/<YYYY-MM-DD>-<slug>.md` (filename must start with `date`).
OKF frontmatter; `type` is always `Event`, `kind` is the event kind. `scripts/validate`
is the authority — match [`kb/events/2023/2023-08-03-prithvi-geospatial-model-open-sourced.md`](kb/events/2023/2023-08-03-prithvi-geospatial-model-open-sourced.md).

```yaml
---
type: Event
kind: project-launch            # one of taxonomy.yaml event_kinds
title: "FooProject launches an open flood-risk model for the Sahel"
description: One-sentence factual summary.
date: 2026-09-03                 # when it happened; YYYY-MM-DD, or YYYY-MM if fuzzy
themes: [climate-justice]        # ⊆ taxonomy theme ids, non-empty
entities: [projects/fooproject, orgs/some-university]   # bundle-relative, no extension
tags: [flood, west-africa]
generated: { by: planetai/openrouter:anthropic/claude-sonnet-5, at: 2026-09-04T06:12:00Z }
status: stable
sources:
  - id: launch-post
    resource: https://…          # required
    title: "FooProject — launch announcement"
    author: FooProject
    last_modified: 2026-09-03
---

2–5 factual, sourced sentences. Cite with footnotes (`[^launch-post]`). No speculation.
```

Entity pages (`kb/entities/<kind>/<slug>.md`, `<kind>` = `projects`/`orgs`/`tech`/
`topics`/`places`): OKF frontmatter (`type: Project`/`Organization`/…), a short factual
intro, and a `<!-- timeline -->` marker the build replaces. Create a stub whenever an
event links an entity with no page yet — `scripts/validate` fails on a dangling ref.

Job openings: one aggregate event per period (`kind: job-openings`,
`kb/events/<year>/<YYYY-MM>-jobs.md`) listing each in-scope posting (org, role,
location, link, closing date). Immutable; next period gets its own file.

### Copyright & sourcing

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
  excluded from the published site.

Full rationale in [docs/DESIGN.md](docs/DESIGN.md) → Legal & licensing. Not legal
advice.

## Repository layout

```
taxonomy.yaml          scope + model + budgets (themes, include/exclude, seeds)
kb/.kiso/               Kiso site config (name, baseUrl, theme)
kb/events/<year>/       immutable event records: <date>-<slug>.md
kb/entities/<kind>/     living context pages (projects/orgs/tech/topics/places)
kb/sources/             raw captured source material (not published)
agent/                  research agent (OpenRouter client, schema, store, discover) — TODO §3
genui/                  front-page generator + layout shell
scripts/                kb.py (loaders), project.py (kb→build/okf+feed), validate.py
build/, site/           artifacts, gitignored, built in CI
tests/                  test suite + fixtures (fixture events live here, not in kb/)
.github/workflows/      ci.yml, publish.yml, validate.yml, research.yml (TODO §4)
docs/                   design doc, ADRs
```
