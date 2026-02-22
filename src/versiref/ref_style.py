"""RefStyle definitions for Bible reference formatting and parsing.

This module provides the RefStyle class which defines how Bible references
are converted to and from strings.
"""

import json
from dataclasses import dataclass, field
from importlib import resources


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
        identifier: optional name for the style

    """

    names: dict[str, str]
    chapter_verse_separator: str = ":"
    range_separator: str = "–"
    following_verse: str = "f"
    following_verses: str = "ff"
    verse_range_separator: str = ", "
    chapter_separator: str = "; "
    recognized_names: dict[str, str] = field(default_factory=dict)
    identifier: str | None = None

    def __post_init__(self) -> None:
        """Initialize recognized_names if not provided.

        By default, recognized_names is the inverse of names, allowing
        parsing of the same abbreviations used for formatting.
        """
        if not self.recognized_names:
            self.recognized_names = _invert(self.names)

    def __str__(self) -> str:
        """Return a string representation of this style.

        If an identifier is set, returns a concise form: RefStyle.named("identifier")
        Otherwise, returns the default representation.

        Returns:
            A string representation of this style

        """
        if self.identifier:
            return f'RefStyle.named("{self.identifier}")'
        return object.__str__(self)

    def also_recognize(self, names: dict[str, str] | str) -> None:
        """Add a set of book names to the recognized_names mapping.

        In the event of a conflict, the existing name will be preferred.

        Args:
            names: Either a dictionary mapping names or abbreviations to book IDs,
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

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RefStyle":
        """Create an instance from a dictionary.

        Args:
            data: A dictionary with a required "names" key (string identifier or
                dict mapping book IDs to names), optional separator fields, and an
                optional "also_recognize" list.

        Raises:
            ValueError: If "names" is missing from the dictionary.

        Returns:
            A newly constructed RefStyle

        """
        if "names" not in data:
            raise ValueError("RefStyle data must include 'names'")

        names_value = data["names"]
        if isinstance(names_value, str):
            names = standard_names(names_value)
        elif isinstance(names_value, dict):
            names = dict(names_value)
        else:
            raise ValueError("'names' must be a string or dict")

        def _str(key: str, default: str) -> str:
            val = data.get(key, default)
            return val if isinstance(val, str) else default

        style = cls(
            names=names,
            chapter_verse_separator=_str("chapter_verse_separator", ":"),
            range_separator=_str("range_separator", "\u2013"),
            following_verse=_str("following_verse", "f"),
            following_verses=_str("following_verses", "ff"),
            verse_range_separator=_str("verse_range_separator", ", "),
            chapter_separator=_str("chapter_separator", "; "),
        )

        also_recognize = data.get("also_recognize")
        if isinstance(also_recognize, list):
            for entry in also_recognize:
                if isinstance(entry, str):
                    style.also_recognize(entry)
                elif isinstance(entry, dict):
                    str_dict: dict[str, str] = {
                        str(k): str(v) for k, v in entry.items()
                    }
                    style.also_recognize(str_dict)

        return style

    @classmethod
    def from_file(cls, file_path: str, identifier: str | None = None) -> "RefStyle":
        """Create an instance from a JSON file.

        Args:
            file_path: Path to a JSON file containing style data.
            identifier: Optional identifier to store in the constructed RefStyle.

        Raises:
            FileNotFoundError: If file_path does not exist.
            json.JSONDecodeError: If file_path is not well-formed JSON.
            ValueError: If the data is missing required fields.

        Returns:
            A newly constructed RefStyle

        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        style = cls.from_dict(data)
        style.identifier = identifier
        return style

    @classmethod
    def named(cls, identifier: str) -> "RefStyle":
        """Create an instance of a standard style.

        Constructs an instance by loading JSON data from the package's data
        directory.

        Args:
            identifier: Standard style identifier (e.g., "en-sbl",
                "en-cmos_short").

        Raises:
            FileNotFoundError: If the named style doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            ValueError: If the JSON is not in the expected format.

        Returns:
            A newly constructed RefStyle

        """
        filename = f"{identifier}.json"
        path = resources.files("versiref").joinpath("data", "styles", filename)
        if path.is_file():
            return cls.from_file(str(path), identifier)
        else:
            raise FileNotFoundError(f"Unknown style identifier: {identifier}")


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
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the JSON is not in the expected format.
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
