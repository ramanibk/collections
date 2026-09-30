from __future__ import annotations

import shutil
from html.parser import HTMLParser
from pathlib import Path

from journal.builder import build_site

REPOSITORY = Path(__file__).resolve().parents[1]


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = "href" if tag == "a" else "src" if tag in {"img", "script"} else None
        if attribute:
            values = dict(attrs)
            if values.get(attribute):
                self.targets.append(values[attribute] or "")


def prepare_project(tmp_path: Path) -> Path:
    root = tmp_path / "archive"
    root.mkdir()
    shutil.copytree(REPOSITORY / "templates", root / "templates")
    shutil.copytree(REPOSITORY / "static", root / "static")
    (root / "content").mkdir()
    (root / "content/about.md").write_text(
        """---
title: Example Person
portrait_url: /portrait.jpg
links:
  - label: GitHub
    url: https://github.com/example
---
I build dependable research infrastructure.
""",
        encoding="utf-8",
    )
    photo = root / "content" / "photographs" / "window"
    photo.mkdir(parents=True)
    (photo / "entry.md").write_text(
        """---
id: photo-000001
title: Window light
date: 2026-09-01
type: photo
orientation: portrait
cover: image.jpg
tags: [light, home]
---
Late light.
""",
        encoding="utf-8",
    )
    (photo / "image.jpg").write_bytes(b"image")
    note = root / "content" / "notes" / "systems"
    note.mkdir(parents=True)
    (note / "entry.md").write_text(
        """---
id: note-000001
title: Durable systems
date: 2026-08-01
type: essay
tags: [systems]
---
Write things down.
""",
        encoding="utf-8",
    )
    (root / "config.yaml").write_text(
        """site:
  title: Test Archive
  base_url: /archive
build:
  output_dir: public
""",
        encoding="utf-8",
    )
    return root


def test_build_only_generates_current_site_sections(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    result = build_site(root)

    assert result.entry_count == 2
    assert result.page_count == 7
    assert result.media_count == 1
    assert (root / "public/about/index.html").exists()
    assert (root / "public/photographs/index.html").exists()
    assert (root / "public/photographs/filter/index.html").exists()
    assert (root / "public/notes/index.html").exists()
    assert not (root / "public/observe").exists()
    assert not (root / "public/cats").exists()
    assert not (root / "public/crafts").exists()
    assert not (root / "public/posts").exists()

    about = (root / "public/about/index.html").read_text(encoding="utf-8")
    assert "dependable research infrastructure" in about
    assert "https://github.com/example" in about

    homepage = (root / "public/index.html").read_text(encoding="utf-8")
    assert ">About<" in homepage
    assert "About / Profile" not in homepage
    assert "Photograph Archive" in homepage
    assert "Notes" in homepage
    assert "Archive Filter" not in homepage

    photographs = (root / "public/photographs/index.html").read_text(encoding="utf-8")
    assert "/archive/media/photo-000001/image.jpg" in photographs
    notes = (root / "public/notes/index.html").read_text(encoding="utf-8")
    assert "Durable systems" in notes
    assert "Window light" not in notes
    filter_page = (root / "public/photographs/filter/index.html").read_text(encoding="utf-8")
    assert 'value="photograph"' in filter_page
    assert 'value="essay"' in filter_page
    assert 'value="systems"' in filter_page


def test_every_generated_internal_link_resolves(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    build_site(root)
    public = root / "public"

    for page in public.rglob("*.html"):
        collector = LinkCollector()
        collector.feed(page.read_text(encoding="utf-8"))
        for target in collector.targets:
            if not target.startswith("/archive/"):
                continue
            relative = target.removeprefix("/archive/").split("?", 1)[0]
            destination = public / relative
            if target.endswith("/"):
                destination /= "index.html"
            assert destination.exists(), f"{page}: broken internal target {target}"
