from pathlib import Path

from journal.cats import build_cat_collection
from journal.parser import parse_entry_text


def cat(
    entry_id: str,
    entry_date: str,
    cat_name: str = "",
    relationship: str = "",
    images=(),
):
    fields = ""
    if cat_name:
        fields += f"cat_name: {cat_name}\n"
    if relationship:
        fields += f"relationship: {relationship}\n"
    text = f"""---
id: {entry_id}
title: Cat {entry_id}
date: {entry_date}
type: cat
category: cats
{fields}---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"), images)


def test_collection_always_has_exactly_three_ordered_profiles() -> None:
    collection = build_cat_collection([])

    assert [profile.name for profile in collection.profiles] == ["Gwen", "Billy", "Jet"]
    assert all(profile.entries == () for profile in collection.profiles)
    assert collection.encounters == ()


def test_profile_combines_case_insensitive_entries_and_photographs() -> None:
    collection = build_cat_collection(
        [
            cat("cat-1", "2026-05-14", "Gwen", "mine", ("01.jpg", "02.jpg")),
            cat("cat-2", "2026-08-29", "gwen", images=("portrait.jpg",)),
        ]
    )
    gwen = collection.profiles[0]

    assert [entry.id for entry in gwen.entries] == ["cat-2", "cat-1"]
    assert [(photo.entry.id, photo.filename) for photo in gwen.photographs] == [
        ("cat-2", "portrait.jpg"),
        ("cat-1", "02.jpg"),
        ("cat-1", "01.jpg"),
    ]
    assert gwen.first_entry.isoformat() == "2026-05-14"
    assert gwen.most_recent_entry.isoformat() == "2026-08-29"
    assert collection.total_entries == 2
    assert collection.total_photographs == 3


def test_unnamed_and_explicit_encounter_entries_are_separate() -> None:
    collection = build_cat_collection(
        [
            cat("cat-1", "2026-05-14"),
            cat("cat-2", "2026-08-29", "Billy", "encounter"),
            cat("cat-3", "2026-08-30", "Jet", "mine"),
        ]
    )

    assert [entry.id for entry in collection.encounters] == ["cat-2", "cat-1"]
    assert [entry.id for entry in collection.profiles[2].entries] == ["cat-3"]
