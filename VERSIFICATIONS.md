# Notes for Versification Data

These are working notes for anyone writing or correcting the JSON versification data in `src/versiref/data/versifications/`.
They record how the data is interpreted and what the harder texts actually look like, which is not deducible from the files themselves.
This file is not packaged and is not part of the user documentation; it exists so that knowledge which took real effort to recover is not lost.

## How the JSON is interpreted

### `maxVerses`

The last verse number of each chapter of each book, as a list per book.
The order of the keys defines the book order, which is what gives each book its number in a verse key.

### `mappedVerses`

Every mapping runs through `org` as an intermediary: a versification says how it differs from `org`, and `map_verse` composes the two halves.
So an entry's target is almost always an `org` coordinate, not a coordinate in some third versification.

Three things about this are easy to get wrong.

**A location with no entry maps to itself.**
Absence does not mean "unknown", it means "identical".
This is the usual source of silent corruption: dropping a wrong entry does not leave a gap, it asserts an identity that may be just as wrong.
When a chapter's verses shift, every one of them needs an entry, not only the ones that look interesting.

**Counts decide the shape of the mapping.**
When the source and target ranges have the same length, the entry expands to that many one-to-one mappings.
When the lengths differ, the whole source range maps to the whole target range, and the mapping is marked as not one-to-one so that a portion-of-a-verse subverse (a scholarly `Rom 8:1a`) is discarded rather than carried across a join it cannot survive.

**A side that is a single verse keeps its subverse.**
`"ESG 8:12u": "ESG 8:34-35"` maps the inserted verse `8:12u`, not the base verse `8:12`.
This matters because such an entry would otherwise be keyed on the base verse and capture it.

### `partialVerses`

Lists the parts of a verse that is followed by inserted verses, such as the Greek additions to Esther.
Each entry is a list whose position gives the sort ordinal: `"-"` is the base verse and the letters follow it.
The ordinal becomes the last field of the integer verse key, which is what lets an inserted verse sort after its base verse and before the next verse.

A subverse cited on a verse that is *not* listed here is treated as a mere portion of that verse and shares the base verse's ordinal, so it collapses onto the same key.
That distinction is the whole point of the table: `ESG 4:17k` is a verse in its own right, while `Rom 8:1a` is half of a verse.

**Known limitation.**
The base verse's ordinal is fixed at 0, so inserted verses always sort *after* it.
Addition A to Esther precedes the Hebrew 1:1, and the CEI prints it that way (`1:1a`–`1:1r`, then `1:1`), but a verse key cannot express that and `1:1` sorts first.
This is accepted rather than special-cased; `nabre` has related trouble placing its insertions.

### `excludedVerses`

A list of verses, or ranges of verses (`"PSA 147:1-11"`), that lie within a chapter's `maxVerses` but that the versification does not have.
Two kinds of verse belong here, and they need not be told apart:

- a verse omitted for text-critical reasons, whose number the edition skips (the NABRE's Matt 17:21);
- a number the numbering never uses, because a chapter does not begin at verse 1 (the Clementine's Ps 115 begins at verse 10 and Ps 147 at verse 12, continuing Ps 114 and 146).

An excluded verse fails validation when a range begins or ends on it, though a range may span one (the NABRE's Tob 11:11-13).
A whole chapter is taken to begin at its first verse that is not excluded, which is what lets Vulgate Ps 147 map to `org` 147:12-20 rather than to the whole Hebrew psalm.
Mapping is not otherwise affected: `map_verse` maps an excluded verse like any other, so that a text can still be shoehorned into the nearest versification the package offers.

#### The NABRE's list

The list first shipped with `nabre` came from the versification sniffer, and was wrong in a way worth knowing about: the sniffer recorded the verse *after* each run of missing verses, not the missing verse.
Every New Testament entry was one too high (Matt 17:22 for 17:21, John 5:5 for 5:4), a run of two got a single entry (Sir 11:17 for 11:15-16), and a run ending a chapter got none (Sir 26:19-27 was absent).
It also missed Mark 11:26 and listed Job 10:2 and Sir 41:15, 17, and 21, all of which the NABRE prints; Sirach 41 is a chapter the NABRE rearranges.

The present list was rebuilt from the NABRE Bible database, which stores a verse the edition does not print as an empty row.
That signal is good but not perfect: Wis 4:15 is empty only because its text was run into 4:14, and Matt 18:11 and Rom 16:24 hold a stray bracket instead of nothing.
So a verse was admitted only with a second witness:
the sixteen New Testament verses are the familiar text-critical omissions, which the database reproduces exactly;
Tob 11:12 and the Sirach verses are empty or missing in at least one of the NETS, NRSV, and RSV-CE databases as well, those editions also treating Sirach's expanded Greek text as secondary.
Five empty rows have no such witness and are left out: Tob 14:8, 1 Macc 9:34, Wis 4:15 (the artifact above), and Sir 12:7 and 37:21.
An omission left out costs nothing, since validation then accepts the number as it always did; a wrong entry would reject a real citation.

## Mapping pitfalls from the `.vrs` conversion

The upstream data was converted from Paratext `.vrs` files, whose mapping lines each pair one verse with one verse.
Where one verse answers to two, the conversion sometimes wrote two separate one-to-one entries rather than one range.
Both mistakes below are the same shape, and both leave the forward direction looking right.

**Two entries sharing a target.**
`"PSA 12:2": "PSA 13:3"` and `"PSA 12:3": "PSA 13:3"` map both Vulgate verses to the Hebrew 13:3, but on the way back the later entry overwrites the earlier, so the Hebrew 13:3 returns to 12:3 alone.
The fix is one entry, `"PSA 12:2-3": "PSA 13:3"`.
The pattern is easy to find by grouping one-to-one entries by their target, and as of this writing it remains in about fifty places in `vulgata` and `nova_vulgata` (mostly 1 Esdras) and a few in `lxx`, `rsc`, and `rso`.
The one intended instance is the Clementine's Dan 14:42, described below.

**A verse that is two, mapped to one.**
`eng` mapped the unnumbered title of Ps 51 (its verse 0) to `org` 51:2, but `org`'s title is two verses, 51:1-2; with no entry of its own, `org` 51:1 fell through to `eng` 51:1, which is `org` 51:3.
The same held for Ps 52, 54, and 60, the four psalms whose Hebrew title runs to two verses, and for the Clementine's Ps 12:1, which holds the title and the first line and so is the Hebrew 13:1-2.
Whole-chapter mapping exposes this kind of error, since it maps a chapter through its first verse.

## Greek Esther

Greek Esther (`ESG`) is the most intricate data in the package, and the sources disagree in ways that are invisible until the verses are counted.

### `org`'s `ESG` follows Swete, not Rahlfs

`org` numbers Greek Esther continuously, with the six additions in place rather than gathered at the end.
The numbering follows **Swete**, who divides the additions into more verses than **Rahlfs** does.
Most modern editions — and the CEI — follow Rahlfs, so a Rahlfs verse sometimes answers to two or three of `org`'s.
This is why `org`'s chapter totals look too large: chapter 4 has 47 verses and chapter 8 has 41.

The additions sit as follows.
Every boundary below is independently corroborated by the `vulgata` data, which reaches the same `ESG` verses from the Vulgate's own chapters 11–16.

| Addition | `org` `ESG` | Rahlfs | Verses to fill | Splits |
| --- | --- | --- | --- | --- |
| A | 1:1-17 | `1:1a`–`1:1r` | 17 | none |
| B | 3:14-20 | `3:13a`–`3:13g` | 7 | none |
| C | 4:18-47 | `4:17a`–`4:17z` | 30 | 6 |
| D | 5:1-16 | `5:1`, `5:1a`–`f`, `5:2`, `5:2a`–`b` | 16 | 6 |
| E | 8:13-36 | `8:12a`–`8:12x` | 24 | 3 |
| F | 10:4-14 | `10:3a`–`10:3l` | 11 | none |

The Hebrew narrative that each addition displaces follows it:
1:1-22 → `org` 1:18-39, 3:14-15 → 3:21-22, 5:3-14 → 5:17-28, 8:13-17 → 8:37-41.
Addition A is the odd one, in that it comes *before* the Hebrew 1:1 rather than after.

### Letter alphabets

The letters skip `j` everywhere, so the sequence runs `…h, i, k, l…`.

Rahlfs skips more than that, and not consistently: he has no `4:17v`, and no `8:12v` or `8:12w`.
Editions that follow him without reproducing his gaps therefore disagree with him by one or two letters near the end of an addition.
The CEI skips only `j`, so:

| CEI | Rahlfs |
| --- | --- |
| `4:17v` | `4:17w` |
| `8:12v` | `8:12x` |

The `lxx` data uses Rahlfs' letters; `cei` uses the CEI's.
The two therefore need the same targets under different keys, which is a standing trap when copying entries between them.

### Where Swete divides a verse that Rahlfs does not

These were established by aligning Swete's Greek against Rahlfs' word by word and attributing each Swete verse to the Rahlfs verse holding most of its words.

| Rahlfs | Swete | `org` |
| --- | --- | --- |
| `4:17c` | C:3–4 | 4:20-21 |
| `4:17d` | C:5–6 | 4:22-23 |
| `4:17k` | C:12–13 | 4:29-30 |
| `4:17l` | C:14–15 | 4:31-32 |
| `4:17n` | C:17–18 | 4:34-35 |
| `4:17o` | C:19–20 | 4:36-37 |
| `5:1a` | D:2–4 | 5:2-4 |
| `5:1f` | D:9–11 | 5:9-11 |
| `5:2a` | D:13–14 | 5:13-14 |
| `5:2b` | D:15–16 | 5:15-16 |
| `8:12r` | E:17–18 | 8:29-30 |
| `8:12s` | E:19–20 | 8:31-32 |
| `8:12u` | E:22–23 | 8:34-35 |

Note that `5:2` is Addition D's own verse, not the Hebrew 5:2; it is `org` 5:12 and needs an explicit entry, since identity would send it to `org` 5:2, which belongs to `5:1a`.

One boundary is a judgement call rather than a fact.
Rahlfs ends `4:17k` in the middle of Swete's C:14: `4:17k` closes with the words that open C:14, and `4:17l` carries the rest of C:14 together with all of C:15.
C:14 is assigned to `4:17l`, which holds nineteen of its twenty-six words against `4:17k`'s six.
The Vulgate agrees that the preceding boundary is real, beginning its chapter 14 — Esther's prayer — at `org` 4:29, which is where `4:17k` starts.

### A versification with both `ESG` and `EST`

`lxx` has only one Esther, so routing its `ESG` narrative verses to `org`'s Hebrew `EST` is sound: nothing else claims them.
A versification that has *both* books cannot do this.
`cei` has both, and inherited `lxx`'s entries wholesale, so `cei` `ESG 1:1` and `cei` `EST 1:1` both landed on `org` `EST 1:1` while `org`'s `ESG` went entirely unused.
When adapting Esther data from `lxx`, the base-verse entries are exactly the ones that must be reconsidered; the lettered ones usually carry over unchanged.

### Checking the work

Greek Esther is worth a stronger check than spot tests, because its errors are arithmetic rather than obvious.
For each chapter, map every slot the versification declares — each base verse plus its `partialVerses` letters — and confirm that the resulting `org` verses tile the chapter exactly: every verse covered, none covered twice.
`tests/test_versification.py::test_cei_greek_esther_covers_org_exactly_once` does this for `cei`.
A collision means two slots claim one verse; a gap means real text has nowhere to go.
Both are the signature of an incomplete mapping rather than a merely inaccurate one.

## The Nova Vulgata's Psalter

The Nova Vulgata numbers the psalms as the Hebrew does, not as the Greek and the old Vulgate do.
Its headings print the Hebrew number and the Vulgate's in parentheses — `PSALMUS 51 (50)`, `PSALMUS 10 (Vg 9, 22-39)`, `PSALMUS 116 (114, 1-9; 115)` — so the Miserere is Psalm 51, the Hebrew 9 and 10 stand apart, and 114/115 and 146/147 are not joined the way the Vulgate joins them.
Titles count as verses, as they do in the Hebrew and in the Vulgate, so `nova_vulgata` and `org` agree verse for verse and the Psalter needs almost no `mappedVerses` at all.
There are 150 of them: the Nova Vulgata's [appendix](https://www.vatican.va/archive/bible/nova_vulgata/documents/nova-vulgata_appendix_lt.html) holds only the Tridentine decrees and the Clementine preface, so it has no Psalm 151.

The data shipped here was copied from `vulgata` wholesale, which gave the Nova Vulgata the Greek numbering throughout: Psalm 9 ran to 39 verses, Psalm 22 was *Dominus pascit me*, and every psalm from 10 to 147 was off by one or two.
Because absence means identity, the fix was mostly deletion: the 174 psalm entries went, and only the six psalms below need to say anything.

### The six psalms that divide their verses differently

| Psalm | Nova Vulgata | `org` | |
| --- | --- | --- | --- |
| 12 | 8 | 9 | `12:8` is `org` `12:8-9` |
| 44 | 26 | 27 | `44:26` is `org` `44:26-27` |
| 60 | 13 | 14 | `60:12` is `org` `60:12-13`, and `60:13` is `org` `60:14` |
| 72 | 19 | 20 | the colophon `org` `72:20` is not printed |
| 94 | 24 | 23 | `org` `94:23` is split into `94:23-24` |
| 150 | 5 | 6 | `150:5` is `org` `150:5-6` |

Five of the six join a pair of Hebrew verses; only Psalm 94 goes the other way.
The joins fall at the end of the psalm except in Psalm 60, where the join is at verse 12 and the last verse shifts.
Psalm 72 is the one that is neither a join nor a split: the Nova Vulgata simply does not print "Defecerunt laudes David filii Iesse", which the Clementine has at 71:20, so `org` `72:20` has nowhere to go and `map_verse` returns `None` for it.

Counts alone were not enough to establish this: they say a psalm differs, not where.
Each join was located by reading the Latin of the divergent verse and finding both Hebrew verses inside it.
`vulgata` is a useful second witness, since it reaches the same psalms by the Vulgate's numbers, and it agrees at 44 and 150.

## The Vulgates' Daniel

The Vulgate tradition puts Susanna and Bel inside Daniel as chapters 13 and 14, and the editions do not agree on where the seam falls.

| | Dan 13 | Dan 14 | Bel 1 is |
| --- | --- | --- | --- |
| Weber (Stuttgart) | 65 | 41 | `DAN 13:65` |
| Clementine (`vulgata`) | 65 | 42 | `DAN 13:65` |
| Nova Vulgata (`nova_vulgata`) | 64 | 42 | `DAN 14:1` |

Weber closes chapter 13 with the verse the Greek counts as `BEL 1:1` ("Et rex Astyages appositus est ad patres suos"), so his chapter 14 runs a verse behind the Greek throughout.
The Nova Vulgata moves that verse to the head of chapter 14, which makes its chapter 14 answer to Bel verse for verse and its chapter 13 one verse shorter.
The Clementine follows Weber and adds a closing `14:42` ("Tunc rex ait: Paveant omnes habitantes in universa terra Deum Danielis") that neither of the others prints; having no Greek counterpart, it is mapped onto `BEL 1:42` alongside `14:41`, and is listed *before* the range entry so that the range keeps the way back.

The upstream UBSCAP data gave both files Weber's chapter lengths and mapped `DAN 13:65` and `DAN 14:1` alike to `BEL 1:1`, which left everything after it a verse out and `BEL 1:42` unreachable.

### `DAG` is not org's way back

Several versifications carry `DAG`, a parallel Greek Daniel that numbers Susanna, the Song of the Three and Bel continuously, beside their ordinary `DAN`.
Its entries reach the same `org` verses as `DAN`'s, so on the inverse mapping it would capture them, and `org` `BEL 1:1` came back as `DAG 14:1` — a reference almost no style can even name.
`_PARALLEL_BOOKS` in `versification.py` keeps such a book out of the inverse mapping entirely: it maps into `org` like any other, but an `org` verse returns to the book that references actually name.

## Verses the Clementine merges

The Clementine ends four chapters a verse earlier than the Greek, joining the closing verse to the one before: Genesis 5:31 carries Noah's begetting of Shem, Ham and Japheth (`org` 5:32), John 11:56 carries the chief priests' order (`org` 11:57), 2 Corinthians 1:23 carries `org` 1:24, and 3 John 14 carries `org` 15.
The Nova Vulgata divides all four as the Greek does, so these are among the few places where the two Vulgate files must differ outside Esther, Daniel, and the Psalter.

John 11 took two passes to settle, and the reason is worth recording.
A Bible database is a witness to its own digitization as much as to its edition, so a database that disagrees with the printed editions is the thing to doubt — but which database is the outlier is not obvious from inside.
Here the Latin Clementine and the Douay agreed on the merge against one electronic Vulgate that split the verses; scans of three printed editions settled it for the merge.
Counting witnesses is not enough when they may descend from one another: prefer a scan of a printed edition, and treat any single electronic text as one witness however authoritative its packaging looks.

## The Douay-Rheims

Challoner's Douay-Rheims is translated from the Clementine and follows its chapters, its psalm numbering, its Daniel seam, and the four merged closing verses above.
It departs from the Clementine's verse divisions in fifteen chapters, so `douay-rheims` is a copy of `vulgata` with those chapters rewritten and nothing else changed.

| Chapter | Clementine | Douay | |
| --- | --- | --- | --- |
| 2 Sa 13 | 39 | 38 | `13:38` is Clementine `13:38-39` |
| Ps 15 | 10 | 11 | Clementine `15:10` is split into `15:10-11` |
| Ps 19 | 10 | 9 | `19:9` is Clementine `19:9-10` |
| Ps 28 | 11 | 10 | `28:10` is Clementine `28:10-11` |
| Ps 42 | 5 | 6 | the boundaries cross; see below |
| Ps 125 | 6 | 7 | Clementine `125:6` is split into `125:6-7` |
| Ps 135 | 26 | 27 | Clementine `135:26` is split into `135:26-27` |
| Ps 150 | 6 | 5 | `150:5` is Clementine `150:5-6` |
| Isa 45 | 25 | 26 | Clementine `45:23` is split into `45:23-24`, and the rest shift up |
| Isa 46 | 13 | 12 | `46:11` is Clementine `46:11-12`, and `46:12` is `46:13` |
| Amos 9 | 15 | 14 | `9:14` is Clementine `9:14-15` |
| Jdt 4 | 17 | 16 | `4:5` is Clementine `4:5-6`, and the rest shift back |
| Sir 29 | 35 | 34 | `29:16` is Clementine `29:16-17`, and the rest shift back |
| 1 Th 4 | 18 | 17 | `4:11` is Clementine `4:11-12`, and the rest shift back |
| 2 Th 2 | 17 | 16 | `2:10` is Clementine `2:10-11`, and the rest shift back |

The Douay's split of Ps 15 restores the Hebrew division, so its Ps 15 answers to `org`'s Ps 16 verse for verse; it is the Clementine that joins them.
Its split of Ps 135 does not: the Clementine's 135:26 ends with a line from the Greek ("Confitemini Domino dominorum…") that the Hebrew lacks, and the Douay numbers it 27, so both 26 and 27 map onto `org` 136:26, as the Clementine's extra Dan 14:42 does onto `BEL 1:42`.

In Ps 42 the Douay divides verses 4 and 5 mid-verse: its 42:4 is the first half of the Clementine's 4, its 42:5 is the second half of 4 with the first half of 5 ("To thee, O God my God, I will give praise upon the harp: why art thou sad, O my soul?"), and its 42:6 ("Hope in God") is the rest of 5.
A mapping cannot end partway through a verse, so Douay `42:4-6` maps to `org` `43:4-5` as a single block: never wrong in either direction, but coarser than the text.
Finer entries (Douay 4 → `org` 4, 5 → 4-5, 6 → 5) cannot work, because each later entry overwrites the reverse mapping of the verses it shares with an earlier one, so one direction always comes out wrong.

`vulgata` has no Tobit, Judith, or Sirach mappings at all, although the Vulgate's text of these books differs from the Greek and its chapter lengths rarely agree with `org`'s.
This is deliberate upstream: Paratext's [`vul.vrs`](https://github.com/ubsicap/versification_json/blob/master/examples/vul.vrs), from which `vulgata` was converted, notes at line 12 "No mapping done for TOB, JDT and SIR, since they seem to follow another 'vorlage' than LXX."
Those books are therefore mapped as identity, and `org`'s coordinates stand in for the Clementine's own.
The Douay's Jdt 4 and Sir 29 entries accordingly target the Clementine's verse numbers, even where they run past `org`'s last verse (`org` Jdt 4 has 15).
Douay↔Clementine conversion is exact there, and Douay↔`org` is exactly as good as `vulgata`'s, which is to say not good.
Fixing it would mean establishing the correspondence verse by verse, by comparing the Vulgate's text of the three books against Swete's, which `org` follows; that would fix both files at once.

The boundaries were found by comparing a BibleWorks export of the 1899 American edition against `vulgata`, then confirmed in the OCR text of two scanned printings (Benziger 1899 and Murphy 1914), which agree with each other and with the export.
The page images were not consulted.
1 Th 4, 2 Th 2, and Amos 9 were also checked by hand in a third printing, the Douay-Rheims with Haydock's commentary, which settles that the divergences belong to the Douay and not to any one printing.
Ps 28 rests on Benziger alone, because Murphy's OCR is unreadable there (as it is at Amos 9, which Haydock now corroborates); the printed 12 of Isa 46 and the printed 5 of Ps 42 were likewise seen only in Benziger, and the printed 27 of Ps 135 only in Murphy.

The export also numbers Ps 115 and Ps 147 differently, but there the export is wrong: both printings number Ps 115 as 10–19 and Ps 147 as 12–20, continuing Ps 114 and Ps 146 exactly as the Clementine does.
Do not "correct" the Douay's Psalter to match that export.

Comparing the two also exposed an error in `vulgata`'s Ps 15, which the Douay splits: the Clementine's 15:10 holds both `org` 16:10 ("thou wilt not leave my soul in hell") and 16:11 ("thou hast made known to me the ways of life"), but was mapped to 16:11 alone, so `org` 16:10 fell through to Vulgate 16:10, which is the Hebrew 17:10.

## Sources

- Rahlfs–Hanhart, *Septuaginta* (Deutsche Bibelgesellschaft, 2006) — the numbering most editions follow.
- H. B. Swete, *The Old Testament in Greek According to the Septuagint* (Cambridge, 1909) — the numbering `org` follows.
- The `vulgata` data in this package, which is an independent witness to the addition boundaries in `org`.
- [Scanned pages from various editions](https://sacredbible.org) of the Clementine Vulgate (1914, M. Hetzenauer ed.; 1861, C. Vercellone ed.; 1590–1599 editions compiled by L. van Ess ed.).
- *The Holy Bible, Translated from the Latin Vulgate* (Douay-Rheims, Challoner revision; New York: Benziger Brothers, 1899), scanned at the Internet Archive as [`holybibletransla00denv`](https://archive.org/details/holybibletransla00denv).
- The same (Baltimore: John Murphy Co., 1914), the publisher of the 1899 American edition, scanned from a University of Toronto copy as [`holybibletransl00balt`](https://archive.org/details/holybibletransl00balt).
- The Douay-Rheims with Haydock's commentary, scanned at the Internet Archive as [`douay-rheims-bible-with-haydock-commentary-complete`](https://archive.org/details/douay-rheims-bible-with-haydock-commentary-complete).
- P. Michael Hetzenauer's 1914 Clementine, pp. 549 and 564, for the Clementine's numbering of Ps 115 and 147, and the Tweedale Clementine text.
- [vatican.va](https://www.vatican.va/archive/bible/nova_vulgata/documents/nova-vulgata_vt_psalmorum_lt.html) for the Nova Vulgata's Psalter, which it carries on one page, verse numbers and all.
- [bibbiaedu.it](https://www.bibbiaedu.it/) for the CEI 2008 text, which prints the addition letters and the variant markers.
- The versification files began as conversions from the UBSCAP repository (see `LICENSE-DATA`).
  Many of its errors have since been corrected, as recorded above and in `CHANGELOG.md`, but a book not discussed here should be presumed to be as UBSCAP left it, errors included.
