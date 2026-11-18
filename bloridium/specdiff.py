"""specdiff.py – Interpretation des Spektral-Diffs (A | B | delta dB) einer
Blofeld-vs-Iridium-Messung.

Zwei Ebenen (hybrid, Spec 2026-11-18):
- DSP (numpy-only, deterministisch, Fallback): diff_matrix -> dsp_features ->
  classify_dsp -> specdiff_score.  Labels: severity light/medium/heavy,
  spread even/punctual, temporal even/periodical/single/multiple/
  increasing/decreasing, bands low/mid/high.
- Vision-Decision-Model (optional, ollama lokal): SystemOneBackend
  (d1-omni via /v1/systemone, choice/noul-Fragen auf dem PNG) oder
  OllamaChatBackend (gemma4 via /api/chat, think:false, JSON-Prompt).
  Liefert die Labels auf dem gerenderten PNG; bei Ausfall -> DSP-Labels.

Score ist immer numerisch aus DSP: specdiff_score = clip(100 - 10*severity_db).
Pad-Spalten (unterschiedliche Laenge) sind 0 dB / nicht aktiv (grau wie im PNG).
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import numpy as np

from . import sim

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_SPECDIFF_MODEL = "d1-omni:2b"

# Schwellen (Spec 2026-11-18)
SEV_LIGHT_DB = 2.0        # mean |delta| aktiv < 2 dB -> light
SEV_HEAVY_DB = 6.0        # < 6 dB -> medium, sonst heavy
SPREAD_THR_DB = 3.0       # Bin "Fehler" ab |delta| > 3 dB
SPREAD_EVEN_FRAC = 0.25   # aktiver Anteil mit Fehler >= 0.25 -> even
BAND_THR_DB = 3.0         # Band betroffen ab Mittel |delta| > 3 dB
LOW_HZ = 250.0
MID_HZ = 2000.0
SLOPE_THR_DB = 1.5        # |Gesamt-Slope| der e(t)-Geraden -> increasing/decreasing
ACORR_THR = 0.5           # Autokorrelation lag 2..n/2 -> periodical
PEAK_THR_DB = 3.0         # Peak in e(t) ab Mittel + 3 dB
ACTIVE_FLOOR_DB = 6.0     # Bin aktiv ab max(sa,sb) >= global_min + 6 dB

SEVERITIES = ("light", "medium", "heavy")
SPREADS = ("even", "punctual")
TEMPORALS = ("even", "periodical", "single", "multiple", "increasing", "decreasing")
BAND_NAMES = ("low", "mid", "high")


# --------------------------------------------------------------------------
# DSP-Kern
# --------------------------------------------------------------------------

def read_wav(path) -> tuple[np.ndarray, int]:
    """Mono-WAV (PCM16/32) via stdlib wave -> (float32-Signal in [-1,1], sr)."""
    import wave
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if sw == 2:
        x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported sampwidth {sw} in {path}")
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def diff_matrix(x_a, x_b, sr: int = 48000) -> dict:
    """Delta-Spektrogram (dB) aus zwei Signalen via sim.features.

    -> {"delta": (n_bands, n_frames), "band_edges", "active": bool-Maske,
        "floor_db"}. Laengere Seite bestimmt n_frames; Pad-Spalten der
    kuerzeren Seite: delta = 0, active = False (grau wie im PNG).
    Raises ValueError bei zu kurzen Signalen (wie sim.features).
    """
    fa = sim.features(np.asarray(x_a, dtype=np.float64), sr=sr)
    fb = sim.features(np.asarray(x_b, dtype=np.float64), sr=sr)
    sa, sb = fa["log_spec"], fb["log_spec"]
    na, nb = sa.shape[1], sb.shape[1]
    n = max(na, nb)
    if na < n:
        sa = np.pad(sa, ((0, 0), (0, n - na)), constant_values=float(sa.min()))
    if nb < n:
        sb = np.pad(sb, ((0, 0), (0, n - nb)), constant_values=float(sb.min()))
    delta = sb - sa
    if na < n:
        delta[:, na:] = 0.0
    if nb < n:
        delta[:, nb:] = 0.0
    floor = min(float(sa.min()), float(sb.min())) + ACTIVE_FLOOR_DB
    active = np.maximum(sa, sb) >= floor
    if na < n:
        active[:, na:] = False
    if nb < n:
        active[:, nb:] = False
    return {"delta": delta, "band_edges": fa["band_edges"],
            "active": active, "floor_db": float(floor)}


def dsp_features(delta: np.ndarray, band_edges: np.ndarray, active: np.ndarray) -> dict:
    """Numerische Merkmale der Delta-Matrix.

    -> {"severity_db", "spread_frac", "temporal": {"e", "slope_total_db",
       "acorr_lag", "acorr_r", "n_peaks"}, "band_mean_db": {low,mid,high}}.
    """
    delta = np.asarray(delta, dtype=np.float64)
    active = np.asarray(active, dtype=bool)
    d = np.abs(delta)
    n_bands, n_frames = delta.shape
    if active.any():
        severity_db = float(d[active].mean())
        spread_frac = float((d[active] > SPREAD_THR_DB).mean())
    else:
        severity_db, spread_frac = 0.0, 0.0
    # temporale Serie: pro Frame Mittel |delta| ueber aktive Baender
    e = np.zeros(n_frames)
    for t in range(n_frames):
        col = active[:, t]
        if col.any():
            e[t] = float(d[col, t].mean())
    if n_frames >= 2:
        slope_total_db = float(np.polyfit(np.arange(n_frames), e, 1)[0] * (n_frames - 1))
    else:
        slope_total_db = 0.0
    acorr_lag, acorr_r = 0, 0.0
    if n_frames >= 8:
        z = e - e.mean()
        denom = float(np.sum(z * z))
        if denom > 1e-12:
            for lag in range(2, n_frames // 2 + 1):
                r = float(np.sum(z[:-lag] * z[lag:]) / denom)
                if r > acorr_r:
                    acorr_lag, acorr_r = lag, r
    # Peaks in e(t): lokale Maxima mit Prominenz
    thr = float(e.mean()) + PEAK_THR_DB
    n_peaks = 0
    for i in range(1, n_frames - 1):
        if e[i] > e[i - 1] and e[i] >= e[i + 1] and e[i] > thr:
            n_peaks += 1
    # Baender: Mittel |delta| ueber aktive Bins im Frequenzbereich
    centers = np.sqrt(band_edges[:-1] * band_edges[1:])
    band_mean_db = {}
    for name, lo, hi in (("low", 0.0, LOW_HZ), ("mid", LOW_HZ, MID_HZ),
                         ("high", MID_HZ, np.inf)):
        m = (centers >= lo) & (centers < hi)
        sub_a = active[m]
        band_mean_db[name] = float(d[m][sub_a].mean()) if sub_a.any() else 0.0
    return {"severity_db": severity_db, "spread_frac": spread_frac,
            "temporal": {"e": e, "slope_total_db": slope_total_db,
                         "acorr_lag": acorr_lag, "acorr_r": acorr_r,
                         "n_peaks": n_peaks},
            "band_mean_db": band_mean_db}


def classify_dsp(feat: dict) -> dict:
    """Deterministische Labels aus dsp_features (Schwellen s. Modulkonstanten)."""
    sev_db = feat["severity_db"]
    if sev_db < SEV_LIGHT_DB:
        severity = "light"
    elif sev_db < SEV_HEAVY_DB:
        severity = "medium"
    else:
        severity = "heavy"
    spread = "even" if feat["spread_frac"] >= SPREAD_EVEN_FRAC else "punctual"
    t = feat["temporal"]
    if abs(t["slope_total_db"]) > SLOPE_THR_DB:
        temporal = "increasing" if t["slope_total_db"] > 0 else "decreasing"
    elif t["acorr_r"] > ACORR_THR:
        temporal = "periodical"
    elif t["n_peaks"] <= 1:
        temporal = "even" if t["n_peaks"] == 0 else "single"
    else:
        temporal = "multiple"
    bands = [b for b in BAND_NAMES if feat["band_mean_db"][b] > BAND_THR_DB]
    summary = (f"delta ~{sev_db:.1f} dB ({severity}), {spread}, temporal {temporal}, "
               f"bands {','.join(bands) if bands else 'none'}")
    return {"severity": severity, "spread": spread, "temporal": temporal,
            "bands": bands, "summary": summary}


def specdiff_score(severity_db: float) -> float:
    """Score 0-100 aus der mittleren aktiven Abweichung: 100 - 10 dB, geclippt."""
    return float(np.clip(100.0 - 10.0 * float(severity_db), 0.0, 100.0))


# --------------------------------------------------------------------------
# Vision-Decision-Model (optional; ollama lokal)
# --------------------------------------------------------------------------

SPECDIFF_STATE = ("Spectrogram comparison of one synthesizer note, three panels "
                  "left to right: A = original (Blofeld), B = converted (Iridium), "
                  "delta = B - A in dB (blue = B quieter, gray = 0, red = B louder). "
                  "x = time, y = frequency on a log scale, LOW frequencies at the TOP "
                  "of the image.")

SPECDIFF_QUESTIONS = {
    "severity": {"type": "choice",
                 "criteria": {"light": "small deviation, barely visible",
                              "medium": "clear but moderate deviation",
                              "heavy": "large deviation, dominates the panel"},
                 "instructions": "Overall deviation magnitude of the delta (right) panel."},
    "spread": {"type": "choice",
               "criteria": {"even": "error spread over the whole panel",
                            "punctual": "error localized to a few spots"},
               "instructions": "Spatial distribution of the error in the delta panel."},
    "temporal": {"type": "choice",
                 "criteria": {"even": "constant over time",
                              "periodical": "repeating pattern over time",
                              "single": "one isolated event",
                              "multiple": "several isolated events",
                              "increasing": "grows over time",
                              "decreasing": "shrinks over time"},
                 "instructions": "Temporal pattern of the error across x = time."},
    "low": {"type": "noul",
            "instructions": "Is the low-frequency region (TOP of the image) affected in the delta panel?"},
    "mid": {"type": "noul",
            "instructions": "Is the mid-frequency region (250-2000 Hz) affected in the delta panel?"},
    "high": {"type": "noul",
             "instructions": "Is the high-frequency region (BOTTOM of the image, > 2000 Hz) affected in the delta panel?"},
}


def _ollama_has_model(host: str, model: str) -> bool:
    import requests
    try:
        r = requests.get(f"{host}/api/tags", timeout=5)
        if r.status_code != 200:
            return False
        names = [m.get("name", "") for m in r.json().get("models", [])]
        return any(n == model or n.startswith(model + ":") for n in names)
    except Exception:
        return False


class SystemOneBackend:
    """d1-omni via /v1/systemone: PNG als image + choice/noul-Fragen (Schema oben)."""

    def __init__(self, model: str = DEFAULT_SPECDIFF_MODEL, host: str = DEFAULT_OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    def available(self) -> bool:
        return _ollama_has_model(self.host, self.model)

    def classify_png(self, png_path, dsp_feats: dict | None = None) -> dict:
        import requests
        payload = {
            "model": self.model,
            "state": SPECDIFF_STATE,
            "images": [base64.b64encode(Path(png_path).read_bytes()).decode()],
            "questions": SPECDIFF_QUESTIONS,
        }
        r = requests.post(f"{self.host}/v1/systemone", json=payload, timeout=600)
        if r.status_code != 200:
            raise RuntimeError(f"systemone[{self.model}] HTTP {r.status_code}: {r.text[:200]}")
        ans = r.json()["answers"]
        labels = {"severity": ans["severity"]["choice"],
                  "spread": ans["spread"]["choice"],
                  "temporal": ans["temporal"]["choice"],
                  "bands": [b for b in BAND_NAMES if float(ans[b]["noul"]) >= 0.5]}
        probs = {q: {k: float(v) for k, v in ans[q]["probabilities"].items()}
                 for q in ("severity", "spread", "temporal")}
        probs.update({b: float(ans[b]["noul"]) for b in BAND_NAMES})
        conf = float(np.mean([float(ans[q].get("confidence", 0.0))
                              for q in ("severity", "spread", "temporal")]))
        return {"labels": labels, "probs": probs, "confidence": conf, "model": self.model}


class OllamaChatBackend:
    """Vision-Model via /api/chat (z. B. gemma4:12b-it-qat) – braucht think:false,
    antwortet mit JSON (Schema wie SPECDIFF_QUESTIONS)."""

    def __init__(self, model: str = "gemma4:12b-it-qat", host: str = DEFAULT_OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    def available(self) -> bool:
        return _ollama_has_model(self.host, self.model)

    def classify_png(self, png_path, dsp_feats: dict | None = None) -> dict:
        import urllib.request
        hint = ""
        if dsp_feats:
            hint = (f"\nDSP measurements for orientation: mean |delta| = "
                    f"{dsp_feats.get('severity_db', 0.0):.2f} dB, spread_frac = "
                    f"{dsp_feats.get('spread_frac', 0.0):.2f}, band_mean_db = "
                    f"{dsp_feats.get('band_mean_db')}")
        prompt = (
            "The image shows a spectrogram comparison, three panels left to right: "
            "A = original (Blofeld), B = converted (Iridium), delta = B - A in dB "
            "(blue = B quieter, gray = 0, red = B louder). x = time, y = frequency "
            "log scale, LOW frequencies at TOP. Classify the delta panel and answer "
            "with ONLY a JSON object, no prose, no markdown fences:\n"
            '{"severity": "light|medium|heavy", "spread": "even|punctual", '
            '"temporal": "even|periodical|single|multiple|increasing|decreasing", '
            '"bands": ["low","mid","high"], "summary": "one sentence"}'
            "\nlow < 250 Hz, mid 250-2000 Hz, high > 2000 Hz." + hint)
        payload = {"model": self.model, "stream": False, "think": False,
                   "messages": [{"role": "user", "content": prompt,
                                 "images": [base64.b64encode(Path(png_path).read_bytes()).decode()]}],
                   "options": {"temperature": 0.0, "num_predict": 400}}
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            txt = json.loads(r.read())["message"]["content"]
        parsed = self._parse_chat(txt)
        return {"labels": parsed["labels"], "probs": None, "confidence": None,
                "model": self.model, "summary": parsed.get("summary", "")}

    def _parse_chat(self, txt: str) -> dict:
        """JSON aus roher Modellantwort extrahieren (Fences/Prosa tolerant) + Labels validieren."""
        js = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        labels = {"severity": js["severity"], "spread": js["spread"],
                  "temporal": js["temporal"],
                  "bands": [b for b in js.get("bands", []) if b in BAND_NAMES]}
        if (labels["severity"] not in SEVERITIES or labels["spread"] not in SPREADS
                or labels["temporal"] not in TEMPORALS):
            raise ValueError(f"invalid labels from model: {labels}")
        return {"labels": labels, "summary": js.get("summary", "")}


def build_backend(want: bool = True, model: str = DEFAULT_SPECDIFF_MODEL,
                  kind: str = "systemone"):
    """SystemOneBackend/OllamaChatBackend or None (want=False oder Modell fehlt -> WARNING)."""
    if not want:
        return None
    b = SystemOneBackend(model) if kind == "systemone" else OllamaChatBackend(model)
    if b.available():
        return b
    print(f"WARNING: specdiff backend not available (model {model}) - DSP fallback",
          file=sys.stderr)
    return None


def interpret_pair(x_a, x_b, sr: int = 48000, backend=None, png_path=None) -> dict:
    """Diff zweier Signale interpretieren: DSP immer, Vision wenn backend verfuegbar.

    -> {"labels", "probs", "confidence", "dsp", "vision", "score", "source", "spec_png"}.
    Labels vom Vision-Model wenn es klappt (source="vision"), sonst DSP ("dsp");
    Score immer numerisch aus DSP. Vision-Fehler -> WARNING, nie Absturz.
    """
    from . import sim_embed

    dm = diff_matrix(x_a, x_b, sr)
    feat = dsp_features(dm["delta"], dm["band_edges"], dm["active"])
    labels = classify_dsp(feat)
    probs = conf = vision = None
    source = "dsp"
    spec_png = None
    if backend is not None or png_path is not None:
        try:
            if png_path is None:
                import tempfile
                png_path = Path(tempfile.mkdtemp()) / "specdiff_pair.png"
            sim_embed.render_spec_pair_png(np.asarray(x_a, dtype=np.float64),
                                           np.asarray(x_b, dtype=np.float64),
                                           sr, png_path)
            spec_png = str(png_path)
            if backend is not None:
                vision = backend.classify_png(png_path, feat)
                labels = vision["labels"]
                probs = vision["probs"]
                conf = vision["confidence"]
                source = "vision"
        except Exception as e:
            print(f"WARNING: specdiff vision failed ({e}) - using DSP labels",
                  file=sys.stderr)
    dsp_slim = {"severity_db": feat["severity_db"], "spread_frac": feat["spread_frac"],
                "band_mean_db": feat["band_mean_db"],
                "temporal": {k: v for k, v in feat["temporal"].items() if k != "e"}}
    return {"labels": labels, "probs": probs, "confidence": conf,
            "dsp": dsp_slim, "vision": vision,
            "score": specdiff_score(feat["severity_db"]),
            "source": source, "spec_png": spec_png}

