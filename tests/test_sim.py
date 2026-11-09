"""sim.py – Features: log-Spektrogramm + RMS-Huelle (TDD Task 1)."""

import numpy as np
import pytest

from bloridium import sim

SR = 48000


def sine(freq, dur=1.0, sr=SR, amp=0.5):
    t = np.arange(int(dur * sr)) / sr
    return amp * np.sin(2 * np.pi * freq * t)


def band_centers(edges):
    return np.sqrt(edges[:-1] * edges[1:])


def test_features_sine_peak_im_richtigen_band():
    f = sim.features(sine(440.0))
    band = int(np.argmax(f["log_spec"].mean(axis=1)))
    nearest = int(np.argmin(np.abs(band_centers(f["band_edges"]) - 440.0)))
    assert abs(band - nearest) <= 1


def test_features_dc_wird_durch_hp_entfernt():
    x = np.full(SR, 0.5) + 0.01 * sine(1000.0, amp=1.0)
    f = sim.features(x)
    band = int(np.argmax(f["log_spec"].mean(axis=1)))
    nearest_1k = int(np.argmin(np.abs(band_centers(f["band_edges"]) - 1000.0)))
    assert abs(band - nearest_1k) <= 1  # nicht das DC-Band 0


def test_features_zu_kurz_wirft():
    with pytest.raises(ValueError):
        sim.features(np.zeros(int(0.1 * SR)))


# --- Task 2: compare() ---

def test_compare_identisch_score_100():
    fa = sim.features(sine(440.0))
    r = sim.compare(fa, fa)
    assert r["score"] == pytest.approx(100.0, abs=0.5)
    assert r["verdict"] == "nahe"


def test_compare_anderes_spektrum_score_sinkt():
    # Sinus vs Saege (gleicher Grundton, anderes Obertonspektrum) -> deutlich abaixo 100
    t = np.arange(SR) / SR
    saw = 0.5 * (2 * ((220.0 * t) % 1) - 1)
    fa = sim.features(sine(220.0))
    fb = sim.features(saw)
    r = sim.compare(fa, fb)
    assert r["spec_cos"] < 0.85
    assert r["score"] < 95.0


def test_compare_unterschiedliche_laenge_ok():
    fa = sim.features(sine(440.0, dur=1.0))
    fb = sim.features(sine(440.0, dur=0.7))
    r = sim.compare(fa, fb)
    assert 0.0 <= r["score"] <= 100.0


def test_band_delta_vorzeichen_heller_positiv_oben():
    fa = sim.features(sine(440.0))
    fb = sim.features(sine(4000.0))   # heller -> hohe Baender staerker
    r = sim.compare(fa, fb)
    delta = np.array(r["band_delta_db"])
    edges = sim.features(sine(440.0))["band_edges"]
    high = np.sqrt(edges[:-1] * edges[1:]) > 2000
    assert delta[high].mean() > 0
    assert delta[~high].mean() < 0
