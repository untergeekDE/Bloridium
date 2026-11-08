#!/usr/bin/env python3
"""Minimaler UMP-Test am Iridium: wenige Pakete als echtes UMP an Endpunkt 'MIDI 2.0'.

Sendet: Universal Device Inquiry + Waldorf-Style Requests (ausgewaehlte Model-IDs)
und liest Antworten auf dem Input 'MIDI 2.0'.
Aufruf:  python3 scripts/step2_probe_iridium_ump_min.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from bloridium import midi

UMP_TOOL = str(Path(__file__).resolve().parent.parent / "tools" / "ump_send")
DEST = "MIDI 2.0"  # CoreMIDI-Endpunktname (siehe midi2.list_destinations)


def ump_sysex7(payload: list[int]) -> list[int]:
    """Komplette SysEx7 (F0..F7) als 128-Bit-UMP-Paket (mt=3, status=0 complete)."""
    b = [0xF0] + [d & 0x7F for d in payload] + [0xF7]
    assert len(b) <= 14
    b += [0] * (14 - len(b))
    w = [0, 0, 0, 0]
    w[0] = (0x3 << 28) | (len(b) << 16) | (b[0] << 8) | b[1]
    for i in range(4):
        w[i] = (w[i] & 0xFFFFFFFF)
    w[1] = (b[2] << 24) | (b[3] << 16) | (b[4] << 8) | b[5]
    w[2] = (b[6] << 24) | (b[7] << 16) | (b[8] << 8) | b[9]
    w[3] = (b[10] << 24) | (b[11] << 16) | (b[12] << 8) | b[13]
    out = []
    for x in w:
        out += [(x >> s) & 0xFF for s in (24, 16, 8, 0)]
    return out


def send_ump(pkt: list[int], dest: str = DEST):
    r = subprocess.run([UMP_TOOL, dest, " ".join(f"{x:02X}" for x in pkt)], capture_output=True, text=True)
    if r.returncode != 0:
        print("ump_send Fehler:", r.stderr.strip()[:200])
        return False
    return True


def main() -> int:
    inp = mido.open_input(midi.match_port(list(mido.get_input_names()), "Iridium Keyboard (MIDI 2.0) MIDI 2.0"))

    def drain(wait):
        msgs = []
        deadline = time.time() + wait
        while time.time() < deadline:
            m = inp.poll()
            if m is not None:
                msgs.append(m)
            else:
                time.sleep(0.005)
        return msgs

    tests = [("Identity", [0x7E, 0x7F, 0x06, 0x01])]
    # ausgewaehlte Waldorf-Model-IDs mit SNDR-Varianten
    for model in [0x13, 0x14, 0x15, 0x10, 0x0F, 0x00, 0x1D, 0x1E, 0x1F]:
        tests.append((f"m{model:02X} SNDR", [0x3E, model, 0x00, 0x00]))
        tests.append((f"m{model:02X} SNDR loc", [0x3E, model, 0x00, 0x00, 0x7F, 0x00]))
    try:
        for name, payload in tests:
            send_ump(ump_sysex7(payload))
            msgs = drain(0.4)
            if msgs:
                print(f"[{name}] -> {len(msgs)} Antwort(en):")
                for m in msgs:
                    if m.type == "sysex":
                        print(f"   SysEx {len(m.data)} B: {bytes([0xF0, *m.data, 0xF7]).hex(' ')[:200]}")
                    else:
                        print(f"   {m}")
            else:
                print(f"[{name}] keine Antwort")
    finally:
        inp.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
