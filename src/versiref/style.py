"""
Style definitions for Bible reference formatting and parsing.

This module provides the Style class which defines how Bible references
are converted to and from strings.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Style:
    """
    Defines how a SimpleBibleRef is converted to and from strings.
    
    A Style primarily holds data that specifies the formatting conventions
    for Bible references. Formatting and parsing is done by other classes
    that use a Style as a specification.
    
    Attributes:
        names: Maps Bible book IDs to string abbreviations or full names
        chapter_verse_separator: Separates chapter number from verse ranges
        verse_range_separator: Separates ranges of verses in a single chapter
        chapter_separator: Separates different chapters in a reference
        recognized_names: Maps abbreviations/names to Bible book IDs for parsing
    """
    
    names: Dict[str, str]
    chapter_verse_separator: str = ":"
    verse_range_separator: str = ", "
    chapter_separator: str = "; "
    recognized_names: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        Initialize recognized_names if not provided.
        
        By default, recognized_names is the inverse of names, allowing
        parsing of the same abbreviations used for formatting.
        """
        if not self.recognized_names:
            # Create inverse mapping of names by default
            self.recognized_names = {name: book_id for book_id, name in self.names.items()}
