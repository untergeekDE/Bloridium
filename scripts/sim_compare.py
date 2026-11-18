#!/usr/bin/env python3
"""sim_compare.py – similarity score Blofeld vs Iridium.

Offline:  python3 scripts/sim_compare.py --npy A.npy B.npy [--log PATH] [--meta k=v ...]
Live:     python3 scripts/sim_compare.py --live [--note 60] [--dur 1.6]
              [--blofeld A043] [--iridium-slot 207] [--log PATH] [--meta k=v ...]
Phase B:  additionally --embed (CLAP-GGUF, models/) and --llm (ollama), --strict,
          --models-dir; exit 3 on strict+missing backend, else degrade (null in log).

.npy: shape (N,) or (ch, N) – is averaged. Live: plays a note on both
synths (Blofeld ch5, Iridium ch6-9), records all 20 Scarlett channels,
compares Blofeld In3/4 vs Iridium In5/6. Log: JSONL (default recordings/sim_log.jsonl).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, sim, sim_embed


def _load_npy(p) -> np.ndarray:
    x = np.asarray(np.load(p), dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=0)
    return x.ravel()


def _meta(pairs) -> dict:
    d = {}
    for kv in pairs or []:
        k, _, v = kv.partition("=")
        d[k] = v
    return d


print_result = sim_embed.print_result  # shared output (sim_embed)


def _score_pair(args, a, b, meta):
    """Build backends + score_pair_embed; strict errors -> pass the RuntimeError through."""
    clap, ollama = sim_embed.build_backends(args.models_dir, args.embed, args.llm)
    d1 = sim_embed.build_profile_backend(getattr(args, "profile", False),
                                         getattr(args, "d1_model", sim_embed.DEFAULT_D1_MODEL))
    return sim_embed.score_pair_embed(a, b, sr=audio.SAMPLERATE, meta=meta,
                                      log_path=args.log, clap=clap, ollama=ollama,
                                      use_llm=args.llm, strict=args.strict,
                                      profile_backend=d1,
                                       spec_png_dir=getattr(args, "spec_png_dir", None))


def run_npy(pa, pb, log, meta, args) -> int:
    a, b = _load_npy(pa), _load_npy(pb)
    try:
        r = _score_pair(args, a, b, meta)
    except RuntimeError as e:
        print(f"ERROR (strict): {e}", file=sys.stderr)
        return 3
    print_result(r, str(pa), str(pb))
    return 0 if r["score"] is not None else 1


def run_live(note, dur, blofeld, slot, log, meta, args) -> int:
    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    try:
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)   # All Notes Off
        for ch in range(16):
            blo.control_change(7, 127, channel=ch)       # only Blofeld: volume full
            # Iridium: do NOT send CC7 -- with the rdb-.mimap CC7 = Filter1 Amount!
        time.sleep(0.4)
        blo.note_on(note=note, velocity=100, channel=blo.channel)
        for ch in (5,):  # only Part 1 (ch6) - monophonic like Blofeld/keyboard
            irr.note_on(note=note, velocity=100, channel=ch)
        time.sleep(0.25)                                 # wait for attack
        d = audio.record(duration=dur, channels=None)
        blo.note_off(note=note, channel=blo.channel)
        for ch in (5,):  # only Part 1 (ch6) - monophonic like Blofeld/keyboard
            irr.note_off(note=note, channel=ch)
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
    finally:
        blo.close()
        irr.close()
    bx = np.asarray(d[audio.CHANNELS["blofeld"], :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(d[audio.CHANNELS["iridium"], :], dtype=np.float64).mean(axis=0)
    m = dict(meta)
    m.update({"mode": "live", "note": note, "blofeld": blofeld, "iridium_slot": slot})
    try:
        r = _score_pair(args, bx, ix, m)
    except RuntimeError as e:
        print(f"ERROR (strict): {e}", file=sys.stderr)
        return 3
    print_result(r, f"blofeld:{blofeld}", f"iridium:{slot}")
    return 0 if r["score"] is not None else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npy", nargs=2, metavar=("A", "B"), help="offline: compare two .npy files")
    ap.add_argument("--live", action="store_true", help="measure live (both synths play)")
    ap.add_argument("--note", type=int, default=60)
    ap.add_argument("--dur", type=float, default=1.6)
    ap.add_argument("--blofeld", default="A043")
    ap.add_argument("--iridium-slot", default="?")
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    ap.add_argument("--meta", nargs="*", default=[], help="k=v pairs for the log")
    ap.add_argument("--embed", action="store_true", help="Phase B: add CLAP embedding score")
    ap.add_argument("--llm", action="store_true", help="Phase B: add ollama LLM verdict")
    ap.add_argument("--profile", action="store_true",
                    help="Phase B: add d1-omni noul profile (explanation layer)")
    ap.add_argument("--d1-model", default=sim_embed.DEFAULT_D1_MODEL)
    ap.add_argument("--strict", action="store_true",
                    help="missing backend is fatal (exit 3) instead of degrade")
    ap.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ap.add_argument("--spec-png-dir", default=None,
                    help="render a side-by-side spectrogram PNG (A|B|delta dB) and link it "
                         "in the log (default: off)")
    args = ap.parse_args(argv)
    meta = _meta(args.meta)
    if args.npy:
        return run_npy(args.npy[0], args.npy[1], args.log, meta, args)
    if args.live:
        return run_live(args.note, args.dur, args.blofeld, args.iridium_slot, args.log, meta, args)
    ap.error("either --npy A B or --live")
    return 2


if __name__ == "__main__":
    sys.exit(main())
