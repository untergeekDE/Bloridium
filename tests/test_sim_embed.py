"""sim_embed.py – Phase B (TDD Task 2: Helfer, Task 3: ClapBackend)."""

import json
import subprocess
import sys
import wave
from types import SimpleNamespace

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


# ---------- Task 3: ClapBackend ----------

class _FakeCLAP:
    """Ersatz fuer clap_cpp.CLAP: zeichnet Aufruf auf, gibt Einheitsvektor zurueck."""
    instances = []

    def __init__(self, path, threads=0):
        self.path = path
        self.calls = []
        _FakeCLAP.instances.append(self)

    def encode_audio(self, pcm, sample_rate=48000, crop_offset=0):
        self.calls.append({"n": len(pcm), "sr": sample_rate})
        v = np.zeros(512, dtype=np.float32)
        v[0] = 1.0
        return v.tolist()


@pytest.fixture
def fake_clap_cpp(monkeypatch):
    _FakeCLAP.instances = []
    fake_mod = SimpleNamespace(CLAP=_FakeCLAP)
    monkeypatch.setitem(sys.modules, "clap_cpp", fake_mod)
    return fake_mod


def test_clap_backend_embed_shape_norm(fake_clap_cpp, tmp_path):
    model = tmp_path / "m.gguf"
    model.write_bytes(b"x")
    b = sim_embed.ClapBackend(model)
    v = b.embed(sine(440.0, dur=1.0), SR)
    assert v.shape == (512,)
    assert v.dtype == np.float32
    assert np.linalg.norm(v) == pytest.approx(1.0)
    assert b._clap.calls[0]["sr"] == 48000


def test_clap_backend_resamples_non_48k(fake_clap_cpp, tmp_path):
    model = tmp_path / "m.gguf"
    model.write_bytes(b"x")
    b = sim_embed.ClapBackend(model)
    x = sine(440.0, dur=1.0, sr=44100)  # 44100 samples
    b.embed(x, 44100)
    call = b._clap.calls[0]
    assert call["sr"] == 48000
    assert call["n"] == int(round(44100 * 48000 / 44100))


def test_clap_backend_different_lengths_ok(fake_clap_cpp, tmp_path):
    model = tmp_path / "m.gguf"
    model.write_bytes(b"x")
    b = sim_embed.ClapBackend(model)
    for n in (126080, 133969):
        v = b.embed(np.zeros(n, dtype=np.float32), SR)
        assert v.shape == (512,)


def test_clap_backend_missing_model_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        sim_embed.ClapBackend(tmp_path / "fehlt.gguf")


def test_clap_backend_subprocess_fallback(monkeypatch, tmp_path):
    model = tmp_path / "m.gguf"
    model.write_bytes(b"x")
    monkeypatch.setitem(sys.modules, "clap_cpp", None)  # import schlaegt fehl
    monkeypatch.setattr(sim_embed.shutil, "which", lambda name: "/fake/clap" if name == "clap" else None)
    vec = [0.0] * 511 + [1.0]

    def fake_run(cmd, **kw):
        assert cmd[0] == "/fake/clap" and "--audio" in cmd
        return SimpleNamespace(returncode=0, stdout=json.dumps(vec))

    monkeypatch.setattr(sim_embed.subprocess, "run", fake_run)
    b = sim_embed.ClapBackend(model)
    v = b.embed(sine(440.0, dur=0.5), SR)
    assert v.shape == (512,) and np.linalg.norm(v) == pytest.approx(1.0)


def test_clap_backend_error_wrapped(fake_clap_cpp, tmp_path, monkeypatch):
    model = tmp_path / "m.gguf"
    model.write_bytes(b"x")

    def boom(self, pcm, sample_rate=48000, crop_offset=0):
        raise ValueError("kaputt")

    monkeypatch.setattr(_FakeCLAP, "encode_audio", boom)
    b = sim_embed.ClapBackend(model)
    with pytest.raises(RuntimeError, match="CLAP"):
        b.embed(sine(440.0, dur=0.5), SR)


# ---------- Task 4: OllamaBackend + DEFAULT_JUDGE_PROMPT ----------

def _resp(status=200, payload=None):
    return SimpleNamespace(status_code=status, json=lambda: payload or {},
                           text=json.dumps(payload or {}))


def _chat_payload(content):
    return {"message": {"role": "assistant", "content": content}}


def test_default_prompt_deutsch_mit_anker_und_contract():
    p = sim_embed.DEFAULT_JUDGE_PROMPT
    assert "100" in p and "nicht unterscheidbar" in p
    assert '"score"' in p and '"summary"' in p and '"differences"' in p


def test_ollama_available_true_false(monkeypatch):
    b = sim_embed.OllamaBackend(model="lfm3-omni:2b", host="http://x:1")
    monkeypatch.setattr(sim_embed.requests, "get",
                        lambda url, timeout=5: _resp(200, {"models": [{"name": "lfm3-omni:2b"}]}))
    assert b.available() is True
    monkeypatch.setattr(sim_embed.requests, "get",
                        lambda url, timeout=5: _resp(200, {"models": [{"name": "other:1"}]}))
    assert b.available() is False

    def boom(url, timeout=5):
        raise ConnectionError("down")
    monkeypatch.setattr(sim_embed.requests, "get", boom)
    assert b.available() is False


def test_judge_audio_mode_ok(monkeypatch, tmp_path):
    calls = []

    def fake_post(url, json=None, timeout=60):
        calls.append(json)
        return _resp(200, _chat_payload('{"score": 87, "summary": "nah dran", "differences": ["heller"]}'))

    monkeypatch.setattr(sim_embed.requests, "post", fake_post)
    b = sim_embed.OllamaBackend()
    r = b.judge(sine(440.0, 0.5), sine(450.0, 0.5), SR)
    assert r["mode"] == "audio" and r["score"] == 87
    assert r["summary"] == "nah dran" and r["differences"] == ["heller"]
    assert r["model"] == sim_embed.DEFAULT_OLLAMA_MODEL
    # Audio-Modus: base64-WAVs im Payload
    msgs = calls[0]["messages"]
    assert "audio" in msgs[0] and len(msgs[0]["audio"]) == 2


def test_judge_falls_back_to_spec_on_400(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=60):
        calls.append(json)
        if "audio" in calls[-1]["messages"][0]:
            return _resp(400, {"error": "audio unsupported"})
        return _resp(200, _chat_payload('{"score": 55, "summary": "s", "differences": []}'))

    monkeypatch.setattr(sim_embed.requests, "post", fake_post)
    b = sim_embed.OllamaBackend()
    r = b.judge(sine(440.0, 0.5), sine(220.0, 0.5), SR)
    assert r["mode"] == "spec" and r["score"] == 55
    assert "images" in calls[-1]["messages"][0] and len(calls[-1]["messages"][0]["images"]) == 2


def test_judge_parses_json_inside_prose(monkeypatch):
    monkeypatch.setattr(sim_embed.requests, "post",
                        lambda url, json=None, timeout=60: _resp(
                            200, _chat_payload('Hier das Urteil:\n{"score": 42, "summary": "x", "differences": ["a", "b"]} Ende.')))
    b = sim_embed.OllamaBackend()
    r = b.judge(sine(440.0, 0.5), sine(440.0, 0.5), SR)
    assert r["score"] == 42 and r["differences"] == ["a", "b"]


def test_judge_invalid_json_raises(monkeypatch):
    monkeypatch.setattr(sim_embed.requests, "post",
                        lambda url, json=None, timeout=60: _resp(200, _chat_payload("kein JSON hier")))
    b = sim_embed.OllamaBackend()
    with pytest.raises(RuntimeError, match="ollama"):
        b.judge(sine(440.0, 0.5), sine(440.0, 0.5), SR)


def test_judge_score_geclippt_0_100(monkeypatch):
    monkeypatch.setattr(sim_embed.requests, "post",
                        lambda url, json=None, timeout=60: _resp(
                            200, _chat_payload('{"score": 250, "summary": "s", "differences": []}')))
    b = sim_embed.OllamaBackend()
    r = b.judge(sine(440.0, 0.5), sine(440.0, 0.5), SR)
    assert r["score"] == 100
