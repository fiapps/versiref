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
uv run ruff check                # Linting
uv run ruff format               # Code formatting
```

### Documentation
```sh
uv run mkdocs build              # Build human-readable documentation
uv run mkdocs serve              # Serve documentation locally
uv run python scripts/build_api_md.py  # Generate the bundled API reference (creates src/versiref/docs/api.md)
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

When asked to make a release, Claude performs steps 1–8; publishing and pushing are done manually afterward (step 9).

1. Bump the version in `pyproject.toml` (the sole source of the version number).
2. Update `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format: rename the `## Unreleased` heading to the new version with the release date (`## X.Y.Z - YYYY-MM-DD`).
3. Run `uv lock` to update the lock file.
4. Run `pip-audit` (see "Dependency auditing") and verify no unfixed advisories apply.
5. Run tests, type checking, and linting to verify everything passes, and run `uv run python test_all_versions.py` so that the tests pass under every supported Python and not only the development one.
6. Make the release commit (subject line `Release X.Y.Z`).
7. Create an annotated tag named with the bare version number (e.g., `0.5.0`, not `v0.5.0`).
   The tag annotation message is the new version's `CHANGELOG.md` section — its `### Added`/`### Changed`/`### Removed` subsection headings and their entries, but **without** the `## X.Y.Z` version heading line.
   Tag with `git tag -a --cleanup=verbatim -F <file>`: the default cleanup strips lines beginning with `#`, which would silently drop the `###` subsection headings.
   GitHub renders this annotation as the release notes on the releases page.
8. Build the artifacts (Claude builds them but does not publish or push), in order:
   1. Regenerate the bundled API reference with `uv run python scripts/build_api_md.py`. `src/versiref/docs/api.md` is generated and git-ignored but ships in the wheel, so skipping this bundles a stale copy (left over from an earlier code state) or, on a fresh checkout, none at all — and because the file is untracked, neither the tests nor the release commit would reveal it.
   2. Delete any artifacts from previous versions with `rm -f dist/*`, so the directory holds only the current release's files and a publish step that uploads `dist/*` cannot pick up stale builds.
   3. Run `uv build` to produce the wheel and sdist in `dist/`.
9. Manual: publish and push the commit and tag.

## Architecture

### Core Classes

The package has a layered architecture with six main classes:

1. **`RefPoint`** (frozen dataclass) - One end of a range: a book ID (Paratext three-letter codes like "GEN", "1CO", "JHN"), a chapter, a verse, and a subverse. A chapter or verse of None means "unspecified": a point with no verse is a whole chapter, and one with no chapter is a whole book. At the start of a range that means the beginning of the chapter or book, and at the end it means the end of it.

2. **`VerseRange`** (frozen dataclass) - A range from a start `RefPoint` to an end `RefPoint`. The two are equal for a single verse, chapter, or book, and may name different books ("Matt–John", "1 Sam 31:1–2 Sam 1:27"). "John 3:16ff" starts at John 3:16 and ends at John 3.

3. **`BibleRef`** (frozen dataclass) - A tuple of `VerseRange`s and a `Versification`, which may be None (like Python's naive datetime): such a reference can be formatted but not validated, mapped, or given verse keys. Equality and hashing ignore `original_text`.

4. **`Versification`** - Represents how the Bible is divided into chapters and verses. Different texts (BHS, UBS GNT, LXX, Vulgate, English Bibles) divide things differently. Loaded from JSON data files in `src/versiref/data/versifications/`. Standard versifications include "org" (original languages), "eng" (typical English), "lxx", and "vulgata". Compared and hashed by identity; `Versification.named()` caches, so it returns the same object for an identifier each time.

5. **`RefStyle`** - Defines separators and book names/abbreviations for formatting and parsing. Controls things like ":" vs "," for chapter-verse separator, "–" vs "-" for ranges, etc.

6. **`RefParser`** - Creates PEG parsers (using pyparsing) based on a `RefStyle` and `Versification`. Can parse single references or scan long strings for all references.

The order of books in a versification's `maxVerses` decides which books lie inside a range that spans books. Most of the bundled versifications use Paratext's order, with the deuterocanonical books after Revelation; `nabre` and `cei` use their Bibles' own order.

### Data Files

- **`src/versiref/data/versifications/`** - JSON files defining chapter/verse divisions for different Bible texts (from UBSCAP GitHub repo, MIT licensed)
- **`src/versiref/data/book_names/`** - JSON files mapping book IDs to names/abbreviations in different languages and styles (e.g., "en-sbl_abbreviations.json", "it-cei_nomi.json")

`VERSIFICATIONS.md` (not packaged) records how the versification JSON is interpreted — notably that an unmapped location maps to itself, which makes a missing entry an assertion rather than a gap — and what the harder texts actually look like. Read it before editing versification data, especially for Greek Esther.

### Special Book ID Handling

- **PSA/PSAS**: Psalm vs Psalms (singular/plural). PSAS is a key in book name dictionaries for the plural form, never a book ID in a reference: a parser reads a plural name as PSA, and formatting chooses the plural when the ranges under one statement of the name cite more than one psalm.
- **PS2**: Psalm 151. No bundled name set names it, so it cannot yet be formatted (issue #39).
- **EST/ESG**: Esther vs Greek Esther (some versifications separate them). The NABRE has only EST: its lettered chapters A–F are held as verses inserted beside a verse of EST, with a subverse made of the letter and verse number (Esther C:12 is the subverse "C12" of EST 4:17, and "C" alone is the whole chapter). The versification data defines them, not the style; see "Lettered chapters" in `VERSIFICATIONS.md`.

## Code Conventions

Per CONVENTIONS.MD:
- Only use comments when necessary (code should be self-explanatory)
- Comments should add information not readily apparent from the code

Additional conventions observed in the codebase:
- Uses strict mypy type checking (`strict = true` in pyproject.toml)
- Ruff linting enforces docstrings (D series rules, ignores D203/D213) along with the E, W, F, I, B, UP, SIM, C4, PT, and RUF rules; RUF001–RUF003 are off because typeset characters such as en dashes are intended
- Docstrings use Google style format
- Imports use absolute imports from versiref package
- All main classes are re-exported from `versiref/__init__.py`
