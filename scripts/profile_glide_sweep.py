#!/usr/bin/env python3
"""Block 5: Glide/Legato sweep (mono setup, YIN pitch tracker).

Plays C3 -> (gap or legato) -> C5 and measures the pitch trajectory on both
synths: glide time, linearity, start pitch and (for Glissando) semitone steps.

Setup notes:
- Blofeld: Allocation = Mono (bit 0), Glide = On, Mode = Portamento.
  In mono mode a released note still provides the start pitch, so the second
  note can be played non-legato.
- Iridium: GlideOnOff/GlideRate come from the converter. The converter does not
  map the Blofeld Glide Mode, so the Iridium is left at GlideType = Onset
  (continuous glide). That is exactly what this sweep verifies.
- FX is off for every take.

Run:  python3 scripts/profile_glide_sweep.py            # measure
      python3 scripts/profile_glide_sweep.py report     # Markdown summary
Writes recordings/glide_sweep.jsonl, recordings/glide/*.npy and
docs/GLIDE-2026-11-21.md.
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

from bloridium import audio, blofeld_dump as bd, midi, qpat  # noqa: E402
from _quir import Iridium  # noqa: E402
import _measure as M  # noqa: E402
import profile_init_sweep as P  # noqa: E402
from profile_todo_measure import (  # noqa: E402
    IridiumState, apply_fx, dry_settings, overrides_for, with_overrides,
)

OUT = REPO / "recordings/glide"
LOG = REPO / "recordings/glide_sweep.jsonl"
SR = audio.SAMPLERATE
NOTE_LO, NOTE_HI = 48, 72
HZ_LO = 130.81           # C3
TARGET_CENTS = 1200 * np.log2(523.25 / HZ_LO)   # C5 ≈ 2400 cents
HOP, FRAME = 256, 2048

# Base sound: Osc 1 saw, open filter, mono, glide on, Portamento, rate 64.
BASE = {8: 2, 24: 0, 40: 0, 61: 127, 62: 0, 63: 0, 64: 0, 65: 0, 66: 0,
        77: 1, 78: 127, 80: 0, 87: 64, 89: 0, 97: 0,   # 87=64: env amount neutral
        128: 0, 129: 0, 144: 0, 145: 0,
        58: 1, 53: 1, 56: 0, 57: 64}

MODES = {
    "glide": dict(param=53, values=[0, 1], rate=64, mode=0),
    "rate": dict(param=57, values=[20, 50, 70, 85], rate=None, mode=0, hold=3.4),
    "mode": dict(param=56, values=[0, 1, 2, 3], rate=70, mode=None,
                 rates={0: 50, 1: 50, 2: 70, 3: 70}),
    # fingered modes played staccato: Blofeld must NOT glide, Iridium Onset does
    "mode_staccato": dict(param=56, values=[1, 3], rate=50, mode=None,
                          rates={1: 50, 3: 50}, overlap=False),
}


# ---------------------------------------------------------------- YIN
def yin_track(x: np.ndarray, fmin: float = 65, fmax: float = 1400,
              thr: float = 0.12) -> tuple[np.ndarray, np.ndarray]:
    """Frame-wise YIN f0 + clarity. Frame-centred timestamps are returned."""
    x = np.asarray(x, dtype=np.float64)
    nfr = max(0, (len(x) - FRAME) // HOP)
    tmin, tmax = max(2, int(SR / fmax)), min(FRAME - 1, int(SR / fmin))
    f0 = np.full(nfr, np.nan)
    clar = np.zeros(nfr)
    win = np.hanning(FRAME)
    for i in range(nfr):
        seg = x[i * HOP:i * HOP + FRAME]
        seg = (seg - seg.mean()) * win
        n = 1
        while n < 2 * FRAME:
            n *= 2
        X = np.fft.rfft(seg, n)
        r = np.fft.irfft(X * np.conj(X), n)[:FRAME]
        c = np.concatenate([[0.0], np.cumsum(seg * seg)])
        tt = np.arange(1, tmax)
        d = np.zeros(tmax)
        d[1:] = c[FRAME - tt] + (c[FRAME] - c[tt]) - 2 * r[1:tmax]
        d = np.maximum(d, 0)
        cm = np.ones(tmax)
        run = np.cumsum(d[1:])
        cm[1:] = d[1:] / (run / np.arange(1, tmax) + 1e-12)
        idx = None
        for t in range(tmin, tmax - 1):
            if cm[t] < thr and cm[t] <= cm[t - 1] and cm[t] <= cm[t + 1]:
                idx = t
                break
        if idx is None:
            idx = tmin + int(np.argmin(cm[tmin:tmax]))
        if 0 < idx < tmax - 1:
            a, b, cc = cm[idx - 1], cm[idx], cm[idx + 1]
            den = a - 2 * b + cc
            tau = idx + (0.5 * (a - cc) / den if abs(den) > 1e-12 else 0.0)
        else:
            tau = float(idx)
        f0[i] = SR / tau
        clar[i] = 1.0 - cm[idx]
    return f0, clar


def rms_frames(x: np.ndarray, frame: int = 1024, hop: int = 256) -> np.ndarray:
    n = max(0, (len(x) - frame) // hop)
    return np.array([np.sqrt(np.mean(x[i * hop:i * hop + frame] ** 2))
                     for i in range(n)])


def glide_metrics(x: np.ndarray, onset_s: float, target: float = TARGET_CENTS,
                  window: float = 2.4) -> dict:
    """Pitch trajectory of the second note starting at onset_s (seconds)."""
    f0, clar = yin_track(x)
    cents = 1200 * np.log2(np.maximum(f0, 1e-9) / HZ_LO)
    times = (np.arange(len(f0)) * HOP + FRAME / 2) / SR
    # level gate: drop the release tail and low-level tracker garbage
    lev = rms_frames(x, frame=FRAME, hop=HOP)
    lev = np.pad(lev, (0, max(0, len(f0) - len(lev))))[:len(f0)]
    gate = lev > 0.15 * float(np.percentile(lev, 90)) if len(lev) else True
    good = (clar > 0.45) & (f0 > 65) & (f0 < 1200) & gate
    cents[~good] = np.nan

    i0 = int((onset_s * SR - FRAME / 2) / HOP)
    if i0 < 0:
        i0 = 0
    # keep the first 1.4 s of the second note
    i1 = min(len(cents), i0 + int(window * SR / HOP))
    seg = cents[i0:i1]
    voiced = np.where(~np.isnan(seg))[0]
    if len(voiced) < 15:
        return {"valid": False, "reason": "too few voiced frames"}

    # start pitch: first 4 voiced frames
    c_start = float(np.nanmedian(seg[voiced[:4]]))
    # end pitch: last 0.3 s of voiced frames (the window may run into the release)
    tail = seg[max(0, voiced[-1] - int(0.3 * SR / HOP)):voiced[-1] + 1]
    c_end = float(np.nanmedian(tail))
    if np.isnan(c_end):
        return {"valid": False, "reason": "no end pitch"}
    depth = c_end - c_start
    if abs(depth) < 250:
        return {"valid": False, "reason": "no interval", "c_start": round(c_start),
                "c_end": round(c_end), "depth": round(depth)}

    rising = depth > 0
    # first frame after onset where the pitch is within 50 cents of c_end and stays
    t_end = None
    run = 0
    for j in range(voiced[0], len(seg)):
        if not np.isnan(seg[j]) and abs(seg[j] - c_end) < 50:
            run += 1
            if run >= 3:
                t_end = j - 2
                break
        else:
            run = 0
    if t_end is None:
        t_end = voiced[-1]
    glide_ms = max(0.0, (t_end - voiced[0]) * HOP / SR * 1000.0)

    # linearity of the transition
    tt = np.arange(len(seg)) * HOP / SR
    m = ~np.isnan(seg) & (np.arange(len(seg)) >= voiced[0]) & (np.arange(len(seg)) <= t_end)
    r2 = 0.0
    if m.sum() >= 6:
        a, b = np.polyfit(tt[m], seg[m], 1)
        pred = a * tt[m] + b
        r2 = 1 - float(np.sum((seg[m] - pred) ** 2)) / (
            float(np.sum((seg[m] - seg[m].mean()) ** 2)) + 1e-9)
        r2 = max(0.0, min(1.0, r2))

    # semitone plateaus (Glissando detection): 3 frames within ±30 cents of a
    # semitone centre. A continuous glide passes through the bins too fast.
    trans = seg[voiced[0]:t_end + 1]
    plateaus = set()
    for j in range(len(trans) - 4):
        w = trans[j:j + 5]
        if np.any(np.isnan(w)):
            continue
        slope = float(np.polyfit(np.arange(5), w, 1)[0])
        if abs(slope) < 0.3 and float(np.ptp(w)) < 25:
            plateaus.add(int(round(float(np.median(w)) / 100)))
    steps = len(plateaus)

    return {"valid": True, "glide_ms": round(glide_ms, 1), "r2": round(r2, 2),
            "steps": int(steps), "c_start": round(c_start), "c_end": round(c_end),
            "depth": round(depth), "rising": bool(rising)}


# ---------------------------------------------------------------- capture
def capture(bl, irr, overlap: bool, dur: float = 4.2, hold: float = 2.6) -> np.ndarray:
    def sched():
        time.sleep(0.45)
        for ch in range(16):
            bl.control_change(123, 0, channel=ch)
            bl.control_change(7, 127, channel=ch)
        irr.silence_part()
        time.sleep(0.05)
        bl.note_on(note=NOTE_LO, velocity=100)
        irr.note_on(note=NOTE_LO, velocity=100)
        time.sleep(0.55)
        if overlap:                       # legato: C5 before C3 is released
            bl.note_on(note=NOTE_HI, velocity=100)
            irr.note_on(note=NOTE_HI, velocity=100)
            time.sleep(0.06)
            bl.note_off(note=NOTE_LO)
            irr.note_off(note=NOTE_LO)
        else:                             # release, short gap, then C5
            bl.note_off(note=NOTE_LO)
            irr.note_off(note=NOTE_LO)
            time.sleep(0.12)
            bl.note_on(note=NOTE_HI, velocity=100)
            irr.note_on(note=NOTE_HI, velocity=100)
        time.sleep(hold)
        bl.note_off(note=NOTE_HI)
        irr.note_off(note=NOTE_HI)

    th = threading.Thread(target=sched, daemon=True)
    th.start()
    try:
        d = audio.record(duration=dur, channels=None)
    finally:
        th.join()
    return d


def first_onset(x: np.ndarray) -> float:
    """Time (s) of the first clear note onset."""
    r = rms_frames(x)
    if not len(r):
        return 0.0
    mx = float(np.percentile(r, 99))
    if mx <= 0:
        return 0.0
    th = 0.25 * mx
    for i in range(3, len(r) - 4):
        if r[i] > th and r[i - 1] <= th and r[i:i + 4].min() > 0.15 * mx:
            return (i * 256 + 512) / SR
    return 0.0


def second_onset(x: np.ndarray, overlap: bool) -> float:
    """Onset of the second note (gap end for staccato, schedule for legato).

    The legato case is analysed from the moment C3 is released (~60 ms after
    C5 starts), so both devices are monophonic again.
    """
    r = rms_frames(x)
    if len(r):
        mx = float(np.percentile(r, 99))
        if mx > 0 and not overlap:
            silent = r < 0.05 * mx
            i = 0
            while i < len(silent):
                if silent[i]:
                    j = i
                    while j < len(silent) and silent[j]:
                        j += 1
                    if j - i >= 4 and 0.25 < i * 256 / SR < 2.0:
                        return (j * 256 + 512) / SR
                    i = j
                else:
                    i += 1
    # overlap: C3 is released 0.06 s after C5 starts (+ a small tracker margin)
    return first_onset(x) + (0.65 if overlap else 0.67)


def overlap_onset(x: np.ndarray) -> float:
    """First frame where the pitch leaves C3 (start of the legato glide)."""
    f0, clar = yin_track(x)
    c = 1200 * np.log2(np.maximum(f0, 1e-9) / HZ_LO)
    c[clar < 0.45] = np.nan
    t = (np.arange(len(c)) * HOP + FRAME / 2) / SR
    for i in range(8, len(c) - 4):
        if np.isnan(c[i]):
            continue
        bs, as_ = c[i - 5:i], c[i:i + 3]
        if np.all(np.isnan(bs)) or np.all(np.isnan(as_)):
            continue
        before, after = np.nanmedian(bs), np.nanmedian(as_)
        if not np.isnan(before) and not np.isnan(after) \
                and before < 120 and after > 250:
            return float(t[i])
    return first_onset(x) + 0.55


# ---------------------------------------------------------------- status
def status_for(gb: dict, gi: dict, mode: int | None) -> str:
    if not gb.get("valid") and not gi.get("valid"):
        return "n/a"
    if gb.get("valid") and not gi.get("valid"):
        return "defekt"
    if not gb.get("valid") and gi.get("valid"):
        return "Mismatch"
    # glissando modes: the Blofeld must step, the Iridium currently glides
    if mode in (2, 3):
        if gb["steps"] >= 3 and gi["steps"] <= 1:
            return "Mismatch"
        if gb["steps"] >= 3 and gi["steps"] >= 3:
            return "OK"
    ratio = gi["glide_ms"] / max(gb["glide_ms"], 1.0)
    if 0.6 <= ratio <= 1.6:
        return "OK"
    if 0.33 <= ratio <= 3.0:
        return "teilweise"
    return "Mismatch"


# ---------------------------------------------------------------- driver
def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        write_report()
        return 0
    only = sys.argv[1] if len(sys.argv) > 1 else None
    groups = [only] if only else list(MODES)
    for g in groups:
        if g not in MODES:
            raise SystemExit(f"unknown group {g!r}; choose from {', '.join(MODES)}")

    init = P.load_init()
    base_sd = with_overrides(init["sdata"], {**BASE, 56: 0, 57: 64})
    base_ov = overrides_for(base_sd)
    init_vals = {k: v["value"] for k, v in
                 qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}
    OUT.mkdir(parents=True, exist_ok=True)
    LOG.unlink(missing_ok=True)

    irr = Iridium()
    bl = midi.connect("blofeld")
    state = IridiumState(irr, base_ov, init_vals)
    rows = []
    try:
        if M.load_sndd_actual(bl, base_sd) is None:
            raise RuntimeError("Basis-Dump nicht geladen")
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        time.sleep(0.6)
        apply_fx(irr, {"kind": "effect"})   # FX off, verified
        irr.set_many([("GlideType", 0.0)])  # Iridium Onset (converter maps no mode)

        for g in groups:
            cfg = MODES[g]
            idx = cfg["param"]
            name = bd.SDATA[idx][0]
            for raw in cfg["values"]:
                sd = with_overrides(base_sd, {idx: raw})
                rate = cfg.get("rates", {}).get(raw, cfg.get("rate"))
                if rate is not None:
                    sd = with_overrides(sd, {57: rate})
                actual = M.load_sndd_actual(bl, sd)
                if actual is None:
                    print(f"  SKIP {name} {raw}: kein Readback", flush=True)
                    continue
                target_ov = overrides_for(actual)
                state.apply(state.desired(target_ov))
                apply_fx(irr, {"kind": "effect"})
                irr.set_many([("GlideType", 0.0)])
                time.sleep(0.2)
                mode = cfg["mode"] if cfg["mode"] is not None else raw
                overlap = cfg["overlap"] if "overlap" in cfg else mode in (1, 3)
                hold = cfg.get("hold", 2.6)
                d = capture(bl, irr, overlap, dur=hold + 1.9, hold=hold)
                np.save(OUT / f"{idx:03d}_{raw:03d}.npy", d)
                xb = np.mean(d[list(audio.CHANNELS['blofeld']), :], axis=0)
                xi = np.mean(d[list(audio.CHANNELS['iridium']), :], axis=0)
                win = max(1.0, hold - 0.4)
                if overlap:
                    # both: start where the pitch leaves C3 (Iridium after C3 release)
                    gb = glide_metrics(xb, overlap_onset(xb), window=win)
                    gi = glide_metrics(xi, overlap_onset(xi), window=win)
                else:
                    gb = glide_metrics(xb, second_onset(xb, False), window=win)
                    gi = glide_metrics(xi, second_onset(xi, False), window=win)
                st = status_for(gb, gi, mode)
                row = {"kind": "row", "variant": "glide", "precomputed": True,
                       "idx": idx, "param": name, "enum": bd.SDATA[idx][1] is not None,
                       "raw": raw, "status": st,
                       "mag_b": gb.get("glide_ms", 0) / 100.0,
                       "mag_i": gi.get("glide_ms", 0) / 100.0,
                       "iridium_keys": sorted(state.desired(target_ov)),
                       "glide_b": gb, "glide_i": gi, "mode": mode,
                       "overlap": overlap,
                       "time": time.strftime("%H:%M:%S")}
                rows.append(row)
                print(f"  {name:14s} {raw:3d} mode {mode} {st:9s} | "
                      f"B {gb.get('glide_ms')}ms (start {gb.get('c_start')}c, "
                      f"steps {gb.get('steps')}) | I {gi.get('glide_ms')}ms "
                      f"(start {gi.get('c_start')}c, steps {gi.get('steps')})", flush=True)
    finally:
        irr.close()
        bl.close()

    with LOG.open("a") as fh:
        fh.write(json.dumps({"kind": "baseline", "variant": "glide", "precomputed": True,
                             "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    write_report()
    print("done")
    return 0


# ---------------------------------------------------------------- report
def write_report() -> None:
    if not LOG.exists():
        print("no glide log")
        return
    rows = [json.loads(l) for l in LOG.read_text().splitlines()
            if l.strip() and json.loads(l).get("kind") == "row"]
    lines = ["# Block 5 — Glide/Legato (2026-11-21)", "",
             "Mono-Setup: Blofeld Allocation = Mono, Glide Mode = Portamento;",
             "Iridium Glide = On, GlideType = Onset (der Konverter mappt den",
             "Blofeld-Modus nicht). C3 → C5, trocken (FX aus).", "",
             "| Parameter | raw | Modus | Anschlag | Start BF/IR | Glide BF | Glide IR | R² BF | Steps BF/IR | Status |",
             "|---|---:|---|---|---|---:|---:|---:|---|---|"]
    for r in rows:
        gb, gi = r.get("glide_b", {}), r.get("glide_i", {})
        sb = f"{gb.get('c_start', '-')}c" if gb.get("valid") else "–"
        si = f"{gi.get('c_start', '-')}c" if gi.get("valid") else "–"
        tb = f"{gb.get('glide_ms', 0):.0f} ms" if gb.get("valid") else "–"
        ti = f"{gi.get('glide_ms', 0):.0f} ms" if gi.get("valid") else "–"
        art = "legato" if r.get("overlap") else "staccato"
        lines.append(f"| {r['param']} | {r['raw']} | {r.get('mode')} | {art} | "
                     f"{sb} / {si} | {tb} | {ti} | {gb.get('r2', '–')} | "
                     f"{gb.get('steps', '–')}/{gi.get('steps', '–')} | {r['status']} |")

    lines += ["", "## Glide-Rate-Kalibrierung", "",
              "Blofeld, gemessen mit derselben C3→C5-Prozedur:", "",
              "| Glide Rate raw | gemessene Glide-Zeit |", "|---:|---:|",
              "| 50 | 155 ms |", "| 64 | 592 ms |", "| 70 | 1013 ms |",
              "| 85 | 2117 ms |", "| 127 | ≈ 5 s (Handbuch, nicht ausgemessen) |", "",
              "Iridium, `GlideRate` direkt gesetzt (ohne Konverter):", "",
              "| GlideRate norm | gemessene Glide-Zeit |", "|---:|---:|",
              "| 0,30 | 139 ms |", "| 0,40 | 267 ms |", "| 0,50 | 379 ms |",
              "| 0,60 | 608 ms |", "| 0,75 | 896 ms |", "| 0,90 | 1349 ms |",
              "| 1,00 | 1600 ms |", "",
              "Aktueller Konverter (`glide_rate_norm`): raw 50 → 0,312 (OK),",
              "64 → 0,387 (0,43×), 70 → 0,419 (0,31×), 85 → 0,500 (0,18×).",
              "Empfehlung für die Fix-Session (gleiche Zeit, soweit erreichbar):",
              "raw 50 → ~0,32, 64 → ~0,59, 70 → ~0,79, ab 85 → 1,0.",
              "Das Iridium-Maximum liegt bei ~1,6 s; die Blofeld-Zeiten ab raw 85",
              "(2,1 s … 5 s) sind damit **nicht** 1:1 erreichbar.", "",
              "## Befunde", "",
              "- **Glide on/off:** aus = beide springen direkt auf C5 (n/a);",
              "  ein = beide gleiten (BF 592 ms / IR 256 ms, teilweise).",
              "- **Glide Rate:** raw 50 OK (155/144 ms); ab raw 70 ist der Blofeld",
              "  deutlich langsamer als der konvertierte Iridium-Wert",
              "  (raw 70: 1013/315 ms, raw 85: 2117/384 ms). Die Blofeld-Zeitkurve",
              "  des Konverters unterschätzt den mittleren/hohen Bereich.",
              "- **Glide Mode:** Portamento OK. fingered P gleitet auf beiden",
              "  (legato; teilweise wegen des Rate-Versatzes). Glissando und",
              "  fingered G erzeugen auf dem Blofeld hörbare Halbtonschritte",
              "  (Steps 6/14), der Iridium gleitet durchgehend (Steps 0) — der",
              "  Modus wird nicht übertragen.",
              "- **Staccato + fingered:** der Blofeld gleitet nicht (Start C5),",
              "  der Iridium (Onset) gleitet trotzdem → Mismatch. Ursache: Der",
              "  Iridium hat keine Mono-Allocation und keinen fingered-Modus.",
              ""]
    out = REPO / "docs/GLIDE-2026-11-21.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(main())
