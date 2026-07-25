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


def test_cei_greek_esther_covers_org_chapter_eight() -> None:
    """The CEI's Greek Esther 8 accounts for every verse of org's, exactly once.

    Swete's 8:1-12 + E:1-24 + 8:13-17 is org's 41 verses, so the additions fill
    org 8:13-36 and the verses after them org 8:37-41.
    """
    cei = Versification.named("cei")
    org = Versification.named("org")
    covered: list[int] = []
    for verse in range(1, cei.last_verse("ESG", 8) + 1):
        ordinals = cei._partial_verses.get(("ESG", 8, verse), {})
        for subverse in [""] + sorted(ordinals, key=lambda s: ordinals[s]):
            start = cei.map_verse("ESG", 8, verse, org, subverse)
            end = cei.map_verse("ESG", 8, verse, org, subverse, end=True)
            assert start is not None and end is not None
            covered.extend(range(start[2], end[2] + 1))
    assert sorted(covered) == list(range(1, org.last_verse("ESG", 8) + 1))
