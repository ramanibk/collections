"""Validated, filesystem-safe static site build orchestration."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .birds import build_bird_notebook
from .cats import build_cat_collection
from .clouds import build_cloud_atlas
from .config import JournalConfig, load_config
from .curiosities import build_curiosity_collection
from .loader import load_content
from .making import build_making_collection
from .renderer import Renderer
from .stats import SiteStatistics, calculate_statistics
from .validation import ValidationIssue, format_report
from .urls import (
    about_url,
    bird_species_url,
    cat_url,
    category_url,
    cloud_genus_url,
    craft_url,
    entry_url,
    observe_url,
    posts_url,
)


class BuildError(RuntimeError):
    """A concise expected build failure."""


@dataclass(frozen=True)
class BuildResult:
    output_dir: Path
    entry_count: int
    page_count: int
    media_count: int
    statistics: SiteStatistics
    warnings: Tuple[ValidationIssue, ...] = ()


def _safe_output_dir(project_root: Path, configured_output: Path) -> Path:
    root = project_root.resolve()
    output = configured_output.resolve()
    try:
        relative = output.relative_to(root)
    except ValueError as exc:
        raise BuildError("build.output_dir must be inside the project directory") from exc
    protected = {"content", "templates", "static", "journal", "tests", ".git"}
    if not relative.parts or relative.parts[0] in protected:
        raise BuildError(f"refusing unsafe build.output_dir: {configured_output}")
    if configured_output.is_symlink():
        raise BuildError(f"refusing symlink build.output_dir: {configured_output}")
    if configured_output.exists() and not configured_output.is_dir():
        raise BuildError(f"build.output_dir is not a directory: {configured_output}")
    return output


def _copy_static(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(source).parts):
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _copy_media(entries, destination: Path) -> int:
    count = 0
    for entry in entries:
        for filename in entry.images:
            target = destination / entry.id / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry.folder / filename, target)
            count += 1
    return count


def build_site(project_root: Path, config_path: Optional[Path] = None) -> BuildResult:
    """Build the currently implemented pages into the configured output tree."""

    root = project_root.resolve()
    selected_config = config_path or (root / "config.yaml")
    config: JournalConfig = load_config(selected_config)
    output = _safe_output_dir(root, config.build.output_dir)
    loaded = load_content(root / "content")
    if not loaded.is_valid:
        raise BuildError(format_report(loaded.report))

    statistics = calculate_statistics(loaded.entries)
    photo_entries = tuple(entry for entry in loaded.entries if entry.cover)
    base_url = config.site.base_url
    observe_href = observe_url(base_url)

    def category_photos(*categories: str):
        return tuple(entry for entry in photo_entries if entry.category in categories)[:6]

    def category_breadcrumbs(category: str, current_label: str):
        if category in ("clouds", "birds", "curiosities"):
            return (
                ("observe", observe_href),
                (current_label, None),
            )
        return ((current_label, None),)

    def entry_breadcrumbs(entry):
        label = {
            "birds": "curiosities",
            "making": "crafts",
        }.get(entry.category, entry.category)
        trail = []
        if entry.category in ("clouds", "birds", "curiosities"):
            trail.append(("observe", observe_href))
        trail.append((label, category_url(entry.category, base_url)))
        craft = entry.get("craft") if entry.category == "making" else None
        if craft:
            trail.append((str(craft), craft_url(str(craft), base_url)))
        trail.append((entry.title, None))
        return tuple(trail)

    cloud_atlas = build_cloud_atlas(
        loaded.entries,
        show_unobserved_genera=config.clouds.show_unobserved_genera,
    )
    bird_notebook = build_bird_notebook(loaded.entries)
    cat_collection = build_cat_collection(loaded.entries)
    making_collection = build_making_collection(loaded.entries)
    curiosity_collection = build_curiosity_collection(loaded.entries)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        renderer = Renderer(root / "templates", staging, config.site)
        renderer.render(
            "home.html",
            "/",
            page_title=config.site.title,
            page_description=config.site.subtitle,
            statistics=statistics,
            recent_entries=loaded.entries[: config.site.recent_entries],
            current_section="home",
        )
        renderer.render(
            "observe.html",
            observe_url(),
            page_title=f"Observe — {config.site.title}",
            page_description="Clouds and a cabinet of natural curiosities.",
            statistics=statistics,
            photo_entries=photo_entries[:6],
            breadcrumbs=(("observe", None),),
            current_section="observe",
        )
        renderer.render(
            "cloud_index.html",
            category_url("clouds"),
            page_title=f"Cloud Atlas — {config.site.title}",
            page_description="A catalogue of observed and identified clouds.",
            atlas=cloud_atlas,
            photo_entries=category_photos("clouds"),
            breadcrumbs=category_breadcrumbs("clouds", "clouds"),
            current_section="observe",
        )
        for genus in cloud_atlas.genus_pages:
            renderer.render(
                "cloud_genus.html",
                cloud_genus_url(genus.name),
                page_title=f"{genus.name.title()} — Cloud Atlas — {config.site.title}",
                page_description=f"{genus.sighting_count} {genus.name.title()} cloud sightings.",
                genus=genus,
                breadcrumbs=(
                    ("observe", observe_href),
                    ("clouds", category_url("clouds", base_url)),
                    (genus.name, None),
                ),
                current_section="observe",
            )
        for species in bird_notebook.species_pages:
            renderer.render(
                "bird_species.html",
                bird_species_url(species.common_name),
                page_title=f"{species.common_name} — Curiosities — {config.site.title}",
                page_description=(
                    f"{species.sighting_count} {species.common_name} "
                    f"sighting{'s' if species.sighting_count != 1 else ''}."
                ),
                species=species,
                breadcrumbs=(
                    ("observe", observe_href),
                    ("curiosities", category_url("curiosities", base_url)),
                    (species.common_name, None),
                ),
                current_section="observe",
            )
        renderer.render(
            "cats.html",
            category_url("cats"),
            page_title=f"Cats — {config.site.title}",
            page_description="Gwen, Billy, Jet, and cat encounters.",
            collection=cat_collection,
            photo_entries=category_photos("cats"),
            breadcrumbs=category_breadcrumbs("cats", "cats"),
            current_section="cats",
        )
        for cat in cat_collection.profiles:
            renderer.render(
                "cat_detail.html",
                cat_url(cat.name),
                page_title=f"{cat.name} — Cats — {config.site.title}",
                page_description=(
                    f"{cat.entry_count} entries and {cat.photograph_count} "
                    f"photographs of {cat.name}."
                ),
                cat=cat,
                breadcrumbs=(
                    ("cats", category_url("cats", base_url)),
                    (cat.name, None),
                ),
                current_section="cats",
            )
        renderer.render(
            "making.html",
            category_url("making"),
            page_title=f"Crafts — {config.site.title}",
            page_description="Projects, materials, and things made by hand.",
            collection=making_collection,
            photo_entries=category_photos("making"),
            breadcrumbs=category_breadcrumbs("making", "crafts"),
            current_section="crafts",
        )
        for craft in making_collection.craft_pages:
            renderer.render(
                "craft.html",
                craft_url(craft.name),
                page_title=f"{craft.name} — Crafts — {config.site.title}",
                page_description=f"{craft.project_count} {craft.name} projects.",
                craft=craft,
                breadcrumbs=(
                    ("crafts", category_url("making", base_url)),
                    (craft.name, None),
                ),
                current_section="crafts",
            )
        renderer.render(
            "curiosities.html",
            category_url("curiosities"),
            page_title=f"Curiosities — {config.site.title}",
            page_description="Finds and observations that resist easy classification.",
            collection=curiosity_collection,
            notebook=bird_notebook,
            combined_entry_count=curiosity_collection.entry_count + bird_notebook.statistics.total_observations,
            combined_photograph_count=sum(
                len(entry.images)
                for entry in loaded.entries
                if entry.category in ("curiosities", "birds")
            ),
            photo_entries=category_photos("curiosities", "birds"),
            breadcrumbs=category_breadcrumbs("curiosities", "curiosities"),
            current_section="observe",
        )
        renderer.render(
            "posts.html",
            posts_url(),
            page_title=f"All Posts — {config.site.title}",
            page_description="Every archive post, sortable by date or title.",
            posts=loaded.entries,
            breadcrumbs=(("all posts", None),),
            current_section="posts",
        )
        renderer.render(
            "about.html",
            about_url(),
            page_title=f"About — {config.site.title}",
            page_description="About this local-first personal archive.",
            breadcrumbs=(("about", None),),
            current_section="about",
        )
        for entry in loaded.entries:
            renderer.render(
                "project.html" if entry.category == "making" else "entry.html",
                entry_url(entry.id),
                page_title=f"{entry.title} — {config.site.title}",
                page_description=entry.body_markdown.split("\n", 1)[0] or config.site.subtitle,
                entry=entry,
                breadcrumbs=entry_breadcrumbs(entry),
                current_section="crafts" if entry.category == "making" else entry.category,
            )
        renderer.render_file(
            "404.html",
            "404.html",
            page_title=f"Page not found — {config.site.title}",
            page_description="The requested archive page could not be found.",
            breadcrumbs=(("page not found", None),),
            current_section=None,
        )
        _copy_static(root / "static", staging / "static")
        media_count = _copy_media(loaded.entries, staging / "media")
        (staging / ".nojekyll").touch()
        page_count = sum(1 for _ in staging.rglob("index.html"))

        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(staging), str(output))
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return BuildResult(
        output_dir=output,
        entry_count=len(loaded.entries),
        page_count=page_count,
        media_count=media_count,
        statistics=statistics,
        warnings=loaded.report.warnings,
    )
