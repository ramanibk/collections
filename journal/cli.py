"""Command-line authoring, validation, building, and preview."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Sequence, TextIO
from urllib.parse import urlsplit, urlunsplit

from .builder import BuildError, BuildResult, build_site
from .config import ConfigError, load_config
from .creation import CreatedEntry, CreationError, create_note_entry, create_photo_entry
from .loader import load_content
from .validation import format_report

Input = Callable[[str], str]
KINDS = ("photo", "note", "essay")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and publish the archive.")
    commands = parser.add_subparsers(dest="command")
    add = commands.add_parser("add", help="create a photograph or note")
    add.add_argument("kind", nargs="?", choices=KINDS)
    commands.add_parser("build", help="validate and build the static site")
    preview = commands.add_parser("preview", help="build and serve the site locally")
    preview.add_argument("--port", type=int, default=8000)
    commands.add_parser("validate", help="check all source content")
    return parser


def _ask(input_func: Input, label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input_func(f"{label}{suffix}: ").strip() or default


def _paths(primary: str, additional: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in (primary, *additional.split(",")) if value.strip())


def _interactive_add(root: Path, kind: str, input_func: Input) -> CreatedEntry:
    today = date.today().isoformat()
    title = _ask(input_func, "Title")
    entry_date = _ask(input_func, "Date", today)
    tags = _ask(input_func, "Tags (comma-separated)")
    notes = _ask(input_func, "Notes")
    if kind == "photo":
        primary = _ask(input_func, "Image path")
        additional = _ask(input_func, "Additional image paths (comma-separated)")
        return create_photo_entry(
            root,
            title=title,
            entry_date=entry_date,
            image_paths=_paths(primary, additional),
            location=_ask(input_func, "Location"),
            orientation=_ask(input_func, "Orientation [portrait/landscape]", "landscape"),
            tags=tags,
            notes=notes,
        )
    return create_note_entry(
        root,
        essay=kind == "essay",
        title=title,
        entry_date=entry_date,
        tags=tags,
        notes=notes,
    )


def _print_build(result: BuildResult, output: TextIO) -> None:
    print(f"Loaded {result.entry_count} entries", file=output)
    print(f"Generated {result.page_count} pages", file=output)
    print(f"Copied {result.media_count} images", file=output)
    print(f"Build complete: {result.output_dir}", file=output)


def _build(root: Path, output: TextIO, error: TextIO) -> BuildResult | None:
    try:
        result = build_site(root)
    except (BuildError, ConfigError) as exc:
        print(f"Build failed:\n{exc}", file=error)
        return None
    for warning in result.warnings:
        print(str(warning), file=error)
    _print_build(result, output)
    return result


def _strip_preview_base(path: str, base_url: str) -> str:
    if not base_url:
        return path
    parsed = urlsplit(path)
    request_path = parsed.path
    if request_path == base_url:
        request_path = "/"
    elif request_path.startswith(f"{base_url}/"):
        request_path = request_path[len(base_url) :]
    return urlunsplit((parsed.scheme, parsed.netloc, request_path, parsed.query, parsed.fragment))


def _preview_handler(directory: Path, base_url: str):
    class PreviewRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def do_GET(self) -> None:
            self.path = _strip_preview_base(self.path, base_url)
            super().do_GET()

        def do_HEAD(self) -> None:
            self.path = _strip_preview_base(self.path, base_url)
            super().do_HEAD()

    return PreviewRequestHandler


def main(
    argv: Sequence[str] | None = None,
    *,
    project_root: Path | None = None,
    input_func: Input = input,
    output: TextIO = sys.stdout,
    error: TextIO = sys.stderr,
) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    if not args.command:
        parser.print_help(file=output)
        return 0
    if args.command == "add":
        kind = args.kind or _ask(input_func, "Entry type [photo/note/essay]")
        if kind not in KINDS:
            print(f"Unknown entry type: {kind}", file=error)
            return 2
        try:
            created = _interactive_add(root, kind, input_func)
        except CreationError as exc:
            print(f"Could not create entry: {exc}", file=error)
            return 1
        print(f"Created {created.entry_id}: {created.directory}", file=output)
        return 0
    if args.command == "validate":
        result = load_content(root / "content")
        print(format_report(result.report), file=output if result.is_valid else error)
        return 0 if result.is_valid else 1
    if args.command == "build":
        return 0 if _build(root, output, error) else 1
    if not 1 <= args.port <= 65535:
        print("Port must be between 1 and 65535", file=error)
        return 2
    result = _build(root, output, error)
    if not result:
        return 1
    config = load_config(root / "config.yaml")
    handler = _preview_handler(result.output_dir, config.site.base_url)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Previewing at http://127.0.0.1:{args.port}{config.site.base_url}/", file=output)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPreview stopped.", file=output)
    finally:
        server.server_close()
    return 0
