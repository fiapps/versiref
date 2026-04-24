# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VersiRef is a Python package for sophisticated parsing, manipulation, and printing of references to the Bible. It supports different versification systems (original language texts, English, LXX, Vulgate), multiple reference styles (SBL, Italian CEI, etc.), and can both parse references from text and format them in various styles.

## Development Commands

This project uses [uv](https://github.com/astral-sh/uv) for package management.

### Testing
```sh
uv run pytest                    # Run all tests
uv run pytest tests/test_*.py    # Run a specific test file
uv run pytest -k test_name       # Run tests matching a pattern
```

### Code Quality
```sh
uv run mypy src/versiref         # Type checking (strict mode enabled)
uv run ruff check                # Linting (docstring checks enabled)
uv run ruff format               # Code formatting
```

### Documentation
```sh
uv run mkdocs build              # Build human-readable documentation
uv run mkdocs serve              # Serve documentation locally
uv run pydoc-markdown            # Build API documentation for LLMs (creates build/api.md)
```

### Building
```sh
uv build                         # Build distribution packages
```

### Dependency auditing

Supply-chain checks run at two points: when upgrading dependencies and before tagging a release. See `SECURITY.md` for the threat model and rationale; the commands are:

**Upgrade with a 7-day cooldown** (hijacked releases are usually detected and yanked within that window):

```sh
uv lock --upgrade --exclude-newer "$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ)"
```

The date expression above is for BSD `date` (macOS). On GNU `date`: `date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ`.

Cooldown exception: if a CVE is announced for a current dependency, bypass the cooldown and upgrade immediately — a known-bad version is worse than an unquarantined good one.

**Scan the locked dependencies for known advisories:**

```sh
uv export --format requirements-txt --no-emit-project | uvx pip-audit -r /dev/stdin --disable-pip --require-hashes
```

`--disable-pip` tells pip-audit to trust the pinned+hashed list from `uv export` rather than spinning up its own venv (which fails on uv-managed Python since ensurepip is disabled there).

Run after any lockfile change and before each release.

### Releasing

To prepare a release:

1. Bump the version in `pyproject.toml` (the sole source of the version number).
2. Update `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
3. Run `uv lock` to update the lock file.
4. Run `pip-audit` (see "Dependency auditing") and verify no unfixed advisories apply.
5. Run tests, type checking, and linting to verify everything passes.

Git tags use bare version numbers (e.g., `0.5.0`, not `v0.5.0`). Building, publishing, and tagging are done manually after the release commit.

## Architecture

### Core Classes

The package has a layered architecture with five main classes:

1. **`VerseRange`** (dataclass) - The atomic unit representing a range of verses within a single book. Contains start/end chapter/verse/subverse fields. A verse number < 0 means "unspecified" (used for whole chapters or "ff" notation).

2. **`SimpleBibleRef`** - Represents a sequence of verse ranges within a single book. Contains a book ID (Paratext three-letter codes like "GEN", "1CO", "JHN") and a list of `VerseRange`s. This is "naive" (like Python's naive datetime) because it has no versification system - you must supply one for operations that need it.

3. **`BibleRef`** - Represents verse ranges across one or more books. Contains a `Versification` and a list of `SimpleBibleRef`s. This is the main class for multi-book references.

4. **`Versification`** - Represents how the Bible is divided into chapters and verses. Different texts (BHS, UBS GNT, LXX, Vulgate, English Bibles) divide things differently. Loaded from JSON data files in `src/versiref/data/versifications/`. Standard versifications include "org" (original languages), "eng" (typical English), "lxx", and "vulgata".

5. **`RefStyle`** - Defines separators and book names/abbreviations for formatting and parsing. Controls things like ":" vs "," for chapter-verse separator, "–" vs "-" for ranges, etc.

6. **`RefParser`** - Creates PEG parsers (using pyparsing) based on a `RefStyle` and `Versification`. Can parse single references or scan long strings for all references.

### Data Files

- **`src/versiref/data/versifications/`** - JSON files defining chapter/verse divisions for different Bible texts (from UBSCAP GitHub repo, MIT licensed)
- **`src/versiref/data/book_names/`** - JSON files mapping book IDs to names/abbreviations in different languages and styles (e.g., "en-sbl_abbreviations.json", "it-cei_nomi.json")

### Special Book ID Handling

- **PSA/PSAS**: Psalm vs Psalms (singular/plural). PSAS is used in book name dictionaries for plural form.
- **PS2**: Psalm 151 - uses PSA abbreviation, PS2 entries in name dictionaries are ignored.
- **EST/ESG**: Esther vs Greek Esther (some versifications separate them, NAB uses letters for ESG chapters).

## Code Conventions

Per CONVENTIONS.MD:
- Only use comments when necessary (code should be self-explanatory)
- Comments should add information not readily apparent from the code

Additional conventions observed in the codebase:
- Uses strict mypy type checking (`strict = true` in pyproject.toml)
- Ruff linting enforces docstrings (D series rules, ignores D203/D213)
- Docstrings use Google style format
- Imports use absolute imports from versiref package
- All main classes are re-exported from `versiref/__init__.py`
