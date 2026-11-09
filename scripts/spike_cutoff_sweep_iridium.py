#!/usr/bin/env python3
"""Cutoff-Sweep-Messung am Iridium: misst den aktuell geladenen Slot.

Aufruf:  python3 scripts/spike_cutoff_sweep_iridium.py <slot-label> [note]
         z. B. python3 scripts/spike_cutoff_sweep_iridium.py 200

Ablauf pro Aufruf:
  - All Notes Off (CC123=0) + CC7=127 (Output Level) auf allen 16 Kanaelen
  - Note-On auf ch6-9 (Parts 1-4, damit der aktive Part egal ist)
  - Aufnahme 1.6 s ueber Scarlett In 5/6 (audio.CHANNELS["iridium"])
  - Sustain-Fenster 0.5-1.2 s (Filter-Env verfaelscht Attack, siehe HANDOVER)
  - peak/rms dBFS + spektraler Centroid + Band-Energien
  - Ergebnis als JSON nach recordings/cutoff_sweep_iridium_<label>_<ts>.json

Slot-Wechsel am Geraet manuell (PC laedt nur Favorites) -> pro Slot ein Aufruf.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, workflow

REPO = Path(__file__).resolve().parent.parent


def _hp(seg: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
    """FFT-Hochpass (nur Analyse): kill DC/Netzbrumm < cutoff Hz."""
    X = np.fft.rfft(seg)
    f = np.fft.rfftfreq(len(seg), 1 / sr)
    X[f < cutoff] = 0
    return np.fft.irfft(X, len(seg))


def _centroid(x: np.ndarray, sr: int) -> float:
    x = np.asarray(x, dtype=np.float64)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((f * X).sum() / max(X.sum(), 1e-12))


def _band_db(x: np.ndarray, sr: int, n_bands: int = 8,
             f_lo: float = 40.0, f_hi: float = 12000.0):
    """Log-Band-Energien in dB + Kanten (1D-Eingang, lokal)."""
    x = np.asarray(x, dtype=np.float64)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    edges = np.geomspace(f_lo, f_hi, n_bands + 1)
    out = []
    for i in range(n_bands):
        m = (f >= edges[i]) & (f < edges[i + 1])
        e = float(np.sqrt(np.sum(X[m] ** 2)))
        out.append(round(20 * np.log10(max(e, 1e-12)), 2))
    return out, [round(float(e), 1) for e in edges]


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "active"
    note = int(sys.argv[2]) if len(sys.argv) > 2 else 60   # 60 = 262 Hz (weg vom Brumm)

    irr = midi.connect("iridium")
    try:
        for ch in range(16):
            irr.control_change(123, 0, channel=ch)   # All Notes Off
            irr.control_change(7, 127, channel=ch)     # Output Level voll
        time.sleep(0.4)
        for ch in (5, 6, 7, 8):                        # Parts 1-4
            irr.note_on(note=note, velocity=127, channel=ch)
        time.sleep(0.25)                               # Attack/Onset abwarten
        d = audio.record(duration=1.6, channels=audio.CHANNELS["iridium"])
        for ch in (5, 6, 7, 8):
            irr.note_off(note=note, channel=ch)
        for ch in range(16):
            irr.control_change(123, 0, channel=ch)
    finally:
        irr.close()

    x = np.asarray(d, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=0)
    x = np.atleast_1d(x).ravel()
    sr = audio.SAMPLERATE
    seg = x[int(0.5 * sr):int(1.2 * sr)]
    seg_hp = _hp(seg, sr, 80.0)

    def stats(s):
        peak = 20 * np.log10(max(float(np.max(np.abs(s))), 1e-12))
        rms = 20 * np.log10(max(float(np.sqrt(np.mean(s ** 2))), 1e-12))
        return peak, rms, _centroid(s, sr)

    peak, rms, cen = stats(seg)
    peak_hp, rms_hp, cen_hp = stats(seg_hp)
    bands, band_edges = _band_db(seg_hp, sr)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = {
        "slot": label, "note": note, "ts": ts,
        "sustain_window_s": [0.5, 1.2],
        "peak_dbfs": round(peak, 2), "rms_dbfs": round(rms, 2),
        "centroid_hz": round(cen, 1),
        "hp80": {"peak_dbfs": round(peak_hp, 2), "rms_dbfs": round(rms_hp, 2),
                 "centroid_hz": round(cen_hp, 1)},
        "band_energies_hp80": bands,
        "band_edges_hz": band_edges,
        "channels": list(audio.CHANNELS["iridium"]),
    }
    path = REPO / "recordings" / f"cutoff_sweep_iridium_{label}_{ts}.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Slot {label}: peak {peak:6.1f} dBFS  rms {rms:6.1f} dBFS  centroid {cen:7.1f} Hz  "
          f"| HP80: peak {peak_hp:6.1f} rms {rms_hp:6.1f} centroid {cen_hp:7.1f} Hz  -> {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
