"""Reusable, noninteractive content-entry creation functions."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from .ids import ID_PREFIXES, next_permanent_id, record_permanent_id
from .parser import ContentParseError, SUPPORTED_IMAGE_SUFFIXES, parse_entry
from .utils import slugify
from .validation import validate_entries


class CreationError(ValueError):
    """Raised when a new entry cannot be safely created."""


@dataclass(frozen=True)
class CreatedEntry:
    entry_id: str
    directory: Path
    source_path: Path
    image_names: tuple[str, ...]


KIND_DETAILS = {
    "cloud": ("clouds", "observation"),
    "bird": ("birds", "observation"),
    "cat": ("cats", "cat"),
    "project": ("making", "project"),
    "curiosity": ("curiosities", "curiosity"),
}


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
    paths: list[Path] = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise CreationError(f"image does not exist or is not a file: {value}")
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            allowed = ", ".join(sorted(SUPPORTED_IMAGE_SUFFIXES))
            raise CreationError(f"unsupported image type for {value}; expected {allowed}")
        paths.append(path)
    return tuple(paths)


def _unique_directory(parent: Path, name: str) -> Path:
    candidate = parent / name
    number = 2
    while candidate.exists():
        candidate = parent / f"{name}-{number}"
        number += 1
    return candidate


def _copy_images(sources: Sequence[Path], destination: Path) -> tuple[str, ...]:
    copied: list[str] = []
    used: set[str] = set()
    for source in sources:
        stem = slugify(source.stem)
        suffix = source.suffix.lower()
        filename = f"{stem}{suffix}"
        number = 2
        while filename.casefold() in used:
            filename = f"{stem}-{number}{suffix}"
            number += 1
        shutil.copy2(source, destination / filename)
        copied.append(filename)
        used.add(filename.casefold())
    return tuple(copied)


def create_entry(
    project_root: Path,
    kind: str,
    *,
    title: str,
    entry_date: date | str | None = None,
    image_paths: Sequence[str | Path] = (),
    location: str | None = None,
    tags: Iterable[str] | str | None = None,
    notes: str = "",
    favorite: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> CreatedEntry:
    """Create one complete entry directory after validating all inputs."""

    normalized_kind = kind.strip().lower()
    if normalized_kind not in KIND_DETAILS:
        raise CreationError(f"unsupported entry kind {kind!r}")
    clean_title = title.strip()
    if not clean_title:
        raise CreationError("title cannot be blank")
    chosen_date = _entry_date(entry_date)
    sources = _image_paths(image_paths)
    root = project_root.resolve()
    content_dir = root / "content"
    category, entry_type = KIND_DETAILS[normalized_kind]
    entry_id = next_permanent_id(content_dir, ID_PREFIXES[normalized_kind])
    parent = content_dir / category
    parent.mkdir(parents=True, exist_ok=True)
    directory = _unique_directory(parent, f"{chosen_date.isoformat()}-{slugify(clean_title)}")
    directory.mkdir()

    try:
        image_names = _copy_images(sources, directory)
        frontmatter: dict[str, Any] = {
            "id": entry_id,
            "title": clean_title,
            "date": chosen_date.isoformat(),
            "type": entry_type,
            "category": category,
        }
        if location and location.strip():
            frontmatter["location"] = location.strip()
        if image_names:
            frontmatter["cover"] = image_names[0]
        if favorite:
            frontmatter["favorite"] = True
        clean_tags = _list(tags)
        if clean_tags:
            frontmatter["tags"] = clean_tags
        for key, value in (metadata or {}).items():
            if value not in (None, "", [], ()):
                frontmatter[key] = list(value) if isinstance(value, tuple) else value

        yaml_text = yaml.safe_dump(
            frontmatter,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).rstrip()
        body = notes.strip()
        source_path = directory / "entry.md"
        source_path.write_text(f"---\n{yaml_text}\n---\n\n{body}\n", encoding="utf-8")
        try:
            parsed = parse_entry(source_path)
        except ContentParseError as exc:
            raise CreationError(str(exc)) from exc
        report = validate_entries((parsed,))
        if report.errors:
            messages = "; ".join(issue.message for issue in report.errors)
            raise CreationError(messages)
        record_permanent_id(content_dir, entry_id)
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise

    return CreatedEntry(entry_id, directory, source_path, image_names)


def create_cloud_entry(project_root: Path, **values: Any) -> CreatedEntry:
    metadata = {
        "cloud_genus": values.pop("cloud_genus", None),
        "cloud_species": values.pop("cloud_species", None),
        "cloud_variety": values.pop("cloud_variety", None),
        "identification": values.pop("identification", None),
        "confidence": values.pop("confidence", None),
    }
    return create_entry(project_root, "cloud", metadata=metadata, **values)


def create_bird_entry(project_root: Path, **values: Any) -> CreatedEntry:
    metadata = {
        "common_name": values.pop("common_name", None),
        "scientific_name": values.pop("scientific_name", None),
        "identification": values.pop("identification", None),
        "confidence": values.pop("confidence", None),
        "count": values.pop("count", None),
    }
    return create_entry(project_root, "bird", metadata=metadata, **values)


def create_cat_entry(project_root: Path, **values: Any) -> CreatedEntry:
    metadata = {
        "cat_name": values.pop("cat_name", None),
        "relationship": values.pop("relationship", None),
    }
    return create_entry(project_root, "cat", metadata=metadata, **values)


def create_project_entry(project_root: Path, **values: Any) -> CreatedEntry:
    started = values.pop("started", None)
    completed = values.pop("completed", None)
    values.setdefault("entry_date", completed or started or None)
    metadata = {
        "craft": values.pop("craft", None),
        "status": values.pop("status", None),
        "started": started,
        "completed": completed,
        "materials": _list(values.pop("materials", None)),
    }
    return create_entry(project_root, "project", metadata=metadata, **values)


def create_curiosity_entry(project_root: Path, **values: Any) -> CreatedEntry:
    return create_entry(project_root, "curiosity", **values)
