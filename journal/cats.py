"""Derived cat profiles and encounter listings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, Optional, Tuple

from .models import CatMetadata, ContentEntry


MY_CATS: Tuple[str, ...] = ("Gwen", "Billy", "Jet")


@dataclass(frozen=True)
class CatPhotograph:
    entry: ContentEntry
    filename: str


@dataclass(frozen=True)
class CatProfile:
    name: str
    entries: Tuple[ContentEntry, ...]
    photographs: Tuple[CatPhotograph, ...]
    first_entry: Optional[date]
    most_recent_entry: Optional[date]

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @property
    def photograph_count(self) -> int:
        return len(self.photographs)


@dataclass(frozen=True)
class CatCollection:
    profiles: Tuple[CatProfile, ...]
    encounters: Tuple[ContentEntry, ...]
    total_entries: int
    total_photographs: int


def _cat_metadata(entry: ContentEntry) -> Optional[CatMetadata]:
    if entry.category == "cats" and isinstance(entry.metadata, CatMetadata):
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


def build_cat_collection(entries: Iterable[ContentEntry]) -> CatCollection:
    """Build the three permanent profiles plus a separate encounter stream."""

    cats = tuple(entry for entry in entries if _cat_metadata(entry) is not None)
    canonical_names: Dict[str, str] = {name.casefold(): name for name in MY_CATS}
    profile_entries: Dict[str, list[ContentEntry]] = {name: [] for name in MY_CATS}
    encounters = []

    for entry in cats:
        metadata = _cat_metadata(entry)
        assert metadata is not None
        name_key = (metadata.cat_name or "").strip().casefold()
        relationship = (metadata.relationship or "").strip().casefold()
        canonical_name = canonical_names.get(name_key)
        if canonical_name and relationship != "encounter":
            profile_entries[canonical_name].append(entry)
        if relationship == "encounter" or not canonical_name:
            encounters.append(entry)

    profiles = []
    for name in MY_CATS:
        ordered = _ordered(profile_entries[name])
        photographs = tuple(
            CatPhotograph(entry, filename)
            for entry in ordered
            for filename in reversed(entry.images)
        )
        profiles.append(
            CatProfile(
                name=name,
                entries=ordered,
                photographs=photographs,
                first_entry=min((entry.date for entry in ordered), default=None),
                most_recent_entry=max((entry.date for entry in ordered), default=None),
            )
        )

    return CatCollection(
        profiles=tuple(profiles),
        encounters=_ordered(encounters),
        total_entries=len(cats),
        total_photographs=sum(len(entry.images) for entry in cats),
    )
