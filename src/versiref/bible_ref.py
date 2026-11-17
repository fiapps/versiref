"""Bible reference handling for versiref.

This module provides classes for representing and manipulating Bible references.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from functools import partial

from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification, lettered_subverse

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
_TargetLoc = tuple[str, int, int, str]


def _mapped_both_ways(
    source: Versification, target: Versification, loc: _TargetLoc, certain: bool = False
) -> tuple[_TargetLoc, _TargetLoc] | None:
    """Return the start and end of what a verse maps to, if that maps back to it.

    Where the data does not account for a verse, it maps to the verse of the
    same number, which may be the counterpart of another verse altogether.
    Such a verse says nothing about what the source range covers in the
    target. With certain, a verse that does not map back at all is not
    returned either.
    """
    book, chapter, verse, part = loc
    first = source.map_verse(book, chapter, verse, target, part)
    last = source.map_verse(book, chapter, verse, target, part, end=True)
    if first is None or last is None:
        return None
    back = target.map_verse(*first[:3], source, first[3])
    back_end = target.map_verse(*last[:3], source, last[3], end=True)
    if back is None or back_end is None or (back[0], back_end[0]) != (book, book):
        return None if certain else (first, last)
    if certain:
        returns = _key(source, back) <= _key(source, loc) <= _key(source, back_end)
    else:
        # A verse inserted beside a verse may come back as the verse itself.
        returns = back[1:3] <= (chapter, verse) <= back_end[1:3]
    return (first, last) if returns else None


def _key(versification: Versification, loc: _TargetLoc) -> tuple[int, int, int]:
    """Return what orders a location among the others of its book."""
    return (loc[1], loc[2], versification.partial_ordinal(*loc))


def _nothing_between(
    source: Versification,
    target: Versification,
    book: str,
    previous: _TargetLoc,
    current: _TargetLoc,
) -> bool:
    """Tell whether the source's book has nothing between two target locations.

    Args:
        source: The Versification being mapped from
        target: The Versification the locations are in
        book: The book ID of the range in the source
        previous: A location in the target
        current: A later location in the same book of the target

    Returns:
        True if no verse between the two is one the source has in the book.
        What it has in another book, or not at all, is passed over. A subverse
        the target does not list is a portion of its verse, and stands
        wherever in the verse it needs to.

    """
    target_book, chapter, verse, part = previous
    parts = target.verse_parts(target_book, chapter, verse)
    if current[1:3] == (chapter, verse) and (
        part not in parts or current[3] not in parts
    ):
        return True
    index = parts.index(part) if part in parts else len(parts) - 1
    while True:
        index += 1
        if index == len(parts):
            verse += 1
            if verse > target.last_verse(target_book, chapter):
                chapter += 1
                # A psalm's title may be cited as a verse 0 it does not own.
                verse = 0 if current[1:3] == (chapter, 0) else 1
                verse = min(verse, target.first_verse(target_book, chapter))
            parts = target.verse_parts(target_book, chapter, verse)
            index = 0
        if (chapter, verse) > current[1:3]:
            return True
        if (chapter, verse) == current[1:3] and (
            current[3] not in parts or current[3] == parts[index]
        ):
            return True
        if target.is_excluded(target_book, chapter, verse):
            continue
        between = _mapped_both_ways(
            target, source, (target_book, chapter, verse, parts[index]), certain=True
        )
        if between is None or between[0][0] != book:
            continue
        _, source_chapter, source_verse, source_part = between[0]
        if (
            source.first_verse(book, source_chapter)
            <= source_verse
            <= source.last_verse(book, source_chapter)
            and not source.is_excluded(book, source_chapter, source_verse)
            and source_part in source.verse_parts(book, source_chapter, source_verse)
        ):
            return False


@dataclass
class _Block:
    """Consecutive verses of the target that verses of a source range map to."""

    order: int
    first_key: tuple[int, int, int]
    first: _TargetLoc
    first_from: _SourceLoc
    last_key: tuple[int, int, int]
    last: _TargetLoc
    last_from: _SourceLoc


def _book_segments(
    source: Versification,
    target: Versification,
    book: str,
    start: _SourceLoc,
    end: _SourceLoc,
) -> list[tuple[_SourceLoc, _SourceLoc]]:
    """Divide a source range into what maps to consecutive verses of the target.

    The range is divided wherever the book it maps into changes. What maps
    into one book is divided again wherever the target has, between two parts
    of it, verses the source has elsewhere in its book: the Vulgate's Esther
    11 is the end of the Greek book followed by its beginning. Verses that
    only stand in a different order, as the commandments do in the Greek
    Exodus 20, do not divide it.

    Args:
        source: The Versification the range is in
        target: The Versification it is being mapped into
        book: The book ID of the range in the source
        start: The (chapter, verse, subverse) at which the range begins
        end: The (chapter, verse, subverse) at which it ends

    Returns:
        (first, last) pairs of source locations, each mapping to the first and
        last of a run of consecutive verses in a single book of the target, in
        the order the source reaches them. Together the runs are what the
        range covers, apart from any verses that have no place in the target.
        The range's own subverses stay on its start and end.

    """
    if (
        source.map_verse(book, start[0], start[1], target, start[2]) is None
        or source.map_verse(book, end[0], end[1], target, end[2]) is None
    ):
        return [(start, end)]

    # Runs of verses in the order of the source that map into the same book.
    runs: list[list[_Block]] = []
    run_book: str | None = None
    order = 0
    start_ordinal = source.partial_ordinal(book, *start)
    end_ordinal = source.partial_ordinal(book, *end)
    for chapter in range(start[0], end[0] + 1):
        first = start[1] if chapter == start[0] else source.first_verse(book, chapter)
        last = end[1] if chapter == end[0] else source.last_verse(book, chapter)
        for verse in range(first, last + 1):
            # The verses inserted beside a verse may map into another book, as
            # the NABRE's lettered chapters of Esther do.
            for part in source.verse_parts(book, chapter, verse):
                ordinal = source.partial_ordinal(book, chapter, verse, part)
                at_start = (chapter, verse) == start[:2]
                at_end = (chapter, verse) == end[:2]
                if (at_start and ordinal < start_ordinal) or (
                    at_end and ordinal > end_ordinal
                ):
                    continue
                # A verse the versification does not have is no part of what
                # the range covers, even at its ends.
                if source.is_excluded(book, chapter, verse):
                    continue
                at_start = at_start and ordinal == start_ordinal
                at_end = at_end and ordinal == end_ordinal
                loc = (chapter, verse, part)
                mapped = _mapped_both_ways(source, target, (book, *loc))
                if at_start or at_end:
                    # The range's own ends are mapped whatever the data says.
                    own = start if at_start else end
                    mapped_first = source.map_verse(book, *own[:2], target, own[2])
                    mapped_last = source.map_verse(
                        book, *own[:2], target, own[2], end=True
                    )
                    if mapped_first is not None and mapped_last is not None:
                        mapped = (mapped_first, mapped_last)
                if mapped is None:
                    continue
                if mapped[0][0] != run_book:
                    run_book = mapped[0][0]
                    runs.append([])
                runs[-1].append(
                    _Block(
                        order,
                        _key(target, mapped[0]),
                        mapped[0],
                        start if at_start else loc,
                        _key(target, mapped[1]),
                        mapped[1],
                        end if at_end else loc,
                    )
                )
                order += 1
    if not runs:
        return [(start, end)]

    segments: list[tuple[_SourceLoc, _SourceLoc]] = []
    for run in runs:
        blocks: list[_Block] = []
        for verse_block in sorted(run, key=lambda block: block.first_key):
            block = blocks[-1] if blocks else None
            if block is None or not (
                verse_block.first_key <= block.last_key
                or _nothing_between(source, target, book, block.last, verse_block.first)
            ):
                blocks.append(verse_block)
                continue
            block.order = min(block.order, verse_block.order)
            if verse_block.last_key > block.last_key:
                block.last_key = verse_block.last_key
                block.last = verse_block.last
                block.last_from = verse_block.last_from
        segments.extend(
            (block.first_from, block.last_from)
            for block in sorted(blocks, key=lambda block: block.order)
        )
    return segments


def _last_present_verse(versification: Versification, book: str, chapter: int) -> int:
    """Return the last verse of a chapter that the versification does not exclude."""
    last = versification.last_verse(book, chapter)
    while last > 1 and versification.is_excluded(book, chapter, last):
        last -= 1
    return last


def _own_parts(
    versification: Versification, book: str, chapter: int, verse: int
) -> list[str]:
    """Return the parts of a verse that belong to its numbered chapter.

    These are the verse and the verses inserted beside it, in reading order,
    apart from the verses of a lettered chapter, which is a chapter of its
    own: the NABRE's Esther 4 ends at 4:17, though Esther C follows that verse
    and is held as verses inserted after it.
    """
    parts = versification.verse_parts(book, chapter, verse)
    return [part for part in parts if lettered_subverse(part) is None] or [""]


def _starts_chapter(
    versification: Versification, loc: tuple[str, int, int, str]
) -> bool:
    """Tell whether nothing of its numbered chapter comes before a location."""
    book, chapter, verse, subverse = loc
    first = versification.first_verse(book, chapter)
    if verse != first:
        return verse < first
    first_part = _own_parts(versification, book, chapter, verse)[0]
    return versification.partial_ordinal(
        book, chapter, verse, subverse
    ) <= versification.partial_ordinal(book, chapter, verse, first_part)


def _ends_chapter(versification: Versification, loc: tuple[str, int, int, str]) -> bool:
    """Tell whether nothing of its numbered chapter comes after a location."""
    book, chapter, verse, subverse = loc
    last = _last_present_verse(versification, book, chapter)
    if verse != last:
        return verse > last
    last_part = _own_parts(versification, book, chapter, verse)[-1]
    return versification.partial_ordinal(
        book, chapter, verse, subverse
    ) >= versification.partial_ordinal(book, chapter, verse, last_part)


def _definite(
    versification: Versification, book: str, subverse: str, last: bool = False
) -> str:
    """Give a whole lettered chapter (the subverse "C") its first or last verse."""
    lettered = lettered_subverse(subverse)
    if lettered is None or lettered[1] is not None:
        return subverse
    located = versification.lettered_chapter(book, lettered[0])
    if located is None:
        return subverse
    return f"{lettered[0]}{located[2] if last else 1}"


@dataclass(frozen=True)
class _Shown:
    """One end of a verse range as it is written: a lettered chapter has its letter."""

    book: str
    chapter: int | str | None = None
    verse: int | None = None
    subverse: str = ""


def _shown(verse_range: "VerseRange") -> tuple[_Shown, _Shown]:
    """Return the ends of a verse range as they are written.

    A verse of a lettered chapter is held as a verse inserted beside a verse
    of the numbered text (the NABRE's Esther C:12 as subverse "C12" of Esther
    4:17, and the whole of Esther C as its subverse "C") but written with the
    letter as its chapter.
    """

    def show(point: RefPoint) -> _Shown:
        parts = None if point.verse is None else lettered_subverse(point.subverse)
        if parts is None:
            return _Shown(point.book, point.chapter, point.verse, point.subverse)
        return _Shown(point.book, *parts)

    return show(verse_range.start), show(verse_range.end)


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
        subverse: Letters naming a part of the verse, or "" for the whole verse.
            A verse of a lettered chapter is held as a verse inserted beside
            a verse of the numbered text, with a subverse made of the letter
            and its verse number: the NABRE's Esther C:12 is the subverse
            "C12" of Esther 4:17, and its first half is "C12a". The letter
            alone, "C", is the lettered chapter as a whole.

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

        This is also true of a range of whole books. A lettered chapter, such
        as the NABRE's Esther C, counts as a chapter.
        """
        start, end = _shown(self)
        return start.verse is None and end.verse is None

    def has_following_verses(self) -> bool:
        """Return True if this range runs from a verse to the end of its chapter.

        This is the form written with "ff", as in John 3:16ff.
        """
        start, end = _shown(self)
        return (
            start.book == end.book
            and start.verse is not None
            and end.verse is None
            and end.chapter == start.chapter
        )

    def _numbered(self) -> tuple[bool, bool]:
        """Tell whether the range is whole numbered chapters, or "ff" in one.

        Unlike :meth:`is_whole_chapters` and :meth:`has_following_verses`,
        this takes a lettered chapter for what it is held as: verses inserted
        beside a verse of a numbered chapter.
        """
        start, end = self.start, self.end
        return (
            start.verse is None and end.verse is None,
            self.is_single_book()
            and start.verse is not None
            and end.verse is None
            and end.chapter == start.chapter
            # A whole lettered chapter is no verse to follow on from.
            and _shown(self)[0].verse is not None,
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

        shown_start, shown_end = _shown(self)
        if (
            shown_start.verse is not None
            and shown_end.verse is None
            and shown_start.chapter != shown_end.chapter
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
        lettered = None if point.verse is None else lettered_subverse(point.subverse)
        if lettered is not None:
            letter, verse, _ = lettered
            located = versification.lettered_chapter(point.book, letter)
            if located is None or located[:2] != (point.chapter, point.verse):
                return f"{label(point.book)} has no chapter {letter}"
            if verse is not None and (verse < 1 or verse > located[2]):
                return (
                    f"{label(point.book)} {letter} has no verse {verse} "
                    f"(only {_count(located[2], 'verse')})"
                )
    if (
        start.book == end.book
        and start.chapter is not None
        and start.verse is not None
        and (start.chapter, start.verse) == (end.chapter, end.verse)
        and versification.partial_ordinal(
            start.book,
            start.chapter,
            start.verse,
            _definite(versification, start.book, start.subverse),
        )
        > versification.partial_ordinal(
            end.book,
            start.chapter,
            start.verse,
            _definite(versification, end.book, end.subverse, last=True),
        )
    ):
        return f"{label(start.book)}: range ends at an earlier verse than it starts"
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


def _whole_lettered(
    piece: VerseRange, target: Versification, starts_chapter: bool, ends_chapter: bool
) -> VerseRange:
    """State a piece mapped from whole chapters as whole lettered chapters if it is.

    The piece must run from the first verse of a lettered chapter, or of a
    numbered one, to the last verse of one.
    """
    start, end = piece.start, piece.end
    if start.verse is None or end.verse is None:
        return piece
    first = lettered_subverse(start.subverse)
    last = lettered_subverse(end.subverse)
    if first is None and last is None:
        return piece
    if first is None:
        if not starts_chapter:
            return piece
        start = RefPoint(start.book, start.chapter)
    elif first[1:] == (1, ""):
        start = RefPoint(start.book, start.chapter, start.verse, first[0])
    else:
        return piece
    if last is None:
        if not ends_chapter:
            return piece
        end = RefPoint(end.book, end.chapter)
    else:
        located = target.lettered_chapter(end.book, last[0])
        if located is None or last[1:] != (located[2], ""):
            return piece
        end = RefPoint(end.book, end.chapter, end.verse, last[0])
    return VerseRange(start, end)


def _map_chapters(
    verse_range: VerseRange,
    source: Versification,
    target: Versification,
    whole_book: bool = False,
) -> list[VerseRange] | None:
    """Map a range that names chapters of a single book, as pieces in the target.

    Returns None if the start or end of a piece does not exist in the target.
    A whole-chapter range naming a chapter the source does not have passes
    through unchanged. With whole_book, the range takes in any lettered
    chapter that stands before its first chapter or after its last.
    """
    book = verse_range.start.book
    start_point, end_point = verse_range.start, verse_range.end
    assert start_point.chapter is not None
    assert end_point.chapter is not None
    whole, follows = verse_range._numbered()
    if whole and (
        source.last_verse(book, start_point.chapter) < 1
        or source.last_verse(book, end_point.chapter) < 1
    ):
        return [
            VerseRange(
                RefPoint(book, start_point.chapter), RefPoint(book, end_point.chapter)
            )
        ]

    # A chapter begins and ends with any verses inserted beside its first
    # and last, unless they are a lettered chapter.
    parts = source.verse_parts if whole_book else partial(_own_parts, source)
    start: _SourceLoc
    if start_point.verse is None:
        first_verse = source.first_verse(book, start_point.chapter)
        start = (
            start_point.chapter,
            first_verse,
            parts(book, start_point.chapter, first_verse)[0],
        )
    else:
        start = (
            start_point.chapter,
            start_point.verse,
            _definite(source, book, start_point.subverse),
        )
    end: _SourceLoc
    if end_point.verse is not None:
        end = (
            end_point.chapter,
            end_point.verse,
            _definite(source, book, end_point.subverse, last=True),
        )
    else:
        if follows:
            last_verse = source.last_verse(book, end_point.chapter)
        else:
            last_verse = _last_present_verse(source, book, end_point.chapter)
        end = (
            end_point.chapter,
            last_verse,
            parts(book, end_point.chapter, last_verse)[-1],
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
        # A lettered chapter is no part of the numbered chapter it adjoins.
        starts_chapter = (
            _starts_chapter(target, first) and lettered_subverse(first[3]) is None
        )
        ends_chapter = (
            _ends_chapter(target, last) and lettered_subverse(last[3]) is None
        )
        # A verse 0 (a psalm title) cannot be cited, so a range that would
        # begin there begins at verse 1.
        piece_verse = max(first[2], 1) if start_point.verse is None else first[2]
        # A piece is whole chapters if the range is. So is the first piece
        # of a divided range that starts with a whole chapter, and the last
        # of one that ends with one, as far as the division allows.
        divided = len(segments) > 1
        whole_piece = (
            whole
            or (divided and index == 0 and start_point.verse is None)
            or (
                divided
                and index == len(segments) - 1
                and end_point.verse is None
                and not follows
            )
        )
        if whole_piece and starts_chapter and ends_chapter:
            piece = VerseRange(
                RefPoint(mapped_book, first[1]), RefPoint(mapped_book, last[1])
            )
        elif follows and len(segments) == 1 and lettered_subverse(first[3]) is None:
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
                RefPoint(mapped_book, first[1], piece_verse, first[3]),
                RefPoint(mapped_book, last[1], last[2], last[3]),
            )
        if whole_piece:
            piece = _whole_lettered(piece, target, starts_chapter, ends_chapter)
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
    pieces = _map_chapters(chapters, source, target, whole_book=True)
    if pieces is None:
        return None
    if len(pieces) == 1 and _fills_book(pieces[0], target):
        mapped_book = pieces[0].start.book
        return [VerseRange(RefPoint(mapped_book), RefPoint(mapped_book))]
    return pieces


def _fills_book(piece: VerseRange, target: Versification) -> bool:
    """Tell whether a piece mapped from whole chapters is a whole book.

    It is if it runs from the book's first chapter to its last, whether or
    not it takes in a lettered chapter that begins or ends the book.
    """
    start, end = piece.start, piece.end
    book = start.book
    if not target.includes(book) or end.book != book:
        return False
    last_chapter = len(target.max_verses[book])
    first_part = target.verse_parts(book, 1, target.first_verse(book, 1))[0]
    last_part = target.verse_parts(
        book, last_chapter, target.last_verse(book, last_chapter)
    )[-1]
    first_letter = lettered_subverse(first_part)
    last_letter = lettered_subverse(last_part)
    begins = (start.chapter, start.verse) == (1, None) or (
        first_letter is not None and start.subverse == first_letter[0]
    )
    ends = (end.chapter, end.verse) == (last_chapter, None) or (
        last_letter is not None and end.subverse == last_letter[0]
    )
    return begins and ends


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
        # The rest of the book takes in a lettered chapter that ends it.
        last_chapter = len(versification.max_verses[start.book])
        last_verse = versification.last_verse(start.book, last_chapter)
        last_part = versification.verse_parts(start.book, last_chapter, last_verse)[-1]
        if start.verse is None and not last_part:
            book_end = RefPoint(start.book, last_chapter)
        else:
            book_end = RefPoint(start.book, last_chapter, last_verse, last_part)
        pieces.append(VerseRange(start, book_end))
    pieces.extend(
        VerseRange(RefPoint(book), RefPoint(book)) for book in books[first + 1 : last]
    )
    if end.chapter is None:
        pieces.append(VerseRange(end, end))
    else:
        # Likewise a lettered chapter that begins the book.
        first_part = versification.verse_parts(end.book, 1, 1)[0]
        if lettered_subverse(first_part) is None:
            book_start = RefPoint(end.book, 1)
        else:
            book_start = RefPoint(end.book, 1, 1, first_part)
        pieces.append(VerseRange(book_start, end))
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
            or _ends_chapter(
                target,
                (
                    point.book,
                    last_chapter,
                    point.verse,
                    _definite(target, point.book, point.subverse, last=True),
                ),
            )
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
        1:1–51. A lettered chapter counts as a chapter: with the NABRE's
        versification, it returns True for Esther C.
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

        A lettered chapter (the NABRE's Esther C) keys among the verses of the
        numbered chapters, where it is read. A numbered chapter leaves out a
        lettered chapter that stands before its first verse or after its last,
        so the NABRE's Esther 4 ends at 4:17, but a whole book takes them in.

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

            # A numbered chapter leaves out a lettered chapter that stands
            # before its first verse or after its last, though a whole book
            # takes them in.
            start_chapter = 1 if start.chapter is None else start.chapter
            start_verse = 0 if start.verse is None else start.verse
            start_subverse = start.subverse
            if start.chapter is not None and start.verse is None:
                own = _own_parts(versification, start.book, start_chapter, 1)[0]
                if own != versification.verse_parts(start.book, start_chapter, 1)[0]:
                    start_verse, start_subverse = 1, own
            start_key = _verse_key(
                books.index(start.book) + 1,
                start_chapter,
                start_verse,
                versification.partial_ordinal(
                    start.book,
                    start_chapter,
                    start_verse,
                    _definite(versification, start.book, start_subverse),
                ),
            )

            end_chapter = end.chapter
            if end_chapter is None:
                end_chapter = len(versification.max_verses[end.book])
            if end.verse is None:
                end_verse = versification.last_verse(end.book, end_chapter)
                end_ordinal = _MAX_SUBVERSE_ORDINAL
                own = _own_parts(versification, end.book, end_chapter, end_verse)[-1]
                if (
                    end.chapter is not None
                    and own
                    != (versification.verse_parts(end.book, end_chapter, end_verse)[-1])
                ):
                    end_ordinal = versification.partial_ordinal(
                        end.book, end_chapter, end_verse, own
                    )
            else:
                end_verse = end.verse
                end_ordinal = versification.partial_ordinal(
                    end.book,
                    end_chapter,
                    end_verse,
                    _definite(versification, end.book, end.subverse, last=True),
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
                if end.verse is None:
                    last_verse = versification.last_verse(end.book, end.chapter)
                    end = RefPoint(end.book, end.chapter, last_verse)
                else:
                    # The end of a lettered chapter.
                    end = RefPoint(
                        end.book,
                        end.chapter,
                        end.verse,
                        _definite(versification, end.book, end.subverse, last=True),
                    )
                verse_range = VerseRange(
                    verse_range.start, end, verse_range.original_text
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
        shown = [_shown(verse_range) for verse_range in self.ranges]

        def single_chapter(book: str) -> bool:
            return versification is not None and versification.is_single_chapter(book)

        def follows(start: _Shown, end: _Shown) -> bool:
            """Tell whether a range is written with "ff"."""
            return (
                start.book == end.book
                and start.verse is not None
                and end.verse is None
                and end.chapter == start.chapter
            )

        def chapter_verse(point: _Shown) -> str:
            """Format a point's chapter and verse, as far as it has them."""
            assert point.chapter is not None
            if isinstance(point.chapter, str):
                text = point.chapter
            else:
                text = style.format_chapter(point.chapter)
            if point.verse is not None:
                text += f"{style.chapter_verse_separator}{point.verse}{point.subverse}"
            return text

        def named(point: _Shown, plural: bool) -> str:
            """Format a point together with the name of its book."""
            name = style.book_name(point.book, plural=plural)
            if point.chapter is None:
                return name
            if single_chapter(point.book):
                if point.verse is None:
                    return name
                return f"{name} {point.verse}{point.subverse}"
            return f"{name} {chapter_verse(point)}"

        def continues(
            previous: tuple[_Shown, _Shown], current: tuple[_Shown, _Shown]
        ) -> bool:
            """Tell whether a range can rely on the book the last one named."""
            previous_end, start = previous[1], current[0]
            if (
                start.book != previous_end.book
                or previous_end.chapter is None
                or start.chapter is None
            ):
                return False
            # A one-chapter book prints no chapter, so only a verse that
            # follows a verse can do without the name.
            return not single_chapter(start.book) or (
                start.verse is not None
                and (previous_end.verse is not None or follows(*previous))
            )

        def is_plural(index: int) -> bool:
            """Tell whether the ranges sharing a book name cite several chapters."""
            chapters: set[int | str | None] = set()
            for position in range(index, len(shown)):
                start, end = shown[position]
                if position > index and not continues(
                    shown[position - 1], shown[position]
                ):
                    break
                chapters.add(start.chapter)
                if start.book != end.book:
                    break
                chapters.add(end.chapter)
            return None in chapters or len(chapters) > 1

        result = ""
        previous: tuple[_Shown, _Shown] | None = None
        for index, (start, end) in enumerate(shown):
            if previous is not None and continues(previous, (start, end)):
                assert start.chapter is not None
                if (
                    start.verse is not None
                    and start.chapter == previous[1].chapter
                    and (previous[1].verse is not None or follows(*previous))
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
            elif follows(start, end):
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
            previous = (start, end)
        return result
