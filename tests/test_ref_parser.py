"""Tests for the ref_parser module."""

import pytest  # noqa: F401
from typing import Optional
from versiref.bible_ref import BibleRef
from versiref.ref_parser import RefParser
from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification


def test_parse_simple_verse() -> None:
    """Test parsing a simple verse reference."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a simple reference: "Gen 1:1"
    ref = parser.parse_simple("Gen 1:1")

    assert ref is not None
    assert ref.book_id == "GEN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 1
    assert ref.ranges[0].start_verse == 1
    assert ref.ranges[0].start_subverse == ""
    assert ref.ranges[0].end_chapter == 1
    assert ref.ranges[0].end_verse == 1
    assert ref.ranges[0].end_subverse == ""
    assert ref.ranges[0].original_text == "Gen 1:1"


def test_parse_verse_with_subverse() -> None:
    """Test parsing a verse reference with a subverse."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a reference with a subverse: "John 3:16b"
    ref = parser.parse_simple("John 3:16b")

    assert ref is not None
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 3
    assert ref.ranges[0].start_verse == 16
    assert ref.ranges[0].start_subverse == "b"
    assert ref.ranges[0].end_chapter == 3
    assert ref.ranges[0].end_verse == 16
    assert ref.ranges[0].end_subverse == "b"
    assert ref.ranges[0].original_text == "John 3:16b"


def test_parse_single_chapter_book() -> None:
    """Test parsing a reference to a verse in a single-chapter book."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification with Jude as a single-chapter book
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a reference to a verse in Jude: "Jude 5"
    ref = parser.parse_simple("Jude 5")

    assert ref is not None
    assert ref.book_id == "JUD"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 1  # Single-chapter books have chapter 1
    assert ref.ranges[0].start_verse == 5
    assert ref.ranges[0].end_chapter == 1
    assert ref.ranges[0].end_verse == 5
    assert ref.ranges[0].original_text == "Jude 5"


def test_parse_nonexistent_reference() -> None:
    """Test parsing a string that is not a Bible reference."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Try to parse a non-reference
    ref = parser.parse_simple("This is not a Bible reference")

    assert ref is None


def test_parse_book_with_space() -> None:
    """Test parsing a book name that contains a space."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a reference with a space in the book name: "2 John 5"
    ref = parser.parse_simple("2 John 5")

    assert ref is not None
    assert ref.book_id == "2JN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 1  # Single-chapter books have chapter 1
    assert ref.ranges[0].start_verse == 5
    assert ref.ranges[0].original_text == "2 John 5"


def test_parse_multi_chapter_book_with_space() -> None:
    """Test parsing a multi-chapter book name that contains a space."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a reference with a space in the book name: "1 Kgs 8:10"
    ref = parser.parse_simple("1 Kgs 8:10")

    assert ref is not None
    assert ref.book_id == "1KI"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 8
    assert ref.ranges[0].start_verse == 10
    assert ref.ranges[0].original_text == "1 Kgs 8:10"


def test_parse_multiple_books() -> None:
    """Test parsing a reference that spans multiple books."""
    # Create a style
    names = standard_names("en-cmos_short")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a reference with multiple books: "Is 7:10-14; Lk 1:26-38"
    ref = parser.parse("Is 7:10-14; Lk 1:26-38")

    assert ref is not None
    assert len(ref.simple_refs) == 2

    # Check first book (Isaiah)
    assert ref.simple_refs[0].book_id == "ISA"
    assert len(ref.simple_refs[0].ranges) == 1
    assert ref.simple_refs[0].ranges[0].start_chapter == 7
    assert ref.simple_refs[0].ranges[0].start_verse == 10
    assert ref.simple_refs[0].ranges[0].end_chapter == 7
    assert ref.simple_refs[0].ranges[0].end_verse == 14

    # Check second book (Luke)
    assert ref.simple_refs[1].book_id == "LUK"
    assert len(ref.simple_refs[1].ranges) == 1
    assert ref.simple_refs[1].ranges[0].start_chapter == 1
    assert ref.simple_refs[1].ranges[0].start_verse == 26
    assert ref.simple_refs[1].ranges[0].end_chapter == 1
    assert ref.simple_refs[1].ranges[0].end_verse == 38


def test_parse_multiple_books_with_multiple_ranges() -> None:
    """Test parsing a reference with multiple books and multiple verse ranges."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a complex reference: "Matt 5:3-12; 6:9-13; 1 John 3:16-17"
    ref = parser.parse("Matt 5:3-12; 6:9-13; 1 John 3:16-17")

    assert ref is not None
    assert len(ref.simple_refs) == 2

    # Check first book (Matthew)
    assert ref.simple_refs[0].book_id == "MAT"
    assert len(ref.simple_refs[0].ranges) == 2
    # First range in Matthew
    assert ref.simple_refs[0].ranges[0].start_chapter == 5
    assert ref.simple_refs[0].ranges[0].start_verse == 3
    assert ref.simple_refs[0].ranges[0].end_chapter == 5
    assert ref.simple_refs[0].ranges[0].end_verse == 12
    # Second range in Matthew
    assert ref.simple_refs[0].ranges[1].start_chapter == 6
    assert ref.simple_refs[0].ranges[1].start_verse == 9
    assert ref.simple_refs[0].ranges[1].end_chapter == 6
    assert ref.simple_refs[0].ranges[1].end_verse == 13

    # Check second book (1 John)
    assert ref.simple_refs[1].book_id == "1JN"
    assert len(ref.simple_refs[1].ranges) == 1
    assert ref.simple_refs[1].ranges[0].start_chapter == 3
    assert ref.simple_refs[1].ranges[0].start_verse == 16
    assert ref.simple_refs[1].ranges[0].end_chapter == 3
    assert ref.simple_refs[1].ranges[0].end_verse == 17


def test_parse_nonexistent_multi_book_reference() -> None:
    """Test parsing a string that is not a valid multi-book Bible reference."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Try to parse a non-reference
    ref = parser.parse("This is not a Bible reference")

    assert ref is None


def test_scan_string() -> None:
    """Test scanning a string for Bible references."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Scan a string with multiple references
    text = "Look at Matt 5:3-12 and John 3:16 for important teachings."
    refs = list(parser.scan_string(text))

    assert len(refs) == 2

    # Check first reference (Matthew)
    ref1, start1, end1 = refs[0]
    assert ref1.simple_refs[0].book_id == "MAT"
    assert len(ref1.simple_refs[0].ranges) == 1
    assert ref1.simple_refs[0].ranges[0].start_chapter == 5
    assert ref1.simple_refs[0].ranges[0].start_verse == 3
    assert ref1.simple_refs[0].ranges[0].end_chapter == 5
    assert ref1.simple_refs[0].ranges[0].end_verse == 12
    assert text[start1:end1] == "Matt 5:3-12"

    # Check second reference (John)
    ref2, start2, end2 = refs[1]
    assert ref2.simple_refs[0].book_id == "JHN"
    assert len(ref2.simple_refs[0].ranges) == 1
    assert ref2.simple_refs[0].ranges[0].start_chapter == 3
    assert ref2.simple_refs[0].ranges[0].start_verse == 16
    assert ref2.simple_refs[0].ranges[0].end_chapter == 3
    assert ref2.simple_refs[0].ranges[0].end_verse == 16
    assert text[start2:end2] == "John 3:16"


def test_scan_string_with_multi_book_reference() -> None:
    """Test scanning a string for multi-book Bible references."""
    # Create a style
    names = standard_names("en-cmos_short")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Scan a string with a multi-book reference
    text = "The prophecy in Is 7:10-14; Lk 1:26-38 is important."
    refs = list(parser.scan_string(text))

    assert len(refs) == 1

    ref, start, end = refs[0]
    assert len(ref.simple_refs) == 2

    # Check first book (Isaiah)
    assert ref.simple_refs[0].book_id == "ISA"
    assert len(ref.simple_refs[0].ranges) == 1
    assert ref.simple_refs[0].ranges[0].start_chapter == 7
    assert ref.simple_refs[0].ranges[0].start_verse == 10
    assert ref.simple_refs[0].ranges[0].end_chapter == 7
    assert ref.simple_refs[0].ranges[0].end_verse == 14

    # Check second book (Luke)
    assert ref.simple_refs[1].book_id == "LUK"
    assert len(ref.simple_refs[1].ranges) == 1
    assert ref.simple_refs[1].ranges[0].start_chapter == 1
    assert ref.simple_refs[1].ranges[0].start_verse == 26
    assert ref.simple_refs[1].ranges[0].end_chapter == 1
    assert ref.simple_refs[1].ranges[0].end_verse == 38

    assert text[start:end] == "Is 7:10-14; Lk 1:26-38"


def test_sub_refs() -> None:
    """Test using sub_refs to normalize references to SBL style."""
    # Create a style for parsing (CMOS)
    cmos_names = standard_names("en-cmos_short")
    cmos_style = RefStyle(names=cmos_names)

    # Create a style for formatting (SBL)
    sbl_names = standard_names("en-sbl_abbreviations")
    sbl_style = RefStyle(names=sbl_names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(cmos_style, versification)

    # Define a callback function to normalize references
    def normalize_ref(ref: BibleRef) -> Optional[str]:
        return ref.format(sbl_style)

    # Test text with multiple references
    text = "See Is 7:10-14; Lk 1:26-38 and Jn 1:1-5, 14 for more."
    result = parser.sub_refs(text, normalize_ref)

    # The references should be normalized to SBL style
    expected = "See Isa 7:10–14; Luke 1:26–38 and John 1:1–5, 14 for more."
    assert result == expected
