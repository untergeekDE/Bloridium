"""Phase B: modellbasierter Sound-Vergleich (Embedding-Score + LLM-Urteil).

Kern bleibt numpy-only; Modelle laufen extern:
- ClapBackend  – CLAP-GGUF (clap.cpp) -> 512-d Audio-Embedding, Cosine = embed_score
- OllamaBackend – ollama Omni-Audio-Modell -> JSON-Urteil {score, summary, differences}
score_pair_embed() kombiniert Phase A (sim.features/sim.compare) mit Embedding (+LLM).

Spec: docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from bloridium import sim

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO / "recordings" / "sim_log.jsonl"
DEFAULT_MODELS_DIR = REPO / "models"
CLAP_GGUF_NAME = "larger_clap_music_and_speech-q8_0.gguf"
DEFAULT_OLLAMA_MODEL = "lfm3-omni:2b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
CLAP_SR = 48000  # clap.cpp resampelt selbst auf 48 kHz; wir liefern 48 kHz


def write_wav(x: np.ndarray, sr: int, path: Path) -> None:
    """Mono-WAV (PCM16) via stdlib wave – float32 in [-1,1] -> int16, geclippt."""
    x = np.asarray(x, dtype=np.float64).ravel()
    x = np.clip(x, -1.0, 1.0)
    # erst float-seitig clippen, dann konvertieren (astype(int16) overflowt sonst!)
    pcm = np.clip(np.round(x * 32768.0), -32768, 32767).astype(np.int16)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm.tobytes())


def render_spec_png(x: np.ndarray, sr: int, path: Path) -> None:
    """Log-Spektrogramm (sim.features) als Graustufen-PNG – Achsen: x=Zeit, y=Band.

    Wird als `images`-Fallback an ollama geschickt, wenn das Server-Audio-Feld
    nicht akzeptiert wird. Wirft ValueError bei zu kurzem Signal (wie sim.features).
    """
    from PIL import Image

    f = sim.features(x, sr=sr)  # ValueError bei < 0.2 s
    spec = f["log_spec"]  # (n_bands, n_frames) in dB
    lo, hi = float(spec.min()), float(spec.max())
    if hi - lo < 1e-9:
        img = np.zeros(spec.shape, dtype=np.uint8)
    else:
        img = ((spec - lo) / (hi - lo) * 255.0).astype(np.uint8)
    Image.fromarray(img.T, mode="L").save(str(path))  # transponiert: Breite = Zeit


def embed_compare(ea: np.ndarray, eb: np.ndarray) -> dict:
    """Cosine zweier Embeddings -> {embed_cos, embed_score 0-100} (linear geclippt)."""
    ea = np.asarray(ea, dtype=np.float64).ravel()
    eb = np.asarray(eb, dtype=np.float64).ravel()
    na, nb = float(np.linalg.norm(ea)), float(np.linalg.norm(eb))
    cos = float(np.dot(ea, eb) / (na * nb)) if na > 0 and nb > 0 else 0.0
    return {"embed_cos": round(cos, 6), "embed_score": round(100.0 * max(0.0, min(1.0, cos)), 2)}
