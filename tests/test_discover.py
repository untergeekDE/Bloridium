"""Tests for bloridium.discover: MIDI/audio interface discovery + config merge."""

import subprocess
import sys
from pathlib import Path

import pytest

from bloridium import config, discover


AVF_SAMPLE = """\
[AVFoundation indev @ 0x1] AVFoundation video devices:
[AVFoundation indev @ 0x1] [0] FaceTime HD Camera
[AVFoundation indev @ 0x1] AVFoundation audio devices:
[AVFoundation indev @ 0x1] [0] Scarlett 18i8 USB
[AVFoundation indev @ 0x1] [1] MacBook Air Microphone
[AVFoundation indev @ 0x1] [2] SoundFlower (2ch)
"""

ALSA_SAMPLE = """\
**** List of ALSA capture devices ****
card 0: USB [Scarlett 18i8 USB], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: Microphone [MacBook Air Microphone], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""


def test_parse_avfoundation_devices_audio_section_only():
    devs = discover.parse_avfoundation_devices(AVF_SAMPLE)
    assert devs == [
        {"index": 0, "name": "Scarlett 18i8 USB", "api": "avfoundation"},
        {"index": 1, "name": "MacBook Air Microphone", "api": "avfoundation"},
        {"index": 2, "name": "SoundFlower (2ch)", "api": "avfoundation"},
    ]


def test_parse_alsa_devices():
    devs = discover.parse_alsa_devices(ALSA_SAMPLE)
    assert devs == [
        {"index": 0, "name": "Scarlett 18i8 USB", "api": "alsa"},
        {"index": 1, "name": "MacBook Air Microphone", "api": "alsa"},
    ]


def test_discover_audio_dispatches_on_api():
    def fake_runner(cmd, capture_output=True, text=None):
        assert "-list_devices" in cmd
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=AVF_SAMPLE)

    devs = discover.discover_audio(api="avfoundation", runner=fake_runner)
    assert devs[0]["name"] == "Scarlett 18i8 USB"

    def fake_runner_alsa(cmd, capture_output=True, text=None):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=ALSA_SAMPLE)

    devs = discover.discover_audio(api="alsa", runner=fake_runner_alsa)
    assert devs[0]["api"] == "alsa"


def test_discover_audio_default_api_matches_platform(monkeypatch):
    seen = {}

    def fake_runner(cmd, capture_output=True, text=None):
        seen["format"] = cmd[cmd.index("-f") + 1]
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=AVF_SAMPLE if seen["format"] == "avfoundation" else ALSA_SAMPLE)

    monkeypatch.setattr(sys, "platform", "darwin")
    assert discover.discover_audio(runner=fake_runner)[0]["api"] == "avfoundation"
    monkeypatch.setattr(sys, "platform", "linux")
    assert discover.discover_audio(runner=fake_runner)[0]["api"] == "alsa"


def test_discover_audio_ffmpeg_missing_returns_empty(monkeypatch):
    def boom(cmd, capture_output=True, text=None):
        raise FileNotFoundError("ffmpeg")

    assert discover.discover_audio(runner=boom) == []


def test_discover_midi_lists_ports(monkeypatch):
    import mido
    monkeypatch.setattr(mido, "get_input_names", lambda: ["Blofeld", "Launchpad Pro MK3 LPProMK3 DIN"])
    monkeypatch.setattr(mido, "get_output_names", lambda: ["Blofeld", "Iridium Keyboard (MIDI 2.0) MIDI 2.0", "Launchpad Pro MK3 LPProMK3 DIN"])
    ports = discover.discover_midi()
    assert ports["in"] == ["Blofeld", "Launchpad Pro MK3 LPProMK3 DIN"]
    assert any("Iridium" in p for p in ports["out"])


def test_parse_identity_reply_waldorf_blofeld():
    import mido
    msg = mido.Message("sysex", data=[0x7E, 0x7F, 0x06, 0x02, 0x00, 0x20, 0x3E, 0x00, 0x13, 0x00, 0x18, 0x00, 0x00])
    ident = discover.parse_identity_reply(msg)
    assert ident["manufacturer"] == "0x3E"   # Waldorf
    assert ident["model"] == "0x13"          # Blofeld


def test_parse_identity_reply_ignores_other_messages():
    import mido
    assert discover.parse_identity_reply(mido.Message("note_on", note=60)) is None
    assert discover.parse_identity_reply(mido.Message("sysex", data=[0x7E, 0x7F, 0x06, 0x01])) is None


def test_probe_port_returns_identity(monkeypatch):
    import mido

    class FakeIn:
        def __init__(self, msgs):
            self.msgs = list(msgs)

        def poll(self):
            return self.msgs.pop(0) if self.msgs else None

        def close(self):
            pass

    class FakeOut:
        def __init__(self):
            self.sent = []

        def send(self, m):
            self.sent.append(m)

        def close(self):
            pass

    reply = mido.Message("sysex", data=[0x7E, 0x7F, 0x06, 0x02, 0x00, 0x20, 0x3E, 0x00, 0x13, 0x01, 0x24, 0x00, 0x00])
    monkeypatch.setattr(mido, "open_output", lambda name: FakeOut())
    monkeypatch.setattr(mido, "open_input", lambda name: FakeIn([reply]))
    ident = discover.probe_port("Blofeld", timeout=0.05)
    assert ident["manufacturer"] == "0x3E"
    assert ident["model"] == "0x13"


def test_build_config_prefers_discovered_over_defaults():
    discovered = {
        "midi_out": ["Blofeld", "Iridium Keyboard (MIDI 2.0) MIDI 2.0"],
        "midi_in": ["Blofeld", "Iridium Keyboard (MIDI 2.0) MIDI 2.0"],
        "audio_devices": [{"index": 0, "name": "Scarlett 18i8 USB", "api": "avfoundation"}],
    }
    cfg = discover.build_config(discovered, existing=None)
    assert cfg["midi"]["blofeld"]["out_port"] == "Blofeld"
    assert "Iridium" in cfg["midi"]["iridium"]["out_port"]
    assert cfg["audio"]["device"] == "Scarlett 18i8 USB"
    # channels are not discoverable -> defaults survive
    assert cfg["midi"]["blofeld"]["channel"] == 4
    assert cfg["audio"]["channels"] == {"blofeld": [2, 3], "iridium": [4, 5]}


def test_build_config_preserves_user_edits():
    discovered = {
        "midi_out": ["Blofeld", "Some Other Interface"],
        "midi_in": ["Blofeld"],
        "audio_devices": [{"index": 0, "name": "Scarlett 18i8 USB", "api": "avfoundation"}],
    }
    existing = {
        "midi": {"blofeld": {"out_port": "My DIN Interface", "channel": 9}},
        "audio": {"device": "Built-in Output", "samplerate": 44100},
    }
    cfg = discover.build_config(discovered, existing=existing)
    # user values win over discovered ...
    assert cfg["midi"]["blofeld"]["out_port"] == "My DIN Interface"
    assert cfg["midi"]["blofeld"]["channel"] == 9
    assert cfg["audio"]["device"] == "Built-in Output"
    assert cfg["audio"]["samplerate"] == 44100
    # ... but keys the user left alone still get discovered/default values
    assert "Iridium" in cfg["midi"]["iridium"]["out_port"] or cfg["midi"]["iridium"]["out_port"]
    assert cfg["audio"]["channels"]["blofeld"] == [2, 3]


def test_build_config_picks_scarlett_when_present():
    discovered = {
        "midi_out": [], "midi_in": [],
        "audio_devices": [
            {"index": 0, "name": "MacBook Air Microphone", "api": "avfoundation"},
            {"index": 1, "name": "Scarlett 18i8 USB", "api": "avfoundation"},
        ],
    }
    cfg = discover.build_config(discovered, existing=None)
    assert cfg["audio"]["device"] == "Scarlett 18i8 USB"


def test_discover_write_creates_yaml(tmp_path, monkeypatch):
    import mido
    monkeypatch.setattr(mido, "get_input_names", lambda: ["Blofeld"])
    monkeypatch.setattr(mido, "get_output_names", lambda: ["Blofeld", "Iridium Keyboard (MIDI 2.0) MIDI 2.0"])

    def fake_runner(cmd, capture_output=True, text=None):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=AVF_SAMPLE)

    path = tmp_path / "bloridium.yaml"
    result = discover.discover(write=True, path=path, runner=fake_runner)
    assert path.exists()
    loaded = config.load_config(path)
    assert loaded["midi"]["blofeld"]["out_port"] == "Blofeld"
    assert loaded["audio"]["device"] == "Scarlett 18i8 USB"
    assert result["config_path"] == path


def test_discover_without_write_does_not_create_file(tmp_path, monkeypatch):
    import mido
    monkeypatch.setattr(mido, "get_input_names", lambda: [])
    monkeypatch.setattr(mido, "get_output_names", lambda: [])

    def fake_runner(cmd, capture_output=True, text=None):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr=AVF_SAMPLE)

    path = tmp_path / "bloridium.yaml"
    discover.discover(write=False, path=path, runner=fake_runner)
    assert not path.exists()
