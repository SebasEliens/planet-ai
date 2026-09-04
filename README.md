# PlanetAI

**Live site:** https://sebaseliens.github.io/planet-ai/

An autonomous **deep-research agent** that maintains a public, append-only
**event knowledge base** on AI for climate justice, human rights, and a livable
planet — and publishes it as a browsable **wiki** on GitHub Pages.

- **What it tracks:** dated, sourced facts — papers, project launches and updates,
  reports, funding, policy and legal moves, datasets/benchmarks, notable news, and
  periodic job-opening snapshots.
- **How it works:** a scheduled GitHub Actions agent discovers in-scope events, verifies
  them against sources, and opens a pull request appending immutable event records in
  [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog).
  On merge, a deterministic build renders the wiki and an AI-generated front page.
- **Design:** [docs/DESIGN.md](docs/DESIGN.md) · **Agent rules:** [AGENTS.md](AGENTS.md)
  · **Roadmap:** [TODO.md](TODO.md)

> Status: **early setup**. Wiki build (Kiso), the generative front page, and Pages
> deploy are live; the research agent isn't wired in yet — see [TODO.md](TODO.md).

## Development

Requires [`uv`](https://docs.astral.sh/uv/) and Python 3.13.

```bash
uv sync                       # create .venv and install dev tooling
uv run pre-commit install     # enable git hooks

uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy                   # type-check
uv run pytest                 # tests
```

## Licensing

- **Code:** MIT — see [LICENSE](LICENSE).
- **Knowledge-base content** (summaries, entity prose): CC BY 4.0 — see
  [LICENSE-content](LICENSE-content). Facts and links are not claimed; each cited
  source remains under its own rights. See [docs/DESIGN.md](docs/DESIGN.md) →
  *Legal & licensing*.

Pages are AI-generated and PR-reviewed; corrections are handled by appending to the
record, never rewriting it.
