# Command-Line Interface

VersiRef installs a `versiref` command. It is a click group; run `versiref
--help` to list subcommands, `versiref COMMAND --help` for one command, or
`versiref --version` for the installed version.

The commands fall into two families: **introspection** (`list ...`) and
**reference operations** (`parse`, `validate`, `convert`, `scan`). Every
operation command accepts `--json` for machine-readable output and sets a
meaningful exit status, so the tool composes in scripts and is friendly to
language-model callers.

## Common options

Parsing a reference needs both a **style** (which book names and separators to
recognize) and a **versification** (which defines single-chapter books and what
counts as in range). The operation commands therefore share:

- `--style NAME` — the reference style to parse with. Default `en-cmos_short`.
  See `versiref list styles`. Note that styles differ in spelling: `en-sbl`
  recognizes `Gen` and `John`, while `en-cmos_short` recognizes `Gn`/`Gen.` and
  `Jn`. Pick the style that matches your input.
- `-v, --versification NAME` — the versification to parse/validate in. Default
  `eng`. See `versiref list versifications`.
- `--out-style NAME` — the style used to render output (defaults to `--style`).
- `--also-recognize SET` — pull in an extra book-name set (repeatable), e.g. to
  recognize abbreviations the base style lacks. See `versiref list book-names`.

## `docs`

Print the filesystem path to the documentation bundled inside the installed
package, resolved with `importlib.resources` (correct for wheel and editable
installs).

```sh
versiref docs            # path to the bundled docs directory
versiref docs api.md     # path to a single bundled doc
```

The bundled files are `index.md` (a copy of the README), `api.md` (the generated
API reference), and `cli.md` (this document).

## `list`

List what the bundled data offers. Each subcommand takes `--pattern` (an
fnmatch-style glob) and `--json` (emit a JSON array instead of one name per
line).

```sh
versiref list styles --pattern 'en-*'
versiref list versifications
versiref list book-names --pattern 'it-*'
```

## `parse`

Parse a single reference and print it normalized, or — with `--json` — emit its
structured book/chapter/verse breakdown.

```sh
versiref parse "Jn 3:16-18" --style en-cmos_short
versiref parse "Ps 119:1ff" --json
```

Exit status: `0` parsed, `2` unparseable.

## `validate`

Check whether a reference both parses and exists in the versification.

```sh
versiref validate "Gen 1:31" --style en-sbl -v eng   # valid
versiref validate "Gen 1:99" --style en-sbl -v eng   # out of range
```

Exit status: `0` valid, `1` parses but out of range, `2` unparseable. Useful for
a caller checking its own citations.

## `convert`

Map a reference from one versification (`--from`) into another (`--to`) — for
example the Psalm numbering shift between the Septuagint, the Hebrew/English
tradition, and the Vulgate.

```sh
versiref convert "Ps 50:3" --style en-sbl --from lxx --to eng       # -> Ps 51:1
versiref convert "Ps 51:3" --style en-sbl --from eng --to vulgata   # -> Ps 50:5
```

Reformatting a reference between styles is the same operation with `--from`
equal to `--to` and a differing `--out-style`. Exit status: `0` ok, `1` not
representable in the target, `2` unparseable.

## `scan`

Find every reference in a file (or stdin) and report each with its character
offsets — the bulk counterpart to `parse`, handy for extracting citations from
prose.

```sh
versiref scan document.md --style en-sbl
cat document.md | versiref scan --style en-sbl --json
```

Plain output is tab-separated: `start`, `end`, the matched text, and the
normalized reference. `--sensitivity {book,chapter,verse}` (default `verse`)
controls the smallest unit reported.

<!-- New subcommands are documented in a new section, mirroring the above. -->
