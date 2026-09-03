"""Jinja environment and deterministic file rendering."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import SiteConfig
from .urls import (
    about_url,
    bird_species_url,
    cat_url,
    category_url,
    cloud_genus_url,
    craft_url,
    entry_url,
    home_url,
    media_url,
    observe_url,
    posts_url,
    static_url,
)
from .utils import slugify


def route_output_path(output_dir: Path, route: str) -> Path:
    """Map an internal page route to its generated ``index.html`` path."""

    if not route.startswith("/") or "?" in route or "#" in route:
        raise ValueError(f"route must be a root-relative page path, got {route!r}")
    parts = [part for part in route.strip("/").split("/") if part]
    if any(part in (".", "..") for part in parts):
        raise ValueError(f"unsafe route {route!r}")
    return output_dir.joinpath(*parts, "index.html")


def human_date(value: date) -> str:
    return f"{value.strftime('%B')} {value.day}, {value.year}"


class Renderer:
    def __init__(self, templates_dir: Path, output_dir: Path, site: SiteConfig):
        self.output_dir = output_dir
        self.site = site
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters.update(human_date=human_date, slugify=slugify)
        base = site.base_url
        self.env.globals.update(
            site=site,
            home_url=lambda: home_url(base),
            observe_url=lambda: observe_url(base),
            category_url=lambda category: category_url(category, base),
            entry_url=lambda entry_id: entry_url(entry_id, base),
            cloud_genus_url=lambda genus: cloud_genus_url(genus, base),
            bird_species_url=lambda species: bird_species_url(species, base),
            cat_url=lambda name: cat_url(name, base),
            craft_url=lambda craft: craft_url(craft, base),
            posts_url=lambda: posts_url(base),
            about_url=lambda: about_url(base),
            static_url=lambda path: static_url(path, base),
            media_url=lambda entry_id, filename: media_url(entry_id, filename, base),
        )

    def render(self, template: str, route: str, **context: Any) -> Path:
        destination = route_output_path(self.output_dir, route)
        destination.parent.mkdir(parents=True, exist_ok=True)
        html = self.env.get_template(template).render(**context)
        destination.write_text(html.rstrip() + "\n", encoding="utf-8")
        return destination

    def render_file(self, template: str, filename: str, **context: Any) -> Path:
        """Render a special top-level file such as GitHub Pages' ``404.html``."""

        if Path(filename).name != filename or filename.startswith("."):
            raise ValueError(f"unsafe output filename {filename!r}")
        destination = self.output_dir / filename
        html = self.env.get_template(template).render(**context)
        destination.write_text(html.rstrip() + "\n", encoding="utf-8")
        return destination
