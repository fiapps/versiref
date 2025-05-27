"""Versification class for handling Bible chapter and verse divisions."""

import json
from dataclasses import dataclass, field
from importlib import resources
from typing import Optional


@dataclass
class Versification:
    """Represents a way of dividing the text of the Bible into chapters and verses.

    Versifications are defined by JSON data that is loaded from a file when an instance is created.
    The class provides methods to query information about the versification, such as the last verse
    of a given chapter in a given book.
    """

    max_verses: dict[str, list[int]] = field(default_factory=dict)
    identifier: Optional[str] = None

    @classmethod
    def from_file(
        cls, file_path: str, identifier: Optional[str] = None
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
        if "maxVerses" in data:
            # Convert string verse counts to integers
            max_verses = {}
            for book, verses in data["maxVerses"].items():
                max_verses[book] = [int(v) for v in verses]
            return cls(max_verses, identifier)
        else:
            raise ValueError("Versification file does not match schema")

    @classmethod
    def named(cls, identifier: str) -> "Versification":
        """Create an instance of a standard versification.

        Constructs an instance by loading JSON data from the package's data
        directory.

        Args:
            identifier: Standard versification identifier (e.g., "org", "eng",
            "LXX", "Vulgata")
                This is converted to lowercase to find the file to load.

        Raises:
            FileNotFoundError: If the named file doesn't exist
            json.JSONDecodeError: if the file contains invalid JSON ValueError: If the JSON is not in the expected format
            The latter two represent internal errors in the package.

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
