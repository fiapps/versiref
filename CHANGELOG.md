# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
