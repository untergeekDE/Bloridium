#!/usr/bin/env python3
"""Schritt 3 (qpat-Weg): Blofeld-Sound als .qpat fuer den Iridium erzeugen.

Wrapper ueber bloridium.workflow (argv/Exit/Stdout unveraendert).

  1. Blofeld-SNDD lesen (Location, z.B. A043)
  2. Template-.qpat laden (Waveform-Template) + Blofeld->qpat-Mapping anwenden
  3. <name>.qpat nach transfer/ schreiben

Danach: transfer/ auf USB-Stick kopieren -> am Iridium Load>Actions>Import ->
Sound laden -> A/B messen (scripts/step4_measure_ab.py).

Aufruf:  python3 scripts/step3_transfer_qpat.py [A043]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import midi, qpat_map, workflow

OUT = workflow.TRANSFER


def main() -> int:
    loc = sys.argv[1] if len(sys.argv) > 1 else "A043"
    synth = midi.connect("blofeld")
    try:
        parsed = workflow.read_sound(synth, loc)
    finally:
        synth.close()
    print(f"Blofeld-Sound: {parsed['name']!r} ({loc})")

    overrides, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    print(f"{len(overrides)} qpat-Parameter gemappt, {len(unmapped)} unmapped")

    out_path, _, _ = workflow.convert_parsed(parsed, loc, OUT)
    print(f"geschrieben: {out_path} ({out_path.stat().st_size} Bytes)")

    # Report
    print("\n--- gemappte Parameter (Auszug) ---")
    for k in sorted(overrides)[:40]:
        v, d = overrides[k]
        print(f"  {k:28s} = {v:.4f}  {d}")
    print(f"\n--- unmapped ({len(unmapped)}) ---")
    for u in unmapped[:25]:
        print("  ", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
