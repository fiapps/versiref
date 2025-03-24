"""
Bible reference handling for versiref.

This module provides classes for representing and manipulating Bible references.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VerseRange:
    """
    Represents a range of verses within a single book of the Bible.

    A verse range has a start and end point, each defined by chapter, verse, and sub-verse.
    The original text from which this range was parsed can be stored.
    """

    start_chapter: int
    start_verse: int
    start_sub_verse: str
    end_chapter: int
    end_verse: int
    end_sub_verse: str
    original_text: Optional[str] = None


@dataclass
class SimpleBibleRef:
    """
    Represents a sequence of verse ranges within a single book of the Bible.

    A SimpleBibleRef consists of a book ID (using Paratext three-letter codes)
    and a list of verse ranges. The ranges are not necessarily in numeric order.
    A SimpleBibleRef with an empty list of ranges refers to the entire book.
    It optionally stores the original text from which the book ID was parsed.

    This class is "naive" in that it doesn't specify its versification system.
    """

    book_id: str
    ranges: List[VerseRange] = field(default_factory=list)
    original_text: Optional[str] = None

    def is_whole_book(self) -> bool:
        """Return True if this reference refers to the entire book."""
        return len(self.ranges) == 0
