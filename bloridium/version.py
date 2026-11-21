"""Single source of truth for the Bloridium version.

Used by pyproject.toml (dynamic version), the CLI (--version), the web app
(UI title, report.json, MANIFEST.md) and the matcher labels. Kept free of
imports so the web app can read it without loading the package.
"""

__version__ = "0.5.1"  # 2026-11-21: Konverter-Fixes A1/A3/A4 (PWM nur fuer
# Puls-Shapes, Reverb-Mix ueber ReverbGain, Unisono-Bits 4-6 + neutrale Pan/Delay);
# Webapp trennt bewusste "Ignored:"-Hinweise von echten MIDI-Map-Luecken
