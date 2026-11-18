#!/usr/bin/env python3
"""Spike 2026-11-15: d1-omni as difference profiler (noul questions, English) on the
9 existing A/B WAV pairs — d1-omni:600m vs d1-omni:2b.

Per pair ONE /v1/systemone call with images=[specA, specB] (spec2img) and 8 questions:
  similarity (score, 10 levels -> 0-100) + 7 noul profile questions.
Evaluation: Spearman vs user ratings (recordings/phaseb_ratings_raw.json)
for score / same_overall / diff_count per model.
Output: recordings/d1_profile_eval_<ts>.json. Throwaway spike.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spike_d1_omni_eval import (CRITERIA, LOCS, STATE_2IMG, b64, latest_pair,
                                load_wav, rank, spec_png, spearman)

REPO = Path(__file__).resolve().parent.parent
HOST = "http://localhost:11434"
MODELS = ["d1-omni:600m", "d1-omni:2b"]

QUESTIONS = {
    "similarity": {
        "type": "score",
        "instructions": ("How similar does sound B sound to reference sound A? "
                         "Judge timbre, spectrum and envelope. Higher = more similar."),
        "criteria": CRITERIA,
    },
    "same_pitch": {"type": "noul", "instructions": "Do A and B have the same pitch?"},
    "octave_lower": {"type": "noul", "instructions": "Is B exactly one octave lower than A?"},
    "brighter": {"type": "noul",
                 "instructions": "Does B have more high-frequency energy (sound brighter) than A?"},
    "darker": {"type": "noul",
               "instructions": "Does B have less high-frequency energy (sound darker, more filtered) than A?"},
    "noisier": {"type": "noul", "instructions": "Does B sound noisier or more grainy than A?"},
    "punchier": {"type": "noul",
                 "instructions": "Does B have a sharper, stronger attack (more punch) than A?"},
    "same_overall": {"type": "noul",
                     "instructions": "Overall, do A and B sound like the same sound?"},
}
DIFF_QUESTIONS = ["octave_lower", "brighter", "darker", "noisier", "punchier"]
NOUL_QUESTIONS = [q for q in QUESTIONS if QUESTIONS[q]["type"] == "noul"]


def systemone(model, images_b64, state, questions, timeout=600):
    payload = {"model": model, "state": state, "images": images_b64, "questions": questions}
    r = requests.post(f"{HOST}/v1/systemone", json=payload, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"systemone[{model}] HTTP {r.status_code}: {r.text[:300]}")
    return r.json()["answers"]


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ratings = json.load(open(REPO / "recordings" / "phaseb_ratings_raw.json"))
    out = {"ts": ts, "models": MODELS, "questions": {k: v["instructions"] for k, v in QUESTIONS.items()},
           "pairs": {}}
    with tempfile.TemporaryDirectory() as td:
        for loc in LOCS:
            blo_p, irr_p = latest_pair(loc)
            xa, sr = load_wav(blo_p)
            xb, _ = load_wav(irr_p)
            spa = spec_png(xa, sr, Path(td) / f"{loc}_a.png")
            spb = spec_png(xb, sr, Path(td) / f"{loc}_b.png")
            imgs = [b64(spa), b64(spb)]
            rec = {"user": ratings[loc]["score"], "user_text": ratings[loc]["text"], "models": {}}
            for model in MODELS:
                ans = systemone(model, imgs, STATE_2IMG, QUESTIONS)
                sim = ans["similarity"]
                probs = {q: round(float(ans[q]["noul"]), 3) for q in NOUL_QUESTIONS}
                flags = [q for q in DIFF_QUESTIONS if probs[q] >= 0.5]
                rec["models"][model] = {
                    "score": round(100.0 * float(sim["score"]) / (len(CRITERIA) - 1), 1),
                    "conf": round(float(sim.get("confidence", 0)), 3),
                    "probs": probs,
                    "flags": flags,
                    "diff_count": len(flags),
                    "same_overall": round(100.0 * probs["same_overall"], 1),
                }
            out["pairs"][loc] = rec
            m2 = rec["models"][MODELS[1]]
            print(f"{loc}: user={rec['user']:3d} | 600m score={rec['models'][MODELS[0]]['score']:5.1f} "
                  f"2b score={m2['score']:5.1f} same_overall={m2['same_overall']:5.1f} "
                  f"diff={m2['diff_count']} {m2['flags']}")

    user = [out["pairs"][k]["user"] for k in LOCS]
    sp = {}
    for model in MODELS:
        sp[f"score_{model}"] = round(spearman(user, [out["pairs"][k]["models"][model]["score"] for k in LOCS]), 3)
        sp[f"same_overall_{model}"] = round(spearman(user, [out["pairs"][k]["models"][model]["same_overall"] for k in LOCS]), 3)
        sp[f"diff_count_{model}"] = round(spearman(user, [out["pairs"][k]["models"][model]["diff_count"] for k in LOCS]), 3)
    out["spearman_user"] = sp
    print("\nSpearman vs user:", json.dumps(sp, indent=1))
    outp = REPO / "recordings" / f"d1_profile_eval_{ts}.json"
    outp.write_text(json.dumps(out, indent=2))
    print("written:", outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
