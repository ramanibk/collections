"""Import new Google Form response rows into the Collections content tree."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import google.auth.transport.requests
import requests
from dateutil import parser as date_parser
from google.oauth2 import service_account
from PIL import Image
from pillow_heif import register_heif_opener

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from journal.creation import CreationError, create_photo_entry  # noqa: E402

SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
)
STATE_PATH = PROJECT_ROOT / "content/.google-form-imports.json"
SUPPORTED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
HEIF_MIME_TYPES = {"image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence"}


class ImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class Cell:
    value: str
    links: tuple[str, ...] = ()


@dataclass(frozen=True)
class Submission:
    key: str
    row_number: int
    title: str
    entry_date: date
    orientation: str
    description: str
    location: str
    tags: tuple[str, ...]
    file_ids: tuple[str, ...]


class GoogleClient:
    def __init__(self, credentials_json: str) -> None:
        try:
            info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        except (ValueError, KeyError, TypeError) as exc:
            raise ImportError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not a valid service account key"
            ) from exc
        self.session = google.auth.transport.requests.AuthorizedSession(credentials)

    def spreadsheet_rows(self, spreadsheet_id: str) -> list[list[Cell]]:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        response = self.session.get(url, params={"includeGridData": "true"}, timeout=60)
        _raise_google_error(response, "read response spreadsheet")
        payload = response.json()
        sheets = payload.get("sheets") or []
        if not sheets:
            raise ImportError("the response spreadsheet has no worksheets")
        data = sheets[0].get("data") or []
        row_data = data[0].get("rowData", []) if data else []
        return [self._cells(row.get("values", [])) for row in row_data]

    @staticmethod
    def _cells(values: list[dict[str, Any]]) -> list[Cell]:
        cells = []
        for raw in values:
            links = []
            if raw.get("hyperlink"):
                links.append(str(raw["hyperlink"]))
            for run in raw.get("textFormatRuns") or []:
                uri = ((run.get("format") or {}).get("link") or {}).get("uri")
                if uri:
                    links.append(str(uri))
            cells.append(
                Cell(
                    value=str(raw.get("formattedValue") or "").strip(),
                    links=tuple(dict.fromkeys(links)),
                )
            )
        return cells

    def drive_metadata(self, file_id: str) -> dict[str, str]:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        response = self.session.get(url, params={"fields": "id,name,mimeType"}, timeout=60)
        _raise_google_error(response, f"read Drive metadata for {file_id}")
        return response.json()

    def download_drive_file(self, file_id: str, destination: Path) -> None:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        response = self.session.get(url, params={"alt": "media"}, timeout=180)
        _raise_google_error(response, f"download Drive file {file_id}")
        destination.write_bytes(response.content)


def _raise_google_error(response: requests.Response, action: str) -> None:
    if response.ok:
        return
    detail = response.text[:500]
    raise ImportError(f"could not {action}: Google API {response.status_code}: {detail}")


def _cell(row: list[Cell], index: int | None) -> Cell:
    if index is None or index >= len(row):
        return Cell("")
    return row[index]


def _header_index(headers: list[Cell], *names: str) -> int | None:
    normalized = {cell.value.strip().casefold(): index for index, cell in enumerate(headers)}
    for name in names:
        if name.casefold() in normalized:
            return normalized[name.casefold()]
    return None


def _required_header(headers: list[Cell], *names: str) -> int:
    index = _header_index(headers, *names)
    if index is None:
        raise ImportError(f"spreadsheet is missing the {names[0]!r} column")
    return index


def _file_id(value: str) -> str | None:
    parsed = urlparse(value)
    query_id = parse_qs(parsed.query).get("id")
    if query_id:
        return query_id[0]
    path_match = re.search(r"/(?:file/d|d)/([A-Za-z0-9_-]+)", parsed.path)
    if path_match:
        return path_match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", value):
        return value
    return None


def _file_ids(cell: Cell) -> tuple[str, ...]:
    candidates = list(cell.links)
    candidates.extend(re.findall(r"https?://[^,\s]+", cell.value))
    if not candidates and cell.value:
        candidates.extend(part.strip() for part in cell.value.split(","))
    ids = [_file_id(candidate) for candidate in candidates]
    return tuple(dict.fromkeys(file_id for file_id in ids if file_id))


def _submission_date(value: str, timestamp: str) -> date:
    for candidate in (value, timestamp):
        if not candidate:
            continue
        try:
            return date_parser.parse(candidate).date()
        except (ValueError, OverflowError):
            continue
    return datetime.now().astimezone().date()


def _tags(value: str) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in value.split(","):
        tag = raw.strip()
        key = tag.casefold()
        if tag and key not in seen:
            result.append(tag)
            seen.add(key)
    return tuple(result)


def parse_submissions(rows: list[list[Cell]]) -> list[Submission]:
    if not rows:
        return []
    headers = rows[0]
    image_column = _required_header(headers, "Image")
    title_column = _required_header(headers, "Identification", "Title")
    orientation_column = _required_header(headers, "Orientation")
    timestamp_column = _header_index(headers, "Timestamp")
    description_column = _header_index(headers, "Description", "Notes")
    date_column = _header_index(headers, "Date")
    location_column = _header_index(headers, "Location")
    tags_column = _header_index(headers, "Tags")

    submissions = []
    for row_number, row in enumerate(rows[1:], start=2):
        title = _cell(row, title_column).value
        image_cell = _cell(row, image_column)
        file_ids = _file_ids(image_cell)
        if not title and not image_cell.value and not image_cell.links:
            continue
        if not title:
            raise ImportError(f"row {row_number}: Identification or Title is blank")
        if not file_ids:
            raise ImportError(f"row {row_number}: could not find a Drive file ID in Image")
        orientation = _cell(row, orientation_column).value.casefold()
        if orientation not in {"portrait", "landscape"}:
            raise ImportError(f"row {row_number}: Orientation must be Portrait or Landscape")

        timestamp = _cell(row, timestamp_column).value
        entry_date = _submission_date(_cell(row, date_column).value, timestamp)
        description = _cell(row, description_column).value
        location = _cell(row, location_column).value
        tags = _tags(_cell(row, tags_column).value)
        identity = json.dumps(
            {
                "timestamp": timestamp,
                "file_ids": file_ids,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        submissions.append(
            Submission(
                key=key,
                row_number=row_number,
                title=title,
                entry_date=entry_date,
                orientation=orientation,
                description=description,
                location=location,
                tags=tags,
                file_ids=file_ids,
            )
        )
    return submissions


def _safe_stem(name: str) -> str:
    stem = Path(name).stem
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-.")
    return cleaned or "image"


def _unique_path(directory: Path, stem: str, suffix: str) -> Path:
    destination = directory / f"{stem}{suffix}"
    number = 2
    while destination.exists():
        destination = directory / f"{stem}-{number}{suffix}"
        number += 1
    return destination


def download_image(client: GoogleClient, file_id: str, directory: Path) -> Path:
    metadata = client.drive_metadata(file_id)
    mime_type = str(metadata.get("mimeType") or "").casefold()
    name = str(metadata.get("name") or "image")
    stem = _safe_stem(name)
    if mime_type in SUPPORTED_MIME_TYPES:
        destination = _unique_path(directory, stem, SUPPORTED_MIME_TYPES[mime_type])
        client.download_drive_file(file_id, destination)
        return destination
    if mime_type in HEIF_MIME_TYPES or Path(name).suffix.casefold() in {".heic", ".heif"}:
        source = _unique_path(directory, stem, ".heic")
        destination = _unique_path(directory, source.stem, ".jpg")
        client.download_drive_file(file_id, source)
        register_heif_opener()
        with Image.open(source) as image:
            exif = image.info.get("exif")
            save_options: dict[str, Any] = {"quality": 92}
            if exif:
                save_options["exif"] = exif
            image.convert("RGB").save(destination, "JPEG", **save_options)
        return destination
    raise ImportError(f"Drive file {name!r} has unsupported type {mime_type!r}")


def load_state() -> set[str]:
    if not STATE_PATH.is_file():
        return set()
    try:
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportError(f"could not read {STATE_PATH}: {exc}") from exc
    if not isinstance(raw, list) or not all(isinstance(value, str) for value in raw):
        raise ImportError(f"{STATE_PATH} must contain a JSON list of import keys")
    return set(raw)


def save_state(keys: set[str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(sorted(keys), indent=2) + "\n", encoding="utf-8")


def import_new_submissions(project_root: Path) -> int:
    credentials_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    spreadsheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()
    if not credentials_json:
        raise ImportError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")
    if not spreadsheet_id:
        raise ImportError("GOOGLE_SHEET_ID is not set")

    client = GoogleClient(credentials_json)
    submissions = parse_submissions(client.spreadsheet_rows(spreadsheet_id))
    imported = load_state()
    new_count = 0
    for submission in submissions:
        if submission.key in imported:
            continue
        with tempfile.TemporaryDirectory(prefix="collections-form-") as temporary:
            temporary_path = Path(temporary)
            images = [
                download_image(client, file_id, temporary_path) for file_id in submission.file_ids
            ]
            try:
                created = create_photo_entry(
                    project_root,
                    title=submission.title,
                    entry_date=submission.entry_date,
                    image_paths=images,
                    location=submission.location,
                    orientation=submission.orientation,
                    tags=submission.tags,
                    notes=submission.description,
                )
            except CreationError as exc:
                raise ImportError(f"row {submission.row_number}: {exc}") from exc
        imported.add(submission.key)
        save_state(imported)
        new_count += 1
        print(f"Imported row {submission.row_number} as {created.entry_id}")
    print(f"Imported {new_count} new submission(s)")
    return new_count


def main() -> int:
    try:
        import_new_submissions(PROJECT_ROOT)
    except ImportError as exc:
        print(f"Import failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
