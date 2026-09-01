# Plan Progress

This document tracks implementation progress against the phases in
[`plan.md`](plan.md). The specification remains the source of truth for what
each phase requires; this file is the source of truth for completion status.

Last updated: 2026-09-01

## Status summary

- Complete: 14 of 14 phases
- In progress: 0 of 14 phases
- Not started: 0 of 14 phases
- Current next phase: routine content authoring and maintenance

Status meanings:

- **Complete** — the phase's scoped implementation exists and its relevant
  checks pass.
- **In progress** — useful pieces exist, but the full phase is not complete.
- **Not started** — no phase-level implementation has been completed.

## Phase tracker

| Phase | Scope | Status | What is already done | Completion evidence / remaining work |
|---:|---|---|---|---|
| 1 | Project skeleton and configuration | **Complete** | Repository directories, `journal` package, `config.yaml`, typed config loader, dependency list, test configuration, and ignore rules | Configuration tests pass; project modules compile |
| 2 | Content parser and models | **Complete** | Typed common/category metadata models, YAML frontmatter parsing, Markdown rendering, ISO date normalization, slugging, image discovery, raw metadata preservation, and centralized cloud taxonomy | Parser/model tests pass; malformed input and category-specific cases are covered |
| 3 | Validation and loading | **Complete** | Dedicated deterministic loader and structured validation report; aggregate parse errors; duplicate-ID, category, cover/media, confidence, and unknown-field checks; compatibility adapter for the prototype builder | Loader and validation tests pass; errors and warnings retain exact source paths |
| 4 | URL generation and base path handling | **Complete** | Central helpers cover home, categories, permanent entries, cloud genera, bird species, cats, crafts, years, static assets, and ID-based media; every helper supports root or GitHub Pages base paths | URL and route-output tests pass for root and `/field-notes` deployment |
| 5 | Basic renderer and homepage | **Complete** | Jinja renderer, safe staged builder, derived homepage statistics, semantic base/home templates, recent entries, static/media copying, `.nojekyll`, and concise build output | Integration tests and the real project build pass; browser check found both stylesheets, correct landmarks, no overflow, and no console errors |
| 6 | Cloud Atlas | **Complete** | Observe landing page; Cloud Atlas summary; configurable taxonomy grouping; observed-genus pages with first/latest dates, species counts, chronological sighting grids, accessible image fallbacks, and links to generated permanent entry pages | Cloud derivation and build integration tests pass; real empty-state build and browser rendering pass without console errors or overflow |
| 7 | Bird Notebook | **Complete** | Bird summary statistics; case-insensitive alphabetical species grouping; identified-species pages with scientific names, observation dates, counts, and galleries; unidentified-observation section; accessible empty states | Bird derivation and build integration tests pass; real empty-state page passes desktop and mobile browser checks without console errors or overflow |
| 8 | Cats / Making / Curiosities | **Complete** | Cats index with exactly three permanent profiles (Gwen, Billy, and Jet), combined entry/photo histories, and encounters; Making index, case-insensitive craft groups, craft pages, and metadata-rich permanent project pages; flexible chronological Curiosities index; category-specific validation | Collection derivation and build integration tests pass; empty states and responsive layouts are browser-verified |
| 9 | Journal and alphabetical index | **Complete** | Site-wide reverse-chronological Journal grouped by year and month; yearly archive pages with entry/category/photo summaries; concise alphabetical index of major categories, observed cloud genera and bird species, fixed cat profiles, and craft types | Archive/index derivation and base-path build tests pass; desktop and mobile browser checks found no overflow or console errors |
| 10 | CLI creation workflow | **Complete** | Reusable creation functions plus `journal.py` commands for interactive add, build, preview, validate, and stats; safe media copying; collision handling; permanent ID high-water marks | CLI and creation tests pass; the real validate and build commands succeed |
| 11 | Styling and responsive design | **Complete** | Six planned CSS modules provide the field-notebook palette, editorial typography, layout, galleries, visible focus treatment, skip link, and desktop/tablet/phone breakpoints | Browser review at 1280 px and 390 px found all assets loaded, correct landmarks, no overflow, and no console errors |
| 12 | Tests | **Complete** | 61 tests cover configuration, parsing, models, loading, validation, permanent IDs, creation, CLI behavior, URLs, statistics, safe builds, all collection pages, responsive asset wiring, and deployment configuration | Full suite passes on the completed implementation |
| 13 | GitHub Pages workflow | **Complete** | Modern two-job Pages workflow installs Python 3.12, tests, validates, builds, uploads `public/`, and deploys with least-privilege job permissions | Workflow structure and current Pages action versions are covered by deployment tests |
| 14 | README and cleanup | **Complete** | Practical setup, authoring, content schema, IDs, configuration, base paths, deployment, customization, and extension documentation; About and 404 pages; legacy facade removed | Final compile, test, validation, build, generated-tree inspection, browser review, and whitespace check pass |

## Verification snapshot

As of 2026-09-01:

```text
61 tests passed
Python compilation passed
git diff --check passed
Real project validation passed (0 errors, 0 warnings)
Real project build passed (13 pages plus 404.html, 0 entries, 0 media)
Homepage, About, and 404 rendering passed at desktop and mobile sizes with all six stylesheets, no console errors, and no overflow
```

The complete `journal.py` command surface is available. `python build.py`
remains as a backward-compatible build shortcut.

## Maintenance rules

Whenever a phase changes:

1. Update its status and the “already done” column.
2. Record specific remaining work instead of marking a partial phase complete.
3. Update the summary counts, next phase, date, and verification snapshot.
4. Add a short dated entry to the activity log below.

## Activity log

- **2026-09-01 — Phases 10–14 completed.** Added reusable entry creation,
  permanent ID high-water marks, interactive CLI commands, preview serving,
  CLI/deployment tests, modular responsive styling, current GitHub Pages
  deployment, complete authoring and maintenance documentation, About and 404
  pages, and final cleanup. Verified 61 tests, clean validation, a deterministic
  real build, and desktop/phone browser rendering without overflow or console
  errors.
- **2026-09-01 — Phases 8–9 completed.** Added craft-grouped Making pages,
  metadata-rich project pages, a flexible Curiosities collection, chronological
  Journal and year archives, and a deliberately concise natural-history-style
  alphabetical index. Added project status/date validation, browser-verified
  the new destinations at desktop and mobile sizes, and increased the test
  total to 49.
- **2026-09-01 — Cats portion of Phase 8 completed.** Added a Cats index with
  exactly three permanent profiles—Gwen, Billy, and Jet—plus combined entry and
  photograph histories and a separate encounter stream. Validation rejects
  other named cats and malformed relationships. Browser-verified the index and
  empty profile states at desktop and mobile sizes and increased the test total
  to 42.
- **2026-09-01 — Phase 7 completed.** Added the Bird Notebook summary,
  alphabetical case-insensitive species grouping, identified-species histories,
  scientific names, galleries, and a separate unidentified-observation area.
  Browser-verified the empty state at desktop and mobile sizes and increased the
  test total to 36.
- **2026-09-01 — Phase 6 completed.** Added the Observe landing page and a
  taxonomy-driven Cloud Atlas with configurable zero-count genera, derived
  identification statistics, genus histories, species counts, sighting grids,
  and working permanent entry pages. Browser-verified the empty state and
  increased the test total to 32.
- **2026-09-01 — Phases 4–5 completed.** Centralized URL generation with full
  base-path support, then implemented a safe staged builder and semantic,
  statistics-driven homepage. Media now uses permanent-ID paths. Added initial
  accessible styling, exercised the real build in a browser, and increased the
  test total to 29.
- **2026-09-01 — Phase 3 completed.** Added deterministic recursive loading and
  structured, aggregate validation with distinct errors and warnings. Covered
  malformed entries, duplicate IDs, unsupported categories, invalid confidence,
  missing cover media, and extensible metadata. Test total increased to 20.
- **2026-09-01 — Phases 1–2 completed.** Established the project/configuration
  foundation and implemented typed content models and parsing. Added 11 passing
  tests. Recorded partial progress for the broader testing and documentation
  phases.
