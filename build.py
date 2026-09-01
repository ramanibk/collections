"""Backward-compatible shortcut for ``python journal.py build``."""

from journal.cli import main as journal_main


def main() -> int:
    return journal_main(["build"])


if __name__ == "__main__":
    raise SystemExit(main())
