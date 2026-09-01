Build a complete, maintainable, file-driven static personal journal/archive site.

The repository is intended to become a long-lived personal archive for observations and creative work. The initial content categories are:

* Clouds
* Birds
* Cats
* Making / Crafts
* Curiosities
* Journal

The system should be optimized for:

* local-first authoring
* plain files as the source of truth
* simple Python tooling
* predictable generated HTML
* Git-based version history
* deployment to GitHub Pages
* long-term maintainability
* easy future extension

Do not use a database or heavyweight frontend framework.

---

# 1. Technology stack

Use:

* Python 3.12+
* Jinja2
* PyYAML
* Markdown
* standard library modules where practical
* plain HTML
* plain CSS
* minimal vanilla JavaScript only where it provides clear value
* GitHub Pages-compatible static output

Do not use:

* React
* Vue
* Svelte
* Astro
* Next.js
* Flask
* Django
* a database
* a CMS
* Tailwind
* Bootstrap
* Node.js unless absolutely unavoidable
* client-side rendering for core content

The generated site must work as ordinary static files.

---

# 2. Architectural principle

The source files are the database.

The architecture should look approximately like:

```text
content files
    ↓
Python loader/parser
    ↓
normalized internal content models
    ↓
indexing / grouping / statistics
    ↓
Jinja rendering
    ↓
public/
    ↓
GitHub Pages
```

Keep the following layers separate:

1. content parsing
2. data models
3. taxonomy / grouping
4. statistics
5. URL generation
6. template rendering
7. CLI
8. validation
9. filesystem operations

Avoid putting all logic into one large `build.py`.

---

# 3. Desired repository structure

Create a structure approximately like:

```text
field-notes/
├── content/
│   ├── clouds/
│   ├── birds/
│   ├── cats/
│   ├── making/
│   └── curiosities/
│
├── journal/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── parser.py
│   ├── loader.py
│   ├── taxonomy.py
│   ├── stats.py
│   ├── urls.py
│   ├── renderer.py
│   ├── builder.py
│   ├── validation.py
│   ├── media.py
│   └── utils.py
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── observe.html
│   ├── cloud_index.html
│   ├── cloud_genus.html
│   ├── bird_index.html
│   ├── bird_species.html
│   ├── cats.html
│   ├── cat_detail.html
│   ├── making.html
│   ├── project.html
│   ├── curiosities.html
│   ├── journal.html
│   ├── year.html
│   ├── index.html
│   ├── entry.html
│   ├── 404.html
│   └── partials/
│       ├── header.html
│       ├── footer.html
│       ├── metadata.html
│       ├── photo_grid.html
│       ├── recent_entries.html
│       └── stats.html
│
├── static/
│   ├── css/
│   │   ├── variables.css
│   │   ├── base.css
│   │   ├── layout.css
│   │   ├── typography.css
│   │   ├── gallery.css
│   │   └── responsive.css
│   └── js/
│       └── main.js
│
├── public/
├── tests/
│   ├── test_parser.py
│   ├── test_loader.py
│   ├── test_validation.py
│   ├── test_urls.py
│   └── test_stats.py
│
├── scripts/
├── config.yaml
├── journal.py
├── build.py
├── requirements.txt
├── .gitignore
├── README.md
└── .github/
    └── workflows/
        └── pages.yml
```

This exact structure is not mandatory, but preserve the separation of responsibilities.

---

# 4. Content storage format

Each content item should live in its own directory.

Example:

```text
content/clouds/2026-08-31-altocumulus-before-sunset/
├── entry.md
├── 01.jpg
├── 02.jpg
└── 03.jpg
```

Each `entry.md` should use YAML frontmatter plus Markdown body content.

Example:

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
cloud_variety:
supplementary_features: []
optical_phenomena: []

identification: tentative
confidence: 4

cover: 02.jpg
favorite: false

tags:
  - clouds
  - sunset
  - altocumulus
---

A broad field of rounded cloudlets appeared before sunset.

I initially thought they might be cirrocumulus, but the elements
appeared larger and lower in the sky.
```

The body after the frontmatter should be rendered as Markdown.

---

# 5. Permanent IDs

Every content item must have a permanent ID.

Examples:

```text
obs-000001
obs-000002
cat-000001
proj-000001
cur-000001
```

Do not derive permanent identity from the title or filename.

Titles, taxonomy, and slugs may change.

IDs should remain stable.

Implement ID generation in one centralized place.

The CLI should scan existing content to find the next available sequence number.

Never reuse deleted IDs automatically.

---

# 6. Content models

Create typed Python models using `dataclasses`.

Prefer dataclasses over a heavy validation library.

There should be a common base model, such as:

```python
ContentEntry
```

with common fields:

```text
id
title
date
type
category
slug
source_path
body_markdown
body_html
tags
cover
images
favorite
```

Then category-specific metadata may either use subclasses or typed metadata objects.

Avoid building an overly complicated inheritance hierarchy.

---

# 7. Common metadata

Support common fields such as:

```yaml
id:
title:
date:
type:
category:
location:
cover:
favorite:
tags:
status:
```

Optional metadata should remain optional.

Unknown metadata should not crash the build.

Preserve raw frontmatter where useful so the system remains extensible.

---

# 8. Cloud observations

Cloud content should support:

```yaml
type: observation
category: clouds

cloud_genus:
cloud_species:
cloud_variety:

supplementary_features:
optical_phenomena:

identification:
confidence:

location:
```

`identification` should support values such as:

```text
unknown
tentative
self-identified
confirmed
```

Do not enforce a strict cloud taxonomy database yet.

However, create a centralized taxonomy configuration file or Python structure for the major cloud genera and altitude groups.

Initial taxonomy:

```text
High
- Cirrus
- Cirrostratus
- Cirrocumulus

Middle
- Altocumulus
- Altostratus
- Nimbostratus

Low
- Stratus
- Stratocumulus

Vertical Development
- Cumulus
- Cumulonimbus
```

Taxonomy should be configurable rather than hard-coded inside templates.

---

# 9. Bird observations

Bird content should support:

```yaml
type: observation
category: birds

common_name:
scientific_name:

identification:
confidence:

count:
location:
```

Do not require scientific name.

Beginner-friendly entries may have:

```yaml
common_name:
identification: unknown
```

Unknown observations should still build correctly.

Species pages should only be generated for entries with an identified species/common name.

---

# 10. Cat content

Support two broad relationships:

```yaml
relationship: mine
```

and:

```yaml
relationship: encounter
```

Possible metadata:

```yaml
type: cat
category: cats

cat_name:
relationship:
location:
```

Multiple entries may refer to the same cat.

Provide a stable cat slug based on `cat_name` when present.

Do not treat every cat photo as a unique cat.

---

# 11. Making / project content

Projects are not observations.

Support:

```yaml
type: project
category: making

craft:
status:
started:
completed:

materials:
```

Possible statuses:

```text
idea
planned
in-progress
paused
completed
abandoned
```

Project directories may contain multiple images.

Example:

```text
content/making/wildflower-hoop/
├── entry.md
├── 01-start.jpg
├── 02-progress.jpg
├── 03-progress.jpg
└── finished.jpg
```

The project page should display these in filename order unless explicit image ordering is later added.

---

# 12. Curiosities

Curiosities must be deliberately flexible.

Required minimum fields:

```yaml
id:
title:
date:
type: curiosity
category: curiosities
```

Everything else should be optional.

Do not require subcategories.

This category exists specifically so that new interests can be archived without changing the site architecture first.

---

# 13. Image discovery

For each content directory:

1. locate `entry.md`
2. find supported image files
3. exclude hidden files
4. sort images predictably
5. validate `cover`
6. expose image metadata to templates

Supported extensions:

```text
.jpg
.jpeg
.png
.webp
```

Case-insensitive.

If `cover` is omitted:

* use the first available image as the cover
* if there are no images, render the entry without an image

Do not fail the entire build because an entry lacks photographs.

---

# 14. Media paths

Generated content should copy or mirror source images into the static output.

Avoid linking generated HTML directly to paths inside `content/`.

Use a predictable structure such as:

```text
public/media/<entry-id>/<filename>
```

Example:

```text
public/media/obs-000001/01.jpg
```

Centralize media URL generation.

---

# 15. Output directory

The generated site lives entirely in:

```text
public/
```

The build process may safely remove generated contents from `public/`, but must never modify:

```text
content/
templates/
static/
```

Implement safety checks before recursively deleting anything.

Do not use dangerous generic deletion code.

Confirm that the target path resolves to the repository's configured output directory before clearing it.

---

# 16. Homepage

The homepage is not a photo feed.

It should function as the high-level index to the collection.

Desired structure:

```text
RAMANI

Field notes, photographs, and things made.

────────────────────────────────────────

THE COLLECTION

91                24
cloud sightings   bird species

412               9
cat photographs   projects made

────────────────────────────────────────

EXPLORE

CLOUD ATLAS                         91 →
A growing catalogue of clouds I've observed.

BIRD NOTEBOOK                       24 →
Species I'm learning to recognize.

CATS                                   →
My cats and cats encountered.

MAKING                               9 →
Embroidery and other small projects.

CURIOSITIES                         18 →
Things that don't belong anywhere else.

────────────────────────────────────────

RECENTLY ADDED

29 AUG 2026    Altocumulus Before Sunset
27 AUG 2026    Miso at the Window
24 AUG 2026    California Scrub-Jay
19 AUG 2026    Wildflower Hoop
```

All numbers must be generated from actual source content.

---

# 17. Homepage statistics

At minimum calculate:

```text
cloud observation count
unique cloud genera
unique cloud species
bird observation count
unique bird species
cat entry count
unique named cats
project count
completed project count
curiosity count
total entry count
```

Keep statistics logic outside templates.

Templates should receive already-computed values.

---

# 18. Main navigation

Use:

```text
Home
Observe
Cats
Make
Journal
Index
About
```

Do not add dropdown navigation initially.

---

# 19. Observe page

Create:

```text
/observe/
```

This page should introduce:

```text
Cloud Atlas
Bird Notebook
Curiosities
```

and show basic counts for each.

---

# 20. Cloud Atlas

Create:

```text
/observe/clouds/
```

Display automatically computed statistics:

```text
total sightings
identified sightings
unidentified sightings
number of genera observed
number of species observed
```

Then group genera by taxonomy.

Example:

```text
HIGH CLOUDS

Cirrus                     12
Cirrostratus                4
Cirrocumulus                7

MIDDLE CLOUDS

Altocumulus                21
Altostratus                 6
Nimbostratus                2

LOW CLOUDS

Stratus                     8
Stratocumulus              17

VERTICAL DEVELOPMENT

Cumulus                    24
Cumulonimbus                3
```

Hide genera with zero observations by default.

Allow a future config option to show them.

---

# 21. Cloud genus pages

Automatically generate a page for each observed genus.

Example:

```text
/observe/clouds/altocumulus/
```

Page content:

```text
ALTOCUMULUS

21 sightings

FIRST RECORDED
May 14, 2026

MOST RECENT
August 29, 2026

SPECIES OBSERVED

stratiformis      8
lenticularis      2
castellanus       1
unclassified     10
```

Then render observation images in a clean grid.

Each grid item should show:

* image
* date
* species if known
* location if present

Clicking it opens the permanent entry URL.

---

# 22. Bird Notebook

Create:

```text
/observe/birds/
```

Display:

```text
total observations
unique species
confirmed IDs
tentative IDs
unknown IDs
```

Then list identified species alphabetically.

Example:

```text
California Scrub-Jay          7 sightings
Dark-eyed Junco               4 sightings
House Finch                   11 sightings
```

Also include an "Unidentified" section if there are unknown bird observations.

---

# 23. Bird species pages

Generate:

```text
/observe/birds/california-scrub-jay/
```

Display:

```text
common name
scientific name if available
observation count
first sighting
most recent sighting
gallery
```

Do not create pages for blank species names.

---

# 24. Cats page

Create:

```text
/cats/
```

Separate:

```text
MY CATS

ENCOUNTERS
```

Named cats should be grouped.

Display counts where meaningful.

If multiple entries have:

```yaml
cat_name: Miso
```

generate:

```text
/cats/miso/
```

The individual page should combine all entries/photos relating to that cat.

---

# 25. Making page

Create:

```text
/make/
```

Group projects by craft.

Example:

```text
EMBROIDERY

Wildflower Hoop
Pine Tree Study
Constellation Sampler
```

Automatically generate craft landing pages such as:

```text
/make/embroidery/
```

and project detail pages.

---

# 26. Journal page

Create:

```text
/journal/
```

This should be a chronological index of all content, regardless of category.

Group by:

```text
year
month
```

Example:

```text
AUGUST 2026

29    Altocumulus Before Sunset      Clouds
27    Miso at the Window             Cats
24    California Scrub-Jay           Birds
19    Wildflower Hoop                Making
```

Use semantic HTML.

---

# 27. Year archive pages

Generate one page per year:

```text
/journal/2026/
```

Show all entries from that year grouped by month.

Also calculate year-level summary statistics where convenient.

---

# 28. Alphabetical Index

Create:

```text
/index/
```

Treat this like the index in the back of a natural-history book.

Automatically include useful concepts such as:

* cloud genera
* bird species
* named cats
* craft types
* major categories

Example:

```text
A

Altocumulus
21 observations

B

Birds
24 species

C

California Scrub-Jay
7 observations

Cirrus
12 observations

Clouds
91 observations
```

Do not include every tag automatically.

Keep the index useful rather than exhaustive.

---

# 29. Permanent entry pages

Each content item should have a stable entry page:

```text
/entry/<id>/
```

Example:

```text
/entry/obs-000001/
```

The entry page should display:

* title
* category
* date
* metadata
* gallery
* rendered Markdown body
* tags
* links back to relevant category/subcategory

If taxonomy or title changes later, this URL remains stable.

---

# 30. URL handling

Centralize slug creation and URL creation.

Create helper functions such as:

```python
slugify()
entry_url()
cloud_genus_url()
bird_species_url()
cat_url()
craft_url()
year_url()
```

Do not manually concatenate URLs throughout templates.

Support GitHub Pages project-site deployment, where the site may be hosted at:

```text
https://username.github.io/repository-name/
```

This means internal URLs must support a configurable `base_url`.

Example config:

```yaml
site:
  title: Ramani
  subtitle: Field notes, photographs, and things made.
  base_url: /field-notes
```

Also support:

```yaml
base_url: ""
```

for root-domain hosting.

Never assume the site is deployed at `/`.

---

# 31. Config file

Create:

```text
config.yaml
```

Example:

```yaml
site:
  title: Ramani
  subtitle: Field notes, photographs, and things made.
  base_url: ""
  recent_entries: 5

build:
  output_dir: public

clouds:
  show_unobserved_genera: false
```

Keep deployment-specific values configurable.

---

# 32. CLI

Create a top-level command:

```bash
python journal.py
```

Use Python `argparse`.

Support:

```bash
python journal.py add
python journal.py add cloud
python journal.py add bird
python journal.py add cat
python journal.py add project
python journal.py add curiosity

python journal.py build
python journal.py preview
python journal.py validate
python journal.py stats
```

---

# 33. `journal add cloud`

Interactive prompt example:

```text
Image path:
Additional image paths:
Title:
Date [today]:
Location:
Cloud genus:
Cloud species:
Cloud variety:
Identification:
Confidence [1-5]:
Favorite [y/N]:
Tags:
Notes:
```

Optional fields should allow blank input.

The tool should:

1. validate supplied image paths
2. assign the next permanent ID
3. create a normalized slug
4. create the destination content directory
5. copy image files
6. rename collisions safely
7. create `entry.md`
8. write valid YAML frontmatter
9. write the notes into the Markdown body
10. print the created path

Do not commit to Git automatically.

---

# 34. `journal add bird`

Ask:

```text
Image path:
Title:
Date:
Location:
Common name:
Scientific name:
Identification:
Confidence:
Count:
Tags:
Notes:
```

All taxonomic fields may be blank.

---

# 35. `journal add cat`

Ask:

```text
Image path:
Title:
Date:
Cat name:
Relationship [mine/encounter]:
Location:
Tags:
Notes:
```

---

# 36. `journal add project`

Ask:

```text
Project title:
Craft:
Status:
Started:
Completed:
Cover image:
Additional image paths:
Materials:
Tags:
Notes:
```

Generate a `proj-*` ID.

---

# 37. `journal add curiosity`

Ask only a minimal set:

```text
Image path:
Title:
Date:
Location:
Tags:
Notes:
```

Avoid making Curiosities cumbersome.

---

# 38. Noninteractive support

Design the CLI so that interactive prompting is isolated from the core creation functions.

For example:

```python
create_cloud_entry(...)
create_bird_entry(...)
```

should accept normal Python arguments.

This allows a future GUI or automation tool to reuse the same entry-creation logic.

---

# 39. Preview server

Implement:

```bash
python journal.py preview
```

Behavior:

1. run a build first
2. serve `public/` locally using Python's built-in HTTP server
3. default to port 8000
4. print the local URL

Support:

```bash
python journal.py preview --port 8080
```

No Flask dependency.

---

# 40. Validation command

Implement:

```bash
python journal.py validate
```

Validation should check:

* duplicate IDs
* malformed YAML
* invalid dates
* missing IDs
* missing titles
* missing category
* missing referenced cover image
* duplicate permanent IDs
* invalid confidence values
* unsupported category values
* nonexistent media references

Warnings versus errors should be distinct.

Unknown metadata fields should normally be warnings at most, not errors.

Return a non-zero process exit code when validation errors exist.

---

# 41. Build behavior

`python journal.py build` should:

1. load config
2. scan content recursively
3. parse all entries
4. validate
5. stop on serious validation errors
6. normalize models
7. copy static assets
8. copy media
9. calculate statistics
10. build indexes
11. render all pages
12. write `public/`
13. print a concise build summary

Example:

```text
Loaded 137 entries

Cloud observations: 91
Bird observations: 24
Cat entries: 8
Projects: 9
Curiosities: 5

Generated 48 pages
Copied 212 images

Build complete: public/
```

---

# 42. Build determinism

The same source content should produce the same output.

Sort consistently.

Do not depend on filesystem traversal order.

Explicitly sort:

* entries by date
* species alphabetically
* genera by configured taxonomy order
* images by filename
* index entries alphabetically

---

# 43. Dates

Use Python date objects internally.

Accept ISO dates:

```text
YYYY-MM-DD
```

Render human-readable dates in templates:

```text
August 31, 2026
```

Do not perform locale-dependent parsing.

---

# 44. Markdown rendering

Use a well-maintained Python Markdown package.

Support normal Markdown:

* paragraphs
* emphasis
* links
* lists
* blockquotes
* headings

Do not enable arbitrary raw HTML unless clearly documented.

Prefer safe/default behavior.

---

# 45. HTML

Use semantic HTML5.

Prefer:

```text
header
nav
main
section
article
figure
figcaption
time
footer
```

Use heading hierarchy correctly.

Avoid div-heavy markup.

---

# 46. Accessibility

Implement basic accessibility from the beginning.

Requirements:

* keyboard-accessible navigation
* meaningful heading structure
* visible focus states
* sufficient contrast
* responsive text
* `alt` support for images
* no hover-only critical information

Allow image metadata to contain optional:

```yaml
image_alt:
```

If absent, derive a conservative alt description from the entry title rather than leaving informative images inaccessible.

---

# 47. CSS architecture

Use plain CSS.

Create reusable variables:

```css
:root {
  --color-bg: ...;
  --color-text: ...;
  --color-muted: ...;
  --color-border: ...;
  --color-link: ...;

  --font-body: ...;
  --font-heading: ...;
  --font-mono: ...;

  --space-xs: ...;
  --space-sm: ...;
  --space-md: ...;
  --space-lg: ...;
  --space-xl: ...;

  --content-width: ...;
  --wide-width: ...;
}
```

Use system fonts initially unless a local/web font is explicitly justified.

Do not require third-party font hosting.

---

# 48. Design direction

The visual language should resemble:

* field notebook
* museum catalogue
* natural-history archive
* personal photographic collection
* understated editorial publication

It should not resemble:

* startup landing page
* SaaS dashboard
* social-media app
* generic card-based portfolio

Use:

* whitespace
* editorial typography
* fine rules
* restrained colors
* image grids
* small labels
* strong hierarchy
* modest statistics

Avoid:

* rounded cards everywhere
* shadows
* gradients
* huge hero blocks
* decorative animations
* pill buttons
* glassmorphism
* oversized UI controls

---

# 49. Homepage visual structure

Approximate visual composition:

```text
RAMANI
Field notes, photographs, and things made.

──────────────────────────────────────────

THE COLLECTION

91                     24
CLOUD SIGHTINGS        BIRD SPECIES

412                    9
CAT PHOTOGRAPHS        PROJECTS MADE

──────────────────────────────────────────

EXPLORE

CLOUD ATLAS                               91 →
A growing catalogue of clouds I've observed.

BIRD NOTEBOOK                             24 →
Species I'm learning to recognize.

CATS                                         →
My cats and cats encountered.

MAKING                                     9 →
Embroidery and other projects.

CURIOSITIES                               18 →
Things that don't belong anywhere else.

──────────────────────────────────────────

RECENTLY ADDED

29 AUG 2026    Altocumulus Before Sunset
27 AUG 2026    Miso at the Window
24 AUG 2026    California Scrub-Jay
19 AUG 2026    Wildflower Hoop
```

Do not duplicate this literally if a better semantic implementation exists, but preserve the restrained editorial feel.

---

# 50. Responsive layout

Support:

* desktop
* tablet
* phone

On desktop:

* content width approximately 900–1100 px
* stats may use multiple columns
* galleries may use 3–4 columns

On smaller screens:

* statistics stack cleanly
* galleries reduce columns
* navigation wraps or simplifies
* no horizontal scrolling

Use CSS Grid and Flexbox.

No JS layout framework.

---

# 51. Photo grids

Use CSS Grid.

Prefer natural editorial spacing.

Example behavior:

```text
desktop: 3 columns
tablet: 2 columns
phone: 1 or 2 columns depending on width
```

Use `object-fit` carefully.

Do not force all photography into overly aggressive fixed crops.

Provide a reasonable consistent gallery treatment.

---

# 52. Metadata display

Metadata on entry pages should be visually secondary but clearly readable.

Example:

```text
DATE          August 31, 2026
LOCATION      Berkeley, California
GENUS         Altocumulus
SPECIES       stratiformis
ID STATUS     Tentative
CONFIDENCE    4 / 5
```

Use definition lists where appropriate.

---

# 53. No manual derived data

Never require the user to manually maintain:

```text
number of sightings
first observation date
latest observation date
species counts
genus counts
year totals
category totals
```

All such values must be derived from content.

---

# 54. Sample content

Create representative sample entries.

At minimum:

```text
2 cloud entries
  - altocumulus
  - cirrus

2 bird entries
  - one identified
  - one unidentified

2 cat entries
  - one personal cat
  - one encounter

1 embroidery project

1 curiosity
```

Use small generated placeholder SVG or local placeholder files if images are needed.

Do not rely on external image URLs.

Clearly mark sample entries so they can be deleted later.

---

# 55. Tests

Use `pytest`.

At minimum test:

## Parsing

* valid frontmatter
* malformed frontmatter
* Markdown body extraction

## IDs

* next ID calculation
* duplicate detection

## URLs

* slugification
* GitHub Pages base path
* entry URLs
* category URLs

## Statistics

* cloud counts
* unique species
* first/latest date
* category totals

## Validation

* bad date
* duplicate ID
* missing cover
* unknown optional metadata

Tests should operate on temporary directories rather than production content.

---

# 56. Logging / output

CLI output should be concise and readable.

Use Python's built-in `logging` module or simple structured console output.

Do not introduce a large logging dependency.

Support:

```bash
python journal.py build --verbose
```

if convenient.

---

# 57. Requirements

Keep dependencies minimal.

Expected approximate dependencies:

```text
Jinja2
PyYAML
Markdown
pytest
```

If you add another dependency, document why.

---

# 58. GitHub Pages deployment

Create a GitHub Actions workflow that:

1. checks out the repository
2. installs Python
3. installs dependencies
4. runs tests
5. validates content
6. builds the site
7. uploads `public/`
8. deploys to GitHub Pages

Use the modern GitHub Pages Actions deployment approach.

Do not require generated `public/` files to be committed unless necessary.

The README should explain how to configure GitHub Pages under repository settings.

Support project URLs such as:

```text
https://USERNAME.github.io/REPOSITORY/
```

through the `base_url` setting.

---

# 59. Local workflow

The intended everyday workflow should be:

```bash
python journal.py add cloud
python journal.py preview
```

Then when satisfied:

```bash
git add .
git commit -m "Add altocumulus observation"
git push
```

GitHub Actions should deploy automatically.

The user should not normally need to manually edit generated HTML.

---

# 60. README

Write a practical README.

Include:

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Add content

```bash
python journal.py add cloud
```

## Validate

```bash
python journal.py validate
```

## Build

```bash
python journal.py build
```

## Preview

```bash
python journal.py preview
```

## Test

```bash
pytest
```

## Deploy

Explain GitHub Pages / GitHub Actions configuration.

Also document:

* project structure
* content format
* frontmatter fields
* permanent IDs
* adding a new category
* modifying templates
* modifying CSS
* changing the site title
* configuring `base_url`
* removing sample content

---

# 61. Code-quality expectations

Prefer:

* small functions
* clear naming
* type hints
* dataclasses
* `pathlib.Path`
* explicit data transformations
* docstrings on non-obvious functions
* minimal global state

Avoid:

* clever abstractions
* complex metaprogramming
* hidden filesystem behavior
* unnecessary classes
* dependency injection frameworks
* generic abstractions before they are needed

This is a personal project that should remain understandable after years of inactivity.

Optimize for readability over abstraction.

---

# 62. Extensibility requirements

Design the system so these features can later be added without a major rewrite:

* EXIF extraction
* image thumbnail generation
* automatic image resizing
* weather data
* geographic maps
* geographic coordinates
* bird taxonomy
* full cloud taxonomy
* tags
* search
* favorites page
* JSON export
* RSS
* Instagram links
* import tools
* local GUI
* richer statistics

Do not implement all of them now.

Just avoid architectural decisions that make them difficult.

---

# 63. Future machine-readable output

As part of the build architecture, make it straightforward to later emit:

```text
public/data/entries.json
public/data/stats.json
```

Do not necessarily expose these publicly in the UI yet.

If simple to implement cleanly now, generate them.

This would allow future JavaScript or external tools to consume the site's archive without reparsing HTML.

---

# 64. Important design decision

Keep content independent of presentation.

The source content should remain useful even if the entire site generator is replaced in five years.

A valid entry should fundamentally be:

```text
directory
├── entry.md
└── photographs
```

Avoid embedding Jinja-specific, CSS-specific, or framework-specific details into content files.

---

# 65. Error handling

Errors should identify the exact problematic file.

For example:

```text
ERROR content/clouds/2026-08-31-altocumulus/entry.md
Invalid date: "08/31/26"
Expected YYYY-MM-DD.
```

or:

```text
ERROR duplicate ID obs-000014

- content/clouds/foo/entry.md
- content/clouds/bar/entry.md
```

Do not output generic tracebacks for ordinary content mistakes.

Unexpected internal failures may still show tracebacks in verbose/debug mode.

---

# 66. Build metadata

Optionally generate a simple build metadata structure containing:

```text
entry count
page count
media count
build timestamp
```

Do not display the build timestamp prominently on the site.

Avoid making generated output nondeterministic unnecessarily.

---

# 67. HTML title and metadata

Generate reasonable `<title>` values.

Examples:

```text
Ramani
Cloud Atlas — Ramani
Altocumulus — Cloud Atlas — Ramani
California Scrub-Jay — Bird Notebook — Ramani
Wildflower Hoop — Making — Ramani
```

Add basic:

```text
description
viewport
canonical URL support where possible
```

Do not add an SEO framework.

---

# 68. 404 page

Generate:

```text
404.html
```

Keep it visually consistent.

Provide links back to:

```text
Home
Index
Journal
```

---

# 69. Development strategy

Implement incrementally in this order:

Implementation status is maintained separately in `PLAN_PROGRESS.md` so this
document can remain the stable specification.

## Phase 1

Project skeleton and configuration.

## Phase 2

Content parser and models.

## Phase 3

Validation and loading.

## Phase 4

URL generation and base path handling.

## Phase 5

Basic renderer and homepage.

## Phase 6

Cloud Atlas.

## Phase 7

Bird Notebook.

## Phase 8

Cats / Making / Curiosities.

## Phase 9

Journal and alphabetical index.

## Phase 10

CLI creation workflow.

## Phase 11

Styling and responsive design.

## Phase 12

Tests.

## Phase 13

GitHub Pages workflow.

## Phase 14

README and cleanup.

Do not attempt to solve everything in one giant file.

---

# 70. Before finishing

Run:

```bash
pytest
python journal.py validate
python journal.py build
```

Then inspect the generated structure.

Fix errors before considering the implementation complete.

---

# 71. Final deliverable

At the end of your work, provide a concise implementation summary containing:

1. final repository tree
2. dependencies used
3. important architectural decisions
4. how IDs work
5. how content is parsed
6. how derived statistics work
7. how URLs work
8. how GitHub Pages base paths are handled
9. commands for setup
10. command to add a cloud observation
11. command to preview locally
12. command to build
13. command to validate
14. command to run tests
15. which files control the site's visual design
16. which files to edit when adding a future category

Also point out any intentionally deferred features.

Do not replace the requested simple architecture with a different framework unless there is a concrete technical blocker. If there is a blocker, explain it before changing the stack.
