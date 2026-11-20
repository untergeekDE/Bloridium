"""audio.py — ffmpeg-Aufnahme darf nicht ewig hängen (Timeout, 2026-11-20)."""

import subprocess
import numpy as np
import pytest

from bloridium import audio


def test_record_passes_timeout_and_returns(monkeypatch):
    calls = []

    class FakeProc:
        returncode = 0
        stderr = b""
        stdout = np.zeros(48000 * 20, dtype=np.float32).tobytes()  # 20 raw channels

    def fake_run(cmd, capture_output=False, timeout=None, **kw):
        calls.append(timeout)
        return FakeProc()

    monkeypatch.setattr(audio.subprocess, "run", fake_run)
    monkeypatch.setattr(audio, "settings", lambda *a, **k: {
        "device": "dev", "samplerate": 48000, "raw_channels": 20})
    x = audio.record(duration=1.0, channels=None)
    assert x.shape[0] == 20
    assert calls and calls[0] == 21.0          # duration + 20 s Puffer


def test_record_timeout_retries_then_raises(monkeypatch):
    calls = []

    def fake_run(cmd, capture_output=False, timeout=None, **kw):
        calls.append(timeout)
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(audio.subprocess, "run", fake_run)
    monkeypatch.setattr(audio, "settings", lambda *a, **k: {
        "device": "dev", "samplerate": 48000, "raw_channels": 20})
    monkeypatch.setattr(audio.time, "sleep", lambda *a: None)
    with pytest.raises(RuntimeError, match="timeout"):
        audio.record(duration=1.6, channels=(2, 3))
    assert len(calls) == 4                       # 4 Versuche, dann Fehler


def test_record_wav_timeout_raises(monkeypatch, tmp_path):
    def fake_run(cmd, check=False, capture_output=False, timeout=None, **kw):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(audio.subprocess, "run", fake_run)
    monkeypatch.setattr(audio, "settings", lambda *a, **k: {
        "device": "dev", "samplerate": 48000, "raw_channels": 20})
    with pytest.raises(RuntimeError, match="timeout"):
        audio.record_wav(tmp_path / "x.wav", duration=1.0, channels=(2, 3))
