"""Command-line interface for versiref.

The CLI is a click group. Subcommands are pure additions: register a new
``@main.command()`` (or a command on the ``list`` subgroup) without touching the
existing ones.

Commands fall into two families:

- Introspection (``list styles``/``versifications``/``book-names``) — what the
  bundled data offers.
- Reference operations (``parse``, ``validate``, ``convert``, ``scan``) — parse
  a reference or a document, check validity, map between versifications, and
  extract references from free text. Each accepts ``--json`` for machine-readable
  output and uses exit codes so it composes in scripts.
"""

import fnmatch
import json
import sys
from importlib.resources import files
from typing import Optional

import click

from versiref import (
    BibleRef,
    RefParser,
    RefStyle,
    Sensitivity,
    SimpleBibleRef,
    VerseRange,
    Versification,
    available_standard_names,
)

DEFAULT_STYLE = "en-cmos_short"
DEFAULT_VERSIFICATION = "eng"

# Exit codes shared by the reference-operation commands.
EXIT_OK = 0
EXIT_FALSIFIED = 1  # Parsed, but invalid / not mappable into the target.
EXIT_UNPARSEABLE = 2  # The input could not be parsed as a reference.


def _load_style(name: str, also_recognize: tuple[str, ...] = ()) -> RefStyle:
    """Load a named style, extending it with extra book-name sets.

    Raises a click error (not a traceback) when a name is unknown.
    """
    try:
        style = RefStyle.named(name)
    except FileNotFoundError:
        raise click.BadParameter(
            f"unknown style: {name!r} (see `versiref list styles`)",
            param_hint="--style",
        )
    for extra in also_recognize:
        try:
            style.also_recognize(extra)
        except FileNotFoundError:
            raise click.BadParameter(
                f"unknown book-name set: {extra!r} (see `versiref list book-names`)",
                param_hint="--also-recognize",
            )
    return style


def _load_versification(
    name: str, param_hint: str = "--versification"
) -> Versification:
    """Load a named versification, reporting unknown names as a click error."""
    try:
        return Versification.named(name)
    except FileNotFoundError:
        raise click.BadParameter(
            f"unknown versification: {name!r} (see `versiref list versifications`)",
            param_hint=param_hint,
        )


def _point(chapter: int, verse: int, subverse: str) -> dict[str, object]:
    """Serialize one end of a verse range; an unspecified verse becomes null."""
    return {
        "chapter": chapter,
        "verse": verse if verse >= 0 else None,
        "subverse": subverse or None,
    }


def _range_dict(vr: VerseRange) -> dict[str, object]:
    """Serialize a VerseRange as a start/end pair."""
    return {
        "start": _point(vr.start_chapter, vr.start_verse, vr.start_subverse),
        "end": _point(vr.end_chapter, vr.end_verse, vr.end_subverse),
        "whole_chapters": vr.is_whole_chapters(),
    }


def _book_dict(sr: SimpleBibleRef) -> dict[str, object]:
    """Serialize a SimpleBibleRef as a book plus its ranges."""
    return {
        "book": sr.book_id,
        "whole_book": sr.is_whole_book(),
        "ranges": [_range_dict(vr) for vr in sr.ranges],
    }


def _ref_dict(ref: BibleRef, out_style: RefStyle) -> dict[str, object]:
    """Serialize a BibleRef, including its formatted form in out_style."""
    vers = ref.versification
    return {
        "versification": vers.identifier if vers is not None else None,
        "valid": ref.is_valid(),
        "formatted": ref.format(out_style),
        "books": [_book_dict(sr) for sr in ref.simple_refs],
    }


def _echo_json(payload: object) -> None:
    """Print a JSON payload with a stable, human-diffable layout."""
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))


@click.group()
@click.version_option(package_name="versiref")
def main() -> None:
    """Parse, manipulate, and format references to the Bible."""


@main.command()
@click.argument("name", required=False)
def docs(name: Optional[str]) -> None:
    """Print the filesystem path to the bundled documentation.

    With no argument, prints the path to the bundled docs directory. Pass a
    file NAME (e.g., api.md) to print the path to that single doc.
    """
    docs_dir = files("versiref") / "docs"
    if name is not None:
        target = docs_dir / name
        if not target.is_file():
            click.echo(f"Error: no such doc: {name}", err=True)
            sys.exit(1)
        click.echo(str(target))
    else:
        click.echo(str(docs_dir))


@main.group(name="list")
def list_() -> None:
    """List the bundled styles, versifications, and book-name sets."""


def _emit_names(names: list[str], as_json: bool) -> None:
    """Print a list of identifiers, one per line or as a JSON array."""
    if as_json:
        _echo_json(names)
    else:
        for name in names:
            click.echo(name)


@list_.command()
@click.option("--pattern", default="*", show_default=True, help="fnmatch-style glob.")
@click.option("--json", "as_json", is_flag=True, help="Output a JSON array.")
def styles(pattern: str, as_json: bool) -> None:
    """List reference styles accepted by --style."""
    _emit_names(RefStyle.available_names(pattern), as_json)


@list_.command()
@click.option("--pattern", default="*", show_default=True, help="fnmatch-style glob.")
@click.option("--json", "as_json", is_flag=True, help="Output a JSON array.")
def versifications(pattern: str, as_json: bool) -> None:
    """List versifications accepted by --versification/--from/--to."""
    names = [
        n for n in Versification.available_names() if fnmatch.fnmatchcase(n, pattern)
    ]
    _emit_names(names, as_json)


@list_.command(name="book-names")
@click.option("--pattern", default="*", show_default=True, help="fnmatch-style glob.")
@click.option("--json", "as_json", is_flag=True, help="Output a JSON array.")
def book_names(pattern: str, as_json: bool) -> None:
    """List book-name sets accepted by --also-recognize."""
    _emit_names(available_standard_names(pattern), as_json)


@main.command()
@click.argument("reference")
@click.option("--style", default=DEFAULT_STYLE, show_default=True, help="Parse style.")
@click.option(
    "-v",
    "--versification",
    default=DEFAULT_VERSIFICATION,
    show_default=True,
    help="Versification to parse in.",
)
@click.option(
    "--out-style",
    default=None,
    help="Style for the normalized output [default: same as --style].",
)
@click.option(
    "--also-recognize",
    multiple=True,
    metavar="SET",
    help="Extra book-name set to recognize (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Output structured JSON.")
def parse(
    reference: str,
    style: str,
    versification: str,
    out_style: Optional[str],
    also_recognize: tuple[str, ...],
    as_json: bool,
) -> None:
    """Parse a single REFERENCE and print its normalized or structured form."""
    parser = RefParser(
        _load_style(style, also_recognize), _load_versification(versification)
    )
    out = _load_style(out_style) if out_style is not None else parser.style

    ref = parser.parse(reference, silent=True)
    if ref is None:
        click.echo(f"Error: could not parse reference: {reference!r}", err=True)
        sys.exit(EXIT_UNPARSEABLE)

    if as_json:
        _echo_json({"input": reference, **_ref_dict(ref, out)})
    else:
        click.echo(ref.format(out))


@main.command()
@click.argument("reference")
@click.option("--style", default=DEFAULT_STYLE, show_default=True, help="Parse style.")
@click.option(
    "-v",
    "--versification",
    default=DEFAULT_VERSIFICATION,
    show_default=True,
    help="Versification to validate against.",
)
@click.option(
    "--also-recognize",
    multiple=True,
    metavar="SET",
    help="Extra book-name set to recognize (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Output structured JSON.")
def validate(
    reference: str,
    style: str,
    versification: str,
    also_recognize: tuple[str, ...],
    as_json: bool,
) -> None:
    """Check whether REFERENCE parses and exists in the versification.

    Exit status: 0 valid, 1 parses but out of range, 2 unparseable.
    """
    parser = RefParser(
        _load_style(style, also_recognize), _load_versification(versification)
    )
    ref = parser.parse(reference, silent=True)

    if ref is None:
        status, code = "unparseable", EXIT_UNPARSEABLE
    elif ref.is_valid():
        status, code = "valid", EXIT_OK
    else:
        status, code = "invalid", EXIT_FALSIFIED

    if as_json:
        _echo_json(
            {
                "input": reference,
                "versification": versification,
                "status": status,
                "valid": status == "valid",
            }
        )
    else:
        messages = {
            "valid": f"valid in {versification}",
            "invalid": f"out of range in {versification}",
            "unparseable": "could not parse",
        }
        stream = sys.stdout if code == EXIT_OK else sys.stderr
        click.echo(f"{reference}: {messages[status]}", file=stream)
    sys.exit(code)


@main.command()
@click.argument("reference")
@click.option(
    "-f",
    "--from",
    "from_vers",
    required=True,
    metavar="VERS",
    help="Source versification of REFERENCE.",
)
@click.option(
    "-t",
    "--to",
    "to_vers",
    required=True,
    metavar="VERS",
    help="Target versification to map into.",
)
@click.option("--style", default=DEFAULT_STYLE, show_default=True, help="Parse style.")
@click.option(
    "--out-style",
    default=None,
    help="Style for the converted output [default: same as --style].",
)
@click.option(
    "--also-recognize",
    multiple=True,
    metavar="SET",
    help="Extra book-name set to recognize (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Output structured JSON.")
def convert(
    reference: str,
    from_vers: str,
    to_vers: str,
    style: str,
    out_style: Optional[str],
    also_recognize: tuple[str, ...],
    as_json: bool,
) -> None:
    """Map REFERENCE from one versification (--from) into another (--to).

    Reformatting between styles is the same operation with --from equal to
    --to and a differing --out-style. Exit status: 0 ok, 1 not representable
    in the target, 2 unparseable.
    """
    source = _load_versification(from_vers, param_hint="--from")
    target = _load_versification(to_vers, param_hint="--to")
    parser = RefParser(_load_style(style, also_recognize), source)
    out = _load_style(out_style) if out_style is not None else parser.style

    ref = parser.parse(reference, silent=True)
    if ref is None:
        click.echo(f"Error: could not parse reference: {reference!r}", err=True)
        sys.exit(EXIT_UNPARSEABLE)

    mapped = ref.map_to(target)
    if mapped is None:
        click.echo(
            f"Error: {reference!r} cannot be represented in {to_vers}",
            err=True,
        )
        sys.exit(EXIT_FALSIFIED)

    if as_json:
        _echo_json(
            {
                "input": reference,
                "from": from_vers,
                "to": to_vers,
                "source": _ref_dict(ref, out),
                "result": _ref_dict(mapped, out),
            }
        )
    else:
        click.echo(mapped.format(out))


@main.command()
@click.argument("file", type=click.File("r"), default="-")
@click.option("--style", default=DEFAULT_STYLE, show_default=True, help="Parse style.")
@click.option(
    "-v",
    "--versification",
    default=DEFAULT_VERSIFICATION,
    show_default=True,
    help="Versification to parse in.",
)
@click.option(
    "--out-style",
    default=None,
    help="Style for normalized output [default: same as --style].",
)
@click.option(
    "--sensitivity",
    type=click.Choice([s.name.lower() for s in Sensitivity], case_sensitive=False),
    default=Sensitivity.VERSE.name.lower(),
    show_default=True,
    help="Smallest unit to report.",
)
@click.option(
    "--also-recognize",
    multiple=True,
    metavar="SET",
    help="Extra book-name set to recognize (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Output structured JSON.")
def scan(
    file: click.utils.LazyFile,
    style: str,
    versification: str,
    out_style: Optional[str],
    sensitivity: str,
    also_recognize: tuple[str, ...],
    as_json: bool,
) -> None:
    """Find every reference in FILE (default stdin) and report it with offsets."""
    parser = RefParser(
        _load_style(style, also_recognize), _load_versification(versification)
    )
    out = _load_style(out_style) if out_style is not None else parser.style
    level = Sensitivity[sensitivity.upper()]

    text = file.read()
    matches = list(parser.scan_string(text, sensitivity=level))

    if as_json:
        _echo_json(
            {
                "count": len(matches),
                "matches": [
                    {
                        "start": start,
                        "end": end,
                        "text": text[start:end],
                        "reference": _ref_dict(ref, out),
                    }
                    for ref, start, end in matches
                ],
            }
        )
    else:
        for ref, start, end in matches:
            click.echo(f"{start}\t{end}\t{text[start:end]}\t{ref.format(out)}")


if __name__ == "__main__":
    main()
