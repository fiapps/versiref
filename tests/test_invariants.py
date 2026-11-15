"""Properties that should hold for every bundled style and versification.

These tests describe behavior through strings and verse keys rather than
through the shape of the reference classes, so that they keep their meaning if
the classes are redesigned. The few places that must build a reference no
parser produces go through the helpers below.

A known bug is recorded as a strict expected failure naming its issue: fixing
the bug makes the test fail until the marker is removed.
"""

import logging

import pytest
from versiref import (
    BibleRef,
    RefParser,
    RefStyle,
    Sensitivity,
    SimpleBibleRef,
    Versification,
)
from versiref.bible_ref import VerseRange

CANONICAL_STYLE = "en-sbl"

# The versification each bundled style is meant for, where it is not "eng".
STYLE_VERSIFICATIONS = {
    "en-douay-rheims": "douay-rheims",
    "en-nabre": "nabre",
    "it-cei": "cei",
    "la-cce": "nova_vulgata",
    "la-vetus": "vulgata",
}

# References in the canonical style, written as that style formats them, in
# every shape the parser produces.
CORPUS = [
    "John 3:16",
    "Phlm 8",
    "Matt 5:3–12",
    "Jude 8–9",
    "Mark 4:3–9, 13–20",
    "Jude 1, 4, 17",
    "Luke 23:50–24:12",
    "Acts 1:8–11; 2:1–4",
    "1 John 1:5–10",
    "John 1:1a",
    "Isa 11:1–2a",
    "Gen 1:1a–c",
    "Rom 8:28ff",
    "Jude 3ff",
    "Ps 23:1",
    "Pss 1:1; 2:1",
    "John 3:16; Rom 8:28; 1 Cor 13:4–7, 13",
    "2 John 4–6; 3 John 2",
    "Ps 23",
    "Pss 1–2",
    "Isa 40–55",
    "Gen 1; 3; 5",
    "Gen 1; Exod 2:1",
    "Rom",
    "Obad",
    "Gen; Exod",
    "Matt; Mark 1:1",
]

_versifications: dict[str, Versification] = {}
_parsers: dict[str, RefParser] = {}


def _versification(name: str) -> Versification:
    if name not in _versifications:
        _versifications[name] = Versification.named(name)
    return _versifications[name]


def _versification_for(style_name: str) -> Versification:
    return _versification(STYLE_VERSIFICATIONS.get(style_name, "eng"))


def _parser(style_name: str, versification_style: str | None = None) -> RefParser:
    """Return a parser for one style in the versification of another."""
    versification_style = versification_style or style_name
    key = f"{style_name}/{versification_style}"
    if key not in _parsers:
        _parsers[key] = RefParser(
            RefStyle.named(style_name), _versification_for(versification_style)
        )
    return _parsers[key]


def _whole_book(book: str, versification: Versification) -> BibleRef:
    return BibleRef([SimpleBibleRef(book)], versification)


def _whole_chapter(book: str, chapter: int, versification: Versification) -> BibleRef:
    return BibleRef(
        [SimpleBibleRef(book, [VerseRange(chapter, -1, "", chapter, -1, "")])],
        versification,
    )


def _chapter_then_verse(
    book: str, chapter: int, verse: int, versification: Versification
) -> BibleRef:
    """Return a whole chapter followed by one verse of the same chapter."""
    return BibleRef(
        [
            SimpleBibleRef(
                book,
                [
                    VerseRange(chapter, -1, "", chapter, -1, ""),
                    VerseRange(chapter, verse, "", chapter, verse, ""),
                ],
            )
        ],
        versification,
    )


def _in_style(canonical: str, style_name: str) -> BibleRef:
    """Parse a corpus entry in the versification that goes with a style."""
    ref = _parser(CANONICAL_STYLE, style_name).parse(canonical)
    assert ref is not None
    return ref


STYLES = RefStyle.available_names()
VERSIFICATIONS = Versification.available_names()


@pytest.mark.parametrize("canonical", CORPUS)
def test_corpus_is_canonical(canonical: str) -> None:
    """Each corpus entry is what the canonical style itself would print."""
    style = RefStyle.named(CANONICAL_STYLE)
    assert _in_style(canonical, CANONICAL_STYLE).format(style) == canonical


@pytest.mark.parametrize("style_name", STYLES)
@pytest.mark.parametrize("canonical", CORPUS)
def test_format_then_parse_round_trips(style_name: str, canonical: str) -> None:
    """A reference formatted in a style parses back to the same reference."""
    style = RefStyle.named(style_name)
    ref = _in_style(canonical, style_name)
    formatted = ref.format(style)

    reparsed = _parser(style_name).parse(formatted)

    assert reparsed is not None
    assert reparsed.format(style) == formatted
    assert list(reparsed.range_keys()) == list(ref.range_keys())
    # A style with one name for Psalm and Psalms cannot give the plural back.
    if style.names.get("PSAS") != style.names["PSA"]:
        assert reparsed.format(RefStyle.named(CANONICAL_STYLE)) == canonical


@pytest.mark.parametrize("style_name", STYLES)
def test_every_named_book_round_trips(style_name: str) -> None:
    """Every book a style names formats to text the style parses back."""
    style = RefStyle.named(style_name)
    versification = _versification_for(style_name)
    parser = _parser(style_name)
    checked = 0
    for book in style.names:
        if not versification.includes(book):
            continue
        ref = BibleRef.for_range(book, 1, 1, versification=versification)
        formatted = ref.format(style)
        reparsed = parser.parse(formatted)
        assert reparsed is not None
        assert reparsed.format(style) == formatted
        # ESG may share EST's name, in which case it reads back as EST.
        if style.recognized_names.get(style.names[book]) in (book, "PSA"):
            assert list(reparsed.range_keys()) == list(ref.range_keys()), formatted
        checked += 1
    assert checked >= 66


@pytest.mark.parametrize("style_name", STYLES)
@pytest.mark.parametrize("suffix", [" and so on", ".", ";", ",", ")", "\n\nNext"])
def test_scan_finds_exactly_the_reference(style_name: str, suffix: str) -> None:
    """Scanning finds a formatted reference whole, whatever follows it."""
    style = RefStyle.named(style_name)
    parser = _parser(style_name)
    for canonical in CORPUS:
        formatted = _in_style(canonical, style_name).format(style)
        text = f"See {formatted}{suffix}"
        found = [
            text[start:end]
            for _, start, end in parser.scan_string(text, sensitivity=Sensitivity.BOOK)
        ]
        # A style may know a name both with and without its period ("Rom"
        # and "Rom."), and then a sentence-ending period reads as the name's.
        assert [match.rstrip(".") for match in found] == [formatted.rstrip(".")], text


@pytest.mark.parametrize("style_name", STYLES)
def test_scan_as_ranges_spans_lie_in_order(style_name: str) -> None:
    """Each range's span holds its own text, and the spans do not overlap."""
    style = RefStyle.named(style_name)
    parser = _parser(style_name)
    for canonical in CORPUS:
        text = _in_style(canonical, style_name).format(style)
        previous_end = 0
        for ref, start, end in parser.scan_string(
            text, as_ranges=True, sensitivity=Sensitivity.BOOK
        ):
            assert start >= previous_end, text
            assert text[start:end] == ref.original_text, text
            previous_end = end


@pytest.mark.xfail(strict=True, reason="#33")
@pytest.mark.parametrize(
    "text",
    ["Gen 1; 2:4", "Gen 1–2:4", "John 3:16; 4", "Rom 8:1–9:5; 12"],
)
def test_scan_reads_mixed_chapters_and_verses_whole(text: str) -> None:
    """A list mixing whole chapters and verses is one reference."""
    parser = _parser(CANONICAL_STYLE)
    found = [
        text[start:end]
        for _, start, end in parser.scan_string(text, sensitivity=Sensitivity.CHAPTER)
    ]
    assert found == [text]


@pytest.mark.xfail(strict=True, reason="#44")
@pytest.mark.parametrize(("book", "chapter"), [("JHN", 3), ("JUD", 1)])
def test_chapter_then_verse_formats_unambiguously(book: str, chapter: int) -> None:
    """A verse after its whole chapter formats to text that means the same."""
    ref = _chapter_then_verse(book, chapter, 5, _versification("eng"))
    formatted = ref.format(RefStyle.named(CANONICAL_STYLE))
    reparsed = _parser(CANONICAL_STYLE).parse(formatted)
    assert reparsed is not None
    assert list(reparsed.range_keys()) == list(ref.range_keys())


@pytest.mark.parametrize("name", VERSIFICATIONS)
def test_bundled_versification_loads_cleanly(
    name: str, caplog: pytest.LogCaptureFixture
) -> None:
    """No entry of a bundled versification is skipped as malformed."""
    with caplog.at_level(logging.DEBUG, logger="versiref"):
        Versification.named(name)
    assert caplog.records == []


@pytest.mark.parametrize("name", VERSIFICATIONS)
def test_keys_nest_and_ascend(name: str) -> None:
    """Verses lie in their chapter, chapters in their book, books in order."""
    versification = _versification(name)
    previous_book_end = 0
    for book, chapters in versification.max_verses.items():
        ((book_start, book_end),) = _whole_book(book, versification).range_keys()
        assert previous_book_end < book_start <= book_end, book
        previous_book_end = book_end

        previous_chapter_end = book_start - 1
        for chapter, last_verse in enumerate(chapters, 1):
            ((start, end),) = _whole_chapter(book, chapter, versification).range_keys()
            where = f"{book} {chapter}"
            assert previous_chapter_end < start <= end <= book_end, where
            previous_chapter_end = end
            for verse in {1, last_verse}:
                ((key, _),) = BibleRef.for_range(
                    book, chapter, verse, versification=versification
                ).range_keys()
                assert start <= key <= end, f"{where}:{verse}"


@pytest.mark.parametrize("name", VERSIFICATIONS)
def test_plural_psalms_have_the_same_keys(name: str) -> None:
    """PSAS is PSA under another name, wherever a book ID is taken."""
    versification = _versification(name)
    assert list(_whole_book("PSAS", versification).range_keys()) == list(
        _whole_book("PSA", versification).range_keys()
    )
    assert list(
        BibleRef.for_range("PSAS", 2, 1, versification=versification).range_keys()
    ) == list(BibleRef.for_range("PSA", 2, 1, versification=versification).range_keys())
    assert versification.is_single_chapter("PSAS") is False


@pytest.mark.parametrize("style_name", STYLES)
def test_mapping_to_the_same_versification_changes_nothing(style_name: str) -> None:
    """Mapping into a second copy of a versification is the identity."""
    canonical_style = RefStyle.named(CANONICAL_STYLE)
    twin = Versification.named(STYLE_VERSIFICATIONS.get(style_name, "eng"))
    for canonical in CORPUS:
        mapped = _in_style(canonical, style_name).map_to(twin)
        assert mapped is not None, canonical
        assert mapped.format(canonical_style) == canonical


@pytest.mark.xfail(strict=True, reason="#39")
def test_psalm_151_can_be_formatted() -> None:
    """PS2 formats in a style that names the Psalms."""
    ref = BibleRef.for_range("PS2", 1, 1, versification=_versification("lxx"))
    assert ref.format(RefStyle.named(CANONICAL_STYLE))


@pytest.mark.xfail(strict=True, reason="#40")
def test_whole_book_maps_as_its_contents_do() -> None:
    """Vulgate Daniel as a whole includes what org calls Susanna."""
    whole = _whole_book("DAN", _versification("vulgata")).map_to(_versification("org"))
    assert whole is not None
    susanna = BibleRef.for_range("SUS", 1, 1, versification=_versification("org"))
    ((verse, _),) = susanna.range_keys()
    assert any(start <= verse <= end for start, end in whole.range_keys())


@pytest.mark.xfail(strict=True, reason="#41")
def test_empty_versification_is_consistent() -> None:
    """A versification has the verses of exactly the books it includes."""
    versification = Versification()
    assert versification.includes("JHN") == (versification.last_verse("JHN", 3) > 0)
