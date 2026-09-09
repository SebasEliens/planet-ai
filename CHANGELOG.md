# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project will use
[Semantic Versioning](https://semver.org/) once it has releases.

Note: this changelog tracks the **project/system** (code, workflows, design). The
knowledge base itself is an append-only event log with its own history in
`kb/events/` and the published `feed.xml`.

## [Unreleased]

### Added
- Initial design doc ([docs/DESIGN.md](docs/DESIGN.md)): autonomous deep-research agent
  → immutable OKF event store → static wiki on GitHub Pages, with an AI-generated
  recent-events front page.
- Editorial model: append-only, immutable event records (papers, launches, updates,
  reports, funding, policy, legal, datasets, news, events, job-openings) linked by
  living entity pages.
- Configurable scope via `taxonomy.yaml` (themes, include/exclude, priorities, seeds).
- Autonomous event discovery from theme feeds + time-filtered web search; no staleness
  pass (the log only grows).
- Job-openings modelled as a periodic aggregate event.
- Legal & licensing section: copyright-light sourcing rules (own-words summaries +
  links, no copied prose/abstracts/media, independent selection, feeds over scraping),
  planned licences (permissive code, CC BY 4.0 content), and an "AI-generated,
  PR-reviewed" disclosure per page.
- `AGENTS.md` — split into rules for **coding agents** (§1, project development) vs.
  **runtime agents** (§2, research + publication in GitHub Actions), which have
  distinct scopes; shared rules and Copyright & sourcing called out separately.
- `TODO.md` — development backlog (explicitly not a research/content queue).
- Project scaffolding: git repo (`main`), `uv` project targeting Python 3.13,
  `pyproject.toml` with ruff (lint + format), mypy (strict), and pytest configured.
- `.pre-commit-config.yaml` — file-hygiene hooks, ruff, ruff-format, mypy, and a
  local hook blocking media/binary files under `kb/`.
- `.github/workflows/ci.yml` — lint, type-check, and test on push/PR.
- `.gitignore`, `.gitattributes`, `.editorconfig`, `.env.example`, `README.md`,
  `LICENSE` (MIT), `LICENSE-content` (CC BY 4.0).
- Directory skeleton: `agent/`, `genui/`, `scripts/`, `kb/{events,entities,sources}/`,
  `tests/`.
- GitHub Pages enabled (Actions build type) and `.github/workflows/publish.yml`
  (`configure-pages` → `upload-pages-artifact` → `deploy-pages`).
- Branch protection on `main` — requires `lint` + `test`; force-push and deletion
  blocked; conversation resolution required.
- **Real wiki pipeline** (replaces the placeholder front page):
  - `scripts/kb.py` — read-only loaders for the `kb/` OKF bundle.
  - `scripts/validate.py` — frontmatter schema, `kind`/`theme` membership, slug/date
    consistency, dangling entity refs, no `[[wikilinks]]`, and append-only immutability
    of `kb/events/**` vs `origin/main`.
  - `scripts/project.py` — projects `kb/` into `build/okf/` (events copied, entity
    `<!-- timeline -->` filled, `index.md` / `log.md` / theme pages generated) and emits
    `build/feed.xml` (Atom). Verified against the real `kiso-cli`.
  - `publish.yml` now runs validate → project → **Kiso** (`oak-invest/kiso` action) →
    feed → deploy. `validate.yml` runs validate + project + `kiso check` on PRs.
- Research-agent architecture chosen: custom Python agent on **OpenRouter**
  (OpenAI-compatible, model = a swappable slug, default `anthropic/claude-sonnet-5`),
  with the LLM boxed to research + structured extraction. `taxonomy.yaml` gains
  `model`, `budgets`, `event_kinds`, `backfill_months`.
- `taxonomy.yaml` — starter scope (climate justice, AI & human rights, environmental
  monitoring, AI governance) with seed feeds; needs a domain-expert pass.
- First `kb/` content: the Prithvi geospatial-model launch event + NASA / IBM / Prithvi
  entities, to pin the format.
- OKF/Kiso alignment: frontmatter follows OKF conventions (`type` + `generated` +
  `sources` + `status`); `[[wikilinks]]` dropped in favour of Markdown links;
  `kb/.kiso/configuration.yaml` added.
- **Generative front page, wired end-to-end** (replaces the placeholder):
  - `scripts/frontpage.py` — deterministic stats (`build/frontpage.json`): windowed
    recent events scored by sources+entities, per-theme activity vs. the prior window,
    new entities, latest job-openings snapshot. No LLM.
  - `genui/select.py` — pure, unit-tested function choosing a layout mode (`HEADLINE`
    / `DIGEST` / `QUIET`) and an accent theme colour from those stats. No LLM.
  - `genui/copy.py` — the one LLM step: OpenRouter call (`anthropic/claude-haiku-4-5`
    default) returns strict JSON copy (kicker/headline/dek/trends-note/theme blurbs);
    falls back to plain deterministic copy on any failure so the build can't break.
  - `genui/layouts/` — Jinja2 templates (base shell + 3 modes), 4 theme accent colours,
    dark-mode aware, CSS-only motion. `genui/build.py` orchestrates and overwrites
    Kiso's `site/index.html`. Verified against the real `kiso-cli` build in all three
    modes.
  - `publish.yml` — genui step runs after Kiso, with `OPENROUTER_API_KEY` from secrets.
- **Front-page visual identity**: colour-accented wordmark, an inline SVG contour-line
  mark (earth-observation motif, not a generic orbit icon) that recolours with the
  period's dominant theme, Source Serif 4 / Source Sans 3 pairing. Removed several
  "generated-page" typographic tells present in the first pass (ALL-CAPS tracked
  labels, dot/dash-joined meta strings, per-card fade-in animation).
- **Research agent, wired end-to-end** (`agent/`) — the last major unbuilt piece:
  - `agent/schema.py` / `agent/store.py` / `agent/discover.py` (feedparser over an
    httpx-fetched body — bounded timeouts, testable) / `agent/llm.py` (OpenRouter
    extraction) / `agent/research.py` (fetch → extract → write, within budget) /
    `agent/run.py` (orchestrate; writes `run-summary.md` + `pr-title.txt`).
  - `.github/workflows/research.yml` — fortnightly cron (1st & 15th) +
    `workflow_dispatch` depth choice; opens a PR via `peter-evans/create-pull-request`
    that auto-merges once `lint` + `test` pass (`gh pr merge --auto`, repo
    `allow_auto_merge` enabled) — no human approval step. `GITHUB_TOKEN`-authored PRs
    don't trigger `pull_request` workflows (GitHub's anti-recursion rule), so the
    `PLANETAI_PR_TOKEN` PAT is now load-bearing: without it the required checks never
    run and the PR waits for a maintainer.
  - **Found and fixed two real bugs via a live smoke test against real feeds + a real
    OpenRouter call** (not just mocked tests): the model wrote theme *labels* instead
    of taxonomy ids (`scripts/validate` correctly rejected both events — now the ids
    are passed explicitly in the prompt, and any drift is normalised back to the
    discovery theme in code, not just requested nicely); and it shortened source URLs
    to a bare domain (now the candidate's exact URL always wins for the primary
    source, regardless of what the model wrote) — both are "never trust the model for
    a fact we already know exactly" fixes, applied in code as defence in depth, not
    just prompt wording. Also bumped `MAX_OUTPUT_TOKENS` after JSON was truncated
    mid-string on longer articles.
  - 65 tests, all network calls (OpenRouter + feeds + article fetch) mocked/stubbed —
    consistent with the no-live-calls-in-CI rule used for `genui.copy`.

### Changed
- **Trunk-based for project development.** Coding agents and the maintainer commit
  straight to `main` (green locally first); a PR is now opt-in, for when review is
  wanted. Runtime agents (`research.yml`) still always open a PR — auto-merged, but
  kept as the traceable record of each run. `AGENTS.md` "How changes land" is the
  authority.
- `.github/workflows/automerge.yml` — arms auto-merge (squash) on any non-draft PR
  opened by the repo owner or the research agent, so a green `lint` + `test` merges
  with no click. Draft PRs and external contributors' PRs are left alone.

### Fixed
- `scripts/project` emitted a bare fuzzy `YYYY-MM` as a `log.md` heading, which Kiso
  rejects (`INVALID_LOG_DATE_FORMAT`) — this broke `publish.yml` on `main`. Log
  headings now use a new `Event.iso_date` (fuzzy months padded to the 1st); bullet
  lists still show the date as recorded.

### Notes
- Prior art surveyed: `langchain-ai/openwiki`, `oak-invest/kiso`,
  `GoogleCloudPlatform/knowledge-catalog` (OKF), `scaccogatto/okf-skills`,
  `github/gh-aw`, `jordan-gibbs/hyperresearch`, `nvk/llm-wiki`.
- Estimated operating cost: ~$5–10/month at the fortnightly-standard cadence (public
  repo), billed through OpenRouter (+~5% credit fee); ~$70–120 if dialled up to daily.
- Kiso pinned at v0.2.3 (Java 21 jar / `oak-invest/kiso` composite action).

[Unreleased]: https://github.com/SebasEliens/planet-ai/commits/main
