"""Tests for the ref_parser module."""

import pyparsing as pp
import pytest

from versiref.bible_ref import BibleRef
from versiref.ref_parser import RefParser, Sensitivity
from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification


def test_parse_single_verse() -> None:
    """Test parsing a simple verse reference."""
    # Create a style
    names = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=names)

    # Create a versification
    versification = Versification.named("eng")

    # Create a parser
    parser = RefParser(style, versification)

    # Parse a simple reference: "Gen 1:1"
    ref = parser.parse("Gen 1:1")

    assert ref is not None
    assert ref.ranges[0].start.book == "GEN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 1
    assert ref.ranges[0].start.verse == 1
    assert ref.ranges[0].start.subverse == ""
    assert ref.ranges[0].end.chapter == 1
    assert ref.ranges[0].end.verse == 1
    assert ref.ranges[0].end.subverse == ""
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
    ref = parser.parse("John 3:16b")

    assert ref is not None
    assert ref.ranges[0].start.book == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 3
    assert ref.ranges[0].start.verse == 16
    assert ref.ranges[0].start.subverse == "b"
    assert ref.ranges[0].end.chapter == 3
    assert ref.ranges[0].end.verse == 16
    assert ref.ranges[0].end.subverse == "b"
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
    ref = parser.parse("Jude 5")

    assert ref is not None
    assert ref.ranges[0].start.book == "JUD"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 1  # Single-chapter books have chapter 1
    assert ref.ranges[0].start.verse == 5
    assert ref.ranges[0].end.chapter == 1
    assert ref.ranges[0].end.verse == 5
    assert ref.ranges[0].original_text == "Jude 5"


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
    ref = parser.parse("2 John 5")

    assert ref is not None
    assert ref.ranges[0].start.book == "2JN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 1  # Single-chapter books have chapter 1
    assert ref.ranges[0].start.verse == 5
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
    ref = parser.parse("1 Kgs 8:10")

    assert ref is not None
    assert ref.ranges[0].start.book == "1KI"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 8
    assert ref.ranges[0].start.verse == 10
    assert ref.ranges[0].original_text == "1 Kgs 8:10"


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
    assert ref.books() == ["MAT", "1JN"]
    assert len(ref.ranges) == 3

    # Check first book (Matthew)
    assert ref.ranges[0].start.book == "MAT"
    assert ref.ranges[1].start.book == "MAT"
    # First range in Matthew
    assert ref.ranges[0].start.chapter == 5
    assert ref.ranges[0].start.verse == 3
    assert ref.ranges[0].end.chapter == 5
    assert ref.ranges[0].end.verse == 12
    # Second range in Matthew
    assert ref.ranges[1].start.chapter == 6
    assert ref.ranges[1].start.verse == 9
    assert ref.ranges[1].end.chapter == 6
    assert ref.ranges[1].end.verse == 13

    # Check second book (1 John)
    assert ref.ranges[2].start.book == "1JN"
    assert ref.ranges[2].start.chapter == 3
    assert ref.ranges[2].start.verse == 16
    assert ref.ranges[2].end.chapter == 3
    assert ref.ranges[2].end.verse == 17


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
    assert ref.books() == ["ISA", "LUK"]
    assert len(ref.ranges) == 2

    # Check first book (Isaiah)
    assert ref.ranges[0].start.book == "ISA"
    assert ref.ranges[0].start.chapter == 7
    assert ref.ranges[0].start.verse == 10
    assert ref.ranges[0].end.chapter == 7
    assert ref.ranges[0].end.verse == 14

    # Check second book (Luke)
    assert ref.ranges[1].start.book == "LUK"
    assert ref.ranges[1].start.chapter == 1
    assert ref.ranges[1].start.verse == 26
    assert ref.ranges[1].end.chapter == 1
    assert ref.ranges[1].end.verse == 38

    assert text[start:end] == "Is 7:10-14; Lk 1:26-38"


def test_scan_ignores_book_name_glued_to_preceding_word() -> None:
    """A book name preceded by a letter is not a reference (e.g. "Rom" in "CongrRom")."""
    names = standard_names("en-cmos_short")
    style = RefStyle(names=names)
    versification = Versification.named("eng")
    parser = RefParser(style, versification)

    refs = list(parser.scan_string("in CongrRom 5:65-103"))
    assert refs == []


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
    ref = parser.parse("John 3")

    assert ref is not None
    assert ref.ranges[0].start.book == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 3
    assert ref.ranges[0].start.verse is None
    assert ref.ranges[0].end.chapter == 3
    assert ref.ranges[0].end.verse is None
    assert ref.ranges[0].is_whole_chapters()


def test_parse_whole_chapter_range() -> None:
    """Test parsing a chapter range like 'John 3–5'."""
    parser = _make_parser()
    ref = parser.parse("John 3–5")

    assert ref is not None
    assert ref.ranges[0].start.book == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start.chapter == 3
    assert ref.ranges[0].end.chapter == 5
    assert ref.ranges[0].is_whole_chapters()


def test_parse_whole_book() -> None:
    """Test parsing a whole-book reference like 'Genesis'."""
    names = standard_names("en-sbl_names")
    style = RefStyle(names=names)
    versification = Versification.named("eng")
    parser = RefParser(style, versification)
    ref = parser.parse("Genesis")

    assert ref is not None
    assert ref.ranges[0].start.book == "GEN"
    assert ref.is_whole_books()
    assert ref.ranges[0].start.chapter is None
    assert ref.ranges[0].end == ref.ranges[0].start
    assert len(ref.ranges) == 1


def test_parse_whole_book_abbreviation() -> None:
    """Test parsing a whole-book reference with an abbreviation."""
    parser = _make_parser()
    ref = parser.parse("Gen")

    assert ref is not None
    assert ref.ranges[0].start.book == "GEN"
    assert ref.ranges[0].start.chapter is None
    assert ref.ranges[0].end == ref.ranges[0].start
    assert ref.is_single_range()
    assert ref.is_whole_books()
    assert ref.is_whole_chapters()


# --- Sensitivity filtering ---


def test_scan_default_sensitivity_skips_chapters() -> None:
    """Default sensitivity (VERSE) should skip whole-chapter references."""
    parser = _make_parser()
    text = "See John 3 and Matt 5:3 for context."
    refs = list(parser.scan_string(text))

    assert len(refs) == 1
    _ref, start, end = refs[0]
    assert text[start:end] == "Matt 5:3"


def test_scan_default_sensitivity_skips_books() -> None:
    """Default sensitivity (VERSE) should skip whole-book references."""
    parser = _make_parser()
    text = "Read Gen and then John 3:16."
    refs = list(parser.scan_string(text))

    assert len(refs) == 1
    _ref, start, end = refs[0]
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
    assert ref.books() == ["GEN", "DAN"]


def test_designator_aliases_and_longest_match() -> None:
    """Aliases resolve, and 'Vulgate' is not parsed as 'Vulg.' plus 'ate'."""
    parser = _make_designator_parser()
    assert parser.parse("Esth 13 Vulgate").versification.identifier == "vulgata"
    assert parser.parse("Gen 1:1 (LXX)").versification.identifier == "lxx"
    assert parser.parse("Gen 1:1 LXX").versification.identifier == "lxx"


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


def _first_range(parser: RefParser, text: str) -> tuple[int | None, int | None, str]:
    """Scan text and return (start_verse, end_verse, span) of the first match."""
    out = list(parser.scan_string(text))
    assert out, f"no match in {text!r}"
    ref, start, end = out[0]
    rng = ref.ranges[0]
    return rng.start.verse, rng.end.verse, text[start:end]


def test_explicit_following_verses_marker_interpreted() -> None:
    """A non-subverse following-verses marker yields an open-ended range."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "John 3:16seqq.") == (16, None, "John 3:16seqq.")


def test_explicit_following_verse_marker_interpreted() -> None:
    """A non-subverse following-verse marker extends the range by one verse."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "John 3:16seq.") == (16, 17, "John 3:16seq.")


def test_following_marker_with_trailing_word() -> None:
    """A marker followed by whitespace and a word is still recognized."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "John 3:16seqq. and X") == (16, None, "John 3:16seqq.")
    assert _first_range(parser, "John 3:16seq. then Y") == (16, 17, "John 3:16seq.")


def test_following_marker_glued_to_word_not_matched() -> None:
    """A marker glued to a longer word is not treated as a marker."""
    parser = _make_latin_marker_parser()
    # "seqq.foo" is not the marker; only "John 3:16" is the reference.
    assert _first_range(parser, "John 3:16seqq.foo") == (16, 16, "John 3:16")


def test_single_chapter_following_marker_interpreted() -> None:
    """Single-chapter books interpret an explicit following marker too."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "Jude 5seqq. more") == (5, None, "Jude 5seqq.")


def test_single_chapter_following_marker_glued_not_matched() -> None:
    """Single-chapter books also reject a marker glued to a longer word."""
    parser = _make_latin_marker_parser()
    assert _first_range(parser, "Jude 5seqq.foo") == (5, 5, "Jude 5")


@pytest.mark.parametrize(
    ("versification", "text", "start", "end"),
    [
        ("cei", "Esg 1:1f", ("ESG", 1, 1, "f"), ("ESG", 1, 1, "f")),
        ("cei", "Esg 3:13f", ("ESG", 3, 13, "f"), ("ESG", 3, 13, "f")),
        ("cei", "Esg 1:1 f", ("ESG", 1, 1, ""), ("ESG", 1, 2, "")),
        ("cei", "Esg 1:1ff", ("ESG", 1, 1, ""), ("ESG", 1, None, "")),
        ("cei", "Rom 8:1f", ("ROM", 8, 1, ""), ("ROM", 8, 2, "")),
        ("lxx", "Esg 1:1f", ("ESG", 1, 1, "f"), ("ESG", 1, 1, "f")),
        # Where the verse has no inserted verse "f", it is the following verse.
        ("org", "Esg 1:1f", ("ESG", 1, 1, ""), ("ESG", 1, 2, "")),
        ("eng", "Esg 1:1f", ("ESG", 1, 1, ""), ("ESG", 1, 2, "")),
    ],
)
def test_glued_following_marker_names_inserted_verse(
    versification: str,
    text: str,
    start: tuple[str, int, int | None, str],
    end: tuple[str, int, int | None, str],
) -> None:
    """A marker glued to a verse that has an inserted verse by its letter names that verse."""
    parser = RefParser(
        RefStyle.named("en-bibleworks"), Versification.named(versification)
    )
    ref = parser.parse(text)
    assert ref is not None
    (rng,) = ref.ranges
    assert (
        rng.start.book,
        rng.start.chapter,
        rng.start.verse,
        rng.start.subverse,
    ) == start
    assert (rng.end.book, rng.end.chapter, rng.end.verse, rng.end.subverse) == end


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
    ranges = ref.ranges
    assert len(ranges) == 2
    assert (ranges[0].start.verse, ranges[0].end.verse) == (28, 28)
    assert (ranges[1].start.verse, ranges[1].end.verse) == (42, 42)


def test_custom_verse_range_separator_with_designator() -> None:
    """The full list parses, validates, and resolves the trailing designator."""
    parser = _make_dot_separator_parser()
    ref = parser.parse("Esth 15:5.10.15 Vulg.")
    assert ref is not None
    assert ref.versification.identifier == "vulgata"
    assert ref.is_valid()
    ranges = ref.ranges
    assert [r.start.verse for r in ranges] == [5, 10, 15]


def _la_vetus_parser() -> RefParser:
    return RefParser(RefStyle.named("la-vetus"), Versification.named("vulgata"))


@pytest.mark.parametrize(
    ("text", "book_id", "chapter", "verse"),
    [
        ("Lc. I, 35", "LUK", 1, 35),
        ("Eccli. XXIV, 5", "SIR", 24, 5),
        ("I Cor. XV, 3", "1CO", 15, 3),
        ("Ps. CIX, 1", "PSA", 109, 1),
        ("Psal. XLIV, 2", "PSA", 44, 2),
        ("Joan. III, 16", "JHN", 3, 16),
        ("Ioan. III, 16", "JHN", 3, 16),
        ("Matth. I, 20", "MAT", 1, 20),
        ("IV Reg. II, 11", "2KI", 2, 11),
        ("Canticum Canticorum IV, 7", "SNG", 4, 7),
    ],
)
def test_parse_la_vetus_forms(
    text: str, book_id: str, chapter: int, verse: int
) -> None:
    """Test parsing traditional Latin abbreviations and variants."""
    parser = _la_vetus_parser()
    ref = parser.parse(text)
    assert ref is not None
    assert ref.ranges[0].start.book == book_id
    assert ref.ranges[0].start.chapter == chapter
    assert ref.ranges[0].start.verse == verse


def test_parse_roman_verse_range() -> None:
    """Test parsing a verse range with a Roman chapter; verses stay Arabic."""
    parser = _la_vetus_parser()
    ref = parser.parse("Io. XIX, 26-27")
    assert ref is not None
    assert ref.ranges[0].start.book == "JHN"
    assert ref.ranges[0].start.chapter == 19
    assert ref.ranges[0].start.verse == 26
    assert ref.ranges[0].end.verse == 27


def test_parse_roman_cross_chapter_range() -> None:
    """Test parsing a range that crosses a chapter boundary."""
    parser = _la_vetus_parser()
    ref = parser.parse("Luc. XXIII, 50-XXIV, 12")
    assert ref is not None
    assert ref.ranges[0].start.chapter == 23
    assert ref.ranges[0].start.verse == 50
    assert ref.ranges[0].end.chapter == 24
    assert ref.ranges[0].end.verse == 12


def test_parse_roman_whole_chapter() -> None:
    """Test parsing a whole-chapter reference with a Roman numeral."""
    parser = _la_vetus_parser()
    ref = parser.parse("Cant. IV")
    assert ref is not None
    assert ref.ranges[0].start.book == "SNG"
    assert ref.ranges[0].start.chapter == 4
    assert ref.ranges[0].start.verse is None


def test_roman_parser_rejects_arabic_chapter() -> None:
    """Test that a Roman-numeral style does not accept Arabic chapters."""
    parser = _la_vetus_parser()
    assert parser.parse("Lc. 1, 35", silent=True) is None


def test_arabic_parser_rejects_roman_chapter() -> None:
    """Test that an Arabic-numeral style does not accept Roman chapters."""
    parser = RefParser(RefStyle.named("la-cce"), Versification.named("vulgata"))
    assert parser.parse("Lc I, 35", silent=True) is None
    ref = parser.parse("Lc 1, 35")
    assert ref is not None
    assert ref.ranges[0].start.book == "LUK"
    assert ref.ranges[0].start.chapter == 1
    assert ref.ranges[0].start.verse == 35


def test_roman_chapter_not_start_of_word() -> None:
    """Test that a Roman numeral glued to a longer word is not a chapter."""
    parser = _la_vetus_parser()
    assert parser.parse("Psal. Clementis, 3", silent=True) is None
    # The æ/œ ligatures count as word characters
    assert parser.parse("Psal. Lætitia, 3", silent=True) is None
    assert parser.parse("Psal. Cœna, 3", silent=True) is None


def test_parse_roman_lowercase_style() -> None:
    """Test a style with lowercase Roman numeral chapters."""
    style = RefStyle.from_dict(
        {"base": "la-vetus", "chapter_number_style": "roman-lower"}
    )
    parser = RefParser(style, Versification.named("vulgata"))
    ref = parser.parse("Lc. i, 35")
    assert ref is not None
    assert ref.ranges[0].start.chapter == 1
    assert ref.ranges[0].start.verse == 35
    assert parser.parse("Lc. I, 35", silent=True) is None


def test_scan_string_la_vetus() -> None:
    """Test scanning Latin text for references."""
    style = RefStyle.named("la-vetus")
    parser = RefParser(style, Versification.named("vulgata"))
    text = "Angelus ait (Lc. I, 35), et propheta praedixit (Isa. VII, 14)."
    refs = list(parser.scan_string(text))
    assert len(refs) == 2
    ref1, start1, end1 = refs[0]
    assert ref1.format(style) == "Luc. I, 35"
    assert text[start1:end1] == ref1.original_text
    ref2, start2, end2 = refs[1]
    assert ref2.format(style) == "Isa. VII, 14"
    assert text[start2:end2] == ref2.original_text


def test_parse_chapter_verse_separator_without_space() -> None:
    """Test that a ", " separator style also parses references without the space."""
    parser = _la_vetus_parser()
    ref = parser.parse("Lc. I,35")
    assert ref is not None
    assert ref.ranges[0].start.chapter == 1
    assert ref.ranges[0].start.verse == 35


def test_reference_wraps_across_single_newline() -> None:
    """Test that a hard-wrapped reference still parses across one newline."""
    parser = RefParser(
        RefStyle(names=standard_names("en-sbl_abbreviations")),
        Versification.named("eng"),
    )
    ref = parser.parse("Mark 4:3-9,\n13-20")
    assert ref is not None
    assert len(ref.ranges) == 2
    assert ref.ranges[1].start.verse == 13
    ref = parser.parse("Luke 23:50-\n24:12")
    assert ref is not None
    assert ref.ranges[0].end.chapter == 24


def test_reference_stops_at_blank_line() -> None:
    """Test that a reference does not continue across a blank line."""
    style = RefStyle.named("la-vetus")
    parser = RefParser(style, Versification.named("vulgata"))
    text = "ut dicitur Gen. XXII, 18.\n\n2 Deinde considerandum est."
    refs = list(parser.scan_string(text))
    assert len(refs) == 1
    ref, start, end = refs[0]
    assert ref.format(style) == "Gen. XXII, 18"
    assert text[start:end] == "Gen. XXII, 18"


def test_reference_stops_at_blank_line_with_spaces() -> None:
    """Test that a blank line containing spaces also ends a reference."""
    parser = RefParser(
        RefStyle(names=standard_names("en-sbl_abbreviations")),
        Versification.named("eng"),
    )
    text = "See Mark 4:3-9,  \n  \n13 is the footnote."
    refs = list(parser.scan_string(text))
    assert len(refs) == 1
    _ref, start, end = refs[0]
    assert text[start:end] == "Mark 4:3-9"


def test_chapter_separator_stops_at_blank_line() -> None:
    """Test that the chapter separator does not reach across a blank line."""
    parser = RefParser(
        RefStyle(names=standard_names("en-sbl_abbreviations")),
        Versification.named("eng"),
    )
    text = "Heb 7:3;\n\n9:4 begins a new paragraph."
    refs = list(parser.scan_string(text))
    assert refs[0][0].format(
        RefStyle(names=standard_names("en-sbl_abbreviations"))
    ) == ("Heb 7:3")


def _scan(
    text: str,
    style: str = "en-sbl",
    versification: str = "eng",
    sensitivity: Sensitivity = Sensitivity.VERSE,
) -> list[tuple[str, str]]:
    """Scan text, returning each match's text and its normalized form."""
    ref_style = RefStyle.named(style)
    parser = RefParser(ref_style, Versification.named(versification))
    return [
        (text[start:end], ref.format(ref_style))
        for ref, start, end in parser.scan_string(text, sensitivity=sensitivity)
    ]


@pytest.mark.parametrize(
    "text", ["Marketing is fun", "Marks", "Jobs 3:4", "Actson 2:3", "Lætare"]
)
def test_book_name_is_not_the_start_of_a_longer_word(text: str) -> None:
    """A name that ends in a letter does not match when a letter follows."""
    assert _scan(text, sensitivity=Sensitivity.BOOK) == []
    assert _scan(text, style="la-cce", sensitivity=Sensitivity.BOOK) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Mark's gospel", "Mark"),
        ("see Mark.", "Mark"),
        ("(Mark)", "Mark"),
        ("Mark3:4", "Mark3:4"),
    ],
)
def test_book_name_may_be_followed_by_a_non_letter(text: str, expected: str) -> None:
    """Punctuation or a digit after a name does not prevent a match."""
    found = _scan(text, sensitivity=Sensitivity.BOOK)
    assert [match for match, _ in found] == [expected]


@pytest.mark.parametrize(
    "text",
    [
        "1\u00a0Kgs 3:4",
        "1\u202fKgs 3:4",
        "1  Kgs 3:4",
        "1\tKgs 3:4",
        "1\nKgs 3:4",
        "1 \n Kgs 3:4",
    ],
)
def test_space_in_book_name_matches_other_whitespace(text: str) -> None:
    """The space in a name stands for any whitespace short of a blank line."""
    assert _scan(text) == [(text, "1 Kgs 3:4")]


def test_space_in_book_name_does_not_match_a_blank_line() -> None:
    """A book name does not continue across a paragraph break."""
    assert _scan("1\n\nKgs 3:4") == []


@pytest.mark.parametrize(
    "text",
    [
        "John\u00a03:16,\u00a018",
        "John\u202f3:16,\u200918",
        "John 3:16,\u00a0 18",
    ],
)
def test_no_break_and_thin_spaces_separate_tokens(text: str) -> None:
    """The spaces typesetters use within a reference count as whitespace."""
    assert _scan(text) == [(text, "John 3:16, 18")]


@pytest.mark.parametrize(
    ("text", "style", "versification", "expected"),
    [
        ("cfr. Mt 5,3-12, dove", "it-cei", "cei", "Mt 5,3-12"),
        ("cfr. Mt 5,3-12,\u00a0dove", "it-cei", "cei", "Mt 5,3-12"),
        ("cf. Mt 5, 3-12, ubi", "la-cce", "nova_vulgata", "Mt 5, 3-12"),
        ("cfr. Mt 5,3-6,2, dove", "it-cei", "cei", "Mt 5,3-6,2"),
    ],
)
def test_range_end_keeps_its_verse_before_a_comma(
    text: str, style: str, versification: str, expected: str
) -> None:
    """A comma after a range is not taken for a chapter-verse separator.

    Where the style writes chapter and verse as "5,3", the 12 of "5,3-12,"
    once parsed as an end chapter awaiting its verse, and the range was cut
    back to its first verse.
    """
    assert [match for match, _ in _scan(text, style, versification)] == [expected]


def _spans(text: str, style: str = "en-sbl") -> list[tuple[object, ...]]:
    """Parse text, describing each range by the book, chapter and verse of its ends."""
    parser = RefParser(RefStyle.named(style), Versification.named("eng"))
    ref = parser.parse(text)
    assert ref is not None
    return [
        (
            r.start.book,
            r.start.chapter,
            r.start.verse,
            r.end.book,
            r.end.chapter,
            r.end.verse,
        )
        for r in ref.ranges
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Gen 1; 2:4", [("GEN", 1, None, "GEN", 1, None), ("GEN", 2, 4, "GEN", 2, 4)]),
        ("Gen 1–2:4", [("GEN", 1, None, "GEN", 2, 4)]),
        ("Gen 1-2:4a", [("GEN", 1, None, "GEN", 2, 4)]),
        (
            "John 3:16; 4",
            [("JHN", 3, 16, "JHN", 3, 16), ("JHN", 4, None, "JHN", 4, None)],
        ),
        (
            "Rom 8:1–9:5; 12; 13:1, 8",
            [
                ("ROM", 8, 1, "ROM", 9, 5),
                ("ROM", 12, None, "ROM", 12, None),
                ("ROM", 13, 1, "ROM", 13, 1),
                ("ROM", 13, 8, "ROM", 13, 8),
            ],
        ),
        (
            "John 3; 4:5; 6–7",
            [
                ("JHN", 3, None, "JHN", 3, None),
                ("JHN", 4, 5, "JHN", 4, 5),
                ("JHN", 6, None, "JHN", 7, None),
            ],
        ),
    ],
)
def test_parse_whole_chapters_mixed_with_verses(
    text: str, expected: list[tuple[object, ...]]
) -> None:
    """Whole chapters and verses of one book may follow one another."""
    assert _spans(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Matt–John", [("MAT", None, None, "JHN", None, None)]),
        ("Luke-Acts", [("LUK", None, None, "ACT", None, None)]),
        ("Matt–Mark 3", [("MAT", None, None, "MRK", 3, None)]),
        ("1 Sam 31:1–2 Sam 1:27", [("1SA", 31, 1, "2SA", 1, 27)]),
        ("Gen 50–Exod 2", [("GEN", 50, None, "EXO", 2, None)]),
        ("Gen 50–Exod 2:3", [("GEN", 50, None, "EXO", 2, 3)]),
        ("Gen 1–2 Sam 3", [("GEN", 1, None, "2SA", 3, None)]),
        ("Ps 150:1–Prov 3", [("PSA", 150, 1, "PRO", 3, None)]),
        # A lone number after a one-chapter book is a verse.
        ("2 John 12–3 John 4", [("2JN", 1, 12, "3JN", 1, 4)]),
        ("Phlm 20–Heb 1:2", [("PHM", 1, 20, "HEB", 1, 2)]),
        # What follows is in the book where the range ended.
        (
            "1 Sam 31–2 Sam 1; 3:1",
            [("1SA", 31, None, "2SA", 1, None), ("2SA", 3, 1, "2SA", 3, 1)],
        ),
        (
            "1 Sam 31:1–2 Sam 1:27, 30",
            [("1SA", 31, 1, "2SA", 1, 27), ("2SA", 1, 30, "2SA", 1, 30)],
        ),
    ],
)
def test_parse_range_that_spans_books(
    text: str, expected: list[tuple[object, ...]]
) -> None:
    """A range may end in another book."""
    assert _spans(text) == expected


def test_parse_range_that_spans_books_roman() -> None:
    """A range into another book parses with Roman-numeral chapters too."""
    assert _spans("I Reg. XXXI, 1-II Reg. I, 27", "la-vetus") == [
        ("1SA", 31, 1, "2SA", 1, 27)
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # A number that begins a numbered book's name starts a new book.
        ("John 3:16; 1 John 2:1", ["John 3:16; 1 John 2:1"]),
        ("John 3:16, 1 Cor 2:3", ["John 3:16", "1 Cor 2:3"]),
        ("John 3; 1 John 2", ["John 3; 1 John 2"]),
        # At the end of a range it does so only if the book is cited.
        ("Luke 1–2 John the Baptist", ["Luke 1–2", "John"]),
        ("Rev 1–3 John wrote", ["Rev 1–3", "John"]),
        ("John 3:16–1 John 2", ["John 3:16–1 John 2"]),
        # A range that starts within a book does not end with a bare name.
        ("Mark 2:1–John", ["Mark 2:1", "John"]),
        # A chapter number is not the start of a word.
        ("John 3:16; 4th", ["John 3:16"]),
        ("John 3rd", ["John"]),
    ],
)
def test_scan_numbers_and_book_names(text: str, expected: list[str]) -> None:
    """Numbers are assigned to the book before or the book after as sense requires."""
    found = _scan(text, sensitivity=Sensitivity.BOOK)
    assert [match for match, _ in found] == expected


def test_scan_as_ranges_reports_each_range() -> None:
    """With as_ranges, every range is reported, whole books among them."""
    style = RefStyle.named("en-sbl")
    parser = RefParser(style, Versification.named("eng"))
    text = "See John; Mark 1:1, 3; 2 and Matt–Luke."

    def found(sensitivity: Sensitivity) -> list[str]:
        return [
            text[start:end]
            for _, start, end in parser.scan_string(
                text, as_ranges=True, sensitivity=sensitivity
            )
        ]

    assert found(Sensitivity.BOOK) == ["John", "Mark 1:1", "3", "2", "Matt–Luke"]
    assert found(Sensitivity.CHAPTER) == ["Mark 1:1", "3", "2"]
    assert found(Sensitivity.VERSE) == ["Mark 1:1", "3"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("? Prov. IX, 1; CCL IX, 156.", ["Prov. IX, 1"]),
        ("1 Ps. CIX, 4; CCL II, 1410.", ["Ps. CIX, 4"]),
        ("Lc. IV, 35; CC XIV, 30", ["Lc. IV, 35"]),
        # A chapter some book could have still continues the reference.
        ("Ps. CIX, 4; CL, 6.", ["Ps. CIX, 4; CL, 6"]),
        # A chapter that follows the book's name is not held to the limit, so
        # that a mistaken number is reported as invalid and not passed over.
        ("Ps. CCL, 1.", ["Ps. CCL, 1"]),
    ],
)
def test_scan_implausible_chapter_ends_the_reference(
    text: str, expected: list[str]
) -> None:
    """A number no book has for a chapter does not continue a reference."""
    parser = RefParser(RefStyle.named("la-vetus"), Versification.named("vulgata"))
    found = [text[start:end] for _, start, end in parser.scan_string(text)]
    assert found == expected


def test_scan_implausible_arabic_chapter_ends_the_reference() -> None:
    """The limit applies to Arabic chapter numbers too."""
    parser = RefParser(RefStyle.named("en-sbl"), Versification.named("eng"))
    text = "John 3:16; 200 people came, and Rom 8:28; 12 too"
    found = [
        text[start:end]
        for _, start, end in parser.scan_string(text, sensitivity=Sensitivity.CHAPTER)
    ]
    assert found == ["John 3:16", "Rom 8:28; 12"]


def test_strict_parser_accepts_only_the_style_range_separator() -> None:
    """A strict parser reads the style's en dash but not a hyphen as a range."""
    style = RefStyle.named("en-sbl")
    versification = Versification.named("eng")
    strict = RefParser(style, versification, strict=True)
    ref = strict.parse("Gen 1:1–3")
    assert ref is not None
    assert ref.format(style) == "Gen 1:1–3"
    assert strict.parse("Gen 1:1-3", silent=True) is None
    assert RefParser(style, versification).parse("Gen 1:1-3") == ref


def test_parse_raises_unless_silent() -> None:
    """parse() raises on text that is not a reference unless silent."""
    parser = RefParser(RefStyle.named("en-sbl"), Versification.named("eng"))
    with pytest.raises(pp.ParseException):
        parser.parse("not a reference")
    assert parser.parse("not a reference", silent=True) is None


def test_style_without_names_matches_nothing() -> None:
    """A parser whose style names no books finds no references."""
    parser = RefParser(RefStyle(names={}), Versification.named("eng"))
    assert parser.parse("Gen 1:1", silent=True) is None
    assert list(parser.scan_string("See Gen 1:1 and John 3:16.")) == []


def test_unusual_range_separator_is_recognized_beside_the_usual_ones() -> None:
    """A lenient parser reads the style's own separator, a hyphen, and an en dash."""
    style = RefStyle(names={"GEN": "Gen"}, range_separator="—")
    parser = RefParser(style, Versification.named("eng"))
    ref = parser.parse("Gen 1:1—3")
    assert ref is not None
    assert ref.format(style) == "Gen 1:1—3"
    assert parser.parse("Gen 1:1-3") == ref
    assert parser.parse("Gen 1:1–3") == ref
