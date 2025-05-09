"""versiref can parse, manipulate, and format references to Bible verses.

It is versatile in that it can handle complex references, different
versifications, and it is flexible about the format is parses and the output it
generates.
"""

from versiref.bible_ref import BibleRef, SimpleBibleRef, VerseRange
from versiref.ref_parser import RefParser
from versiref.ref_style import RefStyle, standard_names
from versiref.versification import Versification

__all__ = [
    "BibleRef",
    "SimpleBibleRef",
    "VerseRange",
    "RefParser",
    "RefStyle",
    "Versification",
    "standard_names",
]
