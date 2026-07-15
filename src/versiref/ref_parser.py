"""Bible reference parsing for versiref.

This module provides the RefParser class for parsing Bible references from strings.

We don't call pp.ParserElement.enablePackrat() because it made parsing slower.
"""

from enum import Enum
from typing import Callable, Generator

import pyparsing as pp
from pyparsing import common

from versiref.bible_ref import BibleRef, SimpleBibleRef, VerseRange
from versiref.ref_style import RefStyle
from versiref.roman import roman_to_int
from versiref.versification import Versification


class Sensitivity(Enum):
    """Controls which references are reported when scanning text.

    Higher sensitivity means more matches, including more false-positive-prone
    ones like bare book names.
    """

    VERSE = "verse"
    CHAPTER = "chapter"
    BOOK = "book"


def _get_int(tokens: pp.ParseResults, name: str, default: int) -> int:
    """Get an integer from the parsed tokens in a type-safe manner."""
    if name in tokens:
        return int(tokens[name])
    else:
        return default


def _get_str(tokens: pp.ParseResults, name: str, default: str) -> str:
    """Get an integer from the parsed tokens in a type-safe manner."""
    if name in tokens:
        return str(tokens[name])
    else:
        return default


class RefParser:
    """Parser for Bible references.

    RefParser uses pyparsing to build a parser that recognizes Bible references
    according to a given style. It can parse a string to produce a SimpleBibleRef
    instance.
    """

    def __init__(
        self, style: RefStyle, versification: Versification, strict: bool = False
    ):
        """Initialize a RefParser with a style and versification.

        Args:
            style: The RefStyle to use for parsing
            versification: The Versification to use for determining single-chapter books
            strict: If True, follow the style more closely.

        Non-strict parsers currently recognize as range separators hyphens, en
        dashes, and the style's range separator if it differs from these.

        Raises:
            FileNotFoundError: If the style names a versification designator
                whose id does not correspond to a bundled versification.

        """
        self.style = style
        self.versification = versification
        self.strict = strict

        # Resolve each distinct versification id once, so aliases such as
        # "Vulg." and "Vulgate" -> "vulgata" load a single Versification.
        resolved: dict[str, Versification] = {}
        self._designator_versifications: dict[str, Versification] = {}
        for designator, vid in style.versification_identifiers.items():
            if vid not in resolved:
                resolved[vid] = Versification.named(vid)
            self._designator_versifications[designator] = resolved[vid]

        # Build the parser
        self._build_parser()

    def _build_parser(self) -> None:
        """Build the pyparsing parser based on the style and versification."""
        # Define basic elements
        book = pp.one_of(list(self.style.recognized_names.keys()))
        # Parse name to book ID.
        book.set_parse_action(lambda t: self.style.recognized_names[t[0]])
        # The lookahead keeps a Roman numeral from matching the start of a
        # longer word ("Cl" in "Clemens"); it counts the æ/œ ligatures common
        # in Latin text as word characters ("Cœna", "Lætitia").
        chapter: pp.ParserElement
        if self.style.chapter_number_style == "roman":
            chapter = pp.Regex(r"[CLXVI]+(?![0-9A-Za-zÆæŒœ])")
            chapter.set_parse_action(lambda t: roman_to_int(t[0]))
        elif self.style.chapter_number_style == "roman-lower":
            chapter = pp.Regex(r"[clxvi]+(?![0-9A-Za-zÆæŒœ])")
            chapter.set_parse_action(lambda t: roman_to_int(t[0]))
        else:
            chapter = common.integer
        verse = common.integer
        subverse = pp.Word(pp.alphas.lower(), max=2).leave_whitespace() + pp.WordEnd(
            pp.alphas.lower()
        )
        optional_subverse = pp.Opt(subverse.copy()).set_parse_action(
            lambda t: t[0] if t else ""
        )
        subverse.set_parse_action(lambda t: t[0] if t else "")
        # A reference never continues across a blank line. Without this check,
        # a citation-ending period followed by a footnote or paragraph number
        # would extend the reference ("Gen. XXII, 18.\n\n2" scanning as verses
        # 18 and 2). leave_whitespace makes the NotAny inspect the raw text on
        # either side of the separator instead of skipping past it.
        paragraph_boundary = pp.NotAny(
            pp.Regex(r"[^\S\n]*\n[^\S\n]*\n")
        ).leave_whitespace()

        def separator(literal: pp.ParserElement | str) -> pp.ParserElement:
            """Suppress a separator that must not sit next to a blank line."""
            return (
                paragraph_boundary.copy()
                + pp.Suppress(literal)
                + paragraph_boundary.copy()
            )

        if self.strict:
            range_separator = separator(self.style.range_separator)
        else:
            range_separators = ["-", "\N{EN DASH}"]
            if self.style.range_separator not in range_separators:
                range_separators.append(self.style.range_separator)
            range_separator = separator(pp.one_of(range_separators))
        # Empty marker to record location
        location_marker = pp.Empty().set_parse_action(lambda s, loc, t: loc)
        # A boundary that fails if the marker is glued to a longer word (e.g. the
        # "ff" in "ffoo"). leave_whitespace keeps the enclosing And from skipping
        # whitespace first and testing the next word instead of the character
        # right after the marker.
        word_boundary = pp.NotAny(pp.Char(pp.identbodychars)).leave_whitespace()

        # For now, we only parse ranges of a single verse.
        verse_range = (
            verse.copy().set_results_name("start_verse")
            + optional_subverse.set_results_name("start_subverse")
            + pp.Opt(
                (
                    (
                        pp.Literal(self.style.following_verses).set_results_name(
                            "following_verses"
                        )
                        | pp.Literal(self.style.following_verse).set_results_name(
                            "following_verse"
                        )
                    )
                    + word_boundary.copy()
                )
                | (
                    range_separator
                    + (
                        # Either a full chapter:verse reference
                        (
                            pp.Opt(
                                chapter.copy().set_results_name("end_chapter")
                                + separator(self.style.chapter_verse_separator.strip())
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
            verse_range, delim=separator(self.style.verse_range_separator.strip())
        ).set_results_name("verse_ranges")

        chapter_range = (
            chapter.copy().set_results_name("start_chapter")
            + separator(self.style.chapter_verse_separator.strip())
            + location_marker.copy().set_results_name("verse_ranges_location")
            + verse_ranges
        ).set_parse_action(self._make_chapter_range)

        chapter_ranges = pp.DelimitedList(
            chapter_range, delim=separator(self.style.chapter_separator.strip())
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
                (
                    (
                        pp.Literal(self.style.following_verses).set_results_name(
                            "following_verses"
                        )
                        | pp.Literal(self.style.following_verse).set_results_name(
                            "following_verse"
                        )
                    )
                    + word_boundary.copy()
                )
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
            sc_verse_range, delim=separator(self.style.verse_range_separator.strip())
        ).set_results_name("chapter_ranges")

        sc_book_verse_ranges = (
            sc_book
            + location_marker.copy().set_results_name("chapter_ranges_location")
            + sc_verse_ranges
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_simple_ref)

        # Whole-chapter references: "John 3", "John 3–5", "John 3; 5; 7"
        chapter_only_range = (
            chapter.copy().set_results_name("start_chapter")
            + pp.Opt(range_separator + chapter.copy().set_results_name("end_chapter"))
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_chapter_only_range)

        chapter_only_ranges = pp.DelimitedList(
            chapter_only_range, delim=separator(self.style.chapter_separator.strip())
        ).set_results_name("chapter_ranges")

        book_chapter_only_ranges = (
            book.copy().set_results_name("book")
            + location_marker.copy().set_results_name("chapter_ranges_location")
            + chapter_only_ranges
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_simple_ref)

        # Whole-book references: bare book name
        book_only = (
            book.copy().set_results_name("book")
            + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_whole_book_ref)

        # A leading word boundary keeps a book name from matching when it is
        # glued to the end of a longer word (e.g. the "Rom" in "CongrRom") while
        # scanning free text. It is a Unicode-aware negative look-behind for a
        # letter, so accented letters in non-ASCII book names count as letters;
        # start of string, whitespace, digits, and punctuation are all valid
        # boundaries. It is zero-width and suppressed, so it neither shifts the
        # match location nor adds a token. At string start (parse/validate) the
        # look-behind has nothing to reject, leaving those code paths unchanged.
        leading_word_boundary = pp.Suppress(pp.Regex(r"(?<![^\W\d_])"))

        # Try the parser with longer matches first, lest Jude 1:5 parse as
        # Jude 1 or "John 3:16" parse as "John 3".
        self.simple_ref_parser = leading_word_boundary + (
            book_chapter_verse_ranges
            | sc_book_verse_ranges
            | book_chapter_only_ranges
            | book_only
        )

        # A trailing versification designator (e.g. "Vulg.", "(LXX)"). one_of
        # escapes regex metacharacters and prefers longer matches, so "Vulgate"
        # wins over "Vulg.". The word boundary keeps "LXX" from matching inside a
        # longer word. The parse action resolves the designator to a Versification.
        if self._designator_versifications:
            # leave_whitespace on the boundary keeps the And from skipping past
            # the space after the designator and testing the next word instead.
            designator = (
                pp.one_of(list(self._designator_versifications.keys()))
                + pp.NotAny(pp.Char(pp.identbodychars)).leave_whitespace()
            )
            designator.set_parse_action(lambda t: self._designator_versifications[t[0]])
        else:
            designator = None

        # Now it's simple to build a parser for BibleRef. A designator at the end
        # of the whole reference applies to every book in it.
        bible_ref_body: pp.ParserElement = pp.DelimitedList(
            self.simple_ref_parser, separator(self.style.chapter_separator.strip())
        )
        if designator is not None:
            bible_ref_body = bible_ref_body + pp.Opt(
                designator.copy().set_results_name("versification_designator")
            )
        self.bible_ref_parser = (
            bible_ref_body + location_marker.copy().set_results_name("end_location")
        ).set_parse_action(self._make_bible_ref)

        # A SimpleBibleRef carries no versification, so parse_simple matches and
        # discards a trailing designator (parse_all then succeeds on the suffix).
        if designator is not None:
            self.simple_ref_parser_top = self.simple_ref_parser + pp.Opt(
                pp.Suppress(designator.copy())
            )
        else:
            self.simple_ref_parser_top = self.simple_ref_parser

    def _make_verse_range(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> VerseRange:
        """Create a VerseRange from parsed tokens.

        Chapter numbers that cannot be determined locally are set to -1.
        This is a parse action for use with pyparsing.

        Returns:
            A VerseRange instance based on the parsed tokens

        """
        start_chapter = _get_int(tokens, "start_chapter", -1)
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
            end_chapter = _get_int(tokens, "end_chapter", start_chapter)
            end_verse = _get_int(tokens, "end_verse", start_verse)
            end_subverse = _get_str(tokens, "end_subverse", start_subverse)
        end_location = _get_int(tokens, "end_location", -1)
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
    ) -> pp.ParseResults:
        """Set the chapter for the verse ranges.

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
            verse_ranges_location = _get_int(tokens, "verse_ranges_location", loc)
            range_0_start = original_text.find(
                verse_ranges[0].original_text, verse_ranges_location
            )
            verse_ranges[0].original_text = original_text[
                loc : range_0_start + len(verse_ranges[0].original_text)
            ]
        assert isinstance(verse_ranges, pp.ParseResults)
        return verse_ranges

    def _make_sc_verse_range(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> VerseRange:
        """Create a VerseRange from parsed tokens.

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
            end_verse = _get_int(tokens, "end_verse", start_verse)
            end_subverse = _get_str(tokens, "end_subverse", start_subverse)
        end_location = _get_int(tokens, "end_location", -1)
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
    def _make_chapter_only_range(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> VerseRange:
        """Create a whole-chapter VerseRange from parsed tokens.

        This is a parse action for use with pyparsing.

        Returns:
            A VerseRange with verse numbers set to -1 (whole chapters)

        """
        start_chapter = tokens.start_chapter
        end_chapter = _get_int(tokens, "end_chapter", start_chapter)
        end_location = _get_int(tokens, "end_location", -1)
        range_original_text = original_text[loc:end_location].strip()
        return VerseRange(
            start_chapter=start_chapter,
            start_verse=-1,
            start_subverse="",
            end_chapter=end_chapter,
            end_verse=-1,
            end_subverse="",
            original_text=range_original_text,
        )

    @staticmethod
    def _make_whole_book_ref(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> SimpleBibleRef:
        """Create a whole-book SimpleBibleRef from parsed tokens.

        This is a parse action for use with pyparsing.

        Returns:
            A SimpleBibleRef with no ranges (whole book)

        """
        book_name = tokens.book
        end_location = _get_int(tokens, "end_location", -1)
        ref_original_text = original_text[loc:end_location].strip()
        return SimpleBibleRef(
            book_id=book_name,
            ranges=[],
            original_text=ref_original_text,
        )

    @staticmethod
    def _make_simple_ref(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> SimpleBibleRef:
        """Create a SimpleBibleRef from parsed tokens.

        This is a parse action for use with pyparsing.

        Returns:
            A SimpleBibleRef instance based on the parsed tokens

        """
        # Extract the book ID and verse ranges
        book_name = tokens.book
        if "chapter_ranges" in tokens:
            verse_ranges = tokens.chapter_ranges
        else:
            verse_ranges = tokens.verse_ranges
        if verse_ranges:
            # Expand the original text for the first verse range to include the
            # book name. Why do we need to use find()? Because there could
            # be whitespace after verse_ranges_location.
            chapter_ranges_location = _get_int(tokens, "chapter_ranges_location", loc)
            range_0_start = original_text.find(
                verse_ranges[0].original_text, chapter_ranges_location
            )
            verse_ranges[0].original_text = original_text[
                loc : range_0_start + len(verse_ranges[0].original_text)
            ]
        end_location = _get_int(tokens, "end_location", -1)
        ref_original_text = original_text[loc:end_location].strip()

        # Create a SimpleBibleRef with the parsed data
        return SimpleBibleRef(
            book_id=book_name,
            ranges=verse_ranges.as_list(),
            original_text=ref_original_text,
        )

    def _make_bible_ref(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> BibleRef:
        """Create a BibleRef from parsed tokens.

        This is a parse action for use with pyparsing.

        Returns:
            A BibleRef instance based on the parsed tokens

        """
        end_location = _get_int(tokens, "end_location", -1)
        # One token (end_location) is not a SimpleBibleRef
        simple_refs = [r for r in tokens if isinstance(r, SimpleBibleRef)]
        ref_original_text = original_text[loc:end_location].strip()

        # A trailing designator overrides the parser's default versification.
        versification = self.versification
        if "versification_designator" in tokens:
            designated = tokens["versification_designator"]
            assert isinstance(designated, Versification)
            versification = designated

        # Create a BibleRef with the parsed data
        return BibleRef(
            versification=versification,
            simple_refs=simple_refs,
            original_text=ref_original_text,
        )

    def parse_simple(self, text: str, silent: bool = False) -> SimpleBibleRef | None:
        """Parse a string to produce a SimpleBibleRef.

        This method attempts to parse the entire string as a reference to a single book of the Bible.

        Args:
            text: The string to parse
            silent: If True, return None on failure instead of raising a pyparsing.ParseException

        Returns:
            A SimpleBibleRef instance, or None if silent=True and parsing fails

        """
        try:
            # Try to parse the text
            result = self.simple_ref_parser_top.parse_string(text, parse_all=True)
            ref = result[0]
            assert isinstance(ref, SimpleBibleRef)
            return ref

        except pp.ParseException as e:
            if silent:
                return None
            else:
                raise e

    def parse(self, text: str, silent: bool = False) -> BibleRef | None:
        """Parse a string to produce a BibleRef.

        This method attempts to parse the entire string as a reference to one or more books of the Bible.

        Args:
            text: The string to parse
            silent: If True, return None on failure instead of raising a pyparsing.ParseException

        Returns:
            A BibleRef instance, or None if silent=True and parsing fails

        """
        try:
            # Try to parse the text
            result = self.bible_ref_parser.parse_string(text, parse_all=True)
            ref = result[0]
            assert isinstance(ref, BibleRef)
            return ref

        except pp.ParseException as e:
            if silent:
                return None
            else:
                raise e

    @staticmethod
    def _passes_sensitivity_simple(
        ref: SimpleBibleRef, sensitivity: "Sensitivity"
    ) -> bool:
        """Check if a SimpleBibleRef passes the sensitivity filter."""
        if sensitivity == Sensitivity.BOOK:
            return True
        if sensitivity == Sensitivity.CHAPTER:
            return not ref.is_whole_book()
        return not ref.is_whole_chapters()

    @staticmethod
    def _passes_sensitivity(ref: BibleRef, sensitivity: "Sensitivity") -> bool:
        """Check if a BibleRef passes the sensitivity filter."""
        if sensitivity == Sensitivity.BOOK:
            return True
        if sensitivity == Sensitivity.CHAPTER:
            return not ref.is_whole_books()
        return not ref.is_whole_chapters()

    def scan_string_simple(
        self,
        text: str,
        as_ranges: bool = False,
        sensitivity: "Sensitivity" = Sensitivity.VERSE,
    ) -> Generator[tuple["SimpleBibleRef", int, int], None, None]:
        """Scan a string for SimpleBibleRefs.

        This method scans the entire string for references to a single book of the Bible.

        Args:
            text: The string to scan
            as_ranges: If True, yield a SimpleBibleRef for each verse range
            sensitivity: Controls which references are reported. VERSE (default)
                skips whole-chapter and whole-book references. CHAPTER also
                reports whole-chapter references. BOOK reports everything.

        Yields:
            A reference and the start and end of its location in text.
            (ref: SimpleBibleRef, start: int, end: int)

        """
        for tokens, start, end in self.simple_ref_parser.scan_string(text):
            ref = tokens[0]
            assert isinstance(ref, SimpleBibleRef)
            if as_ranges:
                next_start = start
                for range_ref in ref.range_refs():
                    if not self._passes_sensitivity_simple(range_ref, sensitivity):
                        continue
                    # Use the original text to find the start and end.
                    assert range_ref.original_text is not None
                    range_start = text.find(range_ref.original_text, next_start)
                    assert range_start >= 0
                    next_start = range_start + len(range_ref.original_text)
                    yield (range_ref, range_start, next_start)
                # Whole-book refs have no ranges; yield as-is if allowed.
                if ref.is_whole_book() and self._passes_sensitivity_simple(
                    ref, sensitivity
                ):
                    assert ref.original_text is not None
                    yield (ref, start, start + len(ref.original_text))
            else:
                if not self._passes_sensitivity_simple(ref, sensitivity):
                    continue
                assert ref.original_text is not None
                yield (ref, start, start + len(ref.original_text))

    def scan_string(
        self,
        text: str,
        as_ranges: bool = False,
        sensitivity: "Sensitivity" = Sensitivity.VERSE,
    ) -> Generator[tuple["BibleRef", int, int], None, None]:
        """Scan a string for BibleRefs.

        This method scans the entire string for references to one or more books of the Bible.

        Args:
            text: The string to scan
            as_ranges: If True, yield a BibleRef for each verse range
            sensitivity: Controls which references are reported. VERSE (default)
                skips whole-chapter and whole-book references. CHAPTER also
                reports whole-chapter references. BOOK reports everything.

        Yields:
            A reference and the start and end of its location in text.
            (ref: BibleRef, start: int, end: int)

        """
        for tokens, start, end in self.bible_ref_parser.scan_string(text):
            ref = tokens[0]
            assert isinstance(ref, BibleRef)
            if as_ranges:
                next_start = start
                for range_ref in ref.range_refs():
                    if not self._passes_sensitivity(range_ref, sensitivity):
                        continue
                    # Use the original text to find the start and end.
                    assert range_ref.original_text is not None
                    range_start = text.find(range_ref.original_text, next_start)
                    assert range_start >= 0
                    next_start = range_start + len(range_ref.original_text)
                    yield (range_ref, range_start, next_start)
                # Whole-book refs have no ranges; yield as-is if allowed.
                if ref.is_whole_books() and self._passes_sensitivity(ref, sensitivity):
                    assert ref.original_text is not None
                    yield (ref, start, start + len(ref.original_text))
            else:
                if not self._passes_sensitivity(ref, sensitivity):
                    continue
                assert ref.original_text is not None
                yield (ref, start, start + len(ref.original_text))

    def sub_refs_simple(
        self,
        text: str,
        callback: Callable[[SimpleBibleRef], str | None],
        as_ranges: bool = False,
        sensitivity: "Sensitivity" = Sensitivity.VERSE,
    ) -> str:
        """Substitute SimpleBibleRefs in a string.

        This method scans the entire string for references to a single book of the Bible and
        applies a callback function to each reference.

        Args:
            text: The string to scan
            callback: A function that takes a SimpleBibleRef and returns a string or None
                Unless None is returned, the reference is replaced with the returned
                value.
            as_ranges: If True, yield a SimpleBibleRef for each verse range
            sensitivity: Controls which references are reported. VERSE (default)
                skips whole-chapter and whole-book references. CHAPTER also
                reports whole-chapter references. BOOK reports everything.

        Returns:
            The modified string

        """
        result = []
        last_end = 0
        for ref, start, end in self.scan_string_simple(text, as_ranges, sensitivity):
            replacement = callback(ref)
            if replacement is not None:
                result.append(text[last_end:start])
                result.append(replacement)
                last_end = end
        result.append(text[last_end:])
        return "".join(result)

    def sub_refs(
        self,
        text: str,
        callback: Callable[[BibleRef], str | None],
        as_ranges: bool = False,
        sensitivity: "Sensitivity" = Sensitivity.VERSE,
    ) -> str:
        """Substitute BibleRefs in a string.

        This method scans the entire string for references to one or more books of the Bible and
        applies a callback function to each reference.

        Args:
            text: The string to scan
            callback: A function that takes a BibleRef and returns a string or None
                Unless None is returned, the reference is replaced with the returned
                value.
            as_ranges: If True, yield a BibleRef for each verse range
            sensitivity: Controls which references are reported. VERSE (default)
                skips whole-chapter and whole-book references. CHAPTER also
                reports whole-chapter references. BOOK reports everything.

        Returns:
            The modified string

        """
        result = []
        last_end = 0
        for ref, start, end in self.scan_string(text, as_ranges, sensitivity):
            replacement = callback(ref)
            if replacement is not None:
                result.append(text[last_end:start])
                result.append(replacement)
                last_end = end
        result.append(text[last_end:])
        return "".join(result)
