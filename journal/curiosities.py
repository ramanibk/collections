"""Derived Curiosities collection data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .models import ContentEntry


@dataclass(frozen=True)
class CuriosityCollection:
    entries: Tuple[ContentEntry, ...]
    photograph_count: int
    favorite_count: int

    @property
    def entry_count(self) -> int:
        return len(self.entries)


def build_curiosity_collection(entries: Iterable[ContentEntry]) -> CuriosityCollection:
    curiosities = tuple(
        sorted(
            (entry for entry in entries if entry.category == "curiosities"),
            key=lambda entry: (entry.date, entry.title.casefold(), entry.id),
            reverse=True,
        )
    )
    return CuriosityCollection(
        entries=curiosities,
        photograph_count=sum(len(entry.images) for entry in curiosities),
        favorite_count=sum(entry.favorite for entry in curiosities),
    )
