#!/usr/bin/env python3
"""Block 5: Glide/Legato sweep.

Plays two overlapping notes (C3 -> C5) and measures the pitch trajectory on both
synths: glide time, linearity and step count. Compare per value.

Run:  python3 scripts/profile_glide_sweep.py
Writes recordings/glide_sweep.jsonl (precomputed rows).
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, blofeld_dump as bd, midi, qpat, qpat_map  # noqa: E402
from _quir import Iridium  # noqa: E402
import _measure as M  # noqa: E402
import profile_init_sweep as P  # noqa: E402

LOG = REPO / "recordings/glide_sweep.jsonl"
SR = audio.SAMPLERATE
NOTE_LO, NOTE_HI = 48, 72
HZ_LO = 130.81


def f0_track(x: np.ndarray, frame: int = 2048, hop: int = 512) -> tuple[np.ndarray, np.ndarray]:
    """Frame-wise f0 (autocorrelation) + clarity, in Hz and 0..1."""
    xs = np.asarray(x, dtype=np.float64)
    n_frames = max(0, (len(xs) - frame) // hop)
    f0 = np.zeros(n_frames)
    clar = np.zeros(n_frames)
    win = np.hanning(frame)
    for i in range(n_frames):
        seg = xs[i * hop:i * hop + frame]
        seg = (seg - seg.mean()) * win
        n = 1 << int(np.ceil(np.log2(2 * len(seg))))
        Y = np.fft.rfft(seg, n=n)
        r = np.fft.irfft(Y * np.conj(Y), n=n)[:len(seg)]
        if r[0] <= 0:
            continue
        r = r / r[0]
        lo, hi = int(SR / 1500), int(SR / 45)
        segr = r[lo:hi]
        if not segr.size:
            continue
        j = int(np.argmax(segr)) + lo
        clar[i] = float(r[j])
        f0[i] = SR / j if j else 0.0
    return f0, clar


def glide_metrics(x: np.ndarray) -> dict:
    f0, clar = f0_track(x)
    if not len(f0):
        return {"valid": False}
    cents = 1200 * np.log2(np.maximum(f0, 1e-6) / HZ_LO)
    cents[f0 < 45] = np.nan
    cents[clar < 0.25] = np.nan
    voiced = np.where(~np.isnan(cents))[0]
    if len(voiced) < 20:
        return {"valid": False}
    # plateaus: first 15 % and last 15 % of the voiced frames before release
    v0, v1 = voiced[0], voiced[-1]
    span = v1 - v0
    c_start = float(np.nanmedian(cents[v0:v0 + max(3, span // 8)]))
    c_end = float(np.nanmedian(cents[v1 - max(3, span // 8):v1]))
    if abs(c_end - c_start) < 400:
        return {"valid": False, "reason": "no interval"}
    rising = c_end > c_start
    thr_lo = c_start + (50 if rising else -50)
    idx = np.arange(len(cents))
    # start of the transition
    t_start = None
    for i in range(v0, v1):
        if np.isnan(cents[i]):
            continue
        if (rising and cents[i] > thr_lo) or (not rising and cents[i] < thr_lo):
            t_start = i
            break
    if t_start is None:
        return {"valid": False, "reason": "no transition"}
    # end: 5 consecutive frames within 20 cents of c_end
    t_end = None
    ok_run = 0
    for i in range(t_start, v1):
        if not np.isnan(cents[i]) and abs(cents[i] - c_end) < 20:
            ok_run += 1
            if ok_run >= 5:
                t_end = i - 4
                break
        else:
            ok_run = 0
    if t_end is None:
        t_end = v1
    glide_ms = (t_end - t_start) * 512 / SR * 1000.0
    # linearity of the transition
    seg = cents[t_start:t_end + 1]
    tt = np.arange(len(seg)) * 512 / SR
    good = ~np.isnan(seg)
    r2 = 0.0
    if good.sum() >= 5:
        a, b = np.polyfit(tt[good], seg[good], 1)
        pred = a * tt[good] + b
        ss = 1 - float(np.sum((seg[good] - pred) ** 2)) / (
            float(np.sum((seg[good] - seg[good].mean()) ** 2)) + 1e-9)
        r2 = max(0.0, min(1.0, ss))
    # rough glissando detection: distinct 100-cent steps with >= 2 frames
    levels = np.round(seg[good] / 100).astype(int)
    steps = 0
    if len(levels) >= 2:
        for lv in np.unique(levels):
            if (levels == lv).sum() >= 2:
                steps += 1
    return {"valid": True, "glide_ms": round(glide_ms, 1), "r2": round(r2, 2),
            "steps": int(steps), "c_start": round(c_start, 0), "c_end": round(c_end, 0)}


def capture_glide(bl, irr, dur: float = 3.6) -> np.ndarray:
    def sched():
        time.sleep(0.55)
        for ch in range(16):
            bl.control_change(123, 0, channel=ch)
            bl.control_change(7, 127, channel=ch)
        irr.silence_part()
        bl.note_on(note=NOTE_LO, velocity=100)
        irr.note_on(note=NOTE_LO, velocity=100)
        time.sleep(0.7)
        bl.note_on(note=NOTE_HI, velocity=100)
        irr.note_on(note=NOTE_HI, velocity=100)
        time.sleep(1.1)
        bl.note_off(note=NOTE_LO)
        bl.note_off(note=NOTE_HI)
        irr.note_off(note=NOTE_LO)
        irr.note_off(note=NOTE_HI)

    th = threading.Thread(target=sched, daemon=True)
    th.start()
    d = audio.record(duration=dur, channels=None)
    th.join()
    return d


def status_for(gb: dict, gi: dict) -> str:
    if not gb.get("valid") or not gi.get("valid"):
        return "n/a"
    b, i = gb["glide_ms"], gi["glide_ms"]
    if b < 30 and i < 30:
        return "n/a"
    if b >= 30 and i < 15:
        return "defekt"
    if b < 30 and i >= 15:
        return "Mismatch"
    ratio = i / max(b, 1.0)
    if 0.6 <= ratio <= 1.6:
        return "OK"
    if 0.33 <= ratio <= 3.0:
        return "teilweise"
    return "Mismatch"


def main() -> int:
    init = P.load_init()
    base_sd = bytes(init["sdata"])
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *base_sd, bd.checksum(base_sd)]
    base_ov, _ = qpat_map.blofeld_to_qpat_params(bd.parse_sndd(bytes([0xF0, *body, 0xF7])))
    init_vals = {k: v["value"] for k, v in qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}

    def base_val(k):
        return base_ov[k][0] if k in base_ov else float(init_vals.get(k, 0.0))

    irr = Iridium()
    bl = midi.connect("blofeld")
    touched = set()
    rows = []
    try:
        if not M.load_sndd_verified(bl, base_sd):
            raise RuntimeError("Init-Dump nicht verifiziert")
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])  # dry
        bases = []
        for _ in range(2):
            d = capture_glide(bl, irr)
            lb, rb = d[2, :], d[3, :]
            li, ri = d[4, :], d[5, :]
            bases.append((float(np.mean(lb)), float(np.mean(li))))
            print("baseline levels", bases[-1], flush=True)

        for idx in (53, 57, 56):
            name = bd.SDATA[idx][0]
            for raw in P.values_for(idx):
                if touched:
                    irr.set_many([(k, base_val(k)) for k in touched])
                    touched = set()
                sd = bytearray(base_sd)
                sd[idx] = raw
                body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
                ov, _ = qpat_map.blofeld_to_qpat_params(bd.parse_sndd(bytes([0xF0, *body, 0xF7])))
                keys = {k: v[0] for k, v in ov.items()
                        if k not in base_ov or abs(v[0] - base_ov[k][0]) > 1e-9}
                if not M.load_sndd_verified(bl, bytes(sd)):
                    raise RuntimeError(f"SNDD-Readback: idx {idx} raw {raw}")
                if keys:
                    irr.set_many(sorted(keys.items()))
                    touched |= set(keys)
                time.sleep(0.2)
                d = capture_glide(bl, irr)
                gb = glide_metrics(np.mean(d[[2, 3], :], axis=0))
                gi = glide_metrics(np.mean(d[[4, 5], :], axis=0))
                st = status_for(gb, gi)
                row = {"kind": "row", "variant": "glide", "precomputed": True,
                       "idx": idx, "param": name, "enum": bd.SDATA[idx][1] is not None,
                       "raw": raw, "status": st,
                       "mag_b": gb.get("glide_ms", 0) / 100.0,
                       "mag_i": gi.get("glide_ms", 0) / 100.0,
                       "cos": None, "iridium_keys": sorted(keys),
                       "glide_b": gb, "glide_i": gi,
                       "time": time.strftime("%H:%M:%S")}
                rows.append(row)
                print(f"  {name:16s} {raw:3d} {st:9s} B {gb.get('glide_ms')}ms "
                      f"(r2 {gb.get('r2')}, steps {gb.get('steps')}) | I "
                      f"{gi.get('glide_ms')}ms (r2 {gi.get('r2')}, steps {gi.get('steps')})",
                      flush=True)
    finally:
        irr.close()
        bl.close()
    with LOG.open("a") as fh:
        fh.write(json.dumps({"kind": "baseline", "variant": "glide", "precomputed": True,
                             "noise": {"levels": bases},
                             "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
