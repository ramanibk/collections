import io
import shutil
from pathlib import Path

import pytest

from journal.cli import _strip_preview_base, main

REPOSITORY = Path(__file__).resolve().parents[1]


def minimal_project(tmp_path: Path) -> Path:
    root = tmp_path / "archive"
    root.mkdir()
    shutil.copytree(REPOSITORY / "templates", root / "templates")
    shutil.copytree(REPOSITORY / "static", root / "static")
    (root / "content").mkdir()
    (root / "content/about.md").write_text(
        """---
title: Example Person
portrait_url: /portrait.jpg
---
About this archive.
""",
        encoding="utf-8",
    )
    (root / "config.yaml").write_text("build:\n  output_dir: public\n", encoding="utf-8")
    return root


def test_cli_adds_note_and_builds(tmp_path: Path) -> None:
    root = minimal_project(tmp_path)
    answers = iter(["A small note", "2026-09-01", "systems", "Remember this."])
    output = io.StringIO()

    assert (
        main(["add", "note"], project_root=root, input_func=lambda _: next(answers), output=output)
        == 0
    )
    assert "Created note-000001" in output.getvalue()
    assert main(["build"], project_root=root, output=io.StringIO()) == 0
    assert (root / "public/notes/index.html").exists()


def test_cli_no_longer_exposes_old_categories_or_stats(tmp_path: Path) -> None:
    root = minimal_project(tmp_path)

    with pytest.raises(SystemExit, match="2"):
        main(["add", "cloud"], project_root=root)
    with pytest.raises(SystemExit, match="2"):
        main(["stats"], project_root=root)


def test_preview_maps_configured_base_path() -> None:
    assert _strip_preview_base("/archive/static/base.css?v=1", "/archive") == "/static/base.css?v=1"
