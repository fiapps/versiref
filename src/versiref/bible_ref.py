"""Bible reference handling for versiref.

This module provides classes for representing and manipulating Bible references.
"""

from dataclasses import dataclass, field
from typing import Generator, Optional

from versiref.ref_style import RefStyle
from versiref.versification import Versification


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
    original_text: Optional[str] = None

    def is_whole_chapters(self) -> bool:
        """Return True if this range does not specify verse limits."""
        return self.start_verse < 0 and self.end_verse < 0

    def is_valid(self) -> bool:
        """Check if this verse range has valid values.

        Returns False if any of these conditions are met:
        - start_verse >= 0 and end_verse < 0 (ff notation) but start_chapter != end_chapter
        - start_verse < 0 and end_verse >= 0
        - start_chapter == end_chapter and start_verse > end_verse
        - start_chapter > end_chapter

        Returns:
            bool: True if the verse range has valid values, False otherwise

        """
        # Check for invalid "ff" notation (must be in same chapter)
        if (
            self.start_verse >= 0
            and self.end_verse < 0
            and self.start_chapter != self.end_chapter
        ):
            return False

        # Cannot have unspecified start verse but specified end verse
        if self.start_verse < 0 and self.end_verse >= 0:
            return False

        # Cannot have start verse greater than end verse in same chapter
        if (
            self.start_chapter == self.end_chapter
            and self.start_verse > self.end_verse
            and self.end_verse >= 0
        ):
            return False

        # Cannot have start chapter greater than end chapter
        if self.start_chapter > self.end_chapter:
            return False

        return True


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
    original_text: Optional[str] = None

    @classmethod
    def for_range(
        cls,
        book_id: str,
        chapter: int,
        start_verse: int,
        end_chapter: Optional[int] = None,
        end_verse: Optional[int] = None,
        start_subverse: str = "",
        end_subverse: str = "",
        original_text: Optional[str] = None,
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

    def is_valid(self, versification: Versification) -> bool:
        """Check if this Bible reference is valid according to the given versification.

        Args:
            versification: The Versification to check against

        Returns:
            bool: True if the reference is valid, False otherwise

        """
        # Check if the book ID is included in the versification
        if not versification.includes(self.book_id):
            return False

        # Check each verse range
        for verse_range in self.ranges:
            # Check if the verse range itself is valid.
            # This will catch ranges that end before they start.
            if not verse_range.is_valid():
                return False

            # Check if the chapters and verses are within the limits of the versification.
            if versification.last_verse(self.book_id, verse_range.end_chapter) < 0:
                return False

            # We only need to check the start if it's in a different chapter or the end is indefinite.
            if (
                verse_range.start_chapter != verse_range.end_chapter
                or verse_range.end_verse < 0
            ) and verse_range.start_verse > versification.last_verse(
                self.book_id, verse_range.start_chapter
            ):
                return False

            # Check end. No special handling is needed if end_verse < 0.
            if verse_range.end_verse > versification.last_verse(
                self.book_id, verse_range.end_chapter
            ):
                return False

        return True

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

    def format(
        self, style: RefStyle, versification: Optional[Versification] = None
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
        # Get the book name according to the style
        if self.book_id not in style.names:
            raise ValueError(f"Unknown book ID: {self.book_id}")

        # We start with the book name and then add ranges incrementally.
        result = style.names[self.book_id]
        last_range = None
        for range in self.ranges:
            if last_range is None:
                result += " "
                if versification is not None and versification.is_single_chapter(
                    self.book_id
                ):
                    states_chapter = False
                else:
                    result += str(range.start_chapter)
                    states_chapter = True
            elif last_range.end_chapter != range.start_chapter:
                result += f"{style.chapter_separator}{range.start_chapter}"
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
                    result += str(range.end_chapter)
                    if range.end_verse >= 0:
                        result += f"{style.chapter_verse_separator}{range.end_verse}"
                elif range.end_verse != range.start_verse:
                    result += f"{range.end_verse}"
                if range.end_verse >= 0:
                    result += range.end_subverse
            last_range = range
        return result

    def resolve_following_verses(self, versification: Versification) -> None:
        """Resolve following verses in the verse ranges.

        This gives a definite end to ranges that use "ff" notation, namely, the
        last verse of the chapter.

        Args:
            versification: The Versification to use for resolving following
            verses

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
    versification: Optional[Versification] = None
    original_text: Optional[str] = None

    @classmethod
    def for_range(
        cls,
        book_id: str,
        chapter: int,
        start_verse: int,
        end_chapter: Optional[int] = None,
        end_verse: Optional[int] = None,
        start_subverse: str = "",
        end_subverse: str = "",
        original_text: Optional[str] = None,
        versification: Optional[Versification] = None,
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

    def is_valid(self) -> bool:
        """Check if this Bible reference is valid according to its versification.

        An empty BibleRef is vacuously valid.

        Returns:
            bool: True if the reference is valid, False otherwise

        """
        if self.versification is None:
            return False
        return all(ref.is_valid(self.versification) for ref in self.simple_refs)

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
