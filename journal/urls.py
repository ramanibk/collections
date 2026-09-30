"""Deployment-aware URLs for the small public site."""

from urllib.parse import quote


def normalize_base_url(base_url: str = "") -> str:
    value = str(base_url or "").strip()
    return "" if value in ("", "/") else "/" + value.strip("/")


def with_base_url(path: str, base_url: str = "") -> str:
    base = normalize_base_url(base_url)
    clean_path = "/" + str(path or "").lstrip("/")
    return f"{base}/" if clean_path == "/" and base else f"{base}{clean_path}"


def home_url(base_url: str = "") -> str:
    return with_base_url("/", base_url)


def entry_url(entry_id: str, base_url: str = "") -> str:
    return with_base_url(f"/entry/{quote(str(entry_id), safe='-._~')}/", base_url)


def photographs_url(base_url: str = "") -> str:
    return with_base_url("/photographs/", base_url)


def photograph_index_url(base_url: str = "") -> str:
    return with_base_url("/photographs/filter/", base_url)


def notes_url(base_url: str = "") -> str:
    return with_base_url("/notes/", base_url)


def about_url(base_url: str = "") -> str:
    return home_url(base_url)


def static_url(path: str, base_url: str = "") -> str:
    return with_base_url(f"/static/{str(path).lstrip('/')}", base_url)


def media_url(entry_id: str, filename: str, base_url: str = "") -> str:
    safe_id = quote(str(entry_id), safe="-._~")
    safe_filename = quote(str(filename), safe="-._~")
    return with_base_url(f"/media/{safe_id}/{safe_filename}", base_url)
