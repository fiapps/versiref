"""
Tests for the RefStyle class.
"""

import pytest  # noqa: F401
from versiref.ref_style import RefStyle


def test_standard_names_abbreviations():
    """Test loading standard abbreviations."""
    names = RefStyle.standard_names("en-sbl_abbreviations")
    assert names is not None
    assert names["DEU"] == "Deut"
    assert names["1PE"] == "1 Pet"
    assert names["2MA"] == "2 Macc"


def test_standard_names_full_names():
    """Test loading standard full names."""
    names = RefStyle.standard_names("en-sbl_names")
    assert names is not None
    assert names["1MA"] == "1 Maccabees"
    assert names["GEN"] == "Genesis"
    assert names["2TI"] == "2 Timothy"


def test_standard_names_nonexistent():
    """Test that loading a nonexistent names file returns None."""
    names = RefStyle.standard_names("nonexistent-file")
    assert names is None


def test_style_initialization():
    """Test that a RefStyle can be initialized with standard names."""
    names = RefStyle.standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)
    assert style.names["GEN"] == "Gen"
    assert style.recognized_names["Gen"] == "GEN"
