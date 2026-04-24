"""Generate build/api.md from the versiref package using griffe.

Produces a single Markdown file summarizing the public API. Replaces the
previous pydoc-markdown invocation and has the side benefit of pulling
black/docspec-python out of the dev dependency tree.
"""

from __future__ import annotations

from pathlib import Path

import griffe

OUTPUT_PATH = Path("build/api.md")
PACKAGE_NAME = "versiref"
SEARCH_PATHS = ["src"]


def is_public(name: str) -> bool:
    """Return True for names that don't start with an underscore."""
    return not name.startswith("_")


def fmt_annotation(ann: object) -> str:
    """Render a griffe annotation/expression as a short string."""
    return str(ann) if ann is not None else ""


def fmt_signature(func: griffe.Function) -> str:
    """Render a function's parameter list and return annotation."""
    parts: list[str] = []
    for p in func.parameters:
        if p.name in ("self", "cls"):
            continue
        s = p.name
        if p.annotation is not None:
            s += f": {fmt_annotation(p.annotation)}"
        if p.default is not None:
            s += f" = {p.default}"
        parts.append(s)
    ret = f" -> {fmt_annotation(func.returns)}" if func.returns is not None else ""
    return f"({', '.join(parts)}){ret}"


def render_docstring(obj: griffe.Object) -> str:
    """Return the object's docstring followed by a blank line, or empty."""
    if obj.docstring is not None:
        return obj.docstring.value.rstrip() + "\n\n"
    return ""


def render_function(func: griffe.Function, level: int) -> str:
    """Render a function or method as a Markdown block."""
    prefix = "#" * level
    body = f"{prefix} `{func.name}`\n\n"
    body += f"```python\n{func.name}{fmt_signature(func)}\n```\n\n"
    body += render_docstring(func)
    return body


def render_class(cls: griffe.Class, level: int) -> str:
    """Render a class and its public attributes and methods."""
    prefix = "#" * level
    bases = f"({', '.join(str(b) for b in cls.bases)})" if cls.bases else ""
    body = f"{prefix} `class {cls.name}{bases}`\n\n"
    body += render_docstring(cls)

    attrs = [
        m
        for m in cls.members.values()
        if isinstance(m, griffe.Attribute) and is_public(m.name)
    ]
    if attrs:
        body += f"{'#' * (level + 1)} Attributes\n\n"
        for a in attrs:
            line = f"- `{a.name}"
            if a.annotation is not None:
                line += f": {fmt_annotation(a.annotation)}"
            line += "`"
            if a.docstring is not None:
                first = a.docstring.value.strip().split("\n")[0]
                line += f" — {first}"
            body += line + "\n"
        body += "\n"

    for m in cls.members.values():
        if isinstance(m, griffe.Function) and is_public(m.name):
            body += render_function(m, level + 1)
    return body


def render_module(mod: griffe.Module, level: int = 2) -> str:
    """Render a module's public contents in source order."""
    if not is_public(mod.name):
        return ""
    prefix = "#" * level
    body = f"{prefix} Module `{mod.name}`\n\n"
    body += render_docstring(mod)
    for m in mod.members.values():
        if not is_public(m.name):
            continue
        if isinstance(m, griffe.Class):
            body += render_class(m, level + 1)
        elif isinstance(m, griffe.Function):
            body += render_function(m, level + 1)
        elif isinstance(m, griffe.Module):
            body += render_module(m, level + 1)
    return body


def main() -> None:
    """Load the package with griffe and write the Markdown output."""
    pkg = griffe.load(PACKAGE_NAME, search_paths=SEARCH_PATHS)
    assert isinstance(pkg, griffe.Module)
    out = f"# {PACKAGE_NAME} API Reference\n\n"
    out += render_docstring(pkg)
    for m in pkg.members.values():
        if isinstance(m, griffe.Module) and is_public(m.name):
            out += render_module(m)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(out)
    print(f"Wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
