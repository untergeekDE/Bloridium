#!/usr/bin/env python3
"""spike_mert_clap_eval.py – CLAP vs MERT als Embedding-Distanz auf unseren 9 Paaren.

Spike 2026-11-17 (Frage: "CLAP oder MERT fuer unsere bisherigen Vergleiche?"):
bettet die vorhandenen pegel-angeglichenen WAV-Paare (ab_<LOC>_20261115_*_n72_w0_*.wav)
mit drei GGUF-Modellen via clap-cpp ein und vergleicht die Cosine-Scores mit den
Benutzer-Ratings (recordings/phaseb_ratings_raw.json, Spearman).

Modelle (alle gorse-io@HF, in models/):
  - larger_clap_music_and_speech-q8_0.gguf (512-d, 48 kHz)  [Production-CLAP]
  - larger_clap_music-q8_0.gguf           (512-d, 48 kHz)  [CLAP music-only]
  - MERT-v1-95M-q8_0.gguf                  (768-d, 24 kHz)  [MERT, Resample 48k->24k]

Output: recordings/mert_clap_eval_<ts>.json + Tabelle + Spearman pro Modell.
Lizenz-Hinweis: MERT = CC-BY-NC-4.0 (Research ok, nicht kommerziell).
"""

from __future__ import annotations

import json
import sys
import time
import wave
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import clap_cpp  # noqa: E402
from sim_eval_offline import spearman  # noqa: E402  (numpy-only, scipy ist hier broken)

REC = REPO / "recordings"
MODELS = REPO / "models"

MODELS_CFG = {
    "clap_music_speech": (MODELS / "larger_clap_music_and_speech-q8_0.gguf", 48000),
    "clap_music": (MODELS / "larger_clap_music-q8_0.gguf", 48000),
    "mert_v1_95m": (MODELS / "MERT-v1-95M-q8_0.gguf", 24000),
}


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    return x, sr


def resample_linear(x: np.ndarray, sr: int, target: int) -> np.ndarray:
    if sr == target:
        return x
    n_out = int(round(len(x) * target / sr))
    idx = np.linspace(0, len(x) - 1, n_out)
    return np.interp(idx, np.arange(len(x)), x)


def main() -> int:
    ratings = {k: v["score"] for k, v in
               json.loads((REC / "phaseb_ratings_raw.json").read_text()).items()}
    locs = sorted(ratings)

    pairs = {}
    for loc in locs:
        blo = sorted(REC.glob(f"ab_{loc}_20261115_*_n72_w0_blo.wav"))
        irr = sorted(REC.glob(f"ab_{loc}_20261115_*_n72_w0_irr.wav"))
        assert blo and irr, f"{loc}: WAV-Paar fehlt"
        pairs[loc] = (blo[-1], irr[-1])

    backends = {}
    for name, (path, sr) in MODELS_CFG.items():
        backends[name] = (clap_cpp.CLAP(str(path)), sr)
        print(f"geladen: {name} ({path.name})", flush=True)

    rows = []
    for loc in locs:
        bx, sr = read_wav_mono(pairs[loc][0])
        ix, _ = read_wav_mono(pairs[loc][1])
        row = {"loc": loc, "rating": ratings[loc]}
        for name, (clap, target_sr) in backends.items():
            ex = clap.encode_audio(resample_linear(bx, sr, target_sr).astype(np.float32),
                                   sample_rate=target_sr)
            ey = clap.encode_audio(resample_linear(ix, sr, target_sr).astype(np.float32),
                                   sample_rate=target_sr)
            cos = float(np.dot(ex, ey) / (np.linalg.norm(ex) * np.linalg.norm(ey) + 1e-12))
            row[f"{name}_cos"] = round(cos, 4)
            row[f"{name}_score"] = round(100.0 * max(0.0, min(1.0, cos)), 2)
        rows.append(row)
        print(f"{loc}: rating={row['rating']:3d} " +
              " ".join(f"{n}={row[f'{n}_score']:.1f}" for n in MODELS_CFG), flush=True)

    print("\nSpearman vs Benutzer-Ratings (n=9):")
    result = {}
    for name in MODELS_CFG:
        rho = spearman([r["rating"] for r in rows], [r[f"{name}_score"] for r in rows])
        result[name] = {"spearman": round(float(rho), 3)}
        print(f"  {name:18s} rho={rho:+.3f}")

    out = {"ts": time.strftime("%Y%m%d_%H%M%S"), "note": 72, "wheel_pct": 0,
           "n_pairs": len(rows), "models": {k: str(v[0].name) for k, v in MODELS_CFG.items()},
           "spearman": result, "rows": rows}
    path = REC / f"mert_clap_eval_{out['ts']}.json"
    path.write_text(json.dumps(out, indent=1))
    print(f"\ngeschrieben: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
