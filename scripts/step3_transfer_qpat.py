#!/usr/bin/env python3
"""Step 3 (qpat path): generate a .qpat for the Iridium from a Blofeld sound.

Wrapper around bloridium.workflow (argv/exit/stdout unchanged).

  1. read Blofeld SNDD (location, e.g. A043)
  2. load template .qpat (waveform template) + apply Blofeld->qpat mapping
  3. write <name>.qpat to transfer/

Afterwards: copy transfer/ to a USB stick -> on the Iridium Load>Actions>Import ->
load sound -> A/B measurement (scripts/step4_measure_ab.py).

Usage:  python3 scripts/step3_transfer_qpat.py [A043]
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
    print(f"Blofeld sound: {parsed['name']!r} ({loc})")

    overrides, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    print(f"{len(overrides)} qpat parameters mapped, {len(unmapped)} unmapped")

    out_path, _, _ = workflow.convert_parsed(parsed, loc, OUT)
    print(f"written: {out_path} ({out_path.stat().st_size} bytes)")

    # Report
    print("\n--- mapped parameters (excerpt) ---")
    for k in sorted(overrides)[:40]:
        v, d = overrides[k]
        print(f"  {k:28s} = {v:.4f}  {d}")
    print(f"\n--- unmapped ({len(unmapped)}) ---")
    for u in unmapped[:25]:
        print("  ", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
