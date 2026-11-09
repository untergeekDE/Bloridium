#!/usr/bin/env python3
"""sim_live.py – Parameter am Iridium per CC drehen und gegen Referenz messen.

Aufruf:
  python3 scripts/sim_live.py --param "Filter1 Cutoff" --value 90 --ref ref.npy
  python3 scripts/sim_live.py --param "Filter1 Cutoff" --value 90   # Blofeld spielt live mit

--ref: Blofeld-Referenz als .npy (z. B. aus sim_compare.py --live). Ohne --ref
spielt der Blofeld (DEFAULT_PORTS, ch5) simultan mit. CC kommt aus
ccmap.cc_for (docs/midi-maps/iridium_pid_map.csv). Ergebnis: Score + JSONL-Log.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, ccmap, midi, sim


def _load_npy(p) -> np.ndarray:
    x = np.asarray(np.load(p), dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=0)
    return x.ravel()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--param", required=True, help="Parametername (z. B. 'Filter1 Cutoff')")
    ap.add_argument("--value", type=int, required=True, help="CC-Wert 0..127")
    ap.add_argument("--ref", help="Blofeld-Referenz-.npy (sonst Blofeld live)")
    ap.add_argument("--note", type=int, default=60)
    ap.add_argument("--dur", type=float, default=1.6)
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    args = ap.parse_args(argv)

    cc, pid = ccmap.cc_for(args.param)
    print(f"Param {args.param!r} -> CC{cc} (Pid {pid}) Wert {args.value}")

    irr = midi.connect("iridium")
    blo = None if args.ref else midi.connect("blofeld")
    try:
        for s in [irr] + ([blo] if blo else []):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
                s.control_change(7, 127, channel=ch)
        for ch in (5, 6, 7, 8):                      # Iridium Parts 1-4
            irr.control_change(cc, args.value, channel=ch)
        time.sleep(0.2)
        if blo:
            blo.note_on(note=args.note, velocity=100, channel=blo.channel)
        for ch in (5, 6, 7, 8):
            irr.note_on(note=args.note, velocity=100, channel=ch)
        time.sleep(0.25)
        d = audio.record(duration=args.dur, channels=None)
        if blo:
            blo.note_off(note=args.note, channel=blo.channel)
        for ch in (5, 6, 7, 8):
            irr.note_off(note=args.note, channel=ch)
        for s in [irr] + ([blo] if blo else []):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
    finally:
        irr.close()
        if blo:
            blo.close()
    ix = np.asarray(d[audio.CHANNELS["iridium"], :], dtype=np.float64).mean(axis=0)

    meta = {"mode": "live", "param": args.param, "cc": cc, "pid": pid,
            "value": args.value, "note": args.note}
    if args.ref:
        bx = _load_npy(args.ref)
        meta["ref"] = str(args.ref)
    else:
        bx = np.asarray(d[audio.CHANNELS["blofeld"], :], dtype=np.float64).mean(axis=0)
        meta["blofeld"] = "live"
    r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE, meta=meta, log_path=args.log)
    print(f"Score: {r['score']} ({r['verdict']})  spec_cos={r.get('spec_cos')} env_dtw={r.get('env_dtw')}")
    return 0 if r["score"] is not None else 1


if __name__ == "__main__":
    sys.exit(main())
