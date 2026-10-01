# Google Form importer

This integration polls the response spreadsheet for the private Google Form at
https://forms.gle/a7yWWGcUeQD4soBL6. New rows become photograph entries, and the
existing Pages workflow publishes them.

The Form does not contain GitHub credentials or Apps Script. GitHub Actions gets
read-only access to the response spreadsheet and upload folder through a Google
service account.

## Form fields

These existing question titles are recognized:

- `Image` — required file upload; one or more images
- `Identification` or `Title` — required; becomes the photograph title
- `Orientation` — required; `Portrait` or `Landscape`
- `Notes` or `Description` — optional; becomes the photograph description

Every Form submission creates a `photo` entry under `content/photographs/`. This
field does not create a field log, journal note, essay, or anything under
`content/notes/`. Renaming the Form question from `Notes` to `Description` is
optional; both titles are supported.

The importer also recognizes optional `Date`, `Location`, and `Tags` questions.
`Tags` should be comma-separated. Without `Date`, the Form submission date is
used.

JPEG, PNG, and WebP are copied directly. HEIC and HEIF uploads are converted to
JPEG automatically.

## One-time Google setup

1. In the Form's **Responses** tab, click **Link to Sheets** and create a response
   spreadsheet.
2. In Google Cloud Console, create a project and enable both **Google Sheets API**
   and **Google Drive API**.
3. Create a service account and download its JSON key.
4. Share the response spreadsheet with the service account email as **Viewer**.
5. From the Form editor, click **View folder** beside the `Image` question and
   share that upload folder with the same service account as **Viewer**. Folder
   access lets the account download current and future uploads.

The spreadsheet ID is the text between `/d/` and `/edit` in its URL:

```text
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

## One-time GitHub setup

In `ramanibk/collections`, open **Settings > Secrets and variables > Actions** and
create these repository secrets:

- `GOOGLE_SERVICE_ACCOUNT_JSON` — the complete contents of the downloaded JSON key
- `GOOGLE_SHEET_ID` — the response spreadsheet ID

Never commit the JSON key to this repository.

## Schedule and testing

`.github/workflows/import-google-form.yml` checks for submissions every 30 minutes.
It can also be started immediately from **Actions > Import Google Form submissions
> Run workflow**.

For the first test, submit one image through the Form and run the workflow
manually. A successful import commits a new directory under
`content/photographs/` and dispatches the existing Pages workflow.

Imported rows are recorded in `content/.google-form-imports.json`, using a hash of
the submission timestamp and uploaded Drive file IDs. This prevents scheduled
runs from importing the same row twice.
