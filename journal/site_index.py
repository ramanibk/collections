"""Concise alphabetical index derived from useful archive concepts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .cats import CatCollection
from .clouds import CloudAtlas
from .making import MakingCollection
from .models import ContentEntry
from .birds import BirdNotebook


@dataclass(frozen=True)
class IndexItem:
    label: str
    kind: str
    value: str
    count: int
    count_name: str

    @property
    def count_text(self) -> str:
        if self.count == 1:
            noun = self.count_name
        elif self.count_name == "entry":
            noun = "entries"
        else:
            noun = f"{self.count_name}s"
        return f"{self.count} {noun}"


@dataclass(frozen=True)
class IndexGroup:
    letter: str
    items: Tuple[IndexItem, ...]


CATEGORY_LABELS = {
    "birds": "Birds",
    "cats": "Cats",
    "clouds": "Clouds",
    "curiosities": "Curiosities",
    "making": "Making",
}


def build_alphabetical_index(
    entries: Iterable[ContentEntry],
    clouds: CloudAtlas,
    birds: BirdNotebook,
    cats: CatCollection,
    making: MakingCollection,
) -> Tuple[IndexGroup, ...]:
    items = []
    content = tuple(entries)
    for category, label in CATEGORY_LABELS.items():
        count = sum(entry.category == category for entry in content)
        count_name = "project" if category == "making" else "entry"
        if category in {"clouds", "birds"}:
            count_name = "observation"
        items.append(IndexItem(label, "category", category, count, count_name))

    items.extend(
        IndexItem(page.name.title(), "cloud", page.name, page.sighting_count, "observation")
        for page in clouds.genus_pages
    )
    items.extend(
        IndexItem(page.common_name, "bird", page.common_name, page.sighting_count, "observation")
        for page in birds.species_pages
    )
    items.extend(
        IndexItem(profile.name, "cat", profile.name, profile.entry_count, "entry")
        for profile in cats.profiles
    )
    items.extend(
        IndexItem(page.name, "craft", page.name, page.project_count, "project")
        for page in making.craft_pages
    )

    by_letter: Dict[str, List[IndexItem]] = {}
    for item in items:
        first = item.label[0].upper() if item.label else "#"
        letter = first if first.isalpha() else "#"
        by_letter.setdefault(letter, []).append(item)
    return tuple(
        IndexGroup(
            letter,
            tuple(sorted(by_letter[letter], key=lambda item: (item.label.casefold(), item.kind))),
        )
        for letter in sorted(by_letter, key=lambda value: (value == "#", value))
    )
