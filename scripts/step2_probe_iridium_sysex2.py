#!/usr/bin/env python3
"""Schritt 2b-2: Iridium-SysEx-Probe, erweitert (read-only).

Varianten pro Endpunkt:
  A) Waldorf-Style mit Location: F0 3E <model> <dev> 00 BB NN F7   (BB NN = 7F 00)
  B) ohne Location:               F0 3E <model> <dev> 00 F7
  C) SNDQ-Inquiry:                F0 3E <model> <dev> 30 F7
  D) via echtem UMP (tools/ump_send) auf dem MIDI-2.0-Endpunkt: Variante B als UMP SysEx7
Model-Sweep 0x00..0x3F, dev in {0x00, 0x7F}.

Aufruf:  python3 scripts/step2_probe_iridium_sysex2.py
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from bloridium import midi, midi2, waldorf

PORTS = [
    "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
    "Iridium Keyboard (MIDI 2.0) Synth",
]
# CoreMIDI-Endpunktnamen (ohne Geraetepraefix, so wie midi2.list_destinations sie sieht)
UMP_DEST = {
    "Iridium Keyboard (MIDI 2.0) MIDI 2.0": "MIDI 2.0",
    "Iridium Keyboard (MIDI 2.0) Synth": "Synth",
}
UMP_TOOL = str(Path(__file__).resolve().parent.parent / "tools" / "ump_send")


def drain(inp, wait):
    msgs = []
    if not inp:
        time.sleep(wait)
        return msgs
    deadline = time.time() + wait
    while time.time() < deadline:
        m = inp.poll()
        if m is not None:
            msgs.append(m)
        else:
            time.sleep(0.005)
    return msgs


def show(msgs, tag):
    for m in msgs:
        if m.type == "sysex":
            print(f"    [{tag}] SysEx {len(m.data)} B: {bytes([0xF0, *m.data, 0xF7]).hex(' ')[:160]}")
        else:
            print(f"    [{tag}] {m}")


def probe_port(port: str, use_ump: bool = False):
    out_name = midi.match_port(list(mido.get_output_names()), port)
    out = mido.open_output(out_name)
    inp = None
    try:
        in_name = midi.match_port(list(mido.get_input_names()), port)
        inp = mido.open_input(in_name)
    except RuntimeError:
        pass
    print(f"\n=== {port} {'(UMP)' if use_ump else '(bytestream)'} ===")
    try:
        for model in range(0x00, 0x40):
            for dev in (0x00, 0x7F):
                variants = {
                    "A(loc)": [0x3E, model, dev, 0x00, 0x7F, 0x00],
                    "B": [0x3E, model, dev, 0x00],
                    "C(SNDQ)": [0x3E, model, dev, 0x30],
                }
                for vname, data in variants.items():
                    if use_ump:
                        # SysEx7 als UMP: komplett in einem 128-Bit-Paket wenn <= 14 Datenbytes
                        full = [0xF0] + data + [0xF7]
                        if len(full) <= 14:
                            # mt=3 (SysEx7), 128-bit, status=0 (complete)
                            b = full + [0] * (14 - len(full))
                            w0 = (0x3 << 28) | (0 << 24) | (len(b) << 16) | (b[0] << 8) | b[1]
                            w1 = (b[2] << 24) | (b[3] << 16) | (b[4] << 8) | b[5]
                            w2 = (b[6] << 24) | (b[7] << 16) | (b[8] << 8) | b[9]
                            w3 = (b[10] << 24) | (b[11] << 16) | (b[12] << 8) | b[13]
                            pkt = [(w0 >> s) & 0xFF for s in (24, 16, 8, 0)] + \
                                  [(w1 >> s) & 0xFF for s in (24, 16, 8, 0)] + \
                                  [(w2 >> s) & 0xFF for s in (24, 16, 8, 0)] + \
                                  [(w3 >> s) & 0xFF for s in (24, 16, 8, 0)]
                            r = subprocess.run([UMP_TOOL, UMP_DEST[port], " ".join(f"{x:02X}" for x in pkt)],
                                               capture_output=True, text=True)
                            if r.returncode != 0:
                                print("ump_send Fehler:", r.stderr[:200])
                                return
                        else:
                            continue
                    else:
                        out.send(mido.Message("sysex", data=data))
                    msgs = drain(inp, 0.15)
                    if msgs:
                        print(f"  model=0x{model:02X} dev=0x{dev:02X} {vname}: {len(msgs)} Antwort(en)")
                        show(msgs, f"m{model:02X}/d{dev:02X}/{vname}")
        print("  Sweep fertig.")
    finally:
        out.close()
        if inp:
            inp.close()


def main() -> int:
    import sys as _sys
    mode = _sys.argv[1] if len(_sys.argv) > 1 else "all"
    if mode in ("all", "byte"):
        probe_port(PORTS[0], use_ump=False)
        probe_port(PORTS[1], use_ump=False)
    if mode in ("all", "ump"):
        probe_port(PORTS[0], use_ump=True)
        probe_port(PORTS[1], use_ump=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
