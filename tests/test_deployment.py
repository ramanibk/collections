from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]


def test_pages_workflow_tests_validates_builds_and_deploys_public() -> None:
    workflow = (REPOSITORY / ".github/workflows/pages.yml").read_text(encoding="utf-8")

    assert "python -m pytest" in workflow
    assert "python journal.py validate" in workflow
    assert "python journal.py build" in workflow
    assert "actions/configure-pages@v6" in workflow
    assert "actions/upload-pages-artifact@v5" in workflow
    assert "path: public" in workflow
    assert "include-hidden-files: true" in workflow
    assert "actions/deploy-pages@v5" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow


def test_all_planned_stylesheets_exist_and_are_linked() -> None:
    base = (REPOSITORY / "templates/base.html").read_text(encoding="utf-8")
    names = (
        "variables.css",
        "base.css",
        "layout.css",
        "typography.css",
        "gallery.css",
        "responsive.css",
    )
    for name in names:
        assert (REPOSITORY / "static/css" / name).is_file()
        assert f"css/{name}" in base
