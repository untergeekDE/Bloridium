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
