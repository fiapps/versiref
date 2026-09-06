"""Tests for the Versification class."""

import logging
import pathlib

import pytest  # noqa: F401
from versiref.versification import Versification


def test_empty_versification() -> None:
    """Test that an empty Versification returns 99 for any book and chapter."""
    v = Versification()
    assert v.last_verse("XYZ", 1) == 99
    assert v.last_verse("GEN", 100) == 99
    assert v.last_verse("REV", 0) == 99


def test_standard_versification_eng() -> None:
    """Test loading the English standard versification."""
    v = Versification.named("eng")
    assert v is not None
    assert v.identifier == "eng"

    # Test specific known verse counts
    assert v.last_verse("GEN", 1) == 31  # Genesis 1 has 31 verses
    assert v.last_verse("GEN", 3) == 24  # Genesis 3 has 24 verses
    assert v.last_verse("PSA", 119) == 176  # Psalm 119 has 176 verses
    assert v.last_verse("JHN", 3) == 36  # John 3 has 36 verses
    assert v.last_verse("REV", 22) == 21  # Revelation 22 has 21 verses


def test_nonexistent_standard_versification() -> None:
    """Test that requesting a nonexistent versification raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        Versification.named("nonexistent")


def test_last_verse_nonexistent_book() -> None:
    """Test that requesting a nonexistent book returns -1."""
    v = Versification.named("eng")
    assert v.last_verse("XYZ", 1) == -1


def test_last_verse_nonexistent_chapter() -> None:
    """Test that requesting a nonexistent chapter returns -1."""
    v = Versification.named("eng")
    assert v.last_verse("GEN", 100) == -1
    assert v.last_verse("GEN", -1) == -1


def test_from_file() -> None:
    """Test loading a versification from a file."""
    # Get the path to one of the standard versification files
    from importlib import resources

    path = resources.files("versiref").joinpath("data", "versifications", "eng.json")

    v = Versification.from_file(str(path), "test-eng")
    assert v is not None
    assert v.identifier == "test-eng"
    assert v.last_verse("GEN", 1) == 31


def test_multiple_versifications() -> None:
    """Test loading and comparing multiple versifications."""
    eng = Versification.named("eng")
    lxx = Versification.named("lxx")
    vul = Versification.named("vulgata")

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


def test_is_single_chapter() -> None:
    """Test ."""
    v = Versification.named("eng")
    assert v.is_single_chapter("GEN") is False
    assert v.is_single_chapter("PSAS") is False
    assert v.is_single_chapter("2JN") is True


def test_mapping_data_loaded() -> None:
    """Test that mappedVerses data is parsed into mapping dicts."""
    eng = Versification.named("eng")
    assert len(eng._map_to_org) > 0
    assert len(eng._map_from_org) > 0
    # GEN 31:55 in eng maps to GEN 32:1 in org
    assert eng._map_to_org[("GEN", 31, 55, "")] == (
        ("GEN", 32, 1, ""),
        ("GEN", 32, 1, ""),
    )


def test_map_verse_with_mapping() -> None:
    """Test mapping a verse that has an explicit mapping entry."""
    eng = Versification.named("eng")
    org = Versification.named("org")
    assert eng.map_verse("GEN", 32, 1, org) == ("GEN", 32, 2, "")


def test_map_verse_identity() -> None:
    """Test mapping a verse with no mapping entry (identity)."""
    eng = Versification.named("eng")
    org = Versification.named("org")
    assert eng.map_verse("GEN", 1, 1, org) == ("GEN", 1, 1, "")


def test_map_verse_same_versification() -> None:
    """Test mapping to the same versification returns input unchanged."""
    eng = Versification.named("eng")
    assert eng.map_verse("GEN", 32, 1, eng) == ("GEN", 32, 1, "")


def test_map_verse_cross_book() -> None:
    """Test mapping a verse that changes book ID."""
    eng = Versification.named("eng")
    org = Versification.named("org")
    # eng BAR 6:1 maps to org LJE 1:1
    assert eng.map_verse("BAR", 6, 1, org) == ("LJE", 1, 1, "")


def test_map_verse_between_non_org() -> None:
    """Test mapping between two non-org versifications via org."""
    eng = Versification.named("eng")
    vul = Versification.named("vulgata")
    # eng GEN 32:1 -> org GEN 32:2 -> vul GEN 32:1
    assert eng.map_verse("GEN", 32, 1, vul) == ("GEN", 32, 1, "")


def test_map_verse_nonexistent_in_target() -> None:
    """Test that mapping returns None when the verse doesn't exist in target."""
    eng = Versification.named("eng")
    org = Versification.named("org")
    # BAR 6:73 maps to LJE 1:73 but LJE only has 72 verses in org
    assert eng.map_verse("BAR", 6, 73, org) is None


def test_includes() -> None:
    """Test checking if a book is included in the versification."""
    v = Versification.named("eng")
    assert v.includes("GEN") is True
    assert v.includes("PSA") is True
    assert v.includes("PSAS") is True
    assert v.includes("XYZ") is False  # Nonexistent book
    assert v.includes("REV") is True


# A versification that maps plain verses to structural subverse locations in
# org, in the style the upstream eng data once used for Greek Esther.
_SUBVERSE_VERSIFICATION = """{
  "maxVerses": {"ESG": [39, 23, 22, 47, 28, 14, 10, 41, 32, 14]},
  "mappedVerses": {
    "ESG 1:1": "ESG 1:1a",
    "ESG 8:32": "ESG 8:12u"
  }
}"""


def _subverse_versification(tmp_path: pathlib.Path) -> Versification:
    """Build a Versification with subverse mapping entries from a temp file."""
    path = tmp_path / "sub.json"
    path.write_text(_SUBVERSE_VERSIFICATION)
    return Versification.from_file(str(path), "sub")


def test_subverse_mapping_data_loaded(tmp_path: pathlib.Path) -> None:
    """Test that subverse mapping entries are parsed correctly."""
    sub = _subverse_versification(tmp_path)
    assert ("ESG", 1, 1, "") in sub._map_to_org
    assert sub._map_to_org[("ESG", 1, 1, "")] == (
        ("ESG", 1, 1, "a"),
        ("ESG", 1, 1, "a"),
    )


def test_map_verse_with_subverse(tmp_path: pathlib.Path) -> None:
    """Test mapping a verse that maps to a subverse location."""
    sub = _subverse_versification(tmp_path)
    org = Versification.named("org")
    assert sub.map_verse("ESG", 8, 32, org) == ("ESG", 8, 12, "u")


def test_map_verse_subverse_roundtrip(tmp_path: pathlib.Path) -> None:
    """Test round-tripping a subverse mapping sub -> org -> sub."""
    sub = _subverse_versification(tmp_path)
    org = Versification.named("org")
    result = sub.map_verse("ESG", 8, 32, org)
    assert result == ("ESG", 8, 12, "u")
    back = org.map_verse(result[0], result[1], result[2], sub, subverse=result[3])
    assert back == ("ESG", 8, 32, "")


def test_map_verse_vulgate_esther_additions() -> None:
    """Vulgate Esther's 16-chapter numbering maps to integrated Greek Esther.

    The printed Vulgate gathers the Greek additions at the end as chapters
    10:4-16; they belong at their integrated ESG positions, not at the naive
    identity locations the old data assumed. Regression for a mapping that sent
    the additions (and the Hebrew verses they displace) to the wrong verses.
    """
    vul = Versification.named("vulgata")
    eng = Versification.named("eng")
    # Addition A, B, C, D, E, F respectively.
    assert vul.map_verse("EST", 11, 2, eng) == ("ESG", 1, 1, "")
    assert vul.map_verse("EST", 13, 8, eng) == ("ESG", 4, 18, "")
    assert vul.map_verse("EST", 14, 3, eng) == ("ESG", 4, 31, "")
    assert vul.map_verse("EST", 15, 1, eng) == ("ESG", 5, 1, "")
    assert vul.map_verse("EST", 16, 24, eng) == ("ESG", 8, 36, "")
    assert vul.map_verse("EST", 10, 4, eng) == ("ESG", 10, 4, "")


def test_map_verse_vulgate_esther_displaced_hebrew() -> None:
    """Hebrew verses displaced by an inserted addition map past the addition.

    The Hebrew text of Esther 1 follows Addition A, so it lands at ESG 1:18-39;
    the tails of chapters 8 and 10 (and the 11:1 colophon) likewise shift.
    """
    vul = Versification.named("vulgata")
    org = Versification.named("org")
    assert vul.map_verse("EST", 1, 1, org) == ("ESG", 1, 18, "")
    assert vul.map_verse("EST", 8, 17, org) == ("ESG", 8, 41, "")
    assert vul.map_verse("EST", 11, 1, org) == ("ESG", 10, 14, "")


def test_map_verse_vulgate_esther_roundtrip() -> None:
    """Vulgate Esther additions round-trip cleanly through org."""
    vul = Versification.named("vulgata")
    org = Versification.named("org")
    for chapter, verse in [(11, 2), (13, 8), (14, 19), (15, 16), (16, 24), (10, 4)]:
        mapped = vul.map_verse("EST", chapter, verse, org)
        assert mapped is not None
        back = org.map_verse(mapped[0], mapped[1], mapped[2], vul, subverse=mapped[3])
        assert back == ("EST", chapter, verse, "")


def test_map_verse_portion_subverse_carried_through_1_to_1() -> None:
    """A portion-of-verse subverse survives a 1:1 mapping (case 2)."""
    eng = Versification.named("eng")
    vul = Versification.named("vulgata")
    # Ps 45:15b (eng) is Ps 44:16b (vulgata); "b" is a line within the verse.
    assert eng.map_verse("PSA", 45, 15, vul, subverse="b") == ("PSA", 44, 16, "b")


def test_map_verse_portion_subverse_carried_through_identity() -> None:
    """A portion-of-verse subverse survives an unmapped (identity) verse."""
    eng = Versification.named("eng")
    org = Versification.named("org")
    assert eng.map_verse("GEN", 1, 1, org, subverse="a") == ("GEN", 1, 1, "a")


def test_map_verse_portion_subverse_discarded_1_to_n() -> None:
    """A portion-of-verse subverse is discarded across a 1:N mapping."""
    rsc = Versification.named("rsc")
    org = Versification.named("org")
    # PSA 141:0 (rsc) explodes into PSA 142:0-1 (org); the line is ambiguous.
    assert rsc.map_verse("PSA", 141, 0, org, subverse="b") == ("PSA", 142, 0, "")


def test_map_verse_portion_subverse_discarded_n_to_1() -> None:
    """A portion-of-verse subverse is discarded across an N:1 mapping."""
    rsc = Versification.named("rsc")
    org = Versification.named("org")
    # PSA 89:0-1 (rsc) collapses into PSA 90:0 (org); the line is ambiguous.
    assert rsc.map_verse("PSA", 89, 1, org, subverse="b") == ("PSA", 90, 0, "")


def test_mismatched_mapping_data_loaded() -> None:
    """Test that mismatched-size mappedVerses entries are loaded."""
    rsc = Versification.named("rsc")
    # PSA 141:0 in rsc maps to PSA 142:0-1 in org (1:2 mapping)
    assert rsc._map_to_org[("PSA", 141, 0, "")] == (
        ("PSA", 142, 0, ""),
        ("PSA", 142, 1, ""),
    )


def test_map_verse_1_to_n_start() -> None:
    """Test mapping start of a 1:N verse mapping."""
    rsc = Versification.named("rsc")
    org = Versification.named("org")
    assert rsc.map_verse("PSA", 141, 0, org, end=False) == ("PSA", 142, 0, "")


def test_map_verse_1_to_n_end() -> None:
    """Test mapping end of a 1:N verse mapping."""
    rsc = Versification.named("rsc")
    org = Versification.named("org")
    assert rsc.map_verse("PSA", 141, 0, org, end=True) == ("PSA", 142, 1, "")


def test_map_verse_n_to_1() -> None:
    """Test mapping an N:1 verse mapping returns same result for start and end."""
    rsc = Versification.named("rsc")
    org = Versification.named("org")
    # PSA 89:0-1 in rsc maps to PSA 90:0 in org
    assert rsc.map_verse("PSA", 89, 1, org, end=False) == ("PSA", 90, 0, "")
    assert rsc.map_verse("PSA", 89, 1, org, end=True) == ("PSA", 90, 0, "")


def test_no_warnings_loading_versifications(caplog: pytest.LogCaptureFixture) -> None:
    """Test that loading all standard versifications produces no warnings."""
    identifiers = [
        "org",
        "eng",
        "lxx",
        "vulgata",
        "nova_vulgata",
        "nabre",
        "rsc",
        "rso",
    ]
    with caplog.at_level(logging.WARNING, logger="versiref.versification"):
        for ident in identifiers:
            Versification.named(ident)
    assert len(caplog.records) == 0


def test_available_names_discovers_bundled_versifications() -> None:
    """available_names() should expose the canonical bundled versifications, sorted."""
    available = Versification.available_names()
    assert available
    assert available == sorted(available)
    assert {"org", "eng", "lxx", "vulgata"}.issubset(available)


def test_available_names_round_trip_through_named() -> None:
    """Every identifier from available_names() must load via named()."""
    for ident in Versification.available_names():
        Versification.named(ident)


def test_map_verse_inserted_verse_answering_to_two() -> None:
    """An inserted verse mapping to two verses must not capture its base verse.

    Swete divides Addition E where Rahlfs does not, so the CEI's ESG 8:12u is
    org's ESG 8:34-35. A one-to-many entry used to drop the source's subverse
    and key itself on the base verse, which sent plain ESG 8:12 to 8:34-35 as
    well; it belongs at 8:12.
    """
    cei = Versification.named("cei")
    org = Versification.named("org")
    assert cei.map_verse("ESG", 8, 12, org, "u") == ("ESG", 8, 34, "")
    assert cei.map_verse("ESG", 8, 12, org, "u", end=True) == ("ESG", 8, 35, "")
    assert cei.map_verse("ESG", 8, 12, org) == ("ESG", 8, 12, "")
    assert org.map_verse("ESG", 8, 34, cei) == ("ESG", 8, 12, "")


def test_cei_greek_esther_covers_org_exactly_once() -> None:
    """The CEI's Greek Esther accounts for every verse of org's, exactly once.

    org numbers the additions as Swete divides them, which is finer than Rahlfs
    (whose numbering the CEI follows) in Additions C, D and E: six of Rahlfs'
    verses answer to two or three of org's in chapter 4, six in chapter 5, and
    three in chapter 8. Every chapter must still tile org's exactly, with no
    verse left uncovered and none claimed twice.
    """
    cei = Versification.named("cei")
    org = Versification.named("org")
    for chapter in range(1, len(cei.max_verses["ESG"]) + 1):
        covered: list[int] = []
        for verse in range(1, cei.last_verse("ESG", chapter) + 1):
            ordinals = cei._partial_verses.get(("ESG", chapter, verse), {})
            for subverse in [""] + sorted(ordinals, key=lambda s: ordinals[s]):
                start = cei.map_verse("ESG", chapter, verse, org, subverse)
                end = cei.map_verse("ESG", chapter, verse, org, subverse, end=True)
                assert start is not None and end is not None
                covered.extend(range(start[2], end[2] + 1))
        expected = list(range(1, org.last_verse("ESG", chapter) + 1))
        assert sorted(covered) == expected, f"ESG {chapter} does not tile org's"


def test_map_verse_greek_esther_additions_c_and_d() -> None:
    """Rahlfs' verses that Swete divides map to ranges, aligned to the Greek.

    Rahlfs 4:17c is Swete C:3-4 (org 4:20-21) and 5:1a is D:2-4 (org 5:2-4);
    the verses around them stay one-to-one. The Hebrew text after Addition D
    follows it, so 5:3-14 lands at org 5:17-28.
    """
    cei = Versification.named("cei")
    org = Versification.named("org")

    def span(chapter: int, verse: int, subverse: str = "") -> tuple[int, int]:
        start = cei.map_verse("ESG", chapter, verse, org, subverse)
        end = cei.map_verse("ESG", chapter, verse, org, subverse, end=True)
        assert start is not None and end is not None
        return start[2], end[2]

    assert span(4, 17, "b") == (19, 19)
    assert span(4, 17, "c") == (20, 21)
    assert span(4, 17, "d") == (22, 23)
    assert span(4, 17, "e") == (24, 24)
    assert span(5, 1, "a") == (2, 4)
    assert span(5, 1, "b") == (5, 5)
    assert span(5, 2) == (12, 12)
    assert span(5, 3) == (17, 17)
    assert span(5, 14) == (28, 28)


def test_vulgate_daniel_deuterocanonical_chapter_lengths() -> None:
    """The Clementine has Dan 13:65 and 14:42; the Nova Vulgata has 13:64 and 14:42.

    Weber's Dan 13:65 is the Nova Vulgata's 14:1, so the Nova Vulgata's chapter
    14 runs one verse longer and its chapter 13 one verse shorter. The
    Clementine follows Weber and adds a further 14:42 that neither of the
    others prints.
    """
    vul = Versification.named("vulgata")
    nov = Versification.named("nova_vulgata")
    assert vul.last_verse("DAN", 13) == 65
    assert vul.last_verse("DAN", 14) == 42
    assert nov.last_verse("DAN", 13) == 64
    assert nov.last_verse("DAN", 14) == 42


def test_map_verse_vulgate_daniel_bel() -> None:
    """The Clementine's Bel runs from Dan 13:65, one verse ahead of the Greek."""
    vul = Versification.named("vulgata")
    org = Versification.named("org")
    assert vul.map_verse("DAN", 13, 64, org) == ("SUS", 1, 64, "")
    assert vul.map_verse("DAN", 13, 65, org) == ("BEL", 1, 1, "")
    assert vul.map_verse("DAN", 14, 1, org) == ("BEL", 1, 2, "")
    assert vul.map_verse("DAN", 14, 41, org) == ("BEL", 1, 42, "")
    # The Clementine's extra closing verse has no Greek counterpart of its own.
    assert vul.map_verse("DAN", 14, 42, org) == ("BEL", 1, 42, "")
    assert org.map_verse("BEL", 1, 1, vul) == ("DAN", 13, 65, "")
    assert org.map_verse("BEL", 1, 42, vul) == ("DAN", 14, 41, "")


def test_map_verse_nova_vulgata_daniel_bel() -> None:
    """The Nova Vulgata's chapter 14 is Bel verse for verse."""
    nov = Versification.named("nova_vulgata")
    org = Versification.named("org")
    assert nov.map_verse("DAN", 13, 64, org) == ("SUS", 1, 64, "")
    assert nov.map_verse("DAN", 14, 1, org) == ("BEL", 1, 1, "")
    assert nov.map_verse("DAN", 14, 42, org) == ("BEL", 1, 42, "")
    assert org.map_verse("BEL", 1, 1, nov) == ("DAN", 14, 1, "")


def test_map_verse_daniel_between_vulgates() -> None:
    """The Vulgates differ by one verse from Bel onward."""
    vul = Versification.named("vulgata")
    nov = Versification.named("nova_vulgata")
    assert vul.map_verse("DAN", 13, 64, nov) == ("DAN", 13, 64, "")
    assert vul.map_verse("DAN", 13, 65, nov) == ("DAN", 14, 1, "")
    assert vul.map_verse("DAN", 14, 41, nov) == ("DAN", 14, 42, "")
    assert nov.map_verse("DAN", 14, 1, vul) == ("DAN", 13, 65, "")


def test_map_from_org_ignores_parallel_greek_daniel() -> None:
    """DAG does not claim org's Daniel deuterocanon on the way back.

    DAG numbers Susanna, the Song of the Three and Bel continuously alongside
    DAN, and its entries would otherwise capture the inverse mapping, so that
    org's BEL and SUS returned as a DAG reference no style can name.
    """
    org = Versification.named("org")
    for name, expected in [
        ("vulgata", ("DAN", 13, 65, "")),
        ("nova_vulgata", ("DAN", 14, 1, "")),
        ("eng", ("BEL", 1, 1, "")),
        ("lxx", ("BEL", 1, 1, "")),
    ]:
        target = Versification.named(name)
        assert org.map_verse("BEL", 1, 1, target) == expected
    assert org.map_verse("SUS", 1, 1, Versification.named("eng")) == ("SUS", 1, 1, "")


def test_sirach_has_fifty_one_chapters_in_both_vulgates() -> None:
    """Neither Vulgate prints the Oratio Salomonis as a chapter 52 of Sirach."""
    for name in ("vulgata", "nova_vulgata"):
        assert Versification.named(name).last_verse("SIR", 52) == -1
        assert Versification.named(name).last_verse("SIR", 51) == 38


def test_nova_vulgata_psalter_follows_the_hebrew_numbering() -> None:
    """The Nova Vulgata numbers the psalms as the Hebrew does, not as the Vulgate.

    Its data had been copied wholesale from `vulgata`, which numbers them as
    the Greek does: Psalm 9 ran to 39 verses (the Hebrew 9 and 10 together) and
    the Miserere was Psalm 50. The headings of the printed text give the Hebrew
    number first and the Vulgate's in parentheses ("PSALMUS 51 (50)").
    """
    nov = Versification.named("nova_vulgata")
    vul = Versification.named("vulgata")
    assert nov.last_verse("PSA", 9) == 21
    assert nov.last_verse("PSA", 10) == 18
    assert nov.last_verse("PSA", 51) == 21
    assert nov.last_verse("PSA", 116) == 19
    assert nov.last_verse("PSA", 119) == 176
    # The Vulgate's own numbering, for contrast.
    assert vul.last_verse("PSA", 9) == 39
    assert vul.last_verse("PSA", 50) == 21


def test_nova_vulgata_psalter_titles_are_verses() -> None:
    """Psalm titles count as verses, as in the Hebrew and in the Vulgate."""
    nov = Versification.named("nova_vulgata")
    org = Versification.named("org")
    # Ps 51:1-2 is the title; the Miserere itself begins at verse 3.
    assert nov.map_verse("PSA", 51, 1, org) == ("PSA", 51, 1, "")
    assert nov.map_verse("PSA", 51, 3, org) == ("PSA", 51, 3, "")


def test_map_verse_nova_vulgata_psalms_to_vulgate() -> None:
    """A Nova Vulgata psalm maps to the Vulgate's number for it."""
    nov = Versification.named("nova_vulgata")
    vul = Versification.named("vulgata")
    assert nov.map_verse("PSA", 51, 3, vul) == ("PSA", 50, 3, "")
    assert vul.map_verse("PSA", 50, 3, nov) == ("PSA", 51, 3, "")
    assert nov.map_verse("PSA", 23, 1, vul) == ("PSA", 22, 1, "")
    # The Hebrew 9 and 10 are the Vulgate's single Psalm 9.
    assert nov.map_verse("PSA", 10, 1, vul) == ("PSA", 9, 22, "")
    # Psalms the two number alike.
    assert nov.map_verse("PSA", 119, 1, vul) == ("PSA", 118, 1, "")
    assert nov.map_verse("PSA", 148, 1, vul) == ("PSA", 148, 1, "")


def test_nova_vulgata_psalms_divided_differently_from_the_hebrew() -> None:
    """Six psalms divide their verses differently from the Hebrew.

    Five join a pair the Hebrew keeps apart — always the closing verse, except
    in Psalm 60, where the join falls at verse 12 and the last verse shifts —
    and Psalm 94 splits the Hebrew's final verse in two.
    """
    nov = Versification.named("nova_vulgata")
    org = Versification.named("org")

    def span(chapter: int, verse: int) -> tuple[int, int]:
        start = nov.map_verse("PSA", chapter, verse, org)
        end = nov.map_verse("PSA", chapter, verse, org, end=True)
        assert start is not None and end is not None
        return start[2], end[2]

    assert span(12, 8) == (8, 9)
    assert span(44, 26) == (26, 27)
    assert span(60, 12) == (12, 13)
    assert span(60, 13) == (14, 14)
    assert span(150, 5) == (5, 6)
    assert nov.map_verse("PSA", 94, 23, org) == ("PSA", 94, 23, "")
    assert nov.map_verse("PSA", 94, 24, org) == ("PSA", 94, 23, "")
    assert org.map_verse("PSA", 94, 23, nov, end=True) == ("PSA", 94, 24, "")
    # The colophon closing Book II is not printed as a verse.
    assert nov.last_verse("PSA", 72) == 19
    assert org.map_verse("PSA", 72, 20, nov) is None


def test_nova_vulgata_psalms_otherwise_agree_with_org() -> None:
    """Every other psalm matches org verse for verse, so it needs no mapping."""
    nov = Versification.named("nova_vulgata")
    org = Versification.named("org")
    divergent = {12, 44, 60, 72, 94, 150}
    for chapter in range(1, 151):
        last = nov.last_verse("PSA", chapter)
        assert last == org.last_verse("PSA", chapter) or chapter in divergent
        if chapter in divergent:
            continue
        for verse in (1, last):
            assert nov.map_verse("PSA", chapter, verse, org) == (
                "PSA",
                chapter,
                verse,
                "",
            )


def test_clementine_merged_closing_verses() -> None:
    """The Clementine merges four closing verses that the Greek keeps apart.

    Genesis 5:31 carries Noah's begetting of Shem, Ham and Japheth, John 11:56
    carries the chief priests' order, and the Clementine ends 2 Corinthians 1
    and 3 John a verse earlier than the Greek. The Nova Vulgata keeps all four
    apart.
    """
    vul = Versification.named("vulgata")
    org = Versification.named("org")

    def span(book: str, chapter: int, verse: int) -> tuple[int, int]:
        start = vul.map_verse(book, chapter, verse, org)
        end = vul.map_verse(book, chapter, verse, org, end=True)
        assert start is not None and end is not None
        return start[2], end[2]

    assert vul.last_verse("GEN", 5) == 31
    assert vul.last_verse("JHN", 11) == 56
    assert vul.last_verse("2CO", 1) == 23
    assert vul.last_verse("3JN", 1) == 14
    assert span("GEN", 5, 31) == (31, 32)
    assert span("JHN", 11, 56) == (56, 57)
    assert span("2CO", 1, 23) == (23, 24)
    assert span("3JN", 1, 14) == (14, 15)
    assert org.map_verse("GEN", 5, 32, vul) == ("GEN", 5, 31, "")
    assert org.map_verse("JHN", 11, 57, vul) == ("JHN", 11, 56, "")
    assert org.map_verse("2CO", 1, 24, vul) == ("2CO", 1, 23, "")
    assert org.map_verse("3JN", 1, 15, vul) == ("3JN", 1, 14, "")


def test_nova_vulgata_keeps_the_verses_the_clementine_merges() -> None:
    """The Nova Vulgata divides all four as the Greek does."""
    nov = Versification.named("nova_vulgata")
    assert nov.last_verse("GEN", 5) == 32
    assert nov.last_verse("JHN", 11) == 57
    assert nov.last_verse("2CO", 1) == 24
    assert nov.last_verse("3JN", 1) == 15
