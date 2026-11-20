"""Similarity Blofeld <-> Iridium (phase A, numpy-only).

features()  - log-spaced spectrogram (dB) + RMS envelope, with FFT high-pass
compare()   - score 0-100 = 70 % level-aligned band deviation + 30 % envelope DTW
              (score_version 2; v1 used a dB-spectrum cosine that saturated)
log_run()   - JSONL log per measurement (recordings/sim_log.jsonl) -> training data
score_pair()- convenience: two raw signals -> features+compare+log
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO / "recordings" / "sim_log.jsonl"

_FRAME = 2048          # FFT window (~43 ms @48 kHz)
_MIN_SEC = 0.2         # shorter -> ValueError


def features(x: np.ndarray, sr: int = 48000, n_bands: int = 48,
             f_lo: float = 40.0, f_hi: float = 12000.0,
             hop_s: float = 0.05, hp_hz: float = 80.0) -> dict:
    """Log spectrogram (n_bands x n_frames, dB) + RMS envelope (n_frames,).

    FFT high-pass `hp_hz` on the whole signal removes DC/mains hum before
    windowing. Raises ValueError below _MIN_SEC seconds.
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size < int(_MIN_SEC * sr):
        raise ValueError(f"too short: {x.size} samples < {int(_MIN_SEC * sr)} @ {sr} Hz")
    # high-pass (analysis only)
    X = np.fft.rfft(x)
    f_all = np.fft.rfftfreq(x.size, 1 / sr)
    X[f_all < hp_hz] = 0.0
    x = np.fft.irfft(X, x.size)

    hop = max(1, int(hop_s * sr))
    win = np.hanning(_FRAME)
    n_frames = 1 + max(0, (x.size - _FRAME) // hop)
    # log-spaced bands: matches the ear's roughly logarithmic frequency resolution,
    # so one band ~ constant perceptual weight instead of favoring high frequencies
    band_edges = np.geomspace(f_lo, f_hi, n_bands + 1)

    log_spec = np.empty((n_bands, n_frames), dtype=np.float64)
    env_rms = np.empty(n_frames, dtype=np.float64)
    # FFT bin frequencies and band masks are the same for every frame -> compute once
    ff = np.fft.rfftfreq(_FRAME, 1 / sr)
    masks = [(ff >= band_edges[b]) & (ff < band_edges[b + 1]) for b in range(n_bands)]
    for t in range(n_frames):
        seg = x[t * hop:t * hop + _FRAME]
        if seg.size < _FRAME:
            seg = np.pad(seg, (0, _FRAME - seg.size))
        env_rms[t] = float(np.sqrt(np.mean(seg ** 2)))
        Xf = np.abs(np.fft.rfft(seg * win))
        for b, m in enumerate(masks):
            # band energy -> dB; +1e-12 avoids log(0) on empty bands
            e = float(np.sqrt(np.sum(Xf[m] ** 2))) if m.any() else 0.0
            log_spec[b, t] = 20 * np.log10(e + 1e-12)

    return {"log_spec": log_spec, "env_rms": env_rms,
            "band_edges": band_edges, "sr": sr, "n_samples": int(x.size)}


def _dtw(a: np.ndarray, b: np.ndarray) -> float:
    """Simple DTW DP (numpy) on 1D sequences; cost = |a-b|, normalized to 0..1."""
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


_DB_SCALE = 40.0  # 40 dB difference = dtw cost 1.0 (clearly audible) for band_dtw


SCORE_VERSION = 2  # bump whenever the score formula changes (logged per result)
_ACTIVE_DB = 60.0  # bands more than 60 dB below the loudest band count as empty
_MAD_SCALE = 20.0  # 20 dB mean level-aligned band deviation = spectrally unrelated


def _verdict(score: float) -> str:
    return "close" if score >= 85 else ("medium" if score >= 60 else "far")


def _spec_mad_db(sa: np.ndarray, sb: np.ndarray) -> float:
    """Mean absolute band deviation (dB) of two frame-averaged log spectra.

    Why this exists: the cosine in compare() runs on raw dB vectors, which are
    almost entirely negative (-40..-120 dB), so it stays near 1.0 for unrelated
    timbres (saw vs. white noise scores 99.3). This metric instead
    - keeps only bands that are active in at least one signal (within
      _ACTIVE_DB of that signal's loudest band), so empty bands at the
      -240 dB floor do not dominate,
    - removes the overall level offset (median of the deltas), because gain
      differences are handled separately and are not timbre.
    """
    active = (sa > sa.max() - _ACTIVE_DB) | (sb > sb.max() - _ACTIVE_DB)
    if not active.any():
        return 0.0
    # clamp to the active range so a band that is empty in one signal counts
    # as "_ACTIVE_DB quieter", not as ~200 dB quieter
    lo_a, lo_b = sa.max() - _ACTIVE_DB, sb.max() - _ACTIVE_DB
    d = np.maximum(sb, lo_b)[active] - np.maximum(sa, lo_a)[active]
    d = d - np.median(d)
    return float(np.mean(np.abs(d)))


def compare(fa: dict, fb: dict) -> dict:
    """Score 0-100: 70 % spectral similarity + 30 % (1-DTW) envelope.

    Spectral similarity = 1 - spec_mad_db / 20 dB (see _spec_mad_db), clipped to 0..1.

    Why 70/30: the frame-averaged spectrum carries the timbre, the dominant
    perceptual dimension of a held synth note; the envelope DTW catches
    attack/decay timing differences. Spectrum gets the larger weight because
    small envelope deviations are less audible than spectral ones.

    Phase A v2 (2026-11-15): additionally time-resolved FFT metrics from the
    log_spec (bands x frames) - diagnostic only, the score formula stays compatible:
      band_dtw    per band: DTW over time (dB/40, 0..1) -> WHERE in frequency
      spec_dtw    mean over band_dtw
      frame_cos   per frame: cosine of the (mean-subtracted) band vectors -> WHEN
      band_edges_hz  frequency edges of the bands for log/print

    score_version 2 (2026-11-20): v1 used the cosine of the raw dB spectra
    (`spec_cos`, still returned as a diagnostic). That saturates: saw vs. white
    noise scored 99.3, see docs/FINDINGS.md. Log rows without
    result.score_version are v1 scores and must not be mixed with v2 for training.
    """
    sa = fa["log_spec"].mean(axis=1)
    sb = fb["log_spec"].mean(axis=1)
    denom = float(np.linalg.norm(sa) * np.linalg.norm(sb))
    spec_cos = float(np.dot(sa, sb) / denom) if denom > 0 else 0.0
    spec_cos = max(0.0, min(1.0, spec_cos))
    # normalize envelope to its peak (otherwise env_dtw is gain-dependent)
    ea, eb = fa["env_rms"], fb["env_rms"]
    ma, mb = float(ea.max()), float(eb.max())
    if ma > 0:
        ea = ea / ma
    if mb > 0:
        eb = eb / mb
    env_dtw = max(0.0, min(1.0, _dtw(ea, eb)))
    spec_mad_db = _spec_mad_db(sa, sb)
    spec_sim = max(0.0, min(1.0, 1.0 - spec_mad_db / _MAD_SCALE))
    score = max(0.0, min(100.0, 100.0 * (0.7 * spec_sim + 0.3 * (1.0 - env_dtw))))
    verdict = _verdict(score)
    band_delta_db = (fb["log_spec"].mean(axis=1) - fa["log_spec"].mean(axis=1)).tolist()

    # time-resolved: per band DTW over the frames (dB scaled), per frame cosine
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
            frame_cos.append(1.0)          # both frames empty -> equal
        elif na == 0 or nb == 0:
            frame_cos.append(0.0)          # only one empty -> completely different
        else:
            frame_cos.append(max(0.0, min(1.0, float(np.dot(a, b) / (na * nb)))))
    return {"score": round(score, 2), "spec_cos": round(spec_cos, 4),
            "env_dtw": round(env_dtw, 4), "band_delta_db": [round(v, 2) for v in band_delta_db],
            "verdict": verdict,
            "spec_mad_db": round(spec_mad_db, 2), "score_version": SCORE_VERSION,
            "spec_dtw": round(spec_dtw, 4),
            "band_dtw": [round(v, 4) for v in band_dtw],
            "frame_cos": [round(v, 4) for v in frame_cos],
            "band_edges_hz": [round(float(e), 1) for e in fa["band_edges"]]}


def log_run(result: dict, meta: dict, path=DEFAULT_LOG) -> bool:
    """Append one JSON line to `path`. OSError -> False (never raise)."""
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
    """Two raw signals -> features + compare + log. Too-short signals -> verdict 'error'."""
    meta = meta or {}
    try:
        fa = features(x_blo, sr)
        fb = features(x_irr, sr)
    except ValueError as e:
        result = {"score": None, "verdict": "error", "error": str(e)}
        log_run(result, meta, log_path)
        return result
    # silence guard: dead recording (wrong cable / silent synth) -> error, never "medium"
    if float(fa["env_rms"].max()) < 1e-4 or float(fb["env_rms"].max()) < 1e-4:
        result = {"score": None, "verdict": "error",
                  "error": "silent recording (env_rms max < 1e-4)"}
        log_run(result, meta, log_path)
        return result
    result = compare(fa, fb)
    log_run(result, meta, log_path)
    return result
