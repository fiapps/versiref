"""RefStyle definitions for Bible reference formatting and parsing.

This module provides the RefStyle class which defines how Bible references
are converted to and from strings.
"""

import fnmatch
import json
from dataclasses import dataclass, field
from importlib import resources

from versiref.roman import int_to_roman

_CHAPTER_NUMBER_STYLES = ("arabic", "roman", "roman-lower")

# The pairs of book IDs that may share a name, mapping each to the book whose
# name wins (the same preference _invert applies).
SHARED_NAME_PARTNER = {"ESG": "EST", "PSAS": "PSA"}


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
        chapter_number_style: How chapter numbers are written: "arabic"
            (default), "roman" (uppercase Roman numerals, e.g. "XLIV"), or
            "roman-lower" (lowercase, e.g. "xliv"). Verse numbers are always
            Arabic.
        chapter_letters: Maps a book ID to the letters that serve as its
            chapter numbers, e.g. {"ESG": ["A", "B", "C", "D", "E", "F"]} for
            the way the NABRE prints the Additions to Esther. Chapter n of
            the book formats as the nth letter, and parsers accept the
            letters as chapters of that book — even when it shares a name
            with another book (as ESG may with EST).
        recognized_names: Maps abbreviations/names to Bible book IDs for parsing
        versification_identifiers: Maps a trailing designator (e.g. "Vulg.",
            "(LXX)") to a versification id string (e.g. "vulgata", "lxx"). A
            parser uses these to recognize a designator at the end of a reference
            and apply the named versification to it.
        identifier: optional name for the style

    """

    names: dict[str, str]
    chapter_verse_separator: str = ":"
    range_separator: str = "–"
    following_verse: str = "f"
    following_verses: str = "ff"
    verse_range_separator: str = ", "
    chapter_separator: str = "; "
    chapter_number_style: str = "arabic"
    chapter_letters: dict[str, list[str]] = field(default_factory=dict)
    recognized_names: dict[str, str] = field(default_factory=dict)
    versification_identifiers: dict[str, str] = field(default_factory=dict)
    identifier: str | None = None

    def __post_init__(self) -> None:
        """Initialize recognized_names if not provided.

        By default, recognized_names is the inverse of names, allowing
        parsing of the same abbreviations used for formatting.

        Raises:
            ValueError: If chapter_number_style is not one of the allowed
                values.

        """
        if self.chapter_number_style not in _CHAPTER_NUMBER_STYLES:
            raise ValueError(
                f"Invalid chapter_number_style: {self.chapter_number_style!r} "
                f"(expected one of {', '.join(_CHAPTER_NUMBER_STYLES)})"
            )
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

    def book_name(self, book_id: str) -> str:
        """Return the name used to format a book.

        A book with chapter letters takes the name of the book it shares a
        name with (ESG takes EST's name), ignoring any name of its own: the
        letters alone distinguish its references, as when the NABRE cites
        the Additions to Esther as "Est A" through "Est F".

        Args:
            book_id: The book to name.

        Returns:
            The book's name in this style.

        Raises:
            ValueError: If the style has no name for the book.

        """
        if book_id in self.chapter_letters:
            partner = SHARED_NAME_PARTNER.get(book_id)
            if partner is not None and partner in self.names:
                return self.names[partner]
        if book_id not in self.names:
            raise ValueError(f"Unknown book ID: {book_id}")
        return self.names[book_id]

    def format_chapter(self, chapter: int, book_id: str | None = None) -> str:
        """Render a chapter number according to the style.

        Args:
            chapter: The chapter number to render.
            book_id: The book the chapter belongs to. When the book has an
                entry in chapter_letters, the chapter renders as its letter;
                otherwise chapter_number_style governs.

        Returns:
            The chapter number as a string.

        Raises:
            ValueError: If the book uses chapter letters but has no letter
                for this chapter number.

        """
        if book_id is not None and book_id in self.chapter_letters:
            letters = self.chapter_letters[book_id]
            if 1 <= chapter <= len(letters):
                return letters[chapter - 1]
            raise ValueError(
                f"No chapter letter for {book_id} {chapter}: "
                f"the style defines letters for {len(letters)} chapters"
            )
        if self.chapter_number_style == "roman":
            return int_to_roman(chapter)
        elif self.chapter_number_style == "roman-lower":
            return int_to_roman(chapter).lower()
        else:
            return str(chapter)

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

    def also_recognize_versifications(self, mapping: dict[str, str]) -> None:
        """Add designators to the versification_identifiers mapping.

        In the event of a conflict, the existing entry will be preferred. This
        lets a base style's designators win over a derived style's, mirroring
        :meth:`also_recognize`.

        Args:
            mapping: A dictionary mapping trailing designators (e.g. "Vulg.")
                to versification id strings (e.g. "vulgata").

        """
        self.versification_identifiers.update(
            {
                designator: id
                for designator, id in mapping.items()
                if designator not in self.versification_identifiers
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RefStyle":
        """Create an instance from a dictionary.

        Args:
            data: A dictionary with either a "names" key (string identifier or
                dict mapping book IDs to names) or a "base" key (identifier of a
                standard style to inherit from), but not both. Optional separator
                fields override the defaults (or the base style's values), an
                optional "also_recognize" list adds extra recognized names, an
                optional "chapter_letters" dict maps book IDs to their chapter
                letters (replacing any inherited from a base style), and an
                optional "versification_identifiers" dict maps trailing
                designators to versification id strings (existing entries win, so
                a base style's designators are preserved).

        Raises:
            ValueError: If neither "names" nor "base" is present, or if both are.

        Returns:
            A newly constructed RefStyle

        """
        has_names = "names" in data
        has_base = "base" in data

        if has_names and has_base:
            raise ValueError("RefStyle data must not include both 'names' and 'base'")

        _separator_keys = (
            "chapter_verse_separator",
            "range_separator",
            "following_verse",
            "following_verses",
            "verse_range_separator",
            "chapter_separator",
            "chapter_number_style",
        )

        if has_base:
            base_value = data["base"]
            if not isinstance(base_value, str):
                raise ValueError("'base' must be a string identifier")
            style = cls.named(base_value)
            style.identifier = None
            for key in _separator_keys:
                val = data.get(key)
                if isinstance(val, str):
                    setattr(style, key, val)
        else:
            if not has_names:
                raise ValueError("RefStyle data must include 'names' or 'base'")
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
                chapter_number_style=_str("chapter_number_style", "arabic"),
            )

        chapter_letters = data.get("chapter_letters")
        if isinstance(chapter_letters, dict):
            style.chapter_letters = {
                str(book): [str(letter) for letter in letters]
                for book, letters in chapter_letters.items()
                if isinstance(letters, list)
            }

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

        versification_identifiers = data.get("versification_identifiers")
        if isinstance(versification_identifiers, dict):
            style.also_recognize_versifications(
                {str(k): str(v) for k, v in versification_identifiers.items()}
            )

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
            identifier: Standard style identifier. Some common values:

                - "en-sbl" — SBL (Society of Biblical Literature)
                - "en-nabre" — SBL extended with the NABRE's Esther chapter
                  letters (Est A–F)
                - "en-cmos_short" — Chicago Manual of Style, short abbreviations
                - "en-cmos_long" — Chicago Manual of Style, long abbreviations
                - "it-cei" — Italian CEI (Conferenza Episcopale Italiana)
                - "la-cce" — Latin, Catechismus Catholicae Ecclesiae abbreviations
                - "la-vetus" — Latin, traditional abbreviations with Roman-numeral
                  chapters (as in the Patrologia Latina and similar editions)

                Call :meth:`available_names` for the full list of bundled
                identifiers.

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

    @classmethod
    def available_names(cls, pattern: str = "*") -> list[str]:
        """Return the identifiers accepted by :meth:`named`.

        Discovered by listing the JSON files in the package's bundled
        style data directory.

        Args:
            pattern: Optional :mod:`fnmatch`-style glob applied to each
                identifier (the JSON filename without its extension).
                Defaults to ``"*"``, which matches every bundled style.
                Useful for restricting results by language prefix, e.g.
                ``"en-*"`` or ``"it-*"``.

        Returns:
            A sorted list of identifiers that can be passed to ``named()``.

        """
        directory = resources.files("versiref").joinpath("data", "styles")
        stems = (
            entry.name.removesuffix(".json")
            for entry in directory.iterdir()
            if entry.is_file() and entry.name.endswith(".json")
        )
        return sorted(s for s in stems if fnmatch.fnmatchcase(s, pattern))


def standard_names(identifier: str) -> dict[str, str]:
    """Load and return a standard set of book names.

    These can be passed to RefStyle(). Since the return value is freshly
    created, it can be modified to customize the abbreviations (e.g,
    names["SNG"] = "Cant") without fear of changing the set of names for other
    callers.

    Args:
        identifier: Identifier for the names file. Some common values:

            - "en-sbl_abbreviations" — SBL abbreviations (e.g., "Josh", "1 Kgs")
            - "en-sbl_names" — SBL full names (e.g., "Joshua", "1 Kings")
            - "en-cmos_short" — Chicago Manual of Style short forms (e.g., "Jo", "1 Kgs")
            - "en-cmos_long" — Chicago Manual of Style long forms (e.g., "Josh.", "1 Kings")
            - "en-douay-rheims_names" — Douay-Rheims names (e.g., "Josue", "3 Kings")
            - "it-cei_abbreviazioni" — Italian CEI abbreviations (e.g., "Gs", "1Re")
            - "it-cei_nomi" — Italian CEI full names (e.g., "Giosuè", "1 Re")
            - "la-cce_abbreviationes" — Latin abbreviations of the Catechismus
              Catholicae Ecclesiae (e.g., "Ios", "1 Reg")
            - "la-vetus_abbreviationes" — traditional Latin abbreviations
              (e.g., "Judic.", "III Reg.")
            - "la-nomina" — full Latin book names (e.g., "Iosue", "Canticum
              Canticorum")

            Call :func:`available_standard_names` for the full list of
            bundled identifiers.

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


def available_standard_names(pattern: str = "*") -> list[str]:
    """Return the identifiers accepted by :func:`standard_names`.

    Discovered by listing the JSON files in the package's bundled book
    names data directory.

    Args:
        pattern: Optional :mod:`fnmatch`-style glob applied to each
            identifier (the JSON filename without its extension).
            Defaults to ``"*"``, which matches every bundled set.
            Useful for restricting results by language prefix, e.g.
            ``"en-*"`` or ``"it-*"``.

    Returns:
        A sorted list of identifiers that can be passed to ``standard_names()``.

    """
    directory = resources.files("versiref").joinpath("data", "book_names")
    stems = (
        entry.name.removesuffix(".json")
        for entry in directory.iterdir()
        if entry.is_file() and entry.name.endswith(".json")
    )
    return sorted(s for s in stems if fnmatch.fnmatchcase(s, pattern))
