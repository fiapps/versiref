"""Tests for the versiref command-line interface."""

from pathlib import Path

from click.testing import CliRunner

from versiref.cli import main


def test_docs_prints_bundled_directory() -> None:
    """`versiref docs` prints a real path to the bundled docs directory."""
    result = CliRunner().invoke(main, ["docs"])
    assert result.exit_code == 0
    path = Path(result.output.strip())
    assert path.is_dir()
    assert (path / "cli.md").is_file()


def test_docs_prints_single_file() -> None:
    """`versiref docs cli.md` prints the path to that bundled file."""
    result = CliRunner().invoke(main, ["docs", "cli.md"])
    assert result.exit_code == 0
    assert Path(result.output.strip()).is_file()


def test_docs_unknown_file_errors() -> None:
    """An unknown doc name exits non-zero with an error message."""
    result = CliRunner().invoke(main, ["docs", "nope.md"])
    assert result.exit_code != 0
    assert "no such doc" in result.output
