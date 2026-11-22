#!/usr/bin/env python3
"""Envelope time sweep (stage-specific), Blofeld raw and Iridium norm.

Usage:
    python3 scripts/calib_envelope2.py blo --stage attack --values 0,16,...
    python3 scripts/calib_envelope2.py irr --stage decay --curve 1
"""
import argparse
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

REPO = Path("/Users/jan/Code/Bloridium")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import calib_envelope as C  # noqa: E402
from _device_tool import Iridium  # noqa: E402
import measure_rf100 as R  # noqa: E402
from bloridium import audio, midi  # noqa: E402

SR = audio.SAMPLERATE
STAGES = ("attack", "decay", "release")


def env_db(x, win=0.01):
    n = max(1, int(win * SR))
    m = len(x) // n
    rms = np.sqrt(np.mean(np.asarray(x)[:m * n].reshape(m, n) ** 2, axis=1))
    return 20 * np.log10(rms + 1e-12), win


def stage_time(x, stage):
    env, win = env_db(x)
    peak_i = int(np.argmax(env))
    peak = float(env[peak_i])
    if peak < -70:
        return None
    if stage == "attack":
        hit = np.where(env[:peak_i + 1] > peak - 10)[0]
        if not len(hit):
            return 0.0
        return (peak_i - int(hit[0])) * win
    if stage == "decay":
        # flat reference right after the peak
        ref = float(np.median(env[peak_i:min(peak_i + 30, len(env))]))
        target = ref - 26
        after = np.where(env[peak_i:] < target)[0]
        return float(after[0] * win) if len(after) else None
    # release: flat sustain level after the attack/decay, then the drop
    a = min(peak_i + 40, len(env) - 1)
    b = min(a + 60, len(env))
    sus = float(np.median(env[a:b]))
    drop = np.where(env[a:] < sus - 2)[0]
    if not len(drop):
        return None
    rel0 = a + int(drop[0])
    below = np.where(env[rel0:] < sus - 26)[0]
    return float(below[0] * win) if len(below) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("synth", choices=("blo", "irr"))
    ap.add_argument("--stage", choices=STAGES, required=True)
    ap.add_argument("--values", default="0,16,32,48,64,80,96,112,127")
    ap.add_argument("--curve", type=int, default=1, help="Iridium envelope curve")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    values = [int(v) for v in args.values.split(",")]

    irr = Iridium() if args.synth == "irr" else None
    bl = midi.connect("blofeld") if args.synth == "blo" else None
    rows = []
    try:
        for v in values:
            if args.synth == "blo":
                a, d, s, r = 0, 64, 127, 64
                if args.stage == "attack":
                    a, s = v, 127
                elif args.stage == "decay":
                    d, s = v, 0
                else:
                    r = v
                C.setup_blofeld(bl, attack=a, decay=d, sustain=s, release=r)
                rec = C.play_and_record(bl, hold=1.5, record_s=6.0)
                x = np.asarray(rec[list(audio.CHANNELS["blofeld"]), :],
                               dtype=np.float64).mean(axis=0)
                label, value = "raw", v
            else:
                norm = v / 127.0
                a, d, s, r = 0.0, 0.5, 1.0, 0.5
                if args.stage == "attack":
                    a, s = norm, 1.0
                elif args.stage == "decay":
                    d, s = norm, 0.0
                else:
                    r = norm
                C.setup_iridium(irr, attack=a, decay=d, sustain=s, release=r)
                R.collect(irr, f"set-param AmpEnvAttackCurve {args.curve}", max_s=10)
                R.collect(irr, f"set-param AmpEnvDecayCurve {args.curve}", max_s=10)
                R.collect(irr, f"set-param AmpEnvReleaseCurve {args.curve}", max_s=10)
                rec = C.play_and_record(irr, hold=1.5, record_s=6.0)
                x = np.asarray(rec[list(audio.CHANNELS["iridium"]), :],
                               dtype=np.float64).mean(axis=0)
                label, value = "norm", norm
            t = stage_time(x, args.stage)
            rows.append({"synth": args.synth, "stage": args.stage,
                         "curve": args.curve if args.synth == "irr" else None,
                         label: value, "time": t})
            print(f"{args.synth} {args.stage} {label} {value:.3f}: "
                  f"{'n/a' if t is None else f'{t:.2f}s'}", flush=True)
            if args.out:
                Path(args.out).write_text(json.dumps(rows, indent=1))
    finally:
        if irr:
            irr.close()
        if bl:
            bl.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
