"""Single source of truth for the Bloridium version.

Used by pyproject.toml (dynamic version), the CLI (--version), the web app
(UI title, report.json, MANIFEST.md) and the matcher labels. Kept free of
imports so the web app can read it without loading the package.
"""

__version__ = "0.5.3"  # 2026-11-21: A7a LFO-Fade -> LfoNAttack/LfoNDecay
# (bipolar raw 64=0); davor A1/A2/A3/A4 in 0.5.1/0.5.2
