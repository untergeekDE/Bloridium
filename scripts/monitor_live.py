#!/usr/bin/env python3
"""Monitor: loggt MIDI-Input auf allen Ports + Audio-Pegel aller 20 Eingaenge."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import rtmidi

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
LOG = sys.argv[2] if len(sys.argv) > 2 else "/tmp/bloridium_monitor.log"


def db(x):
    return -120.0 if x <= 0 else 20 * np.log10(x)


def main():
    ins = []
    rin = rtmidi.MidiIn()
    for i, name in enumerate(rin.get_ports()):
        p = rtmidi.MidiIn()
        p.open_port(i)
        ins.append((name, p))

    with open(LOG, "a") as f:
        f.write(f"\n=== Monitor Start {time.strftime('%H:%M:%S')} ===\n")
        f.flush()
        end = time.time() + DURATION
        while time.time() < end:
            t0 = time.time()
            for name, p in ins:
                while True:
                    m = p.get_message()
                    if not m or not m[0]:
                        break
                    f.write(f"{time.strftime('%H:%M:%S')} MIDI {name}: {[f'{b:02X}' for b in m[0]]}\n")
            try:
                data = audio.record(duration=0.5, channels=None)
            except RuntimeError:
                time.sleep(1.0)
                continue
            peaks = [db(np.max(np.abs(data[i]))) if data.size else -120.0 for i in range(data.shape[0])]
            hot = [(i + 1, p) for i, p in enumerate(peaks) if p > -60]
            if hot:
                f.write(f"{time.strftime('%H:%M:%S')} AUDIO " +
                        ", ".join(f"In{i}:{p:.1f}dBFS" for i, p in hot) + "\n")
            f.flush()
            time.sleep(max(0, 0.5 - (time.time() - t0)))
        f.write(f"=== Monitor Ende {time.strftime('%H:%M:%S')} ===\n")


if __name__ == "__main__":
    main()
