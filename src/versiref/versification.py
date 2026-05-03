"""Versification class for handling Bible chapter and verse divisions."""

import json
import logging
import re
from dataclasses import dataclass, field
from importlib import resources

logger = logging.getLogger(__name__)

_VERSE_RE = re.compile(r"^([A-Z0-9]{3}) (\d+):(\d+)([a-z])?(?:-(\d+)([a-z])?)?$")

_VerseLoc = tuple[str, int, int, str]
_VerseLocRange = tuple[_VerseLoc, _VerseLoc]


@dataclass
class Versification:
    """Represents a way of dividing the text of the Bible into chapters and verses.

    Versifications are defined by JSON data that is loaded from a file when an instance is created.
    The class provides methods to query information about the versification, such as the last verse
    of a given chapter in a given book.

    Attributes:
        max_verses: last valid verse number for each chapter of each book
            The order of keys defines the book order.
        identifier: optional name for the versification

    """

    max_verses: dict[str, list[int]] = field(default_factory=dict)
    identifier: str | None = None
    _map_to_org: dict[_VerseLoc, _VerseLocRange] = field(
        default_factory=dict, repr=False
    )
    _map_from_org: dict[_VerseLoc, _VerseLocRange] = field(
        default_factory=dict, repr=False
    )

    def __str__(self) -> str:
        """Return a string representation of this versification.

        If an identifier is set, returns a concise form: Versification.named("identifier")
        Otherwise, returns the default dataclass representation.

        Returns:
            A string representation of this versification

        """
        if self.identifier:
            return f'Versification.named("{self.identifier}")'
        return object.__str__(self)

    @classmethod
    def from_file(
        cls, file_path: str, identifier: str | None = None
    ) -> "Versification":
        """Create an instance from a JSON file.

        Args:
            file_path: path to a JSON file containing an object with maxVerses
            identifier: identifier to store in the constructed Versififaction
        Raises:
            FileNotFoundError: file_path does not exist
            json.JSONDecodeError: file_path is not well-formed JSON
            ValueError: file_path does not match schema
        Returns:
            Newly constructed Versification

        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "maxVerses" not in data:
            raise ValueError("Versification file does not match schema")

        max_verses = {}
        for book, verses in data["maxVerses"].items():
            max_verses[book] = [int(v) for v in verses]

        map_to_org: dict[_VerseLoc, _VerseLocRange] = {}
        map_from_org: dict[_VerseLoc, _VerseLocRange] = {}
        for src_str, dst_str in data.get("mappedVerses", {}).items():
            src_m = _VERSE_RE.match(src_str)
            dst_m = _VERSE_RE.match(dst_str)
            if not src_m or not dst_m:
                logger.warning(
                    "Skipping malformed mappedVerses entry: %r -> %r",
                    src_str,
                    dst_str,
                )
                continue
            src_book, src_ch, src_v1 = (
                src_m.group(1),
                int(src_m.group(2)),
                int(src_m.group(3)),
            )
            src_sv1 = src_m.group(4) or ""
            dst_book, dst_ch, dst_v1 = (
                dst_m.group(1),
                int(dst_m.group(2)),
                int(dst_m.group(3)),
            )
            dst_sv1 = dst_m.group(4) or ""
            src_v2 = int(src_m.group(5)) if src_m.group(5) else src_v1
            dst_v2 = int(dst_m.group(5)) if dst_m.group(5) else dst_v1
            src_count = src_v2 - src_v1 + 1
            dst_count = dst_v2 - dst_v1 + 1
            if src_count < 1 or dst_count < 1:
                logger.debug(
                    "Skipping mappedVerses entry with invalid range: %r -> %r",
                    src_str,
                    dst_str,
                )
                continue
            if src_count == dst_count:
                for i in range(src_count):
                    src_sv = src_sv1 if src_count == 1 else ""
                    dst_sv = dst_sv1 if src_count == 1 else ""
                    src_loc = (src_book, src_ch, src_v1 + i, src_sv)
                    dst_loc = (dst_book, dst_ch, dst_v1 + i, dst_sv)
                    map_to_org[src_loc] = (dst_loc, dst_loc)
                    map_from_org[dst_loc] = (src_loc, src_loc)
            else:
                dst_start: _VerseLoc = (dst_book, dst_ch, dst_v1, dst_sv1)
                dst_end: _VerseLoc = (dst_book, dst_ch, dst_v2, "")
                src_start: _VerseLoc = (src_book, src_ch, src_v1, src_sv1)
                src_end: _VerseLoc = (src_book, src_ch, src_v2, "")
                for i in range(src_count):
                    src_loc = (src_book, src_ch, src_v1 + i, "")
                    map_to_org[src_loc] = (dst_start, dst_end)
                for i in range(dst_count):
                    dst_loc = (dst_book, dst_ch, dst_v1 + i, "")
                    map_from_org[dst_loc] = (src_start, src_end)

        return cls(max_verses, identifier, map_to_org, map_from_org)

    @classmethod
    def named(cls, identifier: str) -> "Versification":
        """Create an instance of a standard versification.

        Constructs an instance by loading JSON data from the package's data
        directory.

        Args:
            identifier: Standard versification identifier. Available values:

                - "org" — original languages (BHS, UBS GNT)
                - "eng" — typical English Bible
                - "lxx" — Septuagint
                - "vulgata" — Latin Vulgate
                - "nova_vulgata" — Nova Vulgata
                - "cei" — Conferenza Episcopale Italiana (2008)
                - "nabre" — New American Bible Revised Edition
                - "rsc" — Russian Synodal, Protestant canon
                - "rso" — Russian Synodal, Orthodox canon

                Case-insensitive (converted to lowercase to find the file).

        Raises:
            FileNotFoundError: If the named file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
            ValueError: If the JSON is not in the expected format

        Returns:
            A newly constructed Versification

        """
        filename = f"{identifier.lower()}.json"

        path = resources.files("versiref").joinpath("data", "versifications", filename)
        if path.is_file():
            return cls.from_file(str(path), identifier)
        else:
            raise FileNotFoundError(f"Unknown versification identifier: {identifier}")

    def includes(self, book_id: str) -> bool:
        """Check if the given book ID is included in this versification.

        Args:
            book_id: The book ID (using Paratext three-letter codes)

        Returns:
            True if the book is included in this versification, False otherwise.

        """
        if book_id == "PSAS":  # Plural form of PSA
            book_id = "PSA"
        return book_id in self.max_verses

    def is_single_chapter(self, book: str) -> bool:
        """Check if the given book is a single-chapter book.

        Args:
            book: The book ID (using Paratext three-letter codes)

        Returns:
            True if the book has only one chapter, False otherwise.

        """
        if book not in self.max_verses:
            return False
        # The plural form of PSA requires special handling.
        if book == "PSAS":
            book = "PSA"
        return len(self.max_verses[book]) == 1

    def last_verse(self, book: str, chapter: int) -> int:
        """Return the number of the last verse of the given chapter of the given book.

        Args:
            book: The book ID (using Paratext three-letter codes)
            chapter: The chapter number

        Returns:
            The number of the last verse, or -1 if the book or chapter doesn't exist

        """
        # Trivial implementation returns 99 for any book and chapter
        if not self.max_verses:
            return 99

        # Check if the book exists in the versification
        if book == "PSAS":  # plural of PSA
            book = "PSA"
        if book not in self.max_verses:
            return -1

        # Check if the chapter exists in the book
        if chapter < 0 or chapter > len(self.max_verses[book]):
            return -1

        # Return the verse count as an integer
        return self.max_verses[book][chapter - 1]

    def map_verse(
        self,
        book: str,
        chapter: int,
        verse: int,
        target: "Versification",
        subverse: str = "",
        *,
        end: bool = False,
    ) -> _VerseLoc | None:
        """Map a single verse location from this versification to another.

        Maps through the "org" (original languages) versification as an
        intermediary. Verses with no explicit mapping are assumed identical
        across versifications. Returns None if the mapped verse does not
        exist in the target versification.

        Args:
            book: The book ID in this versification
            chapter: The chapter number in this versification
            verse: The verse number in this versification
            target: The target Versification to map into
            subverse: The subverse letter in this versification (default "")
            end: If True, select the end of the mapped range; otherwise the start

        Returns:
            A (book, chapter, verse, subverse) tuple in the target
            versification, or None if the verse does not exist there

        """
        if self is target:
            return (book, chapter, verse, subverse)

        loc = (book, chapter, verse, subverse)
        idx = 1 if end else 0
        org_range = self._map_to_org.get(loc)
        org_loc = org_range[idx] if org_range else loc
        target_range = target._map_from_org.get(org_loc)
        result = target_range[idx] if target_range else org_loc

        if target.last_verse(result[0], result[1]) < result[2]:
            return None
        return result
