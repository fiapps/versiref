"""Versification class for handling Bible chapter and verse divisions."""

import json
import logging
import re
from dataclasses import dataclass, field
from importlib import resources

logger = logging.getLogger(__name__)

_VERSE_RE = re.compile(r"^([A-Z0-9]{3}) (\d+):(\d+)([a-z])?(?:-(\d+)([a-z])?)?$")
_PARTIAL_VERSE_RE = re.compile(r"^([A-Z0-9]{3}) (\d+):(\d+)$")

_VerseLoc = tuple[str, int, int, str]
_VerseLocRange = tuple[_VerseLoc, _VerseLoc]


# Books that hold a second, parallel arrangement of material another book of the
# same versification already carries: ``DAG`` (Greek Daniel) numbers Susanna,
# the Song of the Three and Bel continuously alongside ``DAN``. Their entries
# map into org like any other, but they are not org's way back: an org verse's
# inverse belongs to the book that references actually name, so ``BEL 1:1``
# returns to the Vulgate's ``DAN 13:65`` and to ``BEL 1:1`` in versifications
# that keep Bel as its own book, never to the unnameable ``DAG 14:1``.
_PARALLEL_BOOKS = frozenset({"DAG"})


def _map_stage(
    mapping: dict[_VerseLoc, _VerseLocRange],
    multi: set[_VerseLoc],
    loc: _VerseLoc,
    idx: int,
) -> tuple[_VerseLoc, bool]:
    """Map one location through a single mapping dictionary.

    Args:
        mapping: A verse mapping (``_map_to_org`` or ``_map_from_org``)
        multi: Base locations whose mapping is not one-to-one
        loc: The (book, chapter, verse, subverse) location to map
        idx: 0 for the start of the mapped range, 1 for the end

    Returns:
        A (mapped location, is_one_to_one) pair. The mapped location's
        subverse carries ``loc``'s subverse through a one-to-one mapping and is
        empty otherwise.

    """
    book, chapter, verse, subverse = loc
    if subverse:
        exact = mapping.get(loc)
        if exact is not None:
            return exact[idx], True
    base = (book, chapter, verse, "")
    rng = mapping.get(base)
    if rng is None:
        return loc, True
    mapped = rng[idx]
    if base in multi:
        return (mapped[0], mapped[1], mapped[2], ""), False
    # A subverse on the mapped location is a structural (deuterocanonical)
    # insertion from the data; otherwise carry the input's portion subverse.
    return (mapped[0], mapped[1], mapped[2], mapped[3] or subverse), True


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
    # Base locations (subverse "") whose verse mapping is not one-to-one, i.e.
    # part of a 1:N or N:1 mapping. A portion-of-verse subverse cannot survive
    # such a mapping and must be discarded.
    _multi_to_org: set[_VerseLoc] = field(default_factory=set, repr=False)
    _multi_from_org: set[_VerseLoc] = field(default_factory=set, repr=False)
    # For each verse that is followed by inserted or partial verses (e.g. the
    # Greek additions to Esther), maps each inserted subverse letter to its
    # ordinal within the verse (the base verse being 0). Verses absent here have
    # no inserted verses; a subverse cited on them is a portion of a single
    # verse, not an insertion. Loaded from the data's ``partialVerses``.
    _partial_verses: dict[tuple[str, int, int], dict[str, int]] = field(
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
        multi_to_org: set[_VerseLoc] = set()
        multi_from_org: set[_VerseLoc] = set()
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
                    if src_book not in _PARALLEL_BOOKS:
                        map_from_org[dst_loc] = (src_loc, src_loc)
            else:
                # A side that is a single verse keeps its subverse, as in the
                # one-to-one branch above. Dropping it would key the entry on
                # the base verse and hijack it: an inserted verse that answers
                # to two verses of the other text (cei's ESG 8:12u, which is
                # org's ESG 8:34-35) would capture plain ESG 8:12.
                src_sv = src_sv1 if src_count == 1 else ""
                dst_sv = dst_sv1 if dst_count == 1 else ""
                dst_start: _VerseLoc = (dst_book, dst_ch, dst_v1, dst_sv1)
                dst_end: _VerseLoc = (dst_book, dst_ch, dst_v2, dst_sv)
                src_start: _VerseLoc = (src_book, src_ch, src_v1, src_sv1)
                src_end: _VerseLoc = (src_book, src_ch, src_v2, src_sv)
                for i in range(src_count):
                    src_loc = (src_book, src_ch, src_v1 + i, src_sv)
                    map_to_org[src_loc] = (dst_start, dst_end)
                    multi_to_org.add(src_loc)
                for i in range(dst_count):
                    dst_loc = (dst_book, dst_ch, dst_v1 + i, dst_sv)
                    if src_book in _PARALLEL_BOOKS:
                        continue
                    map_from_org[dst_loc] = (src_start, src_end)
                    multi_from_org.add(dst_loc)

        partial_verses: dict[tuple[str, int, int], dict[str, int]] = {}
        for ref_str, parts in data.get("partialVerses", {}).items():
            m = _PARTIAL_VERSE_RE.match(ref_str)
            if not m:
                logger.warning("Skipping malformed partialVerses entry: %r", ref_str)
                continue
            loc = (m.group(1), int(m.group(2)), int(m.group(3)))
            partial_verses[loc] = {
                stripped: idx
                for idx, part in enumerate(parts)
                if (stripped := part.strip()) and stripped != "-"
            }

        return cls(
            max_verses,
            identifier,
            map_to_org,
            map_from_org,
            multi_to_org,
            multi_from_org,
            partial_verses,
        )

    @classmethod
    def named(cls, identifier: str) -> "Versification":
        """Create an instance of a standard versification.

        Constructs an instance by loading JSON data from the package's data
        directory.

        Args:
            identifier: Standard versification identifier. Some common values:

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
                Call :meth:`available_names` for the full list of bundled
                identifiers.

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

    @classmethod
    def available_names(cls) -> list[str]:
        """Return the identifiers accepted by :meth:`named`.

        Discovered by listing the JSON files in the package's bundled
        versification data directory.

        Returns:
            A sorted list of identifiers that can be passed to ``named()``.

        """
        directory = resources.files("versiref").joinpath("data", "versifications")
        return sorted(
            entry.name.removesuffix(".json")
            for entry in directory.iterdir()
            if entry.is_file() and entry.name.endswith(".json")
        )

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

    def partial_ordinal(
        self, book: str, chapter: int, verse: int, subverse: str
    ) -> int:
        """Return the sort ordinal of a subverse within its verse.

        A verse listed in the versification's ``partialVerses`` is followed by
        inserted or partial verses (for example the Greek additions to Esther,
        ESG 4:17a-z, which follow but are not part of ESG 4:17). Each such part
        is numbered by its position in that verse's part list, the base
        (unlettered) verse being 0, so that an inserted verse sorts after its
        base verse and before the next verse.

        A subverse cited on a verse that is *not* so listed is a mere portion of
        a single verse (for example a scholarly "8:1a"); it shares the base
        verse's ordinal, 0, so that it is not mistaken for an inserted verse.

        Args:
            book: The book ID (using Paratext three-letter codes)
            chapter: The chapter number
            verse: The verse number
            subverse: The subverse string ("" for the base verse)

        Returns:
            The subverse's ordinal within the verse: 0 for the base verse, or for
            a portion of a verse that has no inserted verses.

        """
        if not subverse:
            return 0
        if book == "PSAS":  # plural of PSA
            book = "PSA"
        parts = self._partial_verses.get((book, chapter, verse))
        if parts is None:
            return 0
        return parts.get(subverse, 0)

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

        A subverse letter can mean either a deuterocanonical verse inserted
        into a chapter (represented in the versification's mapping data) or a
        portion of a verse such as a line of a Psalm (never in the mapping
        data). An exact subverse match is treated as the former. Otherwise the
        base verse is mapped: a portion subverse is carried through a 1:1
        mapping and discarded across a 1:N or N:1 mapping.

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

        idx = 1 if end else 0
        org_loc, one_to_one = _map_stage(
            self._map_to_org, self._multi_to_org, (book, chapter, verse, subverse), idx
        )
        result, stage_one_to_one = _map_stage(
            target._map_from_org, target._multi_from_org, org_loc, idx
        )
        if not (one_to_one and stage_one_to_one):
            result = (result[0], result[1], result[2], "")

        if target.last_verse(result[0], result[1]) < result[2]:
            return None
        return result
