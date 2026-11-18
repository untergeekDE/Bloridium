"""specdiff.py – Interpretation des Spektral-Diffs (TDD: Task 1 DSP, Task 2 Vision, Task 3 CLI)."""

import json
from pathlib import Path

import numpy as np
import pytest

from bloridium import sim, specdiff

SR = 48000


def _sig(dur=1.0, freq=220.0, seed=1):
    t = np.arange(int(SR * dur)) / SR
    rng = np.random.default_rng(seed)
    return 0.5 * np.sin(2 * np.pi * freq * t) + 0.02 * rng.standard_normal(t.size)


def _bands(n=48):
    return np.geomspace(40.0, 12000.0, n + 1)


def _delta_matrix(n_bands=48, n_frames=40, fill=0.0):
    d = np.full((n_bands, n_frames), fill, dtype=np.float64)
    return d, _bands(n_bands), np.ones((n_bands, n_frames), dtype=bool)


# --- Task 1: DSP-Kern ---

def test_diff_matrix_pad_and_active():
    a = _sig(1.0, 220.0, seed=1)
    b = _sig(1.5, 330.0, seed=2)          # laenger -> Pad-Spalten bei A
    dm = specdiff.diff_matrix(a, b, SR)
    sa = sim.features(a, sr=SR)["log_spec"]
    sb = sim.features(b, sr=SR)["log_spec"]
    n = max(sa.shape[1], sb.shape[1])
    assert dm["delta"].shape == (sa.shape[0], n)
    na = sa.shape[1]
    assert np.allclose(dm["delta"][:, :na], sb[:, :na] - sa)
    assert np.all(dm["delta"][:, na:] == 0.0)          # Pad-Spalten grau/0
    assert not dm["active"][:, na:].any()               # ... und nicht aktiv
    assert dm["band_edges"].shape == (sa.shape[0] + 1,)


def test_classify_constant_heavy_even_even():
    d, be, act = _delta_matrix(fill=8.0)
    feat = specdiff.dsp_features(d, be, act)
    lab = specdiff.classify_dsp(feat)
    assert feat["severity_db"] == pytest.approx(8.0)
    assert lab["severity"] == "heavy"
    assert lab["spread"] == "even"
    assert lab["temporal"] == "even"
    assert specdiff.specdiff_score(feat["severity_db"]) == pytest.approx(20.0)


def test_classify_single_punctual_single():
    d, be, act = _delta_matrix()
    d[:, 20] = 12.0                       # eine Frame-Spalte, alle Baender
    feat = specdiff.dsp_features(d, be, act)
    lab = specdiff.classify_dsp(feat)
    assert lab["spread"] == "punctual"
    assert lab["temporal"] == "single"
    assert lab["severity"] == "light"     # 12 dB in einer von 40 Spalten -> mean < 2 dB


def test_classify_periodical():
    d, be, act = _delta_matrix()
    t = np.arange(40)
    d[:, :] = 6.0 * np.sin(2 * np.pi * t / 8.0)[None, :]
    feat = specdiff.dsp_features(d, be, act)
    lab = specdiff.classify_dsp(feat)
    assert lab["temporal"] == "periodical"
    assert lab["spread"] == "even"


def test_classify_increasing():
    d, be, act = _delta_matrix()
    ramp = np.linspace(0.0, 10.0, 40)
    d[:, :] = ramp[None, :]
    feat = specdiff.dsp_features(d, be, act)
    lab = specdiff.classify_dsp(feat)
    assert lab["temporal"] == "increasing"


def test_classify_bands_high_only():
    d, be, act = _delta_matrix()
    centers = np.sqrt(be[:-1] * be[1:])
    high = centers > 2000.0
    d[high, :] = 8.0
    feat = specdiff.dsp_features(d, be, act)
    lab = specdiff.classify_dsp(feat)
    assert lab["bands"] == ["high"]
    assert lab["temporal"] == "even"


def test_specdiff_score_bounds():
    assert specdiff.specdiff_score(0.0) == 100.0
    assert specdiff.specdiff_score(20.0) == 0.0
    assert specdiff.specdiff_score(50.0) == 0.0     # clip
    assert specdiff.specdiff_score(3.0) == pytest.approx(70.0)


def test_diff_matrix_too_short_raises():
    with pytest.raises(ValueError):
        specdiff.diff_matrix(np.zeros(100), np.zeros(100), SR)


# --- Task 2: Vision-Backends + interpret_pair (HTTP monkeypatcht) ---

import base64 as _b64


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def _fake_systemone_answers():
    return {"answers": {
        "severity": {"type": "choice", "choice": "medium",
                     "probabilities": {"light": 0.1, "medium": 0.7, "heavy": 0.2},
                     "confidence": 0.4},
        "spread": {"type": "choice", "choice": "even",
                   "probabilities": {"even": 0.8, "punctual": 0.2}, "confidence": 0.5},
        "temporal": {"type": "choice", "choice": "periodical",
                     "probabilities": {k: 0.1 for k in specdiff.TEMPORALS},
                     "confidence": 0.3},
        "low": {"type": "noul", "noul": 0.1},
        "mid": {"type": "noul", "noul": 0.2},
        "high": {"type": "noul", "noul": 0.9},
    }}


def test_systemone_backend_parses_answers(tmp_path, monkeypatch):
    import requests
    png = tmp_path / "p.png"
    png.write_bytes(b"\x89PNG-fake")
    calls = {}

    def fake_post(url, json=None, timeout=None):
        calls["url"] = url
        calls["payload"] = json
        return _FakeResp({"answers": _fake_systemone_answers()["answers"]})

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get",
                        lambda url, timeout=None: _FakeResp({"models": [{"name": "d1-omni:2b"}]}))
    b = specdiff.SystemOneBackend()
    assert b.available()
    out = b.classify_png(png, {"severity_db": 3.0})
    assert calls["url"].endswith("/v1/systemone")
    assert "state" in calls["payload"] and "images" in calls["payload"]
    assert calls["payload"]["images"][0] == _b64.b64encode(b"\x89PNG-fake").decode()
    assert out["labels"] == {"severity": "medium", "spread": "even",
                             "temporal": "periodical", "bands": ["high"]}
    assert out["probs"]["severity"]["medium"] == pytest.approx(0.7)
    assert out["confidence"] > 0.0


def test_interpret_pair_vision_fallback_to_dsp_on_http_error(tmp_path, monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get",
                        lambda url, timeout=None: _FakeResp({"models": [{"name": "d1-omni:2b"}]}))

    def boom(url, json=None, timeout=None):
        raise requests.ConnectionError("ollama down")

    monkeypatch.setattr(requests, "post", boom)
    a = _sig(1.0, 220.0, seed=1)
    b = _sig(1.0, 220.0, seed=1) * 1.5     # nur Pegel -> nach norm? hier roh: delta ~ +3.5 dB
    r = specdiff.interpret_pair(a, b, SR, backend=specdiff.SystemOneBackend())
    assert r["source"] == "dsp"
    assert r["vision"] is None
    assert set(r["labels"]) >= {"severity", "spread", "temporal", "bands"}
    assert 0.0 <= r["score"] <= 100.0


def test_interpret_pair_offline_no_backend():
    a = _sig(1.0, 220.0, seed=1)
    b = _sig(1.0, 331.0, seed=2)
    r = specdiff.interpret_pair(a, b, SR, backend=None)
    assert r["source"] == "dsp"
    assert r["vision"] is None and r["probs"] is None
    assert r["labels"]["severity"] in specdiff.SEVERITIES
    assert r["spec_png"] is None


def test_interpret_pair_vision_labels_win(tmp_path, monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get",
                        lambda url, timeout=None: _FakeResp({"models": [{"name": "d1-omni:2b"}]}))
    monkeypatch.setattr(requests, "post",
                        lambda url, json=None, timeout=None: _FakeResp(_fake_systemone_answers()))
    png_out = tmp_path / "pair.png"
    a = _sig(1.0, 220.0, seed=1)
    b = _sig(1.0, 220.0, seed=2)
    r = specdiff.interpret_pair(a, b, SR, backend=specdiff.SystemOneBackend(),
                                png_path=png_out)
    assert r["source"] == "vision"
    assert r["labels"]["temporal"] == "periodical"     # aus Vision, nicht DSP
    assert r["labels"]["bands"] == ["high"]
    assert png_out.exists() and r["spec_png"] == str(png_out)


def test_ollama_chat_backend_json_extract(monkeypatch):
    import urllib.request
    raw = ('Here you go:\n```json\n{"severity": "heavy", "spread": "punctual", '
           '"temporal": "multiple", "bands": ["low", "high"], "summary": "x"}\n```')

    class _R:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"message": {"content": raw}}).encode()

    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["payload"] = json.loads(req.data.decode())
        return _R()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    b = specdiff.OllamaChatBackend(model="gemma4:12b-it-qat")
    out = b.classify_png(Path("/nonexistent.png"), {"severity_db": 9.0}) \
        if False else b._parse_chat(raw)   # direkt parser testen
    assert out["labels"]["severity"] == "heavy"
    assert out["labels"]["bands"] == ["low", "high"]
    # payload check via echtem aufruf mit bild:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.png"
        p.write_bytes(b"\x89PNG")
        out2 = b.classify_png(p, {"severity_db": 9.0})
        assert seen["payload"]["think"] is False
        assert seen["payload"]["options"]["temperature"] == 0.0
        assert out2["labels"]["temporal"] == "multiple"


def test_ollama_chat_backend_invalid_labels_raise():
    b = specdiff.OllamaChatBackend()
    with pytest.raises(ValueError):
        b._parse_chat('{"severity": "extreme", "spread": "even", "temporal": "even", "bands": []}')


# --- Task 3: CLI bloridium specdiff ---

def _write_wav_pair(rec, loc, ts, note, w=None, seed_a=1, seed_b=2):
    from bloridium import sim_embed
    wtag = f"_w{int(w)}" if w is not None else ""
    sim_embed.write_wav(_sig(1.0, 220.0, seed=seed_a), SR,
                        rec / f"ab_{loc}_{ts}_n{note}{wtag}_blo.wav")
    sim_embed.write_wav(_sig(1.0, 330.0, seed=seed_b), SR,
                        rec / f"ab_{loc}_{ts}_n{note}{wtag}_irr.wav")


def test_cli_specdiff_single_wav(tmp_path, capsys):
    from bloridium import cli
    rec = tmp_path / "rec"
    rec.mkdir()
    _write_wav_pair(rec, "A001", "20261118_000000", 72)
    png = tmp_path / "pair.png"
    rc = cli.main(["specdiff", "--wav",
                   str(rec / "ab_A001_20261118_000000_n72_blo.wav"),
                   str(rec / "ab_A001_20261118_000000_n72_irr.wav"),
                   "--no-vision", "--png", str(png)])
    assert rc == 0
    assert png.exists()
    out = capsys.readouterr().out
    assert '"severity"' in out and '"score"' in out and '"source": "dsp"' in out


def test_cli_specdiff_batch_write(tmp_path, capsys):
    from bloridium import cli
    rec = tmp_path / "rec"
    rec.mkdir()
    _write_wav_pair(rec, "A001", "20261118_000000", 72, w=0)
    _write_wav_pair(rec, "A002", "20261118_000100", 72, w=0)
    log = tmp_path / "sim_log.jsonl"
    rows = [
        {"ts": "20261118_000000", "meta": {"mode": "checkpoint", "blofeld": "A001",
                                           "note": 72, "wheel_pct": 0.0},
         "result": {"score": 90.0}},
        {"ts": "20261118_000100", "meta": {"mode": "checkpoint", "blofeld": "A002",
                                           "note": 72, "wheel_pct": 0.0},
         "result": {"score": 80.0}},
        {"ts": "20261118_000200", "meta": {"mode": "live", "blofeld": "A043", "note": 72},
         "result": {"score": None, "verdict": "fehler"}},   # keine WAVs -> ueberspringen
    ]
    log.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rc = cli.main(["specdiff", "--log", str(log), "--recordings", str(rec),
                   "--no-vision", "--write"])
    assert rc == 0
    lines = [json.loads(l) for l in log.read_text().splitlines()]
    assert "specdiff" in lines[0]["result"] and "specdiff_score" in lines[0]["result"]
    assert lines[0]["result"]["score"] == 90.0          # Rest der Zeile unveraendert
    assert "specdiff" in lines[1]["result"]
    assert "specdiff" not in lines[2]["result"]
    out = capsys.readouterr().out
    assert "A001" in out and "A002" in out


def test_cli_specdiff_batch_no_wavs_exit2(tmp_path, capsys):
    from bloridium import cli
    rec = tmp_path / "rec"
    rec.mkdir()
    log = tmp_path / "l.jsonl"
    log.write_text(json.dumps({"ts": "x", "meta": {"blofeld": "A001", "note": 72},
                               "result": {}}) + "\n")
    rc = cli.main(["specdiff", "--log", str(log), "--recordings", str(rec), "--no-vision"])
    assert rc == 2
    assert capsys.readouterr().err
