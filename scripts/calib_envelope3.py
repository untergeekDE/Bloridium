#!/usr/bin/env python3
"""Verified envelope time sweep: every set-param is read back.

Keeps one clean test patch and only changes the envelope parameters between
points, so the lazy QUIR shell cannot leave a stale state behind.

Usage:
    python3 scripts/calib_envelope3.py irr --stage decay --curve 1 --values 0,32,64,96,127
    python3 scripts/calib_envelope3.py blo --stage attack
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path("/Users/jan/Code/Bloridium")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import calib_envelope as C  # noqa: E402
from _device_tool import Iridium  # noqa: E402
import measure_rf100 as R  # noqa: E402
from bloridium import audio, blofeld_dump as bd, midi  # noqa: E402

SR = audio.SAMPLERATE
CURVE_KEYS = tuple(f"{grp}{stage}Curve" for grp in
                   ("AmpEnv", "Filter1", "Filter2", "FreeEnv1", "FreeEnv2", "FreeEnv3")
                   for stage in ("Attack", "Decay", "Release"))
ENV_KEYS = ("AmpEnvAttack", "AmpEnvDecay", "AmpEnvSustain", "AmpEnvRelease")


def env_db(x, win=0.01):
    n = max(1, int(win * SR))
    m = len(x) // n
    rms = np.sqrt(np.mean(np.asarray(x)[:m * n].reshape(m, n) ** 2, axis=1))
    return 20 * np.log10(rms + 1e-12), win


def stage_time(x, stage, drop=20.0):
    env, win = env_db(x)
    pk_i = int(np.argmax(env))
    pk = float(env[pk_i])
    if pk < -70:
        return None
    if stage == "attack":
        hit = np.where(env[:pk_i + 1] > pk - drop)[0]
        return 0.0 if not len(hit) else (pk_i - int(hit[0])) * win
    if stage == "decay":
        after = np.where(env[pk_i:] < pk - drop)[0]
        return float(after[0] * win) if len(after) else None
    a = min(pk_i + 40, len(env) - 1)
    sus = float(np.median(env[a:min(a + 60, len(env))]))
    d = np.where(env[a:] < sus - 2)[0]
    if not len(d):
        return None
    r0 = a + int(d[0])
    below = np.where(env[r0:] < sus - drop)[0]
    return float(below[0] * win) if len(below) else None


def set_verify(irr, name, value, tol=0.002):
    pid = R.find_pid(irr, name)
    R.collect(irr, f"set-param {name} {value}", max_s=10)
    got = R.collect(irr, f"get-param {pid}", max_s=10)
    try:
        v = float(got.strip().split("=")[-1])
    except ValueError:
        raise SystemExit(f"readback failed for {name}: {got!r}")
    if abs(v - value) > tol:
        raise SystemExit(f"{name}: set {value}, readback {v}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("synth", choices=("blo", "irr"))
    ap.add_argument("--stage", choices=("attack", "decay", "release"), required=True)
    ap.add_argument("--values", default="0,16,32,48,64,80,96,112,127")
    ap.add_argument("--curve", type=int, default=1)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    values = [int(v) for v in args.values.split(",")]

    irr = Iridium() if args.synth == "irr" else None
    bl = midi.connect("blofeld") if args.synth == "blo" else None
    rows = []
    try:
        if irr:
            C.setup_iridium(irr, 0.0, 0.5, 1.0, 0.5)
            for k in CURVE_KEYS:
                set_verify(irr, k, args.curve)
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
                norm = round(v / 127.0, 4)
                a, d, s, r = 0.0, 0.5, 1.0, 0.5
                if args.stage == "attack":
                    a, s = norm, 1.0
                elif args.stage == "decay":
                    d, s = norm, 0.0
                else:
                    r = norm
                set_verify(irr, "AmpEnvAttack", a)
                set_verify(irr, "AmpEnvDecay", d)
                set_verify(irr, "AmpEnvSustain", s)
                set_verify(irr, "AmpEnvRelease", r)
                rec = C.play_and_record(irr, hold=1.5, record_s=6.0)
                x = np.asarray(rec[list(audio.CHANNELS["iridium"]), :],
                               dtype=np.float64).mean(axis=0)
                label, value = "norm", norm
            t = stage_time(x, args.stage)
            rows.append({"synth": args.synth, "stage": args.stage,
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
