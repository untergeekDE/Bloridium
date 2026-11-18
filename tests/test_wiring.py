"""Wiring tests: bloridium.yaml is honored by midi.connect / audio.record / the CLI."""

import json
import subprocess

import pytest


def test_connect_uses_yaml_config(tmp_path, monkeypatch):
    import mido
    from bloridium import midi

    p = tmp_path / "bloridium.yaml"
    p.write_text("midi:\n  blofeld:\n    out_port: MyUsbPort\n    channel: 9\n")

    monkeypatch.setattr(mido, "get_output_names", lambda: ["MyUsbPort"])
    monkeypatch.setattr(mido, "get_input_names", lambda: [])

    class FakeOut:
        def send(self, m):
            pass

        def close(self):
            pass

    monkeypatch.setattr(mido, "open_output", lambda name: FakeOut())
    synth = midi.connect("blofeld", config_path=p)
    assert synth.out_port_name == "MyUsbPort"
    assert synth.channel == 9
    synth.close()


def test_connect_without_yaml_uses_builtin_defaults(tmp_path, monkeypatch):
    import mido
    from bloridium import midi

    monkeypatch.setattr(mido, "get_output_names", lambda: ["Launchpad Pro MK3 LPProMK3 DIN"])
    monkeypatch.setattr(mido, "get_input_names", lambda: [])

    class FakeOut:
        def send(self, m):
            pass

        def close(self):
            pass

    monkeypatch.setattr(mido, "open_output", lambda name: FakeOut())
    synth = midi.connect("blofeld", config_path=tmp_path / "missing.yaml")
    assert synth.out_port_name == "Launchpad Pro MK3 LPProMK3 DIN"
    assert synth.channel == 4  # built-in default (0-based ch 5)
    synth.close()


def test_audio_record_uses_config_device_and_samplerate(tmp_path, monkeypatch):
    from bloridium import audio

    p = tmp_path / "bloridium.yaml"
    p.write_text("audio:\n  device: FakeDevice\n  samplerate: 44100\n")

    captured = {}

    def fake_run(cmd, capture_output=True):
        captured["cmd"] = cmd
        # 200 float32 samples = 2 channels x 100 samples
        return subprocess.CompletedProcess(cmd, 0, stdout=b"\x00" * 800, stderr=b"")

    monkeypatch.setattr(audio.subprocess, "run", fake_run)
    data = audio.record(duration=0.1, channels=(0, 1), config_path=p)
    assert data.shape == (2, 100)
    assert ":FakeDevice" in captured["cmd"]
    assert "44100" in captured["cmd"]


def test_audio_settings_defaults_without_yaml(tmp_path):
    from bloridium import audio
    s = audio.settings(tmp_path / "missing.yaml")
    assert "Scarlett" in s["device"]
    assert s["samplerate"] == 48000
    assert s["channels"] == {"blofeld": [2, 3], "iridium": [4, 5]}


def _patch_discovery(monkeypatch):
    from bloridium import discover
    monkeypatch.setattr(discover, "discover_midi",
                        lambda: {"in": ["Blofeld"], "out": ["Blofeld", "Iridium Keyboard (MIDI 2.0) MIDI 2.0"]})
    monkeypatch.setattr(discover, "discover_audio",
                        lambda api=None, runner=None: [{"index": 0, "name": "Scarlett 18i8 USB", "api": "avfoundation"}])


def test_cli_discover_json(tmp_path, monkeypatch, capsys):
    from bloridium import cli
    _patch_discovery(monkeypatch)
    cfg_path = tmp_path / "bloridium.yaml"
    rc = cli.main(["--config", str(cfg_path), "--json", "discover"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["midi_ports"]["out"] == ["Blofeld", "Iridium Keyboard (MIDI 2.0) MIDI 2.0"]
    assert data["audio_devices"][0]["name"] == "Scarlett 18i8 USB"
    assert data["config"]["midi"]["blofeld"]["out_port"] == "Blofeld"
    assert "Iridium" in data["config"]["midi"]["iridium"]["out_port"]
    assert data["config"]["audio"]["device"] == "Scarlett 18i8 USB"
    assert not cfg_path.exists()  # no --write -> nothing saved


def test_cli_discover_write_saves_yaml(tmp_path, monkeypatch, capsys):
    from bloridium import cli, config
    _patch_discovery(monkeypatch)
    cfg_path = tmp_path / "bloridium.yaml"
    rc = cli.main(["--config", str(cfg_path), "discover", "--write"])
    assert rc == 0
    assert cfg_path.exists()
    loaded = config.load_config(cfg_path)
    assert loaded["midi"]["blofeld"]["out_port"] == "Blofeld"
    assert loaded["audio"]["device"] == "Scarlett 18i8 USB"
    # channels are not discoverable -> defaults preserved
    assert loaded["midi"]["blofeld"]["channel"] == 4
    assert loaded["audio"]["channels"]["iridium"] == [4, 5]


def test_cli_discover_json_flag_after_subcommand(tmp_path, monkeypatch, capsys):
    """`bloridium discover --json` must work like `bloridium --json discover`."""
    from bloridium import cli
    _patch_discovery(monkeypatch)
    # --config points at a not-yet-existing file so the repo's own bloridium.yaml
    # does not count as a user edit here
    rc = cli.main(["--config", str(tmp_path / "bloridium.yaml"), "discover", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["config"]["midi"]["blofeld"]["out_port"] == "Blofeld"


def test_cli_discover_write_preserves_user_edits(tmp_path, monkeypatch, capsys):
    from bloridium import cli, config
    _patch_discovery(monkeypatch)
    cfg_path = tmp_path / "bloridium.yaml"
    cfg_path.write_text("audio:\n  device: MyHandSetDevice\n")
    rc = cli.main(["--config", str(cfg_path), "discover", "--write"])
    assert rc == 0
    loaded = config.load_config(cfg_path)
    assert loaded["audio"]["device"] == "MyHandSetDevice"  # user edit wins
    assert loaded["midi"]["blofeld"]["out_port"] == "Blofeld"  # rest filled from discovery
