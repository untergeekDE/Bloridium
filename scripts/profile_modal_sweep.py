#!/usr/bin/env python3
"""Modal sweep (measurement blocks 1+2): keytrack, velocity, pan/balance.

Each parameter value is measured under *two excitations* (two notes or two
velocities) or with a stereo descriptor, because a single held note cannot show
keytracking, velocity response or panorama.

Writes recordings/modal_sweep.jsonl (rows are precomputed: the analyzer takes
status/magnitudes as-is) and prints a table.

Run:  python3 scripts/profile_modal_sweep.py [keytrack|velocity|pan|pan_noise]
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

from bloridium import audio, blofeld_dump as bd, midi, qpat, qpat_map  # noqa: E402
from _device_tool import Iridium  # noqa: E402
import _measure as M  # noqa: E402
import profile_init_sweep as P  # noqa: E402

LOG = REPO / "recordings/modal_sweep.jsonl"

MODES = {
    # Keytrack needs two notes and a filter that is not fully open.
    "keytrack": {
        "excite": "notes",
        "notes": [48, 72],
        "vel": 100,
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 70, 87: 64, 89: 0,
                    97: 0, 117: 0, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [86],
    },
    # Velocity needs two velocities; filter env amount up + cutoff mid.
    "velocity": {
        "excite": "vels",
        "notes": [60],
        "vels": [40, 120],
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 64, 87: 100, 88: 64, 89: 0,
                    202: 100, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [88, 122],
    },
    # Real panorama (Filter pan amount with LFO source) and the Balance semantics.
    "pan": {
        "excite": "note",
        "notes": [60],
        "vel": 100,
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 120, 87: 64, 89: 0,
                    97: 0, 117: 0, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [95, 62, 64],
    },
    # Block 3b: Filter 2 with the right excitation (all signal -> F2, cutoff mid).
    "f2_keytrack": {
        "excite": "notes",
        "notes": [48, 72],
        "vel": 100,
        "variant": {62: 127, 64: 127, 66: 127, 63: 0, 65: 0, 77: 1, 78: 120,
                    97: 1, 98: 70, 100: 20, 117: 0, 87: 64, 89: 0, 202: 60,
                    128: 0, 129: 0, 144: 0, 145: 0},
        "params": [106],
    },
    "f2_velocity": {
        "excite": "vels",
        "notes": [60],
        "vels": [40, 120],
        "variant": {62: 127, 64: 127, 66: 127, 63: 0, 65: 0, 77: 1, 78: 120,
                    97: 1, 98: 60, 100: 20, 117: 0, 87: 100, 89: 0, 202: 60,
                    128: 0, 129: 0, 144: 0, 145: 0},
        "params": [108],
    },
    "f2_envamount": {
        "excite": "note",
        "notes": [60],
        "vel": 100,
        "variant": {62: 127, 64: 127, 66: 127, 63: 0, 65: 0, 77: 1, 78: 120,
                    97: 1, 98: 60, 100: 20, 117: 0, 89: 0, 202: 60,
                    128: 0, 129: 0, 144: 0, 145: 0},
        "params": [107],
    },
    # Noise balance needs the noise mixer as the only source.
    "pan_noise": {
        "excite": "note",
        "notes": [60],
        "vel": 100,
        "variant": {8: 0, 24: 0, 40: 0, 61: 0, 63: 0, 65: 0, 62: 0, 64: 0, 66: 0,
                    67: 100, 68: 0, 69: 64, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [68],
    },
}


def device_xy(data, name):
    """Blofeld: ch 2/3, Iridium: ch 4/5 -> (L, R)."""
    ch = list(audio.CHANNELS[name])
    return data[ch[0], :], data[ch[1], :]


def measure_takes(bl, irr, mode, variant_sd, idx, raw, base_sd, base_ov):
    """Measure all excitations for one (param, value). Returns a dict of descriptors."""
    sd = bytearray(base_sd)
    if idx is not None:
        sd[idx] = raw
    from bloridium import blofeld_dump as bd2
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd2.checksum(bytes(sd))]
    var = bd2.parse_sndd(bytes([0xF0, *body, 0xF7]))
    ov, _ = qpat_map.blofeld_to_qpat_params(var)
    keys = {k: v[0] for k, v in ov.items()
            if k not in base_ov or abs(v[0] - base_ov[k][0]) > 1e-9}
    if not M.load_sndd_verified(bl, bytes(sd)):
        raise RuntimeError(f"SNDD readback mismatch for idx {idx} raw {raw}")
    if keys:
        irr.set_many(sorted(keys.items()))
    time.sleep(0.2)

    out = {}
    if mode["excite"] == "notes":
        for note in mode["notes"]:
            d = M.capture(bl, irr, note=note, vel=mode["vel"])
            out[f"n{note}"] = np.concatenate([
                M.desc(np.mean(device_xy(d, "blofeld"), axis=0)),
                M.desc(np.mean(device_xy(d, "iridium"), axis=0))])
    elif mode["excite"] == "vels":
        for vel in mode["vels"]:
            d = M.capture(bl, irr, note=mode["notes"][0], vel=vel)
            out[f"v{vel}"] = np.concatenate([
                M.desc(np.mean(device_xy(d, "blofeld"), axis=0)),
                M.desc(np.mean(device_xy(d, "iridium"), axis=0))])
    else:
        d = M.capture(bl, irr, note=mode["notes"][0], vel=mode["vel"])
        lb, rb = device_xy(d, "blofeld")
        li, ri = device_xy(d, "iridium")
        out["pan"] = np.concatenate([M.pan_desc(lb, rb), M.pan_desc(li, ri)])
    return out, keys


def main() -> int:
    mode_name = sys.argv[1] if len(sys.argv) > 1 else "keytrack"
    mode = MODES[mode_name]
    init = P.load_init()
    sd = bytearray(init["sdata"])
    for k, v in mode["variant"].items():
        sd[k] = v
    base_sd = bytes(sd)
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
    base_ov, _ = qpat_map.blofeld_to_qpat_params(bd.parse_sndd(bytes([0xF0, *body, 0xF7])))
    init_vals = {k: v["value"] for k, v in qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}

    def base_val(k):
        return base_ov[k][0] if k in base_ov else float(init_vals.get(k, 0.0))

    irr = Iridium()
    bl = midi.connect("blofeld")
    try:
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])  # dry
        # baseline: two takes per excitation
        bls = []
        for _ in range(2):
            b, _keys = measure_takes(bl, irr, mode, base_sd, None, 0, base_sd, base_ov)
            bls.append(b)
        base = {k: (bls[0][k] + bls[1][k]) / 2 for k in bls[0]}
        noise = {k: float(np.linalg.norm(bls[0][k] - bls[1][k])) for k in bls[0]}
        thr = max(2.0, 2.5 * max(noise.values()))
        print(f"mode {mode_name}: baseline noise {noise} -> threshold {thr:.2f}", flush=True)

        rows = []
        touched = set()
        for idx in mode["params"]:
            name = bd.SDATA[idx][0]
            for raw in P.values_for(idx):
                if touched:
                    irr.set_many([(k, base_val(k)) for k in touched])
                    touched = set()
                vals, keys = measure_takes(bl, irr, mode, base_sd, idx, raw, base_sd, base_ov)
                touched |= set(keys)
                # split Blofeld/Iridium halves of each descriptor block
                blocks_b, blocks_i = [], []
                for k in base:
                    n = len(vals[k]) // 2
                    blocks_b.append(vals[k][:n] - base[k][:n])
                    blocks_i.append(vals[k][n:] - base[k][n:])
                status, mb, mi, cos = M.classify(np.concatenate(blocks_b),
                                                 np.concatenate(blocks_i), thr)
                row = {"kind": "row", "variant": mode_name, "precomputed": True,
                       "idx": idx, "param": name, "enum": bd.SDATA[idx][1] is not None,
                       "raw": raw, "status": status, "mag_b": round(mb, 4),
                       "mag_i": round(mi, 4), "cos": None if cos is None else round(cos, 4),
                       "iridium_keys": sorted(keys),
                       "time": time.strftime("%H:%M:%S")}
                rows.append(row)
                print(f"  {name:28s} {raw:3d} {status:9s} B {mb:5.2f} I {mi:5.2f} "
                      f"cos {cos if cos is None else round(cos, 2)}", flush=True)
            if touched:
                irr.set_many([(k, base_val(k)) for k in touched])
                touched = set()
        with LOG.open("a") as fh:
            fh.write(json.dumps({"kind": "baseline", "variant": mode_name,
                                 "precomputed": True, "noise": noise, "threshold": thr,
                                 "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    finally:
        irr.close()
        bl.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
