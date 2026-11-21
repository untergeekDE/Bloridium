#!/usr/bin/env python3
"""Test-B sweep: same protocol on an Init variant where the usual targets are audible.

Variant: Osc 2+3 on (Saw), Filter 2 active, FX 1/2 with mix, Filter-Env amount up,
LFO 1 vibrato row active, 2-voice unison. Then sweep the parameters that are
inaudible in the plain Init. Writes recordings/profile_testb.jsonl (+ npy prefix b).
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

OUT = REPO / "recordings/profile"
LOG = REPO / "recordings/profile_testb.jsonl"

VARIANT = {
    17: 64,    # Osc 2 Octave center
    18: 64,    # Osc 2 Semitone
    24: 2,     # Osc 2 Shape = Saw
    25: 127,   # Osc 2 Pulsewidth
    33: 76,    # Osc 3 Octave +1
    40: 2,     # Osc 3 Shape = Saw
    41: 127,
    58: 0x40,  # Allocation/Unisono: 2 voices
    59: 0,     # Unisono Detune neutral
    63: 100,   # Osc 2 Level
    64: 64,    # Osc 2 Balance
    65: 100,   # Osc 3 Level
    77: 1,     # Filter 1 Type LP24
    87: 96,    # Filter 1 Env Amount positive
    89: 0,     # Filter 1 Mod Source off
    97: 1,     # Filter 2 Type LP24
    98: 100,   # Filter 2 Cutoff
    100: 40,   # Filter 2 Resonance
    117: 0,    # Filter Routing serial
    128: 1,    # FX1 Chorus
    129: 60,   # FX1 Mix
    130: 40,   # Chorus Speed
    131: 80,   # Chorus Depth
    144: 8,    # FX2 Reverb
    145: 50,   # FX2 Mix
    147: 64,   # Reverb Color
    148: 100,  # Reverb Time
    161: 64,   # LFO 1 Speed
    263: 90,   # Mod 1 Amount (LFO1 -> O1 Pitch)
}

PARAMS = [
    17, 18, 19, 24,        # Osc 2
    33, 34, 35, 40,        # Osc 3
    49, 71,                # sync, ringmod
    63, 65,                # mixer levels
    59,                    # unisono detune
    98, 100, 106, 117,     # filter 2
    129, 130, 131,         # FX1
    145, 147, 148,         # FX2
    161,                   # LFO 1 speed
    199, 201, 202,         # filter envelope
    261, 262, 263,         # mod matrix row 1
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    init = P.load_init()
    sd = bytearray(init["sdata"])
    for idx, raw in VARIANT.items():
        sd[idx] = raw
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
    var = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
    base_sd = bytes(sd)
    base_ov, _ = qpat_map.blofeld_to_qpat_params(var)
    print(f"test-B variant: {len(VARIANT)} changes -> {len(base_ov)} Iridium params", flush=True)

    try:
        done = {(r["idx"], r["raw"]) for r in map(json.loads, LOG.read_text().splitlines())} \
            if LOG.exists() else set()
    except Exception:
        done = set()

    irr = Iridium()
    bl = midi.connect("blofeld")
    touched = set()
    try:
        bl.send_sysex(bd.build_sndd(base_sd, bb=0x7F, nn=0x00))
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        base_vecs = {"blofeld": [], "iridium": []}
        for rep in range(2):
            d = P.rec_once(bl, irr)
            for name in ("blofeld", "iridium"):
                x = np.mean(d[list(audio.CHANNELS[name]), :], axis=0)
                np.save(OUT / f"b_init_{name}_{rep}.npy", x)
                base_vecs[name].append(P.effect_vector(x))
        noise = {n: float(np.linalg.norm(base_vecs[n][0] - base_vecs[n][1])) for n in base_vecs}
        thresh = max(P.THR, 2.5 * max(noise.values()))
        bvec = {n: np.mean(base_vecs[n], axis=0) for n in base_vecs}
        print(f"baseline noise: {noise}", flush=True)

        with LOG.open("a") as log:
            log.write(json.dumps({"kind": "baseline", "variant": "B", "noise": noise,
                                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            for pi, idx in enumerate(PARAMS, 1):
                name = bd.SDATA[idx][0]
                for raw in P.values_for(idx):
                    if (idx, raw) in done:
                        continue
                    if touched:
                        irr.set_many([(k, P.base_value(k)) for k in touched])
                        touched = set()
                    sd2 = bytearray(base_sd)
                    sd2[idx] = raw
                    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd2, bd.checksum(bytes(sd2))]
                    p2 = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
                    ov, _ = qpat_map.blofeld_to_qpat_params(p2)
                    keys = {k: v[0] for k, v in ov.items()
                            if k not in base_ov or abs(v[0] - base_ov[k][0]) > 1e-9}
                    bl.send_sysex(bd.build_sndd(bytes(sd2), bb=0x7F, nn=0x00))
                    if keys:
                        irr.set_many(sorted(keys.items()))
                        touched |= set(keys)
                    time.sleep(0.15)
                    d = P.rec_once(bl, irr)
                    vecs, feats = {}, {}
                    for nm in ("blofeld", "iridium"):
                        x = np.mean(d[list(audio.CHANNELS[nm]), :], axis=0)
                        np.save(OUT / f"b_{idx:03d}_{raw:03d}_{nm}.npy", x)
                        vecs[nm] = P.effect_vector(x)
                        feats[nm] = sim.features(x, sr=audio.SAMPLERATE, n_bands=48)
                    db = vecs["blofeld"] - bvec["blofeld"]
                    di = vecs["iridium"] - bvec["iridium"]
                    status, mb, mi, cos = P.classify(db, di, thresh)
                    pair = sim.compare(feats["blofeld"], feats["iridium"])["score"]
                    row = {"kind": "row", "variant": "B", "idx": idx, "param": name,
                           "enum": bd.SDATA[idx][1] is not None, "raw": raw,
                           "iridium_keys": sorted(keys), "status": status,
                           "mag_b": round(mb, 4), "mag_i": round(mi, 4),
                           "cos": None if cos is None else round(cos, 4),
                           "pair_score": round(pair, 1),
                           "time": time.strftime("%H:%M:%S")}
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    print(f"{pi:2d}/{len(PARAMS)} B {name:30s} {raw:3d} {status:9s} "
                          f"B {mb:5.2f} I {mi:5.2f} cos {cos if cos is None else round(cos,2)}",
                          flush=True)
    finally:
        irr.close()
        bl.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
