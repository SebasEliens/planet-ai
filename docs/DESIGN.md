# PlanetAI — Design Doc

**Status:** draft · **Date:** 2026-09-04

PlanetAI is an autonomous **deep-research agent** that continuously extends a public
**knowledge base** on AI for climate justice, human rights, and a generally livable planet
and just society. It is published it as a browsable **wiki** with an AI-generated front page — all running in
GitHub Actions, hosted on GitHub Pages.

**Editorial model — an immutable event store, linked as a wiki.** The knowledge base
is an append-only log of *factual, dated events*: papers published, projects launched
or updated, reports released, funding announced, policy and legal moves, notable news,
and open job postings. Events are never rewritten — a project being discontinued does
not erase the fact that it launched on a given date. On top of the event log sit
**entity pages** (actors, projects, technologies, topics) that give context and
collect every event referencing them into a timeline. The event log is the source of
truth; entity pages are largely projections of it.

This model narrows scope hard: the agent looks for *verifiable things that happened*,
not opinion or evergreen explainer content. Background prose exists only to make the
events legible.

## Goals

- A research agent that runs on a schedule in CI, searches the web for factual
  developments, and appends dated event records to the knowledge base.
- Append-only: events are immutable once merged (corrections are appended, not edited).
- Knowledge base stored as plain files in **[Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)**
  (Markdown + YAML frontmatter) — human-authorable, agent-parseable, git-native.
- Deterministic build: OKF bundle → static wiki, deployed to GitHub Pages.
- A "generative UI" step that composes a front page around the most recent events.
- Every event traceable to at least one source URL with a publication date.

## Non-goals (v1)

- No runtime backend or database — everything is static files in the repo.
- No human editorial workflow beyond PR review.
- No multi-topic hub; one repo = one thematic knowledge base.
- Not a comprehensive reference work — no exhaustive definitional coverage; entity
  prose stays minimal.
- No opinion/analysis content, no ranking or endorsement of projects.
- No deletion of events for staleness — the log only grows.
- No copied source prose, abstracts, or media — own-words summaries + links only
  (see Legal & licensing).

## Architecture

```
                    ┌─────────────────────────────────────────┐
  cron / manual ──► │  research.yml  (GitHub Actions)          │
                    │  ├─ deep-research agent                  │
                    │  │   ├─ poll seeds + web search (recent) │
                    │  │   ├─ fetch + extract + verify dates   │
                    │  │   ├─ dedupe vs. existing event IDs    │
                    │  │   └─ append event files + entity stubs│
                    │  └─ opens PR with kb/ changes            │
                    └───────────────┬─────────────────────────┘
                                    │ merge
                    ┌───────────────▼─────────────────────────┐
  push to main ───► │  publish.yml  (GitHub Actions)           │
                    │  ├─ validate OKF bundle (+ immutability) │
                    │  ├─ project events → entity timelines    │
                    │  ├─ kiso build  kb/ → site/              │
                    │  ├─ genui agent → site/index.html        │
                    │  └─ deploy site/ + feed.xml → Pages      │
                    └─────────────────────────────────────────┘
```

## Components

### 1. Knowledge base — `kb/`

`kb/` is a valid **[OKF v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bundle**: nested directories of Markdown files, each with a YAML frontmatter block whose
only required field is `type`. Frontmatter follows OKF conventions (`title`,
`description`, `tags`, `generated`, `sources`, `status`); `index.md` and `log.md` are
reserved names (directory listing / chronological history). We add a few custom fields
(`kind`, `date`, `themes`, `entities`) — OKF consumers ignore unknown fields. Two
authored kinds of file:

**Events — `kb/events/<year>/<YYYY-MM-DD>-<slug>.md`  (immutable)**

```yaml
---
type: Event
kind: project-launch      # paper | project-launch | project-update | report | funding |
                          # policy | legal | dataset | benchmark | news | event | job-openings
title: "FooProject launches an open flood-risk model for the Sahel"
description: One-sentence factual summary.
date: 2026-09-03          # when it happened (best-known; note precision if fuzzy)
themes: [climate-justice]
entities: [projects/fooproject, orgs/some-university]   # bundle-relative, no extension
tags: [flood, west-africa, open-model]
generated: { by: planetai/openrouter:anthropic/claude-sonnet-5, at: 2026-09-04T06:12:00Z }
status: stable            # merged events are immutable ⇒ always "stable"
sources:
  - id: launch-post
    resource: https://…
    title: "FooProject — launch announcement"
    author: FooProject
    last_modified: 2026-09-03
---

2–5 factual, sourced sentences — what happened, who, what is new. Claims cite sources
with footnotes (`[^launch-post]`). **Never edited after merge.** Corrections go in an
appended `## Corrections` block (dated) or a follow-up event; CI rejects any PR that
modifies the body or frontmatter of an existing event file.
```

**Entities — `kb/entities/<kind>/<slug>.md`  (living context)**

`type:` is `Project` / `Organization` / `Technology` / `Topic` / `Place`. A short
factual intro (what it is, why it's in scope) plus a `<!-- timeline -->` marker that the
build replaces with every event referencing the entity, reverse-chronological. Entities
are created as stubs the moment an event links them; the intro can be expanded later.
Discontinued projects keep their page and full timeline.

**Job openings** — a single aggregate event per search period (`kind: job-openings`,
`kb/events/<year>/<YYYY-MM>-jobs.md`): a dated snapshot listing every in-scope posting
found that period (org, role, location, link, closing date). Immutable; the next period
gets its own file.

- **Links** are relative Markdown (`../../entities/projects/fooproject.md`) or
  OKF bundle-relative (`/entities/projects/fooproject.md`). No `[[wikilinks]]` — Kiso
  and OKF use standard Markdown. The `entities:` frontmatter list is the machine-readable
  form the projector uses to build timelines.
- `kb/sources/` holds raw captured material (URL, publication date, retrieval date,
  short excerpt) so events stay auditable. Excluded from the published site.
- `kb/.kiso/configuration.yaml` — site name, description, `baseUrl`, theme (§3).
- Validation: `scripts/validate` (own-words schema + immutability + link/ID checks) and
  `kiso-cli check`; optionally [`scaccogatto/okf-skills`](https://github.com/scaccogatto/okf-skills).

### 2. Deep-research agent — `agent/`

Runs in `research.yml`. Responsibilities: discover in-scope factual events not yet in
the log, verify each against sources, and append event files (+ entity stubs).

- **Engine:** a small custom Python agent (`agent/`), not a framework. The LLM is
  reached through **[OpenRouter](https://openrouter.ai)** (OpenAI-compatible API, via
  the `openai` SDK) so the model is a swappable config string — default
  `anthropic/claude-sonnet-5`, changeable to GPT/Gemini/OSS without code changes. Our
  code owns seed-polling, candidate scoring, dedupe, file writes, validation, and PR
  creation; the LLM only researches a candidate and returns a structured event record
  (JSON-schema / `response_format`). This keeps spend hard-capped per run and the
  immutability/dedupe rules deterministic. Runs as a scheduled GitHub Action.
- **Web search / fetch:** OpenRouter's provider-agnostic `web` plugin (Exa-backed) is
  the default "server tool"; theme `seeds` (RSS / journal / org / preprint / job-board
  feeds) are polled first by our own code. Search is behind a thin interface so it can
  swap to Tavily / Brave / a native provider tool.
- **Pipeline** inspired by
  [`langchain-ai/openwiki`](https://github.com/langchain-ai/openwiki) (agent → OKF →
  static export) and
  [`jordan-gibbs/hyperresearch`](https://github.com/jordan-gibbs/hyperresearch)
  (per-sentence cite-checking, adversarial verification).
- **Fact discipline:** an event needs a concrete date and at least one source; the
  agent records the event date as reported (flagging imprecision), never back-dates to
  "now", and writes only what the sources support — no speculation about impact.
- **Dedupe:** before appending, the agent checks the candidate against existing event
  IDs and each linked entity's timeline; near-duplicates from multiple outlets collapse
  to one event with multiple sources.
- **Output discipline:** changes land as a **pull request**, never a direct commit to
  `main` — PR is the review gate. Each PR body summarises the events added.
- **Scope guardrails:** only themes/terms permitted by the taxonomy (§2a); per-run
  budget (max searches, max new files, token budget, wall-clock timeout).

### 2a. Configurable topic taxonomy — `taxonomy.yaml`

A version-controlled file at the repo root is the single source of truth for scope.
Editing it (via PR) is how a maintainer steers the agent — no code changes.

```yaml
# taxonomy.yaml
themes:
  - id: climate-justice
    label: Climate Justice
    include: ["loss and damage", "just transition", "climate litigation", ...]
    exclude: ["carbon-credit market mechanics", ...]
    priority: 3           # relative weight when the agent allocates its run budget
  - id: ai-human-rights
    label: AI & Human Rights
    include: ["algorithmic discrimination", "border surveillance", ...]
    priority: 2
seeds:                     # feeds polled first, per theme (RSS/Atom/JSON, job boards)
  climate-justice: ["https://…", ...]
event_types: [paper, project-launch, project-update, report, funding,
              policy, legal, dataset, benchmark, news, event, job-openings]
search_window_days: 90     # time-filter for supplemental web search
depth_default: standard    # light | standard | deep  (see §2b)
```

`include`/`exclude` terms seed discovery and constrain which events the agent may add.

### 2b. Autonomous event discovery — `scripts/discover`

Each run, before writing, the agent builds a ranked candidate list and works the top
items within budget:

1. **New events from seeds** *(highest weight)* — new items in theme feeds since the
   last run, filtered to in-scope, deduped against existing event IDs.
2. **New events from search** — targeted queries per theme `include` term over the
   `search_window_days` window, for events the feeds missed.
3. **Missing entity pages** — entities linked by events but with no page yet → create
   stubs; optionally enrich thin intros.
4. **Backfill (bounded)** — for a newly tracked entity, pull its recent history back to
   a configured cutoff, then switch to recent-only.
5. **Frontier expansion** — the agent proposes adjacent subtopics/terms; these surface
   in the PR as taxonomy suggestions for maintainer review, not auto-added.

Output: `agent/candidates.json` (regenerated each run, committed with the PR for
transparency). A deterministic scorer ranks candidates; the agent chooses among the top
ones and does the verification work — keeping selection auditable. There is **no
staleness pass** — the log is append-only, so old events are simply old, not stale.

### 3. Wiki build — `publish.yml` → `site/`

1. **`scripts/validate`** — schema + immutability + link/ID checks (also runs on PRs).
2. **`scripts/project`** — deterministic. Reads `kb/` and writes a *derived* OKF bundle
   to `build/okf/`: copies events + entities, fills each entity's `<!-- timeline -->`
   from the events that reference it, generates `index.md` per directory and a per-theme
   + root `log.md` (OKF's reserved chronological-history file), and emits
   `build/feed.xml` (Atom) of recent events. `kb/` stays the minimal immutable log;
   `build/okf/` is disposable.
3. **`kiso-cli build --source build/okf --destination site`** — via the
   [`oak-invest/kiso` action](https://oak-invest.github.io/kiso/) (pinned). Emits the
   Markdown, HTML, `llms.txt`, `sitemap.xml`, client-side search, and a downloadable
   bundle. Config in `build/okf/.kiso/configuration.yaml` (`site.baseUrl` =
   the Pages URL, `site.name/title/description`, `theme.name` — DaisyUI, default
   `light`).
4. **genui** overwrites `site/index.html` (§4); `build/feed.xml` is copied to
   `site/feed.xml`.

Kiso has no feed/RSS output (hence step 2) and its nav is a DaisyUI theme. Fallback if
it proves limiting: an SSG (MkDocs Material, Quartz, Astro Starlight) fed from the same
`build/okf/` bundle.

### 4. Generative UI front page — `genui/`

After the wiki builds, a second agent pass composes `site/index.html` as a
**recent-events briefing**: the newest events (since last publish, then trailing back a
few weeks), grouped by theme, each linking into the wiki; a "new this period" list of
entity pages created; and the current job-openings snapshot. Input = the projected
recent-events list + diff of `kb/` since last publish. Output = one self-contained HTML
file dropped into `site/` before deploy. Deterministic layout shell, generative
copy/curation — isolated so a bad generation can't break the wiki.

### 5. Deploy

`actions/upload-pages-artifact` + `actions/deploy-pages` publish `site/` to GitHub Pages.

## Workflows

| File | Trigger | Does |
|---|---|---|
| `.github/workflows/ci.yml` | `push` to `main`, `pull_request` | ruff + mypy + pytest |
| `.github/workflows/research.yml` | `schedule` (e.g. daily), `workflow_dispatch` | run agent → open PR against `main`. Secret: `OPENROUTER_API_KEY` |
| `.github/workflows/publish.yml` | `push` to `main` (paths: `kb/**`, `genui/**`, `scripts/**`, `taxonomy.yaml`) | validate → project → `kiso build` → genui → deploy Pages |
| `.github/workflows/validate.yml` | `pull_request` | `scripts/validate` + `kiso check` |

## Repo layout

```
taxonomy.yaml      configurable scope: themes, include/exclude, priorities, seeds
kb/                OKF bundle (the knowledge base) — the minimal immutable log
  .kiso/           Kiso site config (name, baseUrl, theme)
  events/<year>/   immutable dated event records (incl. periodic job-openings)
  entities/<kind>/ living context pages (Project/Organization/Technology/Topic/Place)
  sources/         raw captured source material (not published)
agent/             research agent: OpenRouter client, schema, store, discover, research
  candidates.json  ranked discovery list, regenerated each run
genui/             front-page generator + layout shell
scripts/           project (kb → build/okf + feed), validate
build/             derived OKF bundle + feed (gitignored; built in CI)
site/              built site (gitignored; built in CI)
docs/              this doc, ADRs
.github/workflows/ ci, research, publish, validate
```

## Key decisions

- **Immutable event log as the core** — the atomic unit is a dated, sourced fact;
  events are append-only, entity pages are projections. Keeps history honest, makes the
  build deterministic, and sidesteps merge/rewrite conflicts.
- **Facts over analysis** — the agent records verifiable events, not opinion. Narrow
  scope, cheap verification, low controversy surface.
- **OKF over ad-hoc Markdown** — vendor-neutral spec, a ready publishing engine (Kiso),
  agent- and human-readable without a translation layer.
- **OpenRouter, not a provider SDK** — the model is a config string
  (`anthropic/claude-sonnet-5` today), swappable without code changes; one API key and
  bill. The trade is a ~5% credit fee and reliance on OpenRouter as an intermediary.
- **LLM boxed to research + extraction** — all file writes, dedupe, and validation are
  our deterministic code, so spend is hard-capped and immutability is enforceable.
- **PR-gated agent writes** — keeps a human in the loop cheaply; matches the pattern in
  [this weekly-research gh-aw example](https://shinglyu.com/blog/2026/04/15/automating-weekly-research-with-github-agentic-workflows.html).
- **Static-only hosting** — zero infra, free on GitHub Pages, fully forkable.
- **Copyright-light by construction** — storing facts + dates + own-words summaries +
  links (never source prose, abstracts, or media) keeps the KB on the safe side of
  copyright; see below.

## Legal & licensing

Not legal advice. The factual-event model is deliberately the low-risk design, but a
few things still need care.

**Why the model is safe.** Copyright protects expression, not facts, ideas, or events
(US: *Feist*; EU: the originality bar). "Project X launched on date Y, funded by Z" is
a fact; recording it in our own words and linking the source is fine.

**Rules the agent must follow** (enforced in prompts + review; see
[AGENTS.md](../AGENTS.md)):

- **Own words, not close paraphrase.** Infringement isn't limited to verbatim copying —
  tracking a source's sentence structure and phrasing counts. Re-express genuinely.
- **Never copy** abstracts, figure captions, or headlines wholesale; summarize them.
  Retitle events in our own words (the EU press-publishers' right, Art. 15 DSM
  Directive, carves out links + "very short extracts" only).
- **At most one short attributed quote** per source (≤ ~25 words), only where the exact
  wording matters.
- **No copied media.** Images, figures, charts, screenshots, logos are
  copyrighted/trademarked — link, never embed or vendor.
- **Independent selection.** The agent picks events against `taxonomy.yaml`, never by
  mirroring someone's curated list (compilation copyright; EU sui generis database
  right on substantial extraction).
- **Prefer official feeds/APIs** over scraping; respect `robots.txt` and site ToS
  (esp. job boards — a contract/CFAA question separate from copyright).
- **Neutral factual phrasing** for claims about people/orgs (defamation risk is
  separate from copyright); state only what sources support, with attribution.

**`kb/sources/` excerpts** are verification material: cap at one sentence / ~25 words,
mark as a quote with attribution, and keep them **unpublished** (gitignored from the
built site) so the KB redistributes only our own text + links.

**Licensing.**

- **Code** — permissive (MIT or Apache-2.0), `LICENSE`.
- **KB content** (our summaries, entity prose) — CC BY 4.0, `LICENSE-content`, with a
  note that facts and links are not claimed and that each cited source remains under
  its own rights.
- Every page carries a visible **"AI-generated, PR-reviewed"** disclosure and a link to
  the corrections/takedown process (the append-only `## Corrections` block).

**Jurisdiction.** Hosted on GitHub (US), but EU contributors/readers mean the EU
database right and press-publishers' right are the main extra exposure — worth a short
targeted review if the KB grows into a substantial public resource.

## Operational costs

Assumes a **public** repo (Actions minutes and Pages hosting are free). LLM billed
through OpenRouter, which passes provider pricing through (`anthropic/claude-sonnet-5`
= $2 / $10 per MTok in/out, same as first-party) plus a ~5% fee on credit purchases.
Web search via OpenRouter's `web` plugin (Exa) ≈ $4 / 1,000 results, or Tavily / Brave
free tiers. Event extraction is lighter work than open-ended synthesis, so runs sit
toward the low end.

| Item | Light run | Standard run | Deep run |
|---|---|---|---|
| Feeds + searches / pages read | ~8 / ~12 | ~20 / ~30 | ~50 / ~90 |
| Model | Sonnet 5 | Sonnet 5 | Opus 5 + Sonnet/Haiku workers |
| LLM tokens (cached-heavy) | ~$0.3–0.6 | ~$1.5–3 | ~$8–18 |
| Web search | ~$0.08 | ~$0.20 | ~$0.50 |
| **Per research run** | **~$0.4–0.8** | **~$2–3.5** | **~$9–19** |
| GenUI front-page pass | ~$0.15–0.35 (one-shot, Sonnet 5) |||

**Monthly estimate** (research + one GenUI pass per publish):

| Cadence | Depth | ~Monthly |
|---|---|---|
| Daily | light | **$20–35** |
| Daily | standard | **$70–120** |
| Weekly | deep | **$45–85** |
| Daily | deep | **$300–600** |

Levers: prompt caching (Anthropic-model `cache_control` passes through OpenRouter),
a cheaper model for the extraction/dedupe passes (`anthropic/claude-haiku-4-5` or an
OSS model — one config change), capping results per search, and a hard per-run
**token/candidate budget**. Costs scale with how many new events exist per run, which
falls once the log is warm. Private repo adds ~$0.10–0.20 per run past the
2,000-minute Actions free tier.

Recommended starting point: **daily standard** — roughly **$70–120/month** — then tune.

## Open questions

- Taxonomy content: seed `themes` / `include` / `seeds` lists need domain input before
  first run (climate justice, AI & human rights, adjacent topics).
- Backfill cutoff: how far back to pull an entity's history on first tracking
  (e.g. 12–24 months) before switching to recent-only.
- Event granularity: when several outlets cover one thing, one event + many sources —
  but where's the line between "an update" and "a new event"?
- Job-openings cadence: weekly vs. monthly snapshot; which job boards / org pages to
  poll; how to scope "relevant".
- Entity identity & merges: canonical slugs, aliasing, splitting/merging entities
  without breaking event links.
- Discovery scoring weights — tune from `candidates.json` history.
- Kiso theming/nav — the default DaisyUI theme; how much branding to layer on, and
  whether its nav copes with a large flat `events/` tree (may need date-grouped index
  pages from the projector).
- OpenRouter data policy — set the account to no-logging / no-training; low sensitivity
  (public web input) but worth doing.
- Whether `kb/sources/` excerpts are kept in-repo but excluded from the build, or
  dropped entirely after verification.
- Job-board ToS review before polling any non-feed source.

## Prior art

- [`langchain-ai/openwiki`](https://github.com/langchain-ai/openwiki) — agent → OKF →
  static export → self-updating via CI. Closest single reference.
- [`oak-invest/kiso`](https://github.com/oak-invest/kiso) — OKF bundle → static website.
- [`GoogleCloudPlatform/knowledge-catalog`](https://github.com/GoogleCloudPlatform/knowledge-catalog) — OKF spec.
- [`scaccogatto/okf-skills`](https://github.com/scaccogatto/okf-skills) — author/validate/visualize OKF; GitHub Action.
- [`github/gh-aw`](https://github.github.com/gh-aw/) — agentic workflows compiled to GitHub Actions.
- [`jordan-gibbs/hyperresearch`](https://github.com/jordan-gibbs/hyperresearch) — deep-research pipeline with adversarial auditing.
- [`nvk/llm-wiki`](https://github.com/nvk/llm-wiki) — multi-agent research into an interlinked Markdown wiki.
