#!/usr/bin/env python3
"""Release sweep: captures the release phase by sending note-off during the recording.

The main sweep holds the note through the whole recording (attack/decay/sustain).
Release parameters therefore need this separate run.

Run:  python3 scripts/profile_release_sweep.py
Writes recordings/profile_testb_release.jsonl, npy prefix br_.
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

from bloridium import audio, blofeld_dump as bd, midi, qpat_map, sim  # noqa: E402
from _device_tool import Iridium  # noqa: E402
import profile_init_sweep as P  # noqa: E402
import _measure as _M  # noqa: E402

OUT = REPO / "recordings/profile"
LOG = REPO / "recordings/profile_testb_release.jsonl"
PREFIX = "br_"
PARAMS = [217, 205, 229, 241]

CONFIGS = {
    "release": dict(log="profile_testb_release.jsonl", prefix="br_", variant="release",
                    params=[217, 205, 229, 241],
                    over={87: 96, 202: 100, 217: 127}),
    # Block 4: filter envelope release, audible during a long amp release
    "fe4": dict(log="profile_testb_release_fe4.jsonl", prefix="bfr_", variant="fe4_release",
                params=[205], over={78: 70, 87: 110, 202: 60, 217: 127}),
    "fe4b": dict(log="profile_testb_release_fe4b.jsonl", prefix="bfrb_", variant="fe4b_release",
                 params=[205], over={78: 60, 87: 120, 202: 0, 217: 127}),
}
PRE, HOLD, TAIL = 1.5, 1.2, 4.2   # note-on at PRE, note-off at PRE+HOLD, record total TAIL


def record_with_release(bl, irr) -> np.ndarray:
    """Start ffmpeg, play a note, release it mid-recording, return 20-channel audio."""
    s = audio.settings()
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "avfoundation",
           "-i", f":{s['device']}", "-t", f"{TAIL:.3f}", "-ar", str(s["samplerate"]),
           "-f", "f32le", "-"]
    for attempt in range(4):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            time.sleep(PRE)
            for ch in range(16):
                bl.control_change(123, 0, channel=ch)
                bl.control_change(7, 127, channel=ch)
            irr.out.send(mido.Message("control_change", control=123, value=0, channel=5))
            bl.note_on(note=60, velocity=100)
            irr.out.send(mido.Message("note_on", note=60, velocity=100, channel=5))
            time.sleep(HOLD)
            bl.note_off(note=60)
            irr.out.send(mido.Message("note_off", note=60, velocity=0, channel=5))
            raw, _ = proc.communicate(timeout=TAIL + 20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            time.sleep(1.5)
            continue
        finally:
            if proc.poll() is None:
                proc.kill()
        break
    else:
        raise RuntimeError("ffmpeg konnte das Interface nicht öffnen")
    data = np.frombuffer(raw, dtype=np.float32)
    n = s["raw_channels"]
    data = data[: data.size - (data.size % n)].reshape(-1, n)
    return data.T


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "release"
    cfg = CONFIGS[mode]
    LOG = REPO / "recordings" / cfg["log"]
    PREFIX = cfg["prefix"]
    INIT_VARIANT = cfg["variant"]
    params = cfg["params"]
    init = P.load_init()
    sd = bytearray(init["sdata"])
    for k, v in cfg["over"].items():
        sd[k] = v
    base_sd = bytes(sd)
    var = bd.parse_sndd(bytes([0xF0, 0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd,
                               bd.checksum(bytes(sd)), 0xF7]))
    base_ov, _ = qpat_map.blofeld_to_qpat_params(var)

    from bloridium import qpat
    _init_vals = {k: v["value"] for k, v in qpat.load(REPO / "dumps/00000-.qpat")["params"].items()}

    def base_val(k):
        return base_ov[k][0] if k in base_ov else float(_init_vals.get(k, 0.0))

    irr = Iridium()
    bl = midi.connect("blofeld")
    touched = set()
    try:
        if not _M.load_sndd_verified(bl, base_sd):
            raise RuntimeError("Blofeld Release-Dump nicht verifiziert")
        irr.cmd("init-patch", wait=0.8)
        irr.set_many([(k, v[0]) for k, v in sorted(base_ov.items())])
        irr.set_many([("FX1Type", 0.0), ("FX2Type", 0.0)])  # dry
        base_vecs = {"blofeld": [], "iridium": []}
        for rep in range(2):
            d = record_with_release(bl, irr)
            for name in ("blofeld", "iridium"):
                x = np.mean(d[list(audio.CHANNELS[name]), :], axis=0)
                np.save(OUT / f"{PREFIX}init_{name}_{rep}.npy", x)
                base_vecs[name].append(P.effect_vector(x))
        noise = {n: float(np.linalg.norm(base_vecs[n][0] - base_vecs[n][1])) for n in base_vecs}
        thresh = max(P.THR, 1.5 * max(noise.values()))
        bvec = {n: np.mean(base_vecs[n], axis=0) for n in base_vecs}
        print(f"baseline noise: {noise} -> threshold {thresh:.2f}", flush=True)

        with LOG.open("a") as log:
            log.write(json.dumps({"kind": "baseline", "variant": INIT_VARIANT, "prefix": PREFIX,
                                  "noise": noise, "threshold": thresh,
                                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            for idx in params:
                name = bd.SDATA[idx][0]
                for raw in P.values_for(idx):
                    if touched:
                        irr.set_many([(k, base_val(k)) for k in touched])
                        touched = set()
                    sd2 = bytearray(base_sd)
                    sd2[idx] = raw
                    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd2, bd.checksum(bytes(sd2))]
                    p2 = bd.parse_sndd(bytes([0xF0, *body, 0xF7]))
                    ov, _ = qpat_map.blofeld_to_qpat_params(p2)
                    keys = {k: v[0] for k, v in ov.items()
                            if k not in base_ov or abs(v[0] - base_ov[k][0]) > 1e-9}
                    if not _M.load_sndd_verified(bl, bytes(sd2)):
                        raise RuntimeError(f"SNDD-Readback fehlgeschlagen: idx {idx} raw {raw}")
                    if keys:
                        irr.set_many(sorted(keys.items()))
                        touched |= set(keys)
                    time.sleep(0.15)
                    d = record_with_release(bl, irr)
                    vecs = {}
                    for nm in ("blofeld", "iridium"):
                        x = np.mean(d[list(audio.CHANNELS[nm]), :], axis=0)
                        np.save(OUT / f"{PREFIX}{idx:03d}_{raw:03d}_{nm}.npy", x)
                        vecs[nm] = P.effect_vector(x)
                    db = vecs["blofeld"] - bvec["blofeld"]
                    di = vecs["iridium"] - bvec["iridium"]
                    status, mb, mi, cos = P.classify(db, di, thresh)
                    row = {"kind": "row", "precomputed": True, "variant": INIT_VARIANT,
                           "prefix": PREFIX, "idx": idx,
                           "param": name, "enum": bd.SDATA[idx][1] is not None, "raw": raw,
                           "iridium_keys": sorted(keys), "status": status,
                           "mag_b": round(mb, 4), "mag_i": round(mi, 4),
                           "cos": None if cos is None else round(cos, 4),
                           "time": time.strftime("%H:%M:%S")}
                    log.write(json.dumps(row) + "\n")
                    log.flush()
                    print(f"{name:28s} {raw:3d} {status:9s} B {mb:5.2f} I {mi:5.2f} "
                          f"cos {cos if cos is None else round(cos, 2)}", flush=True)
    finally:
        irr.close()
        bl.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
