"""Create photo, note, and essay entries."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

from .ids import ID_PREFIXES, next_permanent_id, record_permanent_id
from .parser import SUPPORTED_IMAGE_SUFFIXES, ContentParseError, parse_entry
from .utils import normalize_tags, slugify
from .validation import validate_entries


class CreationError(ValueError):
    pass


@dataclass(frozen=True)
class CreatedEntry:
    entry_id: str
    directory: Path
    source_path: Path
    image_names: tuple[str, ...]


def _entry_date(value: date | str | None) -> date:
    if value in (None, ""):
        return date.today()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise CreationError(f"invalid date {value!r}; use YYYY-MM-DD") from exc


def _list(values: Iterable[str] | str | None) -> list[str]:
    if values in (None, ""):
        return []
    if isinstance(values, str):
        values = values.split(",")
    return [str(value).strip() for value in values if str(value).strip()]


def _image_paths(values: Sequence[str | Path]) -> tuple[Path, ...]:
    paths = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise CreationError(f"image does not exist or is not a file: {value}")
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            raise CreationError(f"unsupported image type: {value}")
        paths.append(path)
    return tuple(paths)


def _copy_images(sources: Sequence[Path], destination: Path) -> tuple[str, ...]:
    copied = []
    used = set()
    for source in sources:
        stem = slugify(source.stem)
        filename = f"{stem}{source.suffix.lower()}"
        number = 2
        while filename.casefold() in used:
            filename = f"{stem}-{number}{source.suffix.lower()}"
            number += 1
        shutil.copy2(source, destination / filename)
        copied.append(filename)
        used.add(filename.casefold())
    return tuple(copied)


def create_entry(
    project_root: Path,
    entry_type: str,
    *,
    title: str,
    entry_date: date | str | None = None,
    image_paths: Sequence[str | Path] = (),
    location: str | None = None,
    orientation: str = "landscape",
    tags: Iterable[str] | str | None = None,
    notes: str = "",
) -> CreatedEntry:
    normalized_type = entry_type.strip().casefold()
    if normalized_type not in ID_PREFIXES:
        raise CreationError(f"unsupported entry type {entry_type!r}")
    clean_title = title.strip()
    if not clean_title:
        raise CreationError("title cannot be blank")
    sources = _image_paths(image_paths)
    if normalized_type == "photo" and not sources:
        raise CreationError("photo entries require an image")

    chosen_date = _entry_date(entry_date)
    content_dir = project_root.resolve() / "content"
    entry_id = next_permanent_id(content_dir, ID_PREFIXES[normalized_type])
    parent = content_dir / ("photographs" if normalized_type == "photo" else "notes")
    parent.mkdir(parents=True, exist_ok=True)
    directory = parent / f"{chosen_date.isoformat()}-{slugify(clean_title)}"
    number = 2
    while directory.exists():
        directory = parent / f"{chosen_date.isoformat()}-{slugify(clean_title)}-{number}"
        number += 1
    directory.mkdir()

    try:
        image_names = _copy_images(sources, directory)
        frontmatter: dict[str, Any] = {
            "id": entry_id,
            "title": clean_title,
            "date": chosen_date.isoformat(),
            "type": normalized_type,
        }
        if location and location.strip():
            frontmatter["location"] = location.strip()
        if image_names:
            frontmatter["cover"] = image_names[0]
        if normalized_type == "photo":
            frontmatter["orientation"] = orientation.strip().casefold()
        clean_tags = normalize_tags(_list(tags))
        if clean_tags:
            frontmatter["tags"] = clean_tags
        yaml_text = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip()
        source_path = directory / "entry.md"
        source_path.write_text(f"---\n{yaml_text}\n---\n\n{notes.strip()}\n", encoding="utf-8")
        try:
            parsed = parse_entry(source_path)
        except ContentParseError as exc:
            raise CreationError(str(exc)) from exc
        report = validate_entries((parsed,))
        if report.errors:
            raise CreationError("; ".join(issue.message for issue in report.errors))
        record_permanent_id(content_dir, entry_id)
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return CreatedEntry(entry_id, directory, source_path, image_names)


def create_photo_entry(project_root: Path, **values: Any) -> CreatedEntry:
    return create_entry(project_root, "photo", **values)


def create_note_entry(project_root: Path, *, essay: bool = False, **values: Any) -> CreatedEntry:
    return create_entry(project_root, "essay" if essay else "note", **values)
