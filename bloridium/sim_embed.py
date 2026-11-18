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


def render_spec_pair_png(x_a: np.ndarray, x_b: np.ndarray, sr: int, path: Path,
                         db_span: float = 20.0) -> Path:
    """Side-by-Side-Spektrogramm-Vergleich A | B | Delta als RGB-PNG.

    A/B als Graustufen mit GEMEINSAMEM lo/hi ueber beide Spektrogramme (sonst taeuscht
    die Einzel-Normierung); rechtes Panel: Delta = spec_b - spec_a in dB, divergierende
    Skala blau (B leiser) -> mittelgrau (0) -> rot (B lauter), geclippt auf +/-db_span.
    Unterschiedliche Laengen: kuerzeres spec wird rechts mit eigenem min gepadet.
    x = Zeit, y = Frequenzband (log, wie sim.features). Wirft ValueError bei < 0.2 s.
    """
    from PIL import Image

    sa = sim.features(x_a, sr=sr)["log_spec"]
    sb = sim.features(x_b, sr=sr)["log_spec"]
    n = max(sa.shape[1], sb.shape[1])
    if sa.shape[1] < n:
        sa = np.pad(sa, ((0, 0), (0, n - sa.shape[1])), constant_values=float(sa.min()))
    if sb.shape[1] < n:
        sb = np.pad(sb, ((0, 0), (0, n - sb.shape[1])), constant_values=float(sb.min()))
    lo = min(float(sa.min()), float(sb.min()))
    hi = max(float(sa.max()), float(sb.max()))
    if hi - lo < 1e-9:
        hi = lo + 1e-9
    ga = ((sa - lo) / (hi - lo) * 255.0).astype(np.uint8)
    gb = ((sb - lo) / (hi - lo) * 255.0).astype(np.uint8)
    # divergierende LUT: idx 0 = blau (-db_span), 128 = grau (0), 255 = rot (+db_span)
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        t = (i - 128) / 128.0
        if t >= 0:
            lut[i] = (int(128 + 127 * t), int(128 - 128 * t), int(128 - 128 * t))
        else:
            lut[i] = (int(128 + 128 * t), int(128 + 128 * t), int(128 - 127 * t))
    d = np.clip(sb - sa, -db_span, db_span)
    gd = lut[np.clip((d / db_span * 127.5 + 128).astype(int), 0, 255)]
    sep = np.full((sa.shape[0], 2, 3), 255, dtype=np.uint8)
    img = np.concatenate(
        [np.stack([ga] * 3, axis=-1), sep, np.stack([gb] * 3, axis=-1), sep, gd], axis=1)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img, mode="RGB").save(str(path))  # (bands, width, 3) -> Breite = Zeit
    return path


def _spec_png_name(meta: dict, spec_png_dir) -> Path:
    """Dateiname aus meta: spec_<blofeld>_n<note>_w<wheel>.png (Fallback spec_pair.png),
    bei Kollision Suffix _2, _3, ..."""
    d = Path(spec_png_dir)
    d.mkdir(parents=True, exist_ok=True)
    parts = []
    for k in ("blofeld", "note", "wheel_pct"):
        if k in meta and meta[k] is not None:
            v = meta[k]
            if k == "wheel_pct":
                v = f"w{int(v) if float(v) == int(v) else v}"
            elif k == "note":
                v = f"n{v}"
            parts.append(str(v))
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", "spec_" + "_".join(parts) if parts else "spec_pair")
    p = d / f"{base}.png"
    i = 2
    while p.exists():
        p = d / f"{base}_{i}.png"
        i += 1
    return p


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
              prompt: str = DEFAULT_JUDGE_PROMPT,
              peak_a: float | None = None, peak_b: float | None = None) -> dict:
        """Vergleicht zwei Clips -> {score, summary, differences, mode, model}.

        peak_a/peak_b (dBFS): wenn gesetzt, landen die Pegel im Prompt — ein deutlich
        leiseres B darf nicht als 'aehnlich' durchgehen (Kalibrierung)."""
        if peak_a is not None and peak_b is not None:
            prompt = (prompt + f"\nGemessene Pegel: A {peak_a:.1f} dBFS, B {peak_b:.1f} dBFS. "
                      "Ist B deutlich leiser als A (>12 dB), ist das ein massiver Unterschied — "
                      "senke score entsprechend (nahezu unhoerbares B = sehr niedriger score).")
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
    """Erstes balanciertes {...}-Objekt im Text finden und parsen.

    LLM schreibt gern Prosa/Code-Fences drumherum, und Prosa nach dem JSON mit
    eigener Klammer brach den frueheren Greedy-Regex-Match -> balancierter Scan.
    """
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        obj = None
                    if isinstance(obj, dict):
                        return obj
                    break
        start = text.find("{", start + 1)
    return None


PROMPT_ID = "judge-v2-pegel"  # v2: Pegel im Prompt + Deckel bei >24 dB Unterschied

# --- D1-Profil (d1-omni via System One /v1/systemone) als Erklaer-Schicht ---
# Spike 2026-11-15 (scripts/spike_d1_profile_eval.py): als Score schwach (Spearman
# +0.13 vs Benutzer), als noul-Profil matchen die Flags die Benutzer-Bemerkungen.
DEFAULT_D1_MODEL = "d1-omni:2b"

D1_PROFILE_CRITERIA = [
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
D1_PROFILE_QUESTIONS = {
    "similarity": {
        "type": "score",
        "instructions": ("How similar does sound B sound to reference sound A? "
                         "Judge timbre, spectrum and envelope. Higher = more similar."),
        "criteria": D1_PROFILE_CRITERIA,
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
D1_DIFF_QUESTIONS = ["octave_lower", "brighter", "darker", "noisier", "punchier"]
D1_PROFILE_STATE = ("Spectrograms of two short synthesizer notes, both normalized to equal "
                    "peak level. Image 1 = A, the reference sound (Waldorf Blofeld). "
                    "Image 2 = B, the copied sound (Waldorf Iridium).")


class D1ProfileBackend:
    """d1-omni (System One /v1/systemone) als Differenz-Profiler.

    Spektrogramm-PNGs von A und B als `images`, 8 Fragen (1 score + 7 noul) in einem
    Forward Pass -> {score 0-100, probs, flags (p>=0.5 ueber D1_DIFF_QUESTIONS),
    diff_count, same_overall 0-100}.
    """

    def __init__(self, model: str = DEFAULT_D1_MODEL, host: str = DEFAULT_OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    def available(self) -> bool:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            if r.status_code != 200:
                return False
            names = [m.get("name", "") for m in r.json().get("models", [])]
            return any(n == self.model or n.startswith(self.model + ":") for n in names)
        except Exception:
            return False

    def profile(self, x_a, x_b, sr: int, timeout: float = 600) -> dict:
        with tempfile.TemporaryDirectory() as td:
            pa, pb = Path(td) / "a.png", Path(td) / "b.png"
            render_spec_png(np.asarray(x_a, dtype=np.float64), sr, pa)
            render_spec_png(np.asarray(x_b, dtype=np.float64), sr, pb)
            payload = {
                "model": self.model,
                "state": D1_PROFILE_STATE,
                "images": [base64.b64encode(pa.read_bytes()).decode(),
                           base64.b64encode(pb.read_bytes()).decode()],
                "questions": D1_PROFILE_QUESTIONS,
            }
            r = requests.post(f"{self.host}/v1/systemone", json=payload, timeout=timeout)
        if r.status_code != 200:
            raise RuntimeError(f"systemone[{self.model}] HTTP {r.status_code}: {r.text[:200]}")
        ans = r.json()["answers"]
        sim = ans["similarity"]
        n = len(D1_PROFILE_CRITERIA) - 1
        probs = {q: round(float(ans[q]["noul"]), 4)
                 for q, spec in D1_PROFILE_QUESTIONS.items() if spec["type"] == "noul"}
        flags = [q for q in D1_DIFF_QUESTIONS if probs[q] >= 0.5]
        return {"model": self.model,
                "score": round(100.0 * float(sim["score"]) / n, 2),
                "confidence": round(float(sim.get("confidence", 0.0)), 4),
                "probs": probs,
                "flags": flags,
                "diff_count": len(flags),
                "same_overall": round(100.0 * probs["same_overall"], 2)}


def build_profile_backend(want: bool, model: str = DEFAULT_D1_MODEL):
    """D1ProfileBackend oder None (bei want=False oder fehlendem Modell, mit WARNUNG)."""
    if not want:
        return None
    b = D1ProfileBackend(model)
    if b.available():
        return b
    print(f"WARNUNG: d1-Profil nicht verfuegbar (Modell {model} fehlt) – deaktiviert",
          file=sys.stderr)
    return None


def peak_dbfs(x) -> float:
    """Peak-Pegel in dBFS (Guard gegen Stille)."""
    x = np.asarray(x, dtype=np.float64).ravel()
    m = float(np.max(np.abs(x))) if x.size else 0.0
    return 20.0 * float(np.log10(m + 1e-12))


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
    if r.get("profile"):
        p = r["profile"]
        print(f"  profile[{p.get('model')}] score={p.get('score')} same_overall={p.get('same_overall')} "
              f"flags={p.get('flags')} diff_count={p.get('diff_count')}")
    if r.get("spec_png"):
        print(f"  spec_png: {r['spec_png']}")
    if r.get("backend_error"):
        print(f"  backend_error: {r['backend_error']}")
    deltas = r.get("band_delta_db") or []
    if deltas:
        top = sorted(range(len(deltas)), key=lambda i: -abs(deltas[i]))[:5]
        print("Top-Band-Deltas (dB): " + ", ".join(f"band{i}: {deltas[i]:+.1f}" for i in top))
    bd = r.get("band_dtw") or []
    if bd:
        edges = r.get("band_edges_hz") or []
        top = sorted(range(len(bd)), key=lambda i: -bd[i])[:5]
        parts = []
        for i in top:
            hz = (f"{edges[i]:.0f}-{edges[i + 1]:.0f}Hz" if i + 1 < len(edges)
                  else f">={edges[i]:.0f}Hz")
            parts.append(f"{hz}:{bd[i]:.2f}")
        print("Top-Band-DTW zeitl. (0-1, wo in Frequenz): " + ", ".join(parts))


def _fehler_result(error: str) -> dict:
    """Stabiles Fehler-Schema: Backend-Keys immer vorhanden (null), nie fehlend."""
    return {"score": None, "verdict": "fehler", "error": error,
            "spec_cos": None, "env_dtw": None, "band_delta_db": None,
            "embed_cos": None, "embed_score": None, "combined": None,
            "llm": None, "backend_error": None, "peak_dbfs": None, "profile": None,
            "spec_dtw": None, "band_dtw": None, "frame_cos": None, "band_edges_hz": None,
            "spec_png": None}


def score_pair_embed(x_blo, x_irr, sr: int = 48000, meta: dict | None = None,
                     log_path=DEFAULT_LOG, *, clap: ClapBackend | None = None,
                     ollama: OllamaBackend | None = None, use_llm: bool = False,
                     strict: bool = False, judge_prompt: str = DEFAULT_JUDGE_PROMPT,
                     norm_pegel: bool = False,
                     profile_backend: "D1ProfileBackend | None" = None,
                      spec_png_dir=None) -> dict:
    """Phase A + Embedding (+LLM) in einem Ergebnisdict; log_path=None -> kein Log.

    Degrade-Regel: Backend fehlt/kaputt -> Felder null + backend_error, weiterrechnen;
    strict=True -> RuntimeError. combined = 0.5*score + 0.5*embed_score (ohne Embedding:
    combined = score). Genau ein JSONL-Eintrag pro Aufruf (wenn log_path gesetzt).

    norm_pegel=True: embed/LLM bekommen auf Peak 0.5 (-6 dBFS) angeglichene Kopien
    (Phase A bleibt auf Roh-Signal, ist pegel-invariant; peak_dbfs im Log bleibt roh).
    """
    peak_a = peak_dbfs(x_blo)
    peak_b = peak_dbfs(x_irr)
    if norm_pegel:
        def _norm(x, peak):
            x = np.asarray(x, dtype=np.float64)
            return x * (0.5 / (10 ** (peak / 20.0))) if peak > -120.0 else x
        xe_blo, xe_irr = _norm(x_blo, peak_a), _norm(x_irr, peak_b)
        pn_a = pn_b = 20.0 * float(np.log10(0.5))
    else:
        xe_blo, xe_irr = x_blo, x_irr
        pn_a, pn_b = peak_a, peak_b
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
                   "combined": None, "llm": None, "backend_error": None,
                   "profile": None, "spec_png": None})
    errors = []

    if clap is not None:
        try:
            ec = embed_compare(clap.embed(xe_blo, sr), clap.embed(xe_irr, sr))
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
                result["llm"] = ollama.judge(xe_blo, xe_irr, sr, prompt=judge_prompt,
                                             peak_a=pn_a, peak_b=pn_b)
                # Harter Deckel: B >24 dB leiser als A -> LLM-Score kapppen (unhörbar != aehnlich)
                if pn_b < pn_a - 24.0:
                    result["llm"]["score"] = min(result["llm"]["score"], 30)
                    result["llm"]["level_penalty"] = True
            except Exception as e:
                errors.append(f"ollama: {e}")
                if strict:
                    raise BackendError(errors[-1]) from e
        else:
            errors.append("ollama: nicht verfuegbar (Server/Modell fehlt)")
            if strict:
                raise BackendError(errors[-1])
    result["peak_dbfs"] = {"a": round(peak_a, 2), "b": round(peak_b, 2)}

    if profile_backend is not None:
        if profile_backend.available():
            try:
                result["profile"] = profile_backend.profile(xe_blo, xe_irr, sr)
            except Exception as e:
                errors.append(f"d1_profile: {e}")
                if strict:
                    raise BackendError(errors[-1]) from e
        else:
            errors.append("d1_profile: nicht verfuegbar (Modell fehlt)")
            if strict:
                raise BackendError(errors[-1])

    if spec_png_dir is not None:
        # optischer Spektrogramm-Vergleich auf den pegel-normalisierten Signalen
        # (xe_*: sonst zeigt das Delta-Panel nur den Gain-Unterschied)
        try:
            path = _spec_png_name(meta, spec_png_dir)
            render_spec_pair_png(xe_blo, xe_irr, sr, path)
            result["spec_png"] = str(path)
        except Exception as e:
            result["spec_png"] = None
            errors.append(f"spec_png: {e}")
            if strict:
                raise BackendError(errors[-1]) from e

    result["backend_error"] = "; ".join(errors) if errors else None
    if log_path:
        m = dict(meta)
        m["backends"] = {
            "clap": Path(clap.model_path).name if clap is not None else "none",
            "ollama": ollama.model if ollama is not None else "none",
            "llm": use_llm,
            "prompt_id": PROMPT_ID,
            "norm_pegel": norm_pegel,
            "d1_profile": profile_backend.model if profile_backend is not None else "none",
        }
        sim.log_run(result, m, log_path)
    return result
