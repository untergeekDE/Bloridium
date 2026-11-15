#!/usr/bin/env python3
"""Blofeld Filter1-Cutoff-Kalibrierung v2: CC78-Sweep, Grenzfrequenz per Harmonischen-Knick.

CCs (docs/MAPPING-MASTER.md): 78 F1 Cutoff, 80 F1 Reso, 87 F1 Env Amount, 90 F1 Mod Amount
(bipolar, 64 = neutral). Note 36 (C2, 65.4 Hz) -> viele Harmonische; Reso 0.
LP24: A_k ~ (C/k) / sqrt(1+(k*f0/fc)^8). fc gesucht per Grid-Search (beste Anpassung).

Aufruf:  python3 scripts/spike_cutoff_sweep_blofeld.py
Output:  recordings/cutoff_calib_blofeld_<ts>.json + stdout (raw->Hz + log-fit)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
NOTE = 36
F0 = 440.0 * 2 ** ((NOTE - 69) / 12.0)
RAWS = [0, 16, 32, 48, 64, 80, 96, 112, 127]


def cutoff_hz(x: np.ndarray, sr: int, f0: float) -> float:
    """Grenzfrequenz eines LP24-gefilterten Saw: Harmonische A_k, fit fc per Grid-Search."""
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean()
    n = len(x)
    X = np.abs(np.fft.rfft(x * np.hanning(n)))
    f = np.fft.rfftfreq(n, 1.0 / sr)
    ks = np.arange(1, min(60, int(12000 / f0)) + 1)
    amp = np.array([np.interp(k * f0, f, X) for k in ks])
    best_fc, best_err = f0, np.inf
    for fc in np.geomspace(20.0, 22000.0, 400):
        model = (1.0 / ks) / np.sqrt(1.0 + (ks * f0 / fc) ** 8)
        model /= model[0]
        a = amp / amp[0]
        err = float(np.sum((np.log(a[1:] + 1e-12) - np.log(model[1:] + 1e-12)) ** 2))
        if err < best_err:
            best_err, best_fc = err, fc
    return float(best_fc)


def main() -> int:
    blo = midi.connect("blofeld")
    ch = blo.channel
    try:
        for c in range(16):
            blo.control_change(123, 0, channel=c)
        blo.control_change(7, 127, channel=ch)    # Volume voll
        blo.control_change(87, 0, channel=ch)     # F1 Env Amount = 0
        blo.control_change(90, 64, channel=ch)    # F1 Mod Amount neutral
        blo.control_change(80, 0, channel=ch)     # Reso 0 (reiner LP24-Knick)
        time.sleep(0.3)
        rows = []
        for raw in RAWS:
            blo.control_change(78, raw, channel=ch)
            time.sleep(0.15)
            blo.note_on(note=NOTE, velocity=100, channel=ch)
            time.sleep(0.35)
            d = audio.record(duration=1.0, channels=None)
            blo.note_off(note=NOTE, channel=ch)
            blo.control_change(123, 0, channel=ch)
            x = np.asarray(d[audio.CHANNELS["blofeld"], :], dtype=np.float64).mean(axis=0)
            hz = cutoff_hz(x, audio.SAMPLERATE, F0)
            rows.append({"raw": raw, "hz": round(hz, 1)})
            print(f"raw {raw:3d} -> {hz:9.1f} Hz")
        ok = [(r["raw"], r["hz"]) for r in rows if r["hz"] > 20.0]
        xs = np.array([r for r, _ in ok], dtype=np.float64)
        ys = np.log10([h for _, h in ok])
        b, a = np.polyfit(xs, ys, 1)
        print(f"fit: log10(Hz) = {a:.4f} + {b:.6f}*raw")
        print(f"  raw 0 -> {10 ** a:.1f} Hz, raw 64 -> {10 ** (a + b * 64):.1f} Hz, "
              f"raw 127 -> {10 ** (a + b * 127):.1f} Hz")
        ts = time.strftime("%Y%m%d_%H%M%S")
        out = REPO / "recordings" / f"cutoff_calib_blofeld_{ts}.json"
        out.write_text(json.dumps({"ts": ts, "note": NOTE, "rows": rows,
                                   "fit": {"a": float(a), "b": float(b)}}, indent=2))
        print("geschrieben:", out)
        blo.control_change(0, 0, channel=ch)      # Bank A
        blo.program_change(0, channel=ch)          # A001 wiederherstellen
    finally:
        blo.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
