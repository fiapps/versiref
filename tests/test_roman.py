"""Tests for Roman numeral conversion."""

import pytest
from versiref.roman import int_to_roman, roman_to_int


@pytest.mark.parametrize(
    "n,numeral",
    [
        (1, "I"),
        (4, "IV"),
        (9, "IX"),
        (14, "XIV"),
        (40, "XL"),
        (44, "XLIV"),
        (90, "XC"),
        (150, "CL"),
        (176, "CLXXVI"),
        (199, "CXCIX"),
        (200, "CC"),
    ],
)
def test_int_to_roman(n: int, numeral: str) -> None:
    """Test conversion of integers to Roman numerals."""
    assert int_to_roman(n) == numeral


def test_round_trip() -> None:
    """Test that every chapter-sized number survives a round trip."""
    for n in range(1, 201):
        assert roman_to_int(int_to_roman(n)) == n


def test_roman_to_int_additive() -> None:
    """Test that pre-modern additive forms are accepted."""
    assert roman_to_int("IIII") == 4
    assert roman_to_int("XXXX") == 40
    assert roman_to_int("LXXXXVIIII") == 99


def test_roman_to_int_lowercase() -> None:
    """Test that lowercase numerals are accepted."""
    assert roman_to_int("xliv") == 44
    assert roman_to_int("cxcix") == 199


def test_roman_to_int_invalid() -> None:
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError):
        roman_to_int("")
    with pytest.raises(ValueError):
        roman_to_int("XIVA")


def test_int_to_roman_invalid() -> None:
    """Test that non-positive input raises ValueError."""
    with pytest.raises(ValueError):
        int_to_roman(0)
    with pytest.raises(ValueError):
        int_to_roman(-7)
