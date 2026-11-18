#!/usr/bin/env python3
"""sim_eval_offline.py – Phase-B eval on all .npy pairs in recordings/.

Finds pairs <base>_blofeld.npy / <base>_iridium.npy, evaluates each with Phase A +
CLAP embedding (combined), writes recordings/phaseb_eval_<ts>.json and prints
a table. Optional --ratings ratings.json ({"<base>": 0-100}) -> Spearman
rank correlation of score/embed_score/combined against the ratings into the JSON.

Usage:  python3 scripts/sim_eval_offline.py [--rec-dir recordings] [--models-dir models]
             [--out PATH] [--ratings PATH]
Exit: 0 ok (missing GGUF degrades: embed_score null), 2 no pairs found.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import sim_embed


def find_pairs(rec_dir) -> list[tuple[str, Path, Path]]:
    """All <base>_blofeld.npy with an existing <base>_iridium.npy, sorted."""
    rec_dir = Path(rec_dir)
    pairs = []
    for b in sorted(rec_dir.glob("*_blofeld.npy")):
        i = b.with_name(b.name[: -len("_blofeld.npy")] + "_iridium.npy")
        if i.exists():
            pairs.append((b.name[: -len("_blofeld.npy")], b, i))
    return pairs


def spearman(a, b) -> float:
    """Spearman rank correlation (numpy, ties averaged); n<2 or constant series -> 0.0."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size < 2 or a.size != b.size:
        return 0.0

    def ranks(x):
        order = np.argsort(x, kind="mergesort")
        r = np.empty(x.size)
        r[order] = np.arange(x.size)
        _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
        sums = np.zeros(len(counts))
        np.add.at(sums, inv, r)
        return sums[inv] / counts[inv]

    ra, rb = ranks(a), ranks(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    d = float(np.sqrt((ra ** 2).sum() * (rb ** 2).sum()))
    return float((ra * rb).sum() / d) if d > 0 else 0.0


def _mono(p) -> np.ndarray:
    x = np.asarray(np.load(p), dtype=np.float64)
    return x.mean(axis=0) if x.ndim > 1 else x.ravel()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rec-dir", default=str(sim_embed.REPO / "recordings"))
    ap.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ap.add_argument("--out", default=None, help="Default: <rec-dir>/phaseb_eval_<ts>.json")
    ap.add_argument("--ratings", default=None, help="JSON {\"<base>\": 0-100} for Spearman")
    args = ap.parse_args(argv)

    pairs = find_pairs(args.rec_dir)
    if not pairs:
        print(f"no .npy pairs in {args.rec_dir}", file=sys.stderr)
        return 2

    gguf = Path(args.models_dir) / sim_embed.CLAP_GGUF_NAME
    clap = None
    if gguf.exists():
        try:
            clap = sim_embed.ClapBackend(gguf)
        except Exception as e:
            print(f"WARNING clap: {e}", file=sys.stderr)
    else:
        print(f"WARNING: {gguf} missing (scripts/fetch_models.py) – embed_score null",
              file=sys.stderr)

    rows = []
    print(f"{'Pair':<34} {'score':>7} {'embed':>7} {'combined':>9}  verdict / backend_error")
    for base, pa, pb in pairs:
        r = sim_embed.score_pair_embed(_mono(pa), _mono(pb), sr=48000,
                                       meta={"run": "eval", "pair": base},
                                       log_path=None, clap=clap)
        row = {"pair": base, "score": r["score"], "embed_score": r["embed_score"],
               "combined": r["combined"], "verdict": r["verdict"],
               "backend_error": r["backend_error"]}
        rows.append(row)
        print(f"{base:<34} {str(r['score']):>7} {str(r['embed_score']):>7} "
              f"{str(r['combined']):>9}  {r['verdict']}"
              + (f" / {r['backend_error']}" if r["backend_error"] else ""))

    ratings = None
    spearman_out = None
    if args.ratings:
        ratings = json.loads(Path(args.ratings).read_text())
        common = [r for r in rows if r["pair"] in ratings and r["score"] is not None]
        if len(common) >= 2:
            ref = [float(ratings[r["pair"]]) for r in common]
            spearman_out = {
                "score": spearman([r["score"] for r in common], ref),
                "embed_score": spearman([r["embed_score"] if r["embed_score"] is not None
                                          else -1 for r in common], ref),
                "combined": spearman([r["combined"] for r in common], ref),
            }
            print("\nSpearman vs ratings:",
                  {k: round(v, 3) for k, v in spearman_out.items()})

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out) if args.out else Path(args.rec_dir) / f"phaseb_eval_{ts}.json"
    out.write_text(json.dumps({
        "ts": ts,
        "models": {"clap_gguf": sim_embed.CLAP_GGUF_NAME if clap else None},
        "ratings": ratings, "spearman": spearman_out, "rows": rows,
    }, indent=2))
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
