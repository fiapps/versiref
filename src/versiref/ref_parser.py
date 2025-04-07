"""
Bible reference parsing for versiref.

This module provides the RefParser class for parsing Bible references from strings.

We don't call pp.ParserElement.enablePackrat() because it made parsing slower.
"""

from typing import List, Optional

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

    def __init__(
        self, style: Style, versification: Versification, strict: bool = False
    ):
        """
        Initialize a RefParser with a style and versification.

        Args:
            style: The Style to use for parsing
            versification: The Versification to use for determining single-chapter books
            strict: If True, follow the style more closely.

        Non-strict parsers currently recognize as range separators hyphens, en
        dashes, and the style's range separator if it differs from these.
        """
        self.style = style
        self.versification = versification
        self.strict = strict

        # Build the parser
        self._build_parser()

    def _build_parser(self):
        """Build the pyparsing parser based on the style and versification."""
        # Define basic elements
        book = pp.one_of(list(self.style.recognized_names.keys()))
        # Parse name to book ID.
        book.set_parse_action(lambda t: self.style.recognized_names[t[0]])
        chapter = common.integer
        verse = common.integer
        subverse = pp.Word(pp.alphas.lower(), max=2).leave_whitespace() + pp.WordEnd(
            pp.alphas.lower()
        )
        optional_subverse = pp.Opt(subverse.copy()).set_parse_action(
            lambda t: t[0] if t else ""
        )
        subverse.set_parse_action(lambda t: t[0] if t else "")
        if self.strict:
            range_separator = pp.Suppress(self.style.range_separator)
        else:
            range_separators = ["-", "\N{EN DASH}"]
            if self.style.range_separator not in range_separators:
                range_separators.append(self.style.range_separator)
            range_separator = pp.Suppress(pp.one_of(range_separators))
        # Empty marker to record location
        location_marker = pp.Empty().set_parse_action(lambda s, loc, t: loc)

        # For now, we only parse ranges of a single verse.
        verse_range = (
            verse.copy().set_results_name("start_verse")
            + optional_subverse.set_results_name("start_subverse")
            + pp.Opt(
                pp.Literal(self.style.following_verses).set_name("following_verses")
                | pp.Literal(self.style.following_verse).set_name("following_verse")
                | (
                    range_separator
                    + (
                        # Either a full chapter:verse reference
                        (
                            pp.Opt(
                                chapter.copy().set_results_name("end_chapter")
                                + self.style.chapter_verse_separator
                            )
                            + verse.copy().set_results_name("end_verse")
                            + optional_subverse.copy().set_results_name("end_subverse")
                        )
                        # Or just a subverse of the same verse
                        | subverse.copy().set_results_name("end_subverse")
                    )
                )
            )
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_verse_range)

        verse_ranges = pp.DelimitedList(
            verse_range, delim=pp.Suppress(Style.verse_range_separator.strip())
        ).set_results_name("verse_ranges")

        chapter_range = (
            chapter.copy().set_results_name("start_chapter")
            + pp.Suppress(self.style.chapter_verse_separator)
            + location_marker.copy().set_results_name("verse_ranges_location")
            + verse_ranges
        ).set_parse_action(self._make_chapter_range)

        chapter_ranges = pp.DelimitedList(
            chapter_range, delim=pp.Suppress(self.style.chapter_separator.strip())
        ).set_results_name("chapter_ranges")

        book_chapter_verse_ranges = (
            book.copy().set_results_name("book")
            + location_marker.copy().set_results_name("chapter_ranges_location")
            + chapter_ranges
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_simple_ref)

        # The chapter can be omitted for single-chapter (sc) books
        sc_books = [
            name
            for name, id in self.style.recognized_names.items()
            if self.versification.is_single_chapter(id)
        ]
        sc_book = pp.one_of(sc_books).set_results_name("book")
        sc_book.set_parse_action(lambda t: self.style.recognized_names[t[0]])

        sc_verse_range = (
            verse.copy().set_results_name("start_verse")
            + optional_subverse.copy().set_results_name("start_subverse")
            + pp.Opt(
                pp.Literal(self.style.following_verses).set_name("following_verses")
                | pp.Literal(self.style.following_verse).set_name("following_verse")
                | (
                    range_separator
                    + (
                        (
                            verse.copy().set_results_name("end_verse")
                            + optional_subverse.copy().set_results_name("end_subverse")
                        )
                        | subverse.copy().set_results_name("end_subverse")
                    )
                )
            )
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_sc_verse_range)

        sc_verse_ranges = pp.DelimitedList(
            sc_verse_range, delim=pp.Suppress(Style.verse_range_separator.strip())
        ).set_results_name("chapter_ranges")

        sc_book_verse_ranges = (
            sc_book
            + location_marker.copy().set_results_name("chapter_ranges_location")
            + sc_verse_ranges
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_simple_ref)

        # Try the parser with longer matches first, lest Jude 1:5 parse as Jude 1.
        self.simple_ref_parser = book_chapter_verse_ranges | sc_book_verse_ranges

    def _make_verse_range(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> VerseRange:
        """
        Create a VerseRange from parsed tokens.

        Chapter numbers that cannot be determined locally are set to -1.
        This is a parse action for use with pyparsing.

        Returns:
            A VerseRange instance based on the parsed tokens
        """
        start_chapter = tokens.get("start_chapter", -1)
        start_verse = tokens.start_verse
        start_subverse = tokens.start_subverse
        # Handle following_verse(s) mis-parsed as subverse.
        if "following_verse" in tokens:
            has_following_verse = True
        elif start_subverse == self.style.following_verse and "end_verse" not in tokens:
            start_subverse = ""
            has_following_verse = True
        else:
            has_following_verse = False
        if "following_verses" in tokens:
            has_following_verses = True
        elif (
            start_subverse == self.style.following_verses and "end_verse" not in tokens
        ):
            start_subverse = ""
            has_following_verses = True
        else:
            has_following_verses = False
        # Now set end based on type of range.
        if has_following_verse or has_following_verses:
            end_chapter = start_chapter
            if has_following_verse:
                end_verse = start_verse + 1
            else:
                end_verse = -1
            end_subverse = ""
        else:
            end_chapter = tokens.get("end_chapter", start_chapter)
            end_verse = tokens.get("end_verse", start_verse)
            end_subverse = tokens.get("end_subverse", start_subverse)
        end_location = tokens.get("end_location", -1)
        range_original_text = original_text[loc:end_location].strip()
        return VerseRange(
            start_chapter=start_chapter,
            start_verse=start_verse,
            start_subverse=start_subverse,
            end_chapter=end_chapter,
            end_verse=end_verse,
            end_subverse=end_subverse,
            original_text=range_original_text,
        )

    @staticmethod
    def _make_chapter_range(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> List[VerseRange]:
        """
        Set the chapter for the verse ranges.

        Here we supply chapter numbers that cannot be determined locally.
        This is a parse action for use with pyparsing.
        """
        this_chapter = tokens.start_chapter
        verse_ranges = tokens.verse_ranges
        for range in verse_ranges:
            # Set the chapter for each verse range
            range.start_chapter = this_chapter
            if range.end_chapter < 0:
                range.end_chapter = this_chapter
            else:
                this_chapter = range.end_chapter
        if verse_ranges:
            # Expand the original text for the first verse range to include the
            # chapter number. Why do we need to use find()? Because there could
            # be whitespace after verse_ranges_location.
            verse_ranges_location = tokens.get("verse_ranges_location", loc)
            range_0_start = original_text.find(
                verse_ranges[0].original_text, verse_ranges_location
            )
            verse_ranges[0].original_text = original_text[
                loc : range_0_start + len(verse_ranges[0].original_text)
            ]
        return verse_ranges

    def _make_sc_verse_range(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> VerseRange:
        """
        Create a VerseRange from parsed tokens.

        This is for a single-chapter book.
        This is a parse action for use with pyparsing.

        Returns:
            A VerseRange instance based on the parsed tokens
        """
        start_chapter = 1
        start_verse = tokens.start_verse
        start_subverse = tokens.start_subverse
        end_chapter = 1
        # Handle following_verse(s) mis-parsed as subverse.
        if "following_verse" in tokens:
            has_following_verse = True
        elif start_subverse == self.style.following_verse and "end_verse" not in tokens:
            start_subverse = ""
            has_following_verse = True
        else:
            has_following_verse = False
        if "following_verses" in tokens:
            has_following_verses = True
        elif (
            start_subverse == self.style.following_verses and "end_verse" not in tokens
        ):
            start_subverse = ""
            has_following_verses = True
        else:
            has_following_verses = False
        # Now set end based on type of range.
        if has_following_verse or has_following_verses:
            if has_following_verse:
                end_verse = start_verse + 1
            else:
                end_verse = -1
            end_subverse = ""
        else:
            end_verse = tokens.get("end_verse", start_verse)
            end_subverse = tokens.get("end_subverse", start_subverse)
        end_location = tokens.get("end_location", -1)
        range_original_text = original_text[loc:end_location].strip()
        return VerseRange(
            start_chapter=start_chapter,
            start_verse=start_verse,
            start_subverse=start_subverse,
            end_chapter=end_chapter,
            end_verse=end_verse,
            end_subverse=end_subverse,
            original_text=range_original_text,
        )

    @staticmethod
    def _make_simple_ref(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> SimpleBibleRef:
        """
        Create a SimpleBibleRef from parsed tokens.

        This is a parse action for use with pyparsing.

        Returns:
            A SimpleBibleRef instance based on the parsed tokens
        """
        # Extract the book ID and verse ranges
        book_name = tokens.book
        verse_ranges = tokens.get("chapter_ranges", tokens.verse_ranges)
        if verse_ranges:
            # Expand the original text for the first verse range to include the
            # book name. Why do we need to use find()? Because there could
            # be whitespace after verse_ranges_location.
            chapter_ranges_location = tokens.get("chapter_ranges_location", loc)
            range_0_start = original_text.find(
                verse_ranges[0].original_text, chapter_ranges_location
            )
            verse_ranges[0].original_text = original_text[
                loc : range_0_start + len(verse_ranges[0].original_text)
            ]
        end_location = tokens.get("end_location", -1)
        ref_original_text = original_text[loc:end_location].strip()

        # Create a SimpleBibleRef with the parsed data
        return SimpleBibleRef(
            book_id=book_name,
            ranges=verse_ranges.as_list(),
            original_text=ref_original_text,
        )

    def parse_simple(self, text: str, silent: bool = True) -> Optional[SimpleBibleRef]:
        """
        Parse a string to produce a SimpleBibleRef.

        This method attempts to parse the entire string as a reference to a single book of the Bible.

        Args:
            text: The string to parse
            silent: If True, return None on failure instead of raising a pyparsing.ParseException

        Returns:
            A SimpleBibleRef instance, or None if parsing fails
        """
        try:
            # Try to parse the text
            result = self.simple_ref_parser.parse_string(text, parse_all=True)
            return result[0]

        except pp.ParseException as e:
            if silent:
                return None
            else:
                raise e
