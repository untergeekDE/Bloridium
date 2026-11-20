#!/usr/bin/env python3
"""rescore_v2.py – vorhandene ab_*-Aufnahmen offline mit Score v2 neu bewerten.

Die rf-dataset-Messungen (2026-11-19) wurden ohne Roh-Audio geloggt und sind daher
nicht re-scorbar; die aelteren ab_*-Paare (npy/wav in recordings/) schon. Dieses Script
findet alle vollstaendigen Paare, laedt sie mono und scored sie mit
sim_embed.score_pair_embed – damit automatisch SCORE_VERSION=2 – plus optional
CLAP-Embed, ollama-LLM (lfm3-omni) und d1-Profil (d1-omni), pegel-matched (norm_pegel).

Jedes Paar landet als eigene Zeile im Ziel-Log (Default recordings/sim_log_v2.jsonl),
damit das alte sim_log.jsonl (v1) unberuehrt bleibt. meta enthaelt blofeld-Loc
(aus dem Dateinamen), note (aus _nXX) und mode="npy-v2" -> prognose train mit
--min-score-version 2 pickt genau diese Zeilen.

Aufruf:
  python3 scripts/rescore_v2.py                          # alle Paare, embed+llm+d1
  python3 scripts/rescore_v2.py --no-llm --no-d1         # nur v2 + embed
  python3 scripts/rescore_v2.py --rec-dir recordings --log recordings/sim_log_v2.jsonl --limit 5
"""

from __future__ import annotations

import argparse
import re
import sys
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bloridium import audio, sim_embed  # noqa: E402

DEFAULT_REC_DIR = REPO / "recordings"
DEFAULT_LOG = REPO / "recordings" / "sim_log_v2.jsonl"

# ab_A001_20261114_154306_blofeld.npy | ab_A043_20261114_174637_n72_blo.wav
# ab_A008_20261115_140050_n72_w100_irr.wav
_RE_NPY = re.compile(
    r"^ab_(?P<loc>[A-Z]\d{3})_(?P<ts>\d{8}_\d{6})(?P<mid>(?:_n\d+)?(?:_w\d+)?)"
    r"_(?P<side>blofeld|iridium)\.npy$")
_RE_WAV = re.compile(
    r"^ab_(?P<loc>[A-Z]\d{3})_(?P<ts>\d{8}_\d{6})(?P<mid>(?:_n\d+)?(?:_w\d+)?)"
    r"_(?P<side>blo|irr)\.wav$")


def discover_pairs(rec_dir) -> list[dict]:
    """Alle vollstaendigen (A,B)-Paare in rec_dir -> [{loc, note, extra, ext, a, b}]."""
    rec_dir = Path(rec_dir)
    sides: dict[tuple, dict] = {}
    for f in sorted(rec_dir.iterdir()):
        m = _RE_NPY.match(f.name)
        if m:
            ext, side_map = "npy", {"blofeld": "a", "iridium": "b"}
        else:
            m = _RE_WAV.match(f.name)
            if not m:
                continue
            ext, side_map = "wav", {"blo": "a", "irr": "b"}
        g = m.groupdict()
        note_m = re.search(r"_n(\d+)", g["mid"])
        w_m = re.search(r"_w(\d+)", g["mid"])
        key = (g["loc"], g["ts"], g["mid"], ext)
        e = sides.setdefault(key, {"loc": g["loc"], "ts": g["ts"], "ext": ext,
                                   "note": int(note_m.group(1)) if note_m else None,
                                   "extra": w_m.group(0)[1:] if w_m else "",
                                   "a": None, "b": None})
        e[side_map[g["side"]]] = str(f)
    return [v for v in sides.values() if v["a"] and v["b"]]


def load_mono(path) -> np.ndarray:
    """npy (mono/stereo) oder wav (mono) -> 1-D float64 mono."""
    p = Path(path)
    if p.suffix == ".npy":
        x = np.asarray(np.load(p), dtype=np.float64)
        return x.mean(axis=0) if x.ndim > 1 else x.ravel()
    with wave.open(str(p), "rb") as w:
        n = w.getnframes()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        x = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) / 255.0 - 0.5
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rec-dir", default=str(DEFAULT_REC_DIR))
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ap.add_argument("--no-embed", action="store_true")
    ap.add_argument("--no-llm", action="store_true", help="ollama-Judge (lfm3-omni) aus")
    ap.add_argument("--no-d1", action="store_true", help="d1-Profil (d1-omni) aus")
    ap.add_argument("--d1-model", default=sim_embed.DEFAULT_D1_MODEL)
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N Paare (0=alle)")
    args = ap.parse_args(argv)

    pairs = discover_pairs(args.rec_dir)
    if args.limit:
        pairs = pairs[: args.limit]
    print(f"rescore_v2: {len(pairs)} Paare aus {args.rec_dir}, log={args.log}")
    if not pairs:
        return 1

    clap, ollama = sim_embed.build_backends(args.models_dir, not args.no_embed,
                                            not args.no_llm)
    d1 = sim_embed.build_profile_backend(not args.no_d1, args.d1_model)

    n_ok = 0
    for i, p in enumerate(pairs, 1):
        a = load_mono(p["a"])
        b = load_mono(p["b"])
        meta = {"mode": "npy-v2", "blofeld": p["loc"], "note": p["note"],
                "src": f"{p['ts']}{'_' + p['extra'] if p['extra'] else ''}.{p['ext']}",
                "rec_dir": str(args.rec_dir)}
        r = sim_embed.score_pair_embed(a, b, sr=audio.SAMPLERATE, meta=meta,
                                       log_path=args.log, clap=clap, ollama=ollama,
                                       use_llm=not args.no_llm, strict=False,
                                       profile_backend=d1, norm_pegel=True)
        n_ok += r.get("score") is not None
        sim_embed.print_result(r, f"{p['loc']} blo", f"{p['loc']} irr")
        print(f"  [{i}/{len(pairs)}]", flush=True)
    print(f"fertig: {n_ok}/{len(pairs)} mit Score -> {args.log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
