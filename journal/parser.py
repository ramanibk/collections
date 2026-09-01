"""Parse one content directory into a normalized :class:`ContentEntry`."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

import markdown
import yaml

from .models import BirdMetadata, CatMetadata, CloudMetadata, ContentEntry, ProjectMetadata
from .utils import slugify


SUPPORTED_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})
REQUIRED_FIELDS = ("id", "title", "date", "category")


class ContentParseError(ValueError):
    """A source-specific content parsing problem."""


def _string(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    return str(value)


def _strings(value: Any, source: Path, field_name: str) -> Tuple[str, ...]:
    if value in (None, ""):
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ContentParseError(f"{source}: {field_name} must be a list")
    return tuple(str(item) for item in value)


def _integer(value: Any, source: Path, field_name: str) -> Optional[int]:
    if value in (None, ""):
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContentParseError(f"{source}: {field_name} must be an integer")
    return value


def _date(value: Any, source: Path, field_name: str = "date") -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ContentParseError(f"{source}: invalid {field_name} {value!r}; use YYYY-MM-DD") from exc


def split_frontmatter(text: str, source: Path) -> Tuple[Mapping[str, Any], str]:
    """Return YAML metadata and Markdown body from a complete entry file."""

    match = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", text, re.DOTALL)
    if not match:
        raise ContentParseError(f"{source}: missing, malformed, or unclosed YAML frontmatter")
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        detail = f" near line {mark.line + 2}" if mark else ""
        raise ContentParseError(f"{source}: malformed YAML{detail}: {exc}") from exc
    if not isinstance(frontmatter, Mapping):
        raise ContentParseError(f"{source}: frontmatter must be a YAML mapping")
    return dict(frontmatter), match.group(2).strip()


def discover_images(directory: Path) -> Tuple[str, ...]:
    """Find supported, non-hidden images in deterministic filename order."""

    if not directory.exists():
        return ()
    return tuple(
        path.name
        for path in sorted(directory.iterdir(), key=lambda item: (item.name.casefold(), item.name))
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )


def _category_metadata(meta: Mapping[str, Any], source: Path, category: str):
    if category == "clouds":
        return CloudMetadata(
            genus=_string(meta.get("cloud_genus")),
            species=_string(meta.get("cloud_species")),
            variety=_string(meta.get("cloud_variety")),
            supplementary_features=_strings(meta.get("supplementary_features"), source, "supplementary_features"),
            optical_phenomena=_strings(meta.get("optical_phenomena"), source, "optical_phenomena"),
            identification=_string(meta.get("identification")),
            confidence=_integer(meta.get("confidence"), source, "confidence"),
        )
    if category == "birds":
        return BirdMetadata(
            common_name=_string(meta.get("common_name")),
            scientific_name=_string(meta.get("scientific_name")),
            identification=_string(meta.get("identification")),
            confidence=_integer(meta.get("confidence"), source, "confidence"),
            count=_integer(meta.get("count"), source, "count"),
        )
    if category == "cats":
        return CatMetadata(cat_name=_string(meta.get("cat_name")), relationship=_string(meta.get("relationship")))
    if category == "making":
        return ProjectMetadata(
            craft=_string(meta.get("craft")),
            status=_string(meta.get("status")),
            started=_date(meta.get("started"), source, "started"),
            completed=_date(meta.get("completed"), source, "completed"),
            materials=_strings(meta.get("materials"), source, "materials"),
        )
    return None


def parse_entry_text(text: str, source: Path, images: Sequence[str] = ()) -> ContentEntry:
    """Parse entry text. Filesystem image discovery is supplied by ``parse_entry``."""

    meta, body = split_frontmatter(text, source)
    missing = [name for name in REQUIRED_FIELDS if meta.get(name) in (None, "")]
    if missing:
        raise ContentParseError(f"{source}: missing required field(s): {', '.join(missing)}")

    entry_date = _date(meta["date"], source)
    assert entry_date is not None
    category = str(meta["category"]).strip().lower()
    title = str(meta["title"]).strip()
    cat_name = _string(meta.get("cat_name")) if category == "cats" else None
    slug_source = meta.get("slug") or cat_name or title
    image_names = tuple(images)
    declared_cover = _string(meta.get("cover"))
    cover = declared_cover if declared_cover is not None else (image_names[0] if image_names else None)

    return ContentEntry(
        id=str(meta["id"]).strip(),
        title=title,
        date=entry_date,
        type=str(meta.get("type") or "entry").strip().lower(),
        category=category,
        slug=slugify(str(slug_source)),
        source_path=source,
        body_markdown=body,
        body_html=markdown.markdown(body, extensions=["extra", "sane_lists"]),
        tags=_strings(meta.get("tags"), source, "tags"),
        cover=cover,
        images=image_names,
        favorite=bool(meta.get("favorite", False)),
        location=_string(meta.get("location")),
        status=_string(meta.get("status")),
        metadata=_category_metadata(meta, source, category),
        raw_frontmatter=dict(meta),
    )


def parse_entry(source: Path) -> ContentEntry:
    """Read and parse an ``entry.md`` and discover adjacent images."""

    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentParseError(f"could not read {source}: {exc}") from exc
    return parse_entry_text(text, source, discover_images(source.parent))
