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
