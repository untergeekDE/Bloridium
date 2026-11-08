#!/usr/bin/env python3
"""Device-ID-Sweep am Iridium (read-only): F0 3E <model> <dev> 00 F7 ueber alle dev 0x00..0x7E.

Hypothese: das Iridium ignoriert Requests, deren DEV nicht seiner Device-ID entspricht.
Aufruf:  python3 scripts/step2_probe_iridium_devsweep.py [port-index 0|1]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from bloridium import midi

PORTS = [
    "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
    "Iridium Keyboard (MIDI 2.0) Synth",
]
MODELS = [0x13, 0x14, 0x15, 0x16, 0x00, 0x0F, 0x10]


def main() -> int:
    pidx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    port = PORTS[pidx]
    out = mido.open_output(midi.match_port(list(mido.get_output_names()), port))
    inp = mido.open_input(midi.match_port(list(mido.get_input_names()), port))

    def drain(wait):
        msgs = []
        deadline = time.time() + wait
        while time.time() < deadline:
            m = inp.poll()
            if m is not None:
                msgs.append(m)
            else:
                time.sleep(0.003)
        return msgs

    try:
        print(f"Sweep: {port}, models={[hex(m) for m in MODELS]}, dev 0x00..0x7E, cmd 0x00")
        found = 0
        for model in MODELS:
            for dev in range(0x00, 0x7F):
                out.send(mido.Message("sysex", data=[0x3E, model, dev, 0x00]))
                msgs = drain(0.06)
                for m in msgs:
                    found += 1
                    if m.type == "sysex":
                        print(f"  ANTWORT model=0x{model:02X} dev=0x{dev:02X}: {bytes([0xF0, *m.data, 0xF7]).hex(' ')[:200]}")
                    else:
                        print(f"  ANTWORT model=0x{model:02X} dev=0x{dev:02X}: {m}")
            print(f"  model 0x{model:02X} durch, bisher {found} Antworten")
        print("fertig, Antworten:", found)
    finally:
        out.close()
        inp.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
