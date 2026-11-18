"""Hardware discovery: scan MIDI ports and audio devices, merge into bloridium.yaml.

`discover()` lists the visible MIDI ports (mido/CoreMIDI; optional identity
probe via Universal Device Inquiry) and the audio capture devices (ffmpeg
`-list_devices`: AVFoundation on macOS, ALSA on Linux), then merges them into
the config. Precedence: user-edited YAML > discovered > built-in defaults —
a user value is never overwritten.

The CLI entry point is `bloridium discover [--write] [--probe] [--json]`.
"""

from __future__ import annotations

import copy
import re
import subprocess
import sys
import time
from pathlib import Path

import mido

from . import config, midi

# Universal Device Inquiry request (SysEx data without F0/F7): F0 7E 7F 06 01 F7
_DEVICE_INQUIRY = [0x7E, 0x7F, 0x06, 0x01]


# ---------------------------------------------------------------- MIDI -----

def discover_midi() -> dict:
    """All visible MIDI ports: {"in": [...], "out": [...]}."""
    return midi.list_ports()


def parse_identity_reply(msg) -> dict | None:
    """Parse a Universal Identity Reply (SysEx) into {manufacturer, model, device}.

    Layout (data bytes without F0/F7): 7E <device> 06 02 <manufacturer 3 bytes>
    <model 2 bytes> <version 4 bytes>. manufacturer/model are shown via their
    last byte (0x3E = Waldorf, model 0x13 = Blofeld). Non-reply messages -> None.
    """
    if getattr(msg, "type", None) != "sysex":
        return None
    d = list(msg.data)
    if len(d) >= 9 and d[0] == 0x7E and d[2] == 0x06 and d[3] == 0x02:
        return {
            "device": d[1],
            "manufacturer": f"0x{d[6]:02X}",
            "model": f"0x{d[8]:02X}",
        }
    return None


def probe_port(out_port: str, timeout: float = 0.5) -> dict | None:
    """Send a Device Inquiry on `out_port` and return the identity reply, if any.

    Never raises: an unreachable port or a device that stays silent -> None.
    """
    out = inp = None
    try:
        out = mido.open_output(out_port)
        try:
            inp = mido.open_input(out_port)
        except Exception:
            inp = None
        out.send(mido.Message("sysex", data=_DEVICE_INQUIRY))
        if inp is None:
            time.sleep(timeout)
            return None
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = inp.poll()
            if msg is not None:
                ident = parse_identity_reply(msg)
                if ident is not None:
                    return ident
            else:
                time.sleep(0.005)
        return None
    except Exception:
        return None
    finally:
        for port in (out, inp):
            if port is not None:
                try:
                    port.close()
                except Exception:
                    pass


# --------------------------------------------------------------- audio -----

def parse_avfoundation_devices(text: str) -> list[dict]:
    """Parse `ffmpeg -f avfoundation -list_devices true -i ""` output (stderr).

    Only the "AVFoundation audio devices:" section is used (video devices are
    skipped). Returns [{"index": int, "name": str, "api": "avfoundation"}].
    """
    devices = []
    audio_section = False
    for line in text.splitlines():
        if "audio devices:" in line:
            audio_section = True
            continue
        if "video devices:" in line:
            audio_section = False
            continue
        if not audio_section:
            continue
        m = re.search(r"\[(\d+)\]\s+(.+?)\s*$", line)
        if m:
            devices.append({"index": int(m.group(1)), "name": m.group(2), "api": "avfoundation"})
    return devices


def parse_alsa_devices(text: str) -> list[dict]:
    """Parse `ffmpeg -f alsa -list_devices true -i ""` output (stderr).

    Lines look like `card 0: USB [Scarlett 18i8 USB], device 0: ...`.
    Returns [{"index": int, "name": str, "api": "alsa"}].
    """
    devices = []
    for line in text.splitlines():
        m = re.match(r"^card (\d+): .+ \[(.+?)\],", line)
        if m:
            devices.append({"index": int(m.group(1)), "name": m.group(2), "api": "alsa"})
    return devices


def discover_audio(api: str | None = None, runner=subprocess.run) -> list[dict]:
    """List audio capture devices via ffmpeg.

    `api`: "avfoundation" (macOS) or "alsa" (Linux); None = detect from
    sys.platform. `runner` is injectable for tests. ffmpeg missing -> [].
    """
    if api is None:
        if sys.platform == "darwin":
            api = "avfoundation"
        elif sys.platform.startswith("linux"):
            api = "alsa"
        else:
            return []
    cmd = ["ffmpeg", "-hide_banner", "-f", api, "-list_devices", "true", "-i", ""]
    try:
        proc = runner(cmd, capture_output=True)
    except FileNotFoundError:
        return []
    stderr = proc.stderr or ""
    if isinstance(stderr, bytes):
        stderr = stderr.decode(errors="replace")
    if api == "avfoundation":
        return parse_avfoundation_devices(stderr)
    return parse_alsa_devices(stderr)


# --------------------------------------------------------------- merge -----

def _pick(names: list[str], keyword: str) -> str | None:
    """First port name containing `keyword` (case-insensitive), else None."""
    for name in names:
        if keyword in name.lower():
            return name
    return None


def build_config(discovered: dict, existing: dict | None = None) -> dict:
    """Merge discovered hardware into a config dict.

    Precedence: user-edited `existing` YAML > `discovered` > built-in defaults.
    `discovered` keys: midi_out, midi_in (port name lists), audio_devices
    (list of {"name": ...}), identities (optional probe results).
    """
    cfg = copy.deepcopy(config.DEFAULTS)

    midi_out = discovered.get("midi_out", [])
    midi_in = discovered.get("midi_in", [])
    blofeld_out = _pick(midi_out, "blofeld")
    iridium_out = _pick(midi_out, "iridium")
    if blofeld_out:
        cfg["midi"]["blofeld"]["out_port"] = blofeld_out
        cfg["midi"]["fallback_out_ports"]["blofeld"] = [blofeld_out] + [
            p for p in cfg["midi"]["fallback_out_ports"]["blofeld"] if p != blofeld_out
        ]
    if iridium_out:
        cfg["midi"]["iridium"]["out_port"] = iridium_out
        cfg["midi"]["fallback_out_ports"]["iridium"] = [iridium_out] + [
            p for p in cfg["midi"]["fallback_out_ports"]["iridium"] if p != iridium_out
        ]
    blofeld_in = _pick(midi_in, "blofeld")
    iridium_in = _pick(midi_in, "iridium")
    if blofeld_in:
        cfg["midi"]["blofeld"]["in_port"] = blofeld_in
    if iridium_in:
        cfg["midi"]["iridium"]["in_port"] = iridium_in

    devices = discovered.get("audio_devices", [])
    if devices:
        # prefer a known audio interface over built-in microphones
        name = next(
            (d["name"] for d in devices if "scarlett" in d["name"].lower()),
            devices[0]["name"],
        )
        cfg["audio"]["device"] = name

    if existing:
        cfg = config.merge(cfg, existing)  # user edits win
    return cfg


def discover(write: bool = False, path=None, probe: bool = False, runner=subprocess.run) -> dict:
    """Scan MIDI + audio interfaces and merge them into the config.

    Returns {"midi": {"in","out"}, "audio_devices": [...], "identities": {...},
             "config": merged dict, "config_path": Path|None}.
    With `write=True` the merged config is saved to `path` (or the standard
    config location); without `write` nothing is written to disk.
    """
    ports = discover_midi()
    audio_devices = discover_audio(runner=runner)
    identities: dict[str, dict] = {}
    if probe:
        for port in ports["out"]:
            ident = probe_port(port)
            if ident is not None:
                identities[port] = ident

    # Raw user YAML only (NOT merged over defaults): precedence must be
    # user-written keys > discovered > built-in defaults.
    existing = None
    if path is not None and Path(path).exists():
        existing = config.load_raw_config(path)
    elif path is None:
        found = config.find_config_path(None)
        if found is not None and found.exists():
            existing = config.load_raw_config(found)

    merged = build_config(
        {
            "midi_out": ports["out"],
            "midi_in": ports["in"],
            "audio_devices": audio_devices,
            "identities": identities,
        },
        existing=existing,
    )

    result = {
        "midi": ports,
        "audio_devices": audio_devices,
        "identities": identities,
        "config": merged,
        "config_path": None,
    }
    if write:
        target = Path(path) if path is not None else (
            config.find_config_path(None) or Path.cwd() / config.CONFIG_FILENAME
        )
        config.save_config(target, merged)
        result["config_path"] = target
    return result
