import pytest
from versiref import RefParser, RefStyle, Versification, standard_names


@pytest.mark.parametrize(
    "sbl_ref,expected_cei_ref",
    [
        # Single verse
        ("John 3:16", "Gv 3,16"),
        ("Phlm 8", "Fm 1,8"),
        # Verse range in a single chapter
        ("Matt 5:3-12", "Mt 5,3-12"),  # parse hyphen
        ("Heb 11:1–6", "Eb 11,1-6"),  # parse en dash
        # Verse range in a single-chapter book
        ("2 John 4-6", "2Gv 1,4-6"),  # parse hyphen
        ("Jude 8–9", "Gd 1,8-9"),  # parse en dash
        # Multiple verse ranges in a single chapter
        ("Mark 4:3-9,13-20", "Mc 4,3-9.13-20"),
        ("1 Cor 13:4-7,13", "1Cor 13,4-7.13"),
        # Multiple verse ranges in a single-chapter book
        ("Jude 1, 4, 17, 21, 25", "Gd 1,1.4.17.21.25"),
        ("2 John 1, 3, 5-6", "2Gv 1,1.3.5-6"),
        # Cross-chapter range
        ("Luke 23:50-24:12", "Lc 23,50-24,12"),
        ("Phil 3:10-4:1", "Fil 3,10-4,1"),
        # Multiple ranges across chapters
        ("Acts 1:8-11; 2:1-4", "At 1,8-11; 2,1-4"),
        ("Rev 21:1-8; 22:1-5", "Ap 21,1-8; 22,1-5"),
        # Books with spaces in names
        ("1 John 1:5-10", "1Gv 1,5-10"),
        ("2 Tim 2:15", "2Tm 2,15"),
        ("1 Pet 5:7", "1Pt 5,7"),
        # Subverses
        ("John 1:1a", "Gv 1,1a"),
        ("Isa 11:1–2a", "Is 11,1-2a"),
        ("Gen 1:1a-c", "Gen 1,1a-c"),
        # Ranges with f
        ("Matt 5:4f", "Mt 5,4-5"),
        ("Jude 3–4", "Gd 1,3-4"),
        # Ranges with ff
        ("Rom 1:16ff", "Rm 1,16ss"),
        ("Eph 2:8ff", "Ef 2,8ss"),
    ],
)
def test_parse_sbl_and_format_cei(sbl_ref: str, expected_cei_ref: str) -> None:
    """Test parsing references in SBL style and formatting them in CEI style."""
    # Setup
    sbl_abbrevs = standard_names("en-sbl_abbreviations")
    sbl_style = RefStyle(
        names=sbl_abbrevs, chapter_verse_separator=":", verse_range_separator=","
    )

    cei_abbrevs = standard_names("it-cei_abbreviazioni")
    cei_style = RefStyle(
        names=cei_abbrevs,
        chapter_verse_separator=",",
        following_verse="s",
        following_verses="ss",
        range_separator="-",
        verse_range_separator=".",
    )

    eng_versification = Versification.standard("eng")

    # Create parser with SBL style
    parser = RefParser(sbl_style, eng_versification)

    # Parse the reference
    bible_ref = parser.parse_simple(sbl_ref)

    # Assert the reference was parsed successfully
    assert bible_ref is not None, f"Failed to parse: {sbl_ref}"

    # Format the reference in CEI style
    formatted_ref = bible_ref.format(cei_style)

    # Assert the formatted reference matches the expected CEI style
    assert formatted_ref == expected_cei_ref


def test_scan_string_simple() -> None:
    """Test scanning text for Bible references."""
    # Setup
    sbl_style = RefStyle(
        names=standard_names("en-sbl_abbreviations"),
        chapter_verse_separator=":",
        verse_range_separator=",",
    )
    eng_versification = Versification.standard("eng")
    parser = RefParser(sbl_style, eng_versification)

    # Test text with multiple references
    text = "Look at John 3:16 and Rom 8:28-30 for encouragement. Also Matt 5:3-12."

    # Test scanning for complete references
    refs = list(parser.scan_string_simple(text))
    assert len(refs) == 3

    ref1, start1, end1 = refs[0]
    assert ref1.format(sbl_style) == "John 3:16"
    assert text[start1:end1] == ref1.original_text

    ref2, start2, end2 = refs[1]
    assert ref2.format(sbl_style) == "Rom 8:28–30"
    assert text[start2:end2] == ref2.original_text

    ref3, start3, end3 = refs[2]
    assert ref3.format(sbl_style) == "Matt 5:3–12"
    assert text[start3:end3] == ref3.original_text


def test_scan_string_simple_as_ranges() -> None:
    """Test scanning text for Bible references split into verse ranges."""
    # Setup
    sbl_style = RefStyle(
        names=standard_names("en-sbl_abbreviations"),
        chapter_verse_separator=":",
        verse_range_separator=",",
    )
    eng_versification = Versification.standard("eng")
    parser = RefParser(sbl_style, eng_versification)

    # Test text with references containing multiple ranges
    text = "See Mark 4:3–9,13–20 and Acts 1:8–11; 2:1–4"

    # Test scanning with as_ranges=True
    range_refs = list(parser.scan_string_simple(text, as_ranges=True))
    assert len(range_refs) == 4

    ref1, start1, end1 = range_refs[0]
    assert ref1.format(sbl_style) == "Mark 4:3–9"
    assert text[start1:end1] == ref1.original_text

    ref2, start2, end2 = range_refs[1]
    assert ref2.format(sbl_style) == "Mark 4:13–20"
    assert text[start2:end2] == ref2.original_text

    ref3, start3, end3 = range_refs[2]
    assert ref3.format(sbl_style) == "Acts 1:8–11"
    assert text[start3:end3] == ref3.original_text

    ref4, start4, end4 = range_refs[3]
    assert ref4.format(sbl_style) == "Acts 2:1–4"
    assert text[start4:end4] == ref4.original_text


def test_scan_string_simple_with_noise() -> None:
    """Test scanning text with non-reference content."""
    # Setup
    sbl_names = RefStyle(names=standard_names("en-sbl_names"))
    sbl_abbrevs = RefStyle(names=standard_names("en-sbl_abbreviations"))
    eng_versification = Versification.standard("eng")
    parser = RefParser(sbl_names, eng_versification)

    # Test text with references mixed with other content
    text = """
    Chapter 1
    As we read in John 3:16, God loved the world.
    The price was $3:16 at the store.
    Romans 8:28 teaches us about God's purpose.
    """

    # Should only find the valid references
    refs = list(parser.scan_string_simple(text))
    assert len(refs) == 2

    ref1, start1, end1 = refs[0]
    assert ref1.format(sbl_abbrevs) == "John 3:16"
    assert text[start1:end1] == ref1.original_text

    ref2, start2, end2 = refs[1]
    assert ref2.format(sbl_abbrevs) == "Rom 8:28"
    assert text[start2:end2] == ref2.original_text
