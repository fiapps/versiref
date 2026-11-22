"""Bible reference parsing for versiref.

This module provides the RefParser class for parsing Bible references from strings.

We don't call pp.ParserElement.enablePackrat() because it made parsing slower.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum

import pyparsing as pp

from versiref.bible_ref import BibleRef, RefPoint, VerseRange
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
    """Get a string from the parsed tokens in a type-safe manner."""
    if name in tokens:
        return str(tokens[name])
    else:
        return default


def _opt_int(tokens: pp.ParseResults, name: str) -> int | None:
    """Get an integer from the parsed tokens, or None if it is absent."""
    return int(tokens[name]) if name in tokens else None


@dataclass
class _Draft:
    """A verse range as the grammar finds it, before its context is known.

    A chapter left as None is supplied from what precedes the range, and
    the book from the name that begins the reference.
    """

    start_loc: int
    end_loc: int
    whole_book: bool = False
    chapter: int | None = None
    verse: int | None = None
    subverse: str = ""
    following: str = ""
    has_end: bool = False
    end_book: str | None = None
    end_chapter: int | None = None
    end_verse: int | None = None
    end_subverse: str = ""


# What may separate the parts of a reference: pyparsing's defaults plus the
# no-break, thin and narrow no-break spaces that typeset text puts between a
# book name and its chapter or after a separator.
_WHITESPACE_CHARS = " \t\n\r\u00a0\u2009\u202f"

# Whitespace inside a book name such as "1 Kgs": any horizontal whitespace,
# wrapping across at most one line break (never a blank line).
_NAME_SPACE = r"(?:[^\S\n]+(?:\n[^\S\n]*)?|\n[^\S\n]*)"

# Fails when a letter follows, so that a name ending in a letter does not match
# the start of a longer word ("Mark" in "Marketing"). Unicode-aware, like the
# leading boundary in _build_parser.
_NO_LETTER_AHEAD = r"(?![^\W\d_])"

# The most chapters a book is taken to have when the versification names no
# books: the Psalms, counting Psalm 151.
_MOST_CHAPTERS = 151


def _book_element(name_to_id: dict[str, str]) -> pp.ParserElement:
    """Build an element that matches a book name and yields its book ID.

    Args:
        name_to_id: Maps each name or abbreviation to match to a book ID.

    Returns:
        A parser element that prefers longer names and matches nothing if
        there are no names.

    """
    if not name_to_id:
        return pp.NoMatch()
    ids = {" ".join(name.split()): book_id for name, book_id in name_to_id.items()}
    alternatives = [
        _NAME_SPACE.join(re.escape(word) for word in name.split(" "))
        + (_NO_LETTER_AHEAD if name[-1].isalpha() else "")
        for name in sorted(ids, key=len, reverse=True)
    ]
    element = pp.Regex("|".join(alternatives))
    element.set_parse_action(lambda t: ids[" ".join(str(t[0]).split())])
    return element


def _extend_whitespace(element: pp.ParserElement) -> None:
    """Make an element and all it contains skip :data:`_WHITESPACE_CHARS`.

    pyparsing has no per-grammar whitespace setting short of its global
    default, which would change every other grammar in the process.
    """
    seen: set[int] = set()
    pending = [element]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if current.skipWhitespace:
            current.set_whitespace_chars(_WHITESPACE_CHARS)
        pending.extend(getattr(current, "exprs", []))
        inner = getattr(current, "expr", None)
        if inner is not None:
            pending.append(inner)


class RefParser:
    """Parser for Bible references.

    RefParser uses pyparsing to build a parser that recognizes Bible references
    according to a given style. It can parse a string to produce a BibleRef
    instance, or scan a longer text for the references in it.
    """

    def __init__(
        self, style: RefStyle, versification: Versification, strict: bool = False
    ):
        """Initialize a RefParser with a style and versification.

        Args:
            style: The RefStyle to use for parsing
            versification: The Versification of the references. It decides
                which books have a single chapter, and which have lettered
                chapters (the NABRE's Esther A–F) and where they stand.
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

        self._designator_versifications: dict[str, Versification] = {
            designator: Versification.named(vid)
            for designator, vid in style.versification_identifiers.items()
        }

        # Build the parser
        self._build_parser()

    def _build_parser(self) -> None:
        """Build the pyparsing parser based on the style and versification."""
        # "PSAS" marks a plural name for the Psalms; the book is PSA.
        names = {
            name: "PSA" if book_id == "PSAS" else book_id
            for name, book_id in self.style.recognized_names.items()
        }
        book = _book_element(names)
        # The chapter can be omitted for single-chapter (sc) books
        sc_book = _book_element(
            {
                name: book_id
                for name, book_id in names.items()
                if self.versification.is_single_chapter(book_id)
            }
        )
        # A number that begins the name of a numbered book ("1 John") is not a
        # chapter or verse of the book before it.
        not_a_book = pp.NotAny(book)
        most_chapters = max(
            (len(chapters) for chapters in self.versification.max_verses.values()),
            default=_MOST_CHAPTERS,
        )
        if self.versification.includes("PS2") or any(
            versification.includes("PS2")
            for versification in self._designator_versifications.values()
        ):
            most_chapters = max(most_chapters, 151)
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
            chapter = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        verse = pp.Word(pp.nums).set_parse_action(lambda t: int(t[0]))
        # At the end of a range the number is taken for the book's only if a
        # chapter or verse follows the name: "Luke 1–2 John the Baptist" is
        # Luke 1–2, though "Luke 1–2 John 3" is not.
        not_a_cited_book = pp.NotAny(book + (chapter | verse))
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
        chapter_verse_separator = self.style.chapter_verse_separator.strip()
        verse_range_separator = self.style.verse_range_separator.strip()
        chapter_separator = self.style.chapter_separator.strip()
        # Empty marker to record location
        location_marker = pp.Empty().set_parse_action(lambda s, loc, t: loc)
        end_location = location_marker.copy().set_results_name("end_location")
        # A boundary that fails if the marker is glued to a longer word (e.g. the
        # "ff" in "ffoo"). leave_whitespace keeps the enclosing And from skipping
        # whitespace first and testing the next word instead of the character
        # right after the marker.
        word_boundary = pp.NotAny(pp.Char(pp.identbodychars)).leave_whitespace()
        # Likewise for a chapter number that stands alone ("3" in "3rd").
        no_letter_after = pp.Regex(_NO_LETTER_AHEAD).leave_whitespace()

        following = (
            pp.Literal(self.style.following_verses).set_results_name("following_verses")
            | pp.Literal(self.style.following_verse).set_results_name("following_verse")
        ) + word_boundary.copy()

        # The end of a range that runs into another book, which must name a
        # chapter or verse there: "1 Sam 31:1–2 Sam 1:27", "Gen 50–Exod 2",
        # "2 John 12–3 John 4".
        other_book_end = (
            book.copy().set_results_name("end_book")
            + chapter.copy().set_results_name("end_chapter")
            + separator(chapter_verse_separator)
            + verse.copy().set_results_name("end_verse")
            + optional_subverse.copy().set_results_name("end_subverse")
            | sc_book.copy().set_results_name("end_book")
            + verse.copy().set_results_name("end_verse")
            + optional_subverse.copy().set_results_name("end_subverse")
            | book.copy().set_results_name("end_book")
            + chapter.copy().set_results_name("end_chapter")
            + no_letter_after.copy()
        )

        def build_verse_range(
            chapter_elem: pp.ParserElement | None,
        ) -> pp.ParserElement:
            """Build the grammar for one verse or range of verses.

            With no chapter element, as for a single-chapter book, the range
            cannot end with a chapter and verse.
            """
            same_book_end: pp.ParserElement = verse.copy().set_results_name(
                "end_verse"
            ) + optional_subverse.copy().set_results_name("end_subverse")
            if chapter_elem is not None:
                # The lookahead keeps the chapter from claiming an end verse
                # that punctuation happens to follow ("Mt 5,3-12, dove" in a
                # style that writes 5,3).
                same_book_end = (
                    pp.Opt(
                        chapter_elem.copy().set_results_name("end_chapter")
                        + separator(chapter_verse_separator)
                        + pp.FollowedBy(verse)
                    )
                    + same_book_end
                )
            return (
                not_a_book
                + verse.copy().set_results_name("start_verse")
                + optional_subverse.copy().set_results_name("start_subverse")
                + pp.Opt(
                    following
                    | (
                        range_separator
                        + (
                            other_book_end
                            | not_a_cited_book + same_book_end
                            # Or just a subverse of the same verse
                            | subverse.copy().set_results_name("end_subverse")
                        )
                    )
                )
                + end_location
            ).set_parse_action(self._draft_verses)

        def build_book_branches(
            book_elem: pp.ParserElement, chapter_elem: pp.ParserElement
        ) -> tuple[pp.ParserElement, pp.ParserElement]:
            """Build the book grammar branches for a book and chapter element.

            Returns the branch that begins with a chapter and verse
            ("John 3:16; 4") and the one that begins with a whole chapter
            ("John 3", "John 3–5", "John 3; 4:5").
            """
            chapter_and_verses = (
                chapter_elem.copy().set_results_name("start_chapter")
                + separator(chapter_verse_separator)
                + pp.DelimitedList(
                    build_verse_range(chapter_elem),
                    delim=separator(verse_range_separator),
                )
            ).set_parse_action(self._draft_chapter_and_verses)

            whole_chapters = (
                chapter_elem.copy().set_results_name("start_chapter")
                + (
                    range_separator
                    + (
                        other_book_end
                        | not_a_cited_book
                        + chapter_elem.copy().set_results_name("end_chapter")
                        + (
                            separator(chapter_verse_separator)
                            + verse.copy().set_results_name("end_verse")
                            + optional_subverse.copy().set_results_name("end_subverse")
                            | no_letter_after.copy()
                        )
                    )
                    | no_letter_after.copy()
                )
                + end_location
            ).set_parse_action(self._draft_chapters)

            # A chapter that follows without a book name must be one some book
            # could have: "CCL" after "Prov. IX, 1; " is the Corpus
            # Christianorum, not chapter 250.
            plausible_chapter = pp.FollowedBy(
                chapter_elem.copy().add_condition(
                    lambda t: not isinstance(t[0], int) or t[0] <= most_chapters
                )
            )
            more = pp.ZeroOrMore(
                separator(chapter_separator)
                + not_a_book
                + plausible_chapter
                + (chapter_and_verses | whole_chapters)
            )

            verses_first = (
                book_elem.copy().set_results_name("book")
                + chapter_and_verses
                + more
                + end_location
            ).set_parse_action(self._make_ranges)
            chapters_first = (
                book_elem.copy().set_results_name("book")
                + whole_chapters
                + more
                + end_location
            ).set_parse_action(self._make_ranges)
            return verses_first, chapters_first

        verses_first, chapters_first = build_book_branches(book, chapter)

        # A book with lettered chapters (the NABRE's Esther A–F) gets its own
        # branches, whose chapter element matches a letter as well as a
        # number. The letter parses as a negative number, which
        # _finish_ranges turns into the place the versification gives it.
        lettered_verses_first: list[pp.ParserElement] = []
        lettered_chapters_first: list[pp.ParserElement] = []
        for lettered_id in self.versification.max_verses:
            letters = self.versification.chapter_letters(lettered_id)
            lettered_names = [
                name for name, book_id in names.items() if book_id == lettered_id
            ]
            if not lettered_names or not letters:
                continue
            # A factory function gives the parse action a single-argument
            # signature (pyparsing dispatches on arity) with the loop
            # variable bound at definition time.

            def make_letter_action(
                letters: list[str],
            ) -> Callable[[pp.ParseResults], int]:
                """Return a parse action mapping a chapter letter to its number."""
                return lambda t: -1 - letters.index(str(t[0]))

            lettered_book = _book_element(dict.fromkeys(lettered_names, lettered_id))
            # The lookahead keeps a letter from matching the start of a longer
            # word, as with Roman-numeral chapters above.
            letter_chapter = pp.Regex(
                "(?:"
                + "|".join(
                    re.escape(letter)
                    for letter in sorted(letters, key=len, reverse=True)
                )
                + r")(?![0-9A-Za-zÆæŒœ])"
            )
            letter_chapter.set_parse_action(make_letter_action(letters))
            lettered_cv, lettered_c = build_book_branches(
                lettered_book, letter_chapter | chapter
            )
            lettered_verses_first.append(lettered_cv)
            lettered_chapters_first.append(lettered_c)

        sc_verses = (
            sc_book.copy().set_results_name("book")
            + pp.DelimitedList(
                build_verse_range(None), delim=separator(verse_range_separator)
            )
            + end_location
        ).set_parse_action(self._make_sc_ranges)

        # A bare book name is the whole book, and two joined by a range
        # separator are a range of whole books ("Matt–John").
        whole_books = (
            book.copy().set_results_name("book")
            + pp.Opt(
                range_separator
                + (other_book_end | book.copy().set_results_name("end_book"))
            )
            + end_location
        ).set_parse_action(self._make_ranges)

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
        # Jude 1 or "John 3:16" parse as "John 3". The lettered branches come
        # before their numeric counterparts so that a letter chapter is tried
        # before the fallbacks that would match less of the text.
        book_ref = leading_word_boundary + pp.MatchFirst(
            [
                *lettered_verses_first,
                verses_first,
                sc_verses,
                *lettered_chapters_first,
                chapters_first,
                whole_books,
            ]
        )

        # A reference may go on to other books. A trailing versification
        # designator (e.g. "Vulg.", "(LXX)") applies to every book in it.
        bible_ref_body: pp.ParserElement = pp.DelimitedList(
            book_ref, separator(chapter_separator)
        )
        if self._designator_versifications:
            # one_of escapes regex metacharacters and prefers longer matches,
            # so "Vulgate" wins over "Vulg.". The word boundary keeps "LXX"
            # from matching inside a longer word; leave_whitespace on it keeps
            # the And from skipping past the space after the designator and
            # testing the next word instead.
            designator = (
                pp.one_of(list(self._designator_versifications.keys()))
                + pp.NotAny(pp.Char(pp.identbodychars)).leave_whitespace()
            )
            designator.set_parse_action(lambda t: self._designator_versifications[t[0]])
            bible_ref_body = bible_ref_body + pp.Opt(
                designator.set_results_name("versification_designator")
            )
        self.bible_ref_parser = (bible_ref_body + end_location).set_parse_action(
            self._make_bible_ref
        )
        _extend_whitespace(self.bible_ref_parser)

    def _draft_verses(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> _Draft:
        """Draft a verse or range of verses from parsed tokens.

        This is a parse action for use with pyparsing.
        """
        draft = _Draft(
            start_loc=loc,
            end_loc=_get_int(tokens, "end_location", loc),
            verse=int(tokens["start_verse"]),
            subverse=str(tokens["start_subverse"]),
        )
        has_end = any(
            name in tokens for name in ("end_book", "end_verse", "end_subverse")
        )
        # A following-verses marker may have parsed as a subverse. It keeps
        # the subverse until _finish_ranges can tell whether the versification
        # has an inserted verse by that letter.
        if "following_verses" in tokens:
            draft.following = "ff"
        elif "following_verse" in tokens:
            draft.following = "f"
        elif not has_end and draft.subverse == self.style.following_verses:
            draft.following = "ff"
        elif not has_end and draft.subverse == self.style.following_verse:
            draft.following = "f"
        elif has_end:
            draft.has_end = True
            if "end_book" in tokens:
                draft.end_book = str(tokens["end_book"])
            draft.end_chapter = _opt_int(tokens, "end_chapter")
            if draft.end_book is None:
                # A subverse alone ends the range in the verse it starts in.
                draft.end_verse = _get_int(tokens, "end_verse", draft.verse or 0)
            else:
                draft.end_verse = _opt_int(tokens, "end_verse")
            draft.end_subverse = _get_str(tokens, "end_subverse", "")
        return draft

    @staticmethod
    def _draft_chapter_and_verses(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> list[_Draft]:
        """Give the first of a chapter's verse ranges the chapter stated with it.

        This is a parse action for use with pyparsing.
        """
        drafts = [token for token in tokens if isinstance(token, _Draft)]
        drafts[0].chapter = int(tokens["start_chapter"])
        drafts[0].start_loc = loc
        return drafts

    @staticmethod
    def _draft_chapters(
        original_text: str, loc: int, tokens: pp.ParseResults
    ) -> _Draft:
        """Draft a range that begins with a whole chapter from parsed tokens.

        This is a parse action for use with pyparsing.
        """
        draft = _Draft(
            start_loc=loc,
            end_loc=_get_int(tokens, "end_location", loc),
            chapter=int(tokens["start_chapter"]),
        )
        if "end_chapter" in tokens or "end_book" in tokens:
            draft.has_end = True
            if "end_book" in tokens:
                draft.end_book = str(tokens["end_book"])
            draft.end_chapter = _opt_int(tokens, "end_chapter")
            draft.end_verse = _opt_int(tokens, "end_verse")
            draft.end_subverse = _get_str(tokens, "end_subverse", "")
        return draft

    def _make_ranges(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> list[VerseRange]:
        """Create the VerseRanges of one book name from parsed tokens.

        This is a parse action for use with pyparsing.
        """
        return self._finish_ranges(original_text, loc, tokens, None)

    def _make_sc_ranges(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> list[VerseRange]:
        """Create the VerseRanges of a single-chapter book from parsed tokens.

        This is a parse action for use with pyparsing.
        """
        return self._finish_ranges(original_text, loc, tokens, 1)

    def _finish_ranges(
        self,
        original_text: str,
        loc: int,
        tokens: pp.ParseResults,
        chapter: int | None,
    ) -> list[VerseRange]:
        """Supply each drafted range with its book and chapter.

        Args:
            original_text: The text being parsed
            loc: Where the book name begins
            tokens: The book ID and the drafts of its ranges
            chapter: The chapter in force before any is stated

        Returns:
            The finished verse ranges

        """

        def point(
            book: str,
            chapter: int | None,
            verse: int | None,
            subverse: str,
        ) -> RefPoint:
            """Make a point, placing a lettered chapter (a negative number).

            The verses of a lettered chapter are held as verses inserted
            beside a verse of the numbered text, each with a subverse made of
            the letter and its verse number; the letter alone is the chapter
            as a whole.
            """
            if chapter is None or chapter >= 0:
                return RefPoint(book, chapter, verse, subverse)
            letter = self.versification.chapter_letters(book)[-1 - chapter]
            located = self.versification.lettered_chapter(book, letter)
            assert located is not None
            if verse is None:
                return RefPoint(book, located[0], located[1], letter)
            return RefPoint(book, located[0], located[1], f"{letter}{verse}{subverse}")

        book = str(tokens["book"])
        drafts = [token for token in tokens if isinstance(token, _Draft)]
        if not drafts:
            whole_book = _Draft(
                loc, _get_int(tokens, "end_location", loc), whole_book=True
            )
            if "end_book" in tokens:
                whole_book.has_end = True
                whole_book.end_book = str(tokens["end_book"])
                whole_book.end_chapter = _opt_int(tokens, "end_chapter")
                whole_book.end_verse = _opt_int(tokens, "end_verse")
                whole_book.end_subverse = _get_str(tokens, "end_subverse", "")
            drafts = [whole_book]
        drafts[0].start_loc = loc

        ranges: list[VerseRange] = []
        for draft in drafts:
            if draft.whole_book:
                start = RefPoint(book)
            else:
                if draft.chapter is not None:
                    chapter = draft.chapter
                if draft.following and draft.subverse:
                    # A marker glued to the verse names an inserted verse
                    # where there is one ("Esg 1:1f" in the CEI).
                    assert draft.verse is not None
                    if (
                        chapter is not None
                        and chapter >= 0
                        and draft.subverse
                        in self.versification.verse_parts(book, chapter, draft.verse)
                    ):
                        draft.following = ""
                    else:
                        draft.subverse = ""
                start = point(book, chapter, draft.verse, draft.subverse)

            if draft.end_book is not None:
                end_chapter = draft.end_chapter
                # A verse alone is a verse of a single-chapter book.
                if end_chapter is None and draft.end_verse is not None:
                    end_chapter = 1
                end = RefPoint(
                    draft.end_book, end_chapter, draft.end_verse, draft.end_subverse
                )
                book, chapter = end.book, end.chapter
            elif draft.whole_book:
                end = start
            elif draft.following == "ff":
                end = point(book, chapter, None, "")
            elif draft.following == "f":
                assert draft.verse is not None
                end = point(book, chapter, draft.verse + 1, "")
            elif draft.has_end:
                if draft.end_chapter is not None:
                    chapter = draft.end_chapter
                end = point(book, chapter, draft.end_verse, draft.end_subverse)
            else:
                end = start

            ranges.append(
                VerseRange(
                    start,
                    end,
                    original_text[draft.start_loc : draft.end_loc].strip(),
                )
            )
        return ranges

    def _make_bible_ref(
        self, original_text: str, loc: int, tokens: pp.ParseResults
    ) -> BibleRef:
        """Create a BibleRef from parsed tokens.

        This is a parse action for use with pyparsing.

        Returns:
            A BibleRef instance based on the parsed tokens

        """
        end_location = _get_int(tokens, "end_location", -1)
        ranges = [token for token in tokens if isinstance(token, VerseRange)]

        # A trailing designator overrides the parser's default versification.
        versification = self.versification
        if "versification_designator" in tokens:
            designated = tokens["versification_designator"]
            assert isinstance(designated, Versification)
            versification = designated

        if versification.includes("PS2") and versification.last_verse("PSA", 151) < 0:

            def psalm(point: RefPoint) -> RefPoint:
                """Place Psalm 151 in the book this versification gives it."""
                if point.book == "PSA" and point.chapter == 151:
                    return RefPoint("PS2", 1, point.verse, point.subverse)
                return point

            ranges = [
                VerseRange(
                    psalm(verse_range.start),
                    psalm(verse_range.end),
                    verse_range.original_text,
                )
                if verse_range.start.book == verse_range.end.book == "PSA"
                and verse_range.start.chapter == verse_range.end.chapter == 151
                else verse_range
                for verse_range in ranges
            ]

        return BibleRef(
            ranges=ranges,
            versification=versification,
            original_text=original_text[loc:end_location].strip(),
        )

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
    def _passes_sensitivity(ref: BibleRef, sensitivity: "Sensitivity") -> bool:
        """Check if a BibleRef passes the sensitivity filter."""
        if sensitivity == Sensitivity.BOOK:
            return True
        if sensitivity == Sensitivity.CHAPTER:
            return not ref.is_whole_books()
        return not ref.is_whole_chapters()

    def scan_string(
        self,
        text: str,
        as_ranges: bool = False,
        sensitivity: "Sensitivity" = Sensitivity.VERSE,
    ) -> Iterator[tuple[BibleRef, int, int]]:
        """Scan a string for BibleRefs.

        This method scans the entire string for references to one or more books of the Bible.

        Args:
            text: The string to scan
            as_ranges: If True, yield a BibleRef for each verse range
            sensitivity: Controls which references are reported. VERSE (default)
                skips whole-chapter and whole-book references. CHAPTER also
                reports whole-chapter references. BOOK reports everything.
                With as_ranges, each verse range is judged by itself.

        Yields:
            A reference and the start and end of its location in text.
            (ref: BibleRef, start: int, end: int)

        """
        for tokens, start, _ in self.bible_ref_parser.scan_string(text):
            ref = tokens[0]
            assert isinstance(ref, BibleRef)
            if as_ranges:
                next_start = start
                for range_ref in ref.range_refs():
                    # Use the original text to find the start and end.
                    assert range_ref.original_text is not None
                    range_start = text.find(range_ref.original_text, next_start)
                    assert range_start >= 0
                    next_start = range_start + len(range_ref.original_text)
                    if self._passes_sensitivity(range_ref, sensitivity):
                        yield (range_ref, range_start, next_start)
            else:
                if not self._passes_sensitivity(ref, sensitivity):
                    continue
                assert ref.original_text is not None
                yield (ref, start, start + len(ref.original_text))

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
