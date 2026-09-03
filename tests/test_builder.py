import shutil
from pathlib import Path

import pytest

from journal.builder import BuildError, build_site


REPOSITORY = Path(__file__).resolve().parents[1]


def prepare_project(tmp_path: Path, output_dir: str = "public") -> Path:
    root = tmp_path / "field-notes"
    root.mkdir()
    shutil.copytree(REPOSITORY / "templates", root / "templates")
    shutil.copytree(REPOSITORY / "static", root / "static")
    (root / "content/clouds/note").mkdir(parents=True)
    (root / "content/clouds/note/entry.md").write_text(
        """---
id: obs-000001
title: Cumulus at Noon
date: 2026-09-01
type: observation
category: clouds
cloud_genus: cumulus
cover: 01.jpg
margin_note: check the western sky
---
A small cloud.
""",
        encoding="utf-8",
    )
    (root / "content/clouds/note/01.jpg").write_bytes(b"test image")
    (root / "config.yaml").write_text(
        f"""site:
  title: Field Notes
  subtitle: A test archive.
  base_url: /field-notes
  recent_entries: 5
build:
  output_dir: {output_dir}
clouds:
  show_unobserved_genera: false
""",
        encoding="utf-8",
    )
    return root


def test_build_generates_homepage_assets_and_id_based_media(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)

    result = build_site(root)

    homepage = (root / "public/index.html").read_text(encoding="utf-8")
    assert result.entry_count == 1
    assert result.page_count == 13
    assert result.media_count == 1
    assert result.statistics.cloud_observations == 1
    assert "/field-notes/static/css/base.css" in homepage
    assert "/field-notes/observe/clouds/" in homepage
    assert '<nav class="contents-list" aria-label="Contents">' in homepage
    assert "A test archive." in homepage
    assert "Personal archive" not in homepage
    assert "<h1>FIELD NOTES</h1>" not in homepage
    assert '<header class="site-header">' in homepage
    assert '<a class="site-name" href="/field-notes/">field notes</a>' in homepage
    assert '<nav class="breadcrumbs"' not in homepage
    assert "/field-notes/static/icons/" not in homepage
    cloud_page = (root / "public/observe/clouds/index.html").read_text(encoding="utf-8")
    assert '<div class="picture-grid">' in cloud_page
    assert "/field-notes/media/obs-000001/01.jpg" in cloud_page
    assert '<nav class="breadcrumbs" aria-label="Breadcrumb">' in cloud_page
    assert '<a href="/field-notes/">home</a>' in cloud_page
    assert '<a href="/field-notes/observe/">observe</a>' in cloud_page
    assert '<span aria-current="page">clouds</span>' in cloud_page
    assert (root / "public/media/obs-000001/01.jpg").read_bytes() == b"test image"
    assert (root / "public/.nojekyll").exists()
    assert (root / "public/about/index.html").exists()
    assert (root / "public/404.html").exists()
    assert (root / "public/observe/index.html").exists()
    cloud_index = (root / "public/observe/clouds/index.html").read_text(encoding="utf-8")
    assert "Cloud Atlas" in cloud_index
    assert "/field-notes/observe/clouds/cumulus/" in cloud_index
    genus_page = (root / "public/observe/clouds/cumulus/index.html").read_text(encoding="utf-8")
    assert "Cumulus" in genus_page
    assert "/field-notes/media/obs-000001/01.jpg" in genus_page
    assert "/field-notes/entry/obs-000001/" in genus_page
    entry_page = (root / "public/entry/obs-000001/index.html").read_text(encoding="utf-8")
    assert "A small cloud." in entry_page
    assert "clouds / obs-000001" not in entry_page
    assert "check the western sky" not in entry_page
    curiosities = (root / "public/observe/curiosities/index.html").read_text(encoding="utf-8")
    assert "Birds" in curiosities
    assert "No bird species have been identified yet." in curiosities
    assert not (root / "public/observe/birds/index.html").exists()
    cats_index = (root / "public/cats/index.html").read_text(encoding="utf-8")
    assert "Gwen" in cats_index
    assert "Billy" in cats_index
    assert "Jet" in cats_index
    assert (root / "public/cats/gwen/index.html").exists()
    assert (root / "public/cats/billy/index.html").exists()
    assert (root / "public/cats/jet/index.html").exists()
    assert (root / "public/crafts/index.html").exists()
    assert (root / "public/observe/curiosities/index.html").exists()
    posts = (root / "public/posts/index.html").read_text(encoding="utf-8")
    assert "All Posts" in posts
    assert 'data-sort="date"' in posts
    assert 'data-sort="title"' in posts
    assert "/field-notes/static/js/posts.js" in posts
    assert not (root / "public/journal/index.html").exists()
    assert not (root / "public/index/index.html").exists()


def test_entry_gallery_places_latest_numbered_photo_first(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    entry_dir = root / "content/clouds/note"
    for number in range(2, 7):
        (entry_dir / f"{number:02}.jpg").write_bytes(b"test image")

    build_site(root)

    page = (root / "public/entry/obs-000001/index.html").read_text(encoding="utf-8")
    positions = [page.index(f"/{number:02}.jpg") for number in range(6, 0, -1)]
    assert positions == sorted(positions)


def test_build_generates_bird_index_species_pages_and_unknown_section(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    identified = root / "content/birds/jay"
    identified.mkdir(parents=True)
    (identified / "entry.md").write_text(
        """---
id: obs-000002
title: Jay in the Oak
date: 2026-08-30
type: observation
category: birds
common_name: California Scrub-Jay
scientific_name: Aphelocoma californica
identification: confirmed
count: 2
location: Berkeley, California
cover: jay.jpg
---
Two birds in the branches.
""",
        encoding="utf-8",
    )
    (identified / "jay.jpg").write_bytes(b"bird image")
    unknown = root / "content/birds/unknown"
    unknown.mkdir(parents=True)
    (unknown / "entry.md").write_text(
        """---
id: obs-000003
title: Small Brown Bird
date: 2026-08-31
type: observation
category: birds
identification: unknown
---
Seen briefly.
""",
        encoding="utf-8",
    )

    result = build_site(root)

    assert result.page_count == 16
    index = (root / "public/observe/curiosities/index.html").read_text(encoding="utf-8")
    assert "California Scrub-Jay" in index
    assert "1 sighting" in index
    assert "Small Brown Bird" in index
    assert "/field-notes/observe/curiosities/birds/california-scrub-jay/" in index
    species = (
        root / "public/observe/curiosities/birds/california-scrub-jay/index.html"
    ).read_text(encoding="utf-8")
    assert "Aphelocoma californica" in species
    assert "August 30, 2026" in species
    assert "/field-notes/media/obs-000002/jay.jpg" in species
    assert "/field-notes/entry/obs-000002/" in species


def test_build_generates_fixed_cat_profiles_and_encounters(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    gwen = root / "content/cats/gwen-window"
    gwen.mkdir(parents=True)
    (gwen / "entry.md").write_text(
        """---
id: cat-000001
title: Gwen at the Window
date: 2026-08-30
type: cat
category: cats
cat_name: Gwen
relationship: mine
cover: gwen.jpg
---
Watching the garden.
""",
        encoding="utf-8",
    )
    (gwen / "gwen.jpg").write_bytes(b"cat image")
    encounter = root / "content/cats/garden-visitor"
    encounter.mkdir(parents=True)
    (encounter / "entry.md").write_text(
        """---
id: cat-000002
title: Garden Visitor
date: 2026-08-31
type: cat
category: cats
relationship: encounter
location: Berkeley, California
---
A brief visitor.
""",
        encoding="utf-8",
    )

    result = build_site(root)

    assert result.page_count == 15
    index = (root / "public/cats/index.html").read_text(encoding="utf-8")
    assert "/field-notes/cats/gwen/" in index
    assert "1 entry · 1 photo" in index
    assert "Garden Visitor" in index
    profile = (root / "public/cats/gwen/index.html").read_text(encoding="utf-8")
    assert "Gwen at the Window" in profile
    assert "August 30, 2026" in profile
    assert "/field-notes/media/cat-000001/gwen.jpg" in profile
    assert "/field-notes/entry/cat-000001/" in profile
    assert "No entries for Billy yet." in (
        root / "public/cats/billy/index.html"
    ).read_text(encoding="utf-8")


def test_build_generates_crafts_curiosities_and_sortable_posts(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    project = root / "content/making/wildflower-hoop"
    project.mkdir(parents=True)
    (project / "entry.md").write_text(
        """---
id: proj-000001
title: Wildflower Hoop
date: 2026-08-19
type: project
category: making
craft: Embroidery
status: completed
started: 2026-08-01
completed: 2026-08-19
materials: [linen, cotton floss]
cover: finished.jpg
---
The finished hoop.
""",
        encoding="utf-8",
    )
    (project / "finished.jpg").write_bytes(b"project image")
    curiosity = root / "content/curiosities/spiral-shell"
    curiosity.mkdir(parents=True)
    (curiosity / "entry.md").write_text(
        """---
id: cur-000001
title: Spiral Shell
date: 2025-07-04
type: curiosity
category: curiosities
texture: ridged
favorite: true
---
Found near the path.
""",
        encoding="utf-8",
    )

    result = build_site(root)

    assert result.page_count == 16
    crafts = (root / "public/crafts/index.html").read_text(encoding="utf-8")
    assert "Embroidery" in crafts
    assert "Wildflower Hoop" in crafts
    assert "/field-notes/crafts/embroidery/" in crafts
    craft = (root / "public/crafts/embroidery/index.html").read_text(encoding="utf-8")
    assert "/field-notes/entry/proj-000001/" in craft
    project_page = (root / "public/entry/proj-000001/index.html").read_text(encoding="utf-8")
    assert "cotton floss" in project_page
    assert "August 19, 2026" in project_page
    curiosities = (root / "public/observe/curiosities/index.html").read_text(encoding="utf-8")
    assert "Spiral Shell" in curiosities
    assert "/field-notes/entry/cur-000001/" in curiosities
    posts = (root / "public/posts/index.html").read_text(encoding="utf-8")
    assert "Wildflower Hoop" in posts
    assert "Spiral Shell" in posts
    assert posts.index("Wildflower Hoop") < posts.index("Spiral Shell")
    assert 'data-title="wildflower hoop"' in posts
    assert 'data-title="spiral shell"' in posts
    assert not (root / "public/journal/index.html").exists()
    assert not (root / "public/index/index.html").exists()


def test_build_replaces_only_configured_generated_output(tmp_path: Path) -> None:
    root = prepare_project(tmp_path)
    stale = root / "public/stale.txt"
    stale.parent.mkdir()
    stale.write_text("old", encoding="utf-8")

    build_site(root)

    assert not stale.exists()
    assert (root / "content/clouds/note/entry.md").exists()
    assert (root / "templates/home.html").exists()
    assert (root / "static/css/base.css").exists()


def test_build_refuses_protected_output_directory(tmp_path: Path) -> None:
    root = prepare_project(tmp_path, output_dir="content")

    with pytest.raises(BuildError, match="unsafe build.output_dir"):
        build_site(root)

    assert (root / "content/clouds/note/entry.md").exists()
