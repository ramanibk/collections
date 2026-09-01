from pathlib import Path

import pytest

from journal.config import ConfigError, load_config


def test_load_config_normalizes_base_url_and_output_path(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "site:\n  title: Field Notes\n  base_url: /archive/\n  recent_entries: 3\n"
        "build:\n  output_dir: site\n",
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.site.title == "Field Notes"
    assert config.site.base_url == "/archive"
    assert config.site.recent_entries == 3
    assert config.build.output_dir == tmp_path / "site"


def test_load_config_rejects_invalid_recent_count(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("site:\n  recent_entries: many\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="non-negative integer"):
        load_config(path)
