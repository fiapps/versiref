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

## Sources

- Rahlfs–Hanhart, *Septuaginta* (Deutsche Bibelgesellschaft, 2006) — the numbering most editions follow.
- H. B. Swete, *The Old Testament in Greek According to the Septuagint* (Cambridge, 1909) — the numbering `org` follows.
- The `vulgata` data in this package, which is an independent witness to the addition boundaries in `org`.
- [bibbiaedu.it](https://www.bibbiaedu.it/) for the CEI 2008 text, which prints the addition letters and the variant markers.
- The versification files themselves come from the UBSCAP repository (see `LICENSE-DATA`), and reproduce its errors as well as its data.
