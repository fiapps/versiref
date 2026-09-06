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

Present in several data files and **not read by the loader**.
Do not rely on it for anything.

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

## Sources

- Rahlfs–Hanhart, *Septuaginta* (Deutsche Bibelgesellschaft, 2006) — the numbering most editions follow.
- H. B. Swete, *The Old Testament in Greek According to the Septuagint* (Cambridge, 1909) — the numbering `org` follows.
- The `vulgata` data in this package, which is an independent witness to the addition boundaries in `org`.
- [vatican.va](https://www.vatican.va/archive/bible/nova_vulgata/documents/nova-vulgata_vt_psalmorum_lt.html) for the Nova Vulgata's Psalter, which it carries on one page, verse numbers and all.
- [bibbiaedu.it](https://www.bibbiaedu.it/) for the CEI 2008 text, which prints the addition letters and the variant markers.
- The versification files themselves come from the UBSCAP repository (see `LICENSE-DATA`), and reproduce its errors as well as its data.
