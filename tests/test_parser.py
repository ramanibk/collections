from datetime import date
from pathlib import Path

import pytest

from journal.models import CatMetadata, CloudMetadata, ProjectMetadata
from journal.parser import ContentParseError, parse_entry, parse_entry_text


VALID_ENTRY = """---
id: obs-000001
title: Altocumulus Before Sunset
date: 2026-08-31
type: observation
category: clouds
cloud_genus: altocumulus
supplementary_features: []
tags: [clouds, sunset]
favorite: true
unknown_future_field: preserved
---
A broad field of **rounded cloudlets** appeared.
"""


def test_valid_frontmatter_and_markdown_body() -> None:
    entry = parse_entry_text(VALID_ENTRY, Path("entry.md"), ("01.jpg",))

    assert entry.id == "obs-000001"
    assert entry.date == date(2026, 8, 31)
    assert entry.slug == "altocumulus-before-sunset"
    assert entry.body_markdown.startswith("A broad field")
    assert "<strong>rounded cloudlets</strong>" in entry.body_html
    assert entry.cover == "01.jpg"
    assert entry.tags == ("clouds", "sunset")
    assert entry.raw_frontmatter["unknown_future_field"] == "preserved"
    assert isinstance(entry.metadata, CloudMetadata)
    assert entry.metadata.genus == "altocumulus"


@pytest.mark.parametrize("text", ["No frontmatter", "---\ntitle: Broken\n"])
def test_malformed_frontmatter(text: str) -> None:
    with pytest.raises(ContentParseError, match="frontmatter"):
        parse_entry_text(text, Path("entry.md"))


def test_missing_required_field() -> None:
    text = "---\nid: cur-000001\ntitle: Note\ncategory: curiosities\n---\nBody"

    with pytest.raises(ContentParseError, match="date"):
        parse_entry_text(text, Path("entry.md"))


def test_bad_date() -> None:
    text = VALID_ENTRY.replace("2026-08-31", "08/31/26")

    with pytest.raises(ContentParseError, match="YYYY-MM-DD"):
        parse_entry_text(text, Path("entry.md"))


def test_cat_slug_uses_cat_name() -> None:
    text = """---
id: cat-000001
title: Sleeping in the Window
date: 2026-08-31
type: cat
category: cats
cat_name: Miso
relationship: mine
---
Nap time.
"""
    entry = parse_entry_text(text, Path("entry.md"))

    assert entry.slug == "miso"
    assert isinstance(entry.metadata, CatMetadata)


def test_project_dates_are_normalized() -> None:
    text = """---
id: proj-000001
title: Wildflower Hoop
date: 2026-08-31
type: project
category: making
started: 2026-08-01
completed:
materials: [linen, thread]
---
In progress.
"""
    entry = parse_entry_text(text, Path("entry.md"))

    assert isinstance(entry.metadata, ProjectMetadata)
    assert entry.metadata.started == date(2026, 8, 1)
    assert entry.metadata.completed is None
    assert entry.metadata.materials == ("linen", "thread")


def test_image_discovery_is_supported_hidden_free_and_sorted(tmp_path: Path) -> None:
    entry_dir = tmp_path / "observation"
    entry_dir.mkdir()
    (entry_dir / "entry.md").write_text(VALID_ENTRY, encoding="utf-8")
    for name in ("10.webp", "02.PNG", "01.jpg", ".hidden.jpg", "notes.txt", "movie.gif"):
        (entry_dir / name).touch()

    entry = parse_entry(entry_dir / "entry.md")

    assert entry.images == ("01.jpg", "02.PNG", "10.webp")
    assert entry.cover == "01.jpg"
