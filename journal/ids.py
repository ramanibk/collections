"""Permanent ID allocation for file-backed journal entries."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .parser import split_frontmatter


ID_PREFIXES = {
    "cloud": "obs",
    "bird": "obs",
    "cat": "cat",
    "project": "proj",
    "curiosity": "cur",
}
SEQUENCE_FILE = ".id-sequences.yaml"


def _stored_sequences(content_dir: Path) -> dict[str, int]:
    path = content_dir / SEQUENCE_FILE
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): value
        for key, value in raw.items()
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    }


def existing_ids(content_dir: Path) -> tuple[str, ...]:
    """Read IDs that can be recovered from existing entry frontmatter."""

    found: set[str] = set()
    if not content_dir.is_dir():
        return ()
    for source in sorted(content_dir.rglob("entry.md"), key=lambda path: path.as_posix()):
        try:
            metadata, _ = split_frontmatter(source.read_text(encoding="utf-8"), source)
        except (OSError, ValueError, yaml.YAMLError):
            continue
        entry_id = str(metadata.get("id") or "").strip()
        if entry_id:
            found.add(entry_id)
    return tuple(sorted(found))


def next_permanent_id(content_dir: Path, prefix: str) -> str:
    """Return one greater than the highest current sequence for ``prefix``.

    Gaps are deliberately not filled, which prevents ordinary deletions of older
    entries from causing their IDs to be reused.
    """

    normalized = prefix.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9]*", normalized):
        raise ValueError(f"invalid ID prefix {prefix!r}")
    pattern = re.compile(rf"^{re.escape(normalized)}-(\d+)$")
    highest = _stored_sequences(content_dir).get(normalized, 0)
    for entry_id in existing_ids(content_dir):
        match = pattern.fullmatch(entry_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{normalized}-{highest + 1:06d}"


def record_permanent_id(content_dir: Path, entry_id: str) -> None:
    """Persist a high-water mark so a deleted latest ID is never reused."""

    match = re.fullmatch(r"([a-z][a-z0-9]*)-(\d+)", entry_id)
    if not match:
        raise ValueError(f"invalid permanent ID {entry_id!r}")
    prefix, sequence_text = match.groups()
    sequences = _stored_sequences(content_dir)
    sequences[prefix] = max(sequences.get(prefix, 0), int(sequence_text))
    content_dir.mkdir(parents=True, exist_ok=True)
    destination = content_dir / SEQUENCE_FILE
    temporary = content_dir / f"{SEQUENCE_FILE}.tmp"
    temporary.write_text(yaml.safe_dump(sequences, sort_keys=True), encoding="utf-8")
    temporary.replace(destination)
