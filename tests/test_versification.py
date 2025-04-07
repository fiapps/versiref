import pytest  # noqa: F401
from versiref.versification import Versification


def test_empty_versification():
    """Test that an empty Versification returns 99 for any book and chapter."""
    v = Versification()
    assert v.last_verse("XYZ", 1) == 99
    assert v.last_verse("GEN", 100) == 99
    assert v.last_verse("REV", 0) == 99


def test_standard_versification_eng():
    """Test loading the English standard versification."""
    v = Versification.standard_versification("eng")
    assert v is not None
    assert v.identifier == "eng"

    # Test specific known verse counts
    assert v.last_verse("GEN", 1) == 31  # Genesis 1 has 31 verses
    assert v.last_verse("GEN", 3) == 24  # Genesis 3 has 24 verses
    assert v.last_verse("PSA", 119) == 176  # Psalm 119 has 176 verses
    assert v.last_verse("JHN", 3) == 36  # John 3 has 36 verses
    assert v.last_verse("REV", 22) == 21  # Revelation 22 has 21 verses


def test_nonexistent_standard_versification():
    """Test that requesting a nonexistent versification returns None."""
    v = Versification.standard_versification("nonexistent")
    assert v is None


def test_last_verse_nonexistent_book():
    """Test that requesting a nonexistent book returns -1."""
    v = Versification.standard_versification("eng")
    assert v.last_verse("XYZ", 1) == -1


def test_last_verse_nonexistent_chapter():
    """Test that requesting a nonexistent chapter returns -1."""
    v = Versification.standard_versification("eng")
    assert v.last_verse("GEN", 100) == -1
    assert v.last_verse("GEN", -1) == -1


def test_from_file():
    """Test loading a versification from a file."""
    # Get the path to one of the standard versification files
    from importlib import resources

    path = resources.files("versiref").joinpath("data", "versifications", "eng.json")

    v = Versification.from_file(str(path), "test-eng")
    assert v is not None
    assert v.identifier == "test-eng"
    assert v.last_verse("GEN", 1) == 31


def test_multiple_versifications():
    """Test loading and comparing multiple versifications."""
    eng = Versification.standard_versification("eng")
    lxx = Versification.standard_versification("lxx")
    vul = Versification.standard_versification("vulgata")

    assert eng is not None
    assert lxx is not None
    assert vul is not None

    # Test a verse count that might differ between versifications
    # (This is just an example - actual values may vary)
    eng_psa_9 = eng.last_verse("PSA", 9)
    lxx_psa_9 = lxx.last_verse("PSA", 9)

    # Just verify we can get values, not testing specific differences
    assert isinstance(eng_psa_9, int)
    assert isinstance(lxx_psa_9, int)


def test_is_single_chapter():
    """Test ."""
    v = Versification.standard_versification("eng")
    assert v.is_single_chapter("GEN") is False
    assert v.is_single_chapter("PSAS") is False
    assert v.is_single_chapter("2JN") is True


def test_includes():
    """Test checking if a book is included in the versification."""
    v = Versification.standard_versification("eng")
    assert v.includes("GEN") is True
    assert v.includes("PSA") is True
    assert v.includes("PSAS") is True
    assert v.includes("XYZ") is False  # Nonexistent book
    assert v.includes("REV") is True
