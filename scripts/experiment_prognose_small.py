#!/usr/bin/env python3
"""Small-feature prognosis experiment: 150 train / 50 test across both banks.

The full 367-param RF memorises its own log and transfers nothing between
banks. This tries a curated, physically meaningful feature set instead, on a
stratified split (75 A + 75 E train, 25 A + 25 E test) and reports 5 seeds.

Usage:
    python3 scripts/experiment_prognose_small.py
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bloridium import blofeld_dump as bd, prognose  # noqa: E402
from bloridium.prognose import RandomForestRegressor  # noqa: E402  (pure python)

LOGS = {"A": REPO / "recordings/sim_log_v5.jsonl",
        "E": REPO / "recordings/sim_log_bankE.jsonl"}

CURATED = [
    "Osc 1 Shape", "Osc 2 Shape", "Osc 3 Shape",
    "Filter 1 Type", "Filter 2 Type", "Filter Routing",
    "Filter 1 Cutoff", "Filter 2 Cutoff", "Filter 1 Resonance", "Filter 2 Resonance",
    "Filter 1 Drive", "Filter 2 Drive",
    "Filter 1 Env Amount", "Filter 2 Env Amount",
    "Amplifier Envelope Attack", "Amplifier Envelope Decay",
    "Amplifier Envelope Sustain", "Amplifier Envelope Release",
    "Amplifier Velocity", "Allocation/Unisono", "Osc 2 Sync to O3",
    "Effect 1 Type", "Effect 2 Type", "Osc 1 FM Amount",
]


def bank_scores(log: Path) -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for line in log.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        res, meta = r.get("result") or {}, r.get("meta") or {}
        if res.get("score") is not None and meta.get("blofeld"):
            acc.setdefault(meta["blofeld"], []).append(float(res["score"]))
    return {k: float(np.mean(v)) for k, v in acc.items()}


def load_rows() -> tuple[list[dict], list[dict], np.ndarray, np.ndarray]:
    parsed_rows, rows, y, banks = [], [], [], []
    for bank, log in LOGS.items():
        for loc, score in sorted(bank_scores(log).items()):
            parsed = bd.parse_sndd(prognose.find_dump(REPO / "dumps", loc).read_bytes())
            parsed_rows.append(parsed)
            rows.append(parsed["params"])
            y.append(score)
            banks.append(bank)
    return parsed_rows, rows, np.asarray(y), np.asarray(banks)


def encode(rows: list[dict], keys: list[str]) -> np.ndarray:
    """Numeric-encode the curated keys; categorical values -> sorted rank."""
    cols = []
    for k in keys:
        vals = [r.get(k) for r in rows]
        num = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(num) == len(vals):
            cols.append(np.asarray(vals, dtype=float))
            continue
        cats = sorted({str(v) for v in vals})
        cols.append(np.asarray([cats.index(str(v)) for v in vals], dtype=float))
    return np.stack(cols, axis=1)


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    err = p - y
    r2 = 1 - float((err ** 2).sum()) / float(((y - y.mean()) ** 2).sum())
    rho = float(np.corrcoef(np.argsort(np.argsort(p)), np.argsort(np.argsort(y)))[0, 1])
    slope = float(np.polyfit(p, y, 1)[0])
    return {"mae": float(np.abs(err).mean()), "r2": r2, "rho": rho, "slope": slope}


def run(X: np.ndarray, y: np.ndarray, banks: np.ndarray, seeds=(1, 2, 3),
        depth=None) -> dict:
    out, per_bank = [], {"A": [], "E": []}
    for seed in seeds:
        rng = np.random.default_rng(seed)
        tr, te = [], []
        for bank in ("A", "E"):
            idx = np.where(banks == bank)[0]
            rng.shuffle(idx)
            tr += list(idx[:75])
            te += list(idx[75:])
        tr, te = np.asarray(tr), np.asarray(te)
        rf = RandomForestRegressor(n_estimators=200, random_state=seed,
                                   max_depth=depth or 10).fit(X[tr], y[tr])
        pred = rf.predict(X[te])
        m = metrics(y[te], pred)
        m["seed"] = seed
        out.append(m)
        for bank in ("A", "E"):
            sel = banks[te] == bank
            per_bank[bank].append(metrics(y[te][sel], pred[sel])["r2"])
    res = {k: (float(np.mean([o[k] for o in out])), float(np.std([o[k] for o in out])))
           for k in ("mae", "r2", "rho", "slope")}
    res["r2_A"] = (float(np.mean(per_bank["A"])), float(np.std(per_bank["A"])))
    res["r2_E"] = (float(np.mean(per_bank["E"])), float(np.std(per_bank["E"])))
    return res


def main() -> int:
    parsed_rows, rows, y, banks = load_rows()
    print(f"n={len(y)} (A {sum(banks == 'A')}, E {sum(banks == 'E')}), "
          f"mean {y.mean():.1f}, sd {y.std():.1f}")
    Xfull = np.stack([prognose.feature_vector(p) for p in parsed_rows])
    Xcur = encode(rows, CURATED)
    print(f"full features {Xfull.shape[1]}, curated {Xcur.shape[1]}")

    # top-k curated by |pearson| computed on the FULL data only for orientation
    corr = np.asarray([abs(np.corrcoef(Xcur[:, j], y)[0, 1])
                       if Xcur[:, j].std() > 0 else 0.0
                       for j in range(Xcur.shape[1])])
    order = np.argsort(-corr)
    print("strongest curated params:",
          [(CURATED[i], round(float(corr[i]), 2)) for i in order[:6]])

    variants = [("all 367", Xfull, None), ("curated 24", Xcur, None),
                ("curated 24, depth4", Xcur, 4),
                ("curated top10", Xcur[:, order[:10]], None),
                ("curated top5", Xcur[:, order[:5]], None)]
    print(f"\n{'variant':<22} {'MAE':>13} {'R2':>15} {'R2_A':>13} {'R2_E':>13} "
          f"{'spearman':>15} {'slope':>13}")
    for name, X, depth in variants:
        r = run(X, y, banks, depth=depth)
        print(f"{name:<22} {r['mae'][0]:>6.2f}±{r['mae'][1]:<5.2f} "
              f"{r['r2'][0]:>+7.3f}±{r['r2'][1]:<6.3f} "
              f"{r['r2_A'][0]:>+6.3f} {r['r2_E'][0]:>+6.3f} "
              f"{r['rho'][0]:>+7.3f}±{r['rho'][1]:<6.3f} "
              f"{r['slope'][0]:>+6.2f}±{r['slope'][1]:<5.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
