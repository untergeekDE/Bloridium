#!/usr/bin/env python3
"""Spike 2026-11-15: d1-omni (System One /v1/systemone) als LLM-Judge fuer die
vorhandenen 9 A/B-WAV-Paare (recordings/ab_<LOC>_*_n72_{blo,irr}.wav, pegel-angeglichen).

Zwei Input-Varianten pro Paar:
  - spec2img: zwei Spektrogramm-PNGs (A, B) als `images` (Reihenfolge erklaert im state)
  - spec1img: ein Side-by-Side-PNG (links A, rechts B)
Question type "score", 10 Levels (0..9) -> llm_score = round(100*score/9);
plus noul "same_pitch". Baseline: lfm3-omni:2b via OllamaBackend.judge (audio mode)
auf denselben WAVs. Metrik: Spearman gegen Benutzer-Ratings
(recordings/phaseb_ratings_raw.json) und Phase A/embed/combined aus sim_log.jsonl
(norm_pegel-Runs). Output: recordings/d1_omni_eval_<ts>.json. Throwaway-Spike.
"""

from __future__ import annotations

import base64
import glob
import json
import sys
import tempfile
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import sim, sim_embed

REPO = Path(__file__).resolve().parent.parent
HOST = "http://localhost:11434"
D1_MODEL = "d1-omni:600m"
LOCS = ["A001", "A008", "A010", "A019", "A022", "A039", "A043", "A071", "A073"]

CRITERIA = [
    "0-9: completely different sound, nothing in common",
    "10-19: barely any similarity",
    "20-29: only remotely similar",
    "30-39: same general character but clearly different",
    "40-49: similar with clear differences",
    "50-59: similar with moderate differences",
    "60-69: quite similar, small differences",
    "70-79: very similar, minor differences",
    "80-89: nearly indistinguishable, tiny differences",
    "90-100: indistinguishable from the reference",
]

STATE_2IMG = ("Spectrograms of two short synthesizer notes, both normalized to equal peak "
              "level. Image 1 = A, the reference sound (Waldorf Blofeld). Image 2 = B, the "
              "copied sound (Waldorf Iridium).")
STATE_1IMG = ("One spectrogram image, left half = A reference (Waldorf Blofeld), right half "
              "= B copy (Waldorf Iridium). Two short synth notes, equal peak level.")


def load_wav(path):
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    return x, sr


def latest_pair(loc):
    blo = sorted(glob.glob(str(REPO / "recordings" / f"ab_{loc}_*_n72_blo.wav")))[-1]
    irr = blo.replace("_blo.wav", "_irr.wav")
    return blo, irr


def spec_png(x, sr, path, upscale=True):
    sim_embed.render_spec_png(x, sr, path)
    if upscale:
        from PIL import Image
        im = Image.open(path)
        f = max(1, int(np.ceil(256 / im.width)))
        if f > 1:
            im = im.resize((im.width * f, im.height * f), Image.NEAREST)
            im.save(path)
    return path


def side_by_side(pa, pb, path):
    from PIL import Image
    a, b = Image.open(pa), Image.open(pb)
    h = max(a.height, b.height)
    a, b = a.convert("L"), b.convert("L")
    gap = 8
    out = Image.new("L", (a.width + b.width + gap, h), 0)
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gap, 0))
    out.save(path)
    return path


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


def systemone(images_b64, state, timeout=300):
    payload = {
        "model": D1_MODEL,
        "state": state,
        "images": images_b64,
        "questions": {
            "similarity": {
                "type": "score",
                "instructions": ("How similar does sound B sound to reference sound A? "
                                 "Judge timbre, spectrum and envelope. Higher = more similar."),
                "criteria": CRITERIA,
            },
            "same_pitch": {
                "type": "noul",
                "instructions": "Does sound B have the same pitch as reference A?",
            },
        },
    }
    r = requests.post(f"{HOST}/v1/systemone", json=payload, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"systemone HTTP {r.status_code}: {r.text[:300]}")
    return r.json()["answers"]


def rank(x):
    return np.argsort(np.argsort(np.asarray(x, dtype=float)))


def spearman(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ra, rb = rank(a), rank(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ratings = json.load(open(REPO / "recordings" / "phaseb_ratings_raw.json"))
    rows = [json.loads(l) for l in open(REPO / "recordings" / "sim_log.jsonl")
            if '"manual_panel"' in l]
    rows = [r for r in rows if r["meta"]["backends"].get("norm_pegel")
            and r["result"]["score"] is not None]

    def logcol(loc, field):
        return next(r["result"][field] for r in rows if r["meta"]["blofeld"] == loc)

    lfm3 = sim_embed.OllamaBackend()  # lfm3-omni:2b
    out = {"ts": ts, "model": D1_MODEL, "pairs": {}}
    with tempfile.TemporaryDirectory() as td:
        for loc in LOCS:
            blo_p, irr_p = latest_pair(loc)
            xa, sr = load_wav(blo_p)
            xb, _ = load_wav(irr_p)
            spa = spec_png(xa, sr, Path(td) / f"{loc}_a.png")
            spb = spec_png(xb, sr, Path(td) / f"{loc}_b.png")
            sbs = side_by_side(spa, spb, Path(td) / f"{loc}_ab.png")
            a2 = systemone([b64(spa), b64(spb)], STATE_2IMG)
            a1 = systemone([b64(sbs)], STATE_1IMG)
            sim_ans, pitch_ans = a2["similarity"], a2["same_pitch"]
            d1_2img = round(100.0 * sim_ans["score"] / (len(CRITERIA) - 1), 1)
            d1_1img = round(100.0 * a1["similarity"]["score"] / (len(CRITERIA) - 1), 1)
            l = lfm3.judge(xa, xb, sr, prompt=sim_embed.DEFAULT_JUDGE_PROMPT)
            rec = {
                "wav": {"blo": blo_p, "irr": irr_p},
                "user": ratings[loc]["score"],
                "phaseA": logcol(loc, "score"),
                "embed": logcol(loc, "embed_score"),
                "combined": logcol(loc, "combined"),
                "llm_lfm3": l["score"],
                "d1_spec2img": d1_2img,
                "d1_spec1img": d1_1img,
                "d1_conf": round(sim_ans.get("confidence", 0), 3),
                "d1_same_pitch": round(pitch_ans.get("noul", 0), 3),
                "d1_probs": sim_ans.get("probabilities"),
                "llm_lfm3_summary": l.get("summary"),
            }
            out["pairs"][loc] = rec
            print(f"{loc}: user={rec['user']:3d} A={rec['phaseA']:.2f} emb={rec['embed']:.2f} "
                  f"comb={rec['combined']:.2f} lfm3={rec['llm_lfm3']:3d} "
                  f"d1_2img={d1_2img:5.1f} d1_1img={d1_1img:5.1f} conf={rec['d1_conf']} "
                  f"pitch={rec['d1_same_pitch']}")

    user = [out["pairs"][k]["user"] for k in LOCS]
    out["spearman_user"] = {
        name: round(spearman(user, [out["pairs"][k][name] for k in LOCS]), 3)
        for name in ("phaseA", "embed", "combined", "llm_lfm3", "d1_spec2img", "d1_spec1img")
    }
    print("\nSpearman vs Benutzer:", json.dumps(out["spearman_user"]))
    outp = REPO / "recordings" / f"d1_omni_eval_{ts}.json"
    outp.write_text(json.dumps(out, indent=2))
    print("geschrieben:", outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
