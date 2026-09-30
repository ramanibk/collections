"""Parse one photo or note directory into a normalized content entry."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Tuple

import markdown
import yaml

from .models import AboutContent, AboutLink, ContentEntry
from .utils import normalize_tags, slugify

SUPPORTED_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})
REQUIRED_FIELDS = ("id", "title", "date", "type")


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


def _date(value: Any, source: Path) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ContentParseError(f"{source}: invalid date {value!r}; use YYYY-MM-DD") from exc


def split_frontmatter(text: str, source: Path) -> Tuple[Mapping[str, Any], str]:
    match = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(.*)\Z", text, re.DOTALL)
    if not match:
        raise ContentParseError(f"{source}: missing, malformed, or unclosed YAML frontmatter")
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ContentParseError(f"{source}: malformed YAML: {exc}") from exc
    if not isinstance(frontmatter, Mapping):
        raise ContentParseError(f"{source}: frontmatter must be a YAML mapping")
    return dict(frontmatter), match.group(2).strip()


def discover_images(directory: Path) -> Tuple[str, ...]:
    if not directory.exists():
        return ()
    return tuple(
        path.name
        for path in sorted(directory.iterdir(), key=lambda item: (item.name.casefold(), item.name))
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )


def parse_entry_text(text: str, source: Path, images: Sequence[str] = ()) -> ContentEntry:
    meta, body = split_frontmatter(text, source)
    missing = [name for name in REQUIRED_FIELDS if meta.get(name) in (None, "")]
    if missing:
        raise ContentParseError(f"{source}: missing required field(s): {', '.join(missing)}")

    title = str(meta["title"]).strip()
    entry_type = str(meta["type"]).strip().casefold()
    image_names = tuple(images)
    declared_cover = _string(meta.get("cover"))
    cover = (
        declared_cover if declared_cover is not None else (image_names[0] if image_names else None)
    )

    return ContentEntry(
        id=str(meta["id"]).strip(),
        title=title,
        date=_date(meta["date"], source),
        type=entry_type,
        slug=slugify(str(meta.get("slug") or title)),
        source_path=source,
        body_markdown=body,
        body_html=markdown.markdown(body, extensions=["extra", "sane_lists"]),
        tags=normalize_tags(_strings(meta.get("tags"), source, "tags")),
        cover=cover,
        images=image_names,
        location=_string(meta.get("location")),
        orientation=str(meta.get("orientation") or "landscape").strip().casefold(),
        raw_frontmatter=dict(meta),
    )


def parse_entry(source: Path) -> ContentEntry:
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentParseError(f"could not read {source}: {exc}") from exc
    return parse_entry_text(text, source, discover_images(source.parent))


def parse_about_text(text: str, source: Path) -> AboutContent:
    meta, body = split_frontmatter(text, source)
    required = ("title", "portrait_url")
    missing = [name for name in required if meta.get(name) in (None, "")]
    if missing:
        raise ContentParseError(f"{source}: missing required field(s): {', '.join(missing)}")

    raw_links = meta.get("links") or []
    if not isinstance(raw_links, Sequence) or isinstance(raw_links, (str, bytes)):
        raise ContentParseError(f"{source}: links must be a list")
    links = []
    for index, item in enumerate(raw_links, start=1):
        if not isinstance(item, Mapping) or not item.get("label") or not item.get("url"):
            raise ContentParseError(f"{source}: link {index} requires label and url")
        links.append(AboutLink(str(item["label"]).strip(), str(item["url"]).strip()))

    title = str(meta["title"]).strip()
    return AboutContent(
        title=title,
        body_html=markdown.markdown(body, extensions=["extra", "sane_lists"]),
        portrait_url=str(meta["portrait_url"]).strip(),
        portrait_alt=str(meta.get("portrait_alt") or title).strip(),
        record_label=str(meta.get("record_label") or "PROFILE").strip(),
        links=tuple(links),
    )


def parse_about(source: Path) -> AboutContent:
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentParseError(f"could not read {source}: {exc}") from exc
    return parse_about_text(text, source)
