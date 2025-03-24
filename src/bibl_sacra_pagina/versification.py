import json
import os
from pathlib import Path
from typing import Dict, Optional


class Versification:
    """
    Represents a way of dividing the text of the Bible into chapters and verses.
    
    Versifications are defined by JSON data that is loaded from a file when an instance is created.
    The class provides methods to query information about the versification, such as the last verse
    of a given chapter in a given book.
    """
    
    def __init__(self, data: Optional[Dict] = None, file_path: Optional[str] = None):
        """
        Initialize a Versification instance.
        
        Args:
            data: Optional dictionary containing versification data
            file_path: Optional path to a JSON file containing versification data
        
        If neither data nor file_path is provided, a trivial implementation is used.
        """
        self.max_verses = {}
        
        if data:
            self._load_from_data(data)
        elif file_path:
            self._load_from_file(file_path)
    
    def _load_from_file(self, file_path: str) -> None:
        """Load versification data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._load_from_data(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # If file loading fails, we'll use the trivial implementation
            print(f"Warning: Failed to load versification data from {file_path}: {e}")
    
    def _load_from_data(self, data: Dict) -> None:
        """Load versification data from a dictionary."""
        if "maxVerses" in data:
            self.max_verses = data["maxVerses"]
    
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
        
        # Convert chapter to string since JSON keys are strings
        chapter_str = str(chapter)
        
        # Check if the chapter exists in the book
        if chapter_str not in self.max_verses[book]:
            return -1
        
        return self.max_verses[book][chapter_str]
