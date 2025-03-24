"""
Bible reference handling for bibl_sacra_pagina.

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
    start_chapter: str
    start_verse: str
    start_sub_verse: str = ""
    end_chapter: str = ""
    end_verse: str = ""
    end_sub_verse: str = ""
    original_text: Optional[str] = None
    
    def __post_init__(self):
        """Ensure end values default to start values if not provided."""
        if not self.end_chapter:
            self.end_chapter = self.start_chapter
        if not self.end_verse:
            self.end_verse = self.start_verse


@dataclass
class SimpleBibleRef:
    """
    Represents a sequence of verse ranges within a single book of the Bible.
    
    A SimpleBibleRef consists of a book ID (using Paratext three-letter codes)
    and a list of verse ranges. The ranges are not necessarily in numeric order.
    A SimpleBibleRef with an empty list of ranges refers to the entire book.
    
    This class is "naive" in that it doesn't specify its versification system.
    """
    book_id: str
    ranges: List[VerseRange] = field(default_factory=list)
    original_text: Optional[str] = None
    
    def is_whole_book(self) -> bool:
        """Return True if this reference refers to the entire book."""
        return len(self.ranges) == 0
