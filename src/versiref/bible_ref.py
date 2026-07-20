"""Bible reference handling for versiref.

This module provides classes for representing and manipulating Bible references.
"""

from dataclasses import dataclass, field
from typing import Generator

from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification


def _count(n: int, noun: str) -> str:
    """Return ``n`` followed by ``noun``, pluralized with a trailing 's'."""
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _chapter_verse_reason(
    label: str, chapters: list[int], chapter: int, verse: int
) -> str | None:
    """Explain why a (chapter, verse) is out of range, or None if it is in range.

    Args:
        label: Reader-facing book name to name in the message.
        chapters: The book's last-verse-per-chapter list (from the versification).
        chapter: The chapter number to check.
        verse: The verse number to check, or a value < 0 for an unspecified verse.

    Returns:
        An explanatory string, or None if the chapter (and verse, if specified)
        exist in the book.

    """
    if chapter < 1 or chapter > len(chapters):
        return f"{label} has no chapter {chapter} (only {_count(len(chapters), 'chapter')})"
    if verse >= 0:
        max_verse = chapters[chapter - 1]
        if verse < 1 or verse > max_verse:
            return (
                f"{label} {chapter} has no verse {verse} "
                f"(only {_count(max_verse, 'verse')})"
            )
    return None


@dataclass
class VerseRange:
    """Represents a range of verses within a single book of the Bible.

    A verse range has a start and end point, each defined by chapter, verse, and
    subverse. The original text from which this range was parsed can be stored.

    A verse number less than 0 means "unspecified". When a verse number is less
    than 0, the corresponding subverse should be "", but it is ignored
    regardless of its value. If start_verse and end_verse are both less than 0,
    the range is a whole chapter or chapters. If start_verse >= 0 and end_verse
    < 0, the verses are f"{start_verse}ff". This is only allowed if
    start_chapter == end_chapter. Nor is it allowed to have start_verse < 0 and
    end_verse >= 0, start_chapter == end_chapter && start_verse > end_verse, or
    start_chapter < end_chapter. The result of SimpleBibleRef.format() is
    undefined if the class contains a VerseRange with disallowed values. Where a
    definite end is needed, applications can interpret "ff"
    (style.following_verses) as "until the end of the chapter."
    """

    start_chapter: int
    start_verse: int
    start_subverse: str
    end_chapter: int
    end_verse: int
    end_subverse: str
    original_text: str | None = None

    def is_whole_chapters(self) -> bool:
        """Return True if this range does not specify verse limits."""
        return self.start_verse < 0 and self.end_verse < 0

    def invalid_reason(self) -> str | None:
        """Explain why this verse range is structurally invalid.

        This checks the internal consistency of the range only; it says nothing
        about whether the chapters and verses exist in any versification.

        Returns:
            An explanatory string if any of these conditions are met, or None
            if the range is structurally valid:

            - start_chapter > end_chapter
            - start_verse >= 0 and end_verse < 0 ("ff") but start_chapter != end_chapter
            - start_verse < 0 and end_verse >= 0
            - start_chapter == end_chapter and start_verse > end_verse

        """
        # Cannot have start chapter greater than end chapter
        if self.start_chapter > self.end_chapter:
            return "range ends in an earlier chapter than it starts"

        # "ff" notation must stay within a single chapter
        if (
            self.start_verse >= 0
            and self.end_verse < 0
            and self.start_chapter != self.end_chapter
        ):
            return "'ff' range spans more than one chapter"

        # Cannot have unspecified start verse but specified end verse
        if self.start_verse < 0 and self.end_verse >= 0:
            return "unspecified start verse with a specified end verse"

        # Cannot have start verse greater than end verse in same chapter
        if (
            self.start_chapter == self.end_chapter
            and self.end_verse >= 0
            and self.start_verse > self.end_verse
        ):
            return "range ends at an earlier verse than it starts"

        return None

    def is_valid(self) -> bool:
        """Check if this verse range has structurally valid values.

        Returns:
            bool: True if the verse range has valid values, False otherwise

        """
        return self.invalid_reason() is None


@dataclass
class SimpleBibleRef:
    """Represents a sequence of verse ranges within a single book of the Bible.

    A SimpleBibleRef consists of a book ID (using Paratext three-letter codes)
    and a list of verse ranges. The ranges are not necessarily in numeric order.
    A SimpleBibleRef with an empty list of ranges refers to the entire book.
    It optionally stores the original text from which the book ID was parsed.

    This class is "naive" in that it doesn't specify its versification system.
    """

    book_id: str
    ranges: list[VerseRange] = field(default_factory=list)
    original_text: str | None = None

    def __str__(self) -> str:
        """Return a string representation of this simple Bible reference.

        Shows a concise representation using the reference's original text
        or formatted representation.

        Returns:
            A string representation of this simple Bible reference

        """
        ref_part = self.original_text or self.format(
            RefStyle(names=standard_names("en-sbl_abbreviations"))
        )
        return f'SimpleBibleRef("{ref_part}")'

    @classmethod
    def for_range(
        cls,
        book_id: str,
        chapter: int,
        start_verse: int,
        end_chapter: int | None = None,
        end_verse: int | None = None,
        start_subverse: str = "",
        end_subverse: str = "",
        original_text: str | None = None,
    ) -> "SimpleBibleRef":
        """Create a SimpleBibleRef with a single VerseRange.

        Args:
            book_id: The book ID (e.g., "JHN" for John)
            chapter: The chapter number
            start_verse: The starting verse number
            end_chapter: The ending chapter number (defaults to start chapter if None)
            end_verse: The ending verse number (defaults to start verse if None)
            start_subverse: The starting subverse (defaults to "")
            end_subverse: The ending subverse (defaults to "")
            original_text: The original text from which this reference was parsed (defaults to None)

        Returns:
            A SimpleBibleRef instance with a single VerseRange

        """
        # If end_chapter is not specified, use the start chapter
        if end_chapter is None:
            end_chapter = chapter

        # If end_verse is not specified, use the start verse
        if end_verse is None:
            end_verse = start_verse

        verse_range = VerseRange(
            start_chapter=chapter,
            start_verse=start_verse,
            start_subverse=start_subverse,
            end_chapter=end_chapter,
            end_verse=end_verse,
            end_subverse=end_subverse,
            original_text=original_text,
        )

        return cls(book_id=book_id, ranges=[verse_range], original_text=original_text)

    def is_whole_book(self) -> bool:
        """Return True if this reference refers to the entire book.

        Note that this regards the form of the reference rather than its
        content. So it returns True for John but False for John 1–21.
        """
        return len(self.ranges) == 0

    def is_whole_chapters(self) -> bool:
        """Return True if this reference does not specify verse limits.

        Note that this regards the form of the reference rather than its
        content. So it returns true for John and John 6 but False for John
        1:1–51.
        """
        for range in self.ranges:
            if not range.is_whole_chapters():
                return False
        return True

    def invalid_reason(
        self, versification: Versification, style: RefStyle | None = None
    ) -> str | None:
        """Explain why this reference is invalid under the given versification.

        A reference is invalid if its book is not in the versification, if any
        verse range is structurally inconsistent, or if any chapter or verse it
        names does not exist in the book. When more than one verse range is
        invalid, each reason is reported, joined by "; ".

        Args:
            versification: The Versification to check against.
            style: Optional RefStyle whose book names are used to name the book
                in the message. Without it, the Paratext book ID is used.

        Returns:
            An explanatory string, or None if the reference is valid.

        """
        label = (
            self.book_id
            if style is None
            else style.names.get(self.book_id, self.book_id)
        )

        if not versification.includes(self.book_id):
            named = f" {versification.identifier!r}" if versification.identifier else ""
            return f"{label} is not in versification{named}"

        book_id = "PSA" if self.book_id == "PSAS" else self.book_id
        chapters = versification.max_verses.get(book_id, [])

        reasons: list[str] = []
        for verse_range in self.ranges:
            # A structurally inconsistent range (one that ends before it starts,
            # etc.) is reported on its own terms.
            structural = verse_range.invalid_reason()
            if structural is not None:
                reasons.append(f"{label}: {structural}")
                continue

            # Otherwise check that its chapters and verses exist in the book.
            reason = _chapter_verse_reason(
                label, chapters, verse_range.start_chapter, verse_range.start_verse
            ) or _chapter_verse_reason(
                label, chapters, verse_range.end_chapter, verse_range.end_verse
            )
            if reason is not None:
                reasons.append(reason)

        return "; ".join(reasons) if reasons else None

    def is_valid(self, versification: Versification) -> bool:
        """Check if this Bible reference is valid according to the given versification.

        Args:
            versification: The Versification to check against

        Returns:
            bool: True if the reference is valid, False otherwise

        """
        return self.invalid_reason(versification) is None

    def range_refs(self) -> Generator["SimpleBibleRef", None, None]:
        """Yield a new SimpleBibleRef for each verse range.

        Each yielded SimpleBibleRef contains only one verse range from this reference.
        The book ID is preserved, and the original text for each new instance comes
        from the verse range.

        Yields:
            SimpleBibleRef: A new reference containing a single verse range

        """
        for verse_range in self.ranges:
            yield SimpleBibleRef(
                book_id=self.book_id if self.book_id != "PSAS" else "PSA",
                ranges=[verse_range],
                original_text=verse_range.original_text,
            )

    def range_keys(
        self, versification: Versification
    ) -> Generator[tuple[int, int], None, None]:
        """Yield an integer key range for each verse range in this ref.

        Book numbers are derived from versification. If this book ID is not
        included in the versification, no ranges are yielded.

        Whole-book references (with no ranges) yield a single range spanning
        chapter 1, verse 1 through the last verse of the book.

        Verse numbers less than 0 (undefined) are replaced with:
        - 0 for start verses
        - the last verse number for the chapter for end verses

        Args:
            versification: The Versification to use for computing keys.

        Yields:
            (start_key, end_key): integer keys for the start and end of a range.
                Each key has 2 book digits, 3 chapter digits, and 3 verse digits.

        """
        if self.book_id not in versification.max_verses:
            return

        book_num = list(versification.max_verses.keys()).index(self.book_id) + 1

        if not self.ranges:
            last_chapter = len(versification.max_verses[self.book_id])
            last_verse = versification.last_verse(self.book_id, last_chapter)
            yield (
                book_num * 1000000 + 1 * 1000 + 1,
                book_num * 1000000 + last_chapter * 1000 + last_verse,
            )
            return

        for range_ref in self.range_refs():
            range = range_ref.ranges[0]
            start_verse = 0 if range.start_verse < 0 else range.start_verse
            end_verse = range.end_verse
            if end_verse < 0:
                end_verse = versification.last_verse(self.book_id, range.end_chapter)
            start_key = book_num * 1000000 + range.start_chapter * 1000 + start_verse
            end_key = book_num * 1000000 + range.end_chapter * 1000 + end_verse
            yield (start_key, end_key)

    def format(
        self, style: RefStyle, versification: Versification | None = None
    ) -> str:
        """Format this Bible reference as a string according to the given style.

        Args:
            style: The RefStyle to use for formatting
            versification: Optional Versification to use for determining book structure.
                           If provided, chapter numbers will be omitted for
                           one-chapter books.

        Returns:
            A formatted string representation of this Bible reference

        """
        # We start with the book name and then add ranges incrementally.
        result = style.book_name(self.book_id)
        last_range = None
        for range in self.ranges:
            if last_range is None:
                result += " "
                if versification is not None and versification.is_single_chapter(
                    self.book_id
                ):
                    states_chapter = False
                else:
                    result += style.format_chapter(range.start_chapter, self.book_id)
                    states_chapter = True
            elif last_range.end_chapter != range.start_chapter:
                result += style.chapter_separator + style.format_chapter(
                    range.start_chapter, self.book_id
                )
                states_chapter = True
            else:
                result += style.verse_range_separator
                states_chapter = False
            # Add start verse if specified
            if range.start_verse >= 0:
                if states_chapter:
                    result += style.chapter_verse_separator
                result += f"{range.start_verse}{range.start_subverse}"
            # Add range end if different
            if range.end_verse < 0 and range.start_verse >= 0:
                result += style.following_verses
            elif (
                range.end_chapter != range.start_chapter
                or range.end_verse != range.start_verse
                or range.end_subverse != range.start_subverse
            ):
                result += style.range_separator
                if range.end_chapter != range.start_chapter:
                    result += style.format_chapter(range.end_chapter, self.book_id)
                    if range.end_verse >= 0:
                        result += f"{style.chapter_verse_separator}{range.end_verse}"
                elif range.end_verse != range.start_verse:
                    result += f"{range.end_verse}"
                if range.end_verse >= 0:
                    result += range.end_subverse
            last_range = range
        return result

    def map(
        self, source: Versification, target: Versification
    ) -> "SimpleBibleRef | None":
        """Map this reference from one versification to another.

        Each verse location is mapped from the source versification to the
        target, going through the "org" (original languages) versification as
        an intermediary. Whole-chapter references pass through unchanged.

        Args:
            source: The Versification this reference is currently in
            target: The Versification to map into

        Returns:
            A new SimpleBibleRef in the target versification, or None if any
            verse does not exist in the target

        """
        new_ranges: list[VerseRange] = []
        for vr in self.ranges:
            if vr.is_whole_chapters():
                new_ranges.append(
                    VerseRange(
                        vr.start_chapter,
                        vr.start_verse,
                        vr.start_subverse,
                        vr.end_chapter,
                        vr.end_verse,
                        vr.end_subverse,
                    )
                )
                continue

            start = source.map_verse(
                self.book_id,
                vr.start_chapter,
                vr.start_verse,
                target,
                subverse=vr.start_subverse,
            )
            if start is None:
                return None

            if vr.end_verse < 0:
                new_ranges.append(
                    VerseRange(
                        start[1],
                        start[2],
                        start[3],
                        start[1],
                        vr.end_verse,
                        vr.end_subverse,
                    )
                )
                continue

            end = source.map_verse(
                self.book_id,
                vr.end_chapter,
                vr.end_verse,
                target,
                subverse=vr.end_subverse,
                end=True,
            )
            if end is None:
                return None

            new_ranges.append(
                VerseRange(
                    start[1],
                    start[2],
                    start[3],
                    end[1],
                    end[2],
                    end[3],
                )
            )

        new_book = self.book_id
        if new_ranges and not new_ranges[0].is_whole_chapters():
            mapped_start = source.map_verse(
                self.book_id,
                self.ranges[0].start_chapter,
                max(self.ranges[0].start_verse, 1),
                target,
                subverse=self.ranges[0].start_subverse,
            )
            if mapped_start is not None:
                new_book = mapped_start[0]

        return SimpleBibleRef(new_book, new_ranges)

    def resolve_following_verses(self, versification: Versification) -> None:
        """Resolve following verses in the verse ranges.

        This gives a definite end to ranges that use "ff" notation, namely, the
        last verse of the chapter.

        Args:
            versification: The Versification to use for resolving following verses

        """
        for range in self.ranges:
            if range.start_verse >= 0 and range.end_verse < 0:
                range.end_verse = versification.last_verse(
                    self.book_id, range.end_chapter
                )


@dataclass
class BibleRef:
    """Represents a sequence of verse ranges within one or more books of the Bible.

    A BibleRef consists of a list of SimpleBibleRef objects and the Versification
    they use. The versification can be None, though this will not usually be the case.
    It optionally stores the original text from which this reference was parsed.
    """

    simple_refs: list[SimpleBibleRef] = field(default_factory=list)
    versification: Versification | None = None
    original_text: str | None = None

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
        start_verse: int,
        end_chapter: int | None = None,
        end_verse: int | None = None,
        start_subverse: str = "",
        end_subverse: str = "",
        original_text: str | None = None,
        versification: Versification | None = None,
    ) -> "BibleRef":
        """Create a BibleRef with a single SimpleBibleRef containing a single VerseRange.

        Args:
            book_id: The book ID (e.g., "JHN" for John)
            chapter: The chapter number
            start_verse: The starting verse number
            end_chapter: The ending chapter number (defaults to start chapter if None)
            end_verse: The ending verse number (defaults to start verse if None)
            start_subverse: The starting subverse (defaults to "")
            end_subverse: The ending subverse (defaults to "")
            original_text: The original text from which this reference was parsed (defaults to None)
            versification: The Versification to use (defaults to None)

        Returns:
            A BibleRef instance with a single SimpleBibleRef containing a single VerseRange

        """
        simple_ref = SimpleBibleRef.for_range(
            book_id=book_id,
            chapter=chapter,
            start_verse=start_verse,
            end_chapter=end_chapter,
            end_verse=end_verse,
            start_subverse=start_subverse,
            end_subverse=end_subverse,
            original_text=original_text,
        )

        return cls(
            simple_refs=[simple_ref],
            versification=versification,
            original_text=original_text,
        )

    def is_whole_books(self) -> bool:
        """Return True if this reference refers to entire books only.

        Returns True iff all contained SimpleBibleRef instances refer to entire books.
        """
        return all(ref.is_whole_book() for ref in self.simple_refs)

    def is_whole_chapters(self) -> bool:
        """Return True if this reference does not specify verse limits.

        Returns True iff all contained SimpleBibleRef instances refer to whole chapters.
        """
        return all(ref.is_whole_chapters() for ref in self.simple_refs)

    def invalid_reason(self, style: RefStyle | None = None) -> str | None:
        """Explain why this Bible reference is invalid, or None if it is valid.

        The reference is invalid if it has no versification, or if any of its
        single-book references is invalid under that versification. When more
        than one is invalid, each reason is reported, joined by "; ".

        An empty BibleRef with a versification is vacuously valid.

        Args:
            style: Optional RefStyle whose book names are used to name books in
                the message. Without it, Paratext book IDs are used.

        Returns:
            An explanatory string, or None if the reference is valid.

        """
        if self.versification is None:
            return "no versification is set"

        reasons: list[str] = []
        for ref in self.simple_refs:
            reason = ref.invalid_reason(self.versification, style)
            if reason is not None:
                reasons.append(reason)

        return "; ".join(reasons) if reasons else None

    def is_valid(self) -> bool:
        """Check if this Bible reference is valid according to its versification.

        An empty BibleRef is vacuously valid.

        Returns:
            bool: True if the reference is valid, False otherwise

        """
        return self.invalid_reason() is None

    def range_keys(self) -> Generator[tuple[int, int], None, None]:
        """Yield an integer key range for each verse range in the ref.

        Book numbers are derived from self.versification, so it cannot be None.
        If any book ID in the simple refs is not included in the versification,
        no ranges for that book are yielded.

        Verse numbers less than 0 (undefined) are replaced with:
        - 0 for start verses
        - the last verse number for the chapter for end verses

        Yields:
            (start_key, end_key): integer keys for the start and end of a range in the ref
                Each key has 2 book digits, 3 chapter digits, and 3 verse digits.

        """
        if self.versification is None:
            return
        for simple_ref in self.simple_refs:
            yield from simple_ref.range_keys(self.versification)

    def range_refs(self) -> Generator["BibleRef", None, None]:
        """Yield a new BibleRef for each verse range across all simple refs.

        Each yielded BibleRef contains a single SimpleBibleRef with a single verse range.
        The versification is preserved.

        Yields:
            BibleRef: A new reference containing a single verse range

        """
        for simple_ref in self.simple_refs:
            for range_ref in simple_ref.range_refs():
                yield BibleRef(
                    simple_refs=[range_ref],
                    versification=self.versification,
                    original_text=range_ref.original_text,
                )

    def map_to(self, target: Versification) -> "BibleRef | None":
        """Map this reference into a different versification.

        Each verse location is mapped from this reference's versification to
        the target, going through the "org" (original languages) versification
        as an intermediary. Whole-chapter and whole-book references pass
        through unchanged.

        Args:
            target: The target Versification to map into

        Returns:
            A new BibleRef in the target versification, or None if this
            reference has no versification set or any verse does not exist
            in the target

        """
        if self.versification is None:
            return None

        new_simple_refs: list[SimpleBibleRef] = []
        for simple_ref in self.simple_refs:
            mapped = simple_ref.map(self.versification, target)
            if mapped is None:
                return None
            new_simple_refs.append(mapped)

        return BibleRef(new_simple_refs, target)

    def format(self, style: RefStyle) -> str:
        """Format this Bible reference as a string according to the given style.

        Args:
            style: The RefStyle to use for formatting

        Returns:
            A formatted string representation of this Bible reference

        """
        return style.chapter_separator.join(
            [r.format(style, self.versification) for r in self.simple_refs]
        )
