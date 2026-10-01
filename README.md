# Collections

A file-backed personal site for photographs and notes. Markdown content is built
into a static site and deployed with GitHub Pages.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Commands

```bash
python journal.py add photo
python journal.py add note
python journal.py add essay
python journal.py validate
python journal.py build
python journal.py preview
python -m pytest
```

Source content lives in `content/`; generated files in `public/` should not be
edited directly.

Photographs submitted through the private Google Form are imported every 30
minutes. See [`integrations/google-form/README.md`](integrations/google-form/README.md)
for setup details.
