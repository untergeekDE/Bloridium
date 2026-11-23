#!/usr/bin/env python3
"""Isolate the 0.6.5 filter-envelope-amount change: norm(raw) vs 0.5+0.5*norm(raw).

Loads each sound from the package, writes both mapping variants into
Filter1/2EnvAmount and scores them. Everything else stays untouched.

Usage:
    python3 scripts/ab_env_amount.py --only E001,E015,E072,E077,E089 --run
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
from bloridium import audio, blofeld_dump as bd, midi, prognose, sim  # noqa: E402


def score_one(blo, irr, loc: str, note: int = 60):
    data = R.capture_onset(blo, irr, note=note, vel=100)
    bx = np.asarray(data[list(audio.CHANNELS["blofeld"]), :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(data[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
    r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE,
                       meta={"mode": "env_amount_ab", "blofeld": loc, "note": note},
                       log_path="recordings/env_amount_ab.jsonl")
    return r.get("score")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path,
                    default=REPO / "transfer" / "don_solaris_v1" / "MANIFEST.json")
    ap.add_argument("--slot-start", type=int, default=200)
    ap.add_argument("--only", required=True)
    ap.add_argument("--note", type=int, default=60)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if not args.run:
        print("dry run; add --run")
        return 0

    manifest = json.loads(args.manifest.read_text())
    entries = manifest["entries"]
    order = {e["loc"]: i for i, e in enumerate(entries)}
    locs = [v.strip().upper() for v in args.only.split(",")]

    irr = Iridium()
    blo = midi.connect("blofeld")
    rows = []
    try:
        pids = {n: R.find_pid(irr, n) for n in R.VERIFY_PARAMS}
        for loc in locs:
            parsed = bd.parse_sndd(prognose.find_dump(REPO / "dumps", loc).read_bytes())
            p = parsed["params"]
            raw1, raw2 = p["Filter 1 Env Amount"], p["Filter 2 Env Amount"]
            variants = {"old raw/127": (raw1 / 127, raw2 / 127),
                        "bipolar": (0.5 + 0.5 * raw1 / 127, 0.5 + 0.5 * raw2 / 127)}
            R.load_patch(irr, args.slot_start + order[loc])
            R.select_blofeld(blo, loc)
            row = {"loc": loc, "raw1": raw1, "raw2": raw2}
            for name, (v1, v2) in variants.items():
                R.collect(irr, f"set-param Filter1EnvAmount {v1:.5f}", max_s=8)
                R.collect(irr, f"set-param Filter2EnvAmount {v2:.5f}", max_s=8)
                row[name] = score_one(blo, irr, loc, args.note)
                print(f"  {loc} {name:12s} (f1 {v1:.3f}): {row[name]}", flush=True)
            rows.append(row)
    finally:
        irr.close()
        blo.close()

    d = [r["bipolar"] - r["old raw/127"] for r in rows
         if r["bipolar"] is not None and r["old raw/127"] is not None]
    if d:
        print(f"\nmean delta (bipolar - old): {np.mean(d):+.1f} over n={len(d)}")
    Path("recordings/env_amount_ab_summary.json").write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
