# TODO

**Development backlog only** — this file is for coding agents building the pipeline
(see [AGENTS.md](AGENTS.md) §1). It is not a research or content queue: the research
agent finds its own work autonomously from `taxonomy.yaml` and the event log, and
never reads this file.

Build order for PlanetAI. See [docs/DESIGN.md](docs/DESIGN.md). Check items off as
they land; move notable changes into [CHANGELOG.md](CHANGELOG.md).

## 0. Decisions to close first

- [ ] **Domain pass on `taxonomy.yaml`** — the starter themes/include/exclude/seeds
      need an expert review, and every seed feed URL needs verifying, before the first
      real research run.
- [ ] Add `OPENROUTER_API_KEY` to repo Actions secrets (blocks `research.yml`).
- [x] Research engine: custom Python agent on OpenRouter (OpenAI-compatible), LLM boxed
      to research + extraction. See DESIGN §2.
- [x] Wiki generator: **Kiso** (`build/okf/` derived bundle via `scripts/project`;
      timelines/indexes/feed generated pre-build).
- [ ] Backfill cutoff for newly tracked entities — starter is `backfill_months: 18`.
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
- [x] `taxonomy.yaml` — starter content (needs the domain pass in §0).
- [x] `kb/` first example event + entities (Prithvi) to pin the format.
- [x] Flesh out **Commands** in `AGENTS.md`.
- [x] Branch protection on `main` (require `lint` + `test`).

## 2. Knowledge-base tooling — `scripts/`

- [x] `scripts/kb.py` — read-only loaders (events, entities, taxonomy, site config).
- [x] `scripts/validate.py` — schema + `kind`/`theme` checks + slug/date consistency +
      dangling entity refs + no-`[[wikilink]]` + append-only immutability vs `origin/main`.
- [x] `scripts/project.py` — `kb/` → `build/okf/` (timelines, `index.md`, `log.md`,
      theme pages) + `build/feed.xml` (Atom). Verified against `kiso-cli check`/`build`.
- [x] Wire into `validate.yml` (+ `kiso check`) and `publish.yml`.
- [ ] Enforce sourcing rules: `kb/sources/` excerpt length cap. (no-media guard is in
      pre-commit; `.kiso` config already ignores `sources/**` from the built site.)
- [ ] Pydantic models for event/entity frontmatter (currently dataclasses in `kb.py`).
- [ ] Date-grouped `events/` index pages if Kiso's nav strains on a large flat tree.

## 3. Research agent — `agent/`  (needs `OPENROUTER_API_KEY`)

- [x] `uv add openai httpx feedparser pydantic`.
- [x] `agent/schema.py` — pydantic `Candidate` / `EventDraft` / `EntityMention` /
      `SourceRef` / `Budget`.
- [x] `agent/llm.py` — OpenRouter client (`openai` SDK, base_url), model from
      `taxonomy.yaml`, `response_format` structured JSON output. Forces the primary
      source URL and normalises `themes` to taxonomy ids in code (defence in depth —
      both failure modes showed up in live testing; don't just trust the prompt).
- [x] `agent/store.py` — append-only writers on top of `scripts/kb.py`; slug/id
      helpers; refuses to overwrite an existing entity page (events disambiguate with
      a `-2` suffix instead, since a same-day title collision is a legitimate case,
      not a bug).
- [x] `agent/discover.py` — poll seed feeds (feedparser over an httpx-fetched body, so
      fetches are bounded and testable) → hard-filter on exclude-terms + search
      window → dedupe against kb/ and across feeds → deterministic score →
      `agent/candidates.json`.
- [x] `agent/research.py` — per top candidate within budget: fetch, extract via
      `agent.llm`, resolve/create entities, write. No live web search yet (TODO below).
- [x] `agent/run.py` — orchestrate; budget from `$PLANETAI_DEPTH` or
      `depth_default`; writes `run-summary.md` + `pr-title.txt` for the PR.
- [x] `.github/workflows/research.yml` — daily cron + `workflow_dispatch` (depth
      choice); opens a PR via `peter-evans/create-pull-request`.
- [x] Verified against live feeds + a real OpenRouter call (not just mocked tests) —
      see CHANGELOG.
- [ ] Supplemental web search to fill gaps beyond the seed feeds (OpenRouter `web`
      plugin, or Tavily/Brave) — discovery is feed-only for now.
- [ ] Optional `PLANETAI_PR_TOKEN` secret (fine-grained PAT: Contents + Pull requests
      write on this repo) so the agent's own PRs trigger `ci`/`validate` automatically
      — GITHUB_TOKEN-authored PRs don't trigger `pull_request` workflows (GitHub's
      anti-recursion rule). Without it, PRs still open; checks need a manual re-run.
- [ ] Cost telemetry — `Budget.max_usd` is currently informational only, not metered
      against actual OpenRouter token usage.
- [ ] `agent/prompts/` — system prompt embedding AGENTS.md §2a + Copyright rules.
- [ ] Tests with recorded fixtures — no live API in CI.
- [ ] Job-openings aggregator (periodic `kind: job-openings` event).

## 4. Workflows — `.github/workflows/`

- [x] Pages enabled; `publish.yml` = validate → project → `kiso build` → genui → deploy.
- [x] `validate.yml` — `scripts/validate` + `scripts/project` + `kiso check` on PRs.
- [x] `research.yml` — `schedule` + `workflow_dispatch` (depth input);
      `uv run python -m agent.run`; `peter-evans/create-pull-request`. Secret:
      `OPENROUTER_API_KEY`; optional `PLANETAI_PR_TOKEN` (see §3).
- [ ] Add `validate` to branch-protection required checks (once it has run once).

## 5. Wiki build

- [x] Kiso integration via `oak-invest/kiso` action; `.kiso/configuration.yaml`.
- [x] `feed.xml` (Atom) of recent events (`scripts/project`).
- [ ] Branding — Kiso ships a default DaisyUI theme + its own favicon; decide how much
      to customise (theme name, logo, colours).
- [ ] Add `<link rel="alternate" type="application/atom+xml">` to pages if feasible.
- [ ] Keep the SSG fallback (MkDocs/Quartz/Astro from `build/okf/`) documented.

## 6. Generative UI front page — `genui/`

- [x] Deterministic stats (`scripts/frontpage.py` → `build/frontpage.json`): windowed
      recent events, per-theme activity + trend, new entities, job-openings snapshot.
- [x] Deterministic layout + accent selection (`genui/select.py`, pure function,
      unit-tested) — HEADLINE / DIGEST / QUIET, four theme accent colours.
- [x] LLM copy pass via OpenRouter (`genui/copy.py`, strict JSON, `anthropic/claude-haiku-4-5`
      default) with deterministic fallback copy on any failure.
- [x] Jinja2 layouts (`genui/layouts/`) + `genui/build.py` orchestration, wired into
      `publish.yml` after the Kiso build.
- [ ] `THEME_SPOTLIGHT` layout mode, once real theme-activity patterns are visible.
- [ ] Tune `HEADLINE_SCORE_GAP` and the lead-story score formula against real data.

## 7. Hardening / later

- [ ] Tune discovery scoring from `candidates.json` history.
- [ ] Cost telemetry per run; alert if over budget.
- [ ] Entity merge/alias tooling.
- [ ] "AI-generated, PR-reviewed" disclosure + corrections/takedown link on every page.
- [ ] Evaluate multi-agent workers (Haiku) for extraction at scale.
- [ ] Make the repo cleanly forkable for other topic areas (docs + template).
