"""sim.py - features: log-spectrogram + RMS envelope (TDD Task 1)."""

import numpy as np
import pytest

from bloridium import sim

SR = 48000


def sine(freq, dur=1.0, sr=SR, amp=0.5):
    t = np.arange(int(dur * sr)) / sr
    return amp * np.sin(2 * np.pi * freq * t)


def band_centers(edges):
    return np.sqrt(edges[:-1] * edges[1:])


def test_features_sine_peak_in_right_band():
    f = sim.features(sine(440.0))
    band = int(np.argmax(f["log_spec"].mean(axis=1)))
    nearest = int(np.argmin(np.abs(band_centers(f["band_edges"]) - 440.0)))
    assert abs(band - nearest) <= 1


def test_features_dc_removed_by_hp_filter():
    x = np.full(SR, 0.5) + 0.01 * sine(1000.0, amp=1.0)
    f = sim.features(x)
    band = int(np.argmax(f["log_spec"].mean(axis=1)))
    nearest_1k = int(np.argmin(np.abs(band_centers(f["band_edges"]) - 1000.0)))
    assert abs(band - nearest_1k) <= 1  # not the DC band 0


def test_features_too_short_raises():
    with pytest.raises(ValueError):
        sim.features(np.zeros(int(0.1 * SR)))


# --- Task 2: compare() ---

def test_compare_identical_scores_100():
    fa = sim.features(sine(440.0))
    r = sim.compare(fa, fa)
    assert r["score"] == pytest.approx(100.0, abs=0.5)
    assert r["verdict"] == "close"


def test_compare_different_spectrum_score_drops():
    # sine vs saw (same fundamental, different overtone spectrum) -> clearly below 100
    t = np.arange(SR) / SR
    saw = 0.5 * (2 * ((220.0 * t) % 1) - 1)
    fa = sim.features(sine(220.0))
    fb = sim.features(saw)
    r = sim.compare(fa, fb)
    assert r["spec_cos"] < 0.85
    assert r["score"] < 95.0


def test_compare_different_lengths_ok():
    fa = sim.features(sine(440.0, dur=1.0))
    fb = sim.features(sine(440.0, dur=0.7))
    r = sim.compare(fa, fb)
    assert 0.0 <= r["score"] <= 100.0


def test_band_delta_sign_brighter_positive_at_top():
    fa = sim.features(sine(440.0))
    fb = sim.features(sine(4000.0))   # brighter -> high bands stronger
    r = sim.compare(fa, fb)
    delta = np.array(r["band_delta_db"])
    edges = sim.features(sine(440.0))["band_edges"]
    high = np.sqrt(edges[:-1] * edges[1:]) > 2000
    assert delta[high].mean() > 0
    assert delta[~high].mean() < 0


# --- Task 3: log_run + score_pair ---

def test_log_run_writes_jsonl(tmp_path):
    p = tmp_path / "sim_log.jsonl"
    ok = sim.log_run({"score": 91.0}, {"blofeld": "A043"}, path=p)
    assert ok is True
    lines = p.read_text().strip().splitlines()
    assert len(lines) == 1
    import json
    row = json.loads(lines[0])
    assert row["meta"]["blofeld"] == "A043"
    assert row["result"]["score"] == 91.0
    assert "ts" in row


def test_log_run_broken_path_returns_false(tmp_path):
    # mkdir fails because "blocker" is a file
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    ok = sim.log_run({"score": 1}, {}, path=blocker / "sub" / "log.jsonl")
    assert ok is False


def test_score_pair_too_short_returns_error(tmp_path):
    p = tmp_path / "log.jsonl"
    r = sim.score_pair(np.zeros(int(0.05 * SR)), sine(440.0), sr=SR,
                       meta={"test": 1}, log_path=p)
    assert r["verdict"] == "error"
    assert r["score"] is None
    assert p.exists()  # still logged


# --- Fix Important 2: silence guard + level-independent envelope ---

def test_score_pair_silence_returns_error(tmp_path):
    p = tmp_path / "log.jsonl"
    r = sim.score_pair(np.zeros(SR), sine(440.0), sr=SR, meta={}, log_path=p)
    assert r["verdict"] == "error"
    assert r["score"] is None


def test_compare_level_independent():
    # same sound, half the level -> high score after env normalization
    fa = sim.features(sine(440.0, amp=0.5))
    fb = sim.features(sine(440.0, amp=0.25))
    r = sim.compare(fa, fb)
    assert r["score"] > 95.0


# --- Phase A v2: time-resolved FFT metrics (2026-11-15, user: "FFT over time") ---

def test_compare_time_resolved_identical():
    sr = 48000
    t = np.arange(sr) / sr
    x = 0.5 * np.sin(2 * np.pi * 440 * t)
    r = sim.compare(sim.features(x, sr), sim.features(x.copy(), sr))
    assert r["spec_dtw"] == pytest.approx(0.0, abs=1e-9)
    assert max(r["band_dtw"]) < 1e-6
    assert min(r["frame_cos"]) > 0.999
    assert len(r["band_dtw"]) == 48
    assert len(r["frame_cos"]) == r["log_spec_frames"] if "log_spec_frames" in r else True
    assert len(r["band_edges_hz"]) == 49


def test_compare_time_shift_visible_in_frame_cos_and_spec_dtw():
    # same burst signal shifted by 0.3 s -> frame_cos drops, spec_dtw > 0
    sr = 48000
    t = np.arange(sr) / sr
    x = 0.5 * np.sin(2 * np.pi * 220 * t) * (t < 0.5)
    y = np.zeros_like(x)
    y[int(0.3 * sr):] = x[: x.size - int(0.3 * sr)]
    r = sim.compare(sim.features(x, sr), sim.features(y, sr))
    assert min(r["frame_cos"]) < 0.95
    assert r["spec_dtw"] > 0.01


def test_compare_band_dtw_localizes_high_bands():
    # A additional high overtones, B pure sine -> band_dtw clearly higher at top than bottom
    sr = 48000
    t = np.arange(sr) / sr
    a = 0.5 * np.sin(2 * np.pi * 220 * t) + 0.3 * np.sin(2 * np.pi * 2000 * t)
    b = 0.5 * np.sin(2 * np.pi * 220 * t)
    r = sim.compare(sim.features(a, sr), sim.features(b, sr))
    assert max(r["band_dtw"][-8:]) > max(r["band_dtw"][:8]) + 0.05
