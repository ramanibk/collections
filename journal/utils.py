"""Small dependency-free helpers shared by journal layers."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable


def slugify(value: str) -> str:
    """Create a predictable ASCII URL slug."""

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower().strip()).strip("-") or "untitled"


def normalize_tags(values: Iterable[object]) -> tuple[str, ...]:
    """Trim tags and remove case-insensitive duplicates while preserving display case."""

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = str(value).strip()
        key = tag.casefold()
        if tag and key not in seen:
            normalized.append(tag)
            seen.add(key)
    return tuple(normalized)
