"""Content validation with structured errors and warnings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from .models import BirdMetadata, CatMetadata, CloudMetadata, ContentEntry, ProjectMetadata
from .cats import MY_CATS
from .taxonomy import CATEGORIES


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
        suffix = f" [{location}]" if location else ""
        return f"{self.severity.value.upper()}: {self.message}{suffix}"


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
    {
        "id",
        "title",
        "date",
        "type",
        "category",
        "slug",
        "location",
        "cover",
        "favorite",
        "tags",
        "status",
        "image_alt",
        "margin_note",
        "sample",
    }
)

CATEGORY_FIELDS = {
    "clouds": frozenset(
        {
            "cloud_genus",
            "cloud_species",
            "cloud_variety",
            "supplementary_features",
            "optical_phenomena",
            "identification",
            "confidence",
        }
    ),
    "birds": frozenset(
        {"common_name", "scientific_name", "identification", "confidence", "count"}
    ),
    "cats": frozenset({"cat_name", "relationship"}),
    "making": frozenset({"craft", "started", "completed", "materials"}),
    # Curiosities intentionally accept arbitrary metadata.
    "curiosities": frozenset(),
}

PROJECT_STATUSES = frozenset(
    {"idea", "planned", "in-progress", "paused", "completed", "abandoned"}
)


def _validate_entry(entry: ContentEntry, report: ValidationReport) -> None:
    source = entry.source_path
    if entry.category not in CATEGORIES:
        report.add_error(
            "unsupported_category",
            f"unsupported category {entry.category!r}; expected one of {', '.join(CATEGORIES)}",
            source,
        )
        return

    declared_cover = entry.raw_frontmatter.get("cover")
    if declared_cover not in (None, "") and str(declared_cover) not in entry.images:
        report.add_error(
            "missing_media",
            f"referenced cover image {str(declared_cover)!r} does not exist",
            source,
        )

    confidence = None
    if isinstance(entry.metadata, (CloudMetadata, BirdMetadata)):
        confidence = entry.metadata.confidence
    if confidence is not None and not 1 <= confidence <= 5:
        report.add_error(
            "invalid_confidence",
            f"confidence must be between 1 and 5, got {confidence}",
            source,
        )

    if entry.category == "cats" and isinstance(entry.metadata, CatMetadata):
        cat_name = (entry.metadata.cat_name or "").strip()
        relationship = (entry.metadata.relationship or "").strip().casefold()
        allowed_names = {name.casefold() for name in MY_CATS}
        if cat_name and cat_name.casefold() not in allowed_names:
            report.add_error(
                "unsupported_cat_name",
                f"cat_name must be one of {', '.join(MY_CATS)}; got {cat_name!r}",
                source,
            )
        if relationship and relationship not in {"mine", "encounter"}:
            report.add_error(
                "invalid_cat_relationship",
                "relationship must be 'mine' or 'encounter'",
                source,
            )
        if relationship == "mine" and not cat_name:
            report.add_error(
                "missing_cat_name",
                "a cat entry with relationship 'mine' requires cat_name",
                source,
            )

    if entry.category == "making" and isinstance(entry.metadata, ProjectMetadata):
        status = (entry.metadata.status or "").strip().casefold()
        if status and status not in PROJECT_STATUSES:
            report.add_error(
                "invalid_project_status",
                f"unsupported project status {entry.metadata.status!r}",
                source,
            )
        if (
            entry.metadata.started
            and entry.metadata.completed
            and entry.metadata.completed < entry.metadata.started
        ):
            report.add_error(
                "invalid_project_dates",
                "completed date cannot be before started date",
                source,
            )

    if entry.category != "curiosities":
        known = COMMON_FIELDS | CATEGORY_FIELDS[entry.category]
        for key in sorted(set(entry.raw_frontmatter) - known):
            report.add_warning(
                "unknown_metadata",
                f"unknown metadata field {key!r} was preserved",
                source,
            )


def validate_entries(entries: Sequence[ContentEntry]) -> ValidationReport:
    """Validate normalized entries, including collection-wide invariants."""

    report = ValidationReport()
    entries_by_id = {}
    for entry in entries:
        entries_by_id.setdefault(entry.id, []).append(entry)
        _validate_entry(entry, report)

    for entry_id, duplicates in sorted(entries_by_id.items()):
        if len(duplicates) > 1:
            paths = tuple(sorted((entry.source_path for entry in duplicates), key=str))
            report.add_error(
                "duplicate_id",
                f"duplicate permanent ID {entry_id!r}",
                *paths,
            )
    return report


def format_report(report: ValidationReport) -> str:
    """Create concise, deterministic text suitable for a CLI or build log."""

    lines = []
    for issue in report.issues:
        lines.append(f"{issue.severity.value.upper()} {issue.code}: {issue.message}")
        lines.extend(f"  - {path}" for path in issue.paths)
    lines.append(
        f"Validation: {len(report.errors)} error(s), {len(report.warnings)} warning(s)"
    )
    return "\n".join(lines)
