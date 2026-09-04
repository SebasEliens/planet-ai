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

An **OKF bundle**: a directory of Markdown files with YAML frontmatter, no runtime or
SDK required. See the [OKF spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
and [format overview](https://github.com/GoogleCloudPlatform/open-knowledge-format).
Two kinds of file:

**Events — `kb/events/<year>/<date>-<slug>.md`  (immutable)**

```yaml
id: 2026-09-03-fooproject-launch
date: 2026-09-03          # when it happened (best-known; note precision if fuzzy)
recorded: 2026-09-04      # when the agent added it
type: paper | project-launch | project-update | report | funding |
      policy | legal | dataset | benchmark | news | event | job-openings
title: "FooProject launches open flood-risk model for the Sahel"
themes: [climate-justice]
entities: ["[[fooproject]]", "[[some-university]]"]
sources:
  - url: https://…
    publisher: FooProject
    published: 2026-09-03
```

Body: 2–5 factual, sourced sentences — what happened, who, what's new. **Never edited
after merge.** Mistakes are handled by appending a `## Corrections` block (dated) or a
follow-up event; a CI check rejects PRs that modify the body or frontmatter of an
existing event file.

**Entities — `kb/entities/<kind>/<slug>.md`  (living context)**

Actors, projects, technologies, topics, places. A short intro (what it is, why it's in
scope) plus an auto-generated `<!-- timeline -->` block that the build fills with every
event referencing the entity, reverse-chronological. Entities are created as stubs the
moment an event links them; the agent may expand the intro later. Discontinued
projects keep their page and full timeline.

**Job openings** are modelled as a single aggregate event per search period
(`type: job-openings`, e.g. `kb/events/2026/2026-09-jobs.md`): a dated snapshot listing
every in-scope posting found that period — org, role, location, link, closing date.
Immutable like any event; the next period gets its own file. Openings are a useful
signal of where money and attention are moving.

- Cross-links via `[[wikilinks]]` **and** relative Markdown links (dual-linking keeps
  it readable in Obsidian, GitHub, and the built site).
- `kb/sources/` holds raw captured material (URL, publication date, retrieval date,
  excerpt) so events stay auditable.
- Validation in CI with [`scaccogatto/okf-skills`](https://github.com/scaccogatto/okf-skills)
  (ships a GitHub Action) or [`openknowledge`](https://github.com/openknowledge-sh/openknowledge),
  plus a custom immutability check and a link/ID-uniqueness check.

### 2. Deep-research agent — `agent/`

Runs in `research.yml`. Responsibilities: discover in-scope factual events not yet in
the log, verify each against sources, and append event files (+ entity stubs).

- **Engine:** Claude Code / Claude Agent SDK (`claude-sonnet-5`), or
  [GitHub Agentic Workflows (`gh-aw`)](https://github.github.com/gh-aw/) which compiles a
  Markdown+YAML workflow spec into an Actions job with cron, sandboxing, and permissions.
- **Research pipeline** inspired by
  [`langchain-ai/openwiki`](https://github.com/langchain-ai/openwiki) (agent → OKF →
  static export, already wires this end to end),
  [`nvk/llm-wiki`](https://github.com/nvk/llm-wiki) (thesis-driven, anti-confirmation-bias,
  `[[wikilink]]` synthesis), and
  [`jordan-gibbs/hyperresearch`](https://github.com/jordan-gibbs/hyperresearch)
  (multi-critic auditing, per-sentence cite-checking).
- **Sources:** theme `seeds` (RSS / journal / org / preprint / job-board feeds) are
  polled first; [Tavily](https://tavily.com) or Brave Search API fills gaps, time-filtered
  to `search_window_days`.
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

1. **Project** events into entity timelines and theme indexes (deterministic script).
2. **Build** the static site with [`kiso`](https://github.com/oak-invest/kiso)
   (`kiso-cli build --source=kb --destination=site`) — emits Markdown + HTML +
   `sitemap.xml` + `llms.txt` + client-side search + a downloadable bundle;
   [documented for use in a GitHub Action](https://oak-invest.github.io/kiso/).
3. **Emit `feed.xml`** (Atom) of the most recent events.

Fallback if Kiso proves limiting: an SSG (MkDocs Material, Quartz, or Astro Starlight)
fed by a small OKF→SSG adapter.

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
| `.github/workflows/research.yml` | `schedule` (e.g. daily), `workflow_dispatch` | run agent → open PR against `main` |
| `.github/workflows/publish.yml` | `push` to `main` (paths: `kb/**`, `genui/**`, templates) | validate → project → `kiso build` → genui → deploy Pages |
| `.github/workflows/validate.yml` | `pull_request` | OKF validation + event immutability + link/ID checks |

## Repo layout

```
taxonomy.yaml      configurable scope: themes, include/exclude, priorities, seeds
kb/                OKF bundle (the knowledge base)
  events/<year>/   immutable dated event records (incl. periodic job-openings)
  entities/<kind>/ living context pages (actors, projects, tech, topics, places)
  sources/         raw captured source material
agent/             research agent code + prompts
  candidates.json  ranked discovery list, regenerated each run
genui/             front-page generator agent + layout shell
scripts/           discover, project (events→timelines), link/immutability checks
site/              build output (gitignored; built in CI)
docs/              this doc, ADRs
.github/workflows/
```

## Key decisions

- **Immutable event log as the core** — the atomic unit is a dated, sourced fact;
  events are append-only, entity pages are projections. Keeps history honest, makes the
  build deterministic, and sidesteps merge/rewrite conflicts.
- **Facts over analysis** — the agent records verifiable events, not opinion. Narrow
  scope, cheap verification, low controversy surface.
- **OKF over ad-hoc Markdown** — vendor-neutral spec, existing validators and a
  publishing engine (Kiso), agent- and human-readable without a translation layer.
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

Assumes a **public** repo (Actions minutes and Pages hosting are free) and
[Claude API pricing](https://docs.claude.com/en/docs/about-claude/pricing) as of
2026-06: Sonnet 5 $2 / $10 per MTok (in / out), cache reads ~$0.20/MTok; Opus 5
$5 / $25; Haiku 4.5 $1 / $5. Anthropic server-side web search ≈ $10 / 1,000 searches
(or Tavily / Brave free tiers: ~1–2k queries/month). Event extraction is lighter work
than open-ended synthesis, so runs sit toward the low end.

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

Levers: prompt caching (assumed), the
[Batch API](https://docs.claude.com/en/docs/build-with-claude/batch-processing) (−50%,
fine for scheduled runs), `effort: low` + Haiku 4.5 for extraction/dedupe workers, and
a hard per-run **token budget**. Costs scale with how many new events exist per run,
which falls once the log is warm (fewer novel items per crawl). Private repo adds
~$0.10–0.20 per run past the 2,000-minute Actions free tier.

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
- Kiso maturity — evaluate before committing; keep the SSG fallback warm. Does it
  support the entity-timeline projection, or does that stay a pre-build script?
- Confirm licences: code (MIT vs Apache-2.0), content (CC BY 4.0) — see Legal &
  licensing; add `LICENSE` + `LICENSE-content`.
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
