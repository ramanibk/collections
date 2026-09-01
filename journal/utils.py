"""Small dependency-free helpers shared by journal layers."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    """Create a predictable ASCII URL slug."""

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower().strip()).strip("-") or "untitled"
