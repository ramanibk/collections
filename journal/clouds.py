"""Derived Cloud Atlas groupings and genus-page data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from .models import CloudMetadata, ContentEntry
from .taxonomy import CLOUD_GROUPS


@dataclass(frozen=True)
class CloudAtlasStatistics:
    total_sightings: int
    identified_sightings: int
    unidentified_sightings: int
    genera_observed: int
    species_observed: int


@dataclass(frozen=True)
class CloudGenusSummary:
    name: str
    sighting_count: int


@dataclass(frozen=True)
class CloudTaxonomyGroup:
    name: str
    genera: Tuple[CloudGenusSummary, ...]


@dataclass(frozen=True)
class CloudSpeciesSummary:
    name: str
    sighting_count: int


@dataclass(frozen=True)
class CloudGenusPage:
    name: str
    sightings: Tuple[ContentEntry, ...]
    first_recorded: date
    most_recent: date
    species: Tuple[CloudSpeciesSummary, ...]

    @property
    def sighting_count(self) -> int:
        return len(self.sightings)


@dataclass(frozen=True)
class CloudAtlas:
    statistics: CloudAtlasStatistics
    groups: Tuple[CloudTaxonomyGroup, ...]
    genus_pages: Tuple[CloudGenusPage, ...]


def _cloud_metadata(entry: ContentEntry) -> Optional[CloudMetadata]:
    if entry.category == "clouds" and isinstance(entry.metadata, CloudMetadata):
        return entry.metadata
    return None


def _group_label(name: str) -> str:
    return name if name == "Vertical Development" else f"{name} Clouds"


def build_cloud_atlas(
    entries: Iterable[ContentEntry], show_unobserved_genera: bool = False
) -> CloudAtlas:
    clouds = tuple(entry for entry in entries if _cloud_metadata(entry) is not None)
    by_genus: Dict[str, List[ContentEntry]] = {}
    species_observed = set()
    for entry in clouds:
        metadata = _cloud_metadata(entry)
        assert metadata is not None
        genus = (metadata.genus or "").strip().casefold()
        species = (metadata.species or "").strip().casefold()
        if genus:
            by_genus.setdefault(genus, []).append(entry)
        if species:
            species_observed.add(species)

    grouped_names = set()
    groups = []
    for group_name, configured_genera in CLOUD_GROUPS:
        rows = []
        for genus in configured_genera:
            grouped_names.add(genus)
            count = len(by_genus.get(genus, ()))
            if count or show_unobserved_genera:
                rows.append(CloudGenusSummary(genus, count))
        if rows:
            groups.append(CloudTaxonomyGroup(_group_label(group_name), tuple(rows)))

    unplaced = tuple(
        CloudGenusSummary(genus, len(by_genus[genus]))
        for genus in sorted(set(by_genus) - grouped_names)
    )
    if unplaced:
        groups.append(CloudTaxonomyGroup("Other / Unplaced", unplaced))

    genus_pages = []
    for genus, sightings in by_genus.items():
        ordered = tuple(
            sorted(sightings, key=lambda entry: (entry.date, entry.title.casefold(), entry.id), reverse=True)
        )
        species_counts: Dict[str, int] = {}
        for entry in ordered:
            metadata = _cloud_metadata(entry)
            assert metadata is not None
            species = metadata.species.strip().casefold() if metadata.species else "unclassified"
            species_counts[species] = species_counts.get(species, 0) + 1
        species_names = sorted(name for name in species_counts if name != "unclassified")
        if "unclassified" in species_counts:
            species_names.append("unclassified")
        genus_pages.append(
            CloudGenusPage(
                name=genus,
                sightings=ordered,
                first_recorded=min(entry.date for entry in ordered),
                most_recent=max(entry.date for entry in ordered),
                species=tuple(CloudSpeciesSummary(name, species_counts[name]) for name in species_names),
            )
        )

    taxonomy_order = {
        genus: index
        for index, genus in enumerate(genus for _, genera in CLOUD_GROUPS for genus in genera)
    }
    genus_pages.sort(key=lambda page: (taxonomy_order.get(page.name, len(taxonomy_order)), page.name))
    identified = sum(
        1
        for entry in clouds
        if _cloud_metadata(entry) is not None
        and bool((_cloud_metadata(entry).genus or "").strip())
    )
    return CloudAtlas(
        statistics=CloudAtlasStatistics(
            total_sightings=len(clouds),
            identified_sightings=identified,
            unidentified_sightings=len(clouds) - identified,
            genera_observed=len(by_genus),
            species_observed=len(species_observed),
        ),
        groups=tuple(groups),
        genus_pages=tuple(genus_pages),
    )
