"""
Tests for the bible_ref module.
"""

import pytest
from versiref.bible_ref import SimpleBibleRef, VerseRange


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
