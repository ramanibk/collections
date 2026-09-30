# Collections

A small, file-backed personal site for photographs, notes, and an about page. Markdown files with YAML front matter are the source of truth; the Python builder validates them and generates a static site in `public/`.

## Setup

Python 3.12 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Everyday workflow

Create content interactively:

```bash
python journal.py add photo
python journal.py add note
python journal.py add essay
```

Validate, build, and preview:

```bash
python journal.py validate
python journal.py build
python journal.py preview
```

Run development checks:

```bash
ruff check .
ruff format --check .
python -m pytest
```

## Content

The About page is authored in `content/about.md`; its front matter contains the portrait and professional links, while its Markdown body contains the biography.

Photographs live under `content/photographs/`. A photograph requires at least one adjacent image:

```yaml
---
id: photo-000001
title: Window light
date: 2026-09-01
type: photo
orientation: portrait
location: Berkeley, California
cover: window.jpg
tags: [light, home]
---

Late summer light across the room.
```

Notes and essays live under `content/notes/`:

```yaml
---
id: note-000001
title: Durable systems
date: 2026-09-02
type: essay
tags: [systems, research]
---

The note body is ordinary Markdown.
```

Required fields are `id`, `title`, `date`, and `type`. Valid types are `photo`, `note`, and `essay`. Photo orientation is `portrait` or `landscape`. Tags are trimmed and deduplicated case-insensitively during parsing.

## Structure

```text
content/          About Markdown plus source photographs and notes
journal/          parsing, validation, creation, URLs, CLI, and build logic
templates/        About, Photographs, Notes, Filter, entry, and error views
static/           styles, fonts, scripts, and sample images
tests/            focused content, build, CLI, and deployment tests
public/           generated output; never edit directly
```

The public navigation contains only About, Photographs, and Notes. The cross-content tag filter is a supporting archive utility linked from the footer and generated at `/photographs/filter/`.

## Configuration and deployment

`config.yaml` controls the site title, subtitle, deployment base URL, and generated output directory. All links use `journal/urls.py`, so a GitHub Pages project base path is applied consistently.

The GitHub Pages workflow runs Ruff, tests, content validation, and the static build before deployment.
