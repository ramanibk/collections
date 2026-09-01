# Field Notes

A local-first personal archive for observations, photographs, and creative work. Plain Markdown files with YAML frontmatter are the source of truth; a small Python application validates them and generates an ordinary static site in `public/`.

The initial collections are Clouds, Birds, Cats, Making, Curiosities, and the site-wide chronological Journal. There is no database, CMS, JavaScript framework, or client-side rendering requirement.

## Setup

Field Notes requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The only runtime dependencies are Jinja2, PyYAML, and Markdown. Pytest is included for development checks.

## Everyday workflow

Create an entry with an interactive prompt:

```bash
python journal.py add cloud
```

The other entry types are `bird`, `cat`, `project`, and `curiosity`. Running `python journal.py add` asks which type to create. Images are validated and copied beside the new `entry.md`; the command does not commit anything to Git.

Check, build, and preview the archive:

```bash
python journal.py validate
python journal.py build
python journal.py preview
```

Preview uses `http://127.0.0.1:8000/` by default. Choose another port with `python journal.py preview --port 8080`. The preview command builds first and understands a configured GitHub Pages base path.

View collection totals without building:

```bash
python journal.py stats
```

Run the complete test suite:

```bash
python -m pytest
```

`python build.py` remains as a backward-compatible shortcut for `python journal.py build`.

## Project structure

```text
content/                 Markdown entries and their original images
journal/                 parsing, models, validation, derivation, CLI, and build logic
templates/               Jinja page templates
static/css/              design variables and modular stylesheets
tests/                    temporary-directory unit and integration tests
.github/workflows/       GitHub Pages deployment
config.yaml              site title, base URL, output, and taxonomy options
journal.py               main command
public/                  generated output; safe to delete and rebuild
```

Generated files in `public/` are ignored by Git. Edit source content, templates, styles, or Python modules instead.

## Content format

Every item has its own directory containing `entry.md` and optional adjacent images:

```text
content/clouds/2026-08-31-altocumulus-before-sunset/
├── entry.md
├── cloud.jpg
└── cloud-2.jpg
```

An entry is Markdown with YAML frontmatter:

```markdown
---
id: obs-000001
title: Altocumulus Before Sunset
date: 2026-08-31
type: observation
category: clouds
location: Berkeley, California
cloud_genus: altocumulus
cloud_species: stratiformis
identification: tentative
confidence: 4
cover: cloud.jpg
favorite: false
tags:
  - clouds
  - sunset
---

A broad field of rounded cloudlets appeared before sunset.
```

All entries require `id`, `title`, `date`, and `category`. Common optional fields are `type`, `location`, `cover`, `favorite`, `tags`, `status`, and `image_alt`.

Category-specific fields:

- Clouds: `cloud_genus`, `cloud_species`, `cloud_variety`, `supplementary_features`, `optical_phenomena`, `identification`, and `confidence`.
- Birds: `common_name`, `scientific_name`, `identification`, `confidence`, and `count`.
- Cats: `cat_name` and `relationship`. Named personal cats are Gwen, Billy, and Jet; other cats use `relationship: encounter`.
- Making: `craft`, `status`, `started`, `completed`, and `materials`.
- Curiosities deliberately permit flexible extra metadata.

Dates use `YYYY-MM-DD`. Confidence is an integer from 1 through 5. Supported image formats are JPEG, PNG, and WebP. When `image_alt` is absent, templates conservatively use the entry title.

## Permanent IDs

Identity never depends on a title, slug, or directory name. Clouds and birds use `obs-`, cats use `cat-`, projects use `proj-`, and curiosities use `cur-`, followed by a six-digit sequence.

The creation layer scans existing entries and advances the sequence. It never fills gaps. It also records committed high-water marks in `content/.id-sequences.yaml`, so deleting the latest entry does not make that ID available again. Keep this file under version control and never change an existing entry's ID.

## Configuration and URLs

Edit `config.yaml` to change the site title, subtitle, number of recent homepage entries, output directory, or cloud taxonomy display behavior.

For a GitHub Pages project site at `https://USERNAME.github.io/REPOSITORY/`, set:

```yaml
site:
  base_url: /REPOSITORY
```

Use an empty value for a root site or custom domain:

```yaml
site:
  base_url: ""
```

All routes and asset links pass through `journal/urls.py`, so the configured base path is applied consistently. Permanent entry pages use IDs, while human-facing taxonomy pages use normalized slugs.

## GitHub Pages deployment

The workflow in `.github/workflows/pages.yml` runs on pushes to `main`. It installs Python 3.12, runs tests, validates content, builds the site, uploads `public/`, and deploys with the current GitHub Pages Actions flow.

Before the first deployment:

1. Push the repository to GitHub with `main` as the deployment branch.
2. Set the correct `site.base_url` in `config.yaml` as described above.
3. Open the repository's **Settings → Pages**.
4. Under **Build and deployment**, choose **GitHub Actions** as the source.
5. Push to `main`, or run the “Deploy GitHub Pages” workflow manually.

The generated `public/` directory does not need to be committed.

## Customizing the site

- Change colors, spacing, fonts, and widths in `static/css/variables.css`.
- Change global layout in `static/css/layout.css`, type in `typography.css`, image grids in `gallery.css`, and breakpoints in `responsive.css`.
- Change shared navigation and metadata in `templates/base.html`; change individual pages in their corresponding templates.
- Change derived counts in `journal/stats.py`, routes in `journal/urls.py`, and build orchestration in `journal/builder.py`.

To add a future category, update the taxonomy, typed metadata parsing, validation fields, URL mapping, creation workflow, derived collection logic, builder route, templates, and tests. Keep parsing, derivation, rendering, and filesystem operations separate rather than adding category logic directly to templates.

## Sample content and maintenance

There is currently no bundled sample entry to remove. If sample entries are added later, delete their complete directories and rebuild; do not edit `public/` directly. Keep `content/.id-sequences.yaml` so their permanent IDs remain retired.

Before publishing changes, run:

```bash
python -m pytest
python journal.py validate
python journal.py build
```

Implementation progress and verification history are recorded in `PLAN_PROGRESS.md`; the complete original specification remains in `plan.md`.
