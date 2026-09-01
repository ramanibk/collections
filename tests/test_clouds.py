from pathlib import Path

from journal.clouds import build_cloud_atlas
from journal.parser import parse_entry_text


def cloud(entry_id: str, date: str, genus: str = "", species: str = ""):
    extra = ""
    if genus:
        extra += f"cloud_genus: {genus}\n"
    if species:
        extra += f"cloud_species: {species}\n"
    text = f"""---
id: {entry_id}
title: Cloud {entry_id}
date: {date}
type: observation
category: clouds
{extra}---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"))


def test_cloud_atlas_statistics_and_taxonomy_order() -> None:
    atlas = build_cloud_atlas(
        [
            cloud("obs-1", "2026-05-14", "altocumulus", "stratiformis"),
            cloud("obs-2", "2026-08-29", "cumulus", "humilis"),
            cloud("obs-3", "2026-08-30"),
            cloud("obs-4", "2026-08-31", "volutus"),
        ]
    )

    assert atlas.statistics.total_sightings == 4
    assert atlas.statistics.identified_sightings == 3
    assert atlas.statistics.unidentified_sightings == 1
    assert atlas.statistics.genera_observed == 3
    assert atlas.statistics.species_observed == 2
    assert [group.name for group in atlas.groups] == [
        "Middle Clouds",
        "Vertical Development",
        "Other / Unplaced",
    ]
    assert [page.name for page in atlas.genus_pages] == ["altocumulus", "cumulus", "volutus"]


def test_unobserved_genera_follow_configuration() -> None:
    hidden = build_cloud_atlas([], show_unobserved_genera=False)
    shown = build_cloud_atlas([], show_unobserved_genera=True)

    assert hidden.groups == ()
    assert sum(len(group.genera) for group in shown.groups) == 10
    assert all(genus.sighting_count == 0 for group in shown.groups for genus in group.genera)


def test_genus_page_dates_species_counts_and_sighting_order() -> None:
    atlas = build_cloud_atlas(
        [
            cloud("obs-1", "2026-05-14", "altocumulus", "stratiformis"),
            cloud("obs-2", "2026-08-29", "Altocumulus", "stratiformis"),
            cloud("obs-3", "2026-06-01", "altocumulus"),
        ]
    )
    page = atlas.genus_pages[0]

    assert page.first_recorded.isoformat() == "2026-05-14"
    assert page.most_recent.isoformat() == "2026-08-29"
    assert [entry.id for entry in page.sightings] == ["obs-2", "obs-3", "obs-1"]
    assert [(species.name, species.sighting_count) for species in page.species] == [
        ("stratiformis", 2),
        ("unclassified", 1),
    ]
