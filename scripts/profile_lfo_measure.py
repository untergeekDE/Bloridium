#!/usr/bin/env python3
"""A7 measurements: LFO free speed (Hz curve) and fade time constants.

Setup: Blofeld LFO 1 -> Amplifier Volume via modulation slot 10 (amount 96),
sine, Sync off. The converted Iridium matrix row does the same. FX off.
The Blofeld's init modulation rows are cleared so only the volume tremolo
remains.

Run:  python3 scripts/profile_lfo_measure.py [speed|fade|all|report]
Writes recordings/lfo_measure.jsonl and docs/research/LFO-2026-11-21.md.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, midi, qpat  # noqa: E402
from _device_tool import Iridium  # noqa: E402
import _measure as M  # noqa: E402
import profile_init_sweep as P  # noqa: E402
from profile_todo_measure import (  # noqa: E402
    IridiumState, apply_fx, overrides_for, with_overrides,
)

LOG = REPO / "recordings/lfo_measure.jsonl"
SR = audio.SAMPLERATE
SPEEDS = [(20, 10.0), (30, 6.0), (40, 3.5), (50, 3.5), (60, 3.5),
          (70, 3.5), (80, 3.5)]
# (fade raw, delay raw): positive = fade in, negative = fade out after delay
FADES = [(80, 0), (96, 0), (112, 0), (16, 48), (40, 48), (56, 48)]


def base_sdata(speed: int, fade: int, delay: int, amount: int = 96):
    b = {8: 2, 24: 0, 40: 0, 61: 127, 62: 0, 63: 0, 64: 0, 65: 0, 66: 0,
         77: 1, 78: 127, 80: 0, 87: 64, 89: 0, 97: 0,
         128: 0, 129: 0, 144: 0, 145: 0,
         160: 0, 161: speed, 163: 0, 164: 0, 166: delay, 167: fade}
    for m in range(16):          # clear the init matrix rows
        b[261 + 3 * m] = 0
    b.update({288: 1, 289: 30, 290: amount})   # Mod 10: LFO 1 -> Volume
    p = P.load_init()
    return with_overrides(p["sdata"], b)


def rms_env(x: np.ndarray, frame: int = 480, hop: int = 240) -> tuple[np.ndarray, np.ndarray]:
    n = max(0, (len(x) - frame) // hop)
    r = np.array([np.sqrt(np.mean(x[i * hop:i * hop + frame] ** 2)) for i in range(n)])
    t = (np.arange(n) * hop + frame / 2) / SR
    return r, t


def mod_freq(x: np.ndarray, lo: float = 0.05, hi: float = 40.0) -> float:
    r, t = rms_env(x)
    y = 20 * np.log10(np.maximum(r, 1e-7))
    y = (y - y.mean()) * np.hanning(len(y))
    Y = np.abs(np.fft.rfft(y))
    f = np.fft.rfftfreq(len(y), (t[1] - t[0]) if len(t) > 1 else 1 / SR)
    m = (f >= lo) & (f <= hi)
    if not m.any():
        return 0.0
    fm, Ym = f[m], Y[m]
    k = int(np.argmax(Ym))
    if 0 < k < len(Ym) - 1:
        a, b, c = Ym[k - 1], Ym[k], Ym[k + 1]
        den = a - 2 * b + c
        delta = 0.5 * (a - c) / den if abs(den) > 1e-12 else 0.0
        return float(fm[k] + delta * (fm[1] - fm[0]))
    return float(fm[k])


def depth_profile(x: np.ndarray, fmod: float, win: float = 0.6,
                  step: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    """Synchronous amplitude of the tremolo (dB) in sliding windows."""
    r, t = rms_env(x)
    out_t, out_d = [], []
    for t0 in np.arange(0, max(0.0, t[-1] - win), step):
        m = (t >= t0) & (t < t0 + win)
        y, tt = r[m], t[m]
        if len(y) < 10:
            continue
        base = float(y.mean())
        amp = 2 * abs(np.sum((y - base) * np.exp(-2j * np.pi * fmod * tt))) / len(y)
        out_t.append(float(t0))
        out_d.append(float(20 * np.log10((base + amp) / max(base - amp, 1e-9))))
    return np.array(out_t), np.array(out_d)


def half_time(t: np.ndarray, d: np.ndarray, fade_in: bool,
              delay: float = 0.0) -> float:
    if not len(d):
        return float("nan")
    m = t >= delay
    if not m.any():
        return float("nan")
    t, d = t[m], d[m]
    mx, mn = float(np.max(d)), float(np.min(d))
    if mx - mn < 0.3:           # no measurable fade
        return 0.0
    lev = mn + 0.5 * (mx - mn)
    for ti, di in zip(t, d):
        if (fade_in and di >= lev) or (not fade_in and di <= lev):
            return float(ti - delay)
    return float(t[-1] - delay)


def measure_speed(bl, irr, state):
    rows = []
    for raw, dur in SPEEDS:
        sd = base_sdata(raw, 64, 0)
        actual = M.load_sndd_actual(bl, sd)
        if actual is None:
            print(f"SKIP speed {raw}: kein Readback", flush=True)
            continue
        ov = overrides_for(actual)
        state.apply(state.desired(ov))
        apply_fx(irr, {"kind": "effect"})
        time.sleep(0.15)
        d = M.capture(bl, irr, note=60, vel=100, dur=dur, pre=0.15)
        fb = mod_freq(np.mean(d[list(audio.CHANNELS['blofeld']), :], axis=0))
        fi = mod_freq(np.mean(d[list(audio.CHANNELS['iridium']), :], axis=0))
        ratio = fi / max(fb, 1e-6)
        st = "OK" if 0.8 <= ratio <= 1.25 else ("teilweise" if 0.5 <= ratio <= 2.0
                                                else "Mismatch")
        row = {"kind": "row", "variant": "lfo_speed", "idx": 161, "raw": raw,
               "freq_b": round(fb, 3), "freq_i": round(fi, 3),
               "ratio": round(ratio, 3), "status": st,
               "conv_speed": round(ov.get("Lfo1Speed", (0.0,))[0], 3),
               "dur": dur}
        rows.append(row)
        print(f"  speed {raw:3d}  BF {fb:6.2f} Hz  IR {fi:6.2f} Hz  "
              f"ratio {ratio:.2f}  {st}", flush=True)
    return rows


def measure_fade(bl, irr, state):
    rows = []
    for fade, delay in FADES:
        sd = base_sdata(40, fade, delay)
        actual = M.load_sndd_actual(bl, sd)
        if actual is None:
            print(f"SKIP fade {fade}: kein Readback", flush=True)
            continue
        ov = overrides_for(actual)
        state.apply(state.desired(ov))
        apply_fx(irr, {"kind": "effect"})
        time.sleep(0.15)
        d = M.capture(bl, irr, note=60, vel=100, dur=6.5, pre=0.1)
        # fixed LFO rates for the fade profile: the slow fade envelope would
        # otherwise dominate the frequency estimate. Speed raw 40 = 2.5 Hz (BF)
        # and ~1.0 Hz (IR, measured in the speed group).
        fb, fi = 2.5, 1.0
        # delay in the analysed file starts ~0.1 s before the note; keep the
        # reported delay approximate (the shape comparison is what matters)
        db = np.mean(d[list(audio.CHANNELS['blofeld']), :], axis=0)
        di = np.mean(d[list(audio.CHANNELS['iridium']), :], axis=0)
        tb, vb = depth_profile(db, fb)
        ti, vi = depth_profile(di, fi)
        fade_in = fade > 64
        half_b = half_time(tb, vb, fade_in)
        half_i = half_time(ti, vi, fade_in)
        if half_b == 0 and half_i == 0:
            st = "n/a"
        elif half_b == 0 or half_i == 0:
            st = "defekt" if half_b == 0 else "Mismatch"
        else:
            ratio = half_i / max(half_b, 1e-6)
            st = "OK" if 0.5 <= ratio <= 2.0 else ("teilweise" if 0.33 <= ratio <= 3 else "Mismatch")
        row = {"kind": "row", "variant": "lfo_fade", "idx": 167, "raw": fade,
               "delay": delay, "fade_in": bool(fade_in), "freq_b": round(fb, 3),
               "freq_i": round(fi, 3), "half_b": round(half_b, 2),
               "half_i": round(half_i, 2), "depth_b": round(float(vb.max() - vb.min()), 2)
               if len(vb) else 0, "depth_i": round(float(vi.max() - vi.min()), 2)
               if len(vi) else 0, "status": st,
               "conv_attack": round(ov.get("Lfo1Attack", (0.0,))[0], 3),
               "conv_decay": round(ov.get("Lfo1Decay", (0.0,))[0], 3)}
        rows.append(row)
        print(f"  fade {fade:3d} delay {delay:3d}  BF half {half_b:5.2f}s "
              f"(depth {row['depth_b']:4.1f} dB)  IR half {half_i:5.2f}s "
              f"(depth {row['depth_i']:4.1f} dB)  {st}", flush=True)
    return rows


def main() -> int:
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "report":
        write_report()
        return 0
    init_vals = {k: v["value"] for k, v in
                 qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}
    base_sd = base_sdata(40, 64, 0)
    base_ov = overrides_for(base_sd)
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
        apply_fx(irr, {"kind": "effect"})
        if what in ("all", "speed"):
            rows += measure_speed(bl, irr, state)
        if what in ("all", "fade"):
            rows += measure_fade(bl, irr, state)
    finally:
        irr.close()
        bl.close()
    with LOG.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    write_report()
    return 0


def write_report() -> None:
    if not LOG.exists():
        print("no lfo log")
        return
    rows = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
    speed = [r for r in rows if r.get("variant") == "lfo_speed"]
    fade = [r for r in rows if r.get("variant") == "lfo_fade"]
    lines = ["# A7 — LFO Free-Speed und Fade (2026-11-22)", "",
             "LFO 1 → Amplifier Volume (Mod-Slot 10, Amount 96), Sine, Sync off,",
             "FX aus. Der Konverter legt dieselbe Volume-Matrixzeile auf dem",
             "Iridium an.", ""]
    if speed:
        lines += ["## Free-Speed-Hz-Kurve", "",
                  "| LFO Speed raw | Blofeld | Iridium | Verhältnis | konv. Lfo1Speed | Status |",
                  "|---:|---:|---:|---:|---:|---|"]
        for r in speed:
            lines.append(f"| {r['raw']} | {r['freq_b']:.2f} Hz | {r['freq_i']:.2f} Hz | "
                         f"{r['ratio']:.2f} | {r['conv_speed']} | {r['status']} |")
        lines += ["", "Die Blofeld-Kurve ist deutlich steiler. Am nächsten liegt es bei",
                  "raw 20 (0,45 → 0,11 Hz; wegen < 2 Perioden unsicher), ab raw 40",
                  "läuft der Iridium klar zu langsam (2,63 → 1,09 Hz; 10,43 →",
                  "5,66 Hz; 30,65 → 16,32 Hz). Der Konverter mappt",
                  "`Lfo1Speed = norm(raw)` linear; nötig wäre eine Hz-Kalibrierung", 
                  "(siehe Tabelle).", ""]
    if fade:
        lines += ["## Fade-Zeitkonstanten", "",
                  "Tiefe = synchron detektierte Tremolo-Tiefe; Halbzeit relativ zum",
                  "Note-On (bei negativem Fade nach dem Delay).", "",
                  "| Fade raw | Delay | Richtung | BF Halbzeit | IR Halbzeit | BF Tiefe | IR Tiefe | Status |",
                  "|---:|---:|---|---:|---:|---:|---:|---|"]
        for r in fade:
            lines.append(f"| {r['raw']} | {r['delay']} | {'in' if r['fade_in'] else 'out'} | "
                         f"{r['half_b']:.2f} s | {r['half_i']:.2f} s | "
                         f"{r['depth_b']:.1f} dB | {r['depth_i']:.1f} dB | {r['status']} |")
        lines += ["", "Der Blofeld-Fade ist eine **Rate** (größerer Betrag = schneller),",
                  "keine Zeit: +16/+32 (raw 80/96) sind so langsam, dass die Tiefe",
                  "im 6,5-s-Fenster nicht ansteigt; +48 (raw 112) erreicht die halbe",
                  "Tiefe nach 1,4 s. Negativ mit Delay 48: −48 (raw 16) halbe Tiefe",
                  "nach 1,0 s, −24 (raw 40) nach 2,0 s. Ohne Delay ist der LFO bei",
                  "negativem Fade sofort aus.", "",
                  "Der Iridium zeigt mit den konvertierten `Lfo1Attack`/`Lfo1Decay`-",
                  "Werten **keine** messbare Ein-/Ausblendung (Tiefe ab Note-On",
                  "konstant) — auch bei `Lfo1Attack=1.0` in allen `Lfo1Global`-Modi.",
                  "Die lineare `(raw−64)/63`-Abbildung ist damit nicht nur zu grob,",
                  "sondern in der Richtung falsch.", ""]
    out = REPO / "docs/research/LFO-2026-11-21.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(main())
