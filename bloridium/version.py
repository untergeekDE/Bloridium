"""Single source of truth for the Bloridium version.

Used by pyproject.toml (dynamic version), the CLI (--version), the web app
(UI title, report.json, MANIFEST.md) and the matcher labels. Kept free of
imports so the web app can read it without loading the package.
"""

__version__ = "0.5.0"  # 2026-11-21: Mapping-Update (PPG->24dB LP, Filter-Drive->FX1,
# LFOx*MW->Matrix Ctrl, Env-Curves Lin, PWM/FM/Filter-Mod -> Matrix 21+, Oktav-Clamp
# + Constant-Shift, .mid-Upload); Webapp-UI ohne "mapped"-Spalte
