"""Typed, normalized content models used throughout the journal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple, Union


@dataclass(frozen=True)
class CloudMetadata:
    genus: Optional[str] = None
    species: Optional[str] = None
    variety: Optional[str] = None
    supplementary_features: Tuple[str, ...] = ()
    optical_phenomena: Tuple[str, ...] = ()
    identification: Optional[str] = None
    confidence: Optional[int] = None


@dataclass(frozen=True)
class BirdMetadata:
    common_name: Optional[str] = None
    scientific_name: Optional[str] = None
    identification: Optional[str] = None
    confidence: Optional[int] = None
    count: Optional[int] = None


@dataclass(frozen=True)
class CatMetadata:
    cat_name: Optional[str] = None
    relationship: Optional[str] = None


@dataclass(frozen=True)
class ProjectMetadata:
    craft: Optional[str] = None
    status: Optional[str] = None
    started: Optional[date] = None
    completed: Optional[date] = None
    materials: Tuple[str, ...] = ()


CategoryMetadata = Union[CloudMetadata, BirdMetadata, CatMetadata, ProjectMetadata, None]


@dataclass(frozen=True)
class ContentEntry:
    """Common model for every item, with raw metadata kept for extension."""

    id: str
    title: str
    date: date
    type: str
    category: str
    slug: str
    source_path: Path
    body_markdown: str
    body_html: str
    tags: Tuple[str, ...] = ()
    cover: Optional[str] = None
    images: Tuple[str, ...] = ()
    favorite: bool = False
    location: Optional[str] = None
    status: Optional[str] = None
    metadata: CategoryMetadata = None
    raw_frontmatter: Mapping[str, Any] = field(default_factory=dict)

    @property
    def folder(self) -> Path:
        return self.source_path.parent

    @property
    def source(self) -> Path:
        """Compatibility name used by the original build prototype."""

        return self.source_path

    @property
    def meta(self) -> Mapping[str, Any]:
        """Compatibility name for templates and catalogue code."""

        return self.raw_frontmatter

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw_frontmatter.get(key, default)

    @property
    def url(self) -> str:
        """The permanent URL; specialized routes can link back to this page."""

        return f"/entry/{self.id}/"

    def image_url(self, filename: Optional[str]) -> Optional[str]:
        if not filename:
            return None
        from .urls import media_url

        return media_url(self.id, filename)

    @property
    def cover_url(self) -> Optional[str]:
        return self.image_url(self.cover)
