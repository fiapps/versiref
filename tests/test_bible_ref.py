"""
Tests for the bible_ref module.
"""

import pytest
from versiref.bible_ref import SimpleBibleRef, VerseRange
from versiref.style import Style
from versiref.versification import Versification


def test_verse_range_initialization():
    """Test that VerseRange initializes correctly."""
    # Simple case: just a single verse
    vr = VerseRange(3, 16, "", 3, 16, "")
    assert vr.start_chapter == 3
    assert vr.start_verse == 16
    assert vr.end_chapter == 3
    assert vr.end_verse == 16
    assert vr.start_subverse == ""
    assert vr.end_subverse == ""
    assert vr.original_text is None

    # Complex case: full range with subverses
    vr = VerseRange(1, 2, "a", 3, 4, "b", "1:2a-3:4b")
    assert vr.start_chapter == 1
    assert vr.start_verse == 2
    assert vr.start_subverse == "a"
    assert vr.end_chapter == 3
    assert vr.end_verse == 4
    assert vr.end_subverse == "b"
    assert vr.original_text == "1:2a-3:4b"


def test_verse_range_is_valid():
    """Test the is_valid method of VerseRange."""
    # Valid ranges
    assert (
        VerseRange(1, 1, "", 1, 5, "").is_valid() is True
    )  # Simple range in same chapter
    assert VerseRange(1, -1, "", 1, -1, "").is_valid() is True  # Whole chapter
    assert VerseRange(1, -1, "", 3, -1, "").is_valid() is True  # Multiple chapters
    assert VerseRange(1, 1, "", 2, 3, "").is_valid() is True  # Cross-chapter range
    assert (
        VerseRange(1, 5, "", 1, -1, "").is_valid() is True
    )  # "ff" notation in same chapter

    # Invalid ranges
    assert (
        VerseRange(1, 5, "", 2, -1, "").is_valid() is False
    )  # "ff" notation across chapters
    assert (
        VerseRange(1, -1, "", 1, 5, "").is_valid() is False
    )  # Unspecified start, specified end
    assert VerseRange(1, 5, "", 1, 3, "").is_valid() is False  # Start verse > end verse
    assert (
        VerseRange(2, 1, "", 1, 5, "").is_valid() is False
    )  # Start chapter > end chapter


def test_verse_range_is_valid_with_subverses():
    """Test the is_valid method with subverses."""
    # Subverses don't affect validity checks
    assert (
        VerseRange(1, 1, "a", 1, 1, "b").is_valid() is True
    )  # Same verse, different subverses
    assert (
        VerseRange(1, 5, "c", 1, -1, "").is_valid() is True
    )  # "ff" notation with subverse

    # Invalid ranges with subverses
    assert (
        VerseRange(2, 1, "a", 1, 5, "b").is_valid() is False
    )  # Start chapter > end chapter
    assert (
        VerseRange(1, 5, "a", 1, 3, "b").is_valid() is False
    )  # Start verse > end verse


def test_simple_bible_ref():
    """Test that SimpleBibleRef initializes correctly."""
    # Reference to entire book
    ref = SimpleBibleRef("JHN")
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 0
    assert ref.is_whole_book() is True

    # Reference with a single verse range
    ref = SimpleBibleRef(
        "JHN", [VerseRange(3, 16, "", 3, 16, "", original_text="3:16")]
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
            VerseRange(5, 8, "", 5, 8, "", "5:8"),
        ],
        "Rom.",
    )
    assert ref.book_id == "ROM"
    assert len(ref.ranges) == 3
    assert ref.original_text == "Rom."


def test_simple_bible_ref_for_range():
    """Test the for_range class method of SimpleBibleRef."""
    # Basic usage with just book, chapter, and verse
    ref1 = SimpleBibleRef.for_range("JHN", 3, 16)
    assert ref1.book_id == "JHN"
    assert len(ref1.ranges) == 1
    assert ref1.ranges[0].start_chapter == 3
    assert ref1.ranges[0].start_verse == 16
    assert ref1.ranges[0].end_chapter == 3
    assert ref1.ranges[0].end_verse == 16
    assert ref1.ranges[0].start_subverse == ""
    assert ref1.ranges[0].end_subverse == ""

    # With end verse specified
    ref2 = SimpleBibleRef.for_range("ROM", 8, 28, end_verse=39)
    assert ref2.book_id == "ROM"
    assert len(ref2.ranges) == 1
    assert ref2.ranges[0].start_chapter == 8
    assert ref2.ranges[0].start_verse == 28
    assert ref2.ranges[0].end_chapter == 8
    assert ref2.ranges[0].end_verse == 39

    # Cross-chapter reference
    ref3 = SimpleBibleRef.for_range("JHN", 7, 53, end_chapter=8, end_verse=11)
    assert ref3.book_id == "JHN"
    assert len(ref3.ranges) == 1
    assert ref3.ranges[0].start_chapter == 7
    assert ref3.ranges[0].start_verse == 53
    assert ref3.ranges[0].end_chapter == 8
    assert ref3.ranges[0].end_verse == 11

    # With subverses
    ref4 = SimpleBibleRef.for_range(
        "MRK", 5, 3, end_verse=5, start_subverse="b", end_subverse="a"
    )
    assert ref4.book_id == "MRK"
    assert len(ref4.ranges) == 1
    assert ref4.ranges[0].start_chapter == 5
    assert ref4.ranges[0].start_verse == 3
    assert ref4.ranges[0].start_subverse == "b"
    assert ref4.ranges[0].end_chapter == 5
    assert ref4.ranges[0].end_verse == 5
    assert ref4.ranges[0].end_subverse == "a"

    # With original text
    ref5 = SimpleBibleRef.for_range("PSA", 23, 1, original_text="Psalm 23:1")
    assert ref5.book_id == "PSA"
    assert ref5.original_text == "Psalm 23:1"
    assert ref5.ranges[0].original_text == "Psalm 23:1"


def test_simple_bible_ref_is_valid():
    """Test the is_valid method of SimpleBibleRef."""
    # Create a versification
    versification = Versification.standard_versification("eng")

    # Valid whole book reference
    ref = SimpleBibleRef("GEN")
    assert ref.is_valid(versification) == True

    # Invalid book
    ref = SimpleBibleRef("XYZ")
    assert ref.is_valid(versification) == False

    # Valid single verse
    ref = SimpleBibleRef.for_range("JHN", 3, 16)
    assert ref.is_valid(versification) == True

    # Valid verse range
    ref = SimpleBibleRef.for_range("PSA", 119, 1, end_verse=176)
    assert ref.is_valid(versification) == True

    # Valid with plural form of PSA
    ref = SimpleBibleRef(
        "PSAS", [VerseRange(18, 7, "", 18, 7, ""), VerseRange(77, 18, "", 77, 18, "")]
    )
    assert ref.is_valid(versification) == True

    # Valid chapter range
    ref = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=66)
    assert ref.is_valid(versification) == True

    # Valid "ff" notation
    ref = SimpleBibleRef.for_range("ROM", 8, 28, end_chapter=8, end_verse=-1)
    assert ref.is_valid(versification) == True

    # Invalid chapter
    ref = SimpleBibleRef.for_range("JHN", 30, 1, end_verse=10)
    assert ref.is_valid(versification) == False

    # Invalid verse (exceeds chapter limit)
    ref = SimpleBibleRef.for_range("JHN", 3, 40, end_verse=50)
    assert ref.is_valid(versification) == False

    # Invalid verse range (start verse exceeds chapter limit)
    ref = SimpleBibleRef.for_range("JHN", 3, 40, end_chapter=3, end_verse=-1)
    assert ref.is_valid(versification) == False

    # Invalid verse range structure (end verse before start verse)
    ref = SimpleBibleRef.for_range("JHN", 3, 40, end_verse=10)
    assert ref.is_valid(versification) == False


def test_simple_bible_ref_is_whole_chapters():
    """Test the is_whole_chapters method of SimpleBibleRef."""
    # Whole book reference should be considered whole chapters
    ref1 = SimpleBibleRef("JHN")
    assert ref1.is_whole_chapters() is True

    # Chapter reference without verse specification should be whole chapters
    ref2 = SimpleBibleRef.for_range("JHN", 6, -1)
    assert ref2.is_whole_chapters() is True

    # Chapter range without verse specification should be whole chapters
    ref3 = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=39)
    assert ref3.is_whole_chapters() is True

    # Reference with verse specification should not be whole chapters
    ref4 = SimpleBibleRef.for_range("JHN", 3, 16)
    assert ref4.is_whole_chapters() is False

    # Reference with verse range should not be whole chapters
    ref5 = SimpleBibleRef.for_range("ROM", 8, 28, end_verse=39)
    assert ref5.is_whole_chapters() is False

    # Reference with chapter range but specific verses should not be whole chapters
    ref6 = SimpleBibleRef.for_range("PSA", 1, 1, end_chapter=2, end_verse=12)
    assert ref6.is_whole_chapters() is False

    # Mixed reference with both whole chapter and specific verses should not be whole chapters
    ref7 = SimpleBibleRef(
        "MAT",
        [
            VerseRange(5, -1, "", 5, -1, ""),  # Whole chapter
            VerseRange(6, 9, "", 6, 13, ""),  # Specific verses
        ],
    )
    assert ref7.is_whole_chapters() is False


def test_format_simple_reference():
    """Test formatting a simple Bible reference."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)

    # Create a reference for Genesis 1:1-5
    ref = SimpleBibleRef.for_range("GEN", 1, 1, end_verse=5)

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
        start_subverse="",
        end_chapter=3,
        end_verse=16,
        end_subverse="",
    )
    vr2 = VerseRange(
        start_chapter=3,
        start_verse=18,
        start_subverse="",
        end_chapter=3,
        end_verse=20,
        end_subverse="",
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
        start_subverse="",
        end_chapter=1,
        end_verse=32,
        end_subverse="",
    )
    vr2 = VerseRange(
        start_chapter=2,
        start_verse=1,
        start_subverse="",
        end_chapter=2,
        end_verse=5,
        end_subverse="",
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
    ref = SimpleBibleRef.for_range(
        "MRK", 5, 3, start_subverse="b", end_verse=5, end_subverse="a"
    )

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Mark 5:3b–5a"


def test_format_cross_chapter_range():
    """Test formatting a reference that spans across chapters."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)

    # Create a reference for John 7:53-8:11 (the pericope adulterae)
    ref = SimpleBibleRef.for_range("JHN", 7, 53, end_chapter=8, end_verse=11)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "John 7:53–8:11"


def test_format_whole_chapter_range():
    """Test formatting a reference that spans multiple whole chapters."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)

    # Create a reference for Isaiah 1-39
    ref = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=39)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Isa 1–39"


def test_format_ff_reference():
    """Test formatting a reference with 'ff' notation."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)

    # Create a reference for Philippians 2:5ff
    # Unspecified end verse means "ff"
    ref = SimpleBibleRef.for_range("PHP", 2, 5, end_chapter=2, end_verse=-1)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Phil 2:5ff"


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
        start_subverse="",
        end_chapter=1,
        end_verse=5,
        end_subverse="",
    )
    vr2 = VerseRange(
        start_chapter=1,
        start_verse=8,
        start_subverse="b",
        end_chapter=1,
        end_verse=10,
        end_subverse="a",
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


def test_format_single_chapter_book_with_versification():
    """Test formatting a reference to a single-chapter book with versification."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)

    # Create a versification where Philemon (PHM) is a single-chapter book
    versification = Versification.standard_versification("eng")

    # Create a reference for Philemon 6
    ref = SimpleBibleRef.for_range("PHM", 1, 6)

    # Format with versification - should omit chapter number
    formatted = ref.format(style, versification)
    assert formatted == "Phlm 6"

    # Format without versification - should include chapter number
    formatted_without_versification = ref.format(style)
    assert formatted_without_versification == "Phlm 1:6"


def test_format_single_chapter_book_verse_range():
    """Test formatting a verse range in a single-chapter book."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)

    # Create a versification
    versification = Versification.standard_versification("eng")

    # Create a reference for Jude 3-5
    ref = SimpleBibleRef.for_range("JUD", 1, 3, end_verse=5)

    # Format with versification
    formatted = ref.format(style, versification)
    assert formatted == "Jude 3–5"
