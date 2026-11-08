#!/usr/bin/env python3
"""Scan: Auf welchem MIDI-Kanal empfangt welches Gerat?

Pro Port wird Kanal fur Kanal (0..15) eine Note gespielt, alle 20 Scarlett-
Eingaenge aufgenommen und gegen die Baseline gehalten.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from bloridium import audio

NOTE = 60
PORTS = [
    "Iridium Keyboard (MIDI 2.0) Synth",
    "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
    "Launchpad Pro MK3 LPProMK3 DIN",
    "Launchpad Pro MK3 LPProMK3 MIDI",
    "Launchpad Pro MK3 LPProMK3 DAW",
    "Scarlett 18i8 USB",
]


def db(x):
    return -120.0 if x <= 0 else 20 * np.log10(x)


def peak_db(data):
    return np.array([db(np.max(np.abs(data[i]))) if data.size else -120.0 for i in range(data.shape[0])])


def main() -> int:
    print("Baseline...")
    base = peak_db(audio.record(duration=2.5, channels=None))
    time.sleep(1.0)
    print("  " + "  ".join(f"In{i+1}:{base[i]:.0f}" for i in range(20)) + "\n")

    for port in PORTS:
        print(f"=== {port} ===")
        out = mido.open_output(port)
        found = []
        try:
            for ch in range(16):
                out.send(mido.Message("note_on", note=NOTE, velocity=127, channel=ch))
                time.sleep(0.35)
                data = audio.record(duration=1.0, channels=None)
                out.send(mido.Message("note_off", note=NOTE, velocity=0, channel=ch))
                out.send(mido.Message("control_change", control=123, value=0, channel=ch))
                time.sleep(0.7)
                peaks = peak_db(data)
                hot = [(i + 1, peaks[i]) for i in range(20) if peaks[i] - base[i] > 20 and peaks[i] > -90]
                if hot:
                    found.append((ch + 1, hot))
                    print(f"  Kanal {ch+1:2d}: " + ", ".join(f"In{i} ({p:.1f} dBFS)" for i, p in hot))
        finally:
            out.close()
        if not found:
            print("  kein Kanal mit Signal")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
