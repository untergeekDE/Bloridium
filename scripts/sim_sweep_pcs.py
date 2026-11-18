#!/usr/bin/env python3
"""sim_sweep_pcs.py – PC-controlled comparison across all converted sounds.

Blofeld: bank A, PC = location number - 1 (A001 -> PC0, A043 -> PC42), ch5.
Iridium: Favorites set 6, PC per DEFAULT_MAP (current 2026-11-14: A001->108 ...
          A073->116, mido PC 0-based — shifted after re-import, see comment).

Usage:  python3 scripts/sim_sweep_pcs.py [--only A043] [--notes 60,72] [--bank 6] [--log PATH]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, sim

# Blofeld location -> Iridium PC (mido, 0-based) in the active Favorites bank.
# CURRENT 2026-11-14 (both synths reconnected; Favorites set 6 re-assigned
# after re-import, order as in transfer/upload/MANIFEST.md):
#   A001 JMX jun = PC108, A008 Easy Piano = PC109, ... A073 Chord Hose = PC116.
# History 2026-11-09 (before reset): A001->105 ... A073->113 (display: mido PC = "MIDI" - 2).
# Attention: slots 0200+ are the storage; via PC only Favorites are selected.
DEFAULT_MAP = {
    "A001": 108, "A008": 109, "A010": 110, "A019": 111, "A022": 112,
    "A039": 113, "A043": 114, "A071": 115, "A073": 116,
}
CALIB_MAP = {"calib200": 98, "calib201": 99, "calib202": 100, "calib203": 101,
             "calib204": 102, "calib205": 103, "v15init206": 104}


def measure(blo, irr, note: int, dur: float, sr: int):
    for s in (blo, irr):
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    # CC7=127 only on the Blofeld (real volume). On the Iridium CC7 is Filter1 Amount
    # with the rdb map -- CC7=0/127 on ch6 would change the sound!
    for ch in range(16):
        blo.control_change(7, 127, channel=ch)
    time.sleep(0.3)
    blo.note_on(note=note, velocity=100, channel=blo.channel)
    irr.note_on(note=note, velocity=100, channel=5)   # Part 1 (ch6) - monophonic
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
    ap.add_argument("--only", help="only one location (e.g. A043)")
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
            # Select bank A explicitly (CC0/CC32 = bank select on the BLOFELD);
            # otherwise the PC lands in the bank active on the device (B008 trap!)
            blo.control_change(0, 0, channel=blo.channel)
            blo.control_change(32, 0, channel=blo.channel)
            blo.program_change(blo_pc, channel=blo.channel)
            # Iridium: do NOT send CC0/CC32 anymore -- with the rdb-.mimap those are
            # parameters (CC0=Cutoff, CC32=FinePitch), bank 6 stays active.
            irr.program_change(irr_pc, channel=5)
            time.sleep(0.7)
            for note in notes:
                r = measure(blo, irr, note, args.dur, audio.SAMPLERATE)
                if r["score"] is None:
                    print(f"  WARNING: {loc} note{note} silent (score=None) -- possibly the wrong "
                          f"Favorites bank on the Iridium (not controllable via CC0 with the rdb map)!")
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
        print(f"\nBest: {best[0]} note{best[1]} score={best[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
