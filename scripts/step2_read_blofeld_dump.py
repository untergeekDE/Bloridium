#!/usr/bin/env python3
"""Schritt 2a: Blofeld Sound-Dump (SNDR -> SNDD) ueber USB auslesen und speichern.

Request:  F0 3E 13 00 00 BB NN F7     (SNDR mit Location, siehe Blofeld_sysex_v1_04.pdf)
Reply:    F0 3E 13 00 10 BB NN <SDATA 383 B> CHK F7   (SNDD)

Locations (BB NN):  00 00..00 7F = A001..A128, 01.. = B..., 7F 00 = Edit-Puffer
                    (Default ohne BB NN = Edit-Puffer)

Aufruf:  python3 scripts/step2_read_blofeld_dump.py [A043|edit]
         Default: edit (Edit-Puffer)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import blofeld_dump as bd
from bloridium import midi, waldorf

DUMPS = Path(__file__).resolve().parent.parent / "dumps"


def parse_location(arg: str) -> tuple[int, int]:
    """'A043' -> (0x00, 0x2A); 'edit' -> (0x7F, 0x00)."""
    if arg.lower() in ("edit", "puffer", ""):
        return 0x7F, 0x00
    arg = arg.strip().upper()
    bank = ord(arg[0]) - ord("A")
    num = int(arg[1:]) - 1
    if not (0 <= bank <= 0x19 and 0 <= num <= 0x7F):
        raise ValueError(f"ungueltige Location: {arg!r} (z.B. A001..Z128)")
    return bank, num


def read_sndd(synth: midi.Synth, bb: int, nn: int, wait: float = 4.0):
    """Sendet SNDR fuer Location (bb, nn) und gibt die rohe SNDD-Nachricht (mit F0/F7) zurueck."""
    synth.send_sysex(bd.build_sndr(bb=bb, nn=nn))
    for m in synth.receive(timeout=wait):
        if m.type != "sysex":
            continue
        p = waldorf.parse_sysex(m.data)
        if p.get("cmd") == waldorf.CMD["sound_dump"]:
            return bytes([0xF0] + list(m.data) + [0xF7])
    return None


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "edit"
    bb, nn = parse_location(arg)
    DUMPS.mkdir(exist_ok=True)
    synth = midi.connect("blofeld")
    print(f"Port: {synth.out_port_name}, Kanal (0-basiert): {synth.channel}, Location: BB=0x{bb:02X} NN=0x{nn:02X} ({arg})")
    try:
        raw = read_sndd(synth, bb, nn)
        if raw is None:
            print("KEIN SNDD empfangen!")
            return 1
        r = bd.parse_sndd(raw)
        tag = arg.replace(" ", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bin_path = DUMPS / f"blofeld_sndd_{tag}_{ts}.bin"
        hex_path = DUMPS / f"blofeld_sndd_{tag}_{ts}.hex"
        bin_path.write_bytes(raw)
        hex_path.write_text(raw.hex(" ") + "\n")
        print(f"SNDD gespeichert: {bin_path.name} ({len(raw)} Bytes inkl. F0/F7)")
        print(f"  Name={r['name']!r}  CHK ok={r['chk_ok']}  Hex: {hex_path.name}")
        return 0
    finally:
        synth.close()


if __name__ == "__main__":
    sys.exit(main())
