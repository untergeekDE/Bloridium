#!/usr/bin/env python3
"""Schritt 4: A/B-Klangmessung Blofeld (In3/4) vs Iridium (In5/6).

Wrapper ueber bloridium.workflow (argv/Exit/Stdout unveraendert).

Spielt gleichzeitig eine Note auf beiden Synths (Blofeld ch5, Iridium Part 1 ch6),
nimmt alle 20 Scarlett-Kanaele auf und vergleicht Pegel + Spektral centroid.

Aufruf:  python3 scripts/step4_measure_ab.py [--note 36] [--dur 3.0] [--label TEXT]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import workflow

REC = workflow.RECORDINGS


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

    report = workflow.measure_ab(note=note, dur=dur, label=label, rec_dir=REC)
    b, i = report["blofeld"], report["iridium"]
    print(f"=== A/B note {note}, {dur}s ===")
    print(f"Blofeld  In3/4: peak {b['peak_dbfs']:6.1f} dBFS  rms {b['rms_dbfs']:6.1f}  centroid {b['centroid_hz']:8.1f} Hz")
    print(f"Iridium  In5/6: peak {i['peak_dbfs']:6.1f} dBFS  rms {i['rms_dbfs']:6.1f}  centroid {i['centroid_hz']:8.1f} Hz")
    print(f"Delta: peak {i['peak_dbfs'] - b['peak_dbfs']:+.1f} dB   centroid {i['centroid_hz'] - b['centroid_hz']:+.1f} Hz")
    print("\nBand-Vergleich (Iridium - Blofeld in dB, log-Baender):")
    edges = report["band_edges_hz"]
    for k, d in enumerate(report["band_delta_db"]):
        bar = "#" * max(0, int(round(d)))
        print(f"  {edges[k]:7.0f}-{edges[k+1]:7.0f} Hz: {d:+6.1f} dB {bar}")
    f = report["files"]
    print(f"gespeichert: {Path(f['report']).name.replace('_report.json', '')}_*.npy + _report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
