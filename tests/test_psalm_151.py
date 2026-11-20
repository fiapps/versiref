"""Psalm 151 uses the Psalms name even when stored as the separate PS2 book."""

import pytest

from versiref import BibleRef, RefParser, RefPoint, RefStyle, VerseRange, Versification

SEPARATE_PSALM = ["org", "eng", "vulgata", "nova_vulgata", "douay-rheims"]


@pytest.mark.parametrize("versification_name", [*SEPARATE_PSALM, "lxx"])
@pytest.mark.parametrize(
    ("verse", "end_verse", "expected"),
    [(None, None, "Ps 151"), (1, None, "Ps 151:1"), (1, 3, "Ps 151:1–3")],
)
def test_format_separate_psalm(
    versification_name: str, verse: int | None, end_verse: int | None, expected: str
) -> None:
    """Separate PS2 locations print their public psalm number, not chapter 1."""
    reference = BibleRef.for_range(
        "PS2",
        1,
        verse,
        end_verse=end_verse,
        versification=Versification.named(versification_name),
    )
    assert reference.format(RefStyle.named("en-sbl")) == expected
    assert reference.ranges[0].start.book == "PS2"


@pytest.mark.parametrize("style_name", RefStyle.available_names())
def test_psalm_round_trip_in_each_style(style_name: str) -> None:
    """Each style's names, separators and chapter numerals work for Psalm 151."""
    style = RefStyle.named(style_name)
    versification = Versification.named("org")
    reference = BibleRef.for_range(
        "PS2", 1, 1, end_verse=3, versification=versification
    )
    text = reference.format(style)
    assert RefParser(style, versification).parse(text) == reference


@pytest.mark.parametrize("versification_name", SEPARATE_PSALM)
@pytest.mark.parametrize(
    ("text", "start", "end"),
    [
        ("Ps 151", RefPoint("PS2", 1), RefPoint("PS2", 1)),
        ("Ps 151:1", RefPoint("PS2", 1, 1), RefPoint("PS2", 1, 1)),
        ("Ps 151:1–3", RefPoint("PS2", 1, 1), RefPoint("PS2", 1, 3)),
        ("Ps 151:1a–c", RefPoint("PS2", 1, 1, "a"), RefPoint("PS2", 1, 1, "c")),
        ("Ps 151:2ff", RefPoint("PS2", 1, 2), RefPoint("PS2", 1)),
    ],
)
def test_parse_separate_psalm(
    versification_name: str, text: str, start: RefPoint, end: RefPoint
) -> None:
    """A psalm missing from PSA resolves to PS2 where that separate book exists."""
    versification = Versification.named(versification_name)
    reference = RefParser(RefStyle.named("en-sbl"), versification).parse(text)
    assert reference is not None
    assert reference.ranges == (VerseRange(start, end, text),)
    assert reference.invalid_reason() is None


@pytest.mark.parametrize("versification_name", ["lxx", "rso"])
def test_native_psalm_151_keeps_its_book(versification_name: str) -> None:
    """A native PSA chapter 151 remains PSA, including in a trailing designator."""
    style = RefStyle.named("en-sbl")
    style.also_recognize_versifications({"Native": versification_name})
    parser = RefParser(style, Versification.named("org"))
    reference = parser.parse("Ps 151:1 Native")
    assert reference is not None
    assert reference.ranges[0].start == RefPoint("PSA", 151, 1)
    assert reference.invalid_reason() is None
    assert reference.format(style) == "Ps 151:1"


def test_trailing_designator_selects_separate_book() -> None:
    """Normalization uses the selected versification, after reading a designator."""
    style = RefStyle.named("en-sbl")
    style.also_recognize_versifications({"Original": "org"})
    reference = RefParser(style, Versification.named("lxx")).parse("Ps 151:1 Original")
    assert reference is not None
    assert reference.ranges[0].start == RefPoint("PS2", 1, 1)
    assert reference.versification is Versification.named("org")


def test_psalm_151_in_a_list() -> None:
    """Shared plural names, implicit verses and range ends retain their meaning."""
    style = RefStyle.named("en-sbl")
    versification = Versification.named("org")
    reference = BibleRef(
        [
            VerseRange(RefPoint("PSA", 150, 1), RefPoint("PSA", 150, 1)),
            VerseRange(RefPoint("PS2", 1, 1), RefPoint("PS2", 1, 1)),
            VerseRange(RefPoint("PS2", 1, 3), RefPoint("PS2", 1, 3)),
        ],
        versification,
    )
    text = reference.format(style)
    assert text == "Pss 150:1; 151:1, 3"
    assert RefParser(style, versification).parse(text) == reference
    expected_keys = [
        pair
        for book, chapter, verse in [("PSA", 150, 1), ("PS2", 1, 1), ("PS2", 1, 3)]
        for pair in BibleRef.for_range(
            book, chapter, verse, versification=versification
        ).range_keys()
    ]
    assert list(reference.range_keys()) == expected_keys
    mapped = reference.map_to(Versification.named("lxx"))
    assert mapped is not None
    assert mapped.map_to(versification) == reference


def test_whole_separate_book_prints_as_a_psalm() -> None:
    """A whole PS2 book and its sole chapter have the same formatted extent."""
    versification = Versification.named("org")
    reference = BibleRef([VerseRange(RefPoint("PS2"), RefPoint("PS2"))], versification)
    style = RefStyle.named("en-sbl")
    assert reference.format(style) == "Ps 151"
    reparsed = RefParser(style, versification).parse("Ps 151")
    assert reparsed is not None
    assert list(reparsed.range_keys()) == list(reference.range_keys())


@pytest.mark.parametrize("explicit_names", [False, True])
def test_ps2_names_are_ignored(explicit_names: bool) -> None:
    """PS2 does not acquire an independent name through style APIs."""
    style = RefStyle(
        names={"PSA": "Ps", "PSAS": "Pss", "PS2": "Ignored"},
        recognized_names={"Ps": "PSA", "Pss": "PSAS", "Ignored": "PS2"}
        if explicit_names
        else {},
    )
    style.override_names({"PS2": "Still ignored"})
    style.also_recognize({"Also ignored": "PS2"})
    assert style.book_name("PS2") == "Ps"
    assert style.book_name("PS2", plural=True) == "Pss"
    parser = RefParser(style, Versification.named("org"))
    assert parser.parse("Ignored 1", silent=True) is None
    assert parser.parse("Still ignored 1", silent=True) is None
    assert parser.parse("Also ignored 1", silent=True) is None
    assert parser.parse("Ps 151:1") is not None


def test_invalid_psalm_and_other_single_chapter_books() -> None:
    """Validation and ordinary one-chapter book formatting keep their behavior."""
    style = RefStyle.named("en-sbl")
    versification = Versification.named("org")
    parser = RefParser(style, versification)
    invalid = parser.parse("Ps 151:8")
    assert invalid is not None
    assert invalid.invalid_reason() is not None
    ordinary = parser.parse("Jude 3")
    assert ordinary is not None
    assert ordinary.format(style) == "Jude 3"
    assert ordinary.ranges[0].start == RefPoint("JUD", 1, 3)


@pytest.mark.parametrize("text", ["Pss 150:1–151:3", "Pss 150–151", "Ps 150:6–151:1"])
def test_separate_book_boundary_does_not_become_a_valid_cross_book_range(
    text: str,
) -> None:
    """An unsupported psalm boundary must not silently include intervening books."""
    versification = Versification.named("org")
    reference = RefParser(RefStyle.named("en-sbl"), versification).parse(text)
    assert reference is not None
    assert reference.invalid_reason() is not None
    mapped = reference.map_to(Versification.named("lxx"))
    assert mapped is not None
    assert mapped.invalid_reason() is None
    assert mapped.ranges[0].start.book == mapped.ranges[0].end.book == "PSA"
    ((proverbs, _),) = BibleRef.for_range(
        "PRO", 1, 1, versification=versification
    ).range_keys()
    assert not any(start <= proverbs <= end for start, end in reference.range_keys())


def test_format_rejects_ambiguous_cross_book_ps2_range() -> None:
    """Psalm notation must not hide a range that includes intervening books."""
    reference = BibleRef(
        [VerseRange(RefPoint("PSA", 150, 1), RefPoint("PS2", 1, 3))],
        Versification.named("org"),
    )
    with pytest.raises(ValueError, match="cross-book range involving PS2"):
        reference.format(RefStyle.named("en-sbl"))


def test_scan_and_substitute_psalm_list() -> None:
    """Separate-range source offsets survive normalizing the Psalm 151 book."""
    parser = RefParser(RefStyle.named("en-sbl"), Versification.named("org"))
    text = "Read Pss 150:1; 151:1, 3."
    matches = list(parser.scan_string(text, as_ranges=True))
    assert len(matches) == 3
    for reference, start, end in matches:
        assert text[start:end] == reference.original_text
        assert reference.invalid_reason() is None
    assert [reference.ranges[0].start.book for reference, _, _ in matches] == [
        "PSA",
        "PS2",
        "PS2",
    ]
    assert parser.sub_refs(text, lambda ref: "X", as_ranges=True) == "Read X; X, X."
