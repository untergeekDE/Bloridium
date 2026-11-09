#!/usr/bin/env python3
"""sim_sweep_pcs.py – PC-gesteuerter Vergleich ueber alle konvertierten Sounds.

Blofeld: Bank A, PC = Location-Nummer - 1 (A001 -> PC0, A043 -> PC42), ch5.
Iridium: Favorites Bank 6 (CC0=6), PC lt. --map (Default: A001->106 ... A043->112,
          "MIDI 107" = mido-PC 106, 0-basiert).

Aufruf:  python3 scripts/sim_sweep_pcs.py [--only A043] [--notes 60,72] [--bank 6] [--log PATH]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, sim

# Blofeld-Location -> Iridium-PC (mido, 0-basiert) in Favorites Bank 6.
# Empirisch 2026-11-09: "MIDI 113" (SH Power) = mido PC 111 -> mido = MIDI-Nummer - 2.
DEFAULT_MAP = {
    "A001": 105, "A008": 106, "A010": 107, "A019": 108, "A022": 109,
    "A039": 110, "A043": 111, "A071": 112, "A073": 113,
}


def measure(blo, irr, note: int, dur: float, sr: int):
    for s in (blo, irr):
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
            s.control_change(7, 127, channel=ch)
    time.sleep(0.3)
    blo.note_on(note=note, velocity=100, channel=blo.channel)
    irr.note_on(note=note, velocity=100, channel=5)   # Part 1 (ch6) - monophon
    time.sleep(0.3)
    d = audio.record(duration=dur, channels=None)
    blo.note_off(note=note, channel=blo.channel)
    irr.note_off(note=note, channel=5)
    for s in (blo, irr):
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    bx = np.asarray(d[list(audio.CHANNELS["blofeld"]), :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(d[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
    return sim.score_pair(bx, ix, sr=sr, meta={}, log_path="/tmp/x.jsonl")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="nur eine Location (z. B. A043)")
    ap.add_argument("--notes", default="60,72")
    ap.add_argument("--bank", type=int, default=6)
    ap.add_argument("--dur", type=float, default=1.5)
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    args = ap.parse_args(argv)
    notes = [int(n) for n in args.notes.split(",")]

    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    rows = []
    try:
        for loc, irr_pc in DEFAULT_MAP.items():
            if args.only and loc != args.only:
                continue
            blo_pc = int(loc[1:]) - 1
            blo.program_change(blo_pc, channel=blo.channel)
            irr.control_change(0, args.bank, channel=5)
            irr.control_change(32, 0, channel=5)
            irr.program_change(irr_pc, channel=5)
            time.sleep(0.7)
            for note in notes:
                r = measure(blo, irr, note, args.dur, audio.SAMPLERATE)
                meta = {"mode": "pc_sweep", "blofeld": loc, "irr_pc": irr_pc,
                        "bank": args.bank, "note": note}
                r2 = sim.score_pair.__wrapped__ if False else None
                # log with meta:
                import json, time as _t
                sim.log_run(r, meta, args.log)
                rows.append((loc, note, r["score"], r.get("spec_cos"), r.get("env_dtw"), r["verdict"]))
                print(f"{loc} (blo PC{blo_pc} / irr bank{args.bank} PC{irr_pc}) note{note}: "
                      f"score={r['score']} cos={r.get('spec_cos')} dtw={r.get('env_dtw')} {r['verdict']}")
    finally:
        blo.close()
        irr.close()
    if rows:
        best = max(rows, key=lambda r: r[2] if r[2] is not None else -1)
        print(f"\nBeste: {best[0]} note{best[1]} score={best[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
