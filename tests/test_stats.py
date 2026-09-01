from pathlib import Path

from journal.parser import parse_entry_text
from journal.stats import calculate_statistics


def make_entry(entry_id: str, category: str, extra: str = "", images=()):
    type_name = "project" if category == "making" else "observation"
    if category == "cats":
        type_name = "cat"
    if category == "curiosities":
        type_name = "curiosity"
    text = f"""---
id: {entry_id}
title: {entry_id}
date: 2026-09-01
type: {type_name}
category: {category}
{extra}---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"), images)


def test_statistics_are_derived_from_entries() -> None:
    entries = [
        make_entry("obs-1", "clouds", "cloud_genus: cumulus\ncloud_species: humilis\n"),
        make_entry("obs-2", "clouds", "cloud_genus: Cumulus\ncloud_species: mediocris\n"),
        make_entry("obs-3", "birds", "common_name: California Scrub-Jay\n"),
        make_entry("obs-4", "birds", "common_name: california scrub-jay\n"),
        make_entry("cat-1", "cats", "cat_name: Gwen\n", ("01.jpg", "02.jpg")),
        make_entry("proj-1", "making", "status: completed\ncraft: embroidery\n"),
        make_entry("cur-1", "curiosities", "texture: rough\n"),
    ]

    stats = calculate_statistics(entries)

    assert stats.cloud_observations == 2
    assert stats.unique_cloud_genera == 1
    assert stats.unique_cloud_species == 2
    assert stats.bird_observations == 2
    assert stats.unique_bird_species == 1
    assert stats.cat_entries == 1
    assert stats.cat_photographs == 2
    assert stats.unique_named_cats == 1
    assert stats.project_count == 1
    assert stats.completed_project_count == 1
    assert stats.curiosity_count == 1
    assert stats.total_entry_count == 7
