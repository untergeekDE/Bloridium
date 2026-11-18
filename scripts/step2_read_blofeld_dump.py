#!/usr/bin/env python3
"""Step 2a: read Blofeld sound dump (SNDR -> SNDD) via USB and save it.

Wrapper around bloridium.workflow (argv/exit/stdout unchanged).

Request:  F0 3E 13 00 00 BB NN F7     (SNDR with location, see Blofeld_sysex_v1_04.pdf)
Reply:    F0 3E 13 00 10 BB NN <SDATA 383 B> CHK F7   (SNDD)

Locations (BB NN):  00 00..00 7F = A001..A128, 01.. = B..., 7F 00 = edit buffer

Usage:  python3 scripts/step2_read_blofeld_dump.py [A043|edit]
         Default: edit (edit buffer)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import blofeld_dump as bd
from bloridium import midi, workflow

DUMPS = workflow.DUMPS


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "edit"
    bb, nn = workflow.parse_location(arg)
    DUMPS.mkdir(exist_ok=True)
    synth = midi.connect("blofeld")
    print(f"Port: {synth.out_port_name}, channel (0-based): {synth.channel}, Location: BB=0x{bb:02X} NN=0x{nn:02X} ({arg})")
    try:
        try:
            parsed = workflow.read_sound(synth, arg)
        except RuntimeError:
            print("NO SNDD received!")
            return 1
        # reconstruct the raw SNDD (checksum is deterministic) -> byte-identical to what was received
        raw = bytes([0xF0]) + bytes(bd.build_sndd(parsed["sdata"], bb=bb, nn=nn)) + bytes([0xF7])
        tag = arg.replace(" ", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bin_path = DUMPS / f"blofeld_sndd_{tag}_{ts}.bin"
        hex_path = DUMPS / f"blofeld_sndd_{tag}_{ts}.hex"
        bin_path.write_bytes(raw)
        hex_path.write_text(raw.hex(" ") + "\n")
        print(f"SNDD saved: {bin_path.name} ({len(raw)} bytes incl. F0/F7)")
        print(f"  Name={parsed['name']!r}  CHK ok={parsed['chk_ok']}  Hex: {hex_path.name}")
        return 0
    finally:
        synth.close()


if __name__ == "__main__":
    sys.exit(main())
