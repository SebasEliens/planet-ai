# TODO

Build order for PlanetAI. See [docs/DESIGN.md](docs/DESIGN.md). Check items off as
they land; move notable changes into [CHANGELOG.md](CHANGELOG.md).

## 0. Decisions to close first

- [ ] Fill in `taxonomy.yaml` seed content (themes, include/exclude, priorities, feeds)
      — needs domain input.
- [ ] Pick the research engine: Claude Agent SDK vs. `gh-aw`.
- [ ] Confirm OKF profile / version and whether Kiso can render entity timelines, or
      that stays a pre-build `scripts/project` step.
- [ ] Backfill cutoff for newly tracked entities (12–24 months?).
- [x] KB licence (CC BY 4.0) + `LICENSE` (MIT) / `LICENSE-content`.

## 1. Repository skeleton

- [x] `git init` (branch `main`), `.gitignore`, `.gitattributes`, `.editorconfig`.
- [x] `uv` project (`pyproject.toml`, `.python-version` 3.13, `uv.lock`), dev group:
      ruff, mypy, pytest, pre-commit.
- [x] `.pre-commit-config.yaml` (hygiene hooks + ruff + ruff-format + mypy + a
      no-media-in-`kb/` guard).
- [x] `.github/workflows/ci.yml` — lint + type-check + test.
- [x] `LICENSE` (code) and content licence.
- [x] Package dirs `agent/`, `genui/`, `scripts/`; `kb/{events,entities,sources}/`;
      `tests/` smoke test.
- [x] `README.md` with dev commands.
- [ ] `taxonomy.yaml` with real seed content.
- [ ] `kb/` first hand-written example event + entity to pin the format.
- [ ] Flesh out **Commands** in `AGENTS.md` once `scripts/` exist.
- [ ] Enable branch protection on `main` (require CI) once pushed to GitHub.

## 2. Knowledge-base tooling — `scripts/`

- [ ] `scripts/validate`: OKF validation + event **immutability** check (no diffs to
      existing `kb/events/**` bodies/frontmatter) + link resolution + `id` uniqueness.
- [ ] Enforce sourcing rules in CI where checkable: `kb/sources/` excerpt length cap,
      ≥1 source per event (no-media guard already in pre-commit).
- [ ] Exclude `kb/sources/` excerpts from the built site (build config, not deletion).
- [ ] `scripts/project`: events → entity `<!-- timeline -->` blocks + theme indexes +
      recent-events list (JSON) for genui and `feed.xml`.
- [ ] Schema for event & entity frontmatter (JSON Schema or pydantic).
- [ ] Wire `scripts/validate` + `scripts/project` into `validate.yml` / `publish.yml`.

## 3. Research agent — `agent/`

- [ ] Seed poller: fetch RSS/Atom/JSON feeds + job boards per theme, normalise items.
- [ ] Supplemental web search (Tavily or Brave), time-filtered to `search_window_days`.
- [ ] `scripts/discover`: rank candidates → `agent/candidates.json`.
- [ ] Dedupe against existing event IDs + entity timelines.
- [ ] Event extraction + verification prompt (date, sources, factual phrasing).
- [ ] Entity-stub creation for newly linked entities.
- [ ] Per-run budget guards (max searches / files / tokens / wall-clock).
- [ ] Open a PR with summary body.
- [ ] Job-openings aggregator (periodic `type: job-openings` event).

## 4. Workflows — `.github/workflows/`

- [ ] `research.yml`: scheduled + `workflow_dispatch`; runs agent; opens PR. Secrets:
      model API key, search API key.
- [ ] `validate.yml`: runs `scripts/validate` on PRs.
- [ ] `publish.yml`: on push to `main` → validate → `scripts/project` → `kiso build` →
      genui → `feed.xml` → deploy Pages.
- [ ] Pages setup (`actions/upload-pages-artifact`, `actions/deploy-pages`).

## 5. Wiki build

- [ ] Kiso integration (`kiso-cli build`), or SSG fallback (MkDocs Material / Quartz /
      Astro Starlight) + OKF→SSG adapter.
- [ ] `feed.xml` (Atom) of recent events.
- [ ] Basic theme/branding.

## 6. Generative UI front page — `genui/`

- [ ] Deterministic layout shell (`site/index.html` template).
- [ ] Agent pass: recent-events briefing grouped by theme + new entities + jobs snapshot.
- [ ] Isolation: bad generation cannot break the wiki build (fallback to a static
      recent-events list).

## 7. Hardening / later

- [ ] Tune discovery scoring from `candidates.json` history.
- [ ] Cost telemetry per run; alert if over budget.
- [ ] Entity merge/alias tooling.
- [ ] "AI-generated, PR-reviewed" disclosure + corrections/takedown link on every page.
- [ ] Evaluate multi-agent workers (Haiku) for extraction at scale.
- [ ] Make the repo cleanly forkable for other topic areas (docs + template).
