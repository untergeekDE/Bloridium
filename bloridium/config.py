"""User-editable YAML configuration (`bloridium.yaml`) over built-in defaults.

Search order for the config file:
  1. explicit path (function argument / `--config` CLI flag)
  2. $BLORIDIUM_CONFIG environment variable
  3. ./bloridium.yaml (project directory / current working directory)

Without a config file everything falls back to DEFAULTS (the previously
hardcoded values in midi.py / audio.py), so behavior is unchanged.

Merge rule: user YAML > discovered values > built-in defaults. A user-edited
value is never silently overwritten.
"""

from __future__ import annotations

import copy
import os
from pathlib import Path

import yaml

CONFIG_FILENAME = "bloridium.yaml"
ENV_VAR = "BLORIDIUM_CONFIG"

# Built-in defaults (previously hardcoded in midi.py DEFAULT_PORTS and
# audio.py DEVICE/SAMPLERATE/CHANNELS). MIDI channels are 0-based.
DEFAULTS = {
    "midi": {
        "blofeld": {
            "out_port": "Launchpad Pro MK3 LPProMK3 DIN",
            "in_port": "Launchpad Pro MK3 LPProMK3 DIN",
            "channel": 4,  # 0-based MIDI channel 5 (Blofeld Global Channel, Single Mode)
        },
        "iridium": {
            "out_port": "Launchpad Pro MK3 LPProMK3 DIN",
            "in_port": "Launchpad Pro MK3 LPProMK3 DIN",
            "channel": 5,  # 0-based MIDI channel 6 = Part 1 (Parts 1-4 = ch 6-9)
        },
        "fallback_out_ports": {
            "blofeld": ["Launchpad Pro MK3 LPProMK3 DIN", "Blofeld"],
            "iridium": [
                "Launchpad Pro MK3 LPProMK3 DIN",
                "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
                "Iridium Keyboard (MIDI 2.0) Synth",
            ],
        },
    },
    "audio": {
        "device": "Scarlett 18i8 USB",  # ffmpeg/AVFoundation (or ALSA) device name
        "samplerate": 48000,
        "raw_channels": 20,             # channel count of the raw device stream
        "channels": {                   # 0-based input numbers per synth
            "blofeld": [2, 3],          # inputs 3/4
            "iridium": [4, 5],          # inputs 5/6
        },
    },
}

_HEADER = """\
# bloridium.yaml -- Bloridium configuration (edit freely).
# Precedence: --config flag > $BLORIDIUM_CONFIG > ./bloridium.yaml > built-in defaults.
# `bloridium discover --write` only fills keys you left empty.
# MIDI channels are 0-based (Blofeld Global Channel 5 -> 4; Iridium Part 1 = ch 6 -> 5).
# Audio channels are 0-based input numbers on the audio interface.
"""


def merge(base: dict, override: dict) -> dict:
    """Deep-merge `override` over `base` (override wins); neither input is mutated."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def find_config_path(explicit=None) -> Path | None:
    """Resolve the config file location: explicit arg > $BLORIDIUM_CONFIG > ./bloridium.yaml."""
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get(ENV_VAR)
    if env:
        return Path(env)
    cwd_file = Path.cwd() / CONFIG_FILENAME
    return cwd_file if cwd_file.exists() else None


def load_raw_config(path) -> dict | None:
    """Read the YAML file as-is (no defaults merged in); None if missing/empty.

    Raises ValueError (naming the file) on malformed YAML or a non-mapping root.
    Used by discover: only *user-written* keys may override discovered values.
    """
    path = Path(path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path.name}: {exc}") from exc
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(f"invalid config in {path.name}: top level must be a mapping")
    return data


def load_config(path=None) -> dict:
    """Load the YAML config deep-merged over DEFAULTS.

    `path=None` resolves via find_config_path(); a missing file means defaults.
    Raises ValueError (naming the file) on malformed YAML or a non-mapping root.
    """
    if path is None:
        path = find_config_path(None)
    if path is None:
        return copy.deepcopy(DEFAULTS)
    data = load_raw_config(path)
    if data is None:
        return copy.deepcopy(DEFAULTS)
    return merge(DEFAULTS, data)


def save_config(path, cfg: dict) -> None:
    """Write `cfg` as YAML with a guiding header comment."""
    path = Path(path)
    body = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=False, default_flow_style=False)
    path.write_text(_HEADER + body, encoding="utf-8")


def midi_ports(cfg: dict) -> dict:
    """Config in the shape midi.connect() expects: {synth: {"out","in","channel"}}."""
    ports = {}
    for name in ("blofeld", "iridium"):
        entry = cfg["midi"][name]
        ports[name] = {
            "out": entry.get("out_port"),
            "in": entry.get("in_port"),
            "channel": entry.get("channel", 0),
        }
    return ports


def fallback_out_ports(cfg: dict) -> dict:
    """{synth: [port name candidates in priority order]} for port matching."""
    return cfg["midi"].get("fallback_out_ports", {})


def audio_settings(cfg: dict) -> dict:
    """Audio section: device name, samplerate, raw channel count, per-synth inputs."""
    a = cfg["audio"]
    return {
        "device": a["device"],
        "samplerate": a.get("samplerate", 48000),
        "raw_channels": a.get("raw_channels", 20),
        "channels": a.get("channels", {}),
    }
