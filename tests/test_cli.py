import io
import shutil
from pathlib import Path

from journal.cli import _strip_preview_base, main


REPOSITORY = Path(__file__).resolve().parents[1]


def minimal_project(tmp_path: Path) -> Path:
    root = tmp_path / "field-notes"
    root.mkdir()
    shutil.copytree(REPOSITORY / "templates", root / "templates")
    shutil.copytree(REPOSITORY / "static", root / "static")
    for category in ("clouds", "birds", "cats", "making", "curiosities"):
        (root / "content" / category).mkdir(parents=True)
    (root / "config.yaml").write_text(
        """site:
  title: Test Notes
  base_url: ""
build:
  output_dir: public
""",
        encoding="utf-8",
    )
    return root


def test_cli_add_curiosity_isolated_from_terminal_input(tmp_path: Path) -> None:
    root = minimal_project(tmp_path)
    answers = iter(
        [
            "",  # image
            "",  # additional images
            "Spiral Shell",
            "2026-09-01",
            "Berkeley, California",
            "shell, found",
            "Found beside the path.",
        ]
    )
    output = io.StringIO()

    status = main(
        ["add", "curiosity"],
        project_root=root,
        input_func=lambda _prompt: next(answers),
        output=output,
    )

    assert status == 0
    assert "Created cur-000001" in output.getvalue()
    source = next((root / "content/curiosities").rglob("entry.md"))
    assert "Found beside the path." in source.read_text(encoding="utf-8")


def test_cli_validate_stats_and_build(tmp_path: Path) -> None:
    root = minimal_project(tmp_path)
    output = io.StringIO()

    assert main(["validate"], project_root=root, output=output) == 0
    assert "Validation: 0 error(s), 0 warning(s)" in output.getvalue()

    output = io.StringIO()
    assert main(["stats"], project_root=root, output=output) == 0
    assert "Total entries: 0" in output.getvalue()

    output = io.StringIO()
    assert main(["build"], project_root=root, output=output) == 0
    assert "Build complete:" in output.getvalue()
    assert (root / "public/index.html").exists()


def test_cli_validation_errors_return_nonzero(tmp_path: Path) -> None:
    root = minimal_project(tmp_path)
    bad = root / "content/clouds/bad"
    bad.mkdir()
    (bad / "entry.md").write_text("not frontmatter", encoding="utf-8")
    error = io.StringIO()

    status = main(["validate"], project_root=root, output=io.StringIO(), error=error)

    assert status == 1
    assert "ERROR parse_error" in error.getvalue()


def test_preview_maps_configured_base_path_to_generated_root() -> None:
    assert _strip_preview_base("/field-notes/", "/field-notes") == "/"
    assert _strip_preview_base("/field-notes/static/base.css?v=1", "/field-notes") == "/static/base.css?v=1"
    assert _strip_preview_base("/unrelated/", "/field-notes") == "/unrelated/"
