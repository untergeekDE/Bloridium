#!/usr/bin/env python3
"""Schritt 2b: Iridium-SysEx probieren (read-only Requests, harmlos).

1. Universal Device Inquiry auf beiden USB-Endpunkten (MIDI 2.0 + Synth)
2. Waldorf-Style Requests F0 3E <model> 00 <cmd> F7 mit Model-ID-Sweep
   (Blofeld nutzt Model 0x13; Iridium/Quantum vermutlich eigene ID)
   Commands: 0x00 (Sound Request), 0x01 (Multi), 0x04 (Global)

Empfangene SysEx-Antworten werden geloggt.
Aufruf:  python3 scripts/step2_probe_iridium_sysex.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from bloridium import midi, waldorf

PORTS = [
    "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
    "Iridium Keyboard (MIDI 2.0) Synth",
]
CMDS = {"SNDR(0x00)": 0x00, "MULR(0x01)": 0x01, "GLBR(0x04)": 0x04}


def open_pair(port: str):
    out_name = midi.match_port(list(mido.get_output_names()), port)
    out = mido.open_output(out_name)
    inp = None
    in_name = None
    try:
        in_name = midi.match_port(list(mido.get_input_names()), port)
        inp = mido.open_input(in_name)
    except RuntimeError:
        pass
    return out, inp, out_name, in_name


def drain(inp, wait: float):
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
            d = list(m.data)
            print(f"    [{tag}] SysEx ({len(d)} B): {bytes([0xF0, *d, 0xF7]).hex(' ')[:120]}...")
        else:
            print(f"    [{tag}] {m}")


def main() -> int:
    for port in PORTS:
        print(f"\n=== Endpunkt: {port} ===")
        out, inp, out_name, in_name = open_pair(port)
        print(f"  Out: {out_name}   In: {in_name or '(none)'}")
        try:
            # 1) Device Inquiry
            out.send(mido.Message("sysex", data=[0x7E, 0x7F, 0x06, 0x01]))
            msgs = drain(inp, 1.5)
            print(f"  Device Inquiry -> {len(msgs)} Antwort(en)")
            show(msgs, "inquiry")

            # 2) Model-ID-Sweep mit Waldorf-Requests
            for model in range(0x00, 0x20):
                for cname, cmd in CMDS.items():
                    out.send(mido.Message("sysex", data=waldorf.build_sysex(model, cmd)))
                    msgs = drain(inp, 0.25)
                    if msgs:
                        print(f"  model=0x{model:02X} cmd={cname} -> {len(msgs)} Antwort(en)")
                        show(msgs, f"m{model:02X}/{cname}")
            print("  Sweep fertig.")
        finally:
            out.close()
            if inp:
                inp.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
