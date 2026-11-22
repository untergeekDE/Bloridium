#!/usr/bin/env python3
"""Evaluate prognosis models on a measurement log (per-location means).

The question this answers: is a model's reported R² real, or an artifact of
the data it was trained on? Point it at a log the model has never seen.

Usage:
    python3 scripts/eval_model_bank.py --log recordings/sim_log_bankE.jsonl \
        --model models/prognose_rf.pkl --model models/prognose_rf_v5.pkl
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bloridium import blofeld_dump as bd, prognose  # noqa: E402


def per_loc_scores(log_path: Path, target: str = "score") -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        res, meta = e.get("result") or {}, e.get("meta") or {}
        loc = meta.get("blofeld")
        if not loc or res.get("score") is None:
            continue
        acc.setdefault(loc, []).append(float(res[target] if target in res else res["score"]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def evaluate(model_path: Path, scores: dict[str, float], dumps: Path) -> dict:
    bundle = prognose.load_model(model_path)
    rf = bundle["model"]
    locs, y, p = [], [], []
    for loc, score in sorted(scores.items()):
        try:
            dump = prognose.find_dump(dumps, loc)
        except FileNotFoundError:
            continue
        x = prognose.feature_vector(bd.parse_sndd(dump.read_bytes())).reshape(1, -1)
        locs.append(loc)
        y.append(score)
        p.append(float(rf.predict(x)[0]))
    y, p = np.asarray(y), np.asarray(p)
    err = p - y
    r2 = 1.0 - float(np.sum(err ** 2)) / float(np.sum((y - y.mean()) ** 2))
    rank = np.argsort(np.argsort(p)), np.argsort(np.argsort(y))
    spear = float(np.corrcoef(*rank)[0, 1])
    # regression slope of true on predicted: 1 = calibrated, 0 = no signal.
    # Unlike R2 it survives a pure dataset mean shift (bias).
    b = float(np.polyfit(p, y, 1)[0])
    return {"model": model_path.name, "n": len(y),
            "mae": float(np.mean(np.abs(err))), "bias": float(np.mean(err)),
            "r2": r2, "slope": b, "spearman": spear,
            "spread_true": float(y.std()), "spread_pred": float(p.std())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--dumps", type=Path, default=REPO / "dumps")
    ap.add_argument("--target", default="score")
    ap.add_argument("--model", type=Path, action="append", required=True)
    args = ap.parse_args()

    scores = per_loc_scores(args.log, args.target)
    print(f"{args.log.name}: {len(scores)} locations, "
          f"mean {np.mean(list(scores.values())):.1f}, "
          f"sd {np.std(list(scores.values())):.1f}")
    print(f"{'model':<24} {'n':>4} {'MAE':>6} {'bias':>7} {'R2':>7} {'slope':>6} "
          f"{'spearman':>9} {'sd_true':>8} {'sd_pred':>8}")
    for m in args.model:
        r = evaluate(m, scores, args.dumps)
        print(f"{r['model']:<24} {r['n']:>4} {r['mae']:>6.2f} {r['bias']:>+7.2f} "
              f"{r['r2']:>7.3f} {r['slope']:>6.2f} {r['spearman']:>9.3f} "
              f"{r['spread_true']:>8.2f} {r['spread_pred']:>8.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
