"""Derived Making collection and craft groupings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .models import ContentEntry, ProjectMetadata


@dataclass(frozen=True)
class CraftPage:
    name: str
    projects: Tuple[ContentEntry, ...]

    @property
    def project_count(self) -> int:
        return len(self.projects)


@dataclass(frozen=True)
class MakingCollection:
    craft_pages: Tuple[CraftPage, ...]
    uncategorized_projects: Tuple[ContentEntry, ...]
    total_projects: int
    completed_projects: int


def _project_metadata(entry: ContentEntry) -> Optional[ProjectMetadata]:
    if entry.category == "making" and isinstance(entry.metadata, ProjectMetadata):
        return entry.metadata
    return None


def _ordered(entries: Iterable[ContentEntry]) -> Tuple[ContentEntry, ...]:
    return tuple(
        sorted(
            entries,
            key=lambda entry: (entry.date, entry.title.casefold(), entry.id),
            reverse=True,
        )
    )


def build_making_collection(entries: Iterable[ContentEntry]) -> MakingCollection:
    projects = tuple(entry for entry in entries if _project_metadata(entry) is not None)
    by_craft: Dict[str, List[ContentEntry]] = {}
    display_variants: Dict[str, set[str]] = {}
    uncategorized = []

    for entry in projects:
        metadata = _project_metadata(entry)
        assert metadata is not None
        craft = (metadata.craft or "").strip()
        if not craft:
            uncategorized.append(entry)
            continue
        key = craft.casefold()
        by_craft.setdefault(key, []).append(entry)
        display_variants.setdefault(key, set()).add(craft)

    display_names = {
        key: min(
            variants,
            key=lambda name: (-sum(character.isupper() for character in name), name),
        )
        for key, variants in display_variants.items()
    }
    craft_pages = tuple(
        CraftPage(display_names[key], _ordered(by_craft[key]))
        for key in sorted(by_craft, key=lambda value: (display_names[value].casefold(), display_names[value]))
    )
    return MakingCollection(
        craft_pages=craft_pages,
        uncategorized_projects=_ordered(uncategorized),
        total_projects=len(projects),
        completed_projects=sum(
            (metadata.status or "").strip().casefold() == "completed"
            for entry in projects
            if (metadata := _project_metadata(entry)) is not None
        ),
    )
