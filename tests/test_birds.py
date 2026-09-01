from pathlib import Path

from journal.birds import build_bird_notebook
from journal.parser import parse_entry_text


def bird(
    entry_id: str,
    entry_date: str,
    common_name: str = "",
    scientific_name: str = "",
    identification: str = "",
):
    fields = ""
    if common_name:
        fields += f"common_name: {common_name}\n"
    if scientific_name:
        fields += f"scientific_name: {scientific_name}\n"
    if identification:
        fields += f"identification: {identification}\n"
    text = f"""---
id: {entry_id}
title: Bird {entry_id}
date: {entry_date}
type: observation
category: birds
{fields}---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"))


def test_notebook_statistics_species_order_and_unknown_observations() -> None:
    notebook = build_bird_notebook(
        [
            bird("obs-1", "2026-05-14", "House Finch", identification="confirmed"),
            bird("obs-2", "2026-08-29", "California Scrub-Jay", identification="tentative"),
            bird("obs-3", "2026-08-30", identification="unknown"),
            bird("obs-4", "2026-08-31", "house finch", identification="self-identified"),
            bird("obs-5", "2026-09-01", "Mystery bird", identification="unknown"),
        ]
    )

    assert notebook.statistics.total_observations == 5
    assert notebook.statistics.unique_species == 2
    assert notebook.statistics.confirmed_identifications == 2
    assert notebook.statistics.tentative_identifications == 1
    assert notebook.statistics.unknown_identifications == 2
    assert [page.common_name for page in notebook.species_pages] == [
        "California Scrub-Jay",
        "House Finch",
    ]
    assert [entry.id for entry in notebook.unidentified] == ["obs-5", "obs-3"]


def test_species_page_dates_name_and_sighting_order() -> None:
    notebook = build_bird_notebook(
        [
            bird("obs-1", "2026-05-14", "Dark-eyed Junco", "Junco hyemalis", "confirmed"),
            bird("obs-2", "2026-08-29", "dark-eyed junco", identification="tentative"),
            bird("obs-3", "2026-06-01", "Dark-eyed Junco", identification="confirmed"),
        ]
    )
    species = notebook.species_pages[0]

    assert species.common_name == "Dark-eyed Junco"
    assert species.scientific_name == "Junco hyemalis"
    assert species.first_sighting.isoformat() == "2026-05-14"
    assert species.most_recent_sighting.isoformat() == "2026-08-29"
    assert [entry.id for entry in species.sightings] == ["obs-2", "obs-3", "obs-1"]


def test_blank_species_names_do_not_create_pages() -> None:
    notebook = build_bird_notebook([bird("obs-1", "2026-05-14")])

    assert notebook.species_pages == ()
    assert [entry.id for entry in notebook.unidentified] == ["obs-1"]
