"""Command-line interface for authoring, checking, and serving the journal."""

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
from .creation import (
    CreationError,
    CreatedEntry,
    create_bird_entry,
    create_cat_entry,
    create_cloud_entry,
    create_curiosity_entry,
    create_project_entry,
)
from .loader import load_content
from .stats import SiteStatistics, calculate_statistics
from .validation import format_report


Input = Callable[[str], str]
KINDS = ("cloud", "bird", "cat", "project", "curiosity")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and publish the Field Notes archive.")
    commands = parser.add_subparsers(dest="command")
    add = commands.add_parser("add", help="create a new content entry")
    add.add_argument("kind", nargs="?", choices=KINDS)
    commands.add_parser("build", help="validate and build the static site")
    preview = commands.add_parser("preview", help="build and serve the site locally")
    preview.add_argument("--port", type=int, default=8000)
    commands.add_parser("validate", help="check all source content")
    commands.add_parser("stats", help="show derived collection statistics")
    return parser


def _ask(input_func: Input, label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input_func(f"{label}{suffix}: ").strip()
    return answer or default


def _optional_int(value: str, label: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise CreationError(f"{label} must be an integer") from exc


def _paths(primary: str, additional: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in (primary, *additional.split(",")) if value.strip())


def _yes(value: str) -> bool:
    return value.strip().casefold() in {"y", "yes", "true", "1"}


def _common_prompts(input_func: Input, image_label: str = "Image path") -> dict:
    primary = _ask(input_func, image_label)
    additional = _ask(input_func, "Additional image paths (comma-separated)")
    return {"image_paths": _paths(primary, additional)}


def _interactive_add(root: Path, kind: str, input_func: Input) -> CreatedEntry:
    today = date.today().isoformat()
    if kind == "cloud":
        values = _common_prompts(input_func)
        values.update(
            title=_ask(input_func, "Title"),
            entry_date=_ask(input_func, "Date", today),
            location=_ask(input_func, "Location"),
            cloud_genus=_ask(input_func, "Cloud genus"),
            cloud_species=_ask(input_func, "Cloud species"),
            cloud_variety=_ask(input_func, "Cloud variety"),
            identification=_ask(input_func, "Identification"),
            confidence=_optional_int(_ask(input_func, "Confidence [1-5]"), "confidence"),
            favorite=_yes(_ask(input_func, "Favorite [y/N]", "N")),
            tags=_ask(input_func, "Tags (comma-separated)"),
            notes=_ask(input_func, "Notes"),
        )
        return create_cloud_entry(root, **values)
    if kind == "bird":
        values = _common_prompts(input_func)
        values.update(
            title=_ask(input_func, "Title"),
            entry_date=_ask(input_func, "Date", today),
            location=_ask(input_func, "Location"),
            common_name=_ask(input_func, "Common name"),
            scientific_name=_ask(input_func, "Scientific name"),
            identification=_ask(input_func, "Identification"),
            confidence=_optional_int(_ask(input_func, "Confidence [1-5]"), "confidence"),
            count=_optional_int(_ask(input_func, "Count"), "count"),
            tags=_ask(input_func, "Tags (comma-separated)"),
            notes=_ask(input_func, "Notes"),
        )
        return create_bird_entry(root, **values)
    if kind == "cat":
        values = _common_prompts(input_func)
        values.update(
            title=_ask(input_func, "Title"),
            entry_date=_ask(input_func, "Date", today),
            cat_name=_ask(input_func, "Cat name"),
            relationship=_ask(input_func, "Relationship [mine/encounter]"),
            location=_ask(input_func, "Location"),
            tags=_ask(input_func, "Tags (comma-separated)"),
            notes=_ask(input_func, "Notes"),
        )
        return create_cat_entry(root, **values)
    if kind == "project":
        title = _ask(input_func, "Project title")
        craft = _ask(input_func, "Craft")
        status = _ask(input_func, "Status")
        started = _ask(input_func, "Started")
        completed = _ask(input_func, "Completed")
        values = _common_prompts(input_func, "Cover image")
        values.update(
            title=title,
            craft=craft,
            status=status,
            started=started,
            completed=completed,
            materials=_ask(input_func, "Materials (comma-separated)"),
            tags=_ask(input_func, "Tags (comma-separated)"),
            notes=_ask(input_func, "Notes"),
        )
        return create_project_entry(root, **values)
    values = _common_prompts(input_func)
    values.update(
        title=_ask(input_func, "Title"),
        entry_date=_ask(input_func, "Date", today),
        location=_ask(input_func, "Location"),
        tags=_ask(input_func, "Tags (comma-separated)"),
        notes=_ask(input_func, "Notes"),
    )
    return create_curiosity_entry(root, **values)


def _print_statistics(statistics: SiteStatistics, output: TextIO) -> None:
    print(f"Cloud observations: {statistics.cloud_observations}", file=output)
    print(f"Bird observations: {statistics.bird_observations}", file=output)
    print(f"Bird species: {statistics.unique_bird_species}", file=output)
    print(f"Cat entries: {statistics.cat_entries}", file=output)
    print(f"Cat photographs: {statistics.cat_photographs}", file=output)
    print(f"Projects: {statistics.project_count}", file=output)
    print(f"Curiosities: {statistics.curiosity_count}", file=output)
    print(f"Total entries: {statistics.total_entry_count}", file=output)


def _print_build(result: BuildResult, output: TextIO) -> None:
    print(f"Loaded {result.entry_count} entries\n", file=output)
    _print_statistics(result.statistics, output)
    print(f"\nGenerated {result.page_count} pages", file=output)
    print(f"Copied {result.media_count} images", file=output)
    print(f"\nBuild complete: {result.output_dir}", file=output)


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
    """Map a deployment-prefixed local request back into ``public/``."""

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
        kind = args.kind or _ask(input_func, "Entry type [cloud/bird/cat/project/curiosity]")
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
    if args.command == "stats":
        result = load_content(root / "content")
        if not result.is_valid:
            print(format_report(result.report), file=error)
            return 1
        _print_statistics(calculate_statistics(result.entries), output)
        return 0
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
    local_url = f"http://127.0.0.1:{args.port}{config.site.base_url}/"
    print(f"Previewing at {local_url}", file=output)
    print("Press Ctrl+C to stop.", file=output)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPreview stopped.", file=output)
    finally:
        server.server_close()
    return 0
