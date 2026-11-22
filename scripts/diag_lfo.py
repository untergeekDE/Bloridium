#!/usr/bin/env python3
"""Diagnose: does a converted patch's LFO really move the pitch?

Motivation (2026-11-22): on Don Solaris E090 ("Soft Pulses", Iridium slot 289)
LFO1/LFO2 -> Pitch had no audible effect at all, while the same routing works
on an init patch. Prime suspect: the converter writes LfoNAttack = 0 AND
LfoNDecay = 0 for a neutral Blofeld LFO Fade, while every factory/template qpat
has LfoNDecay = 1.0. If Decay is a fade level/time, 0 kills the LFO output.

The script adds a clean matrix row (LFO 1 -> Pitch, amount 1.0, no control),
plays a note and prints the fundamental trajectory in semitones for:
  decay 0.0 (what the converter writes) vs decay 1.0 (factory value).

Usage:
    python3 scripts/diag_lfo.py --slot 289 --run
"""
import argparse
import sys
import threading
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import measure_rf100 as R  # noqa: E402
from _device_tool import Iridium  # noqa: E402
from bloridium import audio, midi  # noqa: E402

SR = audio.SAMPLERATE


def pitch_hz(x: np.ndarray) -> float:
    """Fundamental via autocorrelation (robust for pulse/saw)."""
    x = x - x.mean()
    if np.sqrt(np.mean(x ** 2)) < 1e-5:
        return 0.0
    corr = np.correlate(x, x, mode="full")[len(x) - 1:]
    lo, hi = int(SR / 1200), int(SR / 40)
    lag = lo + int(np.argmax(corr[lo:hi]))
    return SR / lag


def trajectory(x: np.ndarray, start: float, win: float = 0.06, n: int = 24):
    out = []
    for i in range(n):
        a = int((start + i * win) * SR)
        seg = x[a:a + int(win * SR)]
        if len(seg) < 256:
            break
        f = pitch_hz(seg)
        out.append(f)
    if not out or min(out) <= 0:
        return []
    ref = float(np.median(out))
    return [round(12 * np.log2(f / ref), 2) for f in out if f > 0]


def play(bl, irr, note=60, vel=100, lead=0.5, hold=2.5):
    for ch in range(16):
        bl.control_change(123, 0, channel=ch)
        bl.control_change(7, 127, channel=ch)
    irr.silence_part()

    def run():
        time.sleep(lead)
        bl.note_on(note=note, velocity=vel)
        irr.note_on(note=note, velocity=vel)
        time.sleep(hold)
        bl.note_off(note=note)
        irr.note_off(note=note)

    th = threading.Thread(target=run)
    th.start()
    data = audio.record(duration=lead + hold + 0.3, channels=None)
    th.join()
    return data, lead


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slot", type=int, default=289)
    ap.add_argument("--row", type=int, default=24, help="free matrix row to use")
    ap.add_argument("--note", type=int, default=60)
    ap.add_argument("--run", action="store_true", help="actually touch the hardware")
    args = ap.parse_args()
    if not args.run:
        print("dry run; add --run to load the slot and play")
        return 0

    irr = Iridium()
    bl = midi.connect("blofeld")
    try:
        R.load_patch(irr, args.slot)
        r = args.row
        R.collect(irr, f"set-param MatrixSrc{r} 7", max_s=8)          # LFO 1
        R.collect(irr, f"set-param MatrixControl{r} 0", max_s=8)      # Off
        R.collect(irr, f"set-param MatrixDst{r} 1", max_s=8)          # Pitch
        R.collect(irr, f"set-param MatrixAmount{r} 1.0", max_s=8)
        R.collect(irr, f"set-param MatrixOnOff{r} 1", max_s=8)
        for decay in (0.0, 1.0):
            R.collect(irr, f"set-param Lfo1Decay {decay}", max_s=8)
            time.sleep(1.5)
            data, lead = play(bl, irr, note=args.note)
            ir = np.asarray(data[list(audio.CHANNELS["iridium"]), :],
                            dtype=np.float64).mean(axis=0)
            traj = trajectory(ir, lead + 0.2)
            span = max(traj) - min(traj) if traj else 0.0
            print(f"Lfo1Decay {decay}: semitone trajectory {traj} "
                  f"(span {span:.1f})", flush=True)
    finally:
        irr.close()
        bl.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
