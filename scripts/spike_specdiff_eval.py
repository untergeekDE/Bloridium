"""Spike/Eval: specdiff (DSP + d1-omni vision) gegen die echten 20261115-Checkpoint-WAVs
und die User-Ratings (recordings/phaseb_ratings_raw.json, 9 Locs, n72 w0).

Output: recordings/specdiff_eval_<ts>.json + Tabelle + Spearman + Label-vs-Text.
Run: python3 scripts/spike_specdiff_eval.py [--no-vision]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from sim_eval_offline import spearman  # noqa: E402
from bloridium import specdiff  # noqa: E402

REC = REPO / "recordings"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-vision", action="store_true")
    ap.add_argument("--model", default=specdiff.DEFAULT_SPECDIFF_MODEL)
    args = ap.parse_args()

    ratings = {k: v for k, v in
               json.loads((REC / "phaseb_ratings_raw.json").read_text()).items()}
    locs = sorted(ratings)

    backend = None if args.no_vision else specdiff.build_backend(True, args.model, "systemone")
    if not args.no_vision and backend is None:
        print("vision backend nicht verfuegbar -> nur DSP", file=sys.stderr)

    rows = []
    for loc in locs:
        blo = sorted(REC.glob(f"ab_{loc}_20261115_*_n72_w0_blo.wav"))
        irr = sorted(REC.glob(f"ab_{loc}_20261115_*_n72_w0_irr.wav"))
        assert blo and irr, f"{loc}: WAV pair missing"
        a, b, sr = specdiff.load_pair(blo[-1], irr[-1])
        t0 = time.time()
        r = specdiff.interpret_pair(a, b, sr, backend=backend)
        lab = r["labels"]
        row = {"loc": loc, "rating": ratings[loc]["score"], "text": ratings[loc]["text"],
               "score_dsp": round(r["score"], 2), "source": r["source"],
               "severity": lab["severity"], "spread": lab["spread"],
               "temporal": lab["temporal"], "bands": lab["bands"],
               "severity_db": round(r["dsp"]["severity_db"], 2),
               "spread_frac": round(r["dsp"]["spread_frac"], 3),
               "band_mean_db": {k: round(v, 2) for k, v in r["dsp"]["band_mean_db"].items()},
               "confidence": r["confidence"], "secs": round(time.time() - t0, 1)}
        rows.append(row)
        print(f"{loc}: rating={row['rating']:3d} specdiff={row['score_dsp']:5.1f} "
              f"{lab['severity']}/{lab['spread']}/{lab['temporal']} bands={lab['bands']} "
              f"({r['source']}, {row['secs']}s) | {ratings[loc]['text'][:60]}", flush=True)

    rho_dsp = spearman([r["rating"] for r in rows], [r["score_dsp"] for r in rows])
    print(f"\nSpearman(specdiff_score_dsp, rating) n={len(rows)}: rho={rho_dsp:+.3f}")

    # Label-vs-Text: erwartete Band-Richtung aus Schlagworten des User-Feedbacks
    expect = {"dunkler": "high", "darker": "high", "abgefiltert": "high",
              "filter zu weit geschlossen": "high", "hohl": "high",
              "oberton": "mid", "voller": "low", "leiser": "level"}
    hits = tot = 0
    for r in rows:
        t = r["text"].lower()
        for kw, band in expect.items():
            if kw in t:
                tot += 1
                ok = (band == "level") or (band in r["bands"])
                hits += ok
                print(f"  text-hit {r['loc']}: '{kw}' -> band {band}: "
                      f"{'OK' if ok else 'MISS'} (bands={r['bands']})")
    if tot:
        print(f"text-label hits: {hits}/{tot}")

    out = {"ts": time.strftime("%Y%m%d_%H%M%S"), "model": args.model,
           "vision": not args.no_vision, "spearman_specdiff_vs_rating": round(rho_dsp, 4),
           "rows": rows}
    path = REC / f"specdiff_eval_{out['ts']}.json"
    path.write_text(json.dumps(out, indent=1))
    print(f"\ngeschrieben: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
