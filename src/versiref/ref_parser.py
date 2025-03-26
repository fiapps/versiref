"""
Bible reference parsing for versiref.

This module provides the RefParser class for parsing Bible references from strings.
"""

from typing import Dict, List, Optional, Tuple

import pyparsing as pp
from pyparsing import common

from versiref.bible_ref import SimpleBibleRef, VerseRange
from versiref.style import Style
from versiref.versification import Versification


class RefParser:
    """
    Parser for Bible references.

    RefParser uses pyparsing to build a parser that recognizes Bible references
    according to a given style. It can parse a string to produce a SimpleBibleRef
    instance.
    """

    def __init__(self, style: Style, versification: Versification):
        """
        Initialize a RefParser with a style and versification.

        Args:
            style: The Style to use for parsing
            versification: The Versification to use for determining single-chapter books
        """
        self.style = style
        self.versification = versification
        
        # Build the parser
        self._build_parser()

    def _build_parser(self):
        """Build the pyparsing parser based on the style and versification."""
        # Define basic elements
        book = pp.one_of(list(self.style.recognized_names.keys()))
        chapter = common.integer
        verse = common.integer
        subverse = pp.Word(pp.alphas.lower(), max=2).set_parse_action(lambda t: t[0] if t else "")
        
        # Optional subverse
        subverse = subverse.copy().set_parse_action(lambda t: t[0] if t else "")
        
        # Single verse reference: book chapter:verse[subverse]
        single_verse = (
            book.copy().set_results_name("book")
            + chapter.copy().set_results_name("chapter")
            + pp.Suppress(self.style.chapter_verse_separator)
            + verse.copy().set_results_name("verse")
            + subverse.copy().set_results_name("subverse", default="")
        )
        
        # For single-chapter books: book verse[subverse]
        single_chapter_verse = (
            book.copy().set_results_name("book")
            + verse.copy().set_results_name("verse")
            + subverse.copy().set_results_name("subverse", default="")
        )
        
        # Combine the parsers
        self.simple_ref_parser = single_verse | single_chapter_verse
        
    def parse_simple(self, text: str) -> Optional[SimpleBibleRef]:
        """
        Parse a string to produce a SimpleBibleRef.
        
        This method attempts to parse the entire string as a single Bible reference.
        
        Args:
            text: The string to parse
            
        Returns:
            A SimpleBibleRef instance, or None if parsing fails
        """
        try:
            # Try to parse the text
            result = self.simple_ref_parser.parse_string(text, parse_all=True)
            
            # Get the book ID from the recognized name
            book_name = result.book
            book_id = self.style.recognized_names.get(book_name)
            
            if not book_id:
                return None
                
            # Determine if this is a single-chapter book reference
            is_single_chapter_book = False
            if "chapter" not in result:
                # This is a reference to a verse in a single-chapter book
                is_single_chapter_book = True
                chapter = 1  # Single-chapter books have chapter 1
            else:
                chapter = int(result.chapter)
                
            # Get the verse and subverse
            verse = int(result.verse)
            subverse = result.subverse if hasattr(result, "subverse") else ""
            
            # Create a VerseRange for the single verse
            verse_range = VerseRange(
                start_chapter=chapter,
                start_verse=verse,
                start_sub_verse=subverse,
                end_chapter=chapter,
                end_verse=verse,
                end_sub_verse=subverse,
                original_text=text
            )
            
            # Create and return the SimpleBibleRef
            return SimpleBibleRef(
                book_id=book_id,
                ranges=[verse_range],
                original_text=text
            )
            
        except pp.ParseException:
            # Parsing failed
            return None
