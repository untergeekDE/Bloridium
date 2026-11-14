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
import sys
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


PROMPT_ID = "judge-v1"


class BackendError(RuntimeError):
    """strict=True und Backend fehlt/kaputt (unterscheidbar von Hardware-Fehlern)."""


def build_backends(models_dir, want_embed: bool, want_llm: bool):
    """(ClapBackend|None, OllamaBackend|None); fehlt etwas -> WARNUNG auf stderr + None."""
    clap = None
    if want_embed:
        gguf = Path(models_dir) / CLAP_GGUF_NAME
        if gguf.exists():
            try:
                clap = ClapBackend(gguf)
            except Exception as e:
                print(f"WARNUNG clap: {e}", file=sys.stderr)
        else:
            print(f"WARNUNG: {gguf} fehlt (scripts/fetch_models.py) – embed deaktiviert",
                  file=sys.stderr)
    ollama = None
    if want_llm:
        o = OllamaBackend()
        if o.available():
            ollama = o
        else:
            print("WARNUNG: ollama nicht verfuegbar (Server/Modell) – llm deaktiviert",
                  file=sys.stderr)
    return clap, ollama


def print_result(r: dict, a_name: str, b_name: str) -> None:
    """Einheitliche Ausgabe fuer Skripte und CLI."""
    print(f"Score {a_name} vs {b_name}: {r['score']} ({r['verdict']})  "
          f"spec_cos={r.get('spec_cos')} env_dtw={r.get('env_dtw')}")
    if r.get("embed_score") is not None:
        print(f"  embed_cos={r.get('embed_cos')} embed_score={r.get('embed_score')} "
              f"combined={r.get('combined')}")
    if r.get("llm"):
        print(f"  llm[{r['llm'].get('mode')}] score={r['llm'].get('score')}: "
              f"{r['llm'].get('summary')}")
    if r.get("backend_error"):
        print(f"  backend_error: {r['backend_error']}")
    deltas = r.get("band_delta_db") or []
    if deltas:
        top = sorted(range(len(deltas)), key=lambda i: -abs(deltas[i]))[:5]
        print("Top-Band-Deltas (dB): " + ", ".join(f"band{i}: {deltas[i]:+.1f}" for i in top))


def _fehler_result(error: str) -> dict:
    """Stabiles Fehler-Schema: Backend-Keys immer vorhanden (null), nie fehlend."""
    return {"score": None, "verdict": "fehler", "error": error,
            "spec_cos": None, "env_dtw": None, "band_delta_db": None,
            "embed_cos": None, "embed_score": None, "combined": None,
            "llm": None, "backend_error": None}


def score_pair_embed(x_blo, x_irr, sr: int = 48000, meta: dict | None = None,
                     log_path=DEFAULT_LOG, *, clap: ClapBackend | None = None,
                     ollama: OllamaBackend | None = None, use_llm: bool = False,
                     strict: bool = False, judge_prompt: str = DEFAULT_JUDGE_PROMPT) -> dict:
    """Phase A + Embedding (+LLM) in einem Ergebnisdict; log_path=None -> kein Log.

    Degrade-Regel: Backend fehlt/kaputt -> Felder null + backend_error, weiterrechnen;
    strict=True -> RuntimeError. combined = 0.5*score + 0.5*embed_score (ohne Embedding:
    combined = score). Genau ein JSONL-Eintrag pro Aufruf (wenn log_path gesetzt).
    """
    meta = dict(meta or {})
    try:
        fa = sim.features(x_blo, sr)
        fb = sim.features(x_irr, sr)
    except ValueError as e:
        result = _fehler_result(str(e))
        if log_path:
            sim.log_run(result, meta, log_path)
        return result
    if float(fa["env_rms"].max()) < 1e-4 or float(fb["env_rms"].max()) < 1e-4:
        result = _fehler_result("stille Aufnahme (env_rms max < 1e-4)")
        if log_path:
            sim.log_run(result, meta, log_path)
        return result

    base = sim.compare(fa, fb)  # Phase A direkt (kein sim.score_pair -> kein Doppel-Log)
    result = dict(base)
    result.update({"error": None, "embed_cos": None, "embed_score": None,
                   "combined": None, "llm": None, "backend_error": None})
    errors = []

    if clap is not None:
        try:
            ec = embed_compare(clap.embed(x_blo, sr), clap.embed(x_irr, sr))
            result["embed_cos"] = ec["embed_cos"]
            result["embed_score"] = ec["embed_score"]
        except Exception as e:
            errors.append(f"clap: {e}")
            if strict:
                raise BackendError(errors[-1]) from e
    else:
        errors.append("clap: nicht konfiguriert (kein GGUF/Modell)")
        if strict:
            raise BackendError(errors[-1])

    if result["embed_score"] is not None:
        result["combined"] = round(0.5 * base["score"] + 0.5 * result["embed_score"], 2)
    else:
        result["combined"] = base["score"]

    if use_llm:
        if ollama is not None and ollama.available():
            try:
                result["llm"] = ollama.judge(x_blo, x_irr, sr, prompt=judge_prompt)
            except Exception as e:
                errors.append(f"ollama: {e}")
                if strict:
                    raise BackendError(errors[-1]) from e
        else:
            errors.append("ollama: nicht verfuegbar (Server/Modell fehlt)")
            if strict:
                raise BackendError(errors[-1])

    result["backend_error"] = "; ".join(errors) if errors else None
    if log_path:
        m = dict(meta)
        m["backends"] = {
            "clap": Path(clap.model_path).name if clap is not None else "none",
            "ollama": ollama.model if ollama is not None else "none",
            "llm": use_llm,
            "prompt_id": PROMPT_ID,
        }
        sim.log_run(result, m, log_path)
    return result
