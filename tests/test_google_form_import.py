import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "integrations/google-form/import_responses.py"
SPEC = importlib.util.spec_from_file_location("google_form_import", MODULE_PATH)
assert SPEC and SPEC.loader
IMPORTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = IMPORTER
SPEC.loader.exec_module(IMPORTER)


def test_parses_current_form_and_optional_metadata() -> None:
    rows = [
        [
            IMPORTER.Cell("Timestamp"),
            IMPORTER.Cell("Image"),
            IMPORTER.Cell("Identification"),
            IMPORTER.Cell("Orientation"),
            IMPORTER.Cell("Notes"),
            IMPORTER.Cell("Date"),
            IMPORTER.Cell("Location"),
            IMPORTER.Cell("Tags"),
        ],
        [
            IMPORTER.Cell("9/30/2026 16:48:00"),
            IMPORTER.Cell(
                "IMG_1234.HEIC",
                links=("https://drive.google.com/open?id=1AbCdEfGhIjKlMnOpQrStUv",),
            ),
            IMPORTER.Cell("Window light"),
            IMPORTER.Cell("Portrait"),
            IMPORTER.Cell("Late afternoon."),
            IMPORTER.Cell("9/29/2026"),
            IMPORTER.Cell("Berkeley, California"),
            IMPORTER.Cell("light, home, Light"),
        ],
    ]

    submissions = IMPORTER.parse_submissions(rows)

    assert len(submissions) == 1
    submission = submissions[0]
    assert submission.title == "Window light"
    assert submission.entry_date == date(2026, 9, 29)
    assert submission.orientation == "portrait"
    assert submission.description == "Late afternoon."
    assert submission.location == "Berkeley, California"
    assert submission.tags == ("light", "home")
    assert submission.file_ids == ("1AbCdEfGhIjKlMnOpQrStUv",)


def test_uses_timestamp_when_optional_date_is_absent() -> None:
    rows = [
        [
            IMPORTER.Cell("Timestamp"),
            IMPORTER.Cell("Image"),
            IMPORTER.Cell("Title"),
            IMPORTER.Cell("Orientation"),
        ],
        [
            IMPORTER.Cell("2026-09-30 16:48:00"),
            IMPORTER.Cell("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUv/view"),
            IMPORTER.Cell("Cloud study"),
            IMPORTER.Cell("Landscape"),
        ],
    ]

    submission = IMPORTER.parse_submissions(rows)[0]

    assert submission.entry_date == date(2026, 9, 30)
    assert submission.orientation == "landscape"


def test_rejects_rows_without_drive_file_id() -> None:
    rows = [
        [
            IMPORTER.Cell("Image"),
            IMPORTER.Cell("Identification"),
            IMPORTER.Cell("Orientation"),
        ],
        [
            IMPORTER.Cell("image.jpg"),
            IMPORTER.Cell("Unlinked image"),
            IMPORTER.Cell("Portrait"),
        ],
    ]

    with pytest.raises(IMPORTER.ImportError, match="Drive file ID"):
        IMPORTER.parse_submissions(rows)


def test_import_key_is_stable_when_metadata_is_edited() -> None:
    headers = [
        IMPORTER.Cell("Timestamp"),
        IMPORTER.Cell("Image"),
        IMPORTER.Cell("Identification"),
        IMPORTER.Cell("Orientation"),
    ]
    image = IMPORTER.Cell("https://drive.google.com/open?id=1AbCdEfGhIjKlMnOpQrStUv")
    original = [
        IMPORTER.Cell("9/30/2026 16:48:00"),
        image,
        IMPORTER.Cell("First title"),
        IMPORTER.Cell("Portrait"),
    ]
    edited = [
        IMPORTER.Cell("9/30/2026 16:48:00"),
        image,
        IMPORTER.Cell("Edited title"),
        IMPORTER.Cell("Landscape"),
    ]

    original_key = IMPORTER.parse_submissions([headers, original])[0].key
    edited_key = IMPORTER.parse_submissions([headers, edited])[0].key

    assert original_key == edited_key
