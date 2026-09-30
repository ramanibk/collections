"""Typed content model for photographs and notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple


@dataclass(frozen=True)
class AboutLink:
    label: str
    url: str


@dataclass(frozen=True)
class AboutContent:
    title: str
    body_html: str
    portrait_url: str
    portrait_alt: str
    record_label: str
    links: Tuple[AboutLink, ...] = ()


@dataclass(frozen=True)
class ContentEntry:
    id: str
    title: str
    date: date
    type: str
    slug: str
    source_path: Path
    body_markdown: str
    body_html: str
    tags: Tuple[str, ...] = ()
    cover: Optional[str] = None
    images: Tuple[str, ...] = ()
    location: Optional[str] = None
    orientation: str = "landscape"
    raw_frontmatter: Mapping[str, Any] = field(default_factory=dict)

    @property
    def folder(self) -> Path:
        return self.source_path.parent

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw_frontmatter.get(key, default)

    @property
    def url(self) -> str:
        return f"/entry/{self.id}/"

    def image_url(self, filename: Optional[str]) -> Optional[str]:
        if not filename:
            return None
        from .urls import media_url

        return media_url(self.id, filename)

    @property
    def cover_url(self) -> Optional[str]:
        return self.image_url(self.cover)
