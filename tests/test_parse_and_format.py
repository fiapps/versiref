"""Test parsing and formatting Bible references."""

import pytest
from typing import Optional
from versiref import RefParser, RefStyle, SimpleBibleRef, Versification, standard_names


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

    eng_versification = Versification.named("eng")

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


@pytest.mark.parametrize(
    "cmos_ref,expected_sbl_ref",
    [
        # Single book with multiple references
        ("Rom 8:28-30; 12:1-2", "Rom 8:28–30; 12:1–2"),
        ("Jn 1:1-5, 14", "John 1:1–5, 14"),
        # Multiple books
        ("Is 7:10-14; Lk 1:26-38", "Isa 7:10–14; Luke 1:26–38"),
        # Cross-chapter reference and whole chapter
        ("Gn 1:1-2:3; Ps 8:1-9", "Gen 1:1–2:3; Ps 8:1–9"),
        # Multiple books with multiple ranges
        ("Mt 5:3-12; 6:9-13; Jn 3:16-17", "Matt 5:3–12; 6:9–13; John 3:16–17"),
        (
            "1 Cor 13:4-7, 13; Eph 2:8-10; Phil 4:4-7",
            "1 Cor 13:4–7, 13; Eph 2:8–10; Phil 4:4–7",
        ),
        # Books with spaces in names
        ("1 Jn 1:5-10; 2 Jn 5-6", "1 John 1:5–10; 2 John 5–6"),
        ("1 Kgs 8:22-30; 2 Chr 7:1-3", "1 Kgs 8:22–30; 2 Chr 7:1–3"),
        # Mix of single-chapter and multi-chapter books
        ("Jude 3-4; Rv 21:1-5", "Jude 3–4; Rev 21:1–5"),
        ("Ob 15-18; Heb 11:1-6", "Obad 15–18; Heb 11:1–6"),
        # With subverses
        ("Rom 5:1-2a; Gal 2:20", "Rom 5:1–2a; Gal 2:20"),
        ("Jn 1:1a; 1 Jn 1:1b-2", "John 1:1a; 1 John 1:1b–2"),
        # With following verses notation
        ("Mk 16:15f; Acts 1:8", "Mark 16:15–16; Acts 1:8"),
        ("Heb 12:1ff; Jas 1:2-4", "Heb 12:1ff; Jas 1:2–4"),
    ],
)
def test_parse_cmos_and_format_sbl(cmos_ref: str, expected_sbl_ref: str) -> None:
    """Test parsing references in CMOS style and formatting them in SBL style."""
    # Setup
    cmos_style = RefStyle(names=standard_names("en-cmos_short"))
    sbl_style = RefStyle(names=standard_names("en-sbl_abbreviations"))
    eng_versification = Versification.named("eng")

    # Create parser with CMOS style
    parser = RefParser(cmos_style, eng_versification)

    # Parse the reference
    bible_ref = parser.parse(cmos_ref)

    # Assert the reference was parsed successfully
    assert bible_ref is not None, f"Failed to parse: {cmos_ref}"

    # Format the reference in SBL style
    formatted_ref = bible_ref.format(sbl_style)

    # Assert the formatted reference matches the expected SBL style
    assert formatted_ref == expected_sbl_ref


def test_scan_string_simple() -> None:
    """Test scanning text for Bible references."""
    # Setup
    sbl_style = RefStyle(
        names=standard_names("en-sbl_abbreviations"),
        chapter_verse_separator=":",
        verse_range_separator=",",
    )
    eng_versification = Versification.named("eng")
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
    sbl_style = RefStyle(names=standard_names("en-sbl_abbreviations"))
    eng_versification = Versification.named("eng")
    parser = RefParser(sbl_style, eng_versification)

    # Test text with references containing multiple ranges
    text = "See Luke 1:53,79 and Pss 2:1–3, 7–9; 110:1, 5–7"

    # Test scanning with as_ranges=True
    range_refs = list(parser.scan_string_simple(text, as_ranges=True))
    assert len(range_refs) == 6

    ref1, start1, end1 = range_refs[0]
    assert ref1.format(sbl_style) == "Luke 1:53"
    assert text[start1:end1] == ref1.original_text

    ref2, start2, end2 = range_refs[1]
    assert ref2.format(sbl_style) == "Luke 1:79"
    assert text[start2:end2] == ref2.original_text

    ref3, start3, end3 = range_refs[2]
    assert ref3.format(sbl_style) == "Ps 2:1–3"
    assert text[start3:end3] == ref3.original_text

    ref4, start4, end4 = range_refs[3]
    assert ref4.format(sbl_style) == "Ps 2:7–9"
    assert text[start4:end4] == ref4.original_text

    ref5, start5, end5 = range_refs[4]
    assert ref5.format(sbl_style) == "Ps 110:1"
    assert text[start5:end5] == ref5.original_text

    ref6, start6, end6 = range_refs[5]
    assert ref6.format(sbl_style) == "Ps 110:5–7"
    assert text[start6:end6] == ref6.original_text


def test_scan_string_simple_with_noise() -> None:
    """Test scanning text with non-reference content."""
    # Setup
    sbl_names = RefStyle(names=standard_names("en-sbl_names"))
    sbl_abbrevs = RefStyle(names=standard_names("en-sbl_abbreviations"))
    eng_versification = Versification.named("eng")
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


def test_sub_refs_simple_normalize() -> None:
    """Test using sub_refs_simple to normalize references to SBL style."""
    # Setup - create a style that recognizes multiple formats
    sbl_style = RefStyle(names=standard_names("en-sbl_abbreviations"))
    # Add alternative names
    sbl_style.also_recognize("en-cmos_short")
    sbl_style.also_recognize("en-cmos_long")

    eng_versification = Versification.named("eng")
    parser = RefParser(sbl_style, eng_versification)

    # Test text with inconsistently formatted references
    text = (
        "Let us strive to embody Christ’s teaching on loving our neighbors "
        "(Jn 15:12), recognizing His boundless mercy as described in Ps "
        "103:8.  May we find solace knowing that “God so loved the world” "
        "(Jn 3:16) and trust in His providence, echoing the words of "
        "Jeremiah (Jer. 29:11). Remembering St. Paul’s exhortation to live "
        "worthy of our calling (Eph 4:1), let us embrace faith as a shield "
        "(1 Pet 5:7) and seek wisdom from Proverbs (Prv 3:5-6). Finally, "
        "may we always remember the promise found in Revelation (Rev 21:4): "
        '"He will wipe away every tear."'
    )

    # Function to format references consistently
    def normalize_ref(ref: SimpleBibleRef) -> Optional[str]:
        return ref.format(sbl_style)

    # Normalize all references
    result = parser.sub_refs_simple(text, normalize_ref)

    expected = (
        "Let us strive to embody Christ’s teaching on loving our neighbors "
        "(John 15:12), recognizing His boundless mercy as described in Ps "
        "103:8.  May we find solace knowing that “God so loved the world” "
        "(John 3:16) and trust in His providence, echoing the words of "
        "Jeremiah (Jer 29:11). Remembering St. Paul’s exhortation to live "
        "worthy of our calling (Eph 4:1), let us embrace faith as a shield "
        "(1 Pet 5:7) and seek wisdom from Proverbs (Prov 3:5–6). Finally, "
        "may we always remember the promise found in Revelation (Rev 21:4): "
        '"He will wipe away every tear."'
    )

    assert result == expected


def test_sub_refs_simple_no_change() -> None:
    """Test using sub_refs_simple callback returning None."""
    # Setup - create a style that recognizes multiple formats
    sbl_style = RefStyle(names=standard_names("en-sbl_abbreviations"))
    # Add alternative names
    sbl_style.also_recognize("en-cmos_short")
    sbl_style.also_recognize("en-cmos_long")

    eng_versification = Versification.named("eng")
    parser = RefParser(sbl_style, eng_versification)

    # Test text with non-SBL references to convert.
    text = "See Jn 13:16 and Mk 28:1–15."

    # Function to format references consistently
    def normalize_ref(ref: SimpleBibleRef) -> Optional[str]:
        if ref.is_valid(eng_versification):
            return ref.format(sbl_style)
        else:
            return None

    # Normalize all references
    result = parser.sub_refs_simple(text, normalize_ref)

    expected = "See John 13:16 and Mk 28:1–15."

    assert result == expected
