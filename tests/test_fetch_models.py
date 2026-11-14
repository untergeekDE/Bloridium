"""fetch_models.py – Modelle laden (TDD Task 6, subprocess/hf gemockt)."""

import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def fm(repo, monkeypatch):
    sys.path.insert(0, str(repo / "scripts"))
    import fetch_models
    monkeypatch.setattr(fetch_models, "_run", lambda cmd: 0)
    return fetch_models


def test_skips_existing_gguf(fm, tmp_path, monkeypatch, capsys):
    (tmp_path / fm.sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    called = []

    def fake_dl(models_dir):
        called.append(models_dir)
        raise AssertionError("darf nicht aufgerufen werden")

    monkeypatch.setattr(fm, "_hf_download", fake_dl)
    assert fm.main(["--models-dir", str(tmp_path), "--skip-ollama"]) == 0
    assert called == []
    assert "vorhanden" in capsys.readouterr().out


def test_downloads_gguf_and_pulls_ollama(fm, tmp_path, monkeypatch):
    runs = []
    monkeypatch.setattr(fm, "_run", lambda cmd: runs.append(cmd) or 0)
    monkeypatch.setattr(fm, "_hf_download",
                        lambda md: (md / fm.sim_embed.CLAP_GGUF_NAME))
    assert fm.main(["--models-dir", str(tmp_path), "--ollama-model", "lfm3-omni:2b"]) == 0
    assert runs == [["ollama", "pull", "lfm3-omni:2b"]]


def test_failure_exit_1(fm, tmp_path, monkeypatch):
    def boom(md):
        raise RuntimeError("netz weg")
    monkeypatch.setattr(fm, "_hf_download", boom)
    assert fm.main(["--models-dir", str(tmp_path), "--skip-ollama"]) == 1


def test_ollama_failure_exit_1(fm, tmp_path, monkeypatch):
    (tmp_path / fm.sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    monkeypatch.setattr(fm, "_run", lambda cmd: 1)
    assert fm.main(["--models-dir", str(tmp_path)]) == 1
