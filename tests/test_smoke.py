"""Placeholder so the test suite is green before real code lands."""


def test_imports() -> None:
    import agent
    import genui
    import scripts

    assert agent.__doc__ and genui.__doc__ and scripts.__doc__
