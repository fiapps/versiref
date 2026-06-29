# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
