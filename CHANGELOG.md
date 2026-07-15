# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed

- The Italian name of the book of Habakkuk has been corrected. It incorrectly had an "H" at the beginning.

## 0.7.3 - 2026-07-09

### Fixed

- `Versification.map_verse` now handles a subverse that denotes a portion of a verse (e.g. a line of a Psalm) rather than a deuterocanonical insertion. Previously such a subverse defeated the verse lookup and the reference fell through to an identity mapping, so `versiref convert -f eng -t vulgata 'Ps 45:15b'` failed instead of yielding `Ps 44:16b`. When no mapping matches the subverse exactly, the base verse is mapped and the subverse is carried through a 1:1 mapping or discarded across a 1:N or N:1 mapping. Deuterocanonical subverse mappings (e.g. Greek Esther) are unchanged.

## 0.7.2 - 2026-07-01

### Fixed

- The free-text scanner (`RefParser.scan_string`/`scan_string_simple`, used by `versiref scan` and reference indexing) no longer matches a book name glued to the end of a longer word. A leading Unicode-aware word-boundary look-behind now requires the character before a book name to be a non-letter, so a citation prefix like `CongrRom 5:65-103` no longer yields a phantom `Rom 5:65–103`. Matches after whitespace, digits, and punctuation (parentheses, quotes, brackets, en/em dashes) are unchanged, as is single-reference `parse`/`validate` behavior.

## 0.7.1 - 2026-06-29

### Fixed

- `RefParser` now honors a style's custom `verse_range_separator` when parsing verse lists. Two `DelimitedList` call sites read the class default `", "` off the `RefStyle` class instead of the instance value, so a style configured with a different separator (e.g. `"."`, as in `Esth 15:5.10.15`) parsed only the first verse and left the remainder as unparsed trailing text. The default comma-separated behavior is unchanged.

## 0.7.0 - 2026-06-29

### Added

- A `versiref` command-line interface (a click group) exposing the library's core operations from the shell: `convert` a reference between versifications (e.g. the Septuagint/Vulgate Psalm numbering shifts), `validate` that a reference parses and falls in range, `parse` a reference to normalize it or emit its structured form, and `scan` a file or stdin for every reference with character offsets. All accept `--json` and set meaningful exit codes (`0` ok, `1` invalid/unmappable, `2` unparseable).
- Introspection commands `versiref list styles`, `versiref list versifications`, and `versiref list book-names`, each accepting a `--pattern` glob and `--json`.
- A `versiref docs` subcommand that prints the path to the documentation, which now ships inside the package (`index.md`, the generated `api.md`, and `cli.md`) and is resolved via `importlib.resources` so it works in both wheel and editable installs.

### Changed

- The `en-cmos_short`, `en-cmos_long`, and `en-bibleworks` styles now also recognize the SBL abbreviations (e.g. `Gen`, `John`) on input, in addition to their own forms. This is purely additive — existing recognized names keep their meaning (recognition is first-wins) and output formatting is unchanged.

## 0.6.0 - 2026-06-28

### Added

- `RefStyle.versification_identifiers` maps a trailing designator (e.g. `"Vulg."`, `"(LXX)"`) to a versification id string, declarable in style config via a `versification_identifiers` block and extendable with `RefStyle.also_recognize_versifications()`. When a style defines them, `RefParser.parse()`/`scan_string()` recognize a designator at the end of a reference and return a `BibleRef` in the named versification, overriding the parser default; `parse_simple()`/`scan_string_simple()` discard it (resolves #22).

### Fixed

- A custom `following_verse`/`following_verses` marker that the subverse rule cannot capture (longer than two characters, or containing non-lowercase characters, e.g. the Latin `"seq."`/`"seqq."`) is now interpreted correctly instead of being consumed and silently downgraded to a plain verse. The marker literals now set a results name, and the word-boundary test no longer skips intervening whitespace before checking the following character. The boundary is also applied to single-chapter books, so a marker glued to a longer word (e.g. `"seqq.foo"`) is rejected consistently. The default `f`/`ff` markers were unaffected.

## 0.5.1

### Added

- `Versification.available_names()` and `RefStyle.available_names()` list the identifiers their `named()` classmethods accept.
- `available_standard_names()` lists the identifiers the `standard_names()` function accepts.
- The two style/book-name discovery functions accept an optional glob pattern (e.g. `"en-*"`, `"it-*"`) to filter results by language prefix.

## 0.5.0

### Added

- `Sensitivity` enum to control which reference types are reported when scanning text (`VERSE`, `CHAPTER`, `BOOK`).
- `RefParser` can now parse references to whole chapters (e.g., "John 3") and whole books (e.g., "Genesis") (resolves #18).
- `SimpleBibleRef.range_keys()` method, refactored from `BibleRef.range_keys()`.
- Whole-book `SimpleBibleRef`s now yield a key pair spanning the entire book in `range_keys()`.

### Fixed

- Corrected an abbreviation in `it-cei_abbreviazioni.json`.

## 0.4.2

### Added

- `RefStyle.from_dict()` now supports a `base` key to inherit settings from another named style.

### Fixed

- `following_verse` and `following_verses` in the `it-cei` style now correctly use `"s"` and `"ss"`.

## 0.4.1

### Added

- NABRE and CEI (2008) versifications with verse mappings from the Copenhagen Alliance versification sniffer.
- BibleWorks book name abbreviations (`en-bibleworks` standard names *and* style).

### Changed

- `ethiopian_custom` versification excluded from the built package due to errors (resolves #27).
- N:1 and 1:N verse mappings now supported in `BibleRef.map_to()`.
- Subverse letters in versification mappings now supported.
- Fixed malformed mapping entries in `vulgata`, `nova_vulgata`, `rsc`, and `rso` versifications.

## 0.4.0

### Added

- `BibleRef.map_to()` maps a reference from one versification to another, going through the original-language versification as an intermediary.
    - Limitation: NABRE versification still lacks mapping data.

### Changed

- Updated versification data to [Copenhagen Alliance](https://github.com/Copenhagen-Alliance/versification-specification) versions.
- Data files are now licensed under CC BY-SA 4.0.

## 0.3.0

### Added

- `RefStyle.named()` factory method and standard named styles (`en-sbl`, `en-cmos_short`, `it-cei`, etc.).
- This is built on `RefStyle.from_file()` (JSON), which calls  `RefStyle.from_dict()`.

### Changed

- **Breaking change**: `parse()` and `parse_simple()` now default `silent=False`, raising exceptions on parse errors instead of silently returning `None`. Fixes #25.

## 0.2.2

### Added

- `versiref` now supports namespace packages.

## 0.2.1

### Changed

- Dropped support for Python 3.9, which is EOL since 2025-10-31.

## 0.2.0

### Added

- `BibleRef.range_keys()` yields the verse ranges in the form of (first_verse, last_verse) integer pairs, e.g., 23007014 for Is 7:14.

### Changed

- BibleRef, SimpleBibleRef, and Versification now use a concise string representation (`__str__()`).

## 0.1.0

Initial release.
