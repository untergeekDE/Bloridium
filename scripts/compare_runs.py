#!/usr/bin/env python3
"""Compare two measurement logs per location (e.g. before/after a converter fix).

Both logs must use the same location keys (A001..A100 or E001..E100).

Usage:
    python3 scripts/compare_runs.py --old recordings/sim_log_bankE.jsonl \
        --new recordings/sim_log_bankE_v2.jsonl
    # split by "does the patch use an LFO in the mod matrix?"
    python3 scripts/compare_runs.py --old ... --new ... --split-lfo
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bloridium import blofeld_dump as bd, prognose, qpat_map  # noqa: E402


def per_loc(path: Path) -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        res, meta = r.get("result") or {}, r.get("meta") or {}
        if res.get("score") is not None and meta.get("blofeld"):
            acc.setdefault(meta["blofeld"], []).append(float(res["score"]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def lfo_loc(dumps: Path, loc: str) -> bool:
    """True if the Blofeld patch routes any LFO through a modulation slot."""
    try:
        parsed = bd.parse_sndd(prognose.find_dump(dumps, loc).read_bytes())
    except FileNotFoundError:
        return False
    p = parsed["params"]
    for i in range(1, 17):
        src = p.get(f"Modulation {i} Source")
        dst = p.get(f"Modulation {i} Destination")
        amt = p.get(f"Modulation {i} Amount")
        if isinstance(src, str) and src != "off" and "LFO" in src \
                and isinstance(dst, str) and dst != "off" \
                and isinstance(amt, (int, float)) and abs(amt - 64) > 2:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--dumps", type=Path, default=REPO / "dumps")
    ap.add_argument("--split-lfo", action="store_true",
                    help="report LFO-modulated vs static patches separately")
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()

    old, new = per_loc(args.old), per_loc(args.new)
    common = sorted(set(old) & set(new))
    if not common:
        raise SystemExit("no common locations")
    d = {k: new[k] - old[k] for k in common}
    print(f"common {len(common)} locations")
    print(f"old mean {np.mean([old[k] for k in common]):.1f} "
          f"-> new mean {np.mean([new[k] for k in common]):.1f} "
          f"({np.mean(list(d.values())):+.1f})")
    print(f"better >+1: {sum(1 for v in d.values() if v > 1)}  "
          f"worse <-1: {sum(1 for v in d.values() if v < -1)}")
    print("top gains:", [(k, round(v, 1)) for k, v in
                         sorted(d.items(), key=lambda kv: -kv[1])[:args.top]])
    print("top losses:", [(k, round(v, 1)) for k, v in
                          sorted(d.items(), key=lambda kv: kv[1])[:args.top]])

    if args.split_lfo:
        groups = {True: [], False: []}
        for k in common:
            groups[lfo_loc(args.dumps, k)].append(d[k])
        for flag, name in ((True, "LFO-modulated"), (False, "static/no LFO")):
            vals = groups[flag]
            if vals:
                print(f"{name:16s} n={len(vals):3d} delta {np.mean(vals):+.1f} "
                      f"(min {min(vals):+.1f}, max {max(vals):+.1f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
