"""Single source of truth for the Bloridium version.

Used by pyproject.toml (dynamic version), the CLI (--version), the web app
(UI title, report.json, MANIFEST.md) and the matcher labels. Kept free of
imports so the web app can read it without loading the package.
"""

__version__ = "0.6.4"  # 2026-11-22: Poly/Mono allocation, RC/Exp curves, sync mod, sat LP
# Converter code unchanged since 0.5.3 (A1/A2/A3/A4/A7a), before that 0.5.1/0.5.2
