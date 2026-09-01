"""Configuration loading for the journal project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


class ConfigError(ValueError):
    """Raised when ``config.yaml`` cannot be interpreted."""


@dataclass(frozen=True)
class SiteConfig:
    title: str = "Ramani"
    subtitle: str = "Field notes, photographs, and things made."
    base_url: str = ""
    recent_entries: int = 5


@dataclass(frozen=True)
class BuildConfig:
    output_dir: Path = Path("public")


@dataclass(frozen=True)
class CloudConfig:
    show_unobserved_genera: bool = False


@dataclass(frozen=True)
class JournalConfig:
    site: SiteConfig = field(default_factory=SiteConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    clouds: CloudConfig = field(default_factory=CloudConfig)


def _mapping(value: Any, section: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConfigError(f"config section {section!r} must be a mapping")
    return value


def _base_url(value: Any) -> str:
    base_url = str(value or "").strip()
    if base_url in ("", "/"):
        return ""
    return "/" + base_url.strip("/")


def load_config(path: Path) -> JournalConfig:
    """Load a project config, resolving build paths from the config location."""

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ConfigError(f"could not read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"malformed YAML in {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ConfigError("config root must be a mapping")

    site = _mapping(raw.get("site"), "site")
    build = _mapping(raw.get("build"), "build")
    clouds = _mapping(raw.get("clouds"), "clouds")
    recent_entries = site.get("recent_entries", 5)
    if not isinstance(recent_entries, int) or isinstance(recent_entries, bool) or recent_entries < 0:
        raise ConfigError("site.recent_entries must be a non-negative integer")

    output_value = build.get("output_dir", "public")
    if not isinstance(output_value, str) or not output_value.strip():
        raise ConfigError("build.output_dir must be a non-empty path")
    output_dir = Path(output_value)
    if not output_dir.is_absolute():
        output_dir = path.parent / output_dir

    return JournalConfig(
        site=SiteConfig(
            title=str(site.get("title", "Ramani")),
            subtitle=str(site.get("subtitle", "Field notes, photographs, and things made.")),
            base_url=_base_url(site.get("base_url", "")),
            recent_entries=recent_entries,
        ),
        build=BuildConfig(output_dir=output_dir),
        clouds=CloudConfig(show_unobserved_genera=bool(clouds.get("show_unobserved_genera", False))),
    )
