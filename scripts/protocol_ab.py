#!/usr/bin/env python3
"""Protocol A/B: same patch, old pre-roll window vs. onset capture.

The RF100 v4 log was measured with the old protocol (recording starts 0.35 s
after note-on) and v5 with the onset protocol (record from the onset). The
+8.7 mean difference between them is therefore part protocol, part converter.
This script measures the protocol effect on identical patches.

Usage:
    python3 scripts/protocol_ab.py --manifest transfer/rf100_v5/MANIFEST.json \
        --slot-start 200 --only A003,A018,A025,A041,A051,A053,A057,A064,A070,A090
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import _measure as M  # noqa: E402
import measure_rf100 as R  # noqa: E402
from _device_tool import Iridium  # noqa: E402
from bloridium import audio, midi, qpat, sim  # noqa: E402


def score(data: np.ndarray) -> float:
    bx = np.asarray(data[list(audio.CHANNELS["blofeld"]), :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(data[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
    r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE, meta={"mode": "protocol_ab"},
                       log_path="recordings/protocol_ab.jsonl")
    return r.get("score")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path,
                    default=REPO / "transfer" / "rf100_v5" / "MANIFEST.json")
    ap.add_argument("--slot-start", type=int, default=200)
    ap.add_argument("--only", required=True)
    ap.add_argument("--notes", default="72,60")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    all_entries = manifest["entries"]
    wanted = {v.strip().upper() for v in args.only.split(",")}
    order = {e["loc"]: n for n, e in enumerate(all_entries)}
    entries = [e for e in all_entries if e["loc"].upper() in wanted]
    notes = [int(n) for n in args.notes.split(",")]

    irr = Iridium()
    blo = midi.connect("blofeld")
    rows = []
    try:
        if not R.shell_alive(irr):
            raise SystemExit("Iridium shell is not responding; power-cycle it")
        pids = {name: R.find_pid(irr, name) for name in R.VERIFY_PARAMS}
        for e in entries:
            loc = e["loc"]
            slot = args.slot_start + order[loc]
            expected = qpat.load(args.manifest.parent / e["sd_name"])["params"]
            R.load_patch(irr, slot)
            R.verify_patch(irr, expected, pids)
            R.select_blofeld(blo, loc)
            res = {"loc": loc, "slot": slot}
            for note in notes:
                old = score(M.capture(blo, irr, note=note, vel=100, dur=1.5))
                onset = score(R.capture_onset(blo, irr, note=note, vel=100,
                                              hold=1.2, tail=0.9))
                res[f"old_n{note}"] = old
                res[f"onset_n{note}"] = onset
                print(f"  {loc} n{note}: old {old} onset {onset}", flush=True)
            rows.append(res)
    finally:
        irr.close()
        blo.close()

    print()
    old = [v for r in rows for k, v in r.items() if k.startswith("old_") and v is not None]
    new = [v for r in rows for k, v in r.items() if k.startswith("onset_") and v is not None]
    if old and new:
        print(f"old  n={len(old)} mean {np.mean(old):.1f}")
        print(f"onset n={len(new)} mean {np.mean(new):.1f}")
        print(f"protocol bias: {np.mean(new) - np.mean(old):+.1f}")
    Path("recordings/protocol_ab_summary.json").write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
