"""Tests for the RefStyle class."""

import json
import tempfile
from pathlib import Path

import pytest
from versiref.ref_style import RefStyle, standard_names


def test_standard_names_abbreviations() -> None:
    """Test loading standard abbreviations."""
    names = standard_names("en-sbl_abbreviations")
    assert names is not None
    assert names["DEU"] == "Deut"
    assert names["1PE"] == "1 Pet"
    assert names["2MA"] == "2 Macc"


def test_standard_names_full_names() -> None:
    """Test loading standard full names."""
    names = standard_names("en-sbl_names")
    assert names is not None
    assert names["1MA"] == "1 Maccabees"
    assert names["GEN"] == "Genesis"
    assert names["2TI"] == "2 Timothy"


def test_standard_names_nonexistent() -> None:
    """Test that loading a nonexistent names file raises ValueError."""
    with pytest.raises(FileNotFoundError):
        standard_names("nonexistent-file")


def test_style_initialization() -> None:
    """Test that a RefStyle can be initialized with standard names."""
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)
    assert style.names["GEN"] == "Gen"
    assert style.recognized_names["Gen"] == "GEN"


# --- from_dict tests ---


def test_from_dict_with_string_names() -> None:
    """Test from_dict with a standard names identifier string."""
    style = RefStyle.from_dict({"names": "en-sbl_abbreviations"})
    assert style.names["GEN"] == "Gen"
    assert style.recognized_names["Gen"] == "GEN"


def test_from_dict_with_dict_names() -> None:
    """Test from_dict with an inline names dictionary."""
    style = RefStyle.from_dict({"names": {"GEN": "Genesis", "EXO": "Exodus"}})
    assert style.names["GEN"] == "Genesis"
    assert style.recognized_names["Genesis"] == "GEN"


def test_from_dict_with_separators() -> None:
    """Test from_dict applies separator overrides."""
    style = RefStyle.from_dict(
        {
            "names": "en-sbl_abbreviations",
            "chapter_verse_separator": ",",
            "range_separator": "-",
            "verse_range_separator": ". ",
            "chapter_separator": " / ",
        }
    )
    assert style.chapter_verse_separator == ","
    assert style.range_separator == "-"
    assert style.verse_range_separator == ". "
    assert style.chapter_separator == " / "


def test_from_dict_missing_names() -> None:
    """Test from_dict raises ValueError when names is missing."""
    with pytest.raises(ValueError, match="names"):
        RefStyle.from_dict({"chapter_verse_separator": ":"})


def test_from_dict_with_also_recognize_string() -> None:
    """Test from_dict processes also_recognize string entries."""
    style = RefStyle.from_dict(
        {
            "names": "en-sbl_abbreviations",
            "also_recognize": ["en-sbl_names"],
        }
    )
    assert style.recognized_names["Genesis"] == "GEN"


def test_from_dict_with_also_recognize_dict() -> None:
    """Test from_dict processes also_recognize dict entries."""
    style = RefStyle.from_dict(
        {
            "names": "en-sbl_abbreviations",
            "also_recognize": [{"Cant": "SNG", "Qoh": "ECC"}],
        }
    )
    assert style.recognized_names["Cant"] == "SNG"
    assert style.recognized_names["Qoh"] == "ECC"


def test_from_dict_with_also_recognize_mixed() -> None:
    """Test from_dict processes a mix of string and dict entries."""
    style = RefStyle.from_dict(
        {
            "names": "en-sbl_abbreviations",
            "also_recognize": [
                "en-sbl_names",
                {"Cant": "SNG"},
            ],
        }
    )
    assert style.recognized_names["Genesis"] == "GEN"
    assert style.recognized_names["Cant"] == "SNG"


# --- from_file tests ---


def test_from_file() -> None:
    """Test from_file loads a JSON file and creates a RefStyle."""
    data = {
        "names": "en-sbl_abbreviations",
        "chapter_verse_separator": ":",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        style = RefStyle.from_file(f.name, identifier="test-style")
    assert style.names["GEN"] == "Gen"
    assert style.identifier == "test-style"
    Path(f.name).unlink()


def test_from_file_without_identifier() -> None:
    """Test from_file without an identifier."""
    data = {"names": "en-sbl_abbreviations"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        style = RefStyle.from_file(f.name)
    assert style.identifier is None
    Path(f.name).unlink()


# --- identifier and __str__ tests ---


def test_identifier_default_none() -> None:
    """Test that identifier defaults to None."""
    style = RefStyle(names={"GEN": "Gen"})
    assert style.identifier is None


def test_str_with_identifier() -> None:
    """Test __str__ returns named form when identifier is set."""
    style = RefStyle(names={"GEN": "Gen"}, identifier="en-sbl")
    assert str(style) == 'RefStyle.named("en-sbl")'


def test_str_without_identifier() -> None:
    """Test __str__ returns default form when no identifier is set."""
    style = RefStyle(names={"GEN": "Gen"})
    result = str(style)
    assert "RefStyle.named" not in result


# --- named tests ---


def test_named_en_sbl() -> None:
    """Test loading the en-sbl standard style."""
    style = RefStyle.named("en-sbl")
    assert style.names["GEN"] == "Gen"
    assert style.identifier == "en-sbl"
    assert style.chapter_verse_separator == ":"
    assert style.recognized_names["Genesis"] == "GEN"
    assert style.recognized_names["Cant"] == "SNG"
    assert style.recognized_names["Qoheleth"] == "ECC"


def test_named_en_cmos_short() -> None:
    """Test loading the en-cmos_short standard style."""
    style = RefStyle.named("en-cmos_short")
    assert style.identifier == "en-cmos_short"
    assert style.recognized_names["Genesis"] == "GEN"
    assert style.recognized_names["Apocalypse"] == "REV"


def test_named_en_cmos_long() -> None:
    """Test loading the en-cmos_long standard style."""
    style = RefStyle.named("en-cmos_long")
    assert style.identifier == "en-cmos_long"
    assert style.recognized_names["Song of Solomon"] == "SNG"
    assert style.recognized_names["Apocalypse"] == "REV"


def test_named_it_cei() -> None:
    """Test loading the it-cei standard style."""
    style = RefStyle.named("it-cei")
    assert style.identifier == "it-cei"
    assert style.chapter_verse_separator == ","
    assert style.verse_range_separator == "."
    assert style.recognized_names["Genesi"] == "GEN"


def test_named_nonexistent() -> None:
    """Test that loading a nonexistent style raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        RefStyle.named("nonexistent-style")
