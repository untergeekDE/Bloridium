"""sim_compare.py – Phase-B-Flags --embed/--llm/--strict (TDD Task 7, Backends gemockt)."""

import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def sc(repo, monkeypatch):
    sys.path.insert(0, str(repo / "scripts"))
    import sim_compare
    from bloridium import sim_embed
    monkeypatch.setattr(sim_embed, "REPO", repo)
    return sim_compare, sim_embed


def _npy_pair(tmp_path):
    sr = 48000
    t = np.arange(int(1.0 * sr)) / sr
    a = 0.4 * np.sin(2 * np.pi * 440 * t)
    b = 0.4 * np.sin(2 * np.pi * 442 * t)
    pa, pb = tmp_path / "a.npy", tmp_path / "b.npy"
    np.save(pa, a)
    np.save(pb, b)
    return str(pa), str(pb)


class _FakeClap:
    def __init__(self, path):
        self.model_path = path

    def embed(self, x, sr):
        v = np.zeros(512, dtype=np.float32)
        v[0] = 1.0
        return v


class _FakeOllama:
    def __init__(self, *a, **kw):
        self.model = "fake:1"

    def available(self):
        return True

    def judge(self, x_a, x_b, sr, prompt=None):
        return {"score": 77, "summary": "s", "differences": ["d"], "mode": "audio",
                "model": self.model}


def test_npy_embed_flag_adds_embed_score(sc, tmp_path, monkeypatch):
    sim_compare, sim_embed = sc
    md = tmp_path / "models"
    md.mkdir()
    (md / sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    monkeypatch.setattr(sim_embed, "ClapBackend", _FakeClap)
    pa, pb = _npy_pair(tmp_path)
    log = tmp_path / "log.jsonl"
    rc = sim_compare.main(["--npy", pa, pb, "--embed", "--models-dir", str(md),
                           "--log", str(log)])
    assert rc == 0
    entry = json.loads(log.read_text().strip())
    r = entry["result"]
    assert r["embed_score"] == 100.0 and r["combined"] is not None
    assert entry["meta"]["backends"]["clap"] == sim_embed.CLAP_GGUF_NAME


def test_embed_missing_model_degrades_exit_0(sc, tmp_path, capsys):
    sim_compare, sim_embed = sc
    md = tmp_path / "models"
    md.mkdir()  # kein GGUF drin
    pa, pb = _npy_pair(tmp_path)
    log = tmp_path / "log.jsonl"
    rc = sim_compare.main(["--npy", pa, pb, "--embed", "--models-dir", str(md),
                           "--log", str(log)])
    assert rc == 0  # degrade, kein Hard-Fail
    assert "WARNUNG" in capsys.readouterr().err
    r = json.loads(log.read_text().strip())["result"]
    assert r["embed_score"] is None and r["combined"] == r["score"]
    assert "clap" in r["backend_error"]


def test_strict_missing_model_exit_3(sc, tmp_path):
    sim_compare, sim_embed = sc
    md = tmp_path / "models"
    md.mkdir()
    pa, pb = _npy_pair(tmp_path)
    rc = sim_compare.main(["--npy", pa, pb, "--embed", "--strict",
                           "--models-dir", str(md), "--log", str(tmp_path / "l.jsonl")])
    assert rc == 3


def test_llm_flag_calls_ollama(sc, tmp_path, monkeypatch):
    sim_compare, sim_embed = sc
    md = tmp_path / "models"
    md.mkdir()
    (md / sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    monkeypatch.setattr(sim_embed, "ClapBackend", _FakeClap)
    monkeypatch.setattr(sim_embed, "OllamaBackend", _FakeOllama)
    pa, pb = _npy_pair(tmp_path)
    log = tmp_path / "log.jsonl"
    rc = sim_compare.main(["--npy", pa, pb, "--embed", "--llm", "--models-dir", str(md),
                           "--log", str(log)])
    assert rc == 0
    r = json.loads(log.read_text().strip())["result"]
    assert r["llm"]["score"] == 77 and r["llm"]["mode"] == "audio"


def test_no_embed_flag_means_no_backend(sc, tmp_path, monkeypatch):
    sim_compare, sim_embed = sc
    called = []

    class Boom:
        def __init__(self, path):
            called.append(path)

    monkeypatch.setattr(sim_embed, "ClapBackend", Boom)
    md = tmp_path / "models"
    md.mkdir()
    (md / sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    pa, pb = _npy_pair(tmp_path)
    rc = sim_compare.main(["--npy", pa, pb, "--models-dir", str(md),
                           "--log", str(tmp_path / "l.jsonl")])
    assert rc == 0 and called == []  # ohne --embed wird kein Backend gebaut
