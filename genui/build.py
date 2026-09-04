"""Front-page build.

Currently a **placeholder**: renders a static "coming soon" page into
``site/index.html`` from the layout shell, so the GitHub Pages deploy path is live
and green. The real generative build — a recent-events briefing composed from the
projected event log — lands later (see TODO.md §6).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

REPO_URL = "https://github.com/SebasEliens/planet-ai"
SHELL = Path(__file__).parent / "shell.html"
OUT = Path("site/index.html")

PLACEHOLDER = f"""\
    <p><strong>The knowledge base is being set up.</strong> Soon this page will show
    the most recent developments — papers, project launches and updates, reports,
    funding, policy and legal moves, and open roles — each linking into the wiki.</p>
    <p>Until then:</p>
    <ul>
      <li><a href="{REPO_URL}/blob/main/docs/DESIGN.md">Design doc</a> — how the agent,
          event store, and wiki fit together</li>
      <li><a href="{REPO_URL}/blob/main/TODO.md">Roadmap</a></li>
      <li><a href="{REPO_URL}">Repository</a></li>
    </ul>
"""


def render(shell: str, content: str, built: str) -> str:
    return (
        shell.replace("__CONTENT__", content)
        .replace("__BUILT__", built)
        .replace("__REPO__", REPO_URL)
    )


def main() -> None:
    built = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    html = render(SHELL.read_text(encoding="utf-8"), PLACEHOLDER, built)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
