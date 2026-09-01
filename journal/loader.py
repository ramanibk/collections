"""Deterministic collection-wide content loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .models import ContentEntry
from .parser import ContentParseError, parse_entry
from .validation import ValidationReport, validate_entries


@dataclass(frozen=True)
class LoadResult:
    entries: Tuple[ContentEntry, ...]
    report: ValidationReport

    @property
    def is_valid(self) -> bool:
        return self.report.is_valid


def load_content(content_dir: Path) -> LoadResult:
    """Parse every entry and return all ordinary content issues at once."""

    parse_report = ValidationReport()
    entries = []
    if not content_dir.exists():
        parse_report.add_error(
            "missing_content_directory",
            "content directory does not exist",
            content_dir,
        )
        return LoadResult((), parse_report)
    if not content_dir.is_dir():
        parse_report.add_error(
            "invalid_content_directory",
            "content path is not a directory",
            content_dir,
        )
        return LoadResult((), parse_report)

    sources = sorted(content_dir.rglob("entry.md"), key=lambda path: path.as_posix())
    for source in sources:
        try:
            entries.append(parse_entry(source))
        except ContentParseError as exc:
            message = str(exc)
            source_prefix = f"{source}: "
            if message.startswith(source_prefix):
                message = message[len(source_prefix) :]
            parse_report.add_error("parse_error", message, source)

    entries.sort(
        key=lambda entry: (entry.date, entry.title.casefold(), entry.id),
        reverse=True,
    )
    validation_report = validate_entries(entries)
    parse_report.extend(validation_report.issues)
    return LoadResult(tuple(entries), parse_report)
