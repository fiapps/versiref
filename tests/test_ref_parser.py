"""Tests for the ref_parser module."""

import pytest  # noqa: F401
from versiref.bible_ref import BibleRef
from versiref.ref_parser import RefParser, Sensitivity
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
    ref = parser.parse_simple("This is not a Bible reference", silent=True)

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
    ref = parser.parse("This is not a Bible reference", silent=True)

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


def test_scan_ignores_book_name_glued_to_preceding_word() -> None:
    """A book name preceded by a letter is not a reference (e.g. "Rom" in "CongrRom")."""
    names = standard_names("en-cmos_short")
    style = RefStyle(names=names)
    versification = Versification.named("eng")
    parser = RefParser(style, versification)

    refs = list(parser.scan_string("in CongrRom 5:65-103"))
    assert refs == []


def test_scan_finds_book_name_at_word_boundary() -> None:
    """A book name at a word boundary is still found (companion to the glued case)."""
    names = standard_names("en-cmos_short")
    style = RefStyle(names=names)
    versification = Versification.named("eng")
    parser = RefParser(style, versification)

    refs = list(parser.scan_string("see Rom 5:1 now"))
    assert len(refs) == 1
    ref, start, end = refs[0]
    assert ref.simple_refs[0].book_id == "ROM"
    assert "see Rom 5:1 now"[start:end] == "Rom 5:1"


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
    def normalize_ref(ref: BibleRef) -> str | None:
        return ref.format(sbl_style)

    # Test text with multiple references
    text = "See Is 7:10-14; Lk 1:26-38 and Jn 1:1-5, 14 for more."
    result = parser.sub_refs(text, normalize_ref)

    # The references should be normalized to SBL style
    expected = "See Isa 7:10–14; Luke 1:26–38 and John 1:1–5, 14 for more."
    assert result == expected


# --- Whole-chapter and whole-book parsing ---


def _make_parser() -> RefParser:
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)
    versification = Versification.named("eng")
    return RefParser(style, versification)


def test_parse_whole_chapter() -> None:
    """Test parsing a whole-chapter reference like 'John 3'."""
    parser = _make_parser()
    ref = parser.parse_simple("John 3")

    assert ref is not None
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 3
    assert ref.ranges[0].start_verse == -1
    assert ref.ranges[0].end_chapter == 3
    assert ref.ranges[0].end_verse == -1
    assert ref.ranges[0].is_whole_chapters()


def test_parse_whole_chapter_range() -> None:
    """Test parsing a chapter range like 'John 3–5'."""
    parser = _make_parser()
    ref = parser.parse_simple("John 3–5")

    assert ref is not None
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 3
    assert ref.ranges[0].end_chapter == 5
    assert ref.ranges[0].is_whole_chapters()


def test_parse_whole_book() -> None:
    """Test parsing a whole-book reference like 'Genesis'."""
    names = standard_names("en-sbl_names")
    style = RefStyle(names=names)
    versification = Versification.named("eng")
    parser = RefParser(style, versification)
    ref = parser.parse_simple("Genesis")

    assert ref is not None
    assert ref.book_id == "GEN"
    assert ref.is_whole_book()
    assert len(ref.ranges) == 0


def test_parse_whole_book_abbreviation() -> None:
    """Test parsing a whole-book reference with an abbreviation."""
    parser = _make_parser()
    ref = parser.parse_simple("Gen")

    assert ref is not None
    assert ref.book_id == "GEN"
    assert ref.is_whole_book()
    assert len(ref.ranges) == 0


def test_parse_whole_book_bible_ref() -> None:
    """Test parsing a whole-book reference via parse()."""
    parser = _make_parser()
    ref = parser.parse("Gen")

    assert ref is not None
    assert len(ref.simple_refs) == 1
    assert ref.simple_refs[0].is_whole_book()
    assert ref.is_whole_books()


def test_verse_ref_still_preferred_over_chapter() -> None:
    """Ensure 'John 3:16' parses as a verse ref, not chapter 3 followed by junk."""
    parser = _make_parser()
    ref = parser.parse_simple("John 3:16")

    assert ref is not None
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_verse == 16
    assert ref.ranges[0].end_verse == 16


def test_single_chapter_book_still_parses_verse() -> None:
    """Ensure 'Jude 5' still parses as verse 5, not chapter 5."""
    parser = _make_parser()
    ref = parser.parse_simple("Jude 5")

    assert ref is not None
    assert ref.book_id == "JUD"
    assert ref.ranges[0].start_chapter == 1
    assert ref.ranges[0].start_verse == 5


# --- Sensitivity filtering ---


def test_scan_default_sensitivity_skips_chapters() -> None:
    """Default sensitivity (VERSE) should skip whole-chapter references."""
    parser = _make_parser()
    text = "See John 3 and Matt 5:3 for context."
    refs = list(parser.scan_string(text))

    assert len(refs) == 1
    ref, start, end = refs[0]
    assert text[start:end] == "Matt 5:3"


def test_scan_default_sensitivity_skips_books() -> None:
    """Default sensitivity (VERSE) should skip whole-book references."""
    parser = _make_parser()
    text = "Read Gen and then John 3:16."
    refs = list(parser.scan_string(text))

    assert len(refs) == 1
    ref, start, end = refs[0]
    assert text[start:end] == "John 3:16"


def test_scan_chapter_sensitivity() -> None:
    """CHAPTER sensitivity should report whole-chapter refs but not whole-book."""
    parser = _make_parser()
    text = "Read Gen and John 3 and Matt 5:3."
    refs = list(parser.scan_string(text, sensitivity=Sensitivity.CHAPTER))

    assert len(refs) == 2
    assert text[refs[0][1] : refs[0][2]] == "John 3"
    assert text[refs[1][1] : refs[1][2]] == "Matt 5:3"


def test_scan_book_sensitivity() -> None:
    """BOOK sensitivity should report everything."""
    parser = _make_parser()
    text = "Read Gen and John 3 and Matt 5:3."
    refs = list(parser.scan_string(text, sensitivity=Sensitivity.BOOK))

    assert len(refs) == 3


def test_scan_as_ranges_with_sensitivity() -> None:
    """as_ranges=True with VERSE sensitivity filters individual ranges."""
    parser = _make_parser()
    text = "See John 1:14 and John 3 and Rev 12 and Matt 5:3 here."
    refs = list(parser.scan_string(text, as_ranges=True, sensitivity=Sensitivity.VERSE))

    assert len(refs) == 2
    assert text[refs[0][1] : refs[0][2]] == "John 1:14"
    assert text[refs[1][1] : refs[1][2]] == "Matt 5:3"


def test_scan_as_ranges_filters_chapter_from_multi_range() -> None:
    """as_ranges=True filters chapter-only ranges from a multi-range ref."""
    parser = _make_parser()
    # "Matt 5:3-12; 6:9-13" is one BibleRef with two verse-level ranges.
    text = "See Matt 5:3-12; 6:9-13 here."
    refs = list(parser.scan_string(text, as_ranges=True, sensitivity=Sensitivity.VERSE))

    assert len(refs) == 2
    assert text[refs[0][1] : refs[0][2]] == "Matt 5:3-12"
    assert text[refs[1][1] : refs[1][2]] == "6:9-13"


def test_scan_mixed_ref_not_filtered_without_as_ranges() -> None:
    """A ref with both verse and chapter ranges passes VERSE since it's not all chapters."""
    parser = _make_parser()
    text = "See Matt 5:3-12; 6:9-13 here."
    refs = list(parser.scan_string(text, sensitivity=Sensitivity.VERSE))

    # is_whole_chapters() is False because the ranges specify verses
    assert len(refs) == 1


def test_sub_refs_with_sensitivity() -> None:
    """sub_refs should respect sensitivity."""
    parser = _make_parser()
    sbl_style = RefStyle(names=standard_names("en-sbl_abbreviations"))

    def normalize(ref: BibleRef) -> str | None:
        return ref.format(sbl_style)

    text = "See John 3 and Matt 5:3-12."
    # Default sensitivity: only verse-level refs get substituted
    result = parser.sub_refs(text, normalize)
    assert "John 3" in result  # untouched
    assert "Matt 5:3–12" in result  # normalized

    # CHAPTER sensitivity: chapter refs also get substituted
    result = parser.sub_refs(text, normalize, sensitivity=Sensitivity.CHAPTER)
    assert "John 3" in result  # still there (formatted same way)
    assert "Matt 5:3–12" in result


def _make_designator_parser() -> RefParser:
    """Return a parser recognizing LXX/Vulgate designators, defaulting to eng."""
    style = RefStyle(names=standard_names("en-sbl_abbreviations"))
    style.also_recognize_versifications(
        {"Vulg.": "vulgata", "Vulgate": "vulgata", "LXX": "lxx", "(LXX)": "lxx"}
    )
    return RefParser(style, Versification.named("eng"))


def test_designator_overrides_versification() -> None:
    """A trailing designator yields a BibleRef in the named versification."""
    parser = _make_designator_parser()
    ref = parser.parse("Dan 13:23 Vulg.")
    assert ref is not None
    assert ref.versification is not None
    assert ref.versification.identifier == "vulgata"
    assert ref.is_valid()
    assert ref.original_text == "Dan 13:23 Vulg."


def test_designated_ref_invalid_under_default() -> None:
    """The same ref without a designator is invalid under the eng default."""
    parser = _make_designator_parser()
    ref = parser.parse("Dan 13:23")
    assert ref is not None
    assert ref.versification is not None
    assert ref.versification.identifier == "eng"
    assert not ref.is_valid()


def test_designator_applies_to_whole_list() -> None:
    """A designator at the end of a multi-book list applies to every book."""
    parser = _make_designator_parser()
    ref = parser.parse("Gen 1:1; Dan 13:23 Vulg.")
    assert ref is not None
    assert ref.versification is not None
    assert ref.versification.identifier == "vulgata"
    assert len(ref.simple_refs) == 2


def test_designator_aliases_and_longest_match() -> None:
    """Aliases resolve, and 'Vulgate' is not parsed as 'Vulg.' plus 'ate'."""
    parser = _make_designator_parser()
    assert parser.parse("Esth 13 Vulgate").versification.identifier == "vulgata"
    assert parser.parse("Gen 1:1 (LXX)").versification.identifier == "lxx"
    assert parser.parse("Gen 1:1 LXX").versification.identifier == "lxx"


def test_no_designator_uses_default_versification() -> None:
    """Without a designator the parser default versification is used."""
    parser = _make_designator_parser()
    ref = parser.parse("Gen 1:1")
    assert ref is not None
    assert ref.versification.identifier == "eng"


def test_parse_simple_discards_designator() -> None:
    """parse_simple matches and discards a trailing designator."""
    parser = _make_designator_parser()
    ref = parser.parse_simple("Dan 13:23 Vulg.")
    assert ref is not None
    assert ref.book_id == "DAN"
    assert ref.original_text == "Dan 13:23"


def test_scan_string_includes_designator_in_span() -> None:
    """scan_string reports a span covering the designator and the right versification."""
    parser = _make_designator_parser()
    text = "see Dan 13:23 Vulg. here and Gen 1:1 too"
    refs = list(parser.scan_string(text))
    assert len(refs) == 2
    designated, start, end = refs[0]
    assert text[start:end] == "Dan 13:23 Vulg."
    assert designated.versification.identifier == "vulgata"
    plain, p_start, p_end = refs[1]
    assert text[p_start:p_end] == "Gen 1:1"
    assert plain.versification.identifier == "eng"


def test_scan_string_simple_excludes_designator() -> None:
    """scan_string_simple's span ends before the discarded designator."""
    parser = _make_designator_parser()
    text = "see Dan 13:23 Vulg. here"
    refs = list(parser.scan_string_simple(text))
    assert len(refs) == 1
    ref, start, end = refs[0]
    assert text[start:end] == "Dan 13:23"


def test_empty_designator_map_unchanged() -> None:
    """A style with no designators parses exactly as before."""
    parser = _make_parser()
    ref = parser.parse("Gen 1:1")
    assert ref is not None
    assert ref.versification.identifier == "eng"
    # A trailing word that is not a designator is not consumed.
    assert parser.parse("Gen 1:1 Vulg.", silent=True) is None


def _make_latin_marker_parser() -> RefParser:
    """Return a parser using Latin following-verse markers "seq."/"seqq.".

    These markers are longer than two characters and contain a ".", so the
    subverse rule cannot capture them; only the explicit marker branch can.
    """
    style = RefStyle(
        names=standard_names("en-sbl_abbreviations"),
        following_verse="seq.",
        following_verses="seqq.",
    )
    return RefParser(style, Versification.named("eng"))


def _first_range(parser: RefParser, text: str) -> tuple[int, int, str]:
    """Scan text and return (start_verse, end_verse, span) of the first match."""
    out = list(parser.scan_string(text))
    assert out, f"no match in {text!r}"
    ref, start, end = out[0]
    rng = ref.simple_refs[0].ranges[0]
    return rng.start_verse, rng.end_verse, text[start:end]


def test_explicit_following_verses_marker_interpreted() -> None:
    """A non-subverse following-verses marker yields an open-ended range."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "John 3:16seqq.") == (16, -1, "John 3:16seqq.")


def test_explicit_following_verse_marker_interpreted() -> None:
    """A non-subverse following-verse marker extends the range by one verse."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "John 3:16seq.") == (16, 17, "John 3:16seq.")


def test_following_marker_with_trailing_word() -> None:
    """A marker followed by whitespace and a word is still recognized."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "John 3:16seqq. and X") == (16, -1, "John 3:16seqq.")
    assert _first_range(parser, "John 3:16seq. then Y") == (16, 17, "John 3:16seq.")


def test_following_marker_glued_to_word_not_matched() -> None:
    """A marker glued to a longer word is not treated as a marker."""
    parser = _make_latin_marker_parser()
    # "seqq.foo" is not the marker; only "John 3:16" is the reference.
    assert _first_range(parser, "John 3:16seqq.foo") == (16, 16, "John 3:16")


def test_single_chapter_following_marker_interpreted() -> None:
    """Single-chapter books interpret an explicit following marker too."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "Jude 5seqq. more") == (5, -1, "Jude 5seqq.")


def test_single_chapter_following_marker_glued_not_matched() -> None:
    """Single-chapter books also reject a marker glued to a longer word."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "Jude 5seqq.foo") == (5, 5, "Jude 5")


def _make_dot_separator_parser() -> RefParser:
    """Return a parser whose verse-range separator is "." rather than ", ".

    With this style "Lk 1:28.42" denotes verses 28 and 42, and a trailing
    "Vulg." designator resolves the reference to the vulgata versification.
    "Esth" is added as a recognized name for Esther.
    """
    style = RefStyle.from_dict(
        {
            "base": "en-cmos_short",
            "verse_range_separator": ".",
            "also_recognize": [{"Esth": "EST"}],
            "versification_identifiers": {"Vulg.": "vulgata"},
        }
    )
    return RefParser(style, Versification.named("eng"))


def test_custom_verse_range_separator_parses_full_list() -> None:
    """A style's custom verse-range separator is honored, not the class default."""
    parser = _make_dot_separator_parser()
    ref = parser.parse("Lk 1:28.42")
    assert ref is not None
    ranges = ref.simple_refs[0].ranges
    assert len(ranges) == 2
    assert (ranges[0].start_verse, ranges[0].end_verse) == (28, 28)
    assert (ranges[1].start_verse, ranges[1].end_verse) == (42, 42)


def test_custom_verse_range_separator_with_designator() -> None:
    """The full list parses, validates, and resolves the trailing designator."""
    parser = _make_dot_separator_parser()
    ref = parser.parse("Esth 15:5.10.15 Vulg.")
    assert ref is not None
    assert ref.versification.identifier == "vulgata"
    assert ref.is_valid()
    ranges = ref.simple_refs[0].ranges
    assert [r.start_verse for r in ranges] == [5, 10, 15]


def test_default_verse_range_separator_unchanged() -> None:
    """The default comma-separated verse list still parses as before."""
    parser = _make_parser()
    ref = parser.parse("Rom 1:3, 5")
    assert ref is not None
    ranges = ref.simple_refs[0].ranges
    assert len(ranges) == 2
    assert (ranges[0].start_verse, ranges[1].start_verse) == (3, 5)
