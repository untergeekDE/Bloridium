"""Tests for bloridium.config: user-editable YAML config over built-in defaults."""

import os
from pathlib import Path

import pytest

from bloridium import config


def test_load_config_missing_file_returns_defaults(tmp_path):
    cfg = config.load_config(tmp_path / "does-not-exist.yaml")
    assert cfg["midi"]["blofeld"]["channel"] == 4          # 0-based ch 5
    assert cfg["midi"]["iridium"]["channel"] == 5           # 0-based ch 6 = Part 1
    assert "Scarlett" in cfg["audio"]["device"]
    assert cfg["audio"]["samplerate"] == 48000
    assert cfg["audio"]["channels"] == {"blofeld": [2, 3], "iridium": [4, 5]}


def test_load_config_merges_user_yaml_over_defaults(tmp_path):
    p = tmp_path / "bloridium.yaml"
    p.write_text(
        "audio:\n  samplerate: 44100\n  device: My Interface\n"
        "midi:\n  blofeld:\n    channel: 0\n"
    )
    cfg = config.load_config(p)
    # user values win ...
    assert cfg["audio"]["samplerate"] == 44100
    assert cfg["audio"]["device"] == "My Interface"
    assert cfg["midi"]["blofeld"]["channel"] == 0
    # ... but untouched keys keep the defaults (deep merge)
    assert cfg["audio"]["channels"]["blofeld"] == [2, 3]
    assert cfg["midi"]["iridium"]["channel"] == 5
    assert cfg["midi"]["blofeld"]["out_port"]  # default port name present


def test_find_config_path_precedence(tmp_path, monkeypatch):
    explicit = tmp_path / "explicit.yaml"
    env = tmp_path / "env.yaml"
    cwd = tmp_path / config.CONFIG_FILENAME  # the cwd lookup uses the fixed filename
    monkeypatch.setenv("BLORIDIUM_CONFIG", str(env))
    monkeypatch.chdir(tmp_path)
    cwd.write_text("audio: {}\n")
    # explicit beats env beats cwd
    assert config.find_config_path(explicit) == explicit
    assert config.find_config_path(None) == env
    monkeypatch.delenv("BLORIDIUM_CONFIG")
    # resolve(): macOS reports /var/... where pytest's tmp_path is /private/var/...
    assert config.find_config_path(None).resolve() == cwd.resolve()
    monkeypatch.chdir("/")
    assert config.find_config_path(None) is None or Path(config.find_config_path(None)).name == config.CONFIG_FILENAME


def test_save_config_roundtrip(tmp_path):
    p = tmp_path / "bloridium.yaml"
    cfg = config.load_config(tmp_path / "missing.yaml")
    cfg["audio"]["device"] = "Custom Audio Box"
    config.save_config(p, cfg)
    loaded = config.load_config(p)
    assert loaded["audio"]["device"] == "Custom Audio Box"
    assert loaded["midi"] == cfg["midi"]
    # file is real YAML with a guiding header comment
    text = p.read_text()
    assert text.startswith("#")
    assert "bloridium.yaml" in text


def test_load_config_invalid_yaml_raises_with_filename(tmp_path):
    p = tmp_path / "broken.yaml"
    p.write_text("midi: [unclosed\n")
    with pytest.raises(ValueError, match="broken.yaml"):
        config.load_config(p)


def test_midi_ports_shape_matches_connect(tmp_path):
    cfg = config.load_config(tmp_path / "missing.yaml")
    ports = config.midi_ports(cfg)
    assert set(ports) == {"blofeld", "iridium"}
    for name, entry in ports.items():
        assert set(entry) == {"out", "in", "channel"}
        assert isinstance(entry["channel"], int)
    fallbacks = config.fallback_out_ports(cfg)
    assert "Blofeld" in fallbacks["blofeld"]
    assert any("Iridium" in p for p in fallbacks["iridium"])


def test_audio_settings_accessor(tmp_path):
    cfg = config.load_config(tmp_path / "missing.yaml")
    s = config.audio_settings(cfg)
    assert s["device"] == cfg["audio"]["device"]
    assert s["samplerate"] == 48000
    assert s["raw_channels"] == 20
    assert s["channels"]["iridium"] == [4, 5]


def test_defaults_not_mutated_by_load(tmp_path):
    p = tmp_path / "bloridium.yaml"
    p.write_text("audio:\n  samplerate: 44100\n")
    cfg = config.load_config(p)
    cfg["audio"]["channels"]["blofeld"] = [0, 1]
    fresh = config.load_config(tmp_path / "missing.yaml")
    assert fresh["audio"]["channels"]["blofeld"] == [2, 3]
    assert fresh["audio"]["samplerate"] == 48000
