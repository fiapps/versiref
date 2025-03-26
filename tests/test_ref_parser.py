"""
Tests for the ref_parser module.
"""

import pytest
from versiref.ref_parser import RefParser
from versiref.style import Style
from versiref.versification import Versification


def test_parse_simple_verse():
    """Test parsing a simple verse reference."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a versification
    versification = Versification.standard_versification("eng")
    
    # Create a parser
    parser = RefParser(style, versification)
    
    # Parse a simple reference: "Gen 1:1"
    ref = parser.parse_simple("Gen 1:1")
    
    assert ref is not None
    assert ref.book_id == "GEN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 1
    assert ref.ranges[0].start_verse == 1
    assert ref.ranges[0].start_sub_verse == ""
    assert ref.ranges[0].end_chapter == 1
    assert ref.ranges[0].end_verse == 1
    assert ref.ranges[0].end_sub_verse == ""
    assert ref.original_text == "Gen 1:1"


def test_parse_verse_with_subverse():
    """Test parsing a verse reference with a subverse."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a versification
    versification = Versification.standard_versification("eng")
    
    # Create a parser
    parser = RefParser(style, versification)
    
    # Parse a reference with a subverse: "John 3:16b"
    ref = parser.parse_simple("John 3:16b")
    
    assert ref is not None
    assert ref.book_id == "JHN"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 3
    assert ref.ranges[0].start_verse == 16
    assert ref.ranges[0].start_sub_verse == "b"
    assert ref.ranges[0].end_chapter == 3
    assert ref.ranges[0].end_verse == 16
    assert ref.ranges[0].end_sub_verse == "b"
    assert ref.original_text == "John 3:16b"


def test_parse_single_chapter_book():
    """Test parsing a reference to a verse in a single-chapter book."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a versification with Jude as a single-chapter book
    versification = Versification.standard_versification("eng")
    
    # Create a parser
    parser = RefParser(style, versification)
    
    # Parse a reference to a verse in Jude: "Jude 5"
    ref = parser.parse_simple("Jude 5")
    
    assert ref is not None
    assert ref.book_id == "JUD"
    assert len(ref.ranges) == 1
    assert ref.ranges[0].start_chapter == 1  # Single-chapter books have chapter 1
    assert ref.ranges[0].start_verse == 5
    assert ref.ranges[0].end_chapter == 1
    assert ref.ranges[0].end_verse == 5
    assert ref.original_text == "Jude 5"


def test_parse_nonexistent_reference():
    """Test parsing a string that is not a Bible reference."""
    # Create a style
    names = Style.standard_names("en-sbl_abbreviations")
    style = Style(names=names)
    
    # Create a versification
    versification = Versification.standard_versification("eng")
    
    # Create a parser
    parser = RefParser(style, versification)
    
    # Try to parse a non-reference
    ref = parser.parse_simple("This is not a Bible reference")
    
    assert ref is None
