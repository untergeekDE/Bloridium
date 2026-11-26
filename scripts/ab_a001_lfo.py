#!/usr/bin/env python3
"""A/B: A001 "JMX jun." - what exactly differs in its LFO modulation?

Context (2026-11-26): the user's ear verdict on the converted A001 was "LFO
about 2x too strong; half the amount feels right" - but the A8 calibration
confirmed the LFO->Pitch *depth* mapping for A001's amounts (raw 70/58).
Remaining suspects: (a) LFO *speed* (A001 raw 58 -> Iridium norm 0.457),
(b) the *filter cutoff* modulation (LFO1 -> F1 Cutoff, raw 103) whose depth
mapping was never calibrated.

This script plays the original Blofeld A001 and the converted Iridium sound
(slot 300) alternately (same capture, both channels), note 60, and measures:
- pitch vibrato: rate (Hz) and depth (semi) via heterodyne
- brightness modulation: centroid trajectory -> rate and depth (dB)

Usage: python3 scripts/ab_a001_lfo.py [--run]
Writes recordings/ab_a001_lfo.jsonl and prints the comparison.
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

from bloridium import audio, midi  # noqa: E402
import _measure as M  # noqa: E402
import measure_rf100 as R  # noqa: E402
from _device_tool import Iridium  # noqa: E402
from calib_lfo_pitch import inst_pitch_semi, fft_peak_hz  # noqa: E402

LOG = REPO / "recordings/ab_a001_lfo.jsonl"
SR = audio.SAMPLERATE
F0 = 261.63          # note 60
DUR, PRE, SKIP = 8.0, 0.3, 0.35
SLOT = 300           # A001 @ rf600 (0.6.7)


def centroid_track(x: np.ndarray, win: int = 4800, hop: int = 2400) -> np.ndarray:
    """Spectral centroid per frame (brightness trajectory)."""
    n = max(0, (len(x) - win) // hop)
    out = np.empty(n)
    for i in range(n):
        seg = x[i * hop:i * hop + win] * np.hanning(win)
        X = np.abs(np.fft.rfft(seg))
        f = np.fft.rfftfreq(win, 1 / SR)
        out[i] = float((f * X).sum() / max(X.sum(), 1e-12))
    return out


def track_peaks(traj: np.ndarray, frame_rate: float, lo: float = 0.3,
               hi: float = 20.0, n_peaks: int = 3) -> list[dict]:
    """Top modulation peaks (rate Hz, relative dB) of a trajectory via FFT."""
    if len(traj) < 8:
        return []
    y = traj - traj.mean()
    if float(np.max(np.abs(y))) < 1e-9:
        return []
    Y = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    f = np.fft.rfftfreq(len(y), 1.0 / frame_rate)
    m = (f >= lo) & (f <= hi)
    if not m.any():
        return []
    fm, Ym = f[m], Y[m]
    Ydb = 20 * np.log10(Ym / max(Ym.max(), 1e-12))
    peaks = []
    used = np.zeros(len(fm), bool)
    for _ in range(n_peaks):
        cand = np.where(~used)[0]
        if not len(cand):
            break
        k = cand[int(np.argmax(Ym[cand]))]
        used[max(0, k - 2):k + 3] = True
        # parabolic interpolation on the peak
        if 0 < k < len(fm) - 1:
            a, b, c = Ym[k - 1], Ym[k], Ym[k + 1]
            den = a - 2 * b + c
            d = 0.5 * (a - c) / den if abs(den) > 1e-12 else 0.0
        else:
            d = 0.0
        peaks.append({"hz": round(float(fm[k] + d * (fm[1] - fm[0])), 3),
                      "db": round(float(Ydb[k]), 1)})
    return peaks


def pitch_track(x: np.ndarray, f0: float, win_ms: float = 30.0,
                hop: int = 256) -> np.ndarray:
    """High-rate pitch trajectory (semi) for modulation FFT."""
    z = x * np.exp(-2j * np.pi * f0 * np.arange(len(x)) / SR)
    w = max(16, int(win_ms * SR / 1000) // 2 * 2 + 1)
    zz = np.convolve(z, np.ones(w) / w, "same")
    idx = np.arange(int(0.3 * SR), max(0, len(x) - int(0.3 * SR)), hop)
    ph = np.unwrap(np.angle(zz[idx]))
    fr = f0 + np.gradient(ph) * (SR / hop) / (2 * np.pi)
    return 12.0 * np.log2(np.maximum(fr, 20.0) / f0)


def traj_stats(semi: np.ndarray, t_skip: float = SKIP,
               dur: float = DUR) -> tuple[float, float]:
    """(depth_semi, rate_hz) of a pitch trajectory: robust p2p/2 + crossings."""
    if len(semi) < int(0.5 * SR):
        return 0.0, 0.0
    lo, hi = float(np.percentile(semi, 2)), float(np.percentile(semi, 98))
    depth = (hi - lo) / 2.0
    d = semi - np.median(semi)
    sign = np.sign(d)
    cross = int(np.sum((sign[1:] * sign[:-1]) < 0))
    rate = cross / 2.0 / max(dur - 2 * t_skip, 1e-6)
    return depth, rate


def cent_stats(c: np.ndarray, dur: float = DUR, hop: int = 2400) -> tuple[float, float]:
    """(depth_db, rate_hz) of a centroid trajectory (in dB of centroid swing)."""
    if len(c) < 5:
        return 0.0, 0.0
    lo, hi = float(np.percentile(c, 5)), float(np.percentile(c, 95))
    depth_db = 20.0 * np.log10(max(hi, 20.0) / max(lo, 20.0))
    d = c - np.median(c)
    sign = np.sign(d)
    cross = int(np.sum((sign[1:] * sign[:-1]) < 0))
    rate = cross / 2.0 / (len(c) * hop / SR)
    return depth_db, rate


def analyse(x: np.ndarray, f0: float) -> dict:
    semi = inst_pitch_semi(x, f0=f0)
    depth, rate = traj_stats(semi)
    cent = centroid_track(x)
    cdb, crate = cent_stats(cent)
    ptraj = pitch_track(x, f0)
    ppeaks = track_peaks(ptraj, frame_rate=SR / 256)
    cpeaks = track_peaks(cent, frame_rate=SR / 2400)
    return {"pitch_depth_semi": round(depth, 3), "pitch_rate_hz": round(rate, 3),
            "cent_depth_db": round(cdb, 2), "cent_rate_hz": round(crate, 3),
            "fpeak_hz": round(fft_peak_hz(x), 1),
            "pitch_mod_peaks": ppeaks, "cent_mod_peaks": cpeaks}


def run() -> None:
    ap_ok = "--fx-off" in sys.argv
    irr = Iridium()
    bl = midi.connect("blofeld")
    try:
        R.load_patch(irr, SLOT)
        if ap_ok:
            # decisive test: mute ALL FX on both sides -> what remains is pure LFO
            from bloridium import blofeld_dump as bd
            from profile_todo_measure import with_overrides, apply_fx
            parsed = bd.parse_sndd((REPO / "dumps/banks/A/A001.bin").read_bytes())
            sd = with_overrides(parsed["sdata"], {128: 0, 144: 0})  # FX1/2 Bypass
            actual = M.load_sndd_actual(bl, sd)
            print(f"BF edit buffer: A001 with FX bypassed "
                  f"(readback {'ok' if actual else 'FAILED'})", flush=True)
            apply_fx(irr, {"kind": "effect"})   # FX1/FX2 dry on the Iridium
        else:
            R.select_blofeld(bl, "A001")
        time.sleep(0.2)
        for note, f0 in ((60, 261.63), (72, 523.25)):
            d = M.capture(bl, irr, note=note, vel=100, dur=DUR, pre=PRE)
            bx = np.mean(d[list(audio.CHANNELS["blofeld"]), :], axis=0)
            ix = np.mean(d[list(audio.CHANNELS["iridium"]), :], axis=0)
            rb, ri = analyse(bx, f0), analyse(ix, f0)
            tag = "_fxoff" if ap_ok else ""
            np.save(REPO / f"recordings/ab_a001_n{note}_bf{tag}.npy", bx)
            np.save(REPO / f"recordings/ab_a001_n{note}_ir{tag}.npy", ix)
            row = {"kind": "row", "loc": "A001", "slot": SLOT, "note": note,
                   "fx_off": ap_ok, "blofeld": rb, "iridium": ri}
            with LOG.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(f"note {note}:", flush=True)
            for side, r in (("BF", rb), ("IR", ri)):
                print(f"  {side}: pitch {r['pitch_depth_semi']:.2f} semi, "
                      f"pitch-mod peaks {r['pitch_mod_peaks']}, "
                      f"centroid {r['cent_depth_db']:.2f} dB, "
                      f"cent-mod peaks {r['cent_mod_peaks']}, "
                      f"f0 {r['fpeak_hz']} Hz", flush=True)
    finally:
        try:
            irr.cmd("load-patch 200", wait=0.6)
        except Exception:
            pass
        irr.close()
        bl.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--fx-off", action="store_true",
                    help="bypass FX1/FX2 on both sides -> pure LFO comparison")
    args = ap.parse_args()
    if args.run:
        run()
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
