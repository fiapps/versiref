"""Bible reference handling for versiref.

This module provides classes for representing and manipulating Bible references.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field

from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification

# Integer verse keys pack a location as BB CCC VVV SS (book, chapter, verse,
# subverse ordinal). The trailing subverse field gives inserted verses such as
# the Greek additions to Esther (ESG 4:17a-z, which follow but are not part of
# ESG 4:17) a key distinct from, and correctly ordered against, their base
# verse. The ordinal comes from the versification (Versification.partial_ordinal)
# so that a subverse cited on a verse with no inserted verses (a mere portion of
# a single verse) collapses to the base verse's key rather than being mistaken
# for an insertion. Widths: 3 chapter digits, 3 verse digits, 2 ordinal digits.
_BOOK_KEY_FACTOR = 100_000_000
_CHAPTER_KEY_FACTOR = 100_000
_VERSE_KEY_FACTOR = 100

# Inclusive subverse ordinal for a range end that spreads to a whole verse
# (a whole chapter, whole book, or "ff"): large enough to include every
# inserted verse yet below the next verse's base (which starts a new hundred).
_MAX_SUBVERSE_ORDINAL = 99


def _verse_key(book_num: int, chapter: int, verse: int, subverse_ordinal: int) -> int:
    """Pack a verse location into a single sortable integer key.

    Args:
        book_num: 1-based position of the book in the versification.
        chapter: Chapter number.
        verse: Verse number.
        subverse_ordinal: Result of :meth:`Versification.partial_ordinal`, or
            :data:`_MAX_SUBVERSE_ORDINAL` for a range end that spreads to
            include a verse's inserted verses.

    Returns:
        The packed BB CCC VVV SS integer key.

    """
    return (
        book_num * _BOOK_KEY_FACTOR
        + chapter * _CHAPTER_KEY_FACTOR
        + verse * _VERSE_KEY_FACTOR
        + subverse_ordinal
    )


def _count(n: int, noun: str) -> str:
    """Return ``n`` followed by ``noun``, pluralized with a trailing 's'."""
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _chapter_verse_reason(
    label: str, chapters: list[int], chapter: int, verse: int | None
) -> str | None:
    """Explain why a (chapter, verse) is out of range, or None if it is in range.

    Args:
        label: Reader-facing book name to name in the message.
        chapters: The book's last-verse-per-chapter list (from the versification).
        chapter: The chapter number to check.
        verse: The verse number to check, or None for an unspecified verse.

    Returns:
        An explanatory string, or None if the chapter (and verse, if specified)
        exist in the book.

    """
    if chapter < 1 or chapter > len(chapters):
        return f"{label} has no chapter {chapter} (only {_count(len(chapters), 'chapter')})"
    if verse is not None:
        max_verse = chapters[chapter - 1]
        if verse < 1 or verse > max_verse:
            return (
                f"{label} {chapter} has no verse {verse} "
                f"(only {_count(max_verse, 'verse')})"
            )
    return None


_SourceLoc = tuple[int, int, str]


def _book_segments(
    source: Versification,
    target: Versification,
    book: str,
    start: _SourceLoc,
    end: _SourceLoc,
) -> list[tuple[_SourceLoc, _SourceLoc]]:
    """Divide a source range wherever the book it maps into changes.

    Args:
        source: The Versification the range is in
        target: The Versification it is being mapped into
        book: The book ID of the range in the source
        start: The (chapter, verse, subverse) at which the range begins
        end: The (chapter, verse, subverse) at which it ends

    Returns:
        (start, end) pairs of source locations that cover the range in order,
        each mapping into a single book. The range's own subverses stay on its
        first start and last end.

    """
    segments: list[tuple[_SourceLoc, _SourceLoc]] = []
    segment_start = start
    current_book: str | None = None
    previous = start
    for chapter in range(start[0], end[0] + 1):
        first = start[1] if chapter == start[0] else source.first_verse(book, chapter)
        last = end[1] if chapter == end[0] else source.last_verse(book, chapter)
        for verse in range(first, last + 1):
            mapped = source.map_verse(book, chapter, verse, target)
            if mapped is not None:
                if current_book is None:
                    current_book = mapped[0]
                elif mapped[0] != current_book:
                    segments.append((segment_start, previous))
                    segment_start = (chapter, verse, "")
                    current_book = mapped[0]
            previous = (chapter, verse, "")
    segments.append((segment_start, end))
    return segments


def _last_present_verse(versification: Versification, book: str, chapter: int) -> int:
    """Return the last verse of a chapter that the versification does not exclude."""
    last = versification.last_verse(book, chapter)
    while last > 1 and versification.is_excluded(book, chapter, last):
        last -= 1
    return last


@dataclass(frozen=True)
class RefPoint:
    """One end of a verse range: a book, a chapter of it, or a verse.

    A point with no chapter is a whole book, and a point with a chapter but no
    verse is a whole chapter. At the start of a range such a point means the
    beginning of the book or chapter, and at the end of a range it means the
    end of it.

    Attributes:
        book: The book ID (a Paratext three-letter code such as "JHN")
        chapter: The chapter number, or None for the whole book
        verse: The verse number, or None for the whole chapter
        subverse: Letters naming a part of the verse, or "" for the whole verse

    """

    book: str
    chapter: int | None = None
    verse: int | None = None
    subverse: str = ""

    def __post_init__(self) -> None:
        """Reject values that cannot name a location.

        Raises:
            ValueError: If a verse is given without a chapter, if a number is
                negative (an unspecified chapter or verse is None), or if the
                book is "PSAS", which names the Psalms in the plural in book
                name data but is not a book.

        """
        if self.book == "PSAS":
            raise ValueError('"PSAS" is not a book ID; use "PSA"')
        if self.chapter is None and self.verse is not None:
            raise ValueError("A verse requires a chapter")
        if (self.chapter is not None and self.chapter < 0) or (
            self.verse is not None and self.verse < 0
        ):
            raise ValueError(
                "Chapter and verse numbers cannot be negative; "
                "use None for an unspecified chapter or verse"
            )


@dataclass(frozen=True)
class VerseRange:
    """Represents a range of verses, usually within a single book of the Bible.

    A verse range runs from its start point to its end point. The two are
    equal for a single verse, a single chapter, or a single book, and they
    name different books for a range that spans books, such as Matthew–John
    or 1 Sam 31:1–2 Sam 1:27.

    Either point may leave its verse, or its chapter and verse, unspecified
    (see :class:`RefPoint`). John 3:16ff, the verses from 3:16 to the end of
    the chapter, starts at John 3:16 and ends at John 3. Gen 1–2:4 starts at
    Genesis 1 and ends at Genesis 2:4.

    The text from which the range was parsed can be stored. It plays no part
    in comparing ranges.
    """

    start: RefPoint
    end: RefPoint
    original_text: str | None = field(default=None, compare=False)

    def is_single_book(self) -> bool:
        """Return True if this range starts and ends in the same book."""
        return self.start.book == self.end.book

    def is_whole_books(self) -> bool:
        """Return True if this range specifies no chapter or verse limits."""
        return self.start.chapter is None and self.end.chapter is None

    def is_whole_chapters(self) -> bool:
        """Return True if this range does not specify verse limits.

        This is also true of a range of whole books.
        """
        return self.start.verse is None and self.end.verse is None

    def has_following_verses(self) -> bool:
        """Return True if this range runs from a verse to the end of its chapter.

        This is the form written with "ff", as in John 3:16ff.
        """
        return (
            self.is_single_book()
            and self.start.verse is not None
            and self.end.verse is None
            and self.end.chapter == self.start.chapter
        )

    def invalid_reason(self) -> str | None:
        """Explain why this verse range is structurally invalid.

        This checks the internal consistency of the range only; it says nothing
        about whether the books, chapters and verses exist in any
        versification, nor about the order of two different books.

        Returns:
            An explanatory string if the range starts and ends in the same book
            and any of these conditions is met, or None if the range is
            structurally valid:

            - only one end names a chapter
            - it ends in an earlier chapter than it starts
            - it starts at a verse and ends with a whole chapter other than
              the one it starts in
            - it ends at an earlier verse of the same chapter than it starts

        """
        if not self.is_single_book():
            return None
        start, end = self.start, self.end
        if start.chapter is None or end.chapter is None:
            if start.chapter is not None or end.chapter is not None:
                return "range joins the whole book with a part of it"
            return None

        if start.chapter > end.chapter:
            return "range ends in an earlier chapter than it starts"

        if (
            start.verse is not None
            and end.verse is None
            and start.chapter != end.chapter
        ):
            return "'ff' range spans more than one chapter"

        if (
            start.chapter == end.chapter
            and start.verse is not None
            and end.verse is not None
            and start.verse > end.verse
        ):
            return "range ends at an earlier verse than it starts"

        return None

    def is_valid(self) -> bool:
        """Check if this verse range has structurally valid values.

        Returns:
            bool: True if the verse range has valid values, False otherwise

        """
        return self.invalid_reason() is None


def _range_reason(
    verse_range: VerseRange,
    versification: Versification,
    style: RefStyle | None,
    allow_excluded: bool,
) -> str | None:
    """Explain why a verse range is invalid under a versification, or None."""

    def label(book: str) -> str:
        return book if style is None else style.names.get(book, book)

    start, end = verse_range.start, verse_range.end
    for book in dict.fromkeys((start.book, end.book)):
        if not versification.includes(book):
            named = f" {versification.identifier!r}" if versification.identifier else ""
            return f"{label(book)} is not in versification{named}"

    # A structurally inconsistent range (one that ends before it starts,
    # etc.) is reported on its own terms.
    structural = verse_range.invalid_reason()
    if structural is not None:
        return f"{label(start.book)}: {structural}"

    books = list(versification.max_verses)
    if books.index(start.book) > books.index(end.book):
        return (
            f"{label(start.book)}: range ends in an earlier book "
            f"({label(end.book)}) than it starts"
        )

    for point in (start, end):
        if point.chapter is not None:
            reason = _chapter_verse_reason(
                label(point.book),
                versification.max_verses[point.book],
                point.chapter,
                point.verse,
            )
            if reason is not None:
                return reason
    if allow_excluded:
        return None
    # A range may span an excluded verse (the NABRE's Tob 11:12-14), but may
    # not begin or end on one.
    for point in (start, end):
        if (
            point.chapter is not None
            and point.verse is not None
            and versification.is_excluded(point.book, point.chapter, point.verse)
        ):
            return f"{label(point.book)} {point.chapter} has no verse {point.verse}"
    return None


def _map_chapters(
    verse_range: VerseRange, source: Versification, target: Versification
) -> list[VerseRange] | None:
    """Map a range that names chapters of a single book, as pieces in the target.

    Returns None if the start or end of a piece does not exist in the target.
    A whole-chapter range naming a chapter the source does not have passes
    through unchanged.
    """
    book = verse_range.start.book
    start_point, end_point = verse_range.start, verse_range.end
    assert start_point.chapter is not None
    assert end_point.chapter is not None
    whole = verse_range.is_whole_chapters()
    follows = verse_range.has_following_verses()
    if whole and (
        source.last_verse(book, start_point.chapter) < 1
        or source.last_verse(book, end_point.chapter) < 1
    ):
        return [
            VerseRange(
                RefPoint(book, start_point.chapter), RefPoint(book, end_point.chapter)
            )
        ]

    start: _SourceLoc
    if start_point.verse is None:
        start = (
            start_point.chapter,
            source.first_verse(book, start_point.chapter),
            "",
        )
    else:
        start = (start_point.chapter, start_point.verse, start_point.subverse)
    end: _SourceLoc
    if end_point.verse is not None:
        end = (end_point.chapter, end_point.verse, end_point.subverse)
    elif follows:
        end = (end_point.chapter, source.last_verse(book, end_point.chapter), "")
    else:
        end = (
            end_point.chapter,
            _last_present_verse(source, book, end_point.chapter),
            "",
        )

    segments = _book_segments(source, target, book, start, end)
    pieces: list[VerseRange] = []
    for index, (seg_start, seg_end) in enumerate(segments):
        first = source.map_verse(
            book, seg_start[0], seg_start[1], target, subverse=seg_start[2]
        )
        last = source.map_verse(
            book, seg_end[0], seg_end[1], target, subverse=seg_end[2], end=True
        )
        if last is not None and first is not None and last[0] != first[0]:
            # A single verse whose own mapping spans two books.
            last = source.map_verse(
                book, seg_end[0], seg_end[1], target, subverse=seg_end[2]
            )
        if first is None or last is None:
            return None
        mapped_book = first[0]
        starts_chapter = first[2] <= target.first_verse(mapped_book, first[1])
        ends_chapter = last[2] >= _last_present_verse(target, last[0], last[1])
        # A verse 0 (a psalm title) cannot be cited, so a range that would
        # begin there begins at verse 1.
        first_verse = max(first[2], 1) if start_point.verse is None else first[2]
        if whole and starts_chapter and ends_chapter:
            piece = VerseRange(
                RefPoint(mapped_book, first[1]), RefPoint(mapped_book, last[1])
            )
        elif follows and len(segments) == 1:
            piece = VerseRange(
                RefPoint(mapped_book, first[1], first[2], first[3]),
                RefPoint(mapped_book, first[1]),
            )
        elif start_point.verse is None and not whole and index == 0 and starts_chapter:
            piece = VerseRange(
                RefPoint(mapped_book, first[1]),
                RefPoint(mapped_book, last[1], last[2], last[3]),
            )
        else:
            piece = VerseRange(
                RefPoint(mapped_book, first[1], first_verse, first[3]),
                RefPoint(mapped_book, last[1], last[2], last[3]),
            )
        pieces.append(piece)
    return pieces


def _map_single_book(
    verse_range: VerseRange, source: Versification, target: Versification
) -> list[VerseRange] | None:
    """Map a range within one book, as pieces in the target, or None."""
    if not verse_range.is_whole_books():
        return _map_chapters(verse_range, source, target)

    # A whole book maps as its chapters do, and is a whole book again if they
    # fill exactly one book of the target.
    book = verse_range.start.book
    if not source.includes(book):
        return None
    chapters = VerseRange(
        RefPoint(book, 1), RefPoint(book, len(source.max_verses[book]))
    )
    pieces = _map_chapters(chapters, source, target)
    if pieces is None:
        return None
    if len(pieces) == 1 and pieces[0].is_whole_chapters():
        piece = pieces[0]
        mapped_book = piece.start.book
        if (
            target.includes(mapped_book)
            and piece.start.chapter == 1
            and piece.end.chapter == len(target.max_verses[mapped_book])
        ):
            return [VerseRange(RefPoint(mapped_book), RefPoint(mapped_book))]
    return pieces


def _divide_by_book(
    verse_range: VerseRange, versification: Versification
) -> list[VerseRange] | None:
    """Divide a range that spans books into one range for each book.

    Returns None if either book is missing from the versification or the
    range ends in an earlier book than it starts.
    """
    start, end = verse_range.start, verse_range.end
    books = list(versification.max_verses)
    if start.book not in books or end.book not in books:
        return None
    first, last = books.index(start.book), books.index(end.book)
    if first >= last:
        return None

    pieces: list[VerseRange] = []
    if start.chapter is None:
        pieces.append(VerseRange(start, start))
    else:
        last_chapter = len(versification.max_verses[start.book])
        if start.verse is None:
            book_end = RefPoint(start.book, last_chapter)
        else:
            book_end = RefPoint(
                start.book,
                last_chapter,
                versification.last_verse(start.book, last_chapter),
            )
        pieces.append(VerseRange(start, book_end))
    pieces.extend(
        VerseRange(RefPoint(book), RefPoint(book)) for book in books[first + 1 : last]
    )
    if end.chapter is None:
        pieces.append(VerseRange(end, end))
    else:
        pieces.append(VerseRange(RefPoint(end.book, 1), end))
    return pieces


def _map_range(
    verse_range: VerseRange, source: Versification, target: Versification
) -> list[VerseRange] | None:
    """Map one verse range, as ranges in the target, or None."""
    if verse_range.is_single_book():
        return _map_single_book(verse_range, source, target)

    by_book = _divide_by_book(verse_range, source)
    if by_book is None:
        return None
    mapped: list[VerseRange] = []
    for piece in by_book:
        pieces = _map_single_book(piece, source, target)
        if pieces is None:
            return None
        mapped.extend(pieces)

    return _rejoin(mapped, target)


def _rejoin(pieces: list[VerseRange], target: Versification) -> list[VerseRange]:
    """Join the mapped pieces of a range that spans books wherever they abut.

    Two pieces abut when each lies in one book, the second book follows the
    first in the target, the first piece ends its book, and the second begins
    its book. Each run of abutting pieces becomes one range, so books the
    target orders differently divide the range without undoing all of it.
    """
    books = {book: index for index, book in enumerate(target.max_verses)}

    def begins_book(point: RefPoint) -> bool:
        return point.chapter is None or (point.chapter == 1 and point.verse is None)

    def ends_book(point: RefPoint) -> bool:
        if point.chapter is None:
            return True
        last_chapter = len(target.max_verses[point.book])
        return point.chapter == last_chapter and (
            point.verse is None
            or point.verse >= _last_present_verse(target, point.book, last_chapter)
        )

    def abut(first: VerseRange, second: VerseRange) -> bool:
        return (
            first.is_single_book()
            and second.is_single_book()
            and first.end.book in books
            and books.get(second.start.book) == books[first.end.book] + 1
            and ends_book(first.end)
            and begins_book(second.start)
        )

    def joined(run: list[VerseRange]) -> VerseRange:
        if len(run) == 1:
            return run[0]
        start, end = run[0].start, run[-1].end
        if start.chapter is not None and end.chapter is None:
            # Only a range that starts with a whole book can end with one, so
            # the end is stated as the book's last chapter or verse.
            last_chapter = len(target.max_verses[end.book])
            last_verse = (
                None
                if start.verse is None
                else _last_present_verse(target, end.book, last_chapter)
            )
            end = RefPoint(end.book, last_chapter, last_verse)
        return VerseRange(start, end)

    runs: list[list[VerseRange]] = []
    for piece in pieces:
        if runs and abut(runs[-1][-1], piece):
            runs[-1].append(piece)
        else:
            runs.append([piece])
    return [joined(run) for run in runs]


@dataclass(frozen=True)
class BibleRef:
    """Represents a sequence of verse ranges within one or more books of the Bible.

    A BibleRef consists of verse ranges and the Versification they use. The
    ranges are not necessarily in canonical order. The versification can be
    None, though this will not usually be the case: without one a reference
    can be formatted, but it cannot be validated, mapped, or given verse keys.

    It optionally stores the original text from which the reference was
    parsed, which plays no part in comparing references.

    A BibleRef is immutable and hashable. The ranges may be given as any
    sequence and are stored as a tuple.
    """

    ranges: Sequence[VerseRange] = ()
    versification: Versification | None = None
    original_text: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Store the ranges as a tuple."""
        object.__setattr__(self, "ranges", tuple(self.ranges))

    def __str__(self) -> str:
        """Return a string representation of this Bible reference.

        Shows a concise representation using the versification identifier if available,
        and the reference's original text or formatted representation.

        Returns:
            A string representation of this Bible reference

        """
        ref_part = self.original_text or self.format(
            RefStyle(names=standard_names("en-sbl_abbreviations"))
        )
        if self.versification is None:
            return f'BibleRef("{ref_part}")'
        return f'BibleRef("{ref_part}", versification={self.versification})'

    @classmethod
    def for_range(
        cls,
        book_id: str,
        chapter: int,
        start_verse: int | None = None,
        end_chapter: int | None = None,
        end_verse: int | None = None,
        start_subverse: str = "",
        end_subverse: str | None = None,
        original_text: str | None = None,
        versification: Versification | None = None,
        end_book: str | None = None,
    ) -> "BibleRef":
        """Create a BibleRef with a single VerseRange.

        Args:
            book_id: The book ID (e.g., "JHN" for John)
            chapter: The chapter number
            start_verse: The starting verse number, or None for the whole chapter
            end_chapter: The ending chapter number (defaults to the start chapter,
                or to None, the whole book, if end_book is given)
            end_verse: The ending verse number (defaults to the start verse if
                the range ends in the chapter it starts in, and otherwise to
                None, the whole of the ending chapter)
            start_subverse: The starting subverse (defaults to "")
            end_subverse: The ending subverse (defaults to the starting subverse
                for a single verse, and otherwise to "")
            original_text: The original text from which this reference was parsed (defaults to None)
            versification: The Versification to use (defaults to None)
            end_book: The book ID in which the range ends (defaults to book_id)

        Returns:
            A BibleRef instance containing a single VerseRange

        """
        start = RefPoint(book_id, chapter, start_verse, start_subverse)
        same_chapter = end_book is None and end_chapter is None
        if same_chapter and end_verse is None:
            end_verse = start_verse
            if end_subverse is None:
                end_subverse = start_subverse
        if end_book is None and end_chapter is None:
            end_chapter = chapter
        end = RefPoint(end_book or book_id, end_chapter, end_verse, end_subverse or "")
        return cls(
            ranges=(VerseRange(start, end, original_text),),
            versification=versification,
            original_text=original_text,
        )

    @classmethod
    def for_book(
        cls,
        book_id: str,
        end_book: str | None = None,
        original_text: str | None = None,
        versification: Versification | None = None,
    ) -> "BibleRef":
        """Create a BibleRef for a whole book or a range of whole books.

        Args:
            book_id: The book ID (e.g., "JHN" for John)
            end_book: The book ID of the last book of the range (defaults to
                book_id, a single book)
            original_text: The original text from which this reference was parsed (defaults to None)
            versification: The Versification to use (defaults to None)

        Returns:
            A BibleRef instance containing a single whole-book VerseRange

        """
        verse_range = VerseRange(
            RefPoint(book_id), RefPoint(end_book or book_id), original_text
        )
        return cls((verse_range,), versification, original_text)

    def books(self) -> list[str]:
        """Return the IDs of the books this reference names, in order of mention.

        Each book is listed once. The books that lie between the ends of a
        range that spans books are not listed.
        """
        ids: dict[str, None] = {}
        for verse_range in self.ranges:
            ids[verse_range.start.book] = None
            ids[verse_range.end.book] = None
        return list(ids)

    def is_single_range(self) -> bool:
        """Return True if this reference consists of exactly one verse range."""
        return len(self.ranges) == 1

    def is_whole_books(self) -> bool:
        """Return True if this reference refers to entire books only.

        Note that this regards the form of the reference rather than its
        content. So it returns True for John but False for John 1–21.
        """
        return all(verse_range.is_whole_books() for verse_range in self.ranges)

    def is_whole_chapters(self) -> bool:
        """Return True if this reference does not specify verse limits.

        Note that this regards the form of the reference rather than its
        content. So it returns True for John and John 6 but False for John
        1:1–51.
        """
        return all(verse_range.is_whole_chapters() for verse_range in self.ranges)

    def invalid_reason(
        self, style: RefStyle | None = None, *, allow_excluded: bool = True
    ) -> str | None:
        """Explain why this Bible reference is invalid, or None if it is valid.

        The reference is invalid if it has no versification, or if any of its
        verse ranges is invalid under that versification: if a book is not in
        the versification, if the range is structurally inconsistent, if it
        ends in an earlier book than it starts, or if any chapter or verse it
        names does not exist. When more than one verse range is invalid, each
        reason is reported, joined by "; ".

        A verse the versification excludes (see
        :meth:`Versification.is_excluded`), such as the NABRE's Matt 17:21, is
        valid by default: it lies within its chapter and names a place in the
        text, though the versification has nothing there.

        An empty BibleRef with a versification is vacuously valid.

        Args:
            style: Optional RefStyle whose book names are used to name books in
                the message. Without it, Paratext book IDs are used.
            allow_excluded: If False, a range that begins or ends on an
                excluded verse is invalid, though it may still span one.

        Returns:
            An explanatory string, or None if the reference is valid.

        """
        if self.versification is None:
            return "no versification is set"

        reasons: list[str] = []
        for verse_range in self.ranges:
            reason = _range_reason(
                verse_range, self.versification, style, allow_excluded
            )
            if reason is not None:
                reasons.append(reason)

        return "; ".join(reasons) if reasons else None

    def is_valid(self, *, allow_excluded: bool = True) -> bool:
        """Check if this Bible reference is valid according to its versification.

        An empty BibleRef is vacuously valid.

        Args:
            allow_excluded: If False, a range that begins or ends on a verse
                the versification excludes is invalid.

        Returns:
            bool: True if the reference is valid, False otherwise

        """
        return self.invalid_reason(allow_excluded=allow_excluded) is None

    def range_keys(self) -> Iterator[tuple[int, int]]:
        """Yield an integer key range for each verse range in the ref.

        Book numbers are derived from self.versification, so nothing is
        yielded if it is None. Nor is anything yielded for a verse range that
        names a book the versification does not include.

        A point that leaves its verse or chapter unspecified is replaced with:

        - verse 0 of the chapter, or of chapter 1, at the start of a range
        - the last verse of the chapter, or of the book, at the end of a range

        A range that spans books yields a single pair of keys, which takes in
        the books between them in the versification's order.

        Yields:
            (start_key, end_key): integer keys for the start and end of a range in the ref
                Each key has 2 book digits, 3 chapter digits, 3 verse digits, and
                2 subverse-ordinal digits (which place a verse and the verses
                inserted beside it, such as ESG 4:17k, in reading order; 0 for
                a verse that has none). A range end that spreads to
                a whole verse carries the maximal subverse ordinal so that it
                includes that verse's inserted verses.

        """
        versification = self.versification
        if versification is None:
            return
        books = list(versification.max_verses)
        for verse_range in self.ranges:
            start, end = verse_range.start, verse_range.end
            if start.book not in books or end.book not in books:
                continue

            start_chapter = 1 if start.chapter is None else start.chapter
            start_verse = 0 if start.verse is None else start.verse
            start_key = _verse_key(
                books.index(start.book) + 1,
                start_chapter,
                start_verse,
                versification.partial_ordinal(
                    start.book, start_chapter, start_verse, start.subverse
                ),
            )

            end_chapter = end.chapter
            if end_chapter is None:
                end_chapter = len(versification.max_verses[end.book])
            if end.verse is None:
                end_verse = versification.last_verse(end.book, end_chapter)
                end_ordinal = _MAX_SUBVERSE_ORDINAL
            else:
                end_verse = end.verse
                end_ordinal = versification.partial_ordinal(
                    end.book, end_chapter, end_verse, end.subverse
                )
            end_key = _verse_key(
                books.index(end.book) + 1, end_chapter, end_verse, end_ordinal
            )
            yield (start_key, end_key)

    def range_refs(self) -> Iterator["BibleRef"]:
        """Yield a new BibleRef for each verse range.

        Each yielded BibleRef contains a single verse range. The versification
        is preserved, and the original text of each comes from its verse range.

        Yields:
            BibleRef: A new reference containing a single verse range

        """
        for verse_range in self.ranges:
            yield BibleRef(
                ranges=(verse_range,),
                versification=self.versification,
                original_text=verse_range.original_text,
            )

    def resolve_following_verses(self) -> "BibleRef":
        """Return this reference with a definite end for each "ff" range.

        A range that runs from a verse to the end of its chapter (John 3:16ff)
        ends instead at the last verse of the chapter (John 3:16–36).

        Returns:
            A new BibleRef, or this one if it has no versification

        """
        versification = self.versification
        if versification is None:
            return self
        ranges: list[VerseRange] = []
        for verse_range in self.ranges:
            end = verse_range.end
            if verse_range.has_following_verses() and end.chapter is not None:
                last_verse = versification.last_verse(end.book, end.chapter)
                verse_range = VerseRange(
                    verse_range.start,
                    RefPoint(end.book, end.chapter, last_verse),
                    verse_range.original_text,
                )
            ranges.append(verse_range)
        return BibleRef(ranges, versification, self.original_text)

    def map_to(self, target: Versification) -> "BibleRef | None":
        """Map this reference into a different versification.

        Each verse location is mapped from this reference's versification to
        the target, going through the "org" (original languages) versification
        as an intermediary. A verse range is divided wherever the book it maps
        into changes: Vulgate Dan 13:60-65 is org Sus 1:60-64 and Bel 1:1, and
        Vulgate Dan 3 is org Dan 3:1-23, the Song of the Three, and Dan
        3:24-33.

        A whole-chapter range is mapped through its first and last verses, and
        remains whole chapters if the result covers whole chapters in the
        target: Vulgate Ps 50 is Ps 51 in org, and Vulgate Ps 9 is org Ps 9-10,
        but Vulgate Ps 115 is org Ps 116:10-19. A whole book is mapped as its
        chapters are, and remains a whole book if they fill one book of the
        target: Vulgate Daniel is org Daniel together with the Song of the
        Three, Susanna, and Bel.

        A range that spans books is mapped book by book, since the books
        between its ends depend on the versification's order. The pieces are
        rejoined wherever their books are consecutive in the target too: nabre
        Neh–Jdt is eng Neh and Tob–Jdt.

        Args:
            target: The target Versification to map into

        Returns:
            A new BibleRef in the target versification, or None if this
            reference has no versification set or any verse does not exist
            in the target

        """
        if self.versification is None:
            return None

        ranges: list[VerseRange] = []
        for verse_range in self.ranges:
            mapped = _map_range(verse_range, self.versification, target)
            if mapped is None:
                return None
            ranges.extend(mapped)

        return BibleRef(ranges, target)

    def format(self, style: RefStyle) -> str:
        """Format this Bible reference as a string according to the given style.

        If the reference has a versification, chapter numbers are omitted for
        one-chapter books. A book's name is stated where the book changes, and
        the Psalms are named in the plural where more than one is cited.

        Args:
            style: The RefStyle to use for formatting

        Returns:
            A formatted string representation of this Bible reference

        """
        versification = self.versification

        def single_chapter(book: str) -> bool:
            return versification is not None and versification.is_single_chapter(book)

        def chapter_verse(point: RefPoint) -> str:
            """Format a point's chapter and verse, as far as it has them."""
            assert point.chapter is not None
            text = style.format_chapter(point.chapter, point.book)
            if point.verse is not None:
                text += f"{style.chapter_verse_separator}{point.verse}{point.subverse}"
            return text

        def named(point: RefPoint, plural: bool) -> str:
            """Format a point together with the name of its book."""
            name = style.book_name(point.book, plural=plural)
            if point.chapter is None:
                return name
            if single_chapter(point.book):
                if point.verse is None:
                    return name
                return f"{name} {point.verse}{point.subverse}"
            return f"{name} {chapter_verse(point)}"

        def continues(previous: VerseRange, current: VerseRange) -> bool:
            """Tell whether a range can rely on the book the last one named."""
            if (
                current.start.book != previous.end.book
                or previous.end.chapter is None
                or current.start.chapter is None
            ):
                return False
            # A one-chapter book prints no chapter, so only a verse that
            # follows a verse can do without the name.
            return not single_chapter(current.start.book) or (
                current.start.verse is not None
                and (previous.end.verse is not None or previous.has_following_verses())
            )

        def is_plural(index: int) -> bool:
            """Tell whether the ranges sharing a book name cite several chapters."""
            chapters: set[int | None] = set()
            for position in range(index, len(self.ranges)):
                verse_range = self.ranges[position]
                if position > index and not continues(
                    self.ranges[position - 1], verse_range
                ):
                    break
                chapters.add(verse_range.start.chapter)
                if not verse_range.is_single_book():
                    break
                chapters.add(verse_range.end.chapter)
            return None in chapters or len(chapters) > 1

        result = ""
        previous: VerseRange | None = None
        for index, verse_range in enumerate(self.ranges):
            start, end = verse_range.start, verse_range.end
            if previous is not None and continues(previous, verse_range):
                assert start.chapter is not None
                if (
                    start.verse is not None
                    and start.chapter == previous.end.chapter
                    and (
                        previous.end.verse is not None
                        or previous.has_following_verses()
                    )
                ):
                    result += (
                        f"{style.verse_range_separator}{start.verse}{start.subverse}"
                    )
                else:
                    result += style.chapter_separator + chapter_verse(start)
            else:
                if previous is not None:
                    result += style.chapter_separator
                result += named(start, is_plural(index))

            if end.book != start.book:
                result += style.range_separator + named(end, end.chapter is None)
            elif end.chapter is None or start.chapter is None:
                pass
            elif verse_range.has_following_verses():
                result += style.following_verses
            elif end.chapter != start.chapter:
                result += style.range_separator + chapter_verse(end)
            elif end.verse is None:
                pass
            elif start.verse is None:
                result += style.range_separator
                if single_chapter(end.book):
                    result += f"{end.verse}{end.subverse}"
                else:
                    result += chapter_verse(end)
            elif end.verse != start.verse:
                result += f"{style.range_separator}{end.verse}{end.subverse}"
            elif end.subverse != start.subverse:
                result += style.range_separator + end.subverse
            previous = verse_range
        return result
