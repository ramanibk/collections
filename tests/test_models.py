from pathlib import Path

from journal.parser import parse_entry_text


def test_permanent_entry_url_uses_id() -> None:
    text = """---
id: cur-000007
title: A Mutable Title
date: 2026-09-01
type: curiosity
category: curiosities
---
Body.
"""

    entry = parse_entry_text(text, Path("entry.md"))

    assert entry.url == "/entry/cur-000007/"
