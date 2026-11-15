"""Ähnlichkeit Blofeld ↔ Iridium (Phase A, numpy-only).

features()  – log-spaced Spektrogramm (dB) + RMS-Hüllkurve, mit FFT-Hochpass
compare()   – Score 0-100 = 70 % Spektrogramm-Cosine + 30 % Hüllkurven-DTW
log_run()   – JSONL-Log pro Messung (recordings/sim_log.jsonl) -> Trainingsdaten
score_pair()– Convenience: zwei Rohsignale -> features+compare+log
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO / "recordings" / "sim_log.jsonl"

_FRAME = 2048          # FFT-Fenster (~43 ms @48 kHz)
_MIN_SEC = 0.2         # darunter ValueError


def features(x: np.ndarray, sr: int = 48000, n_bands: int = 48,
             f_lo: float = 40.0, f_hi: float = 12000.0,
             hop_s: float = 0.05, hp_hz: float = 80.0) -> dict:
    """Log-Spektrogramm (n_bands x n_frames, dB) + RMS-Hülle (n_frames,).

    FFT-Hochpass `hp_hz` auf dem Gesamtsignal entfernt DC/Netzbrumm, bevor
    gefenstert wird. Wirft ValueError bei weniger als _MIN_SEC Sekunden.
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size < int(_MIN_SEC * sr):
        raise ValueError(f"zu kurz: {x.size} samples < {int(_MIN_SEC * sr)} @ {sr} Hz")
    # Hochpass (Analyse-only)
    X = np.fft.rfft(x)
    f_all = np.fft.rfftfreq(x.size, 1 / sr)
    X[f_all < hp_hz] = 0.0
    x = np.fft.irfft(X, x.size)

    hop = max(1, int(hop_s * sr))
    win = np.hanning(_FRAME)
    n_frames = 1 + max(0, (x.size - _FRAME) // hop)
    band_edges = np.geomspace(f_lo, f_hi, n_bands + 1)

    log_spec = np.empty((n_bands, n_frames), dtype=np.float64)
    env_rms = np.empty(n_frames, dtype=np.float64)
    for t in range(n_frames):
        seg = x[t * hop:t * hop + _FRAME]
        if seg.size < _FRAME:
            seg = np.pad(seg, (0, _FRAME - seg.size))
        env_rms[t] = float(np.sqrt(np.mean(seg ** 2)))
        Xf = np.abs(np.fft.rfft(seg * win))
        ff = np.fft.rfftfreq(_FRAME, 1 / sr)
        for b in range(n_bands):
            m = (ff >= band_edges[b]) & (ff < band_edges[b + 1])
            e = float(np.sqrt(np.sum(Xf[m] ** 2))) if m.any() else 0.0
            log_spec[b, t] = 20 * np.log10(e + 1e-12)

    return {"log_spec": log_spec, "env_rms": env_rms,
            "band_edges": band_edges, "sr": sr, "n_samples": int(x.size)}


def _dtw(a: np.ndarray, b: np.ndarray) -> float:
    """Einfache DTW-DP (numpy) auf 1D-Folgen; Kosten = |a-b|, normiert auf 0..1."""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return 1.0
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = abs(a[i - 1] - b[j - 1])
            D[i, j] = c + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return float(D[n, m] / (n + m))


_DB_SCALE = 40.0  # 40 dB Differenz = dtw-Kosten 1.0 (deutlich hörbar) bei band_dtw


def compare(fa: dict, fb: dict) -> dict:
    """Score 0-100: 70 % Cosine auf frame-gemitteltem log_spec + 30 % (1-DTW) Hülle.

    Phase A v2 (2026-11-15): zusaetzlich zeitaufgeloeste FFT-Metriken aus dem
    log_spec (Bänder x Frames) — diagnostisch, Score-Formel bleibt kompatibel:
      band_dtw    pro Band: DTW ueber die Zeit (dB/40, 0..1) -> WO in Frequenz
      spec_dtw    Mittel ueber band_dtw
      frame_cos   pro Frame: Cosine der (Mittelwert-bereinigten) Bandvektoren -> WANN
      band_edges_hz  Frequenzgrenzen der Bänder fürs Log/Print
    """
    sa = fa["log_spec"].mean(axis=1)
    sb = fb["log_spec"].mean(axis=1)
    denom = float(np.linalg.norm(sa) * np.linalg.norm(sb))
    spec_cos = float(np.dot(sa, sb) / denom) if denom > 0 else 0.0
    spec_cos = max(0.0, min(1.0, spec_cos))
    # Huellkurve pegel-normalisieren (sonst ist env_dtw gain-abhaengig)
    ea, eb = fa["env_rms"], fb["env_rms"]
    ma, mb = float(ea.max()), float(eb.max())
    if ma > 0:
        ea = ea / ma
    if mb > 0:
        eb = eb / mb
    env_dtw = max(0.0, min(1.0, _dtw(ea, eb)))
    score = 100.0 * (0.7 * spec_cos + 0.3 * (1.0 - env_dtw))  # env_dtw siehe unten
    score = max(0.0, min(100.0, score))
    verdict = "nahe" if score >= 85 else ("mittel" if score >= 60 else "weit")
    band_delta_db = (fb["log_spec"].mean(axis=1) - fa["log_spec"].mean(axis=1)).tolist()

    # zeitaufgeloest: pro Band DTW ueber die Frames (dB skaliert), pro Frame Cosine
    sa2, sb2 = fa["log_spec"], fb["log_spec"]
    n_frames = min(sa2.shape[1], sb2.shape[1])
    band_dtw = []
    for b in range(sa2.shape[0]):
        d = _dtw(sa2[b, :n_frames] / _DB_SCALE, sb2[b, :n_frames] / _DB_SCALE)
        band_dtw.append(max(0.0, min(1.0, d)))
    spec_dtw = float(np.mean(band_dtw)) if band_dtw else 1.0
    frame_cos = []
    for t in range(n_frames):
        a = sa2[:, t] - sa2[:, t].mean()
        b = sb2[:, t] - sb2[:, t].mean()
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        if na == 0 and nb == 0:
            frame_cos.append(1.0)          # beide Frames leer -> gleich
        elif na == 0 or nb == 0:
            frame_cos.append(0.0)          # nur einer leer -> voellig verschieden
        else:
            frame_cos.append(max(0.0, min(1.0, float(np.dot(a, b) / (na * nb)))))
    return {"score": round(score, 2), "spec_cos": round(spec_cos, 4),
            "env_dtw": round(env_dtw, 4), "band_delta_db": [round(v, 2) for v in band_delta_db],
            "verdict": verdict,
            "spec_dtw": round(spec_dtw, 4),
            "band_dtw": [round(v, 4) for v in band_dtw],
            "frame_cos": [round(v, 4) for v in frame_cos],
            "band_edges_hz": [round(float(e), 1) for e in fa["band_edges"]]}


def log_run(result: dict, meta: dict, path=DEFAULT_LOG) -> bool:
    """Eine JSON-Zeile an `path` anhängen. OSError -> False (nie werfen)."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y%m%d_%H%M%S"),
                                "meta": meta, "result": result}) + "\n")
        return True
    except OSError:
        return False


def score_pair(x_blo, x_irr, sr: int = 48000, meta: dict | None = None,
               log_path=DEFAULT_LOG) -> dict:
    """Zwei Rohsignale -> features + compare + log. Zu kurze Signale -> verdict 'fehler'."""
    meta = meta or {}
    try:
        fa = features(x_blo, sr)
        fb = features(x_irr, sr)
    except ValueError as e:
        result = {"score": None, "verdict": "fehler", "error": str(e)}
        log_run(result, meta, log_path)
        return result
    # Stille-Guard: tote Aufnahme (falsches Kabel/stummer Synth) -> fehler, nie "mittel"
    if float(fa["env_rms"].max()) < 1e-4 or float(fb["env_rms"].max()) < 1e-4:
        result = {"score": None, "verdict": "fehler",
                  "error": "stille Aufnahme (env_rms max < 1e-4)"}
        log_run(result, meta, log_path)
        return result
    result = compare(fa, fb)
    log_run(result, meta, log_path)
    return result
