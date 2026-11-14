"""Phase B: modellbasierter Sound-Vergleich (Embedding-Score + LLM-Urteil).

Kern bleibt numpy-only; Modelle laufen extern:
- ClapBackend  – CLAP-GGUF (clap.cpp) -> 512-d Audio-Embedding, Cosine = embed_score
- OllamaBackend – ollama Omni-Audio-Modell -> JSON-Urteil {score, summary, differences}
score_pair_embed() kombiniert Phase A (sim.features/sim.compare) mit Embedding (+LLM).

Spec: docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md
"""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
import requests

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


def _resample_linear(x: np.ndarray, sr: int, target: int = CLAP_SR) -> np.ndarray:
    """Lineares Resampling (numpy) auf `target` Hz; bei sr==target identity."""
    if sr == target or x.size == 0:
        return np.asarray(x, dtype=np.float64)
    n = max(1, int(round(x.size * target / sr)))
    return np.interp(np.linspace(0, x.size - 1, n), np.arange(x.size), x)


class ClapBackend:
    """CLAP-Audio-Embeddings aus GGUF – pip-Binding `clap_cpp` zuerst, sonst
    clap.cpp-Binary (`clap embedding --model M --audio WAV`) via subprocess.

    Input-Konvention (Spec): ganze Aufnahme, mono; Resampling auf 48 kHz hier,
    das 10-s-Fenster/Padding uebernimmt das Backend (repeat-pad).
    """

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"CLAP-GGUF fehlt: {self.model_path} "
                                    f"(fetch_models.py)")
        self._clap = None
        self._binary = None
        self.mode = "binary"
        try:
            import clap_cpp  # pip-Paket
            self._clap = clap_cpp.CLAP(str(self.model_path), threads=0)
            self.mode = "pip"
        except ImportError:
            self._binary = shutil.which("clap")
            if self._binary is None:
                raise RuntimeError("CLAP-Backend fehlt: weder clap_cpp (pip) noch "
                                   "clap-Binary im PATH")

    def embed(self, x: np.ndarray, sr: int) -> np.ndarray:
        """Audio -> L2-normalisierter Embedding-Vektor (512, float32)."""
        x = np.asarray(x, dtype=np.float64)
        if x.ndim > 1:
            x = x.mean(axis=0)  # Stereo -> mono
        x = _resample_linear(x.ravel(), sr, CLAP_SR)
        try:
            if self._clap is not None:
                vec = np.asarray(self._clap.encode_audio(x.tolist(), sample_rate=CLAP_SR),
                                 dtype=np.float32)
            else:
                vec = self._embed_binary(x)
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"CLAP-Embedding fehlgeschlagen: {e}") from e
        n = float(np.linalg.norm(vec))
        if n > 0:
            vec = (vec / n).astype(np.float32)
        return vec

    def _embed_binary(self, x: np.ndarray) -> np.ndarray:
        """Fallback: WAV in tmp schreiben, `clap embedding` als subprocess."""
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "in.wav"
            write_wav(x, CLAP_SR, wav)
            r = subprocess.run(
                [self._binary, "embedding", "--model", str(self.model_path), "--audio", str(wav)],
                capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(f"CLAP-Binary exit {r.returncode}: {r.stderr.strip()[:200]}")
        return np.asarray(json.loads(r.stdout), dtype=np.float32)


DEFAULT_JUDGE_PROMPT = (
    "Du bekommst zwei kurze Audio-Clips: A ist das Vorbild (Blofeld), B der "
    "uebertragene Sound (Waldorf Iridium). Bewerte, wie aehnlich B an A klingt. "
    "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt im Format "
    '{"score": 0-100, "summary": "...", "differences": ["...", ...]} '
    " Dabei ist 100 = nicht unterscheidbar, 0 = voellig verschiedener Klang. "
    "differences listet die auffaelligsten klanglichen Unterschiede von B zu A auf."
)


class OllamaBackend:
    """LLM-Urteil ueber ollama (/api/chat). Modus: Audio direkt (`audio`-Feld),
    Fallback bei 4xx: Spektrogramm-PNGs (`images`-Feld). Server muss laufen
    (Menubar-App / systemd); fetch_models.py pullt nur das Modell.
    """

    def __init__(self, model: str = DEFAULT_OLLAMA_MODEL, host: str = DEFAULT_OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    def available(self) -> bool:
        """True wenn der Server antwortet UND das Modell gepullt ist."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            if r.status_code != 200:
                return False
            names = [m.get("name", "") for m in r.json().get("models", [])]
            return any(n == self.model or n.startswith(self.model + ":") for n in names)
        except Exception:
            return False

    def judge(self, x_a: np.ndarray, x_b: np.ndarray, sr: int,
              prompt: str = DEFAULT_JUDGE_PROMPT) -> dict:
        """Vergleicht zwei Clips -> {score, summary, differences, mode, model}."""
        try:
            return self._chat(x_a, x_b, sr, prompt, mode="audio")
        except _HttpError as e:
            if not (400 <= e.status < 500):
                raise RuntimeError(f"ollama-Urteil fehlgeschlagen: {e}") from e
            return self._chat(x_a, x_b, sr, prompt, mode="spec")

    def _chat(self, x_a, x_b, sr, prompt, mode) -> dict:
        with tempfile.TemporaryDirectory() as td:
            if mode == "audio":
                a64, b64 = self._wav_b64(x_a, sr, Path(td) / "a.wav"), \
                           self._wav_b64(x_b, sr, Path(td) / "b.wav")
                extra = {"audio": [a64, b64]}
            else:
                pa, pb = Path(td) / "a.png", Path(td) / "b.png"
                render_spec_png(x_a, sr, pa)
                render_spec_png(x_b, sr, pb)
                extra = {"images": [base64.b64encode(pa.read_bytes()).decode(),
                                    base64.b64encode(pb.read_bytes()).decode()]}
            payload = {"model": self.model, "stream": False,
                       "messages": [{"role": "user", "content": prompt, **extra}]}
            r = requests.post(f"{self.host}/api/chat", json=payload, timeout=300)
            if r.status_code != 200:
                raise _HttpError(r.status_code, r.text[:200])
            content = r.json()["message"]["content"]
        obj = _extract_json(content)
        if obj is None:
            raise RuntimeError(f"ollama-Antwort ohne JSON: {content[:120]!r}")
        score = int(np.clip(int(obj.get("score", 0)), 0, 100))
        diffs = obj.get("differences", [])
        if not isinstance(diffs, list):
            diffs = [str(diffs)]
        return {"score": score, "summary": str(obj.get("summary", "")),
                "differences": [str(d) for d in diffs], "mode": mode, "model": self.model}

    @staticmethod
    def _wav_b64(x, sr, path) -> str:
        write_wav(x, sr, path)
        return base64.b64encode(Path(path).read_bytes()).decode()


class _HttpError(Exception):
    def __init__(self, status: int, text: str):
        super().__init__(f"HTTP {status}: {text}")
        self.status = status


def _extract_json(text: str) -> dict | None:
    """Erstes {...}-Objekt im Text finden und parsen (LLM schreibt gern Prosa drumherum)."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None
