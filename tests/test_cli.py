"""Tests for the versiref command-line interface."""

import json
from pathlib import Path

from click.testing import CliRunner

from versiref.cli import main


def test_list_versifications_includes_known() -> None:
    """`versiref list versifications` lists bundled schemes."""
    result = CliRunner().invoke(main, ["list", "versifications"])
    assert result.exit_code == 0
    names = result.output.split()
    assert {"eng", "lxx", "org", "vulgata"} <= set(names)


def test_list_styles_pattern_filters() -> None:
    """The --pattern glob restricts the listed styles."""
    result = CliRunner().invoke(main, ["list", "styles", "--pattern", "en-*"])
    assert result.exit_code == 0
    assert result.output.strip()
    assert all(line.startswith("en-") for line in result.output.split())


def test_parse_normalizes() -> None:
    """`parse` prints the reference reformatted in the output style."""
    result = CliRunner().invoke(main, ["parse", "Gen 1:1", "--style", "en-sbl"])
    assert result.exit_code == 0
    assert result.output.strip() == "Gen 1:1"


def test_parse_json_structure() -> None:
    """`parse --json` emits the structured book/range breakdown."""
    result = CliRunner().invoke(
        main, ["parse", "Jn 3:16-18", "--style", "en-cmos_short", "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["books"][0]["book"] == "JHN"
    rng = data["books"][0]["ranges"][0]
    assert rng["start"]["verse"] == 16
    assert rng["end"]["verse"] == 18


def test_parse_unparseable_exits_2() -> None:
    """An unparseable reference exits with code 2."""
    result = CliRunner().invoke(main, ["parse", "Florble 9:9", "--style", "en-sbl"])
    assert result.exit_code == 2


def test_validate_valid() -> None:
    """A reference within range validates and exits 0."""
    result = CliRunner().invoke(
        main, ["validate", "Gen 1:31", "--style", "en-sbl", "-v", "eng"]
    )
    assert result.exit_code == 0


def test_validate_out_of_range_exits_1() -> None:
    """A parseable but out-of-range reference exits 1."""
    result = CliRunner().invoke(
        main, ["validate", "Gen 1:99", "--style", "en-sbl", "-v", "eng"]
    )
    assert result.exit_code == 1


def test_validate_unparseable_exits_2() -> None:
    """An unparseable reference exits 2."""
    result = CliRunner().invoke(
        main, ["validate", "nonsense", "--style", "en-sbl", "-v", "eng"]
    )
    assert result.exit_code == 2


def test_convert_maps_psalm_numbering() -> None:
    """Converting a Psalm from LXX to English applies the numbering shift."""
    result = CliRunner().invoke(
        main,
        ["convert", "Ps 50:3", "--style", "en-sbl", "--from", "lxx", "--to", "eng"],
    )
    assert result.exit_code == 0
    assert result.output.strip() == "Ps 51:1"


def test_convert_unmappable_exits_1() -> None:
    """A verse with no counterpart in the target exits 1."""
    result = CliRunner().invoke(
        main,
        ["convert", "Gen 1:99", "--style", "en-sbl", "--from", "eng", "--to", "lxx"],
    )
    assert result.exit_code == 1


def test_scan_finds_references() -> None:
    """`scan` reports each reference found in stdin with its offsets."""
    result = CliRunner().invoke(
        main,
        ["scan", "--style", "en-sbl", "--json"],
        input="See Gen 1:1 and Rom 8:28 today.\n",
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    books = [m["reference"]["books"][0]["book"] for m in data["matches"]]
    assert books == ["GEN", "ROM"]


def test_unknown_style_is_clean_error() -> None:
    """An unknown style name reports a click error, not a traceback."""
    result = CliRunner().invoke(main, ["parse", "Gen 1:1", "--style", "nope"])
    assert result.exit_code == 2
    assert "unknown style" in result.output


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
