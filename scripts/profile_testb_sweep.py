#!/usr/bin/env python3
"""Test-B sweeps: Init variants where the usual targets are audible.

Modes:
  clean -- Osc 2+3 on (Saw), Filter 2 active, Filter-Env amount up. No FX,
           no unison, no vibrato -> low measurement noise. Sweeps osc2/3,
           mixer levels, ringmod, filter 2, filter envelope.
  fx    -- FX 1 (Chorus) 100 % wet / FX 2 (Reverb) 50 %. Sweeps effect mix + params.

Writes recordings/profile_testb_<mode>.jsonl, npy prefix bc_/bf_.
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

from bloridium import audio, blofeld_dump as bd, midi, qpat_map, sim  # noqa: E402
from _quir import Iridium  # noqa: E402
import profile_init_sweep as P  # noqa: E402
import _measure as _M  # noqa: E402

OUT = REPO / "recordings/profile"

MODES = {
    "clean": {
        "prefix": "bc_",
        "variant": {
            17: 64, 18: 64, 24: 2, 25: 127,      # Osc 2 Saw, center
            33: 76, 40: 2, 41: 127,              # Osc 3 Saw, +1 oct
            58: 0,                               # unison off
            63: 100, 64: 64, 65: 100, 66: 64,    # mixer levels
            71: 0,                               # ringmod off
            77: 1, 87: 96, 89: 0,                # F1 LP24, env amount up, no direct mod
            97: 1, 98: 100, 100: 40, 117: 0,     # F2 LP24 active, serial
            128: 0, 129: 0, 144: 0, 145: 0,      # FX off
            161: 64, 263: 64,                    # LFO1 speed mid, mod row neutral
        },
        "params": [17, 18, 19, 24, 33, 34, 35, 40, 49, 71, 63, 65,
                   98, 100, 106, 117, 199, 201, 202],
    },
    "f2": {
        "prefix": "bf2_",
        "variant": {
            77: 1, 78: 120, 87: 64, 89: 0,        # F1 LP24 offen, keine Direktmod
            62: 127, 64: 127, 66: 127,            # Balance 127 = alle Oscs -> Filter 2
            63: 0, 65: 0,                        # nur Osc 1 (keine Schwebung)
            97: 1, 98: 85, 100: 20, 117: 0,       # F2 LP24, Cutoff/Reso, parallel
        },
        "params": [97, 98, 100, 101, 106, 107, 108, 117],
    },
    "fe": {
        "prefix": "bfe_",
        "variant": {
            62: 0, 64: 0, 66: 0,                  # alles -> Filter 1
            78: 64, 87: 100, 88: 64, 89: 0,       # F1 Cutoff mittig, FE-Anteil hoch
            202: 100, 217: 110,                   # FE Sustain hoch, Amp-Release lang
        },
        "params": [86, 87, 199, 201, 202, 205],
    },
    "fe_decay": {
        "prefix": "bfd_",
        "variant": {
            62: 0, 64: 0, 66: 0,
            78: 64, 87: 100, 89: 0, 202: 80, 217: 110,
        },
        "params": [201],
    },
    "fe_rel": {
        "prefix": "bfr_",
        "variant": {
            62: 0, 64: 0, 66: 0,
            78: 64, 87: 100, 89: 0, 202: 100, 217: 127,
        },
        "params": [205],
    },
    "res1": {
        "prefix": "br1_",
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 80, 87: 64, 89: 0,
                    97: 0, 117: 0, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [80],
    },
    "res2": {
        "prefix": "br2_",
        "variant": {62: 127, 64: 127, 66: 127, 63: 0, 65: 0,
                    77: 1, 78: 120, 97: 1, 98: 80, 100: 0, 117: 0,
                    128: 0, 129: 0, 144: 0, 145: 0},
        "params": [100],
    },
    "fe4": {
        "prefix": "bf4_",
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 70, 87: 110, 88: 64, 89: 0,
                    97: 0, 117: 0, 202: 60, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [199, 201, 202],
    },
    "res1b": {
        "prefix": "br1b_", "dur": 3.5,
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 65, 87: 64, 89: 0,
                    97: 0, 117: 0, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [80],
    },
    "res1c": {
        "prefix": "br1c_", "dur": 3.5,
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 85, 87: 64, 89: 0,
                    97: 0, 117: 0, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [80],
    },
    "res2b": {
        "prefix": "br2b_", "dur": 3.5,
        "variant": {62: 127, 64: 127, 66: 127, 63: 0, 65: 0,
                    77: 1, 78: 120, 97: 1, 98: 65, 100: 0, 117: 0,
                    128: 0, 129: 0, 144: 0, 145: 0},
        "params": [100],
    },
    "fe4b": {
        "prefix": "bf4b_", "dur": 3.5,
        "variant": {62: 0, 64: 0, 66: 0, 77: 1, 78: 60, 87: 120, 88: 64, 89: 0,
                    97: 0, 117: 0, 202: 0, 128: 0, 129: 0, 144: 0, 145: 0},
        "params": [199, 201, 202],
    },
    "osc2": {
        "prefix": "bo2_",
        "variant": {
            8: 0, 17: 64, 18: 64, 19: 64, 24: 2, 25: 127,   # Osc1 aus, Osc2 Saw
            61: 0, 63: 127, 64: 0,                # Osc2 -> Filter 1
            128: 0, 129: 0, 144: 0, 145: 0,
        },
        "params": [17, 18, 19, 24, 25, 26, 27, 63],
    },
    "osc3": {
        "prefix": "bo3_",
        "variant": {
            8: 0, 33: 64, 34: 64, 35: 64, 40: 2, 41: 127,
            61: 0, 65: 127, 66: 0,                # Osc3 -> Filter 1
            128: 0, 129: 0, 144: 0, 145: 0,
        },
        "params": [33, 34, 35, 40, 41, 42, 43, 65],
    },
    "sync": {
        "prefix": "bsy_",
        "variant": {
            8: 0, 62: 0, 17: 64, 18: 64, 24: 2, 63: 100, 64: 0,
            33: 64, 34: 64, 40: 2, 65: 100, 66: 0, 49: 0,
            128: 0, 129: 0, 144: 0, 145: 0,
        },
        "params": [49],
    },
    "noise": {
        "prefix": "bno_",
        "variant": {
            8: 0, 24: 0, 40: 0, 61: 0, 63: 0, 65: 0,   # nur Noise-Mixer
            62: 0, 64: 0, 66: 0,
            67: 100, 68: 0, 69: 64,
            128: 0, 129: 0, 144: 0, 145: 0,
        },
        "params": [67, 68, 69],
    },
    "lfo1": {
        "prefix": "bl1_",
        "variant": {
            62: 0, 64: 0, 66: 0,
            261: 1, 262: 1, 263: 90,               # Mod 1: LFO1 -> O1 Pitch, Betrag
            161: 64, 163: 0,
            128: 0, 129: 0, 144: 0, 145: 0,
        },
        "params": [161, 163, 165, 166, 167],
    },
    "unison": {
        "prefix": "bun_",
        # Amp release 0: the old variant used 217=110 (long release), which made
        # consecutive takes overlap -> baseline noise ~1.8 and every row n/a.
        "variant": {58: 0x40, 59: 0, 217: 0, 62: 0, 64: 0, 66: 0},
        "params": [58, 59],
    },
    "fx1": {
        "prefix": "bfx_",
        "variant": {
            62: 0, 64: 0, 66: 0,
            128: 1, 129: 127, 130: 40, 131: 80, 132: 64, 133: 64,
            144: 0, 145: 0,
        },
        "params": [129, 130, 131, 132, 133, 134],
    },
    "fx": {
        "prefix": "bf_",
        "variant": {
            128: 1, 129: 120, 130: 40, 131: 80,  # FX1 Chorus, 94 % wet
            144: 8, 145: 64, 147: 64, 148: 100,  # FX2 Reverb, 50 % mix
        },
        "params": [129, 130, 131, 145, 147, 148],
    },
}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "clean"
    cfg = MODES[mode]
    dur = cfg.get("dur", P.DUR)
    dry = cfg.get("dry", mode not in ("fx", "fx1"))
    LOG = REPO / f"recordings/profile_testb_{mode}.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)

    init = P.load_init()
    sd = bytearray(init["sdata"])
    for idx, raw in cfg["variant"].items():
        sd[idx] = raw
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
    var = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
    base_sd = bytes(sd)
    base_ov, _ = qpat_map.blofeld_to_qpat_params(var)

    from bloridium import qpat
    _init_vals = {k: v["value"] for k, v in qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}

    def base_val(k):
        return base_ov[k][0] if k in base_ov else float(_init_vals.get(k, 0.0))
    print(f"variant {mode}: {len(cfg['variant'])} changes -> {len(base_ov)} Iridium params",
          flush=True)

    done = set()
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            if '"kind": "row"' in line:
                r = json.loads(line)
                done.add((r["idx"], r["raw"]))

    irr = Iridium()
    bl = midi.connect("blofeld")
    touched = set()
    try:
        if not _M.load_sndd_verified(bl, base_sd):
            raise RuntimeError("Blofeld Varianten-Dump nicht verifiziert")
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        if dry:
            irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])
        pre = cfg["prefix"]
        base_vecs = {"blofeld": [], "iridium": []}
        for rep in range(2):
            d = P.rec_once(bl, irr)
            for name in ("blofeld", "iridium"):
                x = np.mean(d[list(audio.CHANNELS[name]), :], axis=0)
                np.save(OUT / f"{pre}init_{name}_{rep}.npy", x)
                base_vecs[name].append(P.effect_vector(x))
        noise = {n: float(np.linalg.norm(base_vecs[n][0] - base_vecs[n][1])) for n in base_vecs}
        thresh = max(P.THR, 2.5 * max(noise.values()))
        bvec = {n: np.mean(base_vecs[n], axis=0) for n in base_vecs}
        print(f"baseline noise: {noise} -> threshold {thresh:.2f}", flush=True)

        with LOG.open("a") as log:
            log.write(json.dumps({"kind": "baseline", "variant": mode, "prefix": pre,
                                  "noise": noise, "threshold": thresh,
                                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            for pi, idx in enumerate(cfg["params"], 1):
                name = bd.SDATA[idx][0]
                for raw in P.values_for(idx):
                    if (idx, raw) in done:
                        continue
                    if touched:
                        irr.set_many([(k, base_val(k)) for k in touched])
                        touched = set()
                    sd2 = bytearray(base_sd)
                    sd2[idx] = raw
                    actual = _M.load_sndd_actual(bl, bytes(sd2))
                    if actual is None:
                        print(f"  SKIP idx {idx} raw {raw}: kein Readback", flush=True)
                        continue
                    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *actual, bd.checksum(bytes(actual))]
                    p2 = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
                    ov, _ = qpat_map.blofeld_to_qpat_params(p2)
                    keys = {k: v[0] for k, v in ov.items()
                            if k not in base_ov or abs(v[0] - base_ov[k][0]) > 1e-9}
                    if keys:
                        irr.set_many(sorted(keys.items()))
                        touched |= set(keys)
                    if dry and idx not in (81, 101):  # drive maps to an FX slot
                        irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])
                    time.sleep(0.15)
                    d = P.rec_once(bl, irr, dur=dur)
                    vecs, feats = {}, {}
                    for nm in ("blofeld", "iridium"):
                        x = np.mean(d[list(audio.CHANNELS[nm]), :], axis=0)
                        np.save(OUT / f"{pre}{idx:03d}_{raw:03d}_{nm}.npy", x)
                        vecs[nm] = P.effect_vector(x)
                        feats[nm] = sim.features(x, sr=audio.SAMPLERATE, n_bands=48)
                    db = vecs["blofeld"] - bvec["blofeld"]
                    di = vecs["iridium"] - bvec["iridium"]
                    status, mb, mi, cos = P.classify(db, di, thresh)
                    pair = sim.compare(feats["blofeld"], feats["iridium"])["score"]
                    row = {"kind": "row", "variant": mode, "prefix": pre, "idx": idx,
                           "param": name, "enum": bd.SDATA[idx][1] is not None, "raw": raw,
                           "iridium_keys": sorted(keys), "status": status,
                           "mag_b": round(mb, 4), "mag_i": round(mi, 4),
                           "cos": None if cos is None else round(cos, 4),
                           "pair_score": round(pair, 1),
                           "time": time.strftime("%H:%M:%S")}
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    print(f"{pi:2d}/{len(cfg['params'])} {mode} {name:28s} {raw:3d} "
                          f"{status:9s} B {mb:5.2f} I {mi:5.2f} "
                          f"cos {cos if cos is None else round(cos, 2)}", flush=True)
    finally:
        irr.close()
        bl.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
