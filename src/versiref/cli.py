"""Command-line interface for versiref.

The CLI is a thin click group. Subcommands are pure additions: register a new
``@main.command()`` here (for example, to list supported versifications or to
convert a citation between them) without touching the existing ones.
"""

import sys
from importlib.resources import files

import click


@click.group()
@click.version_option(package_name="versiref")
def main() -> None:
    """Parse, manipulate, and format references to the Bible."""


@main.command()
@click.argument("name", required=False)
def docs(name: str | None) -> None:
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


if __name__ == "__main__":
    main()
