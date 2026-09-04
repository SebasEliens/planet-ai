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
- GitHub Pages enabled (Actions build type) and `.github/workflows/publish.yml` — the
  deploy path (`configure-pages` → `upload-pages-artifact` → `deploy-pages`) is live
  with a **placeholder** front page (`genui/shell.html` + `genui/build.py`). The build
  step becomes validate → project → wiki build → genui once those land.

### Notes
- Prior art surveyed: `langchain-ai/openwiki`, `oak-invest/kiso`,
  `GoogleCloudPlatform/knowledge-catalog` (OKF), `scaccogatto/okf-skills`,
  `github/gh-aw`, `jordan-gibbs/hyperresearch`, `nvk/llm-wiki`.
- Estimated operating cost: ~$70–120/month at daily-standard cadence (public repo).

[Unreleased]: https://github.com/SebasEliens/planet-ai/commits/main
