"""The placeholder front-page build produces a valid-looking index.html."""

from pathlib import Path

import pytest

from genui import build


def test_render_fills_all_placeholders() -> None:
    html = build.render(
        shell="<x>__CONTENT__ __BUILT__ __REPO__</x>", content="C", built="2026-01-02"
    )
    assert "__CONTENT__" not in html
    assert "__BUILT__" not in html
    assert "__REPO__" not in html
    assert "C" in html
    assert "2026-01-02" in html


def test_main_writes_site_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    build.main()
    out = tmp_path / "site" / "index.html"
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "<title>PlanetAI</title>" in text
    for marker in ("__CONTENT__", "__BUILT__", "__REPO__"):
        assert marker not in text
