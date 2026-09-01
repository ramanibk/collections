from pathlib import Path

import pytest

from journal.renderer import route_output_path
from journal.urls import (
    bird_species_url,
    category_url,
    cloud_genus_url,
    craft_url,
    entry_url,
    home_url,
    index_url,
    journal_url,
    media_url,
    normalize_base_url,
    year_url,
)


def test_base_url_normalization() -> None:
    assert normalize_base_url("") == ""
    assert normalize_base_url("/") == ""
    assert normalize_base_url(" /field-notes/ ") == "/field-notes"


def test_urls_work_at_root_and_github_pages_base() -> None:
    assert home_url() == "/"
    assert home_url("/field-notes") == "/field-notes/"
    assert entry_url("obs-000001") == "/entry/obs-000001/"
    assert entry_url("obs-000001", "/field-notes") == "/field-notes/entry/obs-000001/"
    assert category_url("clouds", "/field-notes") == "/field-notes/observe/clouds/"
    assert cloud_genus_url("Altocumulus", "/field-notes") == "/field-notes/observe/clouds/altocumulus/"
    assert bird_species_url("California Scrub-Jay") == "/observe/birds/california-scrub-jay/"
    assert craft_url("Hand Embroidery", "/field-notes") == "/field-notes/make/hand-embroidery/"
    assert journal_url("/field-notes") == "/field-notes/journal/"
    assert index_url() == "/index/"
    assert year_url(2026) == "/journal/2026/"


def test_media_url_escapes_filename_and_uses_permanent_id() -> None:
    assert media_url("obs-000001", "cloud view.jpg", "/archive") == "/archive/media/obs-000001/cloud%20view.jpg"


def test_unsupported_category_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported category"):
        category_url("rocks")


def test_route_output_path_maps_clean_routes_only(tmp_path: Path) -> None:
    assert route_output_path(tmp_path, "/") == tmp_path / "index.html"
    assert route_output_path(tmp_path, "/entry/obs-1/") == tmp_path / "entry/obs-1/index.html"
    with pytest.raises(ValueError, match="unsafe route"):
        route_output_path(tmp_path, "/../escape/")
