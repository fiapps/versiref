"""Test chapter letters (e.g. the NABRE's Esther A–F) in parsing and formatting."""

import pytest
from versiref import RefParser, RefStyle, SimpleBibleRef, Versification, VerseRange

ESTHER_LETTERS = ["A", "B", "C", "D", "E", "F"]


@pytest.fixture
def parser() -> RefParser:
    """Return a parser for the NABRE style and versification."""
    return RefParser(RefStyle.named("en-nabre"), Versification.named("nabre"))


@pytest.mark.parametrize(
    "text,book_id,ranges,formatted",
    [
        ("Esth C:12", "ESG", [(3, 12, 3, 12)], "Esth C:12"),
        ("Esth C:12-30", "ESG", [(3, 12, 3, 30)], "Esth C:12–30"),
        ("Esth A:1–17", "ESG", [(1, 1, 1, 17)], "Esth A:1–17"),
        ("Esth C:25–D:2", "ESG", [(3, 25, 4, 2)], "Esth C:25–D:2"),
        (
            "Esth C:12, 14, 25–30",
            "ESG",
            [(3, 12, 3, 12), (3, 14, 3, 14), (3, 25, 3, 30)],
            "Esth C:12, 14, 25–30",
        ),
        ("Esth B:1ff", "ESG", [(2, 1, 2, -1)], "Esth B:1ff"),
        # Recognized EST names all take letters
        ("Esther C:12", "ESG", [(3, 12, 3, 12)], "Esth C:12"),
        ("Est D:5", "ESG", [(4, 5, 4, 5)], "Esth D:5"),
        # Whole-chapter references
        ("Esth A", "ESG", [(1, -1, 1, -1)], "Esth A"),
        ("Esth A–C", "ESG", [(1, -1, 3, -1)], "Esth A–C"),
        # ESG's own name still parses with letters, though it formats
        # with EST's name
        ("Add Esth B:5", "ESG", [(2, 5, 2, 5)], "Esth B:5"),
        # Numeric chapters still resolve to EST
        ("Esther 4:17", "EST", [(4, 17, 4, 17)], "Esth 4:17"),
        ("Esth 10:3", "EST", [(10, 3, 10, 3)], "Esth 10:3"),
        ("Esth 3", "EST", [(3, -1, 3, -1)], "Esth 3"),
        # A bare shared name still resolves to EST
        ("Esther", "EST", [], "Esth"),
    ],
)
def test_parse_and_format(
    parser: RefParser,
    text: str,
    book_id: str,
    ranges: list[tuple[int, int, int, int]],
    formatted: str,
) -> None:
    """Letter chapters parse to ESG and format back as letters."""
    ref = parser.parse_simple(text)
    assert ref is not None
    assert ref.book_id == book_id
    assert [
        (r.start_chapter, r.start_verse, r.end_chapter, r.end_verse) for r in ref.ranges
    ] == ranges
    assert ref.format(parser.style, parser.versification) == formatted


def test_scan_string(parser: RefParser) -> None:
    """Scanning picks out letter-chapter references without false positives."""
    text = "Esther Also spoke, but see Esth C:12f and Esth 4:17 for more."
    found = [
        (text[start:end], ref.simple_refs[0].book_id)
        for ref, start, end in parser.scan_string(text)
    ]
    assert found == [("Esth C:12f", "ESG"), ("Esth 4:17", "EST")]


def test_book_name() -> None:
    """A lettered ESG takes EST's name; without letters it keeps its own."""
    style = RefStyle.named("en-nabre")
    assert style.book_name("ESG") == "Esth"
    assert style.book_name("EST") == "Esth"
    plain = RefStyle.named("en-sbl")
    assert plain.book_name("ESG") == "Add Esth"
    with pytest.raises(ValueError, match="Unknown book ID"):
        plain.book_name("XXX")


def test_format_chapter_letters() -> None:
    """format_chapter renders letters for a lettered book, numbers otherwise."""
    style = RefStyle.named("en-nabre")
    assert style.format_chapter(1, "ESG") == "A"
    assert style.format_chapter(6, "ESG") == "F"
    assert style.format_chapter(3, "EST") == "3"
    assert style.format_chapter(3) == "3"


def test_format_chapter_without_letter() -> None:
    """A chapter beyond the letter list raises instead of falling back."""
    style = RefStyle.named("en-nabre")
    with pytest.raises(ValueError, match="No chapter letter for ESG 7"):
        style.format_chapter(7, "ESG")
    ref = SimpleBibleRef("ESG", [VerseRange(7, 1, "", 7, 1, "")])
    with pytest.raises(ValueError, match="No chapter letter for ESG 7"):
        ref.format(style)


def test_from_dict_chapter_letters() -> None:
    """chapter_letters loads from style data, shared name and all."""
    style = RefStyle.from_dict(
        {"base": "en-sbl", "chapter_letters": {"ESG": ESTHER_LETTERS}}
    )
    assert style.chapter_letters == {"ESG": ESTHER_LETTERS}

    style = RefStyle.from_dict(
        {
            "names": {"EST": "Est", "ESG": "Est"},
            "chapter_letters": {"ESG": ESTHER_LETTERS},
        }
    )
    parser = RefParser(style, Versification.named("nabre"))
    ref = parser.parse_simple("Est F:3")
    assert ref is not None
    assert ref.book_id == "ESG"
    assert ref.ranges[0].start_chapter == 6


def test_letters_without_est_name() -> None:
    """Letters work when the style names ESG but not EST."""
    style = RefStyle.from_dict(
        {
            "names": {"ESG": "Greek Esther"},
            "chapter_letters": {"ESG": ESTHER_LETTERS},
        }
    )
    parser = RefParser(style, Versification.named("nabre"))
    ref = parser.parse_simple("Greek Esther D:5")
    assert ref is not None
    assert ref.book_id == "ESG"
    assert ref.ranges[0].start_chapter == 4
    # With no EST name to borrow, ESG formats with its own name
    assert ref.format(style) == "Greek Esther D:5"
