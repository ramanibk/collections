"""Derived Bird Notebook species groupings and observation statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from .models import BirdMetadata, ContentEntry


@dataclass(frozen=True)
class BirdNotebookStatistics:
    total_observations: int
    unique_species: int
    confirmed_identifications: int
    tentative_identifications: int
    unknown_identifications: int


@dataclass(frozen=True)
class BirdSpeciesPage:
    common_name: str
    scientific_name: Optional[str]
    sightings: Tuple[ContentEntry, ...]
    first_sighting: date
    most_recent_sighting: date

    @property
    def sighting_count(self) -> int:
        return len(self.sightings)


@dataclass(frozen=True)
class BirdNotebook:
    statistics: BirdNotebookStatistics
    species_pages: Tuple[BirdSpeciesPage, ...]
    unidentified: Tuple[ContentEntry, ...]


def _bird_metadata(entry: ContentEntry) -> Optional[BirdMetadata]:
    if entry.category == "birds" and isinstance(entry.metadata, BirdMetadata):
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


def build_bird_notebook(entries: Iterable[ContentEntry]) -> BirdNotebook:
    """Build case-insensitive species pages and a complete ID-status summary."""

    birds = tuple(entry for entry in entries if _bird_metadata(entry) is not None)
    by_species: Dict[str, List[ContentEntry]] = {}
    unidentified: List[ContentEntry] = []
    confirmed = 0
    tentative = 0

    for entry in birds:
        metadata = _bird_metadata(entry)
        assert metadata is not None
        common_name = (metadata.common_name or "").strip()
        identification = (metadata.identification or "").strip().casefold()

        if not common_name or identification == "unknown":
            unidentified.append(entry)
            continue

        by_species.setdefault(common_name.casefold(), []).append(entry)
        if identification == "tentative":
            tentative += 1
        else:
            # Named observations without a tentative/unknown status are useful
            # identifications, including "self-identified" and "confirmed".
            confirmed += 1

    species_pages = []
    for sightings in by_species.values():
        ordered = _ordered(sightings)
        common_names = tuple(
            bird_metadata.common_name.strip()
            for sighting in ordered
            if (bird_metadata := _bird_metadata(sighting)) is not None
            and bird_metadata.common_name
            and bird_metadata.common_name.strip()
        )
        common_name = min(
            common_names,
            key=lambda name: (-sum(character.isupper() for character in name), name),
        )
        scientific_name = next(
            (
                bird_metadata.scientific_name.strip()
                for sighting in ordered
                if (bird_metadata := _bird_metadata(sighting)) is not None
                and bird_metadata.scientific_name
                and bird_metadata.scientific_name.strip()
            ),
            None,
        )
        species_pages.append(
            BirdSpeciesPage(
                common_name=common_name,
                scientific_name=scientific_name,
                sightings=ordered,
                first_sighting=min(entry.date for entry in ordered),
                most_recent_sighting=max(entry.date for entry in ordered),
            )
        )

    species_pages.sort(key=lambda page: (page.common_name.casefold(), page.common_name))
    unknown = _ordered(unidentified)
    return BirdNotebook(
        statistics=BirdNotebookStatistics(
            total_observations=len(birds),
            unique_species=len(species_pages),
            confirmed_identifications=confirmed,
            tentative_identifications=tentative,
            unknown_identifications=len(unknown),
        ),
        species_pages=tuple(species_pages),
        unidentified=unknown,
    )
