# SacraPagina Design Document

SacraPagina is a Python package for sophisticated parsing, manipulation, and printing of references to the Bible.

## SimpleBibleRef

An instance of `SimpleBibleRef` represents a sequence of verse ranges within a single book of the Bible.
These ranges are not necessarily in numeric order because the person who creates the citation may prefer a different order.
The class is naive in that it doesn't specify its versification (this is something like `datetime`'s naive classes, which don't specify a time zone).
In the simplest case, it designates a single chapter and verse, such as John 3:16.
More generally, each range contains a start chapter, start verse, start sub-verse, end chapter, end verse, and end sub-verse.
Each range also has `original_text: Optional[str]`: this is the text from which the range was parsed, if any.
The class stores a list of such ranges, a book ID, and the `original_text` from which the book ID was parsed.
Book IDs are the three-letter codes used by Paratext.
The start and end chapter numbers will almost always be the same, but the volume of data is probably not large enough to justify complicating the code by optimizing for that.
Similarly, sub-verse divisions (e.g., "a" or "d") will often not be used: when there is none, the sub-verse will be an empty string.
We can just store all six values for each range, even in the trivial case where the range is a single verse.
Although some Bible translations use letters for "chapter numbers" (e.g., Greek Esther in Rahlfs and NAB), we don't need to support that explicitly: Paratext's scheme represents these as numbered chapters with a different book name (ESG instead of EST).
Nevertheless, it may be simplest to use a string for chapter as we do for verse and sub-verse.

## BibleRef

An instance of `BibleRef` represents a sequence of verse ranges within a one or more books of the Bible.
It holds an array of `SimpleBibleRef` and the `Versification` they use.

## Versification

An instance of `Versification` represents a way of dividing the text of the Bible into chapters and verses.
Versifications are defined by JSON data that is loaded from a file when an instance is created.
Alternatively, the JSON data could be converted to Python data and stored as constants in code.
The `last_verse(book, chapter)` method returns the integer number of the last verse of the given chapter of the given book.
If the book is unknown or the chapter does not exist, it returns -1.
An initial, trivial implementation will not load a data file and will simply return 99 from `last_verse()` regardless of its arguments.
Support for mapping verses between versifications can be added at a later stage.

For versification data, we can use JSON files from a [UBSCAP GitHub repo](https://github.com/ubsicap/versification_json).
These are under an MIT license.
As the README notes, some of the files contain errors: there are mappings from verses that do not exist according to the max verse counts.
However, it seems the best starting point available, and those known errors will be harmless because such mappings will never be applied.
There's a JSON schema in the repo that can be used for validation.
The `maxVerses` property of the top-level object contains the data `last_verse()` must return.

The JSON files have data for Paratext's seven standard versifications.
Mappings are defined relative to the mapping called "Original" (`org.json`) for lack of a better name: This uses the BHS OT, the UBS GNT NT, and the "Catholic" deuterocanon.

It would not be hard to derive `maxVerses` and `excludedVerses` data for specific Bibles from verse lists exported from Accordance.
Mappings for these Bibles are an open question.

### Mapping verses between versifications

This would have to be done one range at a time, mapping the start and end of each.
When mapping a range start, if the location maps to a range, we pick the start of the range.
When mapping a range end, if the location maps to a range, we pick the end of the range.
For example, if 1KI 18:33 maps to 1KI 18:33-34 and we are mapping a range that starts at 1KI 18:33, then the mapped range starts at 1KI 18:33.
But if we are mapping a range that ends at 1KI 18:33, then the mapped range ends at 1KI 18:34.
However, we might not at first need code to handle the case where a location maps to a range, since it seems Paratext doesn't handle that. Consequently, its files don't define such mappings, even though there are cases in which they ought to be used.

## Style

A `Style` defines how a `SimpleBibleRef` or `BibleRef` is converted to a string and how strings are parsed to produce these classes.

* `names`: maps Bible book IDs to string abbreviations or to full names, depending on the style.
* `verse_separator`: Defaults to ", "
* `chapter_separator`: Defaults to "; "
* `recognized_names`: maps abbreviations and/or full names to Bible book IDs. For flexibility in parsing, this typically recognizes additional abbreviations beyond those used in `names`.

### Named sets of book names/abbreviations

We need to have a way of supplying named sets of book names and book name abbreviations, so users can select, e.g., short SBL abbreviations.
These sets are simply dictionaries, but perhaps we need to store them in files or allow users to define their own set of abbreviations in a file.

## RefParser

The constructor takes a `Style` and builds a PEG parser that recognizes Bible references in that style.
Whitespace is generally ignored by the parser (default for `pyparser`).
Various methods support parsing a whole string to a `SimpleBibleRef` or `BibleRef`, scanning a long string for references, and transforming a long string (e.g., to tag references).
