"""Bloridium CLI – Terminal-Tool Phase 1 (klassische Subcommands).

Subcommands (siehe docs/superpowers/specs/2026-11-08-bloridium-cli-design.md):
status, bank read/import/list/show, convert, ab, qpat info, edit.
"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bloridium",
        description="Blofeld -> Iridium Sound-Transfer (Terminal-Tool, Phase 1)",
    )
    p.add_argument(
        "--db",
        default=None,
        help="Pfad zur SQLite-Bank-DB (Default: $BLORIDIUM_DB oder <repo>/bloridium.db)",
    )
    p.add_argument("--json", action="store_true", help="Ausgabe als JSON (wo unterstuetzt)")
    return p


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
