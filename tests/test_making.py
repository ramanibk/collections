from pathlib import Path

from journal.curiosities import build_curiosity_collection
from journal.making import build_making_collection
from journal.parser import parse_entry_text


def entry(entry_id: str, entry_date: str, category: str, extra: str = "", images=()):
    type_name = "project" if category == "making" else "curiosity"
    text = f"""---
id: {entry_id}
title: {entry_id} title
date: {entry_date}
type: {type_name}
category: {category}
{extra}---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"), images)


def test_making_groups_crafts_case_insensitively_and_tracks_completion() -> None:
    collection = build_making_collection(
        [
            entry("proj-1", "2026-05-14", "making", "craft: Embroidery\nstatus: completed\n"),
            entry("proj-2", "2026-08-29", "making", "craft: embroidery\nstatus: in-progress\n"),
            entry("proj-3", "2026-08-30", "making", "status: planned\n"),
        ]
    )

    assert collection.total_projects == 3
    assert collection.completed_projects == 1
    assert [page.name for page in collection.craft_pages] == ["Embroidery"]
    assert [project.id for project in collection.craft_pages[0].projects] == ["proj-2", "proj-1"]
    assert [project.id for project in collection.uncategorized_projects] == ["proj-3"]


def test_curiosities_remain_chronological_and_flexible() -> None:
    collection = build_curiosity_collection(
        [
            entry("cur-1", "2026-05-14", "curiosities", "texture: rough\n", ("01.jpg",)),
            entry("cur-2", "2026-08-29", "curiosities", "favorite: true\nshape: spiral\n"),
        ]
    )

    assert [item.id for item in collection.entries] == ["cur-2", "cur-1"]
    assert collection.entry_count == 2
    assert collection.photograph_count == 1
    assert collection.favorite_count == 1
