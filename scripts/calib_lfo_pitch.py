#!/usr/bin/env python3
"""A8: LFO -> Pitch depth, Blofeld vs Iridium, direct path vs mod matrix.

Motivation (2026-11-26): by ear the converted LFO modulation is ~2x too deep
(user verdict on 0.6.7/A001: "LFO etwa auf die Haelfte zurueckgedreht ... gute
Groessenordnung"). Every LFO->Pitch row is mapped with amt_bipolar(raw) =
0.5 + (raw-64)/254 and the divisor 254 was an assumption, never calibrated.

Setup (mirrors profile_lfo_measure.py): init A066, Osc1 Sine only, FX off,
LFO1 Sine, free rate raw 40 (Blofeld ~2.6 Hz, converted Iridium ~1.1 Hz),
no delay, neutral fade. Two Blofeld paths at the same raw amounts:
  direct : Osc Pitch Source = LFO 1, Osc Pitch Amount = raw   (sdata 50/51)
  matrix : Mod 1 = LFO 1 -> Pitch, Amount = raw               (sdata 261..263)
The Iridium receives exactly the converted values (overrides_for +
IridiumState, i.e. the shipped converter mapping). Both synths play note 60
(C4) in one capture; a heterodyne estimator tracks the instantaneous
frequency and the vibrato depth is (max-min)/2 in semitones.

Usage:
    python3 scripts/calib_lfo_pitch.py --check          # print base programs
    python3 scripts/calib_lfo_pitch.py --run            # full sweep
    python3 scripts/calib_lfo_pitch.py --report         # write the MD table
Writes recordings/lfo_pitch_calib.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, midi, qpat  # noqa: E402
import _measure as M  # noqa: E402
import profile_init_sweep as P  # noqa: E402
from profile_todo_measure import (  # noqa: E402
    IridiumState, apply_fx, base_values, overrides_for, with_overrides,
)
from _device_tool import Iridium  # noqa: E402

LOG = REPO / "recordings/lfo_pitch_calib.jsonl"
SR = audio.SAMPLERATE
F0 = 261.63  # note 60, C4
SPEED_RAW = 40          # Blofeld ~2.6 Hz, Iridium converted ~1.1 Hz (A7 curve)
DUR, PRE, SKIP = 6.0, 0.25, 0.25
AMOUNTS = [64, 66, 70, 74, 80, 88, 96, 112, 127]   # 64 = neutral (zero check)
VARIANTS = ("direct", "matrix")


def base_sdata(variant: str, amount: int, speed: int = SPEED_RAW) -> bytes:
    """Init A066 + single sine osc + clean LFO1, one active modulation path.

    All of the init sound's own mod paths (PWM, F1/F2 cutoff, amp, LFO1*MW
    pitch) are switched off so the path under test is the only LFO consumer.
    """
    b = {8: 4, 24: 0, 40: 0, 61: 127, 62: 0, 63: 0, 64: 0, 65: 0,
         77: 1, 78: 127, 80: 0, 87: 64, 89: 0, 97: 0,
         128: 0, 129: 0, 144: 0, 145: 0,
         6: 0, 10: 0, 109: 0, 123: 0,
         160: 0, 161: speed, 163: 0, 164: 0, 165: 0, 166: 0, 167: 64}
    for m in range(16):          # clear all init matrix rows
        b[261 + 3 * m] = 0
    if variant == "direct":
        b[50] = 1                # Osc Pitch Source = LFO 1
        b[51] = amount           # Osc Pitch Amount (bipolar, 64 = 0)
    else:
        b[50] = 0                # Osc Pitch Source = off
        b[261] = 1               # Mod 1 Source = LFO 1
        b[262] = 0               # Mod 1 Destination = Pitch
        b[263] = amount          # bipolar, 64 = 0
    return with_overrides(P.load_init()["sdata"], b)


def inst_pitch_semi(x: np.ndarray, f0: float = F0, win_ms: float = 60.0,
                   skip_s: float = SKIP) -> np.ndarray:
    """Instantaneous pitch in semitones via complex heterodyne (pure sine).

    win_ms must stay far below the LFO period (>= 0.3 s at our rates) but is
    as long as possible to crush harmonics of the fundamental (the 2nd partial
    at 2*f0 otherwise shows up as envelope ripple -> fake "rate").
    """
    x = np.asarray(x, dtype=np.float64)
    n = np.arange(len(x))
    z = x * np.exp(-2j * np.pi * f0 * n / SR)
    w = max(16, int(win_ms * SR / 1000) // 2 * 2 + 1)
    zz = np.convolve(z, np.ones(w) / w, "same")
    a, b = int(skip_s * SR), max(0, len(x) - int(skip_s * SR))
    ph = np.unwrap(np.angle(zz[a:b]))
    f = f0 + np.gradient(ph, 1.0 / SR) / (2 * np.pi)
    f = np.convolve(f, np.ones(5) / 5, "same")
    return 12.0 * np.log2(np.maximum(f, 20.0) / f0)


def fft_peak_hz(x: np.ndarray, lo: float = 100.0, hi: float = 2000.0) -> float:
    """Dominant FFT peak (fundamental sanity check for a sine patch)."""
    x = np.asarray(x, dtype=np.float64)
    X = np.abs(np.fft.rfft((x - x.mean()) * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = (f >= lo) & (f <= hi)
    return float(f[m][int(np.argmax(X[m]))])


def depth_and_rate(semi: np.ndarray, skip_s: float = SKIP,
                   dur: float = DUR) -> tuple[float, float]:
    """(depth_semi, lfo_hz): robust peak-to-peak/2 and zero-crossing rate."""
    if len(semi) < int(0.5 * SR):
        return 0.0, 0.0
    lo, hi = float(np.percentile(semi, 2)), float(np.percentile(semi, 98))
    depth = (hi - lo) / 2.0
    d = semi - np.median(semi)
    sign = np.sign(d)
    cross = int(np.sum((sign[1:] * sign[:-1]) < 0))
    rate = cross / 2.0 / max(dur - 2 * skip_s, 1e-6)
    return depth, rate


def check() -> None:
    """Print the parsed base programs and converted overrides (no hardware)."""
    for variant in VARIANTS:
        sd = base_sdata(variant, 80)
        from bloridium import blofeld_dump as bd
        body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd]
        body.append(bd.checksum(bytes(sd)))
        p = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
        par = p["params"]
        print(f"--- {variant} amount 80")
        print(f"  Osc1 {par['Osc 1 Shape']!r}, Osc2 {par['Osc 2 Shape']!r}, "
              f"Osc3 {par['Osc 3 Shape']!r}, FX1 {par['Effect 1 Type']!r}, "
              f"FX2 {par['Effect 2 Type']!r}")
        print(f"  LFO1 {par['LFO 1 Shape']!r} speed {par['LFO 1 Speed']!r} "
              f"sync {par['LFO 1 Sync']} clocked {par['LFO 1 Clocked']} "
              f"fade {par['LFO 1 Fade']}")
        if variant == "direct":
            print(f"  direct: {par['Osc Pitch Source']!r} amount {par['Osc Pitch Amount']}")
        else:
            print(f"  matrix: Mod1 {par['Modulation 1 Source']!r} -> "
                  f"{par['Modulation 1 Destination']!r} amount {par['Modulation 1 Amount']}")
        ov = overrides_for(sd)
        mat = {k: round(v[0], 3) for k, v in ov.items() if k.startswith("Matrix")}
        print(f"  converted matrix: {mat}")
        lfo = {k: round(v[0], 3) for k, v in ov.items() if k.startswith("Lfo")}
        print(f"  converted LFO: {lfo}")


def verify_params(irr, pairs, tol: float = 5e-3):
    """Read params back; return the list of mismatching (name, got)."""
    bad = []
    for k, v in pairs:
        try:
            g = irr.get(k)
        except Exception:
            bad.append((k, "read error"))
            continue
        if abs(g - v) > tol:
            bad.append((k, g))
    return bad


def detect_lfo_slot(ov: dict) -> int:
    """Matrix slot carrying the LFO 1 -> Pitch row (Src 7, Dst 1)."""
    for n in range(1, 17):
        src = ov.get(f"MatrixSrc{n}")
        dst = ov.get(f"MatrixDst{n}")
        if src and dst and abs(src[0] - 7.0) < 1e-6 and abs(dst[0] - 1.0) < 1e-6:
            return n
    return 0


def run(amounts: list[int]) -> None:
    init_vals = base_values()
    base_sd = base_sdata("matrix", 64)
    base_ov = overrides_for(base_sd)
    irr = Iridium()
    bl = midi.connect("blofeld")
    state = IridiumState(irr, base_ov, init_vals)
    # CRITICAL: the edit buffer must hold the factory init before the diff
    # machinery can layer anything on top (2026-11-26: a run with "Prophet
    # Brass" in the buffer produced ~8 semi of fake depth at ~400 Hz).
    irr.cmd("init-patch", wait=0.8)
    # CRITICAL #2: right after init-patch the QUIR shell answers get/set-param
    # with memory garbage (measured 2026-11-26) - the first base application
    # gets swallowed and rows that are never re-sent stay dead. Verify the
    # base (matrix + LFO params) by readback and retry until it holds.
    time.sleep(1.2)
    crit = [(k, v[0]) for k, v in sorted(base_ov.items())
            if k.startswith(("Matrix", "Lfo"))]
    bad = None
    for attempt in range(4):
        irr.set_many(crit)
        time.sleep(0.25)
        bad = verify_params(irr, crit)
        if not bad:
            break
        print(f"  base apply retry {attempt + 1}: bad={bad[:4]}", flush=True)
        time.sleep(0.8)
    if bad:
        raise SystemExit(f"base application failed, power-cycle the Iridium: {bad[:6]}")
    rows = []
    try:
        for variant in VARIANTS:
            for amount in amounts:
                sd = base_sdata(variant, amount)
                actual = M.load_sndd_actual(bl, sd)
                if actual is None:
                    print(f"SKIP {variant} {amount}: no Blofeld readback", flush=True)
                    continue
                ov = overrides_for(actual)
                state.apply(state.desired(ov))
                # per-condition verification of the row under test: a swallowed
                # set-param would silently zero the depth (see matrix run 1)
                slot = detect_lfo_slot(ov)
                if slot:
                    row_pairs = [(k, v[0]) for k, v in sorted(ov.items())
                                 if k.startswith(("MatrixSrc", "MatrixDst",
                                                  "MatrixOnOff", "MatrixAmount",
                                                  "MatrixControl"))
                                 and k.endswith(str(slot))]
                    bad = verify_params(irr, row_pairs)
                    if bad:
                        irr.set_many(row_pairs)
                        time.sleep(0.15)
                        bad = verify_params(irr, row_pairs)
                    if bad:
                        print(f"  WARN {variant} raw {amount}: row {slot} not "
                              f"confirmed: {bad}", flush=True)
                apply_fx(irr, {"kind": "effect"})
                time.sleep(0.15)
                d = M.capture(bl, irr, note=60, vel=100, dur=DUR, pre=PRE)
                bx = np.mean(d[list(audio.CHANNELS["blofeld"]), :], axis=0)
                ix = np.mean(d[list(audio.CHANNELS["iridium"]), :], axis=0)
                pb, rb = depth_and_rate(inst_pitch_semi(bx))
                pi, ri = depth_and_rate(inst_pitch_semi(ix))
                fb = fft_peak_hz(bx)
                fi = fft_peak_hz(ix)
                mat = {k: round(v[0], 4) for k, v in ov.items()
                       if k.startswith("MatrixAmount")}
                ratio = pi / pb if pb > 0.01 else float("nan")
                row = {"kind": "row", "variant": variant, "raw": amount,
                       "depth_b": round(pb, 4), "depth_i": round(pi, 4),
                       "rate_b": round(rb, 3), "rate_i": round(ri, 3),
                       "fpeak_b": round(fb, 2), "fpeak_i": round(fi, 2),
                       "ratio": round(ratio, 3) if ratio == ratio else None,
                       "conv_matrix_amounts": mat}
                rows.append(row)
                with LOG.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                print(f"  {variant:6s} raw {amount:3d}  BF {pb:6.3f} semi "
                      f"({fb:6.1f} Hz pk, {rb:4.2f} Hz)  IR {pi:6.3f} semi "
                      f"({fi:6.1f} Hz pk, {ri:4.2f} Hz)  "
                      f"ratio {ratio:5.2f}  conv {mat}", flush=True)
                if amount == amounts[0] and not (250.0 <= fb <= 275.0
                                                  and 250.0 <= fi <= 275.0):
                    print("  WARN: fundamental is not ~261.6 Hz - wrong patch "
                          "in a buffer?", flush=True)
    finally:
        try:                        # restore the user's last selection (E001)
            irr.cmd("load-patch 200", wait=0.6)
        except Exception:
            pass
        irr.close()
        bl.close()
    print(f"\n{len(rows)} rows -> {LOG}")
    for variant in VARIANTS:
        rs = [r for r in rows if r["variant"] == variant]
        if rs:
            print(f"{variant}: " + "  ".join(
                f"{r['raw']}:{r['depth_b']:.2f}/{r['depth_i']:.2f}" for r in rs))


def report() -> None:
    rows = [json.loads(l) for l in LOG.read_text().splitlines()
            if l.strip().startswith("{")]
    rows = [r for r in rows if r.get("kind") == "row"]
    out = ["# A8 — LFO->Pitch depth: Blofeld vs Iridium (2026-11-26)", "",
           "Init A066, Osc1 Sine, FX off, LFO1 Sine, speed raw 40",
           "(Blofeld ~2.6 Hz, converted Iridium ~1.1 Hz), note 60.",
           "depth = peak-to-peak/2 of the fundamental, in semitones.", ""]
    for variant in VARIANTS:
        rs = [r for r in rows if r.get("variant") == variant]
        if not rs:
            continue
        out += [f"## {variant}", "",
                "| raw | BF semi | IR semi | ratio | BF Hz | IR Hz |",
                "|---:|---:|---:|---:|---:|---:|"]
        for r in sorted(rs, key=lambda r: r["raw"]):
            out.append(f"| {r['raw']} | {r['depth_b']:.3f} | {r['depth_i']:.3f} | "
                       f"{r['ratio'] if r.get('ratio') is None else round(r['ratio'], 2)} | "
                       f"{r['rate_b']:.2f} | {r['rate_i']:.2f} |")
        out.append("")
    text = "\n".join(out)
    print(text)
    (REPO / "docs/research/LFO-PITCH-CALIB-2026-11-26.md").write_text(text + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--amounts", default=",".join(str(a) for a in AMOUNTS))
    args = ap.parse_args()
    if args.check:
        check()
    if args.run:
        run([int(a) for a in args.amounts.split(",")])
    if args.report:
        report()
    if not (args.check or args.run or args.report):
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
