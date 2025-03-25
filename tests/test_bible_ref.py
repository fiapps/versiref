"""
Tests for the bible_ref module.
"""

import pytest
from versiref.bible_ref import SimpleBibleRef, VerseRange
from versiref.style import Style


def test_verse_range_initialization():
    """Test that VerseRange initializes correctly."""
    # Simple case: just a single verse
    vr = VerseRange(3, 16, "", 3, 16, "")
    assert vr.start_chapter == 3
    assert vr.start_verse == 16
    assert vr.end_chapter == 3
    assert vr.end_verse == 16
    assert vr.start_sub_verse == ""
    assert vr.end_sub_verse == ""
    assert vr.original_text is None
    
    # Complex case: full range with sub-verses
    vr = VerseRange(1, 2, "a", 3, 4, "b", "1:2a-3:4b")
    assert vr.start_chapter == 1
    assert vr.start_verse == 2
    assert vr.start_sub_verse == "a"
    assert vr.end_chapter == 3
    assert vr.end_verse == 4
    assert vr.end_sub_verse == "b"
    assert vr.original_text == "1:2a-3:4b"


def test_simple_bible_ref():
    """Test that SimpleBibleRef initializes correctly."""
    # Reference to entire book
    ref = SimpleBibleRef("JHN")
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 0
    assert ref.is_whole_book() is True
    
    # Reference with a single verse range
    ref = SimpleBibleRef(
        "JHN", 
        [VerseRange(3, 16, "", 3, 16, "", original_text="3:16")]
    )
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 3
    assert ref.ranges[0].start_verse == 16
    assert ref.ranges[0].end_chapter == 3
    assert ref.ranges[0].end_verse == 16
    assert ref.is_whole_book() is False
    
    # Reference with multiple verse ranges
    ref = SimpleBibleRef(
        "ROM", 
        [
            VerseRange(1, 1, "", 1, 5, "", "1:1-5"),
            VerseRange(3, 23, "", 3, 24, "", "3:23-24"),
            VerseRange(5, 8, "", 5, 8, "", "5:8")
        ],
        "Rom."
    )
    assert ref.book_id == "ROM"
    assert len(ref.ranges) == 3
    assert ref.original_text == "Rom."


def test_format_simple_reference():
    """Test formatting a simple Bible reference."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a reference for Genesis 1:1-5
    vr = VerseRange(
        start_chapter=1,
        start_verse=1,
        start_sub_verse="",
        end_chapter=1,
        end_verse=5,
        end_sub_verse="",
    )
    ref = SimpleBibleRef(book_id="GEN", ranges=[vr])
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Gen 1:1–5"


def test_format_whole_book():
    """Test formatting a whole book reference."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a whole book reference
    ref = SimpleBibleRef(book_id="GEN")
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Gen"


def test_format_multiple_ranges():
    """Test formatting a reference with multiple verse ranges."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a reference for John 3:16, 18-20
    vr1 = VerseRange(
        start_chapter=3,
        start_verse=16,
        start_sub_verse="",
        end_chapter=3,
        end_verse=16,
        end_sub_verse="",
    )
    vr2 = VerseRange(
        start_chapter=3,
        start_verse=18,
        start_sub_verse="",
        end_chapter=3,
        end_verse=20,
        end_sub_verse="",
    )
    ref = SimpleBibleRef(book_id="JHN", ranges=[vr1, vr2])
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "John 3:16, 18–20"


def test_format_multiple_chapters():
    """Test formatting a reference spanning multiple chapters."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a reference for Romans 1:18-32; 2:1-5
    vr1 = VerseRange(
        start_chapter=1,
        start_verse=18,
        start_sub_verse="",
        end_chapter=1,
        end_verse=32,
        end_sub_verse="",
    )
    vr2 = VerseRange(
        start_chapter=2,
        start_verse=1,
        start_sub_verse="",
        end_chapter=2,
        end_verse=5,
        end_sub_verse="",
    )
    ref = SimpleBibleRef(book_id="ROM", ranges=[vr1, vr2])
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Rom 1:18–32; 2:1–5"


def test_format_with_subverses():
    """Test formatting a reference with subverses."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a reference for Mark 5:3b-5a
    vr = VerseRange(
        start_chapter=5,
        start_verse=3,
        start_sub_verse="b",
        end_chapter=5,
        end_verse=5,
        end_sub_verse="a",
    )
    ref = SimpleBibleRef(book_id="MRK", ranges=[vr])
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Mark 5:3b–5a"


def test_format_cross_chapter_range():
    """Test formatting a reference that spans across chapters."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a reference for John 7:53-8:11 (the pericope adulterae)
    vr = VerseRange(
        start_chapter=7,
        start_verse=53,
        start_sub_verse="",
        end_chapter=8,
        end_verse=11,
        end_sub_verse="",
    )
    ref = SimpleBibleRef(book_id="JHN", ranges=[vr])
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "John 7:53–8:11"


def test_format_with_custom_style():
    """Test formatting with a custom style."""
    # Create a custom style
    names = {"GEN": "Genesi", "EXO": "Esodo"}
    style = Style(
        names=names,
        chapter_verse_separator=", ",
        range_separator="-",  # Use hyphen instead of en dash
        verse_range_separator=".",
        chapter_separator="; ",
    )
    
    # Create a reference for Genesis 1:1-5
    vr1 = VerseRange(
        start_chapter=1,
        start_verse=1,
        start_sub_verse="",
        end_chapter=1,
        end_verse=5,
        end_sub_verse="",
    )
    vr2 = VerseRange(
        start_chapter=1,
        start_verse=8,
        start_sub_verse="b",
        end_chapter=1,
        end_verse=10,
        end_sub_verse="a",
    )
    ref = SimpleBibleRef(book_id="GEN", ranges=[vr1, vr2])
    
    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Genesi 1, 1-5.8b-10a"


def test_format_unknown_book():
    """Test formatting with an unknown book ID."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a reference with an unknown book ID
    ref = SimpleBibleRef(book_id="XYZ")
    
    # Formatting should raise a ValueError
    with pytest.raises(ValueError):
        ref.format(style)
