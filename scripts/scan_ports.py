#!/usr/bin/env python3
"""Scan: Auf welchem MIDI-Out-Port erreicht man welchen Synth?

Pro Port: CC7/CC11 (Volume/Expression) auf Maximum, dann Note auf allen
16 Kanaelen, alle 20 Scarlett-Eingaenge aufnehmen, All Notes Off.
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
    "Scarlett 18i8 USB",
    "Launchpad Pro MK3 LPProMK3 DIN",
    "Launchpad Pro MK3 LPProMK3 MIDI",
    "Launchpad Pro MK3 LPProMK3 DAW",
]


def db(x):
    return -120.0 if x <= 0 else 20 * np.log10(x)


def peak_db(data):
    return np.array([db(np.max(np.abs(data[i]))) if data.size else -120.0 for i in range(data.shape[0])])


def probe(port: str, base):
    out = mido.open_output(port)
    try:
        for ch in range(16):  # Volume & Expression hoch
            out.send(mido.Message("control_change", control=7, value=127, channel=ch))
            out.send(mido.Message("control_change", control=11, value=127, channel=ch))
        for ch in range(16):
            out.send(mido.Message("note_on", note=NOTE, velocity=127, channel=ch))
        time.sleep(0.4)
        data = audio.record(duration=1.5, channels=None)
        for ch in range(16):
            out.send(mido.Message("note_off", note=NOTE, velocity=0, channel=ch))
            out.send(mido.Message("control_change", control=123, value=0, channel=ch))
    finally:
        out.close()
    time.sleep(1.0)
    p = peak_db(data)
    hot = [(i + 1, p[i]) for i in range(20) if p[i] - base[i] > 20 and p[i] > -90]
    return hot, p


def main() -> int:
    base = peak_db(audio.record(duration=2.5, channels=None))
    time.sleep(1.0)
    print("Baseline: " + "  ".join(f"In{i+1}:{base[i]:.0f}" for i in range(20)) + "\n")
    for port in PORTS:
        hot, p = probe(port, base)
        tag = ", ".join(f"In{i} ({v:.1f} dBFS)" for i, v in hot) if hot else "kein Signal"
        print(f"[{port}]\n  -> {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
