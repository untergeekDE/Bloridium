#!/usr/bin/env python3
"""Schritt 4: A/B-Klangmessung Blofeld (In3/4) vs Iridium (In5/6).

Spielt gleichzeitig eine Note auf beiden Synths (Blofeld ch5, Iridium Part 1 ch6),
nimmt alle 20 Scarlett-Kanaele auf und vergleicht Pegel + Spektral centroid.

Aufruf:  python3 scripts/step4_measure_ab.py [--note 36] [--dur 3.0] [--label TEXT]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi

REC = Path(__file__).resolve().parent.parent / "recordings"


def spectral_centroid(x: np.ndarray, sr: int = audio.SAMPLERATE) -> float:
    x = np.asarray(x, dtype=np.float64).mean(axis=0)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((f * X).sum() / max(X.sum(), 1e-12))


def band_energies(x: np.ndarray, sr: int = audio.SAMPLERATE, n_bands: int = 8,
                  f_lo: float = 40.0, f_hi: float = 12000.0) -> tuple[np.ndarray, np.ndarray]:
    """Log-spaced band energies (dB) + band edges. x: (channels, samples)."""
    x = np.asarray(x, dtype=np.float64).mean(axis=0)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    edges = np.geomspace(f_lo, f_hi, n_bands + 1)
    bands = []
    for i in range(n_bands):
        m = (f >= edges[i]) & (f < edges[i + 1])
        e = float(np.sqrt(np.sum(X[m] ** 2)))
        bands.append(20 * np.log10(max(e, 1e-12)))
    return np.array(bands), edges


def main() -> int:
    note, dur, label = 36, 3.0, "ab"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--note":
            note = int(args[i + 1])
        elif a == "--dur":
            dur = float(args[i + 1])
        elif a == "--label":
            label = args[i + 1]
    REC.mkdir(exist_ok=True)

    with midi.connect("blofeld") as blo, midi.connect("iridium") as irr:
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
        time.sleep(0.5)
        blo.note_on(note=note, velocity=100)
        irr.note_on(note=note, velocity=100, channel=5)  # Part 1 = MIDI 6
        try:
            time.sleep(0.3)
            data = audio.record(duration=dur, channels=None)  # (20, samples)
        finally:
            blo.note_off(note=note)
            irr.note_off(note=note, channel=5)
            for ch in range(16):
                blo.control_change(123, 0, channel=ch)
                irr.control_change(123, 0, channel=ch)

    b_ch, i_ch = audio.CHANNELS["blofeld"], audio.CHANNELS["iridium"]
    blo_x, irr_x = data[b_ch, :], data[i_ch, :]
    mb, mi = audio.measure(blo_x), audio.measure(irr_x)
    pb, pi = float(np.max(mb["peak_dbfs"])), float(np.max(mi["peak_dbfs"]))
    cb, ci = spectral_centroid(blo_x), spectral_centroid(irr_x)
    bb, edges = band_energies(blo_x)
    ib, _ = band_energies(irr_x)
    print(f"=== A/B note {note}, {dur}s ===")
    print(f"Blofeld  In3/4: peak {pb:6.1f} dBFS  rms {float(np.max(mb['rms_dbfs'])):6.1f}  centroid {cb:8.1f} Hz")
    print(f"Iridium  In5/6: peak {pi:6.1f} dBFS  rms {float(np.max(mi['rms_dbfs'])):6.1f}  centroid {ci:8.1f} Hz")
    print(f"Delta: peak {pi - pb:+.1f} dB   centroid {ci - cb:+.1f} Hz")
    print("\nBand-Vergleich (Iridium - Blofeld in dB, log-Baender):")
    for i in range(len(bb)):
        d = ib[i] - bb[i]
        bar = "#" * max(0, int(round(d)))
        print(f"  {edges[i]:7.0f}-{edges[i+1]:7.0f} Hz: {d:+6.1f} dB {bar}")
    ts = time.strftime("%Y%m%d_%H%M%S")
    np.save(REC / f"{label}_{ts}_blofeld.npy", blo_x)
    np.save(REC / f"{label}_{ts}_iridium.npy", irr_x)
    report = {
        "label": label, "note": note, "dur": dur,
        "blofeld": {"peak_dbfs": pb, "rms_dbfs": float(np.max(mb["rms_dbfs"])), "centroid_hz": cb},
        "iridium": {"peak_dbfs": pi, "rms_dbfs": float(np.max(mi["rms_dbfs"])), "centroid_hz": ci},
        "band_edges_hz": edges.tolist(), "band_delta_db": (ib - bb).tolist(),
    }
    import json
    (REC / f"{label}_{ts}_report.json").write_text(json.dumps(report, indent=2))
    print(f"gespeichert: recordings/{label}_{ts}_*.npy + _report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
