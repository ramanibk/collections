from pathlib import Path

from journal.archives import build_journal_archive
from journal.parser import parse_entry_text


def entry(entry_id: str, entry_date: str, category: str = "clouds"):
    text = f"""---
id: {entry_id}
title: {entry_id} title
date: {entry_date}
type: observation
category: {category}
---
Body.
"""
    return parse_entry_text(text, Path(f"{entry_id}/entry.md"))


def test_journal_groups_years_and_months_in_reverse_chronological_order() -> None:
    archive = build_journal_archive(
        [
            entry("obs-1", "2025-12-31"),
            entry("obs-2", "2026-01-01", "birds"),
            entry("obs-3", "2026-08-29", "cats"),
            entry("obs-4", "2026-08-30"),
        ]
    )

    assert archive.total_entries == 4
    assert [year.year for year in archive.years] == [2026, 2025]
    year = archive.years[0]
    assert [month.label for month in year.months] == ["August 2026", "January 2026"]
    assert [item.id for item in year.months[0].entries] == ["obs-4", "obs-3"]
    assert year.entry_count == 3
    assert year.category_count == 3


def test_empty_journal_has_no_year_pages() -> None:
    archive = build_journal_archive([])

    assert archive.total_entries == 0
    assert archive.years == ()
