# Command-Line Interface

VersiRef installs a `versiref` command. It is a click group; run `versiref
--help` to list the available subcommands, or `versiref --version` to print the
installed version.

```sh
versiref --help
```

## `docs`

Print the filesystem path to the documentation bundled inside the installed
package. The path is resolved with `importlib.resources`, so it is correct for
both wheel and editable installs.

```sh
versiref docs            # path to the bundled docs directory
versiref docs api.md     # path to a single bundled doc
```

With no argument it prints the docs directory; with a file name it prints the
path to that single file (and exits non-zero if the file is not bundled). The
bundled files are `index.md` (a copy of the README), `api.md` (the generated
API reference), and `cli.md` (this document).

<!-- New subcommands are documented below, one section per command. -->
