"""RefStyle definitions for Bible reference formatting and parsing.

This module provides the RefStyle class which defines how Bible references
are converted to and from strings.
"""

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Union


def _invert(d: dict[str, str]) -> dict[str, str]:
    """Invert an ID->name dictionary, resolving conflicts if possible.

    In the event of a PSA/PSAS conflict or a EST/ESG conflict, the former of the
    pair is preferred. Any other conflict will raise a ValueError.
    """
    inverted: dict[str, str] = {}
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
    """Defines how a SimpleBibleRef is converted to and from strings.

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

    names: dict[str, str]
    chapter_verse_separator: str = ":"
    range_separator: str = "–"
    following_verse: str = "f"
    following_verses: str = "ff"
    verse_range_separator: str = ", "
    chapter_separator: str = "; "
    recognized_names: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize recognized_names if not provided.

        By default, recognized_names is the inverse of names, allowing
        parsing of the same abbreviations used for formatting.
        """
        if not self.recognized_names:
            self.recognized_names = _invert(self.names)

    def also_recognize(self, names: Union[dict[str, str], str]) -> None:
        """Add a set of book names to the recognized_names mapping.

        In the event of a conflict, the existing name will be preferred.

        Args:
            names: Either dictionary mapping names or abbreviations to book IDs
            or a string that names a standard set of names, e.g.,
            "en-sbl_abbreviations".

        """
        if isinstance(names, str):
            names = _invert(standard_names(names))
        self.recognized_names.update(
            {
                name: id
                for name, id in names.items()
                if name not in self.recognized_names
            }
        )


def standard_names(identifier: str) -> dict[str, str]:
    """Load and return a standard set of book names.

    These can be passed to RefStyle(). Since the return value is freshly
    created, it can be modified to customize the abbreviations (e.g,
    names["SNG"] = "Cant") without fear of changing the set of names for other
    callers.

    Args:
        identifier: The identifier for the names file, e.g.,
        "en-sbl_abbreviations"

    Returns:
        A dictionary mapping book IDs to names or abbreviations.

    Raises:
        FileNotFoundError: If the names file doesn't exist
        json.JSONDecodeError: if the file contains invalid JSON
        ValueError: If the JSON is not in the expected format
        The latter two represent internal errors in the package.

    """
    # Use importlib.resources to find the file
    data = json.loads(
        resources.files("versiref")
        .joinpath("data", "book_names", f"{identifier}.json")
        .read_text()
    )
    if not isinstance(data, dict):
        raise ValueError(f"Invalid format in {identifier}.json: not a dictionary")
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError(
            f"Invalid format in {identifier}.json: all keys and values must be strings"
        )
    return data
