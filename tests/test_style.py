"""Tests for the RefStyle class."""

import json
import tempfile
from pathlib import Path

import pytest
from versiref.ref_style import RefStyle, available_standard_names, standard_names


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


def test_from_dict_with_base() -> None:
    """Test from_dict with base inherits names and separators from the base style."""
    base = RefStyle.named("en-sbl")
    style = RefStyle.from_dict({"base": "en-sbl"})
    assert style.names == base.names
    assert style.chapter_verse_separator == base.chapter_verse_separator
    assert style.identifier is None


def test_from_dict_with_base_override() -> None:
    """Test from_dict with base applies separator overrides."""
    style = RefStyle.from_dict(
        {"base": "en-sbl", "chapter_verse_separator": ",", "range_separator": "-"}
    )
    assert style.names == RefStyle.named("en-sbl").names
    assert style.chapter_verse_separator == ","
    assert style.range_separator == "-"


def test_from_dict_with_base_and_also_recognize() -> None:
    """Test from_dict with base processes also_recognize."""
    style = RefStyle.from_dict({"base": "en-sbl", "also_recognize": ["en-sbl_names"]})
    assert style.recognized_names["Genesis"] == "GEN"
    assert style.recognized_names["Gen"] == "GEN"


def test_from_dict_base_and_names_raises() -> None:
    """Test from_dict raises ValueError when both base and names are present."""
    with pytest.raises(ValueError, match="both"):
        RefStyle.from_dict({"base": "en-sbl", "names": "en-sbl_abbreviations"})


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


def test_named_en_bibleworks() -> None:
    """Test loading the en-bibleworks standard style."""
    style = RefStyle.named("en-bibleworks")
    assert style.identifier == "en-bibleworks"
    assert style.recognized_names["Esg"] == "ESG"
    assert style.recognized_names["Tbs"] == "TOB"


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


# --- available_names / available_standard_names tests ---


def test_available_names_discovers_bundled_styles() -> None:
    """available_names() should expose the canonical bundled styles, sorted."""
    available = RefStyle.available_names()
    assert available
    assert available == sorted(available)
    assert {"en-sbl", "it-cei"}.issubset(available)


def test_available_names_round_trip_through_named() -> None:
    """Every identifier from available_names() must load via named()."""
    for ident in RefStyle.available_names():
        RefStyle.named(ident)


def test_available_names_filters_by_glob() -> None:
    """available_names() should restrict results to the given glob."""
    english = RefStyle.available_names("en-*")
    italian = RefStyle.available_names("it-*")
    assert english
    assert italian
    assert all(ident.startswith("en-") for ident in english)
    assert all(ident.startswith("it-") for ident in italian)
    assert set(english).isdisjoint(italian)


def test_available_names_glob_no_matches() -> None:
    """A glob that matches nothing should return an empty list."""
    assert RefStyle.available_names("xx-*") == []


def test_available_standard_names_discovers_bundled_files() -> None:
    """available_standard_names() should expose the canonical book-name sets, sorted."""
    available = available_standard_names()
    assert available
    assert available == sorted(available)
    assert {"en-sbl_abbreviations", "en-sbl_names", "it-cei_nomi"}.issubset(available)


def test_available_standard_names_round_trip() -> None:
    """Every identifier from available_standard_names() must load via standard_names()."""
    for ident in available_standard_names():
        standard_names(ident)


def test_available_standard_names_filters_by_glob() -> None:
    """available_standard_names() should restrict results to the given glob."""
    english = available_standard_names("en-*")
    italian = available_standard_names("it-*")
    assert english
    assert italian
    assert all(ident.startswith("en-") for ident in english)
    assert all(ident.startswith("it-") for ident in italian)
    assert set(english).isdisjoint(italian)


def test_available_standard_names_glob_no_matches() -> None:
    """A glob that matches nothing should return an empty list."""
    assert available_standard_names("xx-*") == []


def test_also_recognize_versifications_existing_wins() -> None:
    """also_recognize_versifications keeps existing entries on conflict."""
    style = RefStyle(names=standard_names("en-sbl_abbreviations"))
    style.also_recognize_versifications({"Vulg.": "vulgata"})
    style.also_recognize_versifications({"Vulg.": "nova_vulgata", "LXX": "lxx"})
    assert style.versification_identifiers == {"Vulg.": "vulgata", "LXX": "lxx"}


def test_from_dict_versification_identifiers_names_form() -> None:
    """from_dict reads a versification_identifiers block on a names-based style."""
    style = RefStyle.from_dict(
        {
            "names": "en-sbl_abbreviations",
            "versification_identifiers": {"Vulg.": "vulgata", "LXX": "lxx"},
        }
    )
    assert style.versification_identifiers == {"Vulg.": "vulgata", "LXX": "lxx"}


def test_from_dict_versification_identifiers_base_form() -> None:
    """from_dict reads a versification_identifiers block on a base-derived style."""
    style = RefStyle.from_dict(
        {
            "base": "en-sbl",
            "versification_identifiers": {"Vulg.": "vulgata"},
        }
    )
    assert style.versification_identifiers == {"Vulg.": "vulgata"}
