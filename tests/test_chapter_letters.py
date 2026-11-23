"""Test lettered chapters (the NABRE's Esther A–F) in parsing, formatting and mapping."""

import pytest

from versiref import BibleRef, RefParser, RefPoint, RefStyle, Sensitivity, Versification

# Where each lettered chapter stands among the numbered verses of Esther, and
# how many verses it has.
ADDITIONS = {
    "A": (1, 1, 17),
    "B": (3, 13, 7),
    "C": (4, 17, 30),
    "D": (5, 1, 16),
    "E": (8, 12, 24),
    "F": (10, 3, 11),
}


@pytest.fixture
def parser() -> RefParser:
    """Return a parser for the NABRE style and versification."""
    return RefParser(RefStyle.named("en-nabre"), Versification.named("nabre"))


def _points(ref: BibleRef) -> list[tuple[str, str]]:
    def text(point: RefPoint) -> str:
        if point.chapter is None:
            return ""
        if point.verse is None:
            return str(point.chapter)
        return f"{point.chapter}:{point.verse}{point.subverse}"

    return [(text(r.start), text(r.end)) for r in ref.ranges]


@pytest.mark.parametrize(
    ("text", "points", "formatted"),
    [
        ("Esth C:12", [("4:17C12", "4:17C12")], "Esth C:12"),
        ("Esth C:12-30", [("4:17C12", "4:17C30")], "Esth C:12–30"),
        ("Esth A:1–17", [("1:1A1", "1:1A17")], "Esth A:1–17"),
        ("Esth C:25–D:2", [("4:17C25", "5:1D2")], "Esth C:25–D:2"),
        (
            "Esth C:12, 14, 25–30",
            [("4:17C12", "4:17C12"), ("4:17C14", "4:17C14"), ("4:17C25", "4:17C30")],
            "Esth C:12, 14, 25–30",
        ),
        ("Esth B:1ff", [("3:13B1", "3:13B")], "Esth B:1ff"),
        ("Esth B:1f", [("3:13B1", "3:13B2")], "Esth B:1–2"),
        # A part of a verse of a lettered chapter
        ("Esth C:12a", [("4:17C12a", "4:17C12a")], "Esth C:12a"),
        ("Esth C:12a–c", [("4:17C12a", "4:17C12c")], "Esth C:12a–c"),
        # Every recognized name of the book takes letters
        ("Esther C:12", [("4:17C12", "4:17C12")], "Esth C:12"),
        ("Est D:5", [("5:1D5", "5:1D5")], "Esth D:5"),
        # Whole lettered chapters
        ("Esth A", [("1:1A", "1:1A")], "Esth A"),
        ("Esth A–C", [("1:1A", "4:17C")], "Esth A–C"),
        # Lettered and numbered chapters in one range or one reference
        ("Esth 4:1–C:30", [("4:1", "4:17C30")], "Esth 4:1–C:30"),
        ("Esth A:1–1:3", [("1:1A1", "1:3")], "Esth A:1–1:3"),
        ("Esth 4–C", [("4", "4:17C")], "Esth 4–C"),
        ("Esth C–5", [("4:17C", "5")], "Esth C–5"),
        ("Esth D–5", [("5:1D", "5")], "Esth D–5"),
        ("Esth B:1; 3:14", [("3:13B1", "3:13B1"), ("3:14", "3:14")], "Esth B:1; 3:14"),
        ("Esth 2:21; C:4", [("2:21", "2:21"), ("4:17C4", "4:17C4")], "Esth 2:21; C:4"),
        (
            "Esth C:5; D:3; 6:1",
            [("4:17C5", "4:17C5"), ("5:1D3", "5:1D3"), ("6:1", "6:1")],
            "Esth C:5; D:3; 6:1",
        ),
        # Numbered chapters are unaffected
        ("Esther 4:17", [("4:17", "4:17")], "Esth 4:17"),
        ("Esth 3", [("3", "3")], "Esth 3"),
        ("Esther", [("", "")], "Esth"),
    ],
)
def test_parse_and_format(
    parser: RefParser, text: str, points: list[tuple[str, str]], formatted: str
) -> None:
    """A lettered chapter is held within Esther and written with its letter."""
    ref = parser.parse(text)
    assert ref is not None
    assert ref.books() == ["EST"]
    assert _points(ref) == points
    assert ref.format(parser.style) == formatted
    assert ref.is_valid()


@pytest.mark.parametrize(
    ("text", "formatted"),
    [
        ("Est A:12; B:3", "Esth A:12; B:3"),
        ("Est A:12; 2:21", "Esth A:12; 2:21"),
        ("Est 2:21; C:4", "Esth 2:21; C:4"),
        ("Est A:12 ff; 2:21 ff; 6:1 ff", "Esth A:12ff; 2:21ff; 6:1ff"),
    ],
)
def test_scan_continues_between_lettered_and_numbered_chapters(
    parser: RefParser, text: str, formatted: str
) -> None:
    """A scan carries the book across lettered and numbered chapters alike."""
    content = f"See {text}."
    found = [
        (content[start:end], ref.format(parser.style))
        for ref, start, end in parser.scan_string(content)
    ]
    assert found == [(text, formatted)]


def test_letters_come_from_the_versification() -> None:
    """Lettered chapters parse in any style, but only with a versification that has them."""
    sbl = RefStyle.named("en-sbl")
    ref = RefParser(sbl, Versification.named("nabre")).parse("Esth C:12")
    assert ref is not None
    assert ref.format(sbl) == "Esth C:12"
    eng = RefParser(RefStyle.named("en-nabre"), Versification.named("eng"))
    assert eng.parse("Esth C:12", silent=True) is None


def test_style_key_is_ignored_with_a_warning() -> None:
    """A style definition's old chapter_letters key warns that it can be removed."""
    data = {"base": "en-sbl", "chapter_letters": {"ESG": ["A", "B", "C"]}}
    with pytest.warns(FutureWarning, match="chapter_letters"):
        style = RefStyle.from_dict(data)
    assert not hasattr(style, "chapter_letters")
    assert style.book_name("ESG") == "Add Esth"


def test_format_without_versification() -> None:
    """A lettered chapter formats without a versification."""
    style = RefStyle.named("en-sbl")
    verse = BibleRef.for_range("EST", 4, 17, start_subverse="C12")
    assert verse.format(style) == "Esth C:12"
    chapter = BibleRef.for_range("EST", 4, 17, start_subverse="C")
    assert chapter.format(style) == "Esth C"


def test_whole_chapters_and_following_verses(parser: RefParser) -> None:
    """A lettered chapter is a chapter, and "ff" runs to the end of it."""

    def parse(text: str) -> BibleRef:
        ref = parser.parse(text)
        assert ref is not None
        return ref

    assert parse("Esth C").is_whole_chapters()
    assert parse("Esth C–D").is_whole_chapters()
    assert parse("Esth 4–C").is_whole_chapters()
    assert not parse("Esth C:1–30").is_whole_chapters()
    following = parse("Esth B:1ff")
    assert following.ranges[0].has_following_verses()
    assert following.resolve_following_verses().format(parser.style) == "Esth B:1–7"
    assert not parse("Esth D–5").ranges[0].has_following_verses()


def test_scan_string(parser: RefParser) -> None:
    """Scanning picks out lettered references, and whole chapters only on request."""
    text = "Esther Also spoke, but see Esth C:12f and Esth 4:17 and Esth C for more."
    found = [text[start:end] for _, start, end in parser.scan_string(text)]
    assert found == ["Esth C:12f", "Esth 4:17"]
    found = [
        text[start:end]
        for _, start, end in parser.scan_string(text, sensitivity=Sensitivity.CHAPTER)
    ]
    assert found == ["Esth C:12f", "Esth 4:17", "Esth C"]


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("Esth C:31", "Esth C has no verse 31 (only 30 verses)"),
        ("Esth C:14–12", "Esth: range ends at an earlier verse than it starts"),
        ("Esth C:5–4:3", "Esth: range ends at an earlier verse than it starts"),
    ],
)
def test_invalid(parser: RefParser, text: str, reason: str) -> None:
    """A verse a lettered chapter lacks, or a range that runs backward, is invalid."""
    ref = parser.parse(text)
    assert ref is not None
    assert ref.invalid_reason(parser.style) == reason


def test_invalid_misplaced_letter() -> None:
    """A lettered verse must stand where the versification puts its chapter."""
    nabre = Versification.named("nabre")
    ref = BibleRef.for_range("EST", 4, 16, start_subverse="C12", versification=nabre)
    assert ref.invalid_reason() == "EST has no chapter C"
    ref = BibleRef.for_range("EST", 4, 17, start_subverse="G1", versification=nabre)
    assert ref.invalid_reason() == "EST has no chapter G"


def test_versification_lettered_chapters() -> None:
    """The nabre versification places Esther A–F and counts their verses."""
    nabre = Versification.named("nabre")
    assert not nabre.includes("ESG")
    assert nabre.chapter_letters("EST") == list(ADDITIONS)
    for letter, located in ADDITIONS.items():
        assert nabre.lettered_chapter("EST", letter) == located
    assert nabre.lettered_chapter("EST", "G") is None
    assert nabre.chapter_letters("GEN") == []
    assert Versification.named("eng").chapter_letters("EST") == []
    # A precedes the verse it is held with; C follows its own.
    assert nabre.verse_parts("EST", 1, 1)[0] == "A1"
    assert nabre.verse_parts("EST", 1, 1)[-1] == ""
    assert nabre.verse_parts("EST", 4, 17)[:2] == ["", "C1"]
    assert nabre.verse_parts("EST", 4, 16) == [""]


def test_range_keys_follow_reading_order(parser: RefParser) -> None:
    """Keys put each lettered chapter where the NABRE prints it."""

    def keys(text: str) -> tuple[int, int]:
        ref = parser.parse(text)
        assert ref is not None
        return next(iter(ref.range_keys()))

    in_order = [
        "Esth A:1",
        "Esth A:17",
        "Esth 1:1",
        "Esth 3:13",
        "Esth B:1",
        "Esth B:7",
        "Esth 3:14",
        "Esth 4:17",
        "Esth C:1",
        "Esth C:30",
        "Esth D:1",
        "Esth D:16",
        "Esth 5:1",
        "Esth 8:12",
        "Esth E:24",
        "Esth 8:13",
        "Esth 10:3",
        "Esth F:11",
        "Job 1:1",
    ]
    starts = [keys(text)[0] for text in in_order]
    assert starts == sorted(starts)
    assert len(set(starts)) == len(starts)
    # A part of a verse shares the verse's key.
    assert keys("Esth C:12a") == keys("Esth C:12")
    assert keys("Esth C") == (keys("Esth C:1")[0], keys("Esth C:30")[1])


def test_range_keys_of_chapters_and_the_book(parser: RefParser) -> None:
    """A numbered chapter leaves out a lettered one beside it; the book has them all."""

    def keys(text: str) -> tuple[int, int]:
        ref = parser.parse(text)
        assert ref is not None
        return next(iter(ref.range_keys()))

    def within(inner: str, outer: str) -> bool:
        return keys(outer)[0] <= keys(inner)[0] and keys(inner)[1] <= keys(outer)[1]

    assert not within("Esth A:17", "Esth 1")
    assert within("Esth 1:1", "Esth 1")
    assert not within("Esth C:1", "Esth 4")
    assert not within("Esth D:16", "Esth 5")
    assert not within("Esth F:1", "Esth 10")
    # B and E stand inside chapters 3 and 8.
    assert within("Esth B", "Esth 3")
    assert within("Esth E", "Esth 8")
    assert within("Esth C–D", "Esth 4–5")
    for letter in ADDITIONS:
        assert within(f"Esth {letter}", "Esth")
    assert not within("Esth A", "Esth 1–10")
    assert not within("Esth F", "Esth 1–10")


@pytest.mark.parametrize(
    ("letter", "verse", "target", "expected"),
    [
        # A maps in place: org integrates Addition A at the head of chapter 1
        ("A", 1, "eng", ("ESG", 1, 1, "")),
        # eng gives Addition A 18 verses (LXX's 1:1a-1:1s), so its last verse
        # merges with A:17
        ("A", 17, "eng", ("ESG", 1, 18, "")),
        # B: the first royal letter
        ("B", 1, "eng", ("ESG", 3, 14, "")),
        ("B", 1, "vulgata", ("EST", 13, 1, "")),
        # C: the prayers of Mordecai (1-11) and Esther (12-30)
        ("C", 12, "eng", ("ESG", 4, 29, "")),
        ("C", 12, "vulgata", ("EST", 14, 1, "")),
        # D: Esther before the king
        ("D", 16, "eng", ("ESG", 5, 16, "")),
        ("D", 16, "vulgata", ("EST", 15, 16, "")),
        # E: the second royal letter
        ("E", 24, "vulgata", ("EST", 16, 24, "")),
        # F: the interpretation of the dream (1-10) and colophon (11)
        ("F", 10, "vulgata", ("EST", 10, 13, "")),
        ("F", 11, "eng", ("ESG", 10, 14, "")),
        ("F", 11, "vulgata", ("EST", 11, 1, "")),
    ],
)
def test_map_lettered_chapters(
    letter: str, verse: int, target: str, expected: tuple[str, int, int, str]
) -> None:
    """NABRE lettered chapters map to their integrated ESG positions."""
    nabre = Versification.named("nabre")
    target_vers = Versification.named(target)
    chapter, base, _ = ADDITIONS[letter]
    subverse = f"{letter}{verse}"
    assert nabre.map_verse("EST", chapter, base, target_vers, subverse) == expected
    # And back again
    book, t_chapter, t_verse, _ = expected
    assert target_vers.map_verse(book, t_chapter, t_verse, nabre) == (
        "EST",
        chapter,
        base,
        subverse,
    )


def test_map_part_of_a_lettered_verse() -> None:
    """A part of a lettered verse keeps its letter through a mapping."""
    nabre = Versification.named("nabre")
    org = Versification.named("org")
    assert nabre.map_verse("EST", 4, 17, org, "C12a") == ("ESG", 4, 29, "a")
    assert org.map_verse("ESG", 4, 29, nabre, "a") == ("EST", 4, 17, "C12a")


def test_nabre_esther_covers_org_exactly_once() -> None:
    """Every verse of NABRE Esther maps to one org verse, and none is claimed twice."""
    nabre = Versification.named("nabre")
    org = Versification.named("org")
    seen: set[tuple[str, int, int, str]] = set()
    for chapter in range(1, len(nabre.max_verses["EST"]) + 1):
        for verse in range(1, nabre.last_verse("EST", chapter) + 1):
            for part in nabre.verse_parts("EST", chapter, verse):
                mapped = nabre.map_verse("EST", chapter, verse, org, part)
                assert mapped is not None
                assert mapped not in seen
                assert mapped[0] == ("ESG" if part else "EST")
                seen.add(mapped)
    hebrew = sum(org.max_verses["EST"])
    assert len(seen) == hebrew + sum(count for _, _, count in ADDITIONS.values())


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("Esth C", "Add Esth 4:18–47"),
        ("Esth C–D", "Add Esth 4:18–5:16"),
        ("Esth B:1ff", "Add Esth 3:14–20"),
        ("Esth C:12a–c", "Add Esth 4:29a–c"),
        # A range is divided where it passes between the Hebrew and the Greek.
        ("Esth 4:1–C:30", "Esth 4:1–17; Add Esth 4:18–47"),
        ("Esth A:17–1:1", "Add Esth 1:17; Esth 1:1"),
        ("Esth 3", "Esth 3:1–13; Add Esth 3:14–20; Esth 3:14–15"),
        # A numbered chapter leaves out the lettered chapters beside it.
        ("Esth 4", "Esth 4"),
        ("Esth 1", "Esth 1"),
        ("Esth 4–C", "Esth 4; Add Esth 4:18–47"),
        ("Esth C–5", "Add Esth 4:18–5:16; Esth 5"),
        ("Esth D–5", "Add Esth 5:1–16; Esth 5"),
        ("Esth 4–5", "Esth 4; Add Esth 4:18–5:16; Esth 5"),
        (
            "Esth",
            "Add Esth 1:1–17; Esth 1:1–3:13; Add Esth 3:14–20; Esth 3:14–4:17; "
            "Add Esth 4:18–5:16; Esth 5:1–8:12; Add Esth 8:13–36; Esth 8:13–10:3; "
            "Add Esth 10:4–14",
        ),
        (
            "Esth 9–Job 2",
            "Esth 9–10; Add Esth 10:4–14; 1 Macc–2 Macc; Job 1–2",
        ),
    ],
)
def test_map_from_nabre(parser: RefParser, reference: str, expected: str) -> None:
    """References to NABRE Esther map into org's two books of Esther."""
    ref = parser.parse(reference)
    assert ref is not None
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert mapped.format(RefStyle.named("en-sbl")) == expected


@pytest.mark.parametrize(
    ("source", "reference", "expected"),
    [
        ("org", "Add Esth 4:29", "Esth C:12"),
        ("org", "Add Esth 4:18–47", "Esth C:1–30"),
        ("org", "Add Esth 4:40–5:3", "Esth C:23–D:3"),
        ("org", "Esth 4", "Esth 4"),
        ("org", "Esth", "Esth"),
        ("eng", "Add Esth 4:18ff", "Esth C:1–30"),
        ("vulgata", "Esth 13:1–7", "Esth B:1–7"),
        # A whole chapter that is a lettered chapter stays a whole chapter.
        ("vulgata", "Esth 16", "Esth E"),
        # The Vulgate gathers the additions at the end of the book, so what
        # is consecutive there is not in the NABRE (#52).
        ("vulgata", "Esth 13–14", "Esth B; C"),
        ("vulgata", "Esth 12–13", "Esth A:12–17; B; C:1–11"),
        ("vulgata", "Esth 11", "Esth F:11; A:1–11"),
        ("vulgata", "Esth 10:1–11:12", "Esth 10:1–F:11; A:1–11"),
        # A numbered chapter that takes in a lettered one says so.
        ("vulgata", "Esth 10", "Esth 10:1–F:10"),
        ("org", "Add Esth", "Esth"),
        ("vulgata", "Esth 14", "Esth C:12–30"),
    ],
)
def test_map_into_nabre(source: str, reference: str, expected: str) -> None:
    """References to the additions map into the NABRE's lettered chapters."""
    sbl = RefStyle.named("en-sbl")
    ref = RefParser(sbl, Versification.named(source)).parse(reference)
    assert ref is not None
    mapped = ref.map_to(Versification.named("nabre"))
    assert mapped is not None
    assert mapped.format(RefStyle.named("en-nabre")) == expected
