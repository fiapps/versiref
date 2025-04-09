"""
RefStyle definitions for Bible reference formatting and parsing.

This module provides the RefStyle class which defines how Bible references
are converted to and from strings.
"""

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Dict, Optional


def _invert(d: Dict[str, str]) -> Dict[str, str]:
    """Invert an ID->name dictionary, resolving conflicts if possible.

    In the event of a PSA/PSAS conflict or a EST/ESG conflict, the former of the
    pair is preferred. Any other conflict will raise a ValueError.
    """
    inverted: Dict[str, str] = {}
    for k, v in d.items():
        if v in inverted:
            if inverted[v] == "PSA" or inverted[v] == "PSAS":
                inverted[v] = "PSA"
            elif inverted[v] == "EST" or inverted[v] == "ESG":
                inverted[v] = "EST"
            else:
                raise ValueError(f"Both {inverted[v]} and {k} are abbreviated as {v}.")
        else:
            inverted[v] = k
    return inverted


@dataclass
class RefStyle:
    """
    Defines how a SimpleBibleRef is converted to and from strings.

    A RefStyle primarily holds data that specifies the formatting conventions
    for Bible references. Formatting and parsing is done by other classes
    that use a RefStyle as a specification.

    Attributes:
        names: Maps Bible book IDs to string abbreviations or full names
        chapter_verse_separator: Separates chapter number from verse ranges
        range_separator: Separates the ends of a range. Defaults to an en dash.
        following_verse: indicates the range ends at the verse following the start
        following_verses: indicates the range continues for an unspecified number of verses
        verse_range_separator: Separates ranges of verses in a single chapter
        chapter_separator: Separates ranges of verses in different chapters
        recognized_names: Maps abbreviations/names to Bible book IDs for parsing
    """

    names: Dict[str, str]
    chapter_verse_separator: str = ":"
    range_separator: str = "–"
    following_verse: str = "f"
    following_verses: str = "ff"
    verse_range_separator: str = ", "
    chapter_separator: str = "; "
    recognized_names: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Initialize recognized_names if not provided.

        By default, recognized_names is the inverse of names, allowing
        parsing of the same abbreviations used for formatting.
        """
        if not self.recognized_names:
            self.recognized_names = _invert(self.names)

    @staticmethod
    def standard_names(identifier: str) -> Optional[Dict[str, str]]:
        """
        Load and return a standard set of book names.

        These can be passed to RefStyle(). Since the return value has been created
        by loading a JSON file, it can be modified to customize the
        abbreviations (e.g, names["SNG"] = "Cant") without fear of changing the
        set of names for other callers.

        Args:
            identifier: The identifier for the names file, e.g.,
            "en-sbl_abbreviations"

        Returns:
            A dictionary mapping book IDs to names or abbreviations, or None if
            the file doesn't exist or has an invalid format.
        """
        try:
            # Use importlib.resources to find the file
            with resources.open_text(
                "versiref.data.book_names", f"{identifier}.json"
            ) as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return None
            if not all(
                isinstance(k, str) and isinstance(v, str) for k, v in data.items()
            ):
                return None
            return data
        except (FileNotFoundError, ModuleNotFoundError, json.JSONDecodeError):
            return None
