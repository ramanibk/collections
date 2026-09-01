"""Central taxonomy data; templates should not define these groups."""

from __future__ import annotations

from typing import Tuple


CLOUD_GROUPS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("High", ("cirrus", "cirrostratus", "cirrocumulus")),
    ("Middle", ("altocumulus", "altostratus", "nimbostratus")),
    ("Low", ("stratus", "stratocumulus")),
    ("Vertical Development", ("cumulus", "cumulonimbus")),
)

CATEGORIES = ("clouds", "birds", "cats", "making", "curiosities")
