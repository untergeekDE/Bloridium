"""sim_embed.py – Phase B (TDD Task 2: Helfer, Task 3: ClapBackend)."""

import json
import subprocess
import sys
import wave
from pathlib import Path
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


# ---------- Task 5: score_pair_embed ----------

REC = sim_embed.REPO / "recordings"
# Nur das check_-Paar hat eine nicht-stille Iridium-Seite (die ab_A043-Iridium-Takes
# sind ~1e-5 = stumm, siehe sim_log "stille Aufnahme"); daher check_* als Real-Paar.
PAAR = ("check_20261108_152813_blofeld.npy", "check_20261108_152813_iridium.npy")

SCHEMA_KEYS = {"score", "spec_cos", "env_dtw", "band_delta_db", "verdict", "error",
               "embed_cos", "embed_score", "combined", "llm", "backend_error", "peak_dbfs",
               "profile", "spec_dtw", "band_dtw", "frame_cos", "band_edges_hz", "spec_png"}


class _FakeClap:
    model_path = REC / "fake.gguf"  # nur Name fürs Log

    def embed(self, x, sr):
        v = np.zeros(512, dtype=np.float32)
        v[0] = 1.0
        return v


class _FakeOllama:
    model = "fake-omni:1"

    def available(self):
        return True

    def judge(self, x_a, x_b, sr, prompt=None, peak_a=None, peak_b=None):
        return {"score": 90, "summary": "nah", "differences": ["d"], "mode": "audio",
                "model": self.model}


def _load(p):
    x = np.load(REC / p)
    return x.mean(axis=0) if x.ndim > 1 else x


def test_score_pair_embed_full_schema(tmp_path):
    log = tmp_path / "log.jsonl"
    r = sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR,
                                   meta={"run": "t"}, log_path=log, clap=_FakeClap())
    assert set(r.keys()) == SCHEMA_KEYS  # Schema stabil, auch ohne llm
    assert r["embed_cos"] == pytest.approx(1.0)  # Fake liefert gleichen Vektor
    assert r["embed_score"] == pytest.approx(100.0)
    assert r["combined"] == pytest.approx(round(0.5 * r["score"] + 0.5 * 100.0, 2))
    assert r["llm"] is None and r["backend_error"] is None
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1  # genau ein Log-Eintrag
    entry = json.loads(lines[0])
    assert entry["meta"]["run"] == "t"
    assert entry["meta"]["backends"]["clap"] == "fake.gguf"
    assert entry["meta"]["backends"]["ollama"] == "none"
    assert set(entry["result"].keys()) == SCHEMA_KEYS


def test_no_backend_degrades_not_raises(tmp_path):
    log = tmp_path / "log.jsonl"
    r = sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR,
                                   log_path=log, clap=None)
    assert r["score"] is not None
    assert r["embed_cos"] is None and r["embed_score"] is None
    assert r["combined"] == r["score"]  # Fallback: Phase A allein
    assert r["backend_error"] and "clap" in r["backend_error"]
    # Log-Schema bleibt stabil (null statt fehlend)
    entry = json.loads(log.read_text().strip())
    assert set(entry["result"].keys()) == SCHEMA_KEYS


def test_strict_raises_on_missing_backend(tmp_path):
    with pytest.raises(RuntimeError, match="clap"):
        sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR,
                                   log_path=None, clap=None, strict=True)


def test_silence_verdict_fehler(tmp_path):
    log = tmp_path / "log.jsonl"
    r = sim_embed.score_pair_embed(np.zeros(SR), np.zeros(SR), sr=SR, log_path=log)
    assert r["verdict"] == "fehler" and r["score"] is None
    assert set(r.keys()) == SCHEMA_KEYS
    assert len(log.read_text().strip().splitlines()) == 1


def test_log_path_none_writes_nothing(tmp_path):
    r = sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR,
                                   log_path=None, clap=_FakeClap())
    assert r["embed_score"] == 100.0
    assert not (tmp_path / "log.jsonl").exists()


def test_llm_called_when_use_llm(tmp_path):
    r = sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR,
                                   log_path=None, clap=_FakeClap(),
                                   ollama=_FakeOllama(), use_llm=True)
    assert r["llm"]["score"] == 90 and r["llm"]["mode"] == "audio"
    entry_meta_keys = None
    log = tmp_path / "l.jsonl"
    sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR, log_path=log,
                               clap=_FakeClap(), ollama=_FakeOllama(), use_llm=True)
    entry = json.loads(log.read_text().strip())
    assert entry["meta"]["backends"]["ollama"] == "fake-omni:1"
    assert entry["meta"]["backends"]["llm"] is True


def test_judge_prompt_mit_pegeln(monkeypatch):
    seen = {}

    def fake_post(url, json=None, timeout=60):
        seen["content"] = json["messages"][0]["content"]
        return _resp(200, _chat_payload('{"score": 50, "summary": "s", "differences": []}'))

    monkeypatch.setattr(sim_embed.requests, "post", fake_post)
    b = sim_embed.OllamaBackend()
    b.judge(sine(440.0, 0.5), sine(440.0, 0.5), SR, peak_a=-6.0, peak_b=-40.0)
    assert "-6.0 dBFS" in seen["content"] and "-40.0 dBFS" in seen["content"]


def test_llm_level_penalty_deckelt_score(tmp_path):
    # B 30 dB leiser als A -> LLM-Score wird auf 30 gedeckelt
    loud = sine(440.0, 1.0, amp=0.5)          # ~-6 dBFS
    quiet = sine(440.0, 1.0, amp=0.5 / 1000)   # ~-66 dBFS
    r = sim_embed.score_pair_embed(loud, quiet, sr=SR, log_path=None,
                                   clap=_FakeClap(), ollama=_FakeOllama(), use_llm=True)
    assert r["llm"]["score"] == 30 and r["llm"]["level_penalty"] is True
    assert r["peak_dbfs"]["b"] < r["peak_dbfs"]["a"] - 24
    # bei aehnlichen Pegeln kein Deckel
    r2 = sim_embed.score_pair_embed(loud, sine(441.0, 1.0, amp=0.5), sr=SR,
                                    log_path=None, clap=_FakeClap(), ollama=_FakeOllama(),
                                    use_llm=True)
    assert r2["llm"]["score"] == 90 and "level_penalty" not in r2["llm"]


def test_extract_json_prosa_und_fences():
    # Code-Fence drumherum + Prosa danach mit unbalancierter Klammer -> echtes Objekt gewinnt
    txt = ('Prosa davor.\n```json\n'
           '{"score": 95, "summary": "ok {nested}", "differences": ["a", "b"]}\n```\n'
           'Danach noch Text mit {unbalancierter Klammer.')
    obj = sim_embed._extract_json(txt)
    assert obj == {"score": 95, "summary": "ok {nested}", "differences": ["a", "b"]}


def test_extract_json_kein_json():
    assert sim_embed._extract_json("gar kein objekt hier") is None
    assert sim_embed._extract_json('[1, 2, 3]') is None  # Array ist kein dict


# --- D1ProfileBackend (d1-omni noul-Profil als Erklaer-Schicht) ---

class _FakeD1:
    model = "fake-d1:2b"

    def available(self):
        return True

    def profile(self, x_a, x_b, sr):
        return {"model": self.model, "score": 63.5, "confidence": 0.7,
                "probs": {"same_pitch": 0.9, "octave_lower": 0.1, "brighter": 0.6,
                          "darker": 0.8, "noisier": 0.2, "punchier": 0.3,
                          "same_overall": 0.8},
                "flags": ["brighter", "darker"], "diff_count": 2,
                "same_overall": 80.0}


def test_score_pair_embed_profile_feld_und_log(tmp_path):
    log = tmp_path / "log.jsonl"
    r = sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR, log_path=log,
                                   clap=_FakeClap(), profile_backend=_FakeD1())
    assert r["profile"]["score"] == 63.5
    assert r["profile"]["flags"] == ["brighter", "darker"]
    assert r["profile"]["diff_count"] == 2
    entry = json.loads(log.read_text().strip())
    assert entry["result"]["profile"]["model"] == "fake-d1:2b"
    assert entry["meta"]["backends"]["d1_profile"] == "fake-d1:2b"


def test_score_pair_embed_profile_default_none():
    r = sim_embed.score_pair_embed(_load(PAAR[0]), _load(PAAR[1]), sr=SR,
                                   log_path=None, clap=_FakeClap())
    assert r["profile"] is None


def test_d1_profile_backend_parst_systemone(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        assert url.endswith("/v1/systemone")
        assert json["model"] == "d1-omni:2b"
        assert len(json["images"]) == 2
        qs = json["questions"]
        assert qs["similarity"]["type"] == "score" and len(qs["similarity"]["criteria"]) == 10
        assert qs["darker"]["type"] == "noul"
        return SimpleNamespace(status_code=200, json=lambda: {"answers": {
            "similarity": {"type": "score", "score": 5.7, "confidence": 0.7,
                           "probabilities": {str(i): 0.1 for i in range(10)}},
            "same_pitch": {"type": "noul", "noul": 0.9},
            "octave_lower": {"type": "noul", "noul": 0.6},
            "brighter": {"type": "noul", "noul": 0.2},
            "darker": {"type": "noul", "noul": 0.8},
            "noisier": {"type": "noul", "noul": 0.1},
            "punchier": {"type": "noul", "noul": 0.3},
            "same_overall": {"type": "noul", "noul": 0.77},
        }})
    monkeypatch.setattr(sim_embed.requests, "post", fake_post)
    b = sim_embed.D1ProfileBackend()
    p = b.profile(sine(440.0, 0.5), sine(660.0, 0.5), SR)
    assert p["score"] == pytest.approx(100 * 5.7 / 9, abs=0.05)
    assert p["flags"] == ["octave_lower", "darker"]  # p >= 0.5, nur DIFF-Fragen
    assert p["diff_count"] == 2
    assert p["probs"]["same_overall"] == pytest.approx(0.77)
    assert p["same_overall"] == pytest.approx(77.0)


def test_d1_profile_backend_http_fehler_wirft(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        return SimpleNamespace(status_code=500, text="boom")
    monkeypatch.setattr(sim_embed.requests, "post", fake_post)
    b = sim_embed.D1ProfileBackend()
    with pytest.raises(RuntimeError, match="systemone"):
        b.profile(sine(440.0, 0.5), sine(660.0, 0.5), SR)


# --- 2026-11-18: optischer Spektrogramm-Vergleich (render_spec_pair_png) ---

SEP = 2  # px Separator zwischen den Panels


def _pair_img(tmp_path, a, b, **kw):
    p = tmp_path / "pair.png"
    sim_embed.render_spec_pair_png(a, b, SR, p, **kw)
    with Image.open(p) as im:
        return im, np.asarray(im.convert("RGB")).copy()


def test_render_spec_pair_png_shape(tmp_path):
    a, b = sine(220.0, 1.0, amp=0.3), sine(221.0, 1.0, amp=0.3)
    im, arr = _pair_img(tmp_path, a, b)
    assert im.format == "PNG" and im.mode == "RGB"
    n_bands, n_frames = sim_embed.sim.features(a, SR)["log_spec"].shape
    assert im.size == (3 * n_frames + 2 * SEP, n_bands)  # Breite = 3 Panels + 2 Separatoren


def _panels(arr, n_frames):
    """arr: (n_bands, 3*n_frames + 2*SEP, 3) -> (A, B, Delta) als Spalten-Slices."""
    w = n_frames
    return arr[:, :w], arr[:, w + SEP:2 * w + SEP], arr[:, 2 * w + 2 * SEP:]


def test_render_spec_pair_png_delta_varies_and_common_scale(tmp_path):
    a = sine(220.0, 1.0, amp=0.3)
    b_diff = sine(221.0, 1.0, amp=0.3)   # andere Frequenz -> Delta variiert
    _, arr = _pair_img(tmp_path, a, b_diff)
    nf = sim_embed.sim.features(a, SR)["log_spec"].shape[1]
    _, _, delta = _panels(arr, nf)
    assert delta.std() > 1.0  # nicht konstant
    # gemeinsames lo/hi: leiseres B (gleiche Frequenz, halber Amp) -> B-Panel dunkler
    b_quiet = sine(220.0, 1.0, amp=0.15)
    _, arr2 = _pair_img(tmp_path, a, b_quiet)
    panel_a, panel_b, _ = _panels(arr2, nf)
    assert panel_a.mean() > panel_b.mean()


def test_render_spec_pair_png_gleiches_signal_delta_konstant(tmp_path):
    a = sine(330.0, 1.0, amp=0.3)
    _, arr = _pair_img(tmp_path, a, a.copy())
    nf = sim_embed.sim.features(a, SR)["log_spec"].shape[1]
    _, _, delta = _panels(arr, nf)
    assert delta.std() == 0.0  # identisch -> konstantes 0-Mapping


def test_render_spec_pair_png_pads_unterschiedliche_laengen(tmp_path):
    a, b = sine(220.0, 1.0, amp=0.3), sine(220.0, 1.3, amp=0.3)
    im, _ = _pair_img(tmp_path, a, b)  # darf nicht werfen
    n_bands, n_frames = sim_embed.sim.features(b, SR)["log_spec"].shape
    assert im.size == (3 * n_frames + 2 * SEP, n_bands)


def test_score_pair_embed_spec_png_writes_and_logs(tmp_path):
    log = tmp_path / "log.jsonl"
    sdir = tmp_path / "spec"
    r = sim_embed.score_pair_embed(sine(220.0), sine(221.0), sr=SR,
                                   meta={"blofeld": "A001", "note": 72, "wheel_pct": 0.0},
                                   log_path=log, clap=_FakeClap(), spec_png_dir=sdir)
    assert r["spec_png"] is not None and r["spec_png"].endswith("spec_A001_n72_w0.png")
    assert Path(r["spec_png"]).exists()
    entry = json.loads(log.read_text().strip())
    assert entry["result"]["spec_png"] == r["spec_png"]
    # ohne spec_png_dir: Feld None, keine Datei
    r2 = sim_embed.score_pair_embed(sine(220.0), sine(221.0), sr=SR, log_path=None,
                                    clap=_FakeClap())
    assert r2["spec_png"] is None
    assert not sdir.exists() or len(list(sdir.glob("*.png"))) == 1


def test_score_pair_embed_spec_png_rendert_normierte_signale(tmp_path):
    """Review-Focus: Delta auf pegel-normalisierten Signalen (nicht Roh-Gain)."""
    sdir = tmp_path / "spec"
    loud, quiet = sine(220.0, amp=0.3), sine(220.0, amp=0.03)  # 20 dB Unterschied
    r_norm = sim_embed.score_pair_embed(loud, quiet, sr=SR, log_path=None,
                                        clap=None, norm_pegel=True, spec_png_dir=sdir)
    nf = sim_embed.sim.features(loud, SR)["log_spec"].shape[1]
    arr = np.asarray(Image.open(r_norm["spec_png"]).convert("RGB"))
    d_norm = _panels(arr, nf)[2]
    r_raw = sim_embed.score_pair_embed(loud, quiet, sr=SR, log_path=None,
                                       clap=None, norm_pegel=False, spec_png_dir=sdir)
    arr2 = np.asarray(Image.open(r_raw["spec_png"]).convert("RGB"))
    d_raw = _panels(arr2, nf)[2]
    # nach Norm: identische Signale -> Delta = 0 -> mittelgrau (128,128,128)
    assert abs(d_norm[..., 0].mean() - 128) < 2 and abs(d_norm[..., 2].mean() - 128) < 2
    # roh: B 6 dB leiser -> Delta negativ -> blau (B-Kanal hoch, R niedrig)
    assert d_raw[..., 2].mean() - d_raw[..., 0].mean() > 20


def test_score_pair_embed_spec_png_degrade(monkeypatch, tmp_path):
    """Render-Fehler killt die Messung nicht: score ok, spec_png None, backend_error."""
    def boom(*a, **k):
        raise RuntimeError("kaputt")
    monkeypatch.setattr(sim_embed, "render_spec_pair_png", boom)
    r = sim_embed.score_pair_embed(sine(220.0), sine(221.0), sr=SR, log_path=None,
                                   clap=_FakeClap(), spec_png_dir=tmp_path / "spec")
    assert r["score"] is not None
    assert r["spec_png"] is None
    assert r["backend_error"] and "spec_png" in r["backend_error"]
    with pytest.raises(RuntimeError, match="spec_png"):
        sim_embed.score_pair_embed(sine(220.0), sine(221.0), sr=SR, log_path=None,
                                   clap=_FakeClap(), spec_png_dir=tmp_path / "spec",
                                   strict=True)


def test_spec_png_name_collision(tmp_path):
    sdir = tmp_path / "spec"
    meta = {"blofeld": "A001", "note": 72, "wheel_pct": 0.0}
    r1 = sim_embed.score_pair_embed(sine(220.0), sine(221.0), sr=SR, log_path=None,
                                    clap=None, spec_png_dir=sdir, meta=meta)
    r2 = sim_embed.score_pair_embed(sine(220.0), sine(222.0), sr=SR, log_path=None,
                                    clap=None, spec_png_dir=sdir, meta=meta)
    assert r1["spec_png"] != r2["spec_png"]
    assert Path(r1["spec_png"]).exists() and Path(r2["spec_png"]).exists()
