#!/usr/bin/env python3
"""sim_compare.py – Ähnlichkeits-Score Blofeld vs Iridium.

Offline:  python3 scripts/sim_compare.py --npy A.npy B.npy [--log PATH] [--meta k=v ...]
Live:     python3 scripts/sim_compare.py --live [--note 60] [--dur 1.6]
              [--blofeld A043] [--iridium-slot 207] [--log PATH] [--meta k=v ...]

.npy: shape (N,) oder (ch, N) – wird gemittelt. Live: spielt Note auf beiden
Synths (Blofeld ch5, Iridium ch6-9), nimmt alle 20 Scarlett-Kanäle auf,
vergleicht Blofeld In3/4 vs Iridium In5/6. Log: JSONL (Default recordings/sim_log.jsonl).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, sim


def _load_npy(p) -> np.ndarray:
    x = np.asarray(np.load(p), dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=0)
    return x.ravel()


def _meta(pairs) -> dict:
    d = {}
    for kv in pairs or []:
        k, _, v = kv.partition("=")
        d[k] = v
    return d


def print_result(r: dict, a_name: str, b_name: str) -> None:
    print(f"Score {a_name} vs {b_name}: {r['score']} ({r['verdict']})  "
          f"spec_cos={r.get('spec_cos')} env_dtw={r.get('env_dtw')}")
    deltas = r.get("band_delta_db") or []
    if deltas:
        top = sorted(range(len(deltas)), key=lambda i: -abs(deltas[i]))[:5]
        print("Top-Band-Deltas (dB): " + ", ".join(f"band{i}: {deltas[i]:+.1f}" for i in top))


def run_npy(pa, pb, log, meta) -> int:
    a, b = _load_npy(pa), _load_npy(pb)
    r = sim.score_pair(a, b, sr=audio.SAMPLERATE, meta=meta, log_path=log)
    print_result(r, str(pa), str(pb))
    return 0 if r["score"] is not None else 1


def run_live(note, dur, blofeld, slot, log, meta) -> int:
    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    try:
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)   # All Notes Off
                s.control_change(7, 127, channel=ch)     # Output Level voll
        time.sleep(0.4)
        blo.note_on(note=note, velocity=100, channel=blo.channel)
        for ch in (5, 6, 7, 8):                          # Iridium Parts 1-4
            irr.note_on(note=note, velocity=100, channel=ch)
        time.sleep(0.25)                                 # Attack abwarten
        d = audio.record(duration=dur, channels=None)
        blo.note_off(note=note, channel=blo.channel)
        for ch in (5, 6, 7, 8):
            irr.note_off(note=note, channel=ch)
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
    finally:
        blo.close()
        irr.close()
    bx = np.asarray(d[audio.CHANNELS["blofeld"], :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(d[audio.CHANNELS["iridium"], :], dtype=np.float64).mean(axis=0)
    m = dict(meta)
    m.update({"mode": "live", "note": note, "blofeld": blofeld, "iridium_slot": slot})
    r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE, meta=m, log_path=log)
    print_result(r, f"blofeld:{blofeld}", f"iridium:{slot}")
    return 0 if r["score"] is not None else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npy", nargs=2, metavar=("A", "B"), help="offline: zwei .npy vergleichen")
    ap.add_argument("--live", action="store_true", help="live messen (beide Synths spielen)")
    ap.add_argument("--note", type=int, default=60)
    ap.add_argument("--dur", type=float, default=1.6)
    ap.add_argument("--blofeld", default="A043")
    ap.add_argument("--iridium-slot", default="?")
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    ap.add_argument("--meta", nargs="*", default=[], help="k=v Paare fürs Log")
    args = ap.parse_args(argv)
    meta = _meta(args.meta)
    if args.npy:
        return run_npy(args.npy[0], args.npy[1], args.log, meta)
    if args.live:
        return run_live(args.note, args.dur, args.blofeld, args.iridium_slot, args.log, meta)
    ap.error("entweder --npy A B oder --live")
    return 2


if __name__ == "__main__":
    sys.exit(main())
