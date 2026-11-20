"""rescore_v2.py - vorhandene ab_*-Paare offline mit Score v2 + Embed/d1 re-scoren (Task 1)."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import rescore_v2 as rv
from bloridium import sim_embed

SR = 48000


def _sine(freq=440.0, dur=0.3, sr=SR, amp=0.5):
    t = np.arange(int(dur * sr)) / sr
    return amp * np.sin(2 * np.pi * freq * t)


def test_discover_pairs_npy_and_wav(tmp_path):
    names = [
        "ab_A001_20261114_154306_blofeld.npy", "ab_A001_20261114_154306_iridium.npy",
        "ab_A043_20261114_174637_n72_blo.wav", "ab_A043_20261114_174637_n72_irr.wav",
        "ab_A008_20261115_140050_n72_w100_blo.wav", "ab_A008_20261115_140050_n72_w100_irr.wav",
        "ab_A010_20261114_160856_blofeld.npy",          # unvollstaendig -> ignorieren
        "report.json", "ab_A001_20261114_170201_report.json",
    ]
    for n in names:
        (tmp_path / n).write_bytes(b"x")
    pairs = rv.discover_pairs(tmp_path)
    assert len(pairs) == 3
    by_loc = {p["loc"]: p for p in pairs}
    assert by_loc["A001"]["ext"] == "npy" and by_loc["A001"]["note"] is None
    assert by_loc["A043"]["ext"] == "wav" and by_loc["A043"]["note"] == 72
    assert by_loc["A008"]["note"] == 72 and by_loc["A008"]["extra"] == "w100"
    for p in pairs:
        assert Path(p["a"]).name.endswith(("_blofeld.npy", "_blo.wav"))
        assert Path(p["b"]).name.endswith(("_iridium.npy", "_irr.wav"))


def test_load_mono_npy_and_wav(tmp_path):
    x = _sine()
    pn = tmp_path / "a.npy"
    np.save(pn, x)
    pw = tmp_path / "a.wav"
    sim_embed.write_wav(x, SR, pw)
    xn = rv.load_mono(pn)
    xw = rv.load_mono(pw)
    assert xn.ndim == 1 and xw.ndim == 1
    assert len(xn) == len(xw) == len(x)
    assert np.allclose(xn, x, atol=1e-3) and np.allclose(xw, x, atol=1e-3)
    # Stereo-npy -> mono-Mittel
    ps = tmp_path / "s.npy"
    np.save(ps, np.stack([x, x], axis=0))
    assert np.allclose(rv.load_mono(ps), x, atol=1e-9)


def test_main_scores_pairs_into_log(tmp_path, monkeypatch, capsys):
    rec = tmp_path / "rec"
    rec.mkdir()
    x = _sine()
    for side in ("blofeld", "iridium"):
        np.save(rec / f"ab_A001_20261114_154306_{side}.npy", x)
    log = tmp_path / "sim_log_v2.jsonl"
    calls = []

    def fake_score_pair(x_blo, x_irr, sr=SR, meta=None, log_path=None, **kw):
        calls.append({"meta": meta, "log_path": str(log_path), "kw": sorted(kw)})
        entry = {"meta": meta, "result": {"score": 91.5, "verdict": "close",
                                          "score_version": 2, "embed_score": 55.0}}
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry["result"]

    monkeypatch.setattr(rv.sim_embed, "score_pair_embed", fake_score_pair)
    monkeypatch.setattr(rv.sim_embed, "build_backends", lambda *a, **k: (None, None))
    monkeypatch.setattr(rv.sim_embed, "build_profile_backend", lambda *a, **k: None)
    rc = rv.main(["--rec-dir", str(rec), "--log", str(log), "--no-llm", "--no-d1"])
    assert rc == 0
    assert len(calls) == 1
    assert calls[0]["meta"]["blofeld"] == "A001" and calls[0]["meta"]["mode"] == "npy-v2"
    assert "norm_pegel" in calls[0]["kw"]
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert rows[0]["result"]["score_version"] == 2 and rows[0]["meta"]["blofeld"] == "A001"
