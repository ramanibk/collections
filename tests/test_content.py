from pathlib import Path

import pytest

from journal.creation import CreationError, create_note_entry, create_photo_entry
from journal.loader import load_content
from journal.parser import ContentParseError, parse_about_text, parse_entry_text


def entry_text(**overrides: str) -> str:
    fields = {"id": "note-000001", "title": "A note", "date": "2026-09-01", "type": "note"}
    fields.update(overrides)
    metadata = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{metadata}\n---\nBody.\n"


def test_parser_normalizes_tags_and_renders_markdown() -> None:
    text = entry_text(tags='[" Systems ", systems, field-note]')
    entry = parse_entry_text(text, Path("entry.md"))

    assert entry.tags == ("Systems", "field-note")
    assert entry.body_html == "<p>Body.</p>"


def test_parser_requires_the_compact_common_fields() -> None:
    with pytest.raises(ContentParseError, match="type"):
        parse_entry_text(entry_text(type=""), Path("entry.md"))


def test_about_markdown_parses_content_and_links() -> None:
    about = parse_about_text(
        """---
title: Example Person
portrait_url: /portrait.jpg
links:
  - label: Profile
    url: https://example.com
---
Builds **durable** things.
""",
        Path("about.md"),
    )

    assert about.title == "Example Person"
    assert "<strong>durable</strong>" in about.body_html
    assert about.links[0].label == "Profile"


def test_creation_builds_photo_and_note_entries(tmp_path: Path) -> None:
    image = tmp_path / "image.jpg"
    image.write_bytes(b"image")

    photo = create_photo_entry(
        tmp_path,
        title="Window light",
        image_paths=(image,),
        orientation="portrait",
        tags="light, quiet, Light",
    )
    note = create_note_entry(tmp_path, title="Working note", tags="systems")

    loaded = load_content(tmp_path / "content")
    assert loaded.is_valid
    assert photo.entry_id == "photo-000001"
    assert note.entry_id == "note-000001"
    assert {entry.type for entry in loaded.entries} == {"photo", "note"}
    assert next(entry for entry in loaded.entries if entry.type == "photo").tags == (
        "light",
        "quiet",
    )


def test_photo_creation_requires_an_image(tmp_path: Path) -> None:
    with pytest.raises(CreationError, match="require an image"):
        create_photo_entry(tmp_path, title="Missing image")


def test_validation_rejects_unknown_types_and_orientations(tmp_path: Path) -> None:
    bad = tmp_path / "content" / "notes" / "bad"
    bad.mkdir(parents=True)
    (bad / "entry.md").write_text(entry_text(type="memo", orientation="square"), encoding="utf-8")

    report = load_content(tmp_path / "content").report
    assert {issue.code for issue in report.errors} == {"unsupported_type", "invalid_orientation"}
