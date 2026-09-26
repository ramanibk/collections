# Phone-first photo journal: technical plan

Status: proposed; not yet implemented.

## 1. Recommendation

Add the workflow without replacing the existing Python/Jinja site or changing its
content-first architecture.

Use:

- the existing GitHub Pages repository as the content source of truth;
- one Google Apps Script clock trigger to detect new Drive files;
- one Cloudflare Worker for GitHub sign-in, authorization, and repository writes;
- one GitHub Action for image ingestion and metadata enrichment;
- a small static, mobile-first `/admin/` application built with HTML, CSS, and
  vanilla JavaScript;
- the existing Pages workflow for public builds.

This is the smallest practical design because Google Drive has no simple
"folder changed" trigger for GitHub Actions, and GitHub Pages cannot safely hold
API credentials or perform authenticated writes by itself.

Do not add a database or a frontend framework. The backend should be stateless.
GitHub remains the durable store.

## 2. Existing repository fit

The repository already provides most of the required foundation:

- Markdown plus YAML frontmatter is the source of truth.
- Each entry owns a directory, `entry.md`, and adjacent images.
- `journal.creation` safely allocates permanent IDs and creates entries.
- `journal.loader` and `journal.validation` parse and validate all content.
- `journal.builder` stages a complete static build and copies entry media.
- `.github/workflows/pages.yml` tests, validates, builds, and deploys Pages.
- The public site is plain HTML/CSS with minimal JavaScript and already has
  phone breakpoints.

The requested example cannot be copied literally. In this repository, `status`
already records a craft project's lifecycle (`planned`, `in-progress`,
`completed`, and so on). Use a new common field named `publication_status` for
draft/published state. Existing content defaults to `published`, so this change
is backward compatible.

The Markdown body remains the personal journal text. Do not add a second
`journal` field to frontmatter.

## 3. Target architecture

```text
Lightroom Mobile
  -> Google Drive / Journal Inbox
  -> Google Apps Script (clock trigger, normally every 5 minutes)
  -> POST /v1/ingest on Cloudflare Worker (signed request)
  -> GitHub App installation token
  -> workflow_dispatch: ingest-photo.yml
  -> Drive download + EXIF + weather + Gemini + image optimization
  -> draft entry committed to main
  -> explicit workflow_dispatch: pages.yml

Phone browser
  -> GitHub Pages /admin/
  -> Cloudflare Worker GitHub App OAuth
  -> immutable GitHub numeric user ID check
  -> GitHub Contents API
  -> save draft or publish commit
  -> existing Pages push build
```

Google Drive push notifications are a possible later optimization, but they
require a public webhook receiver and renewable notification channels. A short
Apps Script poll is easier to operate and is sufficient for a personal inbox.

## 4. Content model

An ingested cloud entry should look like this:

```yaml
---
id: obs-000123
title: Untitled photo
date: 2026-09-03
type: observation
category: clouds
publication_status: draft
captured_at: 2026-09-03T18:42:00-07:00
location: Berkeley, California
cover: cloud-001.jpg
image_alt: A field of small rounded clouds in warm evening light.
tags:
  - clouds
  - evening
weather:
  temperature_f: 68
  humidity_percent: 62
  conditions: partly_cloudy
cloud_genus: altocumulus
identification: tentative
identification_verified: false
ai_analysis:
  model: configured-gemini-model
  category: clouds
  subjects:
    - clouds
  suggested_tags:
    - evening
  description: A field of rounded cloudlets lit by a low sun.
  identification:
    kind: cloud
    value: Altocumulus
    confidence: 0.81
ingestion:
  key: sha256:PUBLIC_HASH_ONLY
  source_sha256: sha256:IMAGE_HASH
  imported_at: 2026-09-03T19:01:22Z
instagram_url: ""
---

```

Rules:

- `publication_status` is `draft` or `published` and defaults to `published`
  when absent.
- The Markdown body starts empty and is edited only by the owner.
- `ai_analysis` is evidence/suggestion data, never a verified claim.
- Category-specific fields such as `cloud_genus` or `common_name` may be
  prefilled, but `identification` starts as `tentative` and
  `identification_verified` starts as `false`.
- Gemini confidence is a number from 0 through 1. The existing human-facing
  `confidence` field remains an optional integer from 1 through 5.
- `date` is the local capture date used by the existing site. `captured_at`
  retains the best available timestamp and offset.
- `weather`, `ai_analysis`, and `ingestion` are stored as structured
  frontmatter and validated before commit.
- Only an HMAC/SHA-256 derivative of the Drive file ID is committed. The Drive
  ID itself is used only by the trigger, Worker, and ingestion run.
- Exact latitude, longitude, full EXIF blocks, and the original unstripped
  image are never committed.

The first implementation should accept JPEG input only. Lightroom Mobile can
export JPEG consistently. HEIC support can be added later if it is actually
needed.

## 5. Phase 1: ingestion

### 5.1 Drive trigger

Add `integrations/google-apps-script/JournalInbox.gs` as a small, copyable Apps
Script source file.

On each clock run it:

1. Lists image files in the configured Journal Inbox folder.
2. Ignores folders, non-JPEG files, and files already acknowledged in Script
   Properties.
3. Sends only the Drive file ID, file name, timestamp, and a request timestamp
   to the Worker.
4. Signs the exact request body with `HMAC-SHA256` using a Script Property.
5. Records the file ID as acknowledged only after the Worker returns success.

Script Properties:

- `JOURNAL_FOLDER_ID`
- `JOURNAL_INGEST_URL`
- `JOURNAL_INGEST_SECRET`

The Script Property acknowledgement is a convenience, not the authoritative
idempotency mechanism.

### 5.2 Worker dispatch endpoint

`POST /v1/ingest` must:

1. Require JSON and a small request-size limit.
2. Verify the HMAC in constant time.
3. Reject timestamps outside a five-minute window.
4. Validate the Drive file ID and file name as data, never shell input.
5. Mint a repository-scoped GitHub App installation token with only Actions
   write permission.
6. Dispatch `.github/workflows/ingest-photo.yml` on `main` with the Drive file
   ID as an input.

Return `202 Accepted` after GitHub accepts the dispatch. Repeated dispatches are
safe because the action performs the authoritative duplicate check.

### 5.3 Ingestion workflow

Add `.github/workflows/ingest-photo.yml` with:

- `workflow_dispatch` and one required `drive_file_id` input;
- a repository-wide `photo-ingestion` concurrency group with
  `cancel-in-progress: false`;
- Python 3.12;
- `contents: write` and `actions: write` job permissions;
- a job timeout;
- no pull-request or arbitrary branch trigger.

Use Python modules under `scripts/photo_ingest/` rather than a long YAML shell
script:

```text
scripts/photo_ingest/
  __init__.py
  main.py          orchestration and result reporting
  drive.py         authenticated download
  exif.py          normalized capture/device/GPS extraction
  privacy.py       coarse location and metadata stripping
  weather.py       historical weather adapter
  gemini.py        structured image analysis
  media.py         orientation, resize, color conversion, JPEG output
  entry.py         repository-specific draft creation
```

Processing order:

1. Validate the workflow input.
2. Compute `sha256("google-drive:" + drive_file_id)`.
3. Scan existing entry frontmatter for the ingestion key; exit successfully if
   found.
4. Download the file from Drive with a service account that can read only the
   shared Journal Inbox folder.
5. Validate MIME type, file signature, pixel count, and maximum input size.
6. Read EXIF capture time, orientation, GPS, camera make/model, and device.
7. Determine a timezone from GPS when possible; otherwise preserve the source
   offset or mark the timestamp as approximate.
8. Query historical weather using the temporary coordinates and capture time.
9. Reverse-geocode only to a configured coarse form such as city and state.
10. Send the image to Gemini with a small JSON schema and an explicit instruction
    that taxonomic identification is uncertain.
11. Validate and normalize Gemini output; never place arbitrary model output in
    paths, IDs, or workflow commands.
12. Apply EXIF orientation, convert to sRGB, resize to a configured maximum long
    edge, encode an optimized JPEG, and omit all EXIF/GPS metadata.
13. Create a draft using the existing permanent-ID and validation layers.
14. Re-scan the complete content tree, run tests/validation as appropriate, and
    commit the entry plus `.id-sequences.yaml`.
15. Push with a bounded fetch/rebase/retry to handle a concurrent admin commit.
16. Explicitly dispatch `pages.yml` after the successful push.

Suggested image defaults are a 2400-pixel maximum long edge, JPEG quality 85,
and no upscaling. Make these constants easy to change.

### 5.4 External-service behavior

Use adapters and keep enrichment non-fatal:

- Drive download, valid image decoding, safe output, entry validation, and
  commit are required. Fail the run if one fails.
- EXIF fields are optional. When capture time is absent, use Drive creation time
  and record `capture_time_source: drive_created_time`.
- GPS is optional. Without it, omit location and weather.
- Weather, reverse geocoding, and Gemini are best-effort. If one is unavailable,
  create the draft with an `ingestion.warnings` value so the photo is not lost.
- Do not add factual cloud/bird/plant reference lookups in the first release.

For weather, use one provider behind a small adapter. Open-Meteo's historical
API is a reasonable default because it accepts coordinates, date/time, and
hourly variables without requiring a browser-side key. Pin the response fields
that are stored and retain the provider name in frontmatter.

For coarse location, use a separately configurable reverse-geocoding adapter.
If it is not configured or fails, leave `location` blank rather than storing
coordinates or inventing a place.

For Gemini, request structured JSON with enums and bounded arrays, then perform
normal application validation. Structured output guarantees format, not factual
correctness.

### 5.5 Idempotency

Idempotency is enforced in three layers:

1. Apps Script avoids dispatching acknowledged files.
2. The action serializes ingestion runs.
3. The action checks the committed `ingestion.key` before doing expensive work
   and again immediately before committing.

The committed hash is authoritative. A rerun for the same Drive file exits zero
without creating a new permanent ID or commit. The source image SHA-256 is also
stored to help diagnose a replaced Drive file, but it is not the primary key.

## 6. Public build changes

Extend `ContentEntry` with `publication_status`, but leave the existing project
`status` behavior unchanged.

After parsing and validating all entries, `journal.builder` must derive
`public_entries` and use it everywhere that currently uses `loaded.entries`:

```python
public_entries = tuple(
    entry for entry in loaded.entries
    if entry.publication_status == "published"
)
```

Only `public_entries` may be passed to statistics, category builders, indexes,
entry-page rendering, or media copying. This prevents a draft from leaking via
counts, lists, generated entry URLs, taxonomy pages, or `/media/`.

Validation still covers drafts so malformed drafts cannot silently accumulate.
Add tests that search all generated HTML and generated file names for draft IDs,
titles, body text, and image names.

Important privacy boundary: this prevents drafts from appearing on the Pages
site, but a draft committed to a public repository is still readable through
GitHub and remains in Git history. If drafts must be private, use a separate
private repository or private draft branch and copy only published content to
this repository. That is intentionally outside this simple first version.

## 7. Phase 2: phone editor

### 7.1 Static admin application

Generate or copy these into the Pages build:

```text
static/admin/admin.css
static/admin/admin.js
templates/admin.html
```

`/admin/` contains no entry data, credentials, or secrets. It calls the Worker
API after sign-in.

Required screens:

- signed-out page with a GitHub sign-in button;
- draft list, newest first;
- editor with the photo, automatic metadata, warnings, and mutable fields;
- clear Save draft and Publish actions;
- inline validation, saving state, conflict state, and error state.

Editable fields in the first version:

- title;
- category and category-specific identification fields;
- tags;
- `identification_verified`;
- Instagram URL;
- Markdown body (the personal journal entry).

Automatic weather, EXIF summary, capture time, and ingestion identity are
read-only. AI description may be edited only if it is also used as image alt
text. Do not generate or rewrite the Markdown body.

The editor should use a single-column layout, large touch targets, labels above
controls, no hover-only interactions, and a sticky action bar. It should work at
320 CSS pixels wide and remain usable with a phone keyboard open.

### 7.2 Cloudflare Worker API

Keep routing and GitHub-specific code separate so the core logic can later move
to another Fetch-compatible runtime.

```text
backend/
  package.json
  wrangler.jsonc
  src/
    index.ts        routes, CORS, errors
    auth.ts         OAuth, PKCE, state, session, owner check
    github-app.ts   JWT and installation-token creation
    github.ts       repository reads and optimistic writes
    entries.ts      schema, allowlisted edits, YAML/Markdown serialization
    security.ts     origin, CSRF, cookie, HMAC helpers
  test/
```

Endpoints:

```text
GET  /auth/github
GET  /auth/callback
GET  /v1/session
GET  /v1/drafts
GET  /v1/drafts/:id
GET  /v1/drafts/:id/photo
PUT  /v1/drafts/:id
POST /v1/drafts/:id/publish
POST /v1/ingest
```

Behavior:

- OAuth uses the GitHub App web flow with PKCE and a random, expiring `state`.
- After callback, request the authenticated GitHub user and compare the numeric
  `id` to `ALLOWED_GITHUB_USER_ID`. Never authorize by login name or email.
- Discard the user access token after identity verification. Repository reads
  and writes use short-lived GitHub App installation tokens.
- OAuth `state` and the PKCE verifier use short-lived, signed, `Secure`,
  `HttpOnly`, `SameSite=Lax` cookies on the Worker. They work because OAuth
  navigation and callback are top-level requests.
- The configured Pages site and a default Workers domain are different sites.
  Do not rely on a third-party session cookie, because mobile browsers may block
  it. After successful OAuth, issue a short-lived signed admin session token in
  the URL fragment of the redirect back to `/admin/`. The admin script must
  immediately remove the fragment with `history.replaceState`, retain the token
  only in `sessionStorage`, and send it as `Authorization: Bearer ...`.
- The admin session contains only the immutable user ID, issue/expiry times, and
  a random session ID. It is not a GitHub token and expires after at most one
  hour. Signing uses `SESSION_SECRET`. Logout deletes it from `sessionStorage`.
- Apply a strict Content Security Policy to `/admin/`, load no third-party
  scripts, and never use `innerHTML` with repository data.
- Restrict CORS to the exact configured Pages origin. Do not allow credentialed
  wildcard origins.
- Require the expected `Origin` and the bearer session on every mutation.
- Set `Cache-Control: no-store` on all authenticated responses.
- Accept only known entry IDs and verify their resolved repository paths stay
  under `content/`.
- Parse YAML on the server and update only an allowlist of editable fields.
  Preserve read-only ingestion metadata and unknown existing fields.
- Validate the full result before writing.
- Use the GitHub Contents API file `sha` as an optimistic lock. Return `409
  Conflict` if the entry changed after it was opened; never overwrite silently.
- The photo endpoint proxies the draft image from GitHub after authorization,
  because draft media is deliberately absent from the Pages build.
- Saving writes `publication_status: draft`. Publishing writes
  `publication_status: published`. Each action makes one descriptive commit.

### 7.3 GitHub App permissions

Install the GitHub App on this repository only.

Repository permissions:

- Contents: read and write (admin reads/updates and commits)
- Actions: write (dispatch ingestion)
- Metadata: read (implicit)

Subscribe to no webhooks. Request no organization permissions. When minting an
installation token, scope it to this repository and, where supported, to only
the permission needed for that operation.

## 8. Secrets and configuration

Do not commit `.dev.vars`, `.env`, service-account JSON, private keys, access
tokens, or API keys. Extend `.gitignore` for local backend secret files.

### GitHub Actions secrets

- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`
- `GEMINI_API_KEY`
- optional `GEOCODING_API_KEY`

The weather provider needs no secret if Open-Meteo is used.

### Cloudflare Worker secrets

- `GITHUB_APP_PRIVATE_KEY`
- `GITHUB_APP_CLIENT_SECRET`
- `SESSION_SECRET`
- `INGEST_HMAC_SECRET`

### Non-secret Worker configuration

- `GITHUB_APP_ID`
- `GITHUB_APP_CLIENT_ID`
- `GITHUB_APP_INSTALLATION_ID`
- `GITHUB_OWNER=ramanibk`
- `GITHUB_REPO=collections`
- `GITHUB_BRANCH=main`
- `ALLOWED_GITHUB_USER_ID` (numeric; it is an identifier, not a credential)
- `ADMIN_ORIGIN` (the exact Pages origin)
- `OAUTH_CALLBACK_URL`

### Apps Script properties

- `JOURNAL_FOLDER_ID`
- `JOURNAL_INGEST_URL`
- `JOURNAL_INGEST_SECRET` (same value as the Worker HMAC secret)

The final implementation should add exact creation, installation, sharing,
secret-setting, deployment, smoke-test, and key-rotation instructions to the
main README.

## 9. Proposed repository changes

```text
.github/workflows/ingest-photo.yml
backend/
docs/photo-journal-technical-plan.md
integrations/google-apps-script/JournalInbox.gs
scripts/photo_ingest/
static/admin/admin.css
static/admin/admin.js
templates/admin.html
tests/test_drafts.py
tests/test_ingestion.py
```

Small changes are also required in:

- `journal/models.py`
- `journal/parser.py`
- `journal/validation.py`
- `journal/builder.py`
- `journal/creation.py`
- `journal/urls.py`
- `.gitignore`
- `README.md`

Do not add a new content tree, database, CMS, or JavaScript build pipeline.

## 10. Delivery order and acceptance criteria

### Milestone A: draft-safe site

- Add and validate `publication_status`.
- Exclude drafts and their media from every public output.
- Add `/admin/` shell without secrets.

Acceptance: a fixture draft cannot be found anywhere under `public/`, while
existing entries still publish without modification.

### Milestone B: deterministic local ingestion

- Implement the Python ingestion modules with provider interfaces.
- Exercise them from local fixture files and mocked HTTP responses.
- Reuse repository entry creation, permanent IDs, and validation.

Acceptance: two runs with the same Drive identity produce one entry; optimized
output contains no GPS/EXIF metadata; missing optional enrichment still creates
a valid draft.

### Milestone C: GitHub Action and Drive bridge

- Add `ingest-photo.yml`.
- Add the signed Worker dispatch route.
- Add the Apps Script poller.
- Explicitly start the Pages workflow after an ingestion commit.

Acceptance: adding one JPEG to Journal Inbox produces one draft commit and a
successful Pages build; replaying the request produces no second entry.

### Milestone D: authenticated phone editor

- Complete GitHub App OAuth and immutable-user-ID authorization.
- Implement draft list/read/update/publish endpoints.
- Complete the mobile editor and conflict handling.

Acceptance: an unauthorized GitHub account cannot read draft metadata or
photos; the owner can save a draft and publish it; publishing causes the entry
to appear after the Pages build.

### Milestone E: hardening and documentation

- Run Python tests, backend tests, content validation, and a real build.
- Verify the editor on a narrow phone viewport and with keyboard navigation.
- Test duplicate dispatch, stale SHA, provider timeout, missing GPS, malformed
  image, and revoked GitHub App access.
- Add the exact README setup/runbook and a secret-rotation checklist.

## 11. Deliberately deferred

Keep these out of the first release:

- cloud, bird, or plant reference databases and citations;
- Instagram API integration or automatic Instagram posting;
- Drive push-notification channel renewal;
- multiple-user roles;
- a database, search service, job queue, or CMS;
- HEIC/RAW ingestion;
- AI-generated journal prose;
- editing already-published entries from `/admin/` unless later requested.

The Instagram field is only an optional URL. Rich reference enrichment should
be a later, separately tested adapter that never changes an identification from
unverified to verified.

## 12. Primary implementation references

- [GitHub workflow dispatch REST endpoint](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
- [GitHub token workflow-trigger behavior](https://docs.github.com/en/actions/concepts/security/github_token#when-github_token-triggers-workflow-runs)
- [GitHub repository contents API](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents)
- [GitHub App user authorization](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
- [GitHub App installation authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)
- [Google Apps Script installable triggers](https://developers.google.com/apps-script/guides/triggers/installable)
- [Google Drive change notifications](https://developers.google.com/workspace/drive/api/guides/push)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Cloudflare Worker secrets](https://developers.cloudflare.com/workers/configuration/secrets/)
- [Cloudflare Worker Web Crypto](https://developers.cloudflare.com/workers/runtime-apis/web-crypto/)
