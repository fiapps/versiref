"""
Style definitions for Bible reference formatting and parsing.

This module provides the Style class which defines how Bible references
are converted to and from strings.
"""

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Dict, Optional


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
        range_separator: Separates the ends of a range. Defaults to an en dash.
        verse_range_separator: Separates ranges of verses in a single chapter
        chapter_separator: Separates ranges of verses in different chapters
        recognized_names: Maps abbreviations/names to Bible book IDs for parsing
    """
    
    names: Dict[str, str]
    chapter_verse_separator: str = ":"
    range_separator: str = "–"
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

    @staticmethod
    def standard_names(identifier: str) -> Optional[Dict[str, str]]:
        """
        Load and return a standard set of book names.
        
        These can be passed to Style(). Since the return value has been created
        by loading a JSON file, it can be modified to customize the
        abbreviations (e.g, names["SNG"] = "Cant") without fear of changing the
        set of names for other callers.

        Args:
            identifier: The identifier for the names file, e.g.,
            "en-sbl_abbreviations"
        
        Returns:
            A dictionary mapping book IDs to names or abbreviations, or None if
            the file doesn't exist
        """
        try:
            # Use importlib.resources to find the file
            with resources.open_text("versiref.data.book_names", f"{identifier}.json") as f:
                return json.load(f)
        except (FileNotFoundError, ModuleNotFoundError):
            return None
