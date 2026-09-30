"""Validated static-site build orchestration."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .config import JournalConfig, load_config
from .loader import load_content
from .parser import ContentParseError, parse_about
from .renderer import Renderer
from .urls import about_url, entry_url, notes_url, photograph_index_url, photographs_url
from .validation import ValidationIssue, format_report


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    entry_count: int
    page_count: int
    media_count: int
    warnings: Tuple[ValidationIssue, ...] = ()


def _safe_output_dir(project_root: Path, configured_output: Path) -> Path:
    root = project_root.resolve()
    output = configured_output.resolve()
    try:
        relative = output.relative_to(root)
    except ValueError as exc:
        raise BuildError("build.output_dir must be inside the project directory") from exc
    protected = {"content", "templates", "static", "journal", "tests", ".git"}
    if not relative.parts or relative.parts[0] in protected:
        raise BuildError(f"refusing unsafe build.output_dir: {configured_output}")
    if configured_output.is_symlink():
        raise BuildError(f"refusing symlink build.output_dir: {configured_output}")
    return output


def _copy_static(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or any(
            part.startswith(".") for part in path.relative_to(source).parts
        ):
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _copy_media(entries, destination: Path) -> int:
    count = 0
    for entry in entries:
        for filename in entry.images:
            target = destination / entry.id / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry.folder / filename, target)
            count += 1
    return count


def build_site(project_root: Path, config_path: Optional[Path] = None) -> BuildResult:
    root = project_root.resolve()
    config: JournalConfig = load_config(config_path or root / "config.yaml")
    output = _safe_output_dir(root, config.build.output_dir)
    loaded = load_content(root / "content")
    if not loaded.is_valid:
        raise BuildError(format_report(loaded.report))
    try:
        about = parse_about(root / "content" / "about.md")
    except ContentParseError as exc:
        raise BuildError(str(exc)) from exc

    photo_entries = tuple(entry for entry in loaded.entries if entry.type == "photo")
    note_entries = tuple(entry for entry in loaded.entries if entry.type in {"note", "essay"})
    filter_tags_by_entry = {}
    for entry in loaded.entries:
        derived = ["photograph" if entry.type == "photo" else entry.type]
        derived.extend(tag.casefold() for tag in entry.tags)
        filter_tags_by_entry[entry.id] = tuple(dict.fromkeys(derived))
    index_tags = sorted({tag for tags in filter_tags_by_entry.values() for tag in tags})

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        renderer = Renderer(root / "templates", staging, config.site)
        renderer.render("home.html", "/", page_title=config.site.title, current_section="home")
        renderer.render(
            "photographs.html",
            photographs_url(),
            page_title=f"Photographs — {config.site.title}",
            photo_entries=photo_entries,
            breadcrumbs=(("photographs", None),),
            current_section="photographs",
        )
        renderer.render(
            "photograph_index.html",
            photograph_index_url(),
            page_title=f"Archive Filter — {config.site.title}",
            index_entries=loaded.entries,
            index_tags=index_tags,
            filter_tags_by_entry=filter_tags_by_entry,
            breadcrumbs=(("photographs", photographs_url(config.site.base_url)), ("filter", None)),
            current_section="photographs",
        )
        renderer.render(
            "posts.html",
            notes_url(),
            page_title=f"Notes — {config.site.title}",
            posts=note_entries,
            breadcrumbs=(("notes", None),),
            current_section="notes",
        )
        renderer.render(
            "about.html",
            about_url(),
            page_title=f"{about.title} — {config.site.title}",
            about=about,
            breadcrumbs=(("about", None),),
            current_section="about",
        )
        for entry in loaded.entries:
            parent_url = (
                photographs_url(config.site.base_url)
                if entry.type == "photo"
                else notes_url(config.site.base_url)
            )
            parent_label = "photographs" if entry.type == "photo" else "notes"
            renderer.render(
                "entry.html",
                entry_url(entry.id),
                page_title=f"{entry.title} — {config.site.title}",
                entry=entry,
                breadcrumbs=((parent_label, parent_url), (entry.title, None)),
                current_section=parent_label,
            )
        renderer.render_file(
            "404.html", "404.html", page_title=f"Page not found — {config.site.title}"
        )
        _copy_static(root / "static", staging / "static")
        media_count = _copy_media(loaded.entries, staging / "media")
        (staging / ".nojekyll").touch()
        page_count = sum(1 for _ in staging.rglob("index.html"))
        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(staging), str(output))
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return BuildResult(output, len(loaded.entries), page_count, media_count, loaded.report.warnings)
