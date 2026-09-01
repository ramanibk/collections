from pathlib import Path

from journal.birds import build_bird_notebook
from journal.cats import build_cat_collection
from journal.clouds import build_cloud_atlas
from journal.making import build_making_collection
from journal.parser import parse_entry_text
from journal.site_index import build_alphabetical_index


def entry(entry_id: str, category: str, extra: str = ""):
    type_name = "project" if category == "making" else "observation"
    text = f"""---
id: {entry_id}
title: {entry_id} title
date: 2026-09-01
type: {type_name}
category: {category}
{extra}---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"))


def test_index_contains_useful_concepts_but_not_tags() -> None:
    entries = [
        entry("obs-1", "clouds", "cloud_genus: altocumulus\ntags: [sunset]\n"),
        entry("obs-2", "birds", "common_name: House Finch\n"),
        entry("proj-1", "making", "craft: Embroidery\n"),
    ]
    groups = build_alphabetical_index(
        entries,
        build_cloud_atlas(entries),
        build_bird_notebook(entries),
        build_cat_collection(entries),
        build_making_collection(entries),
    )
    items = [item for group in groups for item in group.items]

    assert [group.letter for group in groups] == sorted(group.letter for group in groups)
    assert {"Altocumulus", "Billy", "Embroidery", "Gwen", "House Finch", "Jet"}.issubset(
        {item.label for item in items}
    )
    assert "sunset" not in {item.label for item in items}
    house_finch = next(item for item in items if item.label == "House Finch")
    assert (house_finch.kind, house_finch.count) == ("bird", 1)
    cats = next(item for item in items if item.label == "Cats")
    assert cats.count_text == "0 entries"
