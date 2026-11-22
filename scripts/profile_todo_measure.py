#!/usr/bin/env python3
"""Measurements from TODO_MEASURE.md (A1 pulse, A3 FX split, A4 unison width).

This script only measures; it does not change the converter. It produces
recordings/todo_measure_<group>.jsonl and, with `report`, a Markdown summary.

Groups:
  pulse_amt    A1 positive case: Osc 2 = Pulse, PWM source LFO 1, sweep amount.
  fx1types     A3 split: FX1 only (FX2 off), sweep Effect 1 type + mix.
  reverb       A3 split: FX1 off, FX2 = Reverb, sweep Effect 2 mix; tail metric.
  unison_detune A4: 5 voices, sweep Unisono Detune; spectral width at C4.
  unison_count  A4: detune 127, sweep 0/2/4/8 voices; spectral width at C4.

Run:  python3 scripts/profile_todo_measure.py <group>|all
      python3 scripts/profile_todo_measure.py report
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mido  # noqa: E402

from bloridium import audio, blofeld_dump as bd, midi, qpat, qpat_map  # noqa: E402
from _quir import Iridium  # noqa: E402
import _measure as _M  # noqa: E402
import profile_init_sweep as P  # noqa: E402

OUT = REPO / "recordings/todo"
SR = audio.SAMPLERATE
C4 = 261.63
WIDTH_LO, WIDTH_HI = C4 - 55, C4 + 55   # ±55 Hz around C4 (matches TODO_MEASURE table)

SOUND = {  # audible dry base sound: Osc 1 saw only
    8: 2, 17: 64, 18: 64, 19: 64, 24: 0, 40: 0,
    61: 127, 62: 0, 63: 0, 64: 0, 65: 0, 66: 0,
    128: 0, 129: 0, 144: 0, 145: 0,
}
# wide-open filter so PWM harmonics stay audible (init filter env closes fast)
OPEN = {77: 1, 78: 127, 80: 0, 87: 0, 89: 0, 97: 0}

GROUPS = {
    "pulse_amt": dict(
        kind="effect", prefix="toa_",
        # Fade must be 64 (center): raw 0 fades the LFO out immediately, so the
        # first pulse run measured no Blofeld PWM at all.
        variant={**SOUND, **OPEN, 8: 0, 24: 1, 25: 64, 26: 1, 27: 64,
                 62: 0, 63: 127, 64: 0, 65: 0, 66: 0,
                 160: 0, 161: 20, 163: 0, 166: 0, 167: 64},
        params=[27], values={27: [0, 32, 64, 127]}, dur=2.0),
    "fx1types": dict(
        kind="effect", prefix="tof_", fx_policy="fx1",
        variant={**SOUND, 128: 3, 129: 127, 130: 40, 131: 80},
        params=[128, 129], values={128: list(range(6)), 129: [0, 32, 64, 127]},
        dur=2.0),
    "fx2types": dict(
        kind="reverb", prefix="to2_", fx_policy="fx2_mapped", takes=2,
        variant={**SOUND, **OPEN, 128: 0, 144: 0, 145: 127, 146: 80,
                 147: 64, 148: 100, 150: 100, 151: 80, 217: 0, 205: 0},
        params=[144], values={144: [0, 6, 7, 8]}),
    "reverb": dict(
        kind="reverb", prefix="tor_",
        variant={**SOUND, **OPEN,
                 128: 0, 144: 8, 145: 0, 147: 64, 148: 100,
                 217: 0, 205: 0},
        params=[145], values={145: [0, 32, 64, 127]}, takes=2),
    "unison_detune": dict(
        kind="width", prefix="tou_",
        variant={**SOUND, **OPEN, 58: 0x40, 59: 0, 217: 0},
        params=[59], values={59: [0, 32, 64, 127]}, takes=2, dur=3.2),
    "unison_count": dict(
        kind="width", prefix="toc_",
        variant={**SOUND, **OPEN, 58: 0x00, 59: 127, 217: 0},
        params=[58], values={58: [0, 16, 32, 48, 64, 80, 96, 112]},
        takes=2, dur=3.2),
}


# ---------------------------------------------------------------- helpers
def with_overrides(sd: bytes, over: dict) -> bytes:
    out = bytearray(sd)
    for k, v in over.items():
        out[k] = v & 0x7F
    return bytes(out)


def overrides_for(sd: bytes):
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd]
    body.append(bd.checksum(bytes(sd)))
    parsed = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
    return qpat_map.blofeld_to_qpat_params(parsed)[0]


def base_values() -> dict:
    return {k: v["value"] for k, v in qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}


def dry_settings(cfg: dict) -> list[tuple[str, float]]:
    """FX state around a measurement: silence FX that are not under test."""
    policy = cfg.get("fx_policy", "fx2" if cfg["kind"] == "reverb" else "dry")
    if policy == "fx1":      # measure FX1 only
        return [("FX2Type", 0.0), ("FX2Bypass", 0.0), ("FXTotalDryWet", 1.0)]
    if policy == "fx2":      # measure FX2 (reverb) only
        return [("FX1Type", 0.0), ("FX2Type", 6.0), ("FX2Bypass", 0.0),
                ("FXTotalDryWet", 1.0)]
    if policy == "fx2_mapped":  # FX2 type comes from the converter, keep it
        return [("FX1Type", 0.0), ("FX2Bypass", 0.0), ("FXTotalDryWet", 1.0)]
    return [("FX1Type", 0.0), ("FX2Type", 0.0), ("FX1Bypass", 0.0), ("FX2Bypass", 0.0)]


def apply_fx(irr, cfg: dict) -> None:
    """Apply and verify the FX state (FX changes are occasionally swallowed)."""
    policy = cfg.get("fx_policy", "fx2" if cfg["kind"] == "reverb" else "dry")
    checks = {"fx1": [("FX2Type", 0.0)], "fx2": [("FX1Type", 0.0), ("FX2Type", 6.0)],
              "fx2_mapped": [("FX1Type", 0.0)],
              "dry": [("FX1Type", 0.0), ("FX2Type", 0.0)]}[policy]
    for _attempt in range(3):
        irr.set_many(dry_settings(cfg))
        time.sleep(0.12)
        try:
            if all(abs(irr.get(k) - v) < 1e-6 for k, v in checks):
                return
        except Exception:
            pass
    print(f"  WARN: FX state not confirmed ({checks})", flush=True)


class IridiumState:
    """Apply the converter diff for one Blofeld state, undoing rows that disappear."""

    def __init__(self, irr, base_ov: dict, init_vals: dict):
        self.irr, self.base_ov, self.init_vals = irr, base_ov, init_vals
        self.managed: dict[str, float] = {}

    def base_val(self, key: str) -> float:
        return self.base_ov[key][0] if key in self.base_ov else float(self.init_vals.get(key, 0.0))

    def desired(self, target_ov: dict) -> dict:
        d = {k: v[0] for k, v in target_ov.items()
             if k not in self.base_ov or abs(v[0] - self.base_ov[k][0]) > 1e-9}
        # Matrix rows that existed in the base state but not in the target -> switch off.
        for k in self.base_ov:
            if k in target_ov:
                continue
            if k.startswith("MatrixOnOff"):
                d[k] = 0.0
            elif not k.startswith("Matrix"):
                d[k] = self.base_val(k)
        return d

    def apply(self, desired: dict) -> None:
        to_set = {}
        for k, v in desired.items():
            if k not in self.managed or abs(self.managed[k] - v) > 1e-9:
                to_set[k] = v
                self.managed[k] = v
        for k in list(self.managed):
            if k in desired:
                continue
            if k.startswith("MatrixOnOff"):
                v = 0.0
            elif k.startswith(("MatrixSrc", "MatrixDst", "MatrixAmount", "MatrixControl")):
                v = 0.0
            else:
                v = self.base_val(k)
            to_set[k] = v
            self.managed[k] = v
        if to_set:
            self.irr.set_many(sorted(to_set.items()))


def spectral_width(x: np.ndarray, lo: float = WIDTH_LO, hi: float = WIDTH_HI) -> float:
    """Power-weighted frequency spread (Hz) around C4 — the TODO_MEASURE metric."""
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean()
    a, b = int(0.3 * SR), min(len(x), int(1.9 * SR))
    x = x[a:b]
    if x.size < 512:
        return float("nan")
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = (f >= lo) & (f <= hi)
    pw, ff = X[m], f[m]
    s = float(pw.sum())
    if s <= 0:
        return float("nan")
    mean = float((ff * pw).sum() / s)
    return float(np.sqrt((pw * (ff - mean) ** 2).sum() / s))


def modulation_depth(x: np.ndarray, n: int = 2048, hop: int = 1024) -> float:
    """Frame-wise log-spectrum standard deviation (how much the timbre moves)."""
    frames = []
    x = np.asarray(x, dtype=np.float64)
    for i in range(0, len(x) - n, hop):
        seg = x[i:i + n] * np.hanning(n)
        X = np.abs(np.fft.rfft(seg)) ** 2
        f = np.fft.rfftfreq(n, 1 / SR)
        edges = np.geomspace(100, 8000, 25)
        frames.append([np.log10(X[(f >= a) & (f < b)].mean() + 1e-12)
                       for a, b in zip(edges[:-1], edges[1:])])
    if len(frames) < 3:
        return float("nan")
    A = np.array(frames)
    A -= A.mean(axis=0)
    return float(np.mean(np.std(A, axis=0)))


def rms_db(x: np.ndarray) -> float:
    return float(20 * np.log10(max(np.sqrt(np.mean(np.asarray(x) ** 2)), 1e-9)))


# ---------------------------------------------------------------- recording
def record_release(bl, irr, note: int = 60, pre: float = 1.5,
                   hold: float = 1.2, tail: float = 5.0) -> np.ndarray:
    """Record with note-off in the middle, so the FX tail is captured."""
    import threading

    def sched():
        time.sleep(pre - 0.1)
        for ch in range(16):
            bl.control_change(123, 0, channel=ch)
            bl.control_change(7, 127, channel=ch)
        irr.silence_part()
        time.sleep(0.05)
        bl.note_on(note=note, velocity=100)
        irr.note_on(note=note, velocity=100)
        time.sleep(hold)
        bl.note_off(note=note)
        irr.note_off(note=note)

    th = threading.Thread(target=sched, daemon=True)
    th.start()
    try:
        d = audio.record(duration=tail, channels=None)
    finally:
        th.join()
    return d


def rec_hold(bl, irr, dur: float) -> np.ndarray:
    return _M.capture(bl, irr, note=60, vel=100, dur=dur, pre=0.35)


def tail_metric(d: np.ndarray) -> dict:
    """Sustain level and reverb tail level (dB) per synth."""
    out = {}
    for name in ("blofeld", "iridium"):
        x = np.mean(d[list(audio.CHANNELS[name]), :], axis=0)
        n = len(x)
        # note-off at pre(1.5)+hold(1.2)=2.7 s after ffmpeg start
        sus = x[int(1.0 * SR):int(2.5 * SR)]
        tail = x[min(n - 1, int(3.0 * SR)):]
        out[name] = {"sustain_db": round(rms_db(sus), 1),
                     "tail_db": round(rms_db(tail), 1),
                     "tail_rel": round(rms_db(tail) - rms_db(sus), 1)}
    return out


# ---------------------------------------------------------------- driver
def run_group(name: str, cfg: dict, init: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logpath = REPO / f"recordings/todo_measure_{name}.jsonl"
    logpath.unlink(missing_ok=True)

    base_sd = with_overrides(init["sdata"], cfg["variant"])
    base_ov = overrides_for(base_sd)
    init_vals = base_values()

    irr = Iridium()
    bl = midi.connect("blofeld")
    state = IridiumState(irr, base_ov, init_vals)
    try:
        actual = _M.load_sndd_actual(bl, base_sd)
        if actual is None:
            raise RuntimeError("Basis-Dump nicht geladen")
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        time.sleep(0.6)  # let init-patch finish before touching the FX chain
        apply_fx(irr, cfg)

        header = {"kind": "meta", "group": name, "prefix": cfg["prefix"],
                  "variant": cfg["variant"], "params": cfg["params"],
                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}

        # ---- baseline for effect-vector groups
        base_vecs, thresh = {}, None
        if cfg["kind"] == "effect":
            base_vecs = {"blofeld": [], "iridium": []}
            for _rep in range(2):
                d = rec_hold(bl, irr, cfg.get("dur", 2.0))
                for nm in ("blofeld", "iridium"):
                    x = np.mean(d[list(audio.CHANNELS[nm]), :], axis=0)
                    np.save(OUT / f"{cfg['prefix']}init_{nm}_{_rep}.npy", x)
                    base_vecs[nm].append(P.effect_vector(x))
            noise = {n: float(np.linalg.norm(base_vecs[n][0] - base_vecs[n][1]))
                     for n in base_vecs}
            thresh = max(P.THR, 2.5 * max(noise.values()))
            header["noise"] = noise
            header["threshold"] = thresh
            print(f"[{name}] baseline noise {noise} -> threshold {thresh:.2f}", flush=True)

        with logpath.open("a") as log:
            log.write(json.dumps(header) + "\n")
            log.flush()
            for idx in cfg["params"]:
                pname = bd.SDATA[idx][0]
                vals = cfg["values"].get(idx) or P.values_for(idx)
                for raw in vals:
                    sd = with_overrides(base_sd, {idx: raw})
                    actual = _M.load_sndd_actual(bl, sd)
                    if actual is None:
                        print(f"  SKIP idx {idx} raw {raw}: kein Readback", flush=True)
                        continue
                    target_ov = overrides_for(actual)
                    state.apply(state.desired(target_ov))
                    apply_fx(irr, cfg)
                    time.sleep(0.15)

                    row = {"kind": "row", "group": name, "prefix": cfg["prefix"],
                           "idx": idx, "param": pname, "raw": raw,
                           "enum": bd.SDATA[idx][1] is not None,
                           "iridium_keys": sorted(state.desired(target_ov)),
                           "time": time.strftime("%H:%M:%S")}

                    if cfg["kind"] == "effect":
                        vecs = {}
                        for nm in ("blofeld", "iridium"):
                            d = rec_hold(bl, irr, cfg.get("dur", 2.0))
                            x = np.mean(d[list(audio.CHANNELS[nm]), :], axis=0)
                            np.save(OUT / f"{cfg['prefix']}{idx:03d}_{raw:03d}_{nm}.npy", x)
                            vecs[nm] = P.effect_vector(x)
                        db = vecs["blofeld"] - np.mean(base_vecs["blofeld"], axis=0)
                        di = vecs["iridium"] - np.mean(base_vecs["iridium"], axis=0)
                        status, mb, mi, cos = P.classify(db, di, thresh)
                        row.update(status=status, mag_b=round(mb, 3), mag_i=round(mi, 3),
                                   cos=None if cos is None else round(cos, 3))
                        print(f"  {name} {pname:22s} {raw:3d} {status:9s} "
                              f"B {mb:5.2f} I {mi:5.2f} cos "
                              f"{cos if cos is None else round(cos, 2)}", flush=True)
                    elif cfg["kind"] == "width":
                        widths = {"blofeld": [], "iridium": []}
                        for _take in range(cfg.get("takes", 2)):
                            d = rec_hold(bl, irr, cfg.get("dur", 3.2))
                            for nm in ("blofeld", "iridium"):
                                x = np.mean(d[list(audio.CHANNELS[nm]), :], axis=0)
                                np.save(OUT / f"{cfg['prefix']}{idx:03d}_{raw:03d}_"
                                              f"{nm}_{_take}.npy", x)
                                widths[nm].append(spectral_width(x))
                        wb = float(np.mean(widths["blofeld"]))
                        wi = float(np.mean(widths["iridium"]))
                        row.update(width_b=round(wb, 2), width_i=round(wi, 2),
                                   takes=cfg.get("takes", 2))
                        print(f"  {name} {pname:22s} {raw:3d} width "
                              f"B {wb:5.2f} Hz  I {wi:5.2f} Hz", flush=True)
                    else:  # reverb
                        mets = []
                        for _take in range(cfg.get("takes", 2)):
                            d = record_release(bl, irr)
                            mets.append(tail_metric(d))
                        mb = {k: float(np.mean([m["blofeld"][k] for m in mets]))
                              for k in ("sustain_db", "tail_db", "tail_rel")}
                        mi = {k: float(np.mean([m["iridium"][k] for m in mets]))
                              for k in ("sustain_db", "tail_db", "tail_rel")}
                        row.update(tail_b={k: round(v, 1) for k, v in mb.items()},
                                   tail_i={k: round(v, 1) for k, v in mi.items()})
                        try:
                            row["iridium_gain"] = round(irr.get("ReverbGain"), 3)
                            row["iridium_fx2"] = round(irr.get("FX2Type"), 3)
                        except Exception as exc:  # pragma: no cover - device hiccup
                            row["iridium_gain"] = f"ERR {exc}"
                        print(f"  {name} {pname:22s} {raw:3d} tail-rel "
                              f"B {mb['tail_rel']:6.1f} dB  I {mi['tail_rel']:6.1f} dB  "
                              f"gain {row['iridium_gain']}", flush=True)

                    if cfg.get("fx_policy") == "fx1":
                        try:
                            got = irr.get("FX1Type")
                            want_fx1 = target_ov.get(
                                "FX1Type", base_ov.get("FX1Type", (0.0, "")))[0]
                            row["iridium_fx1"] = round(got, 3)
                            row["iridium_fx1_ok"] = abs(got - want_fx1) < 1e-6
                        except Exception as exc:  # pragma: no cover
                            row["iridium_fx1"] = f"ERR {exc}"

                    log.write(json.dumps(row) + "\n")
                    log.flush()
    finally:
        irr.close()
        bl.close()
    print(f"[{name}] done -> {logpath.relative_to(REPO)}", flush=True)


# ---------------------------------------------------------------- report
def derive_effect(rows):
    return rows


def derive_width(rows):
    base = {r["idx"]: r for r in rows if r["raw"] == 0}
    out = []
    for r in rows:
        b = base.get(r["idx"])
        if b is None:
            r["status"] = "?"
        else:
            db = r["width_b"] - b["width_b"]
            di = r["width_i"] - b["width_i"]
            if db < 0.5 and di < 0.5:
                st = "n/a"
            elif db >= 0.5 and di < 0.5:
                st = "defekt"
            elif db < 0.5 and di >= 0.5:
                st = "Mismatch"
            else:
                ratio = di / db
                st = "OK" if 0.6 <= ratio <= 1.6 else ("teilweise" if 0.33 <= ratio <= 3 else "Mismatch")
            r["status"] = st
            r["delta_b"], r["delta_i"] = round(db, 2), round(di, 2)
        out.append(r)
    return out


def derive_reverb(rows):
    by_raw = {r["raw"]: r for r in rows}
    lo, hi = by_raw.get(0), by_raw.get(127)
    if lo and hi:
        rng_b = hi["tail_b"]["tail_rel"] - lo["tail_b"]["tail_rel"]
        rng_i = hi["tail_i"]["tail_rel"] - lo["tail_i"]["tail_rel"]
    else:
        rng_b = rng_i = 0.0
    summary = {"range_b": round(rng_b, 1), "range_i": round(rng_i, 1)}
    if rng_b >= 6 and rng_i >= 6:
        summary["status"] = "OK"
    elif rng_i >= 3:
        summary["status"] = "teilweise"
    else:
        summary["status"] = "defekt"
    return summary


def write_report() -> None:
    logs = {g: REPO / f"recordings/todo_measure_{g}.jsonl" for g in GROUPS}
    data = {}
    for g, path in logs.items():
        if not path.exists():
            continue
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        meta = next((r for r in rows if r.get("kind") == "meta"), {})
        rr = [r for r in rows if r.get("kind") == "row"]
        data[g] = (meta, rr)

    lines = ["# TODO_MEASURE — Messergebnisse 2026-11-21", "",
             "Automatisch erzeugt von `scripts/profile_todo_measure.py report`.", ""]

    if "pulse_amt" in data:
        lines += ["## A1 — PWM bei Pulse-Wellenform (positiver Fall)", "",
                  "Osc 2 = Pulse, PWM Source = LFO 1; LFO 1 mit Fade = 64 (kein Ausblenden),"
                  " Filter offen, FX aus. Amount 64 ist die Neutralstellung (0 Modulation),"
                  " 0 = maximale negative, 127 = maximale positive Modulation.", ""]
        for g in ("pulse_amt",):
            if g not in data:
                continue
            meta, rr = data[g]
            prefix = meta.get("prefix", "")
            lines += [f"**{rr[0]['param'] if rr else g}** (Schwelle {meta.get('threshold', 0):.1f})", "",
                      "| raw | Blofeld | Iridium | Cos | Modulation BF / IR | Status |",
                      "|---:|---:|---:|---:|---:|---|"]
            for r in rr:
                cos = "-" if r.get("cos") is None else f"{r['cos']:.2f}"
                mods = []
                for nm in ("blofeld", "iridium"):
                    f = REPO / f"recordings/todo/{prefix}{r['idx']:03d}_{r['raw']:03d}_{nm}.npy"
                    mods.append(modulation_depth(np.load(f)) if f.exists() else float("nan"))
                lines.append(f"| {r['raw']} | {r['mag_b']:.2f} | {r['mag_i']:.2f} | "
                             f"{cos} | {mods[0]:.3f} / {mods[1]:.3f} | {r['status']} |")
            lines.append("")

    if "fx2types" in data:
        meta, rr = data["fx2types"]
        lines += ["## A3 — FX2-Typen (FX1 = Off, Effect 2 Mix 127)", "",
                  "Blofeld erlaubt in Effect 2 nur Delay/Clk.Delay/Reverb; Effect 1 nur"
                  " Chorus/Flanger/Phaser/Overdrive/Triple FX. Delay/Reverb in Effect 1"
                  " normalisiert das Gerät auf Chorus (Readback geprüft). Delay-Tails"
                  " weichen ab: der Blofeld-Delay braucht seine Zeit-/Feed-Parameter,"
                  " der Konverter setzt nur Feed/HiCut (p5/p6), keine Delay-Zeit.", "",
                  "| Effect 2 Type | Blofeld Tail | Iridium Tail | Iridium FX2 |",
                  "|---:|---:|---:|---:|"]
        for r in rr:
            lines.append(f"| {r['raw']} | {r['tail_b']['tail_rel']:.1f} dB | "
                         f"{r['tail_i']['tail_rel']:.1f} dB | {r.get('iridium_fx2')} |")
        lines.append("")

    if "fx1types" in data:
        meta, rr = data["fx1types"]
        lines += ["## A3 — FX getrennt: FX1 allein (FX2 = Off)", "",
                  f"Schwelle {meta.get('threshold', 0):.1f}. Die Baseline ist Phaser"
                  " (100 % wet); die Typen 0–5 sind die gültigen Effect-1-Typen."
                  " Delay/Clk.Delay/Reverb normalisiert der Blofeld in Effect 1 auf"
                  " Chorus (Readback: 6/7/8 → 1). Beide Seiten reagieren auf alle"
                  " gültigen Typen mit vergleichbarer Stärke; der spektrale Charakter"
                  " der Engines unterscheidet sich (niedriger Cos).", "",
                  "| Parameter | raw | Blofeld | Iridium | Cos | Status |",
                  "|---|---:|---:|---:|---:|---|"]
        for r in rr:
            cos = "-" if r.get("cos") is None else f"{r['cos']:.2f}"
            lines.append(f"| {r['param']} | {r['raw']} | {r['mag_b']:.2f} | "
                         f"{r['mag_i']:.2f} | {cos} | {r['status']} |")
        lines.append("")

    if "reverb" in data:
        meta, rr = data["reverb"]
        summ = derive_reverb(rr)
        lines += ["## A3 — FX getrennt: FX2 = Reverb (FX1 = Off)", "",
                  "Metrik: Pegel des Hall-Schweifs ab 3,0 s (≈1 s nach Note-Off) bis"
                  " Aufnahmeende, relativ zum gehaltenen Ton.", "",
                  "| Mix | Blofeld Tail | Iridium Tail | Iridium ReverbGain |",
                  "|---:|---:|---:|---:|"]
        for r in rr:
            lines.append(f"| {r['raw']} | {r['tail_b']['tail_rel']:.1f} dB | "
                         f"{r['tail_i']['tail_rel']:.1f} dB | {r.get('iridium_gain')} |")
        lines += ["", f"**Hub Blofeld {summ['range_b']:.1f} dB, Iridium {summ['range_i']:.1f} dB"
                      f" → {summ['status']}.**", ""]

    for g in ("unison_detune", "unison_count"):
        if g not in data:
            continue
        meta, rr = data[g]
        rr = derive_width(rr)
        lines += [f"## A4 — {'Unisono Detune (5 Stimmen)' if g.endswith('detune') else 'Unisono Count (Detune 127)'}",
                  "",
                  "Metrik: leistungsgewichtete Spektralbreite um C4 (±55 Hz), Mittel aus 2 Takes.", "",
                  "| raw | Blofeld | Iridium | Δ Blofeld | Δ Iridium | Status |",
                  "|---:|---:|---:|---:|---:|---|"]
        for r in rr:
            lines.append(f"| {r['raw']} | {r['width_b']:.2f} Hz | {r['width_i']:.2f} Hz | "
                         f"{r.get('delta_b', 0):+.2f} | {r.get('delta_i', 0):+.2f} | {r['status']} |")
        lines.append("")

    out = REPO / "docs/TODO-MEASURE-2026-11-21.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out.relative_to(REPO)}")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args[0] == "report":
        write_report()
        return 0
    groups = list(GROUPS) if args[0] == "all" else args
    for g in groups:
        if g not in GROUPS:
            raise SystemExit(f"unknown group {g!r}; choose from {', '.join(GROUPS)}")
    init = P.load_init()
    for g in groups:
        run_group(g, GROUPS[g], init)
    write_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
