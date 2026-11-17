"""Tests for the bible_ref module."""

import pathlib
import string

import pytest

from versiref.bible_ref import BibleRef, RefPoint, VerseRange
from versiref.ref_parser import RefParser
from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification

SBL = RefStyle(names=standard_names("en-sbl_abbreviations"))


def _range(
    book: str,
    chapter: int | None,
    verse: int | None,
    end_chapter: int | None,
    end_verse: int | None,
    subverse: str = "",
    end_subverse: str = "",
    original_text: str | None = None,
) -> VerseRange:
    """Build a VerseRange within one book."""
    return VerseRange(
        RefPoint(book, chapter, verse, subverse),
        RefPoint(book, end_chapter, end_verse, end_subverse),
        original_text,
    )


def _whole_book(book: str) -> VerseRange:
    return VerseRange(RefPoint(book), RefPoint(book))


def _spans(ref: BibleRef) -> list[tuple[object, ...]]:
    """Describe each range as (book, chapter, verse, book, chapter, verse)."""
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


def _parsed(text: str, versification: str = "eng") -> BibleRef:
    ref = RefParser(SBL, Versification.named(versification)).parse(text)
    assert ref is not None
    return ref


def _mapped(text: str, source: str, target: str) -> str | None:
    """Parse text in one versification and format it mapped into another."""
    mapped = _parsed(text, source).map_to(Versification.named(target))
    return None if mapped is None else mapped.format(SBL)


# --- RefPoint and VerseRange ---


def test_ref_point_initialization() -> None:
    """Test that RefPoint initializes correctly."""
    point = RefPoint("JHN", 3, 16, "a")
    assert (point.book, point.chapter, point.verse, point.subverse) == (
        "JHN",
        3,
        16,
        "a",
    )
    whole_book = RefPoint("JHN")
    assert whole_book.chapter is None
    assert whole_book.verse is None
    assert whole_book.subverse == ""
    assert RefPoint("JHN", 3).verse is None
    # A verse 0 (a psalm title) is a verse.
    assert RefPoint("PSA", 51, 0).verse == 0


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (("JHN", None, 16), "A verse requires a chapter"),
        (("JHN", 3, -1), "cannot be negative"),
        (("JHN", -1), "cannot be negative"),
        (("PSAS", 1, 1), '"PSAS" is not a book ID'),
    ],
)
def test_ref_point_rejects_impossible_values(
    args: tuple[str, int | None, int | None], message: str
) -> None:
    """A point cannot have a verse without a chapter, or a negative number."""
    with pytest.raises(ValueError, match=message):
        RefPoint(*args)


def test_verse_range_initialization() -> None:
    """Test that VerseRange initializes correctly."""
    vr = _range("JHN", 3, 16, 3, 16)
    assert vr.start == RefPoint("JHN", 3, 16)
    assert vr.end == vr.start
    assert vr.original_text is None

    vr = _range("GEN", 1, 2, 3, 4, "a", "b", original_text="1:2a-3:4b")
    assert vr.start == RefPoint("GEN", 1, 2, "a")
    assert vr.end == RefPoint("GEN", 3, 4, "b")
    assert vr.original_text == "1:2a-3:4b"


@pytest.mark.parametrize(
    "verse_range",
    [
        _range("GEN", 1, 1, 1, 5),  # Simple range in same chapter
        _range("GEN", 1, None, 1, None),  # Whole chapter
        _range("GEN", 1, None, 3, None),  # Multiple chapters
        _range("GEN", 1, 1, 2, 3),  # Cross-chapter range
        _range("GEN", 1, 5, 1, None),  # "ff" notation in same chapter
        _range("GEN", 1, None, 2, 4),  # From a chapter to a verse
        _range("GEN", 1, None, 1, 5),  # From a chapter to a verse of it
        _whole_book("GEN"),
        _range("GEN", 1, 1, 1, 1, "a", "b"),  # Same verse, different subverses
        _range("GEN", 1, 5, 1, None, "c"),  # "ff" notation with subverse
        # A range that spans books has no structural constraint.
        VerseRange(RefPoint("MAT"), RefPoint("JHN")),
        VerseRange(RefPoint("1SA", 31, 1), RefPoint("2SA", 1, 27)),
        VerseRange(RefPoint("MAT", 28, 16), RefPoint("MRK", 1)),
        VerseRange(RefPoint("MAT"), RefPoint("MRK", 3)),
    ],
)
def test_verse_range_is_valid(verse_range: VerseRange) -> None:
    """Test structurally valid ranges."""
    assert verse_range.is_valid() is True
    assert verse_range.invalid_reason() is None


@pytest.mark.parametrize(
    ("verse_range", "reason"),
    [
        (
            _range("GEN", 2, 1, 1, 5),
            "range ends in an earlier chapter than it starts",
        ),
        (
            _range("GEN", 2, 1, 1, 5, "a", "b"),
            "range ends in an earlier chapter than it starts",
        ),
        (_range("GEN", 1, 5, 2, None), "'ff' range spans more than one chapter"),
        (_range("GEN", 1, 5, 1, 3), "range ends at an earlier verse than it starts"),
        (
            _range("GEN", 1, 5, 1, 3, "a", "b"),
            "range ends at an earlier verse than it starts",
        ),
        (
            VerseRange(RefPoint("GEN"), RefPoint("GEN", 3)),
            "range joins the whole book with a part of it",
        ),
        (
            VerseRange(RefPoint("GEN", 3), RefPoint("GEN")),
            "range joins the whole book with a part of it",
        ),
    ],
)
def test_verse_range_invalid_reason(verse_range: VerseRange, reason: str) -> None:
    """Each structural failure returns an explanatory string."""
    assert verse_range.is_valid() is False
    assert verse_range.invalid_reason() == reason


def test_verse_range_kinds() -> None:
    """Test the predicates that describe the form of a range."""
    verse = _range("JHN", 3, 16, 3, 16)
    following = _range("JHN", 3, 16, 3, None)
    chapters = _range("JHN", 3, None, 5, None)
    book = _whole_book("JHN")
    books = VerseRange(RefPoint("MAT"), RefPoint("JHN"))

    assert [r.is_whole_chapters() for r in (verse, following, chapters, book)] == [
        False,
        False,
        True,
        True,
    ]
    assert [r.is_whole_books() for r in (verse, chapters, book, books)] == [
        False,
        False,
        True,
        True,
    ]
    assert [r.has_following_verses() for r in (verse, following, chapters)] == [
        False,
        True,
        False,
    ]
    assert book.is_single_book() is True
    assert books.is_single_book() is False


def test_equality_ignores_original_text() -> None:
    """Ranges and references compare by what they cite, not how it was written."""
    assert _range("JHN", 3, 16, 3, 16, original_text="Jn 3:16") == _range(
        "JHN", 3, 16, 3, 16
    )
    eng = Versification.named("eng")
    constructed = BibleRef.for_range("JHN", 3, 16, versification=eng)
    assert _parsed("John 3:16") == constructed
    assert _parsed("John 3:16") != _parsed("John 3:17")
    # The versification is part of what a reference is.
    assert constructed != BibleRef.for_range("JHN", 3, 16)


def test_references_are_hashable() -> None:
    """References can be collected in sets and used as dictionary keys."""
    refs = {_parsed("John 3:16"), _parsed("John 3:16; Rom 8:28"), _parsed("John 3:16")}
    assert len(refs) == 2
    counts = {_parsed("John 3:16"): 1}
    assert (
        counts[
            BibleRef.for_range(
                "JHN", 3, 16, versification=_parsed("Gen 1").versification
            )
        ]
        == 1
    )
    assert hash(RefPoint("JHN", 3, 16)) == hash(RefPoint("JHN", 3, 16))


# --- BibleRef construction ---


def test_bible_ref_initialization() -> None:
    """Test that BibleRef initializes correctly."""
    ref = BibleRef()
    assert ref.ranges == ()
    assert ref.versification is None
    assert ref.original_text is None

    versification = Versification.named("eng")
    ref = BibleRef(versification=versification)
    assert ref.ranges == ()
    assert ref.versification is versification

    # Ranges may be given as a list and are stored as a tuple.
    verse_range = _range("JHN", 3, 16, 3, 16)
    ref = BibleRef([verse_range], versification, original_text="John 3:16")
    assert ref.ranges == (verse_range,)
    assert ref.versification is versification
    assert ref.original_text == "John 3:16"


def test_bible_ref_for_range() -> None:
    """Test the for_range class method of BibleRef."""
    versification = Versification.named("eng")

    # Basic usage with just book, chapter, and verse
    ref = BibleRef.for_range("JHN", 3, 16, versification=versification)
    assert _spans(ref) == [("JHN", 3, 16, "JHN", 3, 16)]
    assert ref.ranges[0].start.subverse == ""
    assert ref.ranges[0].end.subverse == ""
    assert ref.versification is versification
    assert ref.original_text is None

    # With end verse specified
    ref = BibleRef.for_range("ROM", 8, 28, end_verse=39)
    assert _spans(ref) == [("ROM", 8, 28, "ROM", 8, 39)]
    assert ref.versification is None

    # Cross-chapter reference
    ref = BibleRef.for_range("JHN", 7, 53, end_chapter=8, end_verse=11)
    assert _spans(ref) == [("JHN", 7, 53, "JHN", 8, 11)]

    # With subverses
    ref = BibleRef.for_range(
        "MRK", 5, 3, end_verse=5, start_subverse="b", end_subverse="a"
    )
    assert ref.ranges[0].start == RefPoint("MRK", 5, 3, "b")
    assert ref.ranges[0].end == RefPoint("MRK", 5, 5, "a")

    # A single verse's subverse is that of both ends.
    ref = BibleRef.for_range("MRK", 5, 3, start_subverse="b")
    assert ref.ranges[0].end == RefPoint("MRK", 5, 3, "b")
    assert ref.format(SBL) == "Mark 5:3b"

    # With original text
    ref = BibleRef.for_range("PSA", 23, 1, original_text="Psalm 23:1")
    assert ref.original_text == "Psalm 23:1"
    assert ref.ranges[0].original_text == "Psalm 23:1"

    # Whole chapters
    assert _spans(BibleRef.for_range("JHN", 6)) == [("JHN", 6, None, "JHN", 6, None)]
    assert _spans(BibleRef.for_range("ISA", 1, end_chapter=39)) == [
        ("ISA", 1, None, "ISA", 39, None)
    ]

    # From a verse to the end of its chapter ("ff") has no shorthand.
    ref = BibleRef([_range("ROM", 8, 28, 8, None)])
    assert ref.ranges[0].has_following_verses()

    # Into another book
    ref = BibleRef.for_range("1SA", 31, 1, end_book="2SA", end_chapter=1, end_verse=27)
    assert _spans(ref) == [("1SA", 31, 1, "2SA", 1, 27)]
    assert _spans(BibleRef.for_range("MAT", 28, 16, end_book="MRK")) == [
        ("MAT", 28, 16, "MRK", None, None)
    ]


def test_bible_ref_for_book() -> None:
    """Test the for_book class method of BibleRef."""
    versification = Versification.named("eng")
    ref = BibleRef.for_book("JHN", versification=versification)
    assert _spans(ref) == [("JHN", None, None, "JHN", None, None)]
    assert ref.versification is versification
    assert ref.is_whole_books()

    ref = BibleRef.for_book("MAT", "JHN", original_text="the Gospels")
    assert _spans(ref) == [("MAT", None, None, "JHN", None, None)]
    assert ref.original_text == "the Gospels"


def test_books_and_single_range() -> None:
    """Test the books and is_single_range methods."""
    ref = _parsed("John 3:16; Rom 8:28; John 1:1; 1 Sam 31:1–2 Sam 1:27")
    assert ref.books() == ["JHN", "ROM", "1SA", "2SA"]
    assert ref.is_single_range() is False
    assert _parsed("John 3:16").is_single_range() is True
    assert BibleRef().books() == []
    assert BibleRef().is_single_range() is False


def test_bible_ref_str() -> None:
    """Test the string representation of a BibleRef."""
    assert str(_parsed("John 3:16")) == (
        'BibleRef("John 3:16", versification=Versification.named("eng"))'
    )
    assert str(BibleRef.for_range("JHN", 3, 16)) == 'BibleRef("John 3:16")'


# --- Whole books and chapters ---


def test_bible_ref_is_whole_books() -> None:
    """Test the is_whole_books method of BibleRef."""
    # Empty BibleRef is vacuously whole books
    assert BibleRef().is_whole_books() is True
    assert BibleRef.for_book("GEN").is_whole_books() is True
    assert BibleRef([_whole_book("GEN"), _whole_book("EXO")]).is_whole_books() is True
    assert BibleRef.for_book("MAT", "JHN").is_whole_books() is True
    # Mixed whole book and verse references
    mixed = BibleRef([_whole_book("GEN"), _range("JHN", 3, 16, 3, 16)])
    assert mixed.is_whole_books() is False
    assert BibleRef.for_range("JHN", 3, 16).is_whole_books() is False
    assert BibleRef.for_range("JHN", 3).is_whole_books() is False


def test_bible_ref_is_whole_chapters() -> None:
    """Test the is_whole_chapters method of BibleRef."""
    # Empty BibleRef is vacuously whole chapters
    assert BibleRef().is_whole_chapters() is True
    # A whole book is whole chapters
    assert BibleRef.for_book("GEN").is_whole_chapters() is True
    assert BibleRef.for_range("JHN", 6).is_whole_chapters() is True
    assert BibleRef.for_range("ISA", 1, end_chapter=39).is_whole_chapters() is True
    assert (
        BibleRef(
            [_whole_book("GEN"), _range("ISA", 1, None, 39, None)]
        ).is_whole_chapters()
        is True
    )
    # Verses are not whole chapters, even alongside them or across chapters
    assert BibleRef.for_range("JHN", 3, 16).is_whole_chapters() is False
    assert BibleRef.for_range("ROM", 8, 28, end_verse=39).is_whole_chapters() is False
    assert (
        BibleRef.for_range("PSA", 1, 1, end_chapter=2, end_verse=12).is_whole_chapters()
        is False
    )
    mixed = BibleRef([_range("MAT", 5, None, 5, None), _range("MAT", 6, 9, 6, 13)])
    assert mixed.is_whole_chapters() is False
    assert _parsed("Gen 1–2:4").is_whole_chapters() is False


# --- Validity ---


@pytest.mark.parametrize(
    "ref",
    [
        BibleRef(),  # Empty BibleRef is vacuously valid
        BibleRef.for_book("GEN"),
        BibleRef.for_range("JHN", 3, 16),
        BibleRef.for_range("PSA", 119, 1, end_verse=176),
        BibleRef([_range("PSA", 18, 7, 18, 7), _range("PSA", 77, 18, 77, 18)]),
        BibleRef.for_range("ISA", 1, end_chapter=66),
        BibleRef([_range("ROM", 8, 28, 8, None)]),  # "ff" notation
        BibleRef([_range("JHN", 3, 16, 3, 16), _range("ROM", 8, 28, 8, 28)]),
        BibleRef([_range("GEN", 1, None, 2, 4)]),
        BibleRef.for_book("MAT", "JHN"),
        BibleRef.for_range("1SA", 31, 1, end_book="2SA", end_chapter=1, end_verse=27),
    ],
)
def test_bible_ref_is_valid(ref: BibleRef) -> None:
    """Test references that are valid in eng."""
    ref = BibleRef(ref.ranges, Versification.named("eng"))
    assert ref.is_valid() is True
    assert ref.invalid_reason() is None
    assert ref.invalid_reason(SBL) is None


@pytest.mark.parametrize(
    ("ref", "reason", "styled"),
    [
        # Book not in the versification. The message names the versification.
        (
            BibleRef.for_book("XYZ"),
            "XYZ is not in versification 'eng'",
            "XYZ is not in versification 'eng'",
        ),
        # Nonexistent chapter
        (
            BibleRef.for_range("JHN", 30, 1, end_verse=10),
            "JHN has no chapter 30 (only 21 chapters)",
            "John has no chapter 30 (only 21 chapters)",
        ),
        (
            BibleRef.for_range("JHN", 30),
            "JHN has no chapter 30 (only 21 chapters)",
            "John has no chapter 30 (only 21 chapters)",
        ),
        # Nonexistent verse, at the start or at the end
        (
            BibleRef.for_range("JHN", 3, 40, end_verse=50),
            "JHN 3 has no verse 40 (only 36 verses)",
            "John 3 has no verse 40 (only 36 verses)",
        ),
        (
            BibleRef.for_range("JHN", 3, 30, end_verse=50),
            "JHN 3 has no verse 50 (only 36 verses)",
            "John 3 has no verse 50 (only 36 verses)",
        ),
        (
            BibleRef([_range("JHN", 3, 40, 3, None)]),
            "JHN 3 has no verse 40 (only 36 verses)",
            "John 3 has no verse 40 (only 36 verses)",
        ),
        # A structural problem is reported ahead of any range check.
        (
            BibleRef.for_range("JHN", 3, 40, end_verse=10),
            "JHN: range ends at an earlier verse than it starts",
            "John: range ends at an earlier verse than it starts",
        ),
        # Every offending range is reported, joined by "; ".
        (
            BibleRef([_range("PSA", 200, 1, 200, 1), _range("PSA", 2, 99, 2, 99)]),
            "PSA has no chapter 200 (only 150 chapters); "
            "PSA 2 has no verse 99 (only 12 verses)",
            "Ps has no chapter 200 (only 150 chapters); "
            "Ps 2 has no verse 99 (only 12 verses)",
        ),
        # Valid ranges contribute nothing.
        (
            BibleRef(
                [
                    _range("JHN", 3, 16, 3, 16),
                    _range("JHN", 30, 1, 30, 1),
                    _whole_book("XYZ"),
                ]
            ),
            "JHN has no chapter 30 (only 21 chapters); "
            "XYZ is not in versification 'eng'",
            "John has no chapter 30 (only 21 chapters); "
            "XYZ is not in versification 'eng'",
        ),
        # A range that spans books must run forward in the versification.
        (
            BibleRef.for_book("JHN", "MAT"),
            "JHN: range ends in an earlier book (MAT) than it starts",
            "John: range ends in an earlier book (Matt) than it starts",
        ),
        (
            BibleRef.for_range("MAT", 28, 16, end_book="MRK", end_chapter=20),
            "MRK has no chapter 20 (only 16 chapters)",
            "Mark has no chapter 20 (only 16 chapters)",
        ),
        (
            BibleRef.for_book("MAT", "XYZ"),
            "XYZ is not in versification 'eng'",
            "XYZ is not in versification 'eng'",
        ),
    ],
)
def test_bible_ref_invalid_reason(ref: BibleRef, reason: str, styled: str) -> None:
    """The reason names the book by its ID, or as a style names it."""
    ref = BibleRef(ref.ranges, Versification.named("eng"))
    assert ref.is_valid() is False
    assert ref.invalid_reason() == reason
    assert ref.invalid_reason(SBL) == styled


def test_bible_ref_without_versification_is_invalid() -> None:
    """A missing versification is itself the reason."""
    ref = BibleRef.for_range("JHN", 3, 16)
    assert ref.is_valid() is False
    assert ref.invalid_reason() == "no versification is set"


def test_invalid_reason_unnamed_versification(tmp_path: pathlib.Path) -> None:
    """A versification with no identifier is not named in the message."""
    path = tmp_path / "v.json"
    path.write_text('{"maxVerses": {"GEN": [31]}}')
    versification = Versification.from_file(str(path))
    ref = BibleRef.for_book("XYZ", versification=versification)
    assert ref.invalid_reason() == "XYZ is not in versification"


def test_invalid_reason_excluded_verses() -> None:
    """An excluded verse is valid unless asked for, and may always be spanned."""

    def reason(text: str, versification: str) -> str | None:
        ref = _parsed(text, versification)
        assert ref.is_valid()
        assert ref.invalid_reason() is None
        strict = ref.invalid_reason(allow_excluded=False)
        assert ref.is_valid(allow_excluded=False) == (strict is None)
        return strict

    assert reason("Ps 147:1", "vulgata") == "PSA 147 has no verse 1"
    assert reason("Ps 147:1–20", "vulgata") == "PSA 147 has no verse 1"
    assert reason("Ps 147:12", "vulgata") is None
    assert reason("Ps 114:9–115:10", "vulgata") is None
    assert reason("Matt 17:21", "nabre") == "MAT 17 has no verse 21"
    assert reason("Matt 17:22", "nabre") is None
    assert reason("Tob 11:11–13", "nabre") is None
    assert reason("Tob 11:12–13", "nabre") == "TOB 11 has no verse 12"
    # Whole chapters name no verse.
    assert reason("Ps 147", "vulgata") is None


# --- Formatting ---


@pytest.mark.parametrize(
    ("ref", "expected"),
    [
        (BibleRef(), ""),
        (BibleRef.for_range("GEN", 1, 1, end_verse=5), "Gen 1:1–5"),
        (BibleRef.for_book("GEN"), "Gen"),
        (
            BibleRef([_range("JHN", 3, 16, 3, 16), _range("JHN", 3, 18, 3, 20)]),
            "John 3:16, 18–20",
        ),
        (
            BibleRef([_range("ROM", 1, 18, 1, 32), _range("ROM", 2, 1, 2, 5)]),
            "Rom 1:18–32; 2:1–5",
        ),
        (
            BibleRef.for_range(
                "MRK", 5, 3, start_subverse="b", end_verse=5, end_subverse="a"
            ),
            "Mark 5:3b–5a",
        ),
        (BibleRef([_range("GEN", 1, 1, 1, 1, "a", "c")]), "Gen 1:1a–c"),
        # The pericope adulterae
        (
            BibleRef.for_range("JHN", 7, 53, end_chapter=8, end_verse=11),
            "John 7:53–8:11",
        ),
        (BibleRef.for_range("ISA", 1, end_chapter=39), "Isa 1–39"),
        # Unspecified end verse means "ff"
        (BibleRef([_range("PHP", 2, 5, 2, None)]), "Phil 2:5ff"),
        (
            BibleRef([_range("JHN", 3, 16, 3, 16), _range("ROM", 8, 28, 8, 39)]),
            "John 3:16; Rom 8:28–39",
        ),
        (
            BibleRef(
                [
                    _range("JHN", 3, 16, 3, 16),
                    _range("JHN", 3, 18, 3, 20),
                    _range("ROM", 8, 28, 8, 39),
                ]
            ),
            "John 3:16, 18–20; Rom 8:28–39",
        ),
        # A book is named again when it returns after another.
        (
            BibleRef(
                [
                    _range("JHN", 3, 16, 3, 16),
                    _range("ROM", 8, 28, 8, 28),
                    _range("JHN", 1, 1, 1, 1),
                ]
            ),
            "John 3:16; Rom 8:28; John 1:1",
        ),
        (BibleRef([_whole_book("GEN"), _whole_book("EXO")]), "Gen; Exod"),
        (
            BibleRef([_whole_book("JHN"), _range("JHN", 3, 16, 3, 16)]),
            "John; John 3:16",
        ),
        # Whole chapters mixed with verses
        (
            BibleRef([_range("GEN", 1, None, 1, None), _range("GEN", 2, 4, 2, 4)]),
            "Gen 1; 2:4",
        ),
        (BibleRef([_range("GEN", 1, None, 2, 4)]), "Gen 1–2:4"),
        (
            BibleRef([_range("JHN", 3, 16, 3, 16), _range("JHN", 4, None, 4, None)]),
            "John 3:16; 4",
        ),
        (
            BibleRef([_range("JHN", 3, None, 3, None), _range("JHN", 3, 5, 3, 5)]),
            "John 3; 3:5",
        ),
        (BibleRef([_range("JHN", 3, None, 3, 5)]), "John 3–3:5"),
        (
            BibleRef([_range("JHN", 3, 16, 3, None), _range("JHN", 3, 20, 3, 20)]),
            "John 3:16ff, 20",
        ),
        # The Psalms are plural when more than one is cited under the name.
        (BibleRef.for_range("PSA", 23, 1), "Ps 23:1"),
        (BibleRef.for_range("PSA", 23), "Ps 23"),
        (BibleRef.for_range("PSA", 1, end_chapter=2), "Pss 1–2"),
        (BibleRef.for_book("PSA"), "Pss"),
        (
            BibleRef([_range("PSA", 2, 1, 2, 3), _range("PSA", 2, 7, 2, 9)]),
            "Ps 2:1–3, 7–9",
        ),
        (
            BibleRef([_range("PSA", 2, 1, 2, 3), _range("PSA", 110, 1, 110, 1)]),
            "Pss 2:1–3; 110:1",
        ),
        (
            BibleRef(
                [
                    _range("PSA", 2, 1, 2, 1),
                    _range("JHN", 1, 1, 1, 1),
                    _range("PSA", 3, 1, 3, 1),
                ]
            ),
            "Ps 2:1; John 1:1; Ps 3:1",
        ),
        # Ranges that span books
        (BibleRef.for_book("MAT", "JHN"), "Matt–John"),
        (BibleRef.for_book("PSA", "PRO"), "Pss–Prov"),
        (
            BibleRef.for_range(
                "1SA", 31, 1, end_book="2SA", end_chapter=1, end_verse=27
            ),
            "1 Sam 31:1–2 Sam 1:27",
        ),
        (
            BibleRef.for_range("GEN", 50, end_book="EXO", end_chapter=2),
            "Gen 50–Exod 2",
        ),
        (BibleRef([VerseRange(RefPoint("MAT"), RefPoint("MRK", 3))]), "Matt–Mark 3"),
        (BibleRef.for_range("JOB", 42, end_book="PSA", end_chapter=3), "Job 42–Ps 3"),
        # What follows such a range is in the book where it ended.
        (
            BibleRef(
                [
                    VerseRange(RefPoint("1SA", 31), RefPoint("2SA", 1)),
                    _range("2SA", 3, 1, 3, 1),
                ]
            ),
            "1 Sam 31–2 Sam 1; 3:1",
        ),
    ],
)
def test_format(ref: BibleRef, expected: str) -> None:
    """Test formatting references that have no versification."""
    assert ref.format(SBL) == expected


def test_format_with_custom_style() -> None:
    """Test formatting with a custom style."""
    style = RefStyle(
        names={"GEN": "Genesi", "EXO": "Esodo"},
        chapter_verse_separator=", ",
        range_separator="-",  # Use hyphen instead of en dash
        verse_range_separator=".",
        chapter_separator="; ",
    )
    ref = BibleRef([_range("GEN", 1, 1, 1, 5), _range("GEN", 1, 8, 1, 10, "b", "a")])
    assert ref.format(style) == "Genesi 1, 1-5.8b-10a"

    style = RefStyle(
        names={"JHN": "Giovanni", "ROM": "Romani"},
        chapter_verse_separator=",",
        range_separator="-",
        verse_range_separator="; ",
        chapter_separator=" e ",
    )
    ref = BibleRef(
        [
            _range("JHN", 3, 16, 3, 16),
            _range("JHN", 3, 18, 3, 20),
            _range("ROM", 8, 28, 8, 39),
        ]
    )
    assert ref.format(style) == "Giovanni 3,16; 18-20 e Romani 8,28-39"


def test_format_unknown_book() -> None:
    """Test formatting with an unknown book ID."""
    with pytest.raises(ValueError, match="Unknown book ID"):
        BibleRef.for_book("XYZ").format(SBL)


@pytest.mark.parametrize(
    ("ref", "with_versification", "without"),
    [
        (BibleRef.for_range("PHM", 1, 6), "Phlm 6", "Phlm 1:6"),
        (BibleRef.for_range("JUD", 1, 3, end_verse=5), "Jude 3–5", "Jude 1:3–5"),
        (
            BibleRef(
                [
                    _range("JUD", 1, 1, 1, 1),
                    _range("JUD", 1, 4, 1, 4),
                    _range("JUD", 1, 17, 1, 17),
                ]
            ),
            "Jude 1, 4, 17",
            "Jude 1:1, 4, 17",
        ),
        (BibleRef([_range("JUD", 1, 3, 1, None)]), "Jude 3ff", "Jude 1:3ff"),
        # The whole chapter of a one-chapter book is named by the book alone.
        (BibleRef.for_range("JUD", 1), "Jude", "Jude 1"),
        # A verse after the whole book needs the name again.
        (
            BibleRef([_range("JUD", 1, None, 1, None), _range("JUD", 1, 5, 1, 5)]),
            "Jude; Jude 5",
            "Jude 1; 1:5",
        ),
        (
            BibleRef.for_range(
                "2JN", 1, 12, end_book="3JN", end_chapter=1, end_verse=4
            ),
            "2 John 12–3 John 4",
            "2 John 1:12–3 John 1:4",
        ),
    ],
)
def test_format_single_chapter_book(
    ref: BibleRef, with_versification: str, without: str
) -> None:
    """A versification lets the chapter of a one-chapter book be omitted."""
    assert ref.format(SBL) == without
    known = BibleRef(ref.ranges, Versification.named("eng"))
    assert known.format(SBL) == with_versification


# --- Mapping between versifications ---


def test_map_to_with_mapping() -> None:
    """Test mapping a verse range where verses have explicit mappings."""
    eng = Versification.named("eng")
    org = Versification.named("org")
    # eng GEN 32:1-32 maps to org GEN 32:2-33
    ref = BibleRef.for_range("GEN", 32, 1, end_verse=32, versification=eng)
    mapped = ref.map_to(org)
    assert mapped is not None
    assert mapped.versification is org
    assert _spans(mapped) == [("GEN", 32, 2, "GEN", 32, 33)]


def test_map_to_identity() -> None:
    """Test mapping a verse with no mapping entry passes through unchanged."""
    eng = Versification.named("eng")
    ref = BibleRef.for_range("GEN", 1, 1, end_verse=5, versification=eng)
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("GEN", 1, 1, "GEN", 1, 5)]


def test_map_to_same_versification() -> None:
    """Test mapping to the same versification returns equivalent ref."""
    eng = Versification.named("eng")
    ref = BibleRef.for_range("GEN", 32, 1, end_verse=32, versification=eng)
    mapped = ref.map_to(eng)
    assert mapped == ref
    assert mapped is not None
    assert mapped.versification is eng


def test_map_to_cross_book() -> None:
    """Test mapping a verse range that changes book ID."""
    # eng BAR 6:1-5 maps to org LJE 1:1-5
    ref = BibleRef.for_range(
        "BAR", 6, 1, end_verse=5, versification=Versification.named("eng")
    )
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("LJE", 1, 1, "LJE", 1, 5)]


def test_map_to_between_non_org() -> None:
    """Test mapping between two non-org versifications."""
    vul = Versification.named("vulgata")
    ref = BibleRef.for_range(
        "GEN", 32, 1, end_verse=5, versification=Versification.named("eng")
    )
    mapped = ref.map_to(vul)
    assert mapped is not None
    assert mapped.versification is vul
    assert mapped.books() == ["GEN"]


def test_map_to_whole_chapter() -> None:
    """A whole chapter that is whole chapters in the target stays so."""
    ref = BibleRef.for_range("GEN", 1, versification=Versification.named("eng"))
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("GEN", 1, None, "GEN", 1, None)]


def test_map_to_whole_chapter_to_verses() -> None:
    """A whole chapter that is not whole chapters in the target becomes verses.

    eng Gen 31:55 is org Gen 32:1, so eng Gen 32 is org Gen 32:2-33.
    """
    ref = BibleRef.for_range("GEN", 32, versification=Versification.named("eng"))
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("GEN", 32, 2, "GEN", 32, 33)]


@pytest.mark.parametrize(
    ("source", "reference", "target", "expected"),
    [
        # Renumbered psalms stay whole.
        ("vulgata", "Ps 50", "org", "Ps 51"),
        ("org", "Ps 51", "vulgata", "Ps 50"),
        ("vulgata", "Ps 50-52", "org", "Pss 51–53"),
        ("org", "Ps 119", "vulgata", "Ps 118"),
        # One psalm that is two, and two that are one.
        ("vulgata", "Ps 9", "org", "Pss 9–10"),
        ("org", "Ps 9-10", "vulgata", "Ps 9"),
        ("vulgata", "Ps 113", "org", "Pss 114–115"),
        ("org", "Ps 116", "vulgata", "Pss 114–115"),
        # Part of a chapter. The Clementine's Ps 115 begins at verse 10, and
        # its Ps 147 at verse 12, continuing Ps 114 and 146.
        ("org", "Ps 10", "vulgata", "Ps 9:22–39"),
        ("vulgata", "Ps 114", "org", "Ps 116:1–9"),
        ("vulgata", "Ps 115", "org", "Ps 116:10–19"),
        ("vulgata", "Ps 146", "org", "Ps 147:1–11"),
        ("vulgata", "Ps 147", "org", "Ps 147:12–20"),
        ("vulgata", "Mal 3", "org", "Mal 3:1–18"),
        ("vulgata", "Mal 4", "org", "Mal 3:19–24"),
        ("org", "Mal 3", "vulgata", "Mal 3–4"),
        # eng's unnumbered psalm titles are its verse 0, which org counts as
        # one verse or, in Ps 51, two.
        ("eng", "Ps 3", "org", "Ps 3"),
        ("org", "Ps 3", "eng", "Ps 3"),
        ("eng", "Ps 51", "org", "Ps 51"),
        ("org", "Ps 51", "eng", "Ps 51"),
        ("vulgata", "Ps 12", "org", "Ps 13"),
        # Psalms cited in the plural are renumbered like the singular.
        ("vulgata", "Pss 50:3-5", "org", "Ps 51:3–5"),
        ("vulgata", "Pss 50-51", "org", "Pss 51–52"),
        # A range from a chapter to a verse keeps its form where it can.
        ("eng", "Gen 1–2:4", "org", "Gen 1–2:4"),
        ("eng", "Gen 31–32:5", "org", "Gen 31–32:6"),
    ],
)
def test_map_whole_chapters(
    source: str, reference: str, target: str, expected: str
) -> None:
    """Whole chapters are mapped through their first and last verses."""
    assert _mapped(reference, source, target) == expected


@pytest.mark.parametrize(
    ("source", "reference", "target", "expected"),
    [
        # A book the target numbers differently is still the whole book.
        ("vulgata", "Ps", "org", "Pss"),
        ("eng", "Gen", "org", "Gen"),
        # Vulgate Daniel holds what org divides among four books.
        (
            "vulgata",
            "Dan",
            "org",
            "Dan 1:1–3:23; Sg Three; Dan 3:24–12:13; Sus; Bel",
        ),
        # And org's Daniel is only part of the Vulgate's.
        ("org", "Dan", "vulgata", "Dan 1–12"),
        ("org", "Bel", "vulgata", "Dan 13:65–14:41"),
    ],
)
def test_map_whole_book(
    source: str, reference: str, target: str, expected: str
) -> None:
    """A whole book is mapped as its chapters are."""
    assert _mapped(reference, source, target) == expected


def test_map_whole_book_missing_from_source() -> None:
    """A book the source does not have cannot be mapped."""
    ref = BibleRef.for_book("XYZ", versification=Versification.named("eng"))
    assert ref.map_to(Versification.named("org")) is None


def test_map_to_nonexistent_in_target() -> None:
    """Test that map_to returns None when a verse doesn't exist in the target."""
    # BAR 6:73 maps to LJE 1:73 but LJE only has 72 verses in org
    ref = BibleRef.for_range(
        "BAR", 6, 70, end_verse=73, versification=Versification.named("eng")
    )
    assert ref.map_to(Versification.named("org")) is None


def test_map_to_ff_notation() -> None:
    """Test mapping a reference with ff notation."""
    # eng GEN 32:1ff -> org GEN 32:2ff
    ref = BibleRef([_range("GEN", 32, 1, 32, None)], Versification.named("eng"))
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("GEN", 32, 2, "GEN", 32, None)]
    assert mapped.ranges[0].has_following_verses()


def _subverse_versification(tmp_path: pathlib.Path) -> Versification:
    """Build a Versification that maps a plain verse to a subverse location."""
    path = tmp_path / "sub.json"
    path.write_text(
        '{"maxVerses": {"ESG": [39, 23, 22, 47, 28, 14, 10, 41, 32, 14]},'
        ' "mappedVerses": {"ESG 8:13": "ESG 8:12a"}}'
    )
    return Versification.from_file(str(path), "sub")


def test_map_to_with_subverse(tmp_path: pathlib.Path) -> None:
    """Test mapping to a subverse location and back."""
    sub = _subverse_versification(tmp_path)
    org = Versification.named("org")
    # sub ESG 8:13 maps to org ESG 8:12a (single verse)
    ref = BibleRef.for_range("ESG", 8, 13, versification=sub)
    mapped = ref.map_to(org)
    assert mapped is not None
    assert mapped.ranges[0].start == RefPoint("ESG", 8, 12, "a")

    back = mapped.map_to(sub)
    assert back is not None
    assert back.ranges[0].start == RefPoint("ESG", 8, 13)


def test_map_to_1_to_n() -> None:
    """Test mapping with a 1:N verse mapping."""
    # rsc PSA 141:0 maps to org PSA 142:0-1
    ref = BibleRef.for_range("PSA", 141, 0, versification=Versification.named("rsc"))
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("PSA", 142, 0, "PSA", 142, 1)]


def test_map_to_n_to_1() -> None:
    """Test mapping with an N:1 verse mapping."""
    # rsc PSA 89:1-2 (the title, then the first line) maps to org PSA 90:1
    ref = BibleRef.for_range(
        "PSA", 89, 1, end_verse=2, versification=Versification.named("rsc")
    )
    mapped = ref.map_to(Versification.named("org"))
    assert mapped is not None
    assert _spans(mapped) == [("PSA", 90, 1, "PSA", 90, 1)]


def test_map_to_no_versification() -> None:
    """Test that map_to returns None when versification is not set."""
    ref = BibleRef.for_range("GEN", 1, 1)
    assert ref.map_to(Versification.named("org")) is None


@pytest.mark.parametrize(
    ("source", "reference", "target", "expected"),
    [
        # Susanna and Bel are Vulgate Dan 13-14, and the seam falls at 13:65.
        ("vulgata", "Dan 13", "org", "Sus; Bel 1"),
        ("vulgata", "Dan 13:60-65", "org", "Sus 60–64; Bel 1"),
        ("vulgata", "Dan 13:60ff", "org", "Sus 60–64; Bel 1"),
        ("vulgata", "Dan 13:65-14:3", "org", "Bel 1–4"),
        ("vulgata", "Dan 12-14", "org", "Dan 12; Sus; Bel"),
        ("org", "Bel 1:1-3", "vulgata", "Dan 13:65–14:2"),
        # A range can leave a book and come back: the Song of the Three is
        # Vulgate Dan 3:24-90.
        ("vulgata", "Dan 3", "org", "Dan 3:1–23; Sg Three; Dan 3:24–33"),
        ("vulgata", "Dan 3:1-30", "org", "Dan 3:1–23; Sg Three 1–7"),
        ("vulgata", "Dan 3:50", "org", "Sg Three 27"),
        # Ranges of one reference that map into one book stay together.
        ("vulgata", "Ps 50:3; 51:4", "org", "Pss 51:3; 52:4"),
    ],
)
def test_map_into_several_books(
    source: str, reference: str, target: str, expected: str
) -> None:
    """A range that maps into more than one book becomes a range in each."""
    assert _mapped(reference, source, target) == expected


@pytest.mark.parametrize(
    ("source", "reference", "target", "expected"),
    [
        # Books that are consecutive in the target too remain one range.
        ("eng", "Matt–John", "org", "Matt–John"),
        ("eng", "Gen–Deut", "vulgata", "Gen–Deut"),
        ("eng", "Gen 50–Exod 2:3", "org", "Gen 50–Exod 2:3"),
        ("eng", "Gen 31:1–Exod 2", "org", "Gen 31:1–Exod 2"),
        # Each end is renumbered: eng Mal 4 is org Mal 3:19-24.
        ("eng", "Mal 4–Matt 1", "org", "Mal 3:19–Matt 1"),
        ("org", "Mal 3–Matt 1", "eng", "Mal 3–Matt 1"),
        # The books between the ends are those of the source's order, which
        # the target may not keep together: nabre sets Tobit and Judith
        # between Nehemiah and Esther, and eng sets them after Revelation.
        # The books that are still consecutive are rejoined.
        ("nabre", "Neh–Jdt", "eng", "Neh; Tob–Jdt"),
        ("nabre", "Ezra 9–Jdt 2:3", "eng", "Ezra 9–Neh 13; Tob–Jdt 2:3"),
        ("nabre", "Ezra 9:1–Jdt 2:3", "eng", "Ezra 9:1–Neh 13:31; Tob–Jdt 2:3"),
        # eng has no place for the deuterocanonical books among the others.
        (
            "eng",
            "Gen–Rev",
            "nabre",
            "Gen–Neh; Esth; Job–Song; Isa–Lam; Ezek–Dan 12; Hos–Rev",
        ),
    ],
)
def test_map_range_that_spans_books(
    source: str, reference: str, target: str, expected: str
) -> None:
    """A range that spans books is mapped book by book and rejoined where it can be."""
    assert _mapped(reference, source, target) == expected


def test_map_range_that_spans_books_backwards() -> None:
    """A range that ends in an earlier book than it starts cannot be mapped."""
    ref = BibleRef.for_book("JHN", "MAT", versification=Versification.named("eng"))
    assert ref.map_to(Versification.named("org")) is None


# --- Following verses and ranges ---


def test_resolve_following_verses() -> None:
    """Test resolving ff ranges to definite references."""
    versification = Versification.named("eng")

    ref = BibleRef([_range("MAT", 12, 46, 12, None)], versification, "Matt 12:46ff")
    resolved = ref.resolve_following_verses()
    assert resolved.format(SBL) == "Matt 12:46–50"
    assert resolved.original_text == "Matt 12:46ff"
    # The original is unchanged.
    assert ref.format(SBL) == "Matt 12:46ff"

    ref = BibleRef(
        [_range("JHN", 8, 48, 8, None), _range("JHN", 10, 22, 10, None)],
        versification,
    )
    assert ref.resolve_following_verses().format(SBL) == "John 8:48–59; 10:22–42"

    # Other ranges are left alone, as is a reference with no versification.
    assert _parsed("John 3; 4:1–5").resolve_following_verses() == _parsed(
        "John 3; 4:1–5"
    )
    naive = BibleRef([_range("MAT", 12, 46, 12, None)])
    assert naive.resolve_following_verses() is naive


def test_bible_ref_range_refs() -> None:
    """Test the range_refs method of BibleRef."""
    versification = Versification.named("eng")

    # Empty BibleRef yields nothing
    assert list(BibleRef(versification=versification).range_refs()) == []

    # Single range
    ref = BibleRef.for_range(
        "JHN", 3, 16, original_text="John 3:16", versification=versification
    )
    (only,) = ref.range_refs()
    assert isinstance(only, BibleRef)
    assert only == ref
    assert only.versification is versification
    assert only.original_text == "John 3:16"

    # Several ranges, each with the text it was parsed from
    ref = BibleRef(
        [
            _range("JHN", 3, 16, 3, 16, original_text="John 3:16"),
            _range("JHN", 3, 18, 3, 20, original_text="18-20"),
            _range("ROM", 8, 28, 8, 39, original_text="Rom 8:28-39"),
            _whole_book("JUD"),
        ],
        versification,
        original_text="John 3:16, 18-20; Rom 8:28-39; Jude",
    )
    range_refs = list(ref.range_refs())
    assert [r.format(SBL) for r in range_refs] == [
        "John 3:16",
        "John 3:18–20",
        "Rom 8:28–39",
        "Jude",
    ]
    assert [r.original_text for r in range_refs] == [
        "John 3:16",
        "18-20",
        "Rom 8:28-39",
        None,
    ]
    assert all(r.versification is versification for r in range_refs)
    assert all(r.is_single_range() for r in range_refs)


# --- Verse keys ---


@pytest.mark.parametrize(
    ("ref", "keys"),
    [
        # 43 (John) | 003 (chapter 3) | 016 (verse 16) | 00 (base verse)
        (BibleRef.for_range("JHN", 3, 16), [(4300301600, 4300301600)]),
        # Genesis is book 1
        (BibleRef.for_range("GEN", 1, 1, end_verse=5), [(100100100, 100100500)]),
        # The pericope adulterae
        (
            BibleRef.for_range("JHN", 7, 53, end_chapter=8, end_verse=11),
            [(4300705300, 4300801100)],
        ),
        # Isaiah is book 23
        (BibleRef.for_range("ISA", 7, 14), [(2300701400, 2300701400)]),
        (
            BibleRef([_range("JHN", 3, 16, 3, 16), _range("JHN", 3, 18, 3, 20)]),
            [(4300301600, 4300301600), (4300301800, 4300302000)],
        ),
        (
            BibleRef([_range("JHN", 3, 16, 3, 16), _range("ROM", 8, 28, 8, 39)]),
            [(4300301600, 4300301600), (4500802800, 4500803900)],
        ),
        # A whole chapter starts at verse 0. The last verse of John 6 is 71,
        # and a whole-chapter end spreads to ordinal 99.
        (BibleRef.for_range("JHN", 6), [(4300600000, 4300607199)]),
        # The last verse of Matthew 12 is 50; an "ff" end spreads likewise.
        (BibleRef([_range("MAT", 12, 46, 12, None)]), [(4001204600, 4001205099)]),
        # A whole book starts as a whole chapter does. John ends at 21:25.
        (BibleRef.for_book("JHN"), [(4300100000, 4302102599)]),
        (
            BibleRef([_whole_book("GEN"), _whole_book("REV")]),
            [(100100000, 105002699), (6600100000, 6602202199)],
        ),
        # From a chapter to a verse
        (BibleRef([_range("GEN", 1, None, 2, 4)]), [(100100000, 100200400)]),
        # A range that spans books is one pair of keys.
        (BibleRef.for_book("MAT", "JHN"), [(4000100000, 4302102599)]),
        (
            BibleRef.for_range(
                "1SA", 31, 1, end_book="2SA", end_chapter=1, end_verse=27
            ),
            [(903100100, 1000102700)],
        ),
        (
            BibleRef.for_range("GEN", 50, end_book="EXO", end_chapter=2),
            [(105000000, 200202599)],
        ),
        # An unknown book yields nothing, at either end of a range.
        (BibleRef.for_range("XYZ", 1, 1), []),
        (BibleRef.for_book("XYZ"), []),
        (BibleRef.for_book("MAT", "XYZ"), []),
        (
            BibleRef([_range("JHN", 3, 16, 3, 16), _range("XYZ", 1, 1, 1, 1)]),
            [(4300301600, 4300301600)],
        ),
        (BibleRef(), []),
    ],
)
def test_range_keys(ref: BibleRef, keys: list[tuple[int, int]]) -> None:
    """Test range_keys in the eng versification."""
    ref = BibleRef(ref.ranges, Versification.named("eng"))
    assert list(ref.range_keys()) == keys


def test_range_keys_without_versification() -> None:
    """Test range_keys when no versification is set."""
    assert list(BibleRef.for_range("JHN", 3, 16).range_keys()) == []


def test_range_keys_inserted_verse_distinct_from_base() -> None:
    """An inserted verse (ESG 4:17k) keys distinctly from its base verse.

    The Greek additions to Esther follow but are not part of ESG 4:17, so
    4:17k must not collide with 4:17, and must sort between 4:17 and 4:18.
    """
    lxx = Versification.named("lxx")

    def start(subverse: str, verse: int = 17) -> int:
        ref = BibleRef.for_range(
            "ESG", 4, verse, start_subverse=subverse, versification=lxx
        )
        return next(iter(ref.range_keys()))[0]

    base = start("")  # ESG 4:17
    ins_k = start("k")  # ESG 4:17k (tenth insertion, j skipped)
    following = start("", 18)  # ESG 4:18

    assert ins_k != base
    # 'k' is the 10th insertion letter (a=1..i=9, k=10)
    assert ins_k - base == 10
    assert base < ins_k < following


def test_range_keys_inserted_verses_sort_in_reading_order() -> None:
    """The additions to Esther (ESG 4:17...) key in ascending order, all distinct.

    The letters are taken from those the versification actually treats as
    insertions (the Esther additions skip both 'j' and 'v'), so the test does
    not assume a particular alphabet.
    """
    lxx = Versification.named("lxx")
    letters = [
        c for c in string.ascii_lowercase if lxx.partial_ordinal("ESG", 4, 17, c) > 0
    ]
    assert "k" in letters
    assert "j" not in letters
    assert "v" not in letters

    def start(subverse: str) -> int:
        ref = BibleRef.for_range(
            "ESG", 4, 17, start_subverse=subverse, versification=lxx
        )
        return next(iter(ref.range_keys()))[0]

    keys = [start("")] + [start(c) for c in letters]
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)
    # Ordinals are contiguous from 1: base then each insertion in turn.
    assert [k - keys[0] for k in keys] == list(range(len(keys)))


def test_range_keys_addition_a_precedes_its_base_verse() -> None:
    """Addition A to Esther (ESG 1:1a-r) keys before ESG 1:1, as it reads."""
    cei = Versification.named("cei")

    def keys(
        verse: int | None = 1, subverse: str = "", end_verse: int | None = None
    ) -> tuple[int, int]:
        ref = BibleRef.for_range(
            "ESG",
            1,
            verse,
            end_verse=end_verse,
            start_subverse=subverse,
            versification=cei,
        )
        return next(iter(ref.range_keys()))

    first, last, base, following = keys(1, "a"), keys(1, "r"), keys(1), keys(2)
    assert first < last < base < following
    # A portion of the base verse, not an inserted verse, shares its key.
    assert cei.partial_ordinal("ESG", 1, 1, "z") == cei.partial_ordinal("ESG", 1, 1, "")
    # "ESG 1:1-3" leaves the addition out; the whole chapter takes it in.
    assert keys(1, end_verse=3)[0] > last[1]
    assert keys(None)[0] < first[0]


def test_range_keys_portion_of_uninserted_verse_collapses() -> None:
    """A subverse on a verse with no inserted verses shares the base key.

    A scholarly "8:1a" cites part of a single verse; it is not an inserted
    verse and must map to the same key as 8:1 rather than a distinct one.
    """
    eng = Versification.named("eng")

    def key(subverse: str) -> tuple[int, int]:
        ref = BibleRef.for_range(
            "ROM", 8, 1, start_subverse=subverse, versification=eng
        )
        return next(iter(ref.range_keys()))

    assert key("a") == key("")
    assert key("b") == key("")


def test_range_keys_inserted_verse_range() -> None:
    """A range across insertions (ESG 4:17a-4:17e) keys start-to-end correctly."""
    ref = BibleRef.for_range(
        "ESG",
        4,
        17,
        end_verse=17,
        start_subverse="a",
        end_subverse="e",
        versification=Versification.named("lxx"),
    )
    (start_key, end_key) = next(iter(ref.range_keys()))
    assert end_key - start_key == 4  # a=1 .. e=5
    assert start_key % 100 == 1
    assert end_key % 100 == 5


def test_partial_ordinal_direct() -> None:
    """Versification.partial_ordinal reflects partialVerses membership."""
    lxx = Versification.named("lxx")
    assert lxx.partial_ordinal("ESG", 4, 17, "") == 0
    assert lxx.partial_ordinal("ESG", 4, 17, "a") == 1
    assert lxx.partial_ordinal("ESG", 4, 17, "i") == 9
    assert lxx.partial_ordinal("ESG", 4, 17, "k") == 10
    assert lxx.partial_ordinal("ESG", 4, 17, "z") == 24
    # A verse with no inserted verses: any subverse collapses to the base.
    assert lxx.partial_ordinal("ROM", 8, 1, "a") == 0
    # A verse absent from this versification's partialVerses.
    assert Versification.named("eng").partial_ordinal("ESG", 4, 17, "k") == 0


def test_for_range_end_subverse_without_end_verse() -> None:
    """An end subverse alone ends the range in the start verse."""
    ref = BibleRef.for_range("GEN", 1, 3, start_subverse="a", end_subverse="b")
    (verse_range,) = ref.ranges
    assert verse_range.start == RefPoint("GEN", 1, 3, "a")
    assert verse_range.end == RefPoint("GEN", 1, 3, "b")


def test_lettered_chapter_the_versification_lacks_is_invalid() -> None:
    """A whole lettered chapter is invalid where there are no lettered chapters."""
    point = RefPoint("EST", 4, 17, "C")
    ref = BibleRef((VerseRange(point, point),), Versification.named("eng"))
    assert ref.invalid_reason() == "EST has no chapter C"
    assert len(list(ref.range_keys())) == 1


def test_map_whole_chapter_ends_before_excluded_verses(tmp_path: pathlib.Path) -> None:
    """A whole chapter maps through the last verse the versification has."""
    path = tmp_path / "v.json"
    path.write_text(
        '{"maxVerses": {"GEN": [31, 10]}, "excludedVerses": ["GEN 2:9-10"]}'
    )
    source = Versification.from_file(str(path))
    chapter = RefPoint("GEN", 2)
    mapped = BibleRef((VerseRange(chapter, chapter),), source).map_to(
        Versification.named("org")
    )
    assert mapped is not None
    assert mapped.format(RefStyle.named("en-sbl")) == "Gen 2:1–8"


def test_map_chapter_the_source_lacks_passes_through() -> None:
    """A whole chapter the source does not have is left as it is."""
    chapter = RefPoint("GEN", 99)
    ranges = (VerseRange(chapter, chapter),)
    mapped = BibleRef(ranges, Versification.named("eng")).map_to(
        Versification.named("org")
    )
    assert mapped is not None
    assert mapped.ranges == ranges


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (RefPoint("GEN", 1), RefPoint("XXX", 2)),
        (RefPoint("EXO", 1), RefPoint("GEN", 2)),
        (RefPoint("GEN", 1, 1), RefPoint("EXO", 1, 99)),
    ],
    ids=["unknown book", "books out of order", "verse the book lacks"],
)
def test_map_unmappable_range_across_books(start: RefPoint, end: RefPoint) -> None:
    """A range across books does not map if any part of it cannot."""
    ref = BibleRef((VerseRange(start, end),), Versification.named("eng"))
    assert ref.map_to(Versification.named("org")) is None


def test_map_range_ending_in_book_that_begins_with_lettered_chapter() -> None:
    """A range into NABRE Esther takes in Esther A, which begins the book."""
    ref = BibleRef(
        (VerseRange(RefPoint("JDT", 16, 1), RefPoint("EST", 1, 5)),),
        Versification.named("nabre"),
    )
    mapped = ref.map_to(Versification.named("cei"))
    assert mapped is not None
    assert (
        mapped.format(RefStyle.named("en-sbl"))
        == "Jdt 16:1–25; Add Esth 1:1a–r; Esth 1:1–5"
    )


@pytest.mark.parametrize(
    ("source", "reference", "target", "expected"),
    [
        # The Vulgate's Esther 11 is the end of the Greek book and its start.
        ("vulgata", "Esth 11", "org", "Add Esth 10:14; 1:1–11"),
        ("vulgata", "Esth 12–13", "org", "Add Esth 1:12–17; 3:14–20; 4:18–28"),
        # The Greek Jeremiah has the oracles against the nations after 25:13.
        ("lxx", "Jer 25", "org", "Jer 25:1–12; 49:34–39"),
        # Verses that only stand in another order do not divide a range.
        ("lxx", "Exod 20", "org", "Exod 20"),
        ("lxx", "Jer", "org", "Jer"),
        # Nor do verses the source or the target excludes, even at its ends.
        ("nabre", "Matt 17:20–22", "org", "Matt 17:20–22"),
        ("org", "Matt 17:20–22", "nabre", "Matt 17:20–22"),
        ("vulgata", "Ps 147:1–14", "org", "Ps 147:12–14"),
        ("vulgata", "Ps 115:2–18", "eng", "Ps 116:10–18"),
    ],
)
def test_map_divides_where_the_target_is_interrupted(
    source: str, reference: str, target: str, expected: str
) -> None:
    """A range is divided where what it maps to is not consecutive (#52)."""
    mapped = _parsed(reference, source).map_to(Versification.named(target))
    assert mapped is not None
    assert mapped.is_valid()
    assert mapped.format(SBL) == expected
