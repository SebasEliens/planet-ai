"""`scripts.validate` accepts the committed kb/ and flags obvious breakage."""

from scripts import validate


def test_repo_kb_is_valid() -> None:
    assert validate.main() == 0


def test_wikilink_regex() -> None:
    assert validate.WIKILINK.search("see [[foo-bar]] here")
    assert not validate.WIKILINK.search("see [foo](bar.md) here")
