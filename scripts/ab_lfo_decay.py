#!/usr/bin/env python3
"""Isolate the LFO Decay fix: same patch, LfoNDecay 0.0 vs 1.0.

The 0.6.6 measurement changed two things at once (LfoNDecay and the bipolar
filter envelope amount from 0.6.5). This A/B keeps everything else fixed and
only toggles the LFO decay, so the score delta is attributable to the LFO fix.

Usage:
    python3 scripts/ab_lfo_decay.py --manifest transfer/don_solaris_v1/MANIFEST.json \
        --slot-start 200 --only E001,E016,E072,E089,E090 --run
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import measure_rf100 as R  # noqa: E402
from _device_tool import Iridium  # noqa: E402
from bloridium import audio, midi, qpat, sim  # noqa: E402

LFO_DECAY = [f"Lfo{n}Decay" for n in (1, 2, 3)]


def score_one(blo, irr, loc: str, note: int = 60) -> float:
    data = R.capture_onset(blo, irr, note=note, vel=100)
    bx = np.asarray(data[list(audio.CHANNELS["blofeld"]), :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(data[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
    r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE,
                       meta={"mode": "lfo_decay_ab", "blofeld": loc, "note": note},
                       log_path="recordings/lfo_decay_ab.jsonl")
    return r.get("score")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path,
                    default=REPO / "transfer" / "don_solaris_v1" / "MANIFEST.json")
    ap.add_argument("--slot-start", type=int, default=200)
    ap.add_argument("--only", required=True)
    ap.add_argument("--notes", default="60")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    entries = manifest["entries"]
    order = {e["loc"]: i for i, e in enumerate(entries)}
    wanted = [v.strip().upper() for v in args.only.split(",")]
    notes = [int(n) for n in args.notes.split(",")]
    if not args.run:
        print("dry run; add --run")
        return 0

    irr = Iridium()
    blo = midi.connect("blofeld")
    rows = []
    try:
        pids = {n: R.find_pid(irr, n) for n in R.VERIFY_PARAMS}
        for loc in wanted:
            e = entries[order[loc]]
            expected = qpat.load(args.manifest.parent / e["sd_name"])["params"]
            R.load_patch(irr, args.slot_start + order[loc])
            R.verify_patch(irr, expected, pids)
            R.select_blofeld(blo, loc)
            res = {"loc": loc}
            for decay in (0.0, 1.0):
                for k in LFO_DECAY:
                    R.collect(irr, f"set-param {k} {decay}", max_s=8)
                scores = [score_one(blo, irr, loc, n) for n in notes]
                scores = [s for s in scores if s is not None]
                res[f"decay_{decay}"] = float(np.mean(scores)) if scores else None
                print(f"  {loc} decay {decay}: {res[f'decay_{decay}']}", flush=True)
            rows.append(res)
    finally:
        irr.close()
        blo.close()

    d = [r["decay_1.0"] - r["decay_0.0"] for r in rows
         if r["decay_1.0"] is not None and r["decay_0.0"] is not None]
    if d:
        print(f"\nmean delta (LFO on - off): {np.mean(d):+.1f} over n={len(d)}")
    Path("recordings/lfo_decay_ab_summary.json").write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
