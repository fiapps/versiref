"""Tests for the bible_ref module."""

import pytest
from versiref.bible_ref import BibleRef, SimpleBibleRef, VerseRange
from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification


def test_verse_range_initialization() -> None:
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


def test_verse_range_is_valid() -> None:
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


def test_verse_range_is_valid_with_subverses() -> None:
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


def test_simple_bible_ref() -> None:
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


def test_simple_bible_ref_for_range() -> None:
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


def test_simple_bible_ref_is_valid() -> None:
    """Test the is_valid method of SimpleBibleRef."""
    # Create a versification
    versification = Versification.named("eng")

    # Valid whole book reference
    ref = SimpleBibleRef("GEN")
    assert ref.is_valid(versification) is True

    # Invalid book
    ref = SimpleBibleRef("XYZ")
    assert ref.is_valid(versification) is False

    # Valid single verse
    ref = SimpleBibleRef.for_range("JHN", 3, 16)
    assert ref.is_valid(versification) is True

    # Valid verse range
    ref = SimpleBibleRef.for_range("PSA", 119, 1, end_verse=176)
    assert ref.is_valid(versification) is True

    # Valid with plural form of PSA
    ref = SimpleBibleRef(
        "PSAS", [VerseRange(18, 7, "", 18, 7, ""), VerseRange(77, 18, "", 77, 18, "")]
    )
    assert ref.is_valid(versification) is True

    # Valid chapter range
    ref = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=66)
    assert ref.is_valid(versification) is True

    # Valid "ff" notation
    ref = SimpleBibleRef.for_range("ROM", 8, 28, end_chapter=8, end_verse=-1)
    assert ref.is_valid(versification) is True

    # Invalid chapter
    ref = SimpleBibleRef.for_range("JHN", 30, 1, end_verse=10)
    assert ref.is_valid(versification) is False

    # Invalid verse (exceeds chapter limit)
    ref = SimpleBibleRef.for_range("JHN", 3, 40, end_verse=50)
    assert ref.is_valid(versification) is False

    # Invalid verse range (start verse exceeds chapter limit)
    ref = SimpleBibleRef.for_range("JHN", 3, 40, end_chapter=3, end_verse=-1)
    assert ref.is_valid(versification) is False

    # Invalid verse range structure (end verse before start verse)
    ref = SimpleBibleRef.for_range("JHN", 3, 40, end_verse=10)
    assert ref.is_valid(versification) is False


def test_simple_bible_ref_is_whole_chapters() -> None:
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


def test_format_simple_reference() -> None:
    """Test formatting a simple Bible reference."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a reference for Genesis 1:1-5
    ref = SimpleBibleRef.for_range("GEN", 1, 1, end_verse=5)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Gen 1:1–5"


def test_format_whole_book() -> None:
    """Test formatting a whole book reference."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a whole book reference
    ref = SimpleBibleRef(book_id="GEN")

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Gen"


def test_format_multiple_ranges() -> None:
    """Test formatting a reference with multiple verse ranges."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

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


def test_format_multiple_chapters() -> None:
    """Test formatting a reference spanning multiple chapters."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

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


def test_format_with_subverses() -> None:
    """Test formatting a reference with subverses."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a reference for Mark 5:3b-5a
    ref = SimpleBibleRef.for_range(
        "MRK", 5, 3, start_subverse="b", end_verse=5, end_subverse="a"
    )

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Mark 5:3b–5a"


def test_format_cross_chapter_range() -> None:
    """Test formatting a reference that spans across chapters."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a reference for John 7:53-8:11 (the pericope adulterae)
    ref = SimpleBibleRef.for_range("JHN", 7, 53, end_chapter=8, end_verse=11)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "John 7:53–8:11"


def test_format_whole_chapter_range() -> None:
    """Test formatting a reference that spans multiple whole chapters."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a reference for Isaiah 1-39
    ref = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=39)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Isa 1–39"


def test_format_ff_reference() -> None:
    """Test formatting a reference with 'ff' notation."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a reference for Philippians 2:5ff
    # Unspecified end verse means "ff"
    ref = SimpleBibleRef.for_range("PHP", 2, 5, end_chapter=2, end_verse=-1)

    # Format the reference
    formatted = ref.format(style)
    assert formatted == "Phil 2:5ff"


def test_format_with_custom_style() -> None:
    """Test formatting with a custom style."""
    # Create a custom style
    names = {"GEN": "Genesi", "EXO": "Esodo"}
    style = RefStyle(
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


def test_format_unknown_book() -> None:
    """Test formatting with an unknown book ID."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a reference with an unknown book ID
    ref = SimpleBibleRef(book_id="XYZ")

    # Formatting should raise a ValueError
    with pytest.raises(ValueError):
        ref.format(style)


def test_format_single_chapter_book_with_versification() -> None:
    """Test formatting a reference to a single-chapter book with versification."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification where Philemon (PHM) is a single-chapter book
    versification = Versification.named("eng")

    # Create a reference for Philemon 6
    ref = SimpleBibleRef.for_range("PHM", 1, 6)

    # Format with versification - should omit chapter number
    formatted = ref.format(style, versification)
    assert formatted == "Phlm 6"

    # Format without versification - should include chapter number
    formatted_without_versification = ref.format(style)
    assert formatted_without_versification == "Phlm 1:6"


def test_format_single_chapter_book_verse_range() -> None:
    """Test formatting a verse range in a single-chapter book."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a reference for Jude 3-5
    ref = SimpleBibleRef.for_range("JUD", 1, 3, end_verse=5)

    # Format with versification
    formatted = ref.format(style, versification)
    assert formatted == "Jude 3–5"


def test_resolve_following_verses() -> None:
    """Test resolving ff ranges to definite references."""
    # Create a style and versification.
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)
    versification = Versification.named("eng")

    ref1 = SimpleBibleRef.for_range("MAT", 12, 46, end_verse=-1)
    ref1.resolve_following_verses(versification)
    assert ref1.format(style, versification) == "Matt 12:46–50"

    vr1 = VerseRange(
        start_chapter=8,
        start_verse=48,
        start_subverse="",
        end_chapter=8,
        end_verse=-1,
        end_subverse="",
    )
    vr2 = VerseRange(
        start_chapter=10,
        start_verse=22,
        start_subverse="",
        end_chapter=10,
        end_verse=-1,
        end_subverse="",
    )
    ref2 = SimpleBibleRef("JHN", [vr1, vr2])
    ref2.resolve_following_verses(versification)
    assert ref2.format(style, versification) == "John 8:48–59; 10:22–42"


def test_bible_ref_initialization() -> None:
    """Test that BibleRef initializes correctly."""
    # Empty initialization
    ref = BibleRef()
    assert ref.simple_refs == []
    assert ref.versification is None
    assert ref.original_text is None

    # With versification
    versification = Versification.named("eng")
    ref = BibleRef(versification=versification)
    assert ref.simple_refs == []
    assert ref.versification is versification
    assert ref.original_text is None

    # With simple refs
    simple_ref = SimpleBibleRef.for_range("JHN", 3, 16)
    ref = BibleRef(simple_refs=[simple_ref], versification=versification)
    assert len(ref.simple_refs) == 1
    assert ref.simple_refs[0] == simple_ref
    assert ref.versification is versification
    assert ref.original_text is None

    # With original text
    ref = BibleRef(
        simple_refs=[simple_ref], versification=versification, original_text="John 3:16"
    )
    assert ref.original_text == "John 3:16"


def test_bible_ref_for_range() -> None:
    """Test the for_range class method of BibleRef."""
    versification = Versification.named("eng")

    # Basic usage
    ref = BibleRef.for_range("JHN", 3, 16, versification=versification)
    assert len(ref.simple_refs) == 1
    assert ref.simple_refs[0].book_id == "JHN"
    assert len(ref.simple_refs[0].ranges) == 1
    assert ref.simple_refs[0].ranges[0].start_chapter == 3
    assert ref.simple_refs[0].ranges[0].start_verse == 16
    assert ref.simple_refs[0].ranges[0].end_chapter == 3
    assert ref.simple_refs[0].ranges[0].end_verse == 16
    assert ref.versification is versification
    assert ref.original_text is None

    # With original text
    ref = BibleRef.for_range(
        "JHN", 3, 16, original_text="John 3:16", versification=versification
    )
    assert ref.original_text == "John 3:16"
    assert ref.simple_refs[0].original_text == "John 3:16"

    # With range
    ref = BibleRef.for_range("ROM", 8, 28, end_verse=39, versification=versification)
    assert len(ref.simple_refs) == 1
    assert ref.simple_refs[0].book_id == "ROM"
    assert len(ref.simple_refs[0].ranges) == 1
    assert ref.simple_refs[0].ranges[0].start_chapter == 8
    assert ref.simple_refs[0].ranges[0].start_verse == 28
    assert ref.simple_refs[0].ranges[0].end_chapter == 8
    assert ref.simple_refs[0].ranges[0].end_verse == 39
    assert ref.versification is versification

    # Cross-chapter reference
    ref = BibleRef.for_range(
        "JHN", 7, 53, end_chapter=8, end_verse=11, versification=versification
    )
    assert len(ref.simple_refs) == 1
    assert ref.simple_refs[0].book_id == "JHN"
    assert len(ref.simple_refs[0].ranges) == 1
    assert ref.simple_refs[0].ranges[0].start_chapter == 7
    assert ref.simple_refs[0].ranges[0].start_verse == 53
    assert ref.simple_refs[0].ranges[0].end_chapter == 8
    assert ref.simple_refs[0].ranges[0].end_verse == 11
    assert ref.versification is versification


def test_bible_ref_is_whole_books() -> None:
    """Test the is_whole_books method of BibleRef."""
    versification = Versification.named("eng")

    # Empty BibleRef is vacuously whole books
    ref = BibleRef(versification=versification)
    assert ref.is_whole_books() is True

    # Single whole book reference
    simple_ref = SimpleBibleRef("GEN")
    ref = BibleRef(simple_refs=[simple_ref], versification=versification)
    assert ref.is_whole_books() is True

    # Multiple whole book references
    simple_ref1 = SimpleBibleRef("GEN")
    simple_ref2 = SimpleBibleRef("EXO")
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.is_whole_books() is True

    # Mixed whole book and verse references
    simple_ref1 = SimpleBibleRef("GEN")
    simple_ref2 = SimpleBibleRef.for_range("JHN", 3, 16)
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.is_whole_books() is False

    # Only verse references
    ref = BibleRef.for_range("JHN", 3, 16, versification=versification)
    assert ref.is_whole_books() is False


def test_bible_ref_is_whole_chapters() -> None:
    """Test the is_whole_chapters method of BibleRef."""
    versification = Versification.named("eng")

    # Empty BibleRef is vacuously whole chapters
    ref = BibleRef(versification=versification)
    assert ref.is_whole_chapters() is True

    # Whole book reference is whole chapters
    simple_ref = SimpleBibleRef("GEN")
    ref = BibleRef(simple_refs=[simple_ref], versification=versification)
    assert ref.is_whole_chapters() is True

    # Chapter reference is whole chapters
    ref = BibleRef.for_range("JHN", 6, -1, versification=versification)
    assert ref.is_whole_chapters() is True

    # Chapter range is whole chapters
    ref = BibleRef.for_range("ISA", 1, -1, end_chapter=39, versification=versification)
    assert ref.is_whole_chapters() is True

    # Multiple whole chapter references
    simple_ref1 = SimpleBibleRef("GEN")
    simple_ref2 = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=39)
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.is_whole_chapters() is True

    # Mixed whole chapter and verse references
    simple_ref1 = SimpleBibleRef.for_range("ISA", 1, -1, end_chapter=39)
    simple_ref2 = SimpleBibleRef.for_range("JHN", 3, 16)
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.is_whole_chapters() is False

    # Only verse references
    ref = BibleRef.for_range("JHN", 3, 16, versification=versification)
    assert ref.is_whole_chapters() is False


def test_bible_ref_is_valid() -> None:
    """Test the is_valid method of BibleRef."""
    versification = Versification.named("eng")

    # Empty BibleRef is vacuously valid
    ref = BibleRef(versification=versification)
    assert ref.is_valid() is True

    # Valid reference with versification
    ref = BibleRef.for_range("JHN", 3, 16, versification=versification)
    assert ref.is_valid() is True

    # Invalid reference with versification
    ref = BibleRef.for_range(
        "JHN", 30, 1, versification=versification
    )  # Chapter 30 doesn't exist
    assert ref.is_valid() is False

    # Multiple valid references
    simple_ref1 = SimpleBibleRef.for_range("JHN", 3, 16)
    simple_ref2 = SimpleBibleRef.for_range("ROM", 8, 28)
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.is_valid() is True

    # Mixed valid and invalid references
    simple_ref1 = SimpleBibleRef.for_range("JHN", 3, 16)
    simple_ref2 = SimpleBibleRef.for_range("JHN", 30, 1)  # Invalid chapter
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.is_valid() is False

    # Reference without versification
    ref = BibleRef.for_range("JHN", 3, 16, versification=None)
    assert ref.is_valid() is False


def test_bible_ref_range_refs() -> None:
    """Test the range_refs method of BibleRef."""
    versification = Versification.named("eng")

    # Empty BibleRef yields nothing
    ref = BibleRef(versification=versification)
    assert list(ref.range_refs()) == []

    # Single reference with single range
    ref = BibleRef.for_range(
        "JHN", 3, 16, original_text="John 3:16", versification=versification
    )
    range_refs = list(ref.range_refs())
    assert len(range_refs) == 1
    assert isinstance(range_refs[0], BibleRef)
    assert range_refs[0].simple_refs[0].book_id == "JHN"
    assert range_refs[0].simple_refs[0].ranges[0].start_chapter == 3
    assert range_refs[0].simple_refs[0].ranges[0].start_verse == 16
    assert range_refs[0].versification is versification
    assert range_refs[0].original_text == "John 3:16"

    # Single reference with multiple ranges
    vr1 = VerseRange(3, 16, "", 3, 16, "", original_text="John 3:16")
    vr2 = VerseRange(3, 18, "", 3, 20, "", original_text="18-20")
    simple_ref = SimpleBibleRef("JHN", [vr1, vr2])
    ref = BibleRef(
        simple_refs=[simple_ref],
        versification=versification,
        original_text="John 3:16, 18-20",
    )
    range_refs = list(ref.range_refs())
    assert len(range_refs) == 2
    assert all(isinstance(r, BibleRef) for r in range_refs)
    assert range_refs[0].simple_refs[0].book_id == "JHN"
    assert range_refs[0].simple_refs[0].ranges[0].start_verse == 16
    assert range_refs[0].original_text == "John 3:16"
    assert range_refs[1].simple_refs[0].book_id == "JHN"
    assert range_refs[1].simple_refs[0].ranges[0].start_verse == 18
    assert range_refs[1].original_text == "18-20"

    # Multiple references with multiple ranges
    vr1 = VerseRange(3, 16, "", 3, 16, "")
    vr2 = VerseRange(3, 18, "", 3, 20, "")
    simple_ref1 = SimpleBibleRef("JHN", [vr1, vr2])
    vr3 = VerseRange(8, 28, "", 8, 39, "")
    simple_ref2 = SimpleBibleRef("ROM", [vr3])
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    range_refs = list(ref.range_refs())
    assert len(range_refs) == 3
    assert all(isinstance(r, BibleRef) for r in range_refs)
    assert range_refs[0].simple_refs[0].book_id == "JHN"
    assert range_refs[0].simple_refs[0].ranges[0].start_verse == 16
    assert range_refs[1].simple_refs[0].book_id == "JHN"
    assert range_refs[1].simple_refs[0].ranges[0].start_verse == 18
    assert range_refs[2].simple_refs[0].book_id == "ROM"
    assert range_refs[2].simple_refs[0].ranges[0].start_verse == 28


def test_bible_ref_format() -> None:
    """Test the format method of BibleRef."""
    versification = Versification.named("eng")
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Empty BibleRef formats to empty string
    ref = BibleRef(versification=versification)
    assert ref.format(style) == ""

    # Single reference
    ref = BibleRef.for_range("JHN", 3, 16, versification=versification)
    assert ref.format(style) == "John 3:16"

    # Multiple references
    simple_ref1 = SimpleBibleRef.for_range("JHN", 3, 16)
    simple_ref2 = SimpleBibleRef.for_range("ROM", 8, 28, end_verse=39)
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.format(style) == "John 3:16; Rom 8:28–39"

    # Reference with single-chapter book
    ref = BibleRef.for_range("PHM", 1, 6, versification=versification)
    assert ref.format(style) == "Phlm 6"

    # Complex reference with multiple ranges
    vr1 = VerseRange(3, 16, "", 3, 16, "")
    vr2 = VerseRange(3, 18, "", 3, 20, "")
    simple_ref1 = SimpleBibleRef("JHN", [vr1, vr2])
    vr3 = VerseRange(8, 28, "", 8, 39, "")
    simple_ref2 = SimpleBibleRef("ROM", [vr3])
    ref = BibleRef(simple_refs=[simple_ref1, simple_ref2], versification=versification)
    assert ref.format(style) == "John 3:16, 18–20; Rom 8:28–39"

    # Custom style
    custom_style = RefStyle(
        names={"JHN": "Giovanni", "ROM": "Romani"},
        chapter_verse_separator=",",
        range_separator="-",
        verse_range_separator="; ",
        chapter_separator=" e ",
    )
    assert ref.format(custom_style) == "Giovanni 3,16; 18-20 e Romani 8,28-39"
