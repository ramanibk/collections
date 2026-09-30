"""Jinja environment and deterministic file rendering."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import SiteConfig
from .urls import (
    about_url,
    entry_url,
    home_url,
    media_url,
    notes_url,
    photograph_index_url,
    photographs_url,
    static_url,
)


def route_output_path(output_dir: Path, route: str) -> Path:
    if not route.startswith("/") or "?" in route or "#" in route:
        raise ValueError(f"route must be a root-relative page path, got {route!r}")
    parts = [part for part in route.strip("/").split("/") if part]
    if any(part in (".", "..") for part in parts):
        raise ValueError(f"unsafe route {route!r}")
    return output_dir.joinpath(*parts, "index.html")


class Renderer:
    def __init__(self, templates_dir: Path, output_dir: Path, site: SiteConfig):
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        base = site.base_url
        self.env.globals.update(
            site=site,
            home_url=lambda: home_url(base),
            entry_url=lambda entry_id: entry_url(entry_id, base),
            photographs_url=lambda: photographs_url(base),
            photograph_index_url=lambda: photograph_index_url(base),
            notes_url=lambda: notes_url(base),
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
        if Path(filename).name != filename or filename.startswith("."):
            raise ValueError(f"unsafe output filename {filename!r}")
        destination = self.output_dir / filename
        html = self.env.get_template(template).render(**context)
        destination.write_text(html.rstrip() + "\n", encoding="utf-8")
        return destination
