# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- A new versification, `douay-rheims`, for Challoner's Douay-Rheims. It follows the Clementine (`vulgata`) except in fifteen chapters that the printed Douay divides differently. Ten join two Clementine verses into one: 2 Samuel 13:38, Psalms 19:9, 28:10, and 150:5, Isaiah 46:11, Amos 9:14, Judith 4:5, Sirach 29:16, 1 Thessalonians 4:11, and 2 Thessalonians 2:10, most with the rest of the chapter shifting back a verse. Four split one Clementine verse in two: Psalms 15:10, 125:6, and 135:26, and Isaiah 45:23, where the Douay gives "For every knee shall be bowed to me" a number of its own. In Psalm 42 the boundaries cross mid-verse, so Douay 42:4-6 and Clementine 42:4-5 map to each other as a block. The `en-douay-rheims` style is now documented for use with this versification rather than `vulgata`. The divisions were checked against scans of the Benziger (1899) and Murphy (1914) printings, and those in 1 Thessalonians 4, 2 Thessalonians 2, and Amos 9 against a third, the Haydock edition.
- `Versification.is_excluded()` reports a verse that lies within a chapter's range but that the versification does not have, as read from the data's `excludedVerses`, which the loader had ignored. `Versification.first_verse()` gives the verse at which the whole of a chapter begins: its first verse that is not excluded, or 0 where the versification maps an unnumbered psalm title to text in `org`, as `eng` does.
- `vulgata` and `douay-rheims` exclude Psalm 115:1-9 and 147:1-11: the Clementine numbers those psalms 10-19 and 12-20, continuing Psalms 114 and 146.
- `SimpleBibleRef.map_parts()` maps a reference into another versification as a list of references, one for each book it lands in, for a reference that `map()` cannot express as one.

### Changed

- `SimpleBibleRef.map()` and `BibleRef.map_to()` now map whole-chapter references, which had passed through unchanged, so that a renumbered chapter came back under its old number: Vulgate Psalm 50 mapped to `org` Psalm 50 rather than 51, and Vulgate Malachi 4 to a chapter `org` does not have. A whole-chapter range is now mapped through its first and last verses, and stays whole chapters when the result covers whole chapters in the target: Vulgate Psalm 50 is `org` Psalm 51, Psalm 9 is Psalms 9-10, and `org` Malachi 3 is Vulgate Malachi 3-4. Otherwise it becomes a verse range: Vulgate Psalm 115 is `org` Psalm 116:10-19, Malachi 4 is Malachi 3:19-24, and `eng` Genesis 32 is `org` Genesis 32:2-33. Whole-book references still pass through unchanged.
- Validation (`invalid_reason()` and `is_valid()`) now rejects a reference that begins or ends on an excluded verse, such as Vulgate Psalm 147:1 or the NABRE's Matthew 17:21, which had been accepted because they lie within the chapter's verse count. A range may still span an excluded verse.
- `BibleRef.map_to()` now divides a range wherever the book it maps into changes, where it had given a single range running from the start in one book to the end in another. Vulgate Daniel 13:60-65 had mapped to `org` "Sus 60–1"; it is now Susanna 1:60-64 and Bel 1:1. A range that leaves a book and returns is divided too: Vulgate Daniel 3, which carries the Song of the Three at 3:24-90, is `org` Daniel 3:1-23, the Song of the Three, and Daniel 3:24-33. `SimpleBibleRef.map()`, which returns a single reference, returns None for a reference that maps into more than one book.

### Fixed

- The `nabre` versification's list of excluded verses, produced by the versification sniffer, named the verse after each omission rather than the omission itself (Matthew 17:22 for 17:21, John 5:5 for 5:4), missed Mark 11:26 and the whole of Sirach 26:19-27, and listed Job 10:2 and Sirach 41:15, 17, and 21, which the NABRE prints. It is replaced by the 50 omissions confirmed against the NABRE text and a second witness: the sixteen familiar New Testament verses, Tobit 11:12, and 33 verses of Sirach.
- The `eng` versification mapped the unnumbered titles of Psalms 51, 52, 54, and 60 to the second of `org`'s two title verses alone, so `org` 51:1 mapped to `eng` 51:1, which is `org` 51:3. Each title now maps to both.
- The `vulgata` and `douay-rheims` versifications mapped Psalm 12:1 to the Hebrew 13:2 alone, though it holds the title as well, and mapped the Hebrew 13:3 back to Psalm 12:3 alone, though 12:2 and 12:3 together are that verse.
- Where two verses answer to one verse of `org`, several versifications gave each its own one-to-one entry, so the later overwrote the earlier on the way back and the `org` verse mapped to only one of them: `org` Numbers 20:28 mapped to Vulgate 20:29 alone, though the Vulgate divides it as 20:28-29. About fifty such pairs in `vulgata`, `douay-rheims`, `nova_vulgata`, `rsc`, and `rso`, most of them in 1 Esdras, are merged into single range entries, and ranges that met on a shared verse are split around it: Vulgate Psalm 10:1-2 (Hebrew 11:1), `rso` Psalm 89:1-2 (Hebrew 90:1), and the Song of the Three 1:29-30 (Greek Daniel 3:52) in `eng` and `org`. Mapping into `org` is unchanged except for Vulgate Isaiah 9:20, which holds the Hebrew 9:19 and part of 9:20 but had mapped to 9:20 alone.
- The `vulgata` versification mapped Psalm 15:10 to the Hebrew 16:11 alone, though the Clementine's verse holds both 16:10 and 16:11. The Hebrew 16:10 therefore had no Vulgate verse and fell through to Vulgate 16:10, which is the Hebrew 17:10. It now maps to Psalm 15:10.
- References to the Psalms in the plural (`PSAS`, as in "Pss 50:3-5") were not renumbered when mapped, because the mapping data knows the book only as `PSA`: Vulgate Psalms 50:3-5 mapped to `org` Psalms 50:3-5 rather than 51:3-5.
- Formatting a whole-chapter reference to a one-chapter book with a versification left a trailing space ("Jude "); it is now the book name alone.
- The `vulgata` and `douay-rheims` versifications mapped Psalm 55:11 to the Hebrew 56:12 alone, though it holds 56:11 as well, so the Hebrew 56:11 fell through to Vulgate 56:11, a different psalm.
- The `rsc` and `rso` versifications, the same Synodal Psalter with different canons, disagreed with each other and with themselves in three psalms. Both mapped the Hebrew 87:1 back to Psalm 86:2, through an entry for 86:2 that the next entry overrode in the other direction; `rsc` mapped Psalm 89:1, the title, to the Hebrew 90:0, where `org` has no verse, rather than with 89:2 to the Hebrew 90:1; and `rso` mapped the unnumbered title of Psalm 141 to the Hebrew 142:0 rather than 142:1, so the Hebrew 142:1 fell through to `rso` 142:1, which is the Hebrew 143:1. `rso`'s Psalm 114:8, which its own verse count makes the Hebrew 116:8-9, is also mapped to both.

## 0.11.1 - 2026-09-27

### Fixed

- The `nova_vulgata` Psalter carried the Vulgate's psalm numbering, having been copied from `vulgata` wholesale: Psalm 9 ran to 39 verses (the Hebrew 9 and 10 together), Psalm 22 was *Dominus pascit me*, the Miserere was Psalm 50, and every psalm between 10 and 147 was off by one or two. The Nova Vulgata numbers the psalms as the Hebrew does, printing the Vulgate's number in parentheses (`PSALMUS 51 (50)`), and counts titles as verses, so it now agrees with `org` verse for verse and its 174 psalm mappings are gone. Six psalms genuinely divide their verses differently and keep an entry: `12:8`, `44:26` and `150:5` each hold two verses of `org` (its closing pair), `60:12` holds `org` `60:12-13` so that `60:13` is `org` `60:14`, `94:23-24` split `org` `94:23` in two, and Psalm 72 stops at verse 19 because the Nova Vulgata does not print the colophon the Clementine has at 71:20, leaving `org` `72:20` with no Nova Vulgata verse. Counts were taken from the official Latin text at vatican.va; any index built on the old psalm keys is invalidated.
- The `vulgata` and `nova_vulgata` versifications both gave Daniel Weber's chapter lengths (13:65, 14:41) and mapped `DAN 13:65` and `DAN 14:1` alike to `BEL 1:1`, which left every verse of chapter 14 a place behind the Greek and `BEL 1:42` with no Vulgate verse at all. `vulgata` now follows the Clementine, whose chapter 14 has 42 verses: `13:65` is `BEL 1:1`, `14:1-41` are `BEL 1:2-42`, and the Clementine's closing `14:42` ("Tunc rex ait: Paveant omnes...") — which neither Weber nor the Nova Vulgata prints, and which has no Greek counterpart — maps onto `BEL 1:42` beside `14:41`. `nova_vulgata` gets the Nova Vulgata's own division, which moves Weber's `13:65` to the head of chapter 14: Daniel 13 has 64 verses and 14 has 42, answering to Bel verse for verse.
- Susanna and Bel came back from `org` as references to `DAG`, the parallel Greek Daniel that numbers them continuously, rather than to the book a reference would name. Because `DAG` has an abbreviation in only one bundled style, converting `org` `Bel 1:1` into `eng`, `lxx`, `vulgata`, or `nova_vulgata` raised `ValueError: Unknown book ID: DAG` when the result was formatted. A book carrying such a parallel arrangement no longer claims the inverse mapping, so `org` `Bel 1:1` now returns as `Bel 1:1` in `eng` and `lxx`, `Dan 13:65` in `vulgata`, and `Dan 14:1` in `nova_vulgata`.
- The `vulgata` versification gave Genesis 5, John 11, 2 Corinthians 1, and 3 John the Greek's verse counts (32, 57, 24, and 15). The Clementine merges each of those closing verses into the one before, so Genesis 5:31 carries Noah's begetting of Shem, Ham and Japheth, John 11:56 carries the chief priests' order to report where Jesus was, and the two epistles end at 1:23 and 1:14; the chapters now hold 31, 56, 23, and 14 verses and map their last verse to the pair in `org`. `nova_vulgata` divides all four as the Greek does and is unchanged.
- Both Vulgate versifications gave Sirach a 52nd chapter of 13 verses, the *Oratio Salomonis* that the Stuttgart edition appends. Neither the Clementine nor the Nova Vulgata prints it, and Sirach now ends at chapter 51 in both.

## 0.11.0 - 2026-08-13

### Added

- A new book-name set, `en-douay-rheims_abbreviations` (`Jos.`, `1 Par.`, `Ecclus.`, `Apoc.`, …), joins the `en-douay-rheims_names` full names that shipped without any style to reach them. No abbreviation standard for the Douay-Rheims ever existed, so these follow the common Catholic forms of the era; the books of Kings are left unabbreviated (`1 Kings` … `4 Kings`), as the Douay editions leave them.
- A new bundled style, `en-douay-rheims`, formats with those abbreviations and recognizes the full names, as `en-sbl` does (`Jos. 1:1`, `3 Kings 18:20`, `Apoc. 21:1`). It is meant for the `vulgata` versification, whose Esther has no separate `ESG`. Because the editions disagree with each other, it also recognizes the competing abbreviations (`Psal.`, `Eccli.`, `Ezec.`, `Isa.`, `1 Mac.`, `2 Esd.`, `Wisd.`, `Mt.`, …) and the Roman numerals that era used for numbered books (`III Kings`, `I Cor.`, `IV Esd.`). It recognizes `en-sbl_names` as well, so modern names parse too; where the two disagree the Douay-Rheims reading wins, since that is the text being cited: `1 Kings` and `2 Kings` are Samuel, `3 Kings` and `4 Kings` are Kings, and `1 Esdras` and `2 Esdras` are Ezra and Nehemias rather than the apocrypha SBL gives those names to. The SBL abbreviations are deliberately not recognized, because `1 Esd` there and `1 Esd.` here are different books, and a style in which the period decides the book would be a trap.

## 0.10.1 - 2026-07-25

### Fixed

- The `cei` versification's Greek Esther (`ESG`) mappings were copied from `lxx`, which has no `EST` book: there, routing `ESG`'s Hebrew-parallel verses to `org`'s `EST` is sound because nothing else claims them, but `cei` has both books, so `cei` `ESG 1:1` and `cei` `EST 1:1` both mapped to `org` `EST 1:1` while `org`'s own `ESG` went entirely unused. `ESG` now maps to `org`'s `ESG`: Addition A to `ESG 1:1-17` and the Hebrew narrative it displaces to `ESG 1:18-39`, and likewise for the displaced tails of chapters 3, 5, and 8 (`ESG 3:14-15` → `3:21-22`, `5:3-14` → `5:17-28`, `8:13-17` → `8:37-41`). The copied Addition A letters began at `1:1b` and ran one place long, ending in an `ESG 1:1s` that is `1:1r` under another name; they now begin at `1:1a`, and `partialVerses` gains the `a` they imply. Chapters 2, 6, 7, 9, and 10 match `org` verse for verse and need no entries at all.
- `org` numbers the additions to Esther as Swete divides them, which is finer than Rahlfs, whose numbering the `cei` and `lxx` data follow, so fifteen of Rahlfs' verses answer to two or three of `org`'s. Six of them in Addition C (`4:17c`, `d`, `k`, `l`, `n`, `o`), six in Addition D (`5:1a` and `5:1f`, to three verses apiece, plus `5:2a`, `5:2b`, and Addition D's own `5:2`, which is `org` `5:12`), and three in Addition E (`8:12r`, `s`, `u`) now map to ranges instead of to their first verse alone, which had left the rest of each divided verse unmapped. Every verse of `org`'s Greek Esther is now accounted for exactly once in all ten chapters. Two letters were also keyed by Rahlfs' alphabet rather than the CEI's, which skips only `j`: `cei`'s `ESG 4:17w` and `ESG 8:12x` are renamed `4:17v` and `8:12v`.
- Loading a `mappedVerses` entry whose source and target ranges differ in length dropped the subverse from a side that is a single verse, so the entry was keyed on the base verse and captured it: `"ESG 8:12u": "ESG 8:34-35"` sent plain `ESG 8:12` to `8:34-35` instead of leaving it at `8:12`. A side that is a single verse now keeps its subverse, as the equal-length branch already did.

## 0.10.0 - 2026-07-20

### Changed

- `SimpleBibleRef.range_keys` and `BibleRef.range_keys` now give an inserted verse — such as a Greek addition to Esther (`ESG 4:17k`, which follows but is not part of `ESG 4:17`) — an integer key distinct from, and correctly ordered against, its base verse. Each key gains a two-digit least-significant field for the subverse ordinal, so the layout is now `BB CCC VVV SS` (ten digits instead of eight); the ordinal comes from a new `Versification.partial_ordinal()`, which reads the versification's `partialVerses` table. Because the ordinal is driven by that table, a subverse cited on a verse that is *not* followed by inserted verses — a portion of a single verse, such as a scholarly `Rom 8:1a` — collapses to the base verse's key rather than being mistaken for an insertion. A range end that spreads to a whole verse (a whole chapter or book, or `ff`) carries the maximal ordinal so that it includes that verse's inserted verses. Widening every key by two digits is a breaking change for any index built on the previous eight-digit keys.
- The `en-bibleworks` style now gives the LXX alternate-version books — the alternate Greek translations, such as Theodotion's — their own BibleWorks abbreviations in its book-name set: `Dng` (`DAG`), `Jsa` (`JSA`), `Tbs` (`TBS`), `Sut` (`SST`), `Dat` (`DNT`), and `Bet` (`BLT`). These replace the style's `also_recognize` aliases that had folded those abbreviations into the common books they parallel. As a result `Jsa`, `Tbs`, `Sut`, `Dat`, and `Bet` now resolve to the alternate-version book IDs (`JSA`, `TBS`, `SST`, `DNT`, `BLT`) instead of `JOS`, `TOB`, `SUS`, `DAG`, and `BEL`; only `Jda` (`JDG`) remains an alias.

## 0.9.0 - 2026-07-20

### Added

- A new `RefStyle` option, `chapter_letters`, maps a book ID to the letters that serve as its chapter numbers, as the NABRE prints the Additions to Esther (`Est A` through `Est F`, chapters 1–6 of `ESG` in the `nabre` versification). A lettered book takes the name of the book it may share a name with (`ESG` takes `EST`'s name, via the new `RefStyle.book_name()` method), so parsers resolve any recognized Esther name followed by a letter chapter to `ESG` while numeric chapters keep resolving to `EST`; `format_chapter()` accepts an optional book ID and renders letters for a lettered book, raising `ValueError` for a chapter beyond the letter list.
- A new bundled style, `en-nabre`, extends `en-sbl` with the NABRE's Esther chapter letters and also recognizes the CMOS name sets.
- The `nabre` versification now maps its lettered `ESG` chapters to their integrated Greek Esther positions (e.g. `C:12`, the start of Esther's prayer, ↔ `ESG 4:29` in `org`/`eng` and `EST 14:1` in `vulgata`), so `map_verse` converts lettered references to and from other versifications instead of passing their coordinates through unchanged.

### Fixed

- The `nabre` versification gave Addition D of Esther (`ESG` chapter 4) 15 verses; the NABRE text has 16.
- The versification data now addresses the integrated Greek Esther (`ESG`) in org with a single coordinate convention. The `eng` data mapped its `ESG` verses to LXX-style subverse coordinates (`ESG 1:1a` … `10:3l`) while the `vulgata` (and new `nabre`) data target the plain integrated coordinates that org's `maxVerses` describe, so the two sides could not interoperate: `vulgata` `Esther 13:1` (the first royal letter) mapped into `eng` as Hebrew `ESG 3:21`, and `eng` additions mapped into `vulgata` not at all. The plain convention is now canonical: `eng`'s 110 `ESG` entries reduce to one (its Addition A has 18 verses where org has 17, so `eng` `ESG 1:18` merges with `1:17`), and `rso`'s — which were copies of `eng`'s referencing verses beyond its own Hebrew-shaped `ESG` — are replaced with the lxx-style mapping of its Hebrew-parallel verses to `EST`.
- The `cei` versification's verse mappings were stored under a misspelled key (`verseMappings` instead of `mappedVerses`), so they were silently ignored: references to the Daniel additions, the Letter of Jeremiah, and the other remapped passages passed through `map_verse` unmapped.
- Vulgate Esther references to the Greek additions now map to their correct integrated Greek Esther (`ESG`) positions. The printed Vulgate gathers the additions at the end as chapters 10:4-16, but the mapping data placed them naively (e.g. `EST 13:1-18` → `ESG 4:1-18`), so `map_verse` sent them — and the Hebrew verses they displace — to the wrong verses (`vulgata` `Esther 13:8` resolved to Hebrew Esther 4:8 instead of the start of Mordecai's prayer at `ESG 4:18`). Each addition (A–F), its colophon, and the displaced Hebrew tails of chapters 1, 3, 5, and 8 now map to the correct `ESG` verse. The `org` and `eng` `ESG` maxVerses were extended to 41 (ch. 8) and 14 (ch. 10) to accommodate the tails, reconciling the `eng` counts with the `eng.vrs` mapping lines that already referenced them.
- The `lxx` versification did not map the Greek Esther additions. Its `ESG` numbered verses (the Hebrew-parallel narrative) map to `org`'s Hebrew `EST`, but the additions — carried as subverses on anchor verses (`1:1b`–`1:1s`, `3:13a`–`g`, `4:17a`–`z`, `5:1a`–`f` and `5:2a`–`b`, `8:12a`–`x`, `10:3a`–`l`) — had no mapping, so a reference such as the start of Mordecai's prayer at LXX `Esther 4:17a` fell through to a spurious `EST 4:17a` instead of the integrated `ESG 4:18`. Each addition subverse now maps to its integrated `org` `ESG` position, so `4:17a` ↔ `org ESG 4:18` ↔ `vulgata Esther 13:8` ↔ `nabre C:1`, interoperating with the other versifications. Where the continuous `ESG` numbering subdivides a single Greek subverse into several verses, the subverse maps to the first; the Hebrew-parallel numbered verses are unchanged.
- The `cei` versification carried no Greek Esther additions at all: it declared no `ESG` subverses and no `ESG` mappings, and its `ESG` chapter 3 was stored with 13 verses where the CEI text has 15 (verses 14–15 follow the Addition B subverses `3,13a`–`g`). The seven addition anchors are now declared as partial verses and mapped exactly as in `lxx` — the Hebrew-parallel numbered verses to `org`'s `EST` and each addition subverse to its integrated `ESG` position — and the chapter-3 count is corrected, so a CEI reference such as `Est 4,17a` resolves like the others.

### Removed

- The `ethiopian_custom` versification data file, whose upstream JSON conversion was malformed. It was already excluded from the built package (#27); the file, its build exclusion in `pyproject.toml`, and its README attribution are now removed.

## 0.8.1 - 2026-07-15

### Added

- `invalid_reason()` methods on `VerseRange`, `SimpleBibleRef`, and `BibleRef`, each returning a human-readable explanation of why a reference is invalid, or `None` if it is valid. Messages name the offending part (e.g. `John has no chapter 30 (only 21 chapters)`, `Ps 2 has no verse 99 (only 12 verses)`); an optional `RefStyle` supplies reader-facing book names. The existing `is_valid()` methods now delegate to these, so a boolean check and its explanation cannot diverge.

## 0.8.0 - 2026-07-15

### Added

- Latin support. Two new bundled styles: `la-cce`, using the abbreviations of the Latin editio typica of the Catechismus Catholicae Ecclesiae with Arabic chapter numbers (e.g. `Io 3, 16`), and `la-vetus`, using the traditional abbreviations of the Patrologia Latina era with uppercase Roman-numeral chapters (e.g. `Joan. III, 16`) and recognizing many variant spellings (`Ioan.`, `Io.`, `Ps.`, `Psalm.`, `Matt.`, …). Three new book-name sets back them: `la-cce_abbreviationes`, `la-vetus_abbreviationes`, and `la-nomina` (full Latin names).
- A new `RefStyle` option, `chapter_number_style`, controls how chapter numbers are parsed and formatted: `"arabic"` (default), `"roman"` (uppercase, e.g. `XLIV`), or `"roman-lower"` (e.g. `xliv`). Verse numbers are always Arabic.

### Fixed

- A reference no longer continues across a blank line. Previously a separator could reach past a paragraph break, so a citation-ending period followed by a footnote or paragraph number (e.g. `Gen. XXII, 18.` at the end of a paragraph, with `2` starting the next) was scanned as additional verses. A single newline inside a reference — as produced by word-wrapping — still parses as before.
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
