"""Task 1: CLI-Skelett – main() mit --help, importierbares __main__."""

import pytest


def test_help_exits_zero_and_prints_usage(capsys):
    from bloridium import cli

    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_main_returns_zero_without_args():
    from bloridium import cli

    assert cli.main([]) == 0


def test_module_main_importable():
    import bloridium.__main__  # noqa: F401
