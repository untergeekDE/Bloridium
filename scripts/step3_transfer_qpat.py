#!/usr/bin/env python3
"""Schritt 3 (qpat-Weg): Blofeld-Sound als .qpat fuer den Iridium erzeugen.

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

from bloridium import blofeld_dump as bd
from bloridium import midi, qpat, qpat_map, waldorf

TEMPLATE = Path(__file__).resolve().parent.parent / "docs" / "refs" / "qpat" / "template_waveform.qpat"
OUT = Path(__file__).resolve().parent.parent / "transfer"


def read_blofeld(location: str) -> dict:
    if location.lower() in ("edit", ""):
        bb, nn = 0x7F, 0x00
    else:
        location = location.strip().upper()
        bb, nn = ord(location[0]) - ord("A"), int(location[1:]) - 1
    synth = midi.connect("blofeld")
    try:
        synth.send_sysex(bd.build_sndr(bb=bb, nn=nn))
        for m in synth.receive(timeout=4.0):
            if m.type == "sysex":
                p = waldorf.parse_sysex(m.data)
                if p.get("cmd") == 0x10:
                    return bd.parse_sndd(bytes([0xF0] + list(m.data) + [0xF7]))
        raise RuntimeError("kein SNDD empfangen")
    finally:
        synth.close()


def main() -> int:
    loc = sys.argv[1] if len(sys.argv) > 1 else "A043"
    parsed = read_blofeld(loc)
    print(f"Blofeld-Sound: {parsed['name']!r} ({loc})")

    template = qpat.load(TEMPLATE)
    overrides, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    print(f"{len(overrides)} qpat-Parameter gemappt, {len(unmapped)} unmapped")

    merged = qpat_map.apply_to_template(template, overrides, name=parsed["name"])
    OUT.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in parsed["name"]).strip() or loc
    out_path = OUT / f"{safe}_{loc}.qpat"
    out_path.write_bytes(qpat.build_qpat(
        merged["name"], merged["params"], creator=merged["creator"],
        description=merged["description"], categories=merged["categories"],
        version=merged["version"]))
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
