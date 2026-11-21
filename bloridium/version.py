"""Single source of truth for the Bloridium version.

Used by pyproject.toml (dynamic version), the CLI (--version), the web app
(UI title, report.json, MANIFEST.md) and the matcher labels. Kept free of
imports so the web app can read it without loading the package.
"""

__version__ = "0.5.2"  # 2026-11-21: A2 Filter-2-Fix (parallel FilterLink=Independent
# + Filter2Type, Resonanz-Kennlinie raw 113 -> 1.0, Filter-Drive als Insert mit
# DriveDryWet=1.0); A1/A3/A4 aus 0.5.1
