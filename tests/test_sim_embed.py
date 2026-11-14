"""sim_embed.py – Phase B: reine Helfer (TDD Task 2: write_wav/render_spec_png/embed_compare)."""

import wave

import numpy as np
import pytest
from PIL import Image

from bloridium import sim_embed

SR = 48000


def sine(freq, dur=1.0, sr=SR, amp=0.5):
    t = np.arange(int(dur * sr)) / sr
    return amp * np.sin(2 * np.pi * freq * t)


def test_write_wav_roundtrip(tmp_path):
    x = sine(440.0, dur=0.5, amp=0.8)
    p = tmp_path / "t.wav"
    sim_embed.write_wav(x, SR, p)
    with wave.open(str(p), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == SR
        assert w.getsampwidth() == 2
        raw = w.readframes(w.getnframes())
    y = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    assert len(y) == len(x)
    assert np.max(np.abs(y)) == pytest.approx(0.8, abs=1e-3)


def test_write_wav_clippt_ueber_1(tmp_path):
    x = np.array([2.0, -2.0, 0.5])
    p = tmp_path / "c.wav"
    sim_embed.write_wav(x, SR, p)
    with wave.open(str(p), "rb") as w:
        y = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    assert y[0] == 32767 and y[1] == -32768
    assert abs(y[2] / 32767.0 - 0.5) < 1e-3  # int16-Rundung


def test_render_spec_png_valid(tmp_path):
    x = sine(1000.0, dur=1.0)
    p = tmp_path / "s.png"
    sim_embed.render_spec_png(x, SR, p)
    with Image.open(p) as im:
        assert im.format == "PNG"
        assert im.mode == "L"
        assert im.size[0] > 0 and im.size[1] > 0


def test_render_spec_png_zu_kurz_wirft(tmp_path):
    with pytest.raises(ValueError):
        sim_embed.render_spec_png(np.zeros(100), SR, tmp_path / "x.png")


def test_embed_compare_edges():
    r = sim_embed.embed_compare(np.array([1.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
    assert set(r.keys()) == {"embed_cos", "embed_score"}
    assert r["embed_cos"] == pytest.approx(1.0)
    assert r["embed_score"] == pytest.approx(100.0)
    r0 = sim_embed.embed_compare(np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    assert r0["embed_cos"] == pytest.approx(0.0)
    assert r0["embed_score"] == pytest.approx(0.0)
    rn = sim_embed.embed_compare(np.array([1.0, 0.0]), np.array([-1.0, 0.0]))
    assert rn["embed_cos"] == pytest.approx(-1.0)
    assert rn["embed_score"] == 0.0  # negativ geclippt
    rz = sim_embed.embed_compare(np.zeros(3), np.array([1.0, 0.0, 0.0]))
    assert rz["embed_cos"] == 0.0 and rz["embed_score"] == 0.0  # Null-Vektor kein Crash
