"""Central, deployment-aware URL generation."""

from __future__ import annotations

from urllib.parse import quote

from .utils import slugify


CATEGORY_PATHS = {
    "clouds": "/observe/clouds/",
    "birds": "/observe/curiosities/",
    "cats": "/cats/",
    "making": "/crafts/",
    "curiosities": "/observe/curiosities/",
}


def normalize_base_url(base_url: str = "") -> str:
    value = str(base_url or "").strip()
    if value in ("", "/"):
        return ""
    return "/" + value.strip("/")


def with_base_url(path: str, base_url: str = "") -> str:
    """Prefix a root-relative site path with a normalized deployment base."""

    base = normalize_base_url(base_url)
    clean_path = "/" + str(path or "").lstrip("/")
    if clean_path == "/":
        return f"{base}/" if base else "/"
    return f"{base}{clean_path}"


def home_url(base_url: str = "") -> str:
    return with_base_url("/", base_url)


def observe_url(base_url: str = "") -> str:
    return with_base_url("/observe/", base_url)


def category_url(category: str, base_url: str = "") -> str:
    try:
        path = CATEGORY_PATHS[category]
    except KeyError as exc:
        raise ValueError(f"unsupported category {category!r}") from exc
    return with_base_url(path, base_url)


def entry_url(entry_id: str, base_url: str = "") -> str:
    return with_base_url(f"/entry/{quote(str(entry_id), safe='-._~')}/", base_url)


def cloud_genus_url(genus: str, base_url: str = "") -> str:
    return with_base_url(f"/observe/clouds/{slugify(genus)}/", base_url)


def bird_species_url(species: str, base_url: str = "") -> str:
    return with_base_url(f"/observe/curiosities/birds/{slugify(species)}/", base_url)


def cat_url(cat_name: str, base_url: str = "") -> str:
    return with_base_url(f"/cats/{slugify(cat_name)}/", base_url)


def craft_url(craft: str, base_url: str = "") -> str:
    return with_base_url(f"/crafts/{slugify(craft)}/", base_url)


def posts_url(base_url: str = "") -> str:
    return with_base_url("/posts/", base_url)


def about_url(base_url: str = "") -> str:
    return with_base_url("/about/", base_url)


def static_url(path: str, base_url: str = "") -> str:
    return with_base_url(f"/static/{str(path).lstrip('/')}", base_url)


def media_url(entry_id: str, filename: str, base_url: str = "") -> str:
    safe_id = quote(str(entry_id), safe="-._~")
    safe_filename = quote(str(filename), safe="-._~")
    return with_base_url(f"/media/{safe_id}/{safe_filename}", base_url)
