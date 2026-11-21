#!/usr/bin/env python3
"""Profiling sweep: Init sound on Blofeld vs converted Init on Iridium.

For every Blofeld parameter the converter maps, vary the parameter on the
Blofeld Init patch and let the converter compute the Iridium counterpart.
Both synths play the same note simultaneously; audio is recorded per synth and
the *parameter effect* (delta vs. Init) is compared.

Writes one JSON line per (param, value) to recordings/profile_sweep.jsonl and
the recordings to recordings/profile/*.npy. Resumable: existing rows are read.

Run:  python3 scripts/profile_init_sweep.py [--only NAME] [--values 0,32,64,127]
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

import mido

from bloridium import audio, blofeld_dump as bd, midi, qpat, qpat_map, sim
from _quir import Iridium, init_overrides
import _measure as _M

OUT = REPO / "recordings" / "profile"
LOG = REPO / "recordings" / "profile_sweep.jsonl"
INIT_LOC = "A066"
NOTE, VEL, DUR, PRE = 60, 100, 2.0, 0.35

_BASE_CACHE: dict = {}


def base_value(key: str) -> float:
    """Value a parameter key has in the converted-Init state (override or device Init)."""
    global _BASE_CACHE
    if not _BASE_CACHE:
        from bloridium import qpat
        _BASE_CACHE["ov"] = init_overrides(REPO)
        _BASE_CACHE["init"] = {k: v["value"] for k, v in
                               qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}
    ov, ini = _BASE_CACHE["ov"], _BASE_CACHE["init"]
    return ov[key][0] if key in ov else float(ini.get(key, 0.0))

# --------------------------------------------------------------------------
def load_init():
    p = bd.parse_sndd((REPO / f"dumps/banks/A/{INIT_LOC}.bin").read_bytes())
    return p


# musically meaningful values where 0/25/50/100 % of raw would be inaudible
VALUE_OVERRIDES = {
    1: [32, 48, 64, 80], 17: [32, 48, 64, 80], 33: [32, 48, 64, 80],   # Octave (+/-2)
    2: [52, 58, 64, 76], 18: [52, 58, 64, 76], 34: [52, 58, 64, 76],   # Semitone (+/-12)
    53: [0, 1], 56: [0, 1, 2, 3], 117: [0, 1],                           # enums without table
}


def values_for(idx: int) -> list[int]:
    """0/25/50/100 % of the parameter range (enums: of the table)."""
    if idx in VALUE_OVERRIDES:
        return VALUE_OVERRIDES[idx]
    table = bd.SDATA[idx][1]
    if table:
        n = len(table)
        picks = sorted({0, int(round((n - 1) * 0.25)), int(round((n - 1) * 0.5)), n - 1})
        return picks
    return [0, 32, 64, 127]


def overrides_from_sdata(sdata: bytes):
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sdata]
    body.append(bd.checksum(bytes(sdata)))
    return qpat_map.blofeld_to_qpat_params(
        bd.parse_sndd(bytes([0xF0, *body, 0xF7])))[0]


def synth_params(idx: int, raw: int, init_sdata: bytes):
    """Blofeld SDATA with one byte changed -> (sdata, iridium base-diff overrides)."""
    sd = bytearray(init_sdata)
    sd[idx] = raw & 0x7F
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd]
    body.append(bd.checksum(bytes(sd)))
    parsed = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    return bytes(sd), ov


def mapped_params(init_parsed) -> list[tuple[int, str, bool]]:
    out = []
    base_sd = bytearray(init_parsed["sdata"])
    base, _ = qpat_map.blofeld_to_qpat_params(init_parsed)
    for idx in sorted(bd.SDATA):
        name, table = bd.SDATA[idx]
        if idx >= 363:
            continue
        touched = False
        for raw in values_for(idx):
            sd = bytearray(base_sd)
            sd[idx] = raw
            body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
            ov, _ = qpat_map.blofeld_to_qpat_params(bd.parse_sndd(bytes([0xF0, *body, 0xF7])))
            if any(k not in base or abs(v[0] - base[k][0]) > 1e-9 for k, v in ov.items()):
                touched = True
                break
        if touched:
            out.append((idx, name, table is not None))
    return out


def effect_vector(x: np.ndarray) -> np.ndarray:
    if x.size < int(0.2 * audio.SAMPLERATE):
        return np.zeros(64)
    f = sim.features(x, sr=audio.SAMPLERATE, n_bands=48)
    spec = f["log_spec"].mean(axis=1)
    spec = (spec - np.median(spec)) / 20.0
    env = f["env_rms"]
    if env.max() > 0:
        env = env / env.max()
    env = np.interp(np.linspace(0, 1, 16), np.linspace(0, 1, len(env)), env)
    return np.concatenate([spec, 2.0 * env])


def rec_once(bl, irr, note=NOTE, vel=VEL, dur=DUR, pre=PRE) -> np.ndarray:
    for ch in range(16):
        bl.control_change(123, 0, channel=ch)
        bl.control_change(7, 127, channel=ch)
    irr.out.send(mido.Message("control_change", control=123, value=0, channel=5))
    time.sleep(0.05)
    bl.note_on(note=note, velocity=vel)
    irr.out.send(mido.Message("note_on", note=note, velocity=vel, channel=5))
    time.sleep(pre)
    data = audio.record(duration=dur, channels=None)
    bl.note_off(note=note)
    irr.out.send(mido.Message("note_off", note=note, velocity=0, channel=5))
    return data


def load_row():
    if not LOG.exists():
        return []
    rows = []
    for line in LOG.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


THR = 2.0   # effect magnitude below this = inaudible / within run-to-run drift


def classify(delta_b, delta_i, thr: float = THR):
    mb, mi = float(np.linalg.norm(delta_b)), float(np.linalg.norm(delta_i))
    if mb < thr and mi < thr:
        return "n/a", mb, mi, None
    if mb < thr:
        return "Mismatch", mb, mi, None
    if mi < thr:
        return "defekt", mb, mi, None
    cos = float(np.dot(delta_b, delta_i) / (mb * mi))
    ratio = mi / mb
    if cos >= 0.80 and 0.5 <= ratio <= 2.0:
        return "OK", mb, mi, cos
    if cos >= 0.50:
        return "teilweise", mb, mi, cos
    return "Mismatch", mb, mi, cos


# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="substring of the Blofeld parameter name")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-baseline", action="store_true")
    args = ap.parse_args(argv)

    OUT.mkdir(parents=True, exist_ok=True)
    init = load_init()
    base_sd = bytes(init["sdata"])
    base_ov = init_overrides(REPO)
    params = mapped_params(init)
    if args.only:
        params = [p for p in params if args.only.lower() in p[1].lower()]
    if args.limit:
        params = params[: args.limit]

    done = {(r["idx"], r["raw"]) for r in load_row() if r.get("kind") == "row"}
    print(f"{len(params)} parameters, {len(done)} rows already measured", flush=True)

    irr = Iridium()
    bl = midi.connect("blofeld")
    touched = set()
    try:
        # ---- baseline: Init on both, twice (noise floor) -------------------
        if not _M.load_sndd_verified(bl, base_sd):
            raise RuntimeError("Blofeld Init-Dump nicht verifiziert")
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])  # dry (no reverb/chorus)
        base_vecs = {"blofeld": [], "iridium": []}
        for rep in range(2):
            d = rec_once(bl, irr)
            for name in ("blofeld", "iridium"):
                ch = list(audio.CHANNELS[name])
                x = np.mean(d[ch, :], axis=0)
                np.save(OUT / f"init_{name}_{rep}.npy", x)
                base_vecs[name].append(effect_vector(x))
        noise = {n: float(np.linalg.norm(base_vecs[n][0] - base_vecs[n][1]))
                 for n in base_vecs}
        print(f"baseline noise floor: {noise}", flush=True)
        bvec = {n: np.mean(base_vecs[n], axis=0) for n in base_vecs}

        # ---- sweep ---------------------------------------------------------
        with LOG.open("a") as log:
            log.write(json.dumps({"kind": "baseline", "loc": INIT_LOC, "noise": noise,
                                  "note": NOTE, "vel": VEL, "dur": DUR,
                                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            log.flush()
            for pi, (idx, pname, is_enum) in enumerate(params, 1):
                vals = values_for(idx)
                # reset whatever a previous parameter left behind
                if touched:
                    irr.set_many([(k, base_value(k)) for k in touched])
                    touched = set()
                for raw in vals:
                    if (idx, raw) in done:
                        continue
                    # restore base values of anything touched before, then apply this value
                    if touched:
                        irr.set_many([(k, base_value(k)) for k in touched])
                        touched = set()
                    sd = bytearray(base_sd)
                    sd[idx] = raw & 0x7F
                    actual = _M.load_sndd_actual(bl, bytes(sd))
                    if actual is None:
                        print(f"  SKIP idx {idx} raw {raw}: kein Readback", flush=True)
                        continue
                    ov = overrides_from_sdata(actual)
                    keys = {k: v[0] for k, v in ov.items()
                            if k not in base_ov or abs(v[0] - base_ov[k][0]) > 1e-9}
                    if keys:
                        irr.set_many(sorted(keys.items()))
                        touched |= set(keys)
                    if not (128 <= idx <= 159) and idx not in (81, 101):  # FX/drive stay wet
                        irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])
                    time.sleep(0.15)
                    d = rec_once(bl, irr)
                    vecs, feats = {}, {}
                    for name in ("blofeld", "iridium"):
                        ch = list(audio.CHANNELS[name])
                        x = np.mean(d[ch, :], axis=0)
                        np.save(OUT / f"{idx:03d}_{raw:03d}_{name}.npy", x)
                        vecs[name] = effect_vector(x)
                        feats[name] = sim.features(x, sr=audio.SAMPLERATE, n_bands=48)
                    featb, feati = feats["blofeld"], feats["iridium"]
                    db = vecs["blofeld"] - bvec["blofeld"]
                    di = vecs["iridium"] - bvec["iridium"]
                    status, mb, mi, cos = classify(db, di, max(THR, 2.5 * max(noise.values())))
                    pair = sim.compare(featb, feati)["score"]
                    row = {"kind": "row", "idx": idx, "param": pname, "enum": is_enum,
                           "raw": raw, "value_pct": raw / 127.0 if not is_enum else None,
                           "iridium_keys": sorted(keys), "status": status,
                           "raw_effective": int(actual[idx]) if actual[idx] != (raw & 0x7F) else None,
                           "mag_b": round(mb, 4), "mag_i": round(mi, 4),
                           "pair_score": round(pair, 1),
                           "cos": None if cos is None else round(cos, 4),
                           "time": time.strftime("%H:%M:%S")}
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    print(f"{pi:3d}/{len(params)} {pname:32s} {raw:3d} {status:9s} "
                          f"B {mb:5.2f} I {mi:5.2f} cos {cos if cos is None else round(cos,2)}",
                          flush=True)
    finally:
        irr.close()
        bl.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
