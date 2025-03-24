import json
import os
from dataclasses import dataclass, field
from importlib import resources
from typing import Dict, List, Optional


@dataclass
class Versification:
    """
    Represents a way of dividing the text of the Bible into chapters and verses.
    
    Versifications are defined by JSON data that is loaded from a file when an instance is created.
    The class provides methods to query information about the versification, such as the last verse
    of a given chapter in a given book.
    """
    
    max_verses: Dict[str, List[int]] = field(default_factory=dict)
    identifier: str = None
    
    @classmethod
    def from_file(cls, file_path: str, identifier: str = None) -> "Versification":
        """Create an instance from a JSON file.

        Args:
            file_path: path to a JSON file containing an object with maxVerses
            identifier: identifier to store in the constructed Versififaction
        This can throw FileNotFoundError, json.JSONDecodeError, ValueError
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "maxVerses" in data:
                return cls(data["maxVerses"], identifier)
            else:
                # Is there a better way to report a malformed JSON file?
                raise ValueError()
    
    @classmethod
    def standard_versification(cls, identifier: str) -> Optional["Versification"]:
        """
        Create an instance of a standard versification.
        
        Constructs an instance by loading JSON data or returns None if the
        identifier is unknown.
        Args:
            identifier: Standard versification identifier (e.g., "org", "eng",
            "LXX", "Vul")
                This is converted to lowercase to find the file to load.
        
        Standard versifications are loaded from JSON files in the package's data
        directory.
        """
        filename = f"{identifier.lower()}.json"
        
        path = resources.files("bibl_sacra_pagina").joinpath("data", "versifications", filename)
        if os.path.exists(path):
            return cls.from_file(path, identifier)
        else:
            return None
    
    def last_verse(self, book: str, chapter: int) -> int:
        """
        Return the number of the last verse of the given chapter of the given book.
        
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
        if book not in self.max_verses:
            return -1
        
        # Check if the chapter exists in the book
        if chapter < 0 or chapter > len(self.max_verses[book]):
            return -1
        
        return self.max_verses[book][chapter-1]
