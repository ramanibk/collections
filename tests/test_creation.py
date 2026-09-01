import shutil
from pathlib import Path

import pytest

from journal.creation import CreationError, create_cloud_entry, create_project_entry
from journal.ids import next_permanent_id
from journal.parser import parse_entry


def write_existing(content: Path, entry_id: str, folder: str) -> None:
    destination = content / "clouds" / folder
    destination.mkdir(parents=True)
    (destination / "entry.md").write_text(
        f"""---
id: {entry_id}
title: Existing
date: 2026-08-01
category: clouds
---
""",
        encoding="utf-8",
    )


def test_next_permanent_id_uses_highest_sequence_without_filling_gaps(tmp_path: Path) -> None:
    content = tmp_path / "content"
    write_existing(content, "obs-000001", "one")
    write_existing(content, "obs-000009", "nine")

    assert next_permanent_id(content, "obs") == "obs-000010"
    assert next_permanent_id(content, "cat") == "cat-000001"


def test_create_cloud_entry_copies_images_and_writes_parseable_frontmatter(tmp_path: Path) -> None:
    first = tmp_path / "camera-a" / "Cloud.JPG"
    second = tmp_path / "camera-b" / "Cloud.JPG"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    created = create_cloud_entry(
        tmp_path,
        title="Altocumulus Before Sunset",
        entry_date="2026-08-31",
        image_paths=(first, second),
        location="Berkeley, California",
        tags="clouds, sunset",
        notes="Rounded cloudlets before sunset.",
        cloud_genus="altocumulus",
        confidence=4,
    )

    assert created.entry_id == "obs-000001"
    assert created.image_names == ("cloud.jpg", "cloud-2.jpg")
    assert (created.directory / "cloud.jpg").read_bytes() == b"first"
    entry = parse_entry(created.source_path)
    assert entry.title == "Altocumulus Before Sunset"
    assert entry.cover == "cloud.jpg"
    assert entry.tags == ("clouds", "sunset")
    assert entry.metadata.genus == "altocumulus"
    assert entry.body_markdown == "Rounded cloudlets before sunset."


def test_create_project_uses_completion_date_and_project_prefix(tmp_path: Path) -> None:
    created = create_project_entry(
        tmp_path,
        title="Wildflower Hoop",
        craft="Embroidery",
        status="completed",
        started="2026-08-01",
        completed="2026-08-19",
        materials="linen, cotton floss",
    )

    entry = parse_entry(created.source_path)
    assert created.entry_id == "proj-000001"
    assert entry.date.isoformat() == "2026-08-19"
    assert entry.metadata.materials == ("linen", "cotton floss")


def test_created_high_water_mark_prevents_reusing_deleted_latest_id(tmp_path: Path) -> None:
    created = create_cloud_entry(tmp_path, title="Temporary cloud")
    shutil.rmtree(created.directory)

    assert next_permanent_id(tmp_path / "content", "obs") == "obs-000002"


def test_creation_validates_images_before_creating_destination(tmp_path: Path) -> None:
    with pytest.raises(CreationError, match="image does not exist"):
        create_cloud_entry(
            tmp_path,
            title="No Image",
            image_paths=(tmp_path / "missing.jpg",),
        )

    assert not (tmp_path / "content").exists()


def test_creation_rejects_invalid_category_metadata_without_leaving_entry(tmp_path: Path) -> None:
    with pytest.raises(CreationError, match="confidence must be between 1 and 5"):
        create_cloud_entry(tmp_path, title="Uncertain cloud", confidence=9)

    assert not tuple((tmp_path / "content/clouds").glob("*/entry.md"))
