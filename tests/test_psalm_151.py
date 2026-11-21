"""Psalm 151 uses the Psalms name even when stored as the separate PS2 book."""

import pytest

from versiref import BibleRef, RefParser, RefPoint, RefStyle, VerseRange, Versification


@pytest.mark.parametrize(
    ("verse", "end_verse", "expected"),
    [(None, None, "Ps 151"), (1, None, "Ps 151:1"), (1, 3, "Ps 151:1–3")],
)
def test_format_separate_psalm(
    verse: int | None, end_verse: int | None, expected: str
) -> None:
    """Separate PS2 locations print their public psalm number, not chapter 1."""
    reference = BibleRef.for_range(
        "PS2",
        1,
        verse,
        end_verse=end_verse,
        versification=Versification.named("org"),
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


@pytest.mark.parametrize(
    ("text", "start", "end"),
    [
        ("Ps 151", RefPoint("PS2", 1), RefPoint("PS2", 1)),
        ("Ps 151:1–3", RefPoint("PS2", 1, 1), RefPoint("PS2", 1, 3)),
        ("Ps 151:2ff", RefPoint("PS2", 1, 2), RefPoint("PS2", 1)),
    ],
)
def test_parse_separate_psalm(text: str, start: RefPoint, end: RefPoint) -> None:
    """A psalm missing from PSA resolves to PS2 where that separate book exists."""
    versification = Versification.named("org")
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
    if reference.versification is not None and reference.versification.includes("PS2"):
        separate = BibleRef.for_range(
            "PS2", 1, 1, versification=reference.versification
        )
        assert separate.format(style) == reference.format(style)
        assert parser.parse(separate.format(style) + " Native") == reference
        assert separate.ranges[0].start == RefPoint("PS2", 1, 1)


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


@pytest.mark.parametrize(
    "recognized_names",
    [None, {"Ps": "PSA", "Pss": "PSAS", "Ignored": "PS2"}, {"Ignored": "PS2"}],
)
def test_ps2_names_are_ignored(recognized_names: dict[str, str] | None) -> None:
    """PS2 does not acquire an independent name through style APIs."""
    style = RefStyle(
        names={"PSA": "Ps", "PSAS": "Pss", "PS2": "Ignored"},
        recognized_names=recognized_names or {},
    )
    style.override_names({"PS2": "Still ignored"})
    style.also_recognize({"Also ignored": "PS2"})
    assert style.book_name("PS2") == "Ps"
    assert style.book_name("PS2", plural=True) == "Pss"
    parser = RefParser(style, Versification.named("org"))
    assert parser.parse("Ignored 1", silent=True) is None
    assert parser.parse("Still ignored 1", silent=True) is None
    assert parser.parse("Also ignored 1", silent=True) is None
    if recognized_names == {"Ignored": "PS2"}:
        assert style.recognized_names == {}
        assert parser.parse("Ps 151:1", silent=True) is None
    else:
        assert parser.parse("Ps 151:1") is not None


def test_invalid_psalm_reports_its_public_chapter() -> None:
    """A styled diagnostic uses the chapter the user wrote, not PS2 chapter 1."""
    style = RefStyle.named("en-sbl")
    versification = Versification.named("org")
    parser = RefParser(style, versification)
    invalid = parser.parse("Ps 151:8")
    assert invalid is not None
    style.names["PS2"] = "Ignored mutation"
    assert invalid.invalid_reason(style) == "Ps 151 has no verse 8 (only 7 verses)"
    assert invalid.invalid_reason() == "PS2 1 has no verse 8 (only 7 verses)"


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


@pytest.mark.parametrize("versification_name", [None, "org"])
def test_string_of_hand_built_ps2_range_uses_raw_book_ids(
    versification_name: str | None,
) -> None:
    """Logging an unformattable reference must preserve both raw endpoints."""
    reference = BibleRef(
        [VerseRange(RefPoint("PSA", 150, 1), RefPoint("PS2", 1, 3))],
        Versification.named(versification_name) if versification_name else None,
    )
    text = str(reference)
    assert "PSA" in text
    assert "PS2" in text
    assert "150" in text
    assert "Ps 151" not in text
    with pytest.raises(ValueError, match="cross-book range involving PS2"):
        reference.format(RefStyle.named("en-sbl"))
