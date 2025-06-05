# VersiRef

VersiRef is a Python package for sophisticated parsing, manipulation, and printing of references to the Bible.

## Features

- Parse and manipulate Bible references.
- Support for different versification systems (e.g., original language \[BHS + UBS GNT\], "English," LXX, Vulgate).
- Query information about chapters and verses in different books of the Bible.

## Overview of `versiref` classes

- `BibleRef` represents a sequence of verse ranges within one or more books of the Bible.
    - It has a `Versification` and a list of `SimpleBibleRef`s.
- `Versification` represents a division of the Bible into chapters and verses. Different texts of the Bible do this differently.
- `SimpleBibleRef` represents a sequence of verse ranges within a single book of the Bible.
    - It can be used independently of a `BibleRef`, but since it has no `Versification`, you need to supply a `Versification` for all operations that require one.
    - It contains a list of `VerseRange`s: this is a data class not intended to be used independently.
- `RefStyle` defines separators and book names or abbreviations to use in formatting or parsing a reference.
    - This gives the package the versatility to handle different styles and languages.
- `RefParser` creates PEG parsers based on a `RefStyle` and `Versification`.
    - These can be used to parse a single reference or to find all references in a long string, e.g., the content of a text file.

## Examples

### Convert references from one style to another

```python
from pyparsing import ParseException
from versiref import RefParser, RefStyle, standard_names, Versification

def parse_reference(reference: str) -> None:
    """Parse argument and print result."""
    # Expect SBL abbreviations in the input
    sbl_abbrevs = standard_names("en-sbl_abbreviations")
    sbl_style = RefStyle(names=sbl_abbrevs)
    # Use typical versification for English Bibles
    versification = Versification.named("eng")
    # Build parser for style
    parser = RefParser(sbl_style, versification)
    # Use Italian CEI Bible style for output
    cei_abbrevs = standard_names("it-cei_abbreviazioni")
    cei_style = RefStyle(names=cei_abbrevs, chapter_verse_separator=",", verse_range_separator=".")
    try:
        ref = parser.parse(reference, silent=False)
        # Check whether it refers to verse ranges that exist
        if not ref.is_valid():
            print(f"Warning: {reference} is not a valid reference.")
        print(ref.format(cei_style))
    except ParseException as e:
        print(f"Could not parse reference: {reference}")
        print(e)

# Prints "Gv 7,53–8,11"
parse_reference("John 7:53–8:11")
```

### Look for references in a string

```python
from versiref import RefParser, RefStyle, Versification, standard_names

def scan_string(content: str) -> None:
    """Count and print the Bible references in content."""
    # Use SBL abbreviations
    sbl_abbrevs = standard_names("en-sbl_abbreviations")
    style = RefStyle(names=sbl_abbrevs)
    # But also recognize abbreviations from the Chicago Manual of Style
    style.also_recognize("en-cmos_short")
    # Use typical versification for English Bibles
    versification = Versification.named("eng")
    # Build parser for style
    parser = RefParser(style, versification)
    count = 0
    for ref, start, end in parser.scan_string(content):
        # Check for out-of-range chapter or verse
        if not ref.is_valid():
            print(f"Warning: {ref.format(style)} is not a valid reference.")
        else:
            # Print in SBL style
            print(ref.format(style))
        count += 1
    print(f"Found {count} references.")

text = """
Today's readings are Acts 2:1-11; Ps 104:1,24,29-30,31,34; 1 Cor 12:3b-7,12-13; Jn 20:19-23.
The prophecy in Is 7:10-14 is important background for Lk 1:26-38.
The Septuagint has a Ps 118:120, but English Bibles don't.
"""
scan_string(text)
```

Output:

```
Acts 2:1–11; Ps 104:1, 24, 29–30, 31, 34; 1 Cor 12:3b–7, 12–13; John 20:19–23
Isa 7:10–14
Luke 1:26–38
Warning: Ps 118:120 is not a valid reference.
Found 4 references.
```
