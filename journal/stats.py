"""Derived site statistics, kept independent from templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Set

from .models import BirdMetadata, CatMetadata, CloudMetadata, ContentEntry, ProjectMetadata


@dataclass(frozen=True)
class SiteStatistics:
    cloud_observations: int = 0
    unique_cloud_genera: int = 0
    unique_cloud_species: int = 0
    bird_observations: int = 0
    unique_bird_species: int = 0
    cat_entries: int = 0
    cat_photographs: int = 0
    unique_named_cats: int = 0
    project_count: int = 0
    completed_project_count: int = 0
    curiosity_count: int = 0
    total_entry_count: int = 0


def _normalized(values: Iterable[str]) -> Set[str]:
    return {value.strip().casefold() for value in values if value and value.strip()}


def calculate_statistics(entries: Iterable[ContentEntry]) -> SiteStatistics:
    items = tuple(entries)
    clouds = tuple(entry for entry in items if entry.category == "clouds")
    birds = tuple(entry for entry in items if entry.category == "birds")
    cats = tuple(entry for entry in items if entry.category == "cats")
    projects = tuple(entry for entry in items if entry.category == "making")

    cloud_genera = _normalized(
        entry.metadata.genus
        for entry in clouds
        if isinstance(entry.metadata, CloudMetadata) and entry.metadata.genus
    )
    cloud_species = _normalized(
        entry.metadata.species
        for entry in clouds
        if isinstance(entry.metadata, CloudMetadata) and entry.metadata.species
    )
    bird_species = _normalized(
        entry.metadata.common_name
        for entry in birds
        if isinstance(entry.metadata, BirdMetadata) and entry.metadata.common_name
    )
    named_cats = _normalized(
        entry.metadata.cat_name
        for entry in cats
        if isinstance(entry.metadata, CatMetadata) and entry.metadata.cat_name
    )
    completed_projects = sum(
        1
        for entry in projects
        if isinstance(entry.metadata, ProjectMetadata)
        and (entry.metadata.status or "").strip().casefold() == "completed"
    )
    return SiteStatistics(
        cloud_observations=len(clouds),
        unique_cloud_genera=len(cloud_genera),
        unique_cloud_species=len(cloud_species),
        bird_observations=len(birds),
        unique_bird_species=len(bird_species),
        cat_entries=len(cats),
        cat_photographs=sum(len(entry.images) for entry in cats),
        unique_named_cats=len(named_cats),
        project_count=len(projects),
        completed_project_count=completed_projects,
        curiosity_count=sum(entry.category == "curiosities" for entry in items),
        total_entry_count=len(items),
    )
