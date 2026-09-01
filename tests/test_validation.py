from pathlib import Path

from journal.loader import load_content
from journal.parser import parse_entry_text
from journal.validation import Severity, format_report, validate_entries


def entry_text(entry_id: str, **overrides: object) -> str:
    fields = {
        "id": entry_id,
        "title": "Field Note",
        "date": "2026-09-01",
        "type": "observation",
        "category": "clouds",
    }
    fields.update(overrides)
    frontmatter = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{frontmatter}\n---\nBody.\n"


def write_entry(root: Path, folder: str, text: str) -> Path:
    directory = root / folder
    directory.mkdir(parents=True)
    source = directory / "entry.md"
    source.write_text(text, encoding="utf-8")
    return source


def test_loader_recurses_and_sorts_entries_deterministically(tmp_path: Path) -> None:
    write_entry(tmp_path, "clouds/older", entry_text("obs-000001", date="2025-01-01", title="Old"))
    write_entry(tmp_path, "birds/newer", entry_text("obs-000002", date="2026-01-01", title="New", category="birds"))

    result = load_content(tmp_path)

    assert result.is_valid
    assert [entry.id for entry in result.entries] == ["obs-000002", "obs-000001"]


def test_loader_collects_parse_errors_and_keeps_valid_entries(tmp_path: Path) -> None:
    write_entry(tmp_path, "good", entry_text("obs-000001"))
    write_entry(tmp_path, "bad-date", entry_text("obs-000002", date="09/01/26"))
    write_entry(tmp_path, "bad-yaml", "---\ntitle: [broken\n---\nBody")

    result = load_content(tmp_path)

    assert [entry.id for entry in result.entries] == ["obs-000001"]
    assert len(result.report.errors) == 2
    assert all(issue.code == "parse_error" for issue in result.report.errors)


def test_duplicate_ids_report_every_source(tmp_path: Path) -> None:
    first = write_entry(tmp_path, "one", entry_text("obs-000014"))
    second = write_entry(tmp_path, "two", entry_text("obs-000014", title="Another"))

    report = load_content(tmp_path).report
    issue = next(issue for issue in report.errors if issue.code == "duplicate_id")

    assert issue.paths == tuple(sorted((first, second), key=str))
    assert "obs-000014" in issue.message


def test_unsupported_category_is_an_error() -> None:
    entry = parse_entry_text(entry_text("obs-000001", category="rocks"), Path("entry.md"))

    report = validate_entries([entry])

    assert any(issue.code == "unsupported_category" for issue in report.errors)


def test_missing_cover_is_an_error(tmp_path: Path) -> None:
    source = write_entry(tmp_path, "cloud", entry_text("obs-000001", cover="missing.jpg"))

    report = load_content(tmp_path).report

    issue = next(issue for issue in report.errors if issue.code == "missing_media")
    assert issue.paths == (source,)


def test_invalid_confidence_is_an_error() -> None:
    entry = parse_entry_text(entry_text("obs-000001", confidence=6), Path("entry.md"))

    report = validate_entries([entry])

    assert any(issue.code == "invalid_confidence" for issue in report.errors)


def test_unknown_optional_metadata_is_preserved_with_warning() -> None:
    entry = parse_entry_text(entry_text("obs-000001", weather="windy"), Path("entry.md"))

    report = validate_entries([entry])

    issue = next(issue for issue in report.warnings if issue.code == "unknown_metadata")
    assert issue.severity is Severity.WARNING
    assert entry.raw_frontmatter["weather"] == "windy"


def test_curiosity_metadata_remains_deliberately_flexible() -> None:
    entry = parse_entry_text(
        entry_text("cur-000001", category="curiosities", type="curiosity", texture="rough"),
        Path("entry.md"),
    )

    report = validate_entries([entry])

    assert report.is_valid
    assert not report.warnings


def test_named_cats_are_limited_to_gwen_billy_and_jet() -> None:
    entry = parse_entry_text(
        entry_text(
            "cat-000001",
            category="cats",
            type="cat",
            cat_name="Miso",
            relationship="mine",
        ),
        Path("entry.md"),
    )

    report = validate_entries([entry])

    issue = next(issue for issue in report.errors if issue.code == "unsupported_cat_name")
    assert "Gwen, Billy, Jet" in issue.message


def test_my_cat_entries_require_a_name_and_valid_relationship() -> None:
    unnamed = parse_entry_text(
        entry_text("cat-000001", category="cats", type="cat", relationship="mine"),
        Path("unnamed/entry.md"),
    )
    invalid = parse_entry_text(
        entry_text(
            "cat-000002",
            category="cats",
            type="cat",
            cat_name="Gwen",
            relationship="friend",
        ),
        Path("invalid/entry.md"),
    )

    report = validate_entries([unnamed, invalid])

    assert any(issue.code == "missing_cat_name" for issue in report.errors)
    assert any(issue.code == "invalid_cat_relationship" for issue in report.errors)


def test_project_status_and_date_order_are_validated() -> None:
    entry = parse_entry_text(
        entry_text(
            "proj-000001",
            category="making",
            type="project",
            status="finished-ish",
            started="2026-09-01",
            completed="2026-08-01",
        ),
        Path("entry.md"),
    )

    report = validate_entries([entry])

    assert any(issue.code == "invalid_project_status" for issue in report.errors)
    assert any(issue.code == "invalid_project_dates" for issue in report.errors)


def test_formatted_report_distinguishes_errors_and_warnings() -> None:
    entry = parse_entry_text(
        entry_text("obs-000001", cover="missing.jpg", weather="windy"),
        Path("entry.md"),
    )

    text = format_report(validate_entries([entry]))

    assert "ERROR missing_media" in text
    assert "WARNING unknown_metadata" in text
    assert "Validation: 1 error(s), 1 warning(s)" in text
