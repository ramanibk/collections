"""Chronological journal and yearly archive derivation."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .models import ContentEntry


@dataclass(frozen=True)
class MonthArchive:
    year: int
    month: int
    entries: Tuple[ContentEntry, ...]

    @property
    def label(self) -> str:
        return f"{calendar.month_name[self.month]} {self.year}"


@dataclass(frozen=True)
class YearArchive:
    year: int
    months: Tuple[MonthArchive, ...]
    entry_count: int
    category_count: int
    photograph_count: int


@dataclass(frozen=True)
class JournalArchive:
    years: Tuple[YearArchive, ...]
    total_entries: int


def build_journal_archive(entries: Iterable[ContentEntry]) -> JournalArchive:
    ordered = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.date, entry.title.casefold(), entry.id),
            reverse=True,
        )
    )
    by_year_month: Dict[Tuple[int, int], List[ContentEntry]] = {}
    for entry in ordered:
        by_year_month.setdefault((entry.date.year, entry.date.month), []).append(entry)

    years = []
    for year in sorted({entry.date.year for entry in ordered}, reverse=True):
        year_entries = tuple(entry for entry in ordered if entry.date.year == year)
        months = tuple(
            MonthArchive(year, month, tuple(by_year_month[(year, month)]))
            for month in sorted(
                (month for candidate_year, month in by_year_month if candidate_year == year),
                reverse=True,
            )
        )
        years.append(
            YearArchive(
                year=year,
                months=months,
                entry_count=len(year_entries),
                category_count=len({entry.category for entry in year_entries}),
                photograph_count=sum(len(entry.images) for entry in year_entries),
            )
        )
    return JournalArchive(tuple(years), len(ordered))
