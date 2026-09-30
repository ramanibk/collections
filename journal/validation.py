"""Validation for the compact photo-and-note content model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from .models import ContentEntry


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    paths: Tuple[Path, ...] = ()

    def __str__(self) -> str:
        location = ", ".join(str(path) for path in self.paths)
        return f"{self.severity.value.upper()}: {self.message}" + (
            f" [{location}]" if location else ""
        )


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> Tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is Severity.ERROR)

    @property
    def warnings(self) -> Tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is Severity.WARNING)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def add_error(self, code: str, message: str, *paths: Path) -> None:
        self.issues.append(ValidationIssue(Severity.ERROR, code, message, tuple(paths)))

    def add_warning(self, code: str, message: str, *paths: Path) -> None:
        self.issues.append(ValidationIssue(Severity.WARNING, code, message, tuple(paths)))

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues.extend(issues)


COMMON_FIELDS = frozenset(
    {"id", "title", "date", "type", "slug", "location", "cover", "tags", "image_alt", "orientation"}
)
ENTRY_TYPES = frozenset({"photo", "note", "essay"})


def _validate_entry(entry: ContentEntry, report: ValidationReport) -> None:
    source = entry.source_path
    if entry.type not in ENTRY_TYPES:
        report.add_error("unsupported_type", "type must be 'photo', 'note', or 'essay'", source)
    if entry.type == "photo" and not entry.images:
        report.add_error("missing_photo", "photo entries require at least one image", source)
    if entry.orientation not in {"portrait", "landscape"}:
        report.add_error(
            "invalid_orientation", "orientation must be 'portrait' or 'landscape'", source
        )
    declared_cover = entry.raw_frontmatter.get("cover")
    if declared_cover not in (None, "") and str(declared_cover) not in entry.images:
        report.add_error(
            "missing_media", f"referenced cover image {declared_cover!r} does not exist", source
        )
    for key in sorted(set(entry.raw_frontmatter) - COMMON_FIELDS):
        report.add_warning(
            "unknown_metadata", f"unknown metadata field {key!r} was preserved", source
        )


def validate_entries(entries: Sequence[ContentEntry]) -> ValidationReport:
    report = ValidationReport()
    entries_by_id = {}
    for entry in entries:
        entries_by_id.setdefault(entry.id, []).append(entry)
        _validate_entry(entry, report)
    for entry_id, duplicates in sorted(entries_by_id.items()):
        if len(duplicates) > 1:
            paths = tuple(sorted((entry.source_path for entry in duplicates), key=str))
            report.add_error("duplicate_id", f"duplicate permanent ID {entry_id!r}", *paths)
    return report


def format_report(report: ValidationReport) -> str:
    lines = []
    for issue in report.issues:
        lines.append(f"{issue.severity.value.upper()} {issue.code}: {issue.message}")
        lines.extend(f"  - {path}" for path in issue.paths)
    lines.append(f"Validation: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return "\n".join(lines)
