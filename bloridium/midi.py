"""MIDI connections to the synthesizers (Waldorf Blofeld & Iridium).

Primary: both synths directly via USB on the Mac (see CLAUDE.md).
- Blofeld: CoreMIDI port "Blofeld" (bidirectional, identity reply 3E/13)
- Iridium: CoreMIDI endpoint "Iridium Keyboard (MIDI 2.0) MIDI 2.0"
  (MIDI 1.0 bytes are delivered by CoreMIDI as UMP)

Fallback (if USB does not work): Novation Launchpad Pro MK3 as MIDI interface
via DIN - Iridium MIDI Out -> Launchpad MIDI In, Launchpad MIDI Out2 -> Blofeld MIDI In
  -> CoreMIDI port "Launchpad Pro MK3 LPProMK3 DIN"
"""

from __future__ import annotations

import time

import mido

from . import config as _config

# Default port configuration per synth (names see `list_ports()`).
# The values live in config.DEFAULTS (single source of truth); the user-editable
# bloridium.yaml overrides them at runtime - see ports_from_config().
# MIDI channels (0-based) are empirically determined and confirmed:
#   Blofeld: USB port "Blofeld" (bidirectional, identity reply Waldorf 3E/13,
#            firmware 1.24), Global Channel = channel 5 (1-based), SINGLE MODE active.
#            ATTENTION: mode NOT detectable via channel scan (multi parts may sit on
#            any channel); change on the device: Shift+Sound/Multi.
#   Iridium: USB endpoint "MIDI 2.0", parts 1-4 on channels 6-9 (1-based).
#            The endpoint "Synth" currently receives nothing.
# Current cabling (2026-11-08): USB unplugged on both (ground loop -> USB noise on
# In 5/6); both synths on the Launchpad Pro 3 DIN out, separated by channel
# (Blofeld ch5, Iridium ch6-9), the Iridium on its own power supply.
DEFAULT_PORTS = _config.midi_ports(_config.DEFAULTS)

# Fallback candidates if the default ports do not work
FALLBACK_OUT_PORTS = _config.fallback_out_ports(_config.DEFAULTS)


def list_ports() -> dict:
    """List all visible CoreMIDI ports."""
    return {"in": list(mido.get_input_names()), "out": list(mido.get_output_names())}


def match_port(available: list, wanted: str) -> str:
    """Exact match, else case-insensitive substring match."""
    if wanted in available:
        return wanted
    wl = wanted.lower()
    for p in available:
        if wl in p.lower():
            return p
    raise RuntimeError(f"MIDI port not found: {wanted!r} - available: {available}")


class Synth:
    """A MIDI connection to a synthesizer (out + optional in)."""

    def __init__(self, name: str, out_port: str, in_port: str | None = None, channel: int = 0):
        self.name = name
        self.channel = channel          # 0-based default MIDI channel of the synth
        self.out_port_name = match_port(list(mido.get_output_names()), out_port)
        self.out = mido.open_output(self.out_port_name)
        self.inp = None
        self.in_port_name = None
        if in_port:
            try:
                self.in_port_name = match_port(list(mido.get_input_names()), in_port)
                self.inp = mido.open_input(self.in_port_name)
            except RuntimeError:
                self.inp = None

    # ---- send -----------------------------------------------------------

    def send(self, msg: mido.Message) -> None:
        self.out.send(msg)

    def note_on(self, note: int = 60, velocity: int = 100, channel: int | None = None) -> None:
        self.send(mido.Message("note_on", note=note, velocity=velocity, channel=self.channel if channel is None else channel))

    def note_off(self, note: int = 60, velocity: int = 0, channel: int | None = None) -> None:
        self.send(mido.Message("note_off", note=note, velocity=velocity, channel=self.channel if channel is None else channel))

    def all_notes_off(self, channel: int | None = None) -> None:
        self.control_change(123, 0, channel)

    def program_change(self, program: int, channel: int | None = None) -> None:
        self.send(mido.Message("program_change", program=program, channel=self.channel if channel is None else channel))

    def control_change(self, control: int, value: int, channel: int | None = None) -> None:
        self.send(mido.Message("control_change", control=control, value=value, channel=self.channel if channel is None else channel))

    def pitchwheel(self, pitch: int = 0, channel: int | None = None) -> None:
        self.send(mido.Message("pitchwheel", pitch=pitch, channel=self.channel if channel is None else channel))

    def send_sysex(self, data) -> None:
        """Send SysEx; `data` without F0/F7, e.g. [0x7E, 0x7F, 0x06, 0x01]."""
        self.send(mido.Message("sysex", data=[int(b) & 0x7F for b in data]))

    def device_inquiry(self) -> None:
        """Universal Device Inquiry: F0 7E 7F 06 01 F7."""
        self.send_sysex([0x7E, 0x7F, 0x06, 0x01])

    # ---- receive --------------------------------------------------------

    def receive(self, timeout: float = 1.0) -> list:
        """Collects all MIDI messages arriving within `timeout` s."""
        msgs: list = []
        if not self.inp:
            time.sleep(timeout)
            return msgs
        deadline = time.time() + timeout
        while time.time() < deadline:
            m = self.inp.poll()
            if m is not None:
                msgs.append(m)
            else:
                time.sleep(0.005)
        return msgs

    def close(self) -> None:
        try:
            self.out.close()
        except Exception:
            pass
        if self.inp:
            try:
                self.inp.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def ports_from_config(config_path=None) -> dict:
    """Effective port table {synth: {"out", "in", "channel"}}: YAML config over DEFAULT_PORTS."""
    return _config.midi_ports(_config.load_config(config_path))


def fallback_out_ports(config_path=None) -> dict:
    """Effective fallback port candidates: YAML config over FALLBACK_OUT_PORTS."""
    return _config.fallback_out_ports(_config.load_config(config_path))


def connect(name: str, ports: dict | None = None, config_path=None) -> Synth:
    """Connect to a synth ('blofeld' or 'iridium'); ports default to the YAML config."""
    ports = ports or ports_from_config(config_path)
    cfg = ports[name]
    return Synth(name, cfg["out"], cfg.get("in"), cfg.get("channel", 0))


def connect_all(ports: dict | None = None, config_path=None) -> dict:
    """Connect to both synthesizers."""
    ports = ports or ports_from_config(config_path)
    return {name: connect(name, ports) for name in ports}


def open_input(port_name: str):
    """Open only MIDI in (read-only captures, e.g. `explore`).

    -> (matched port name, mido.MidiIn). Raises RuntimeError if the port is missing.
    """
    name = match_port(list(mido.get_input_names()), port_name)
    return name, mido.open_input(name)
