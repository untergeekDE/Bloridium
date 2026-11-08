"""MIDI-Verbindungen zu den Synthesizern (Waldorf Blofeld & Iridium).

Primär: beide Synths direkt per USB am Mac (siehe CLAUDE.md).
- Blofeld: CoreMIDI-Port "Blofeld" (bidirektional, Identity Reply 3E/13)
- Iridium: CoreMIDI-Endpunkt "Iridium Keyboard (MIDI 2.0) MIDI 2.0"
  (MIDI-1.0-Bytes werden von CoreMIDI als UMP zugestellt)

Fallback (falls USB nicht greift): Novation Launchpad Pro MK3 als MIDI-Interface
per DIN – Iridium MIDI Out -> Launchpad MIDI In, Launchpad MIDI Out2 -> Blofeld MIDI In
  -> CoreMIDI-Port "Launchpad Pro MK3 LPProMK3 DIN"
"""

from __future__ import annotations

import time

import mido

# Standard-Port-Konfiguration pro Synth (Namen siehe `list_ports()`)
# Primär beide Synths per USB; Launchpad DIN nur als Fallback.
# MIDI-Kanaele (0-basiert) sind empirisch ermittelt und bestaetigt:
#   Blofeld: USB-Port "Blofeld" (bidirektional, Identity Reply Waldorf 3E/13,
#            Firmware 1.24), Global Channel = Kanal 5 (1-basiert), SINGLE MODE aktiv.
#            ACHTUNG: Modus per Kanal-Scan NICHT erkennbar (Multi-Parts duerfen auf
#            beliebigen Kanaelen liegen); am Geraet aendern: Shift+Sound/Multi.
#   Iridium: USB-Endpunkt "MIDI 2.0", Parts 1-4 auf Kanal 6-9 (1-basiert).
#            Der Endpunkt "Synth" empfaengt derzeit nichts.
DEFAULT_PORTS = {
    "iridium": {
        "out": "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
        "in": "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
        "channel": 5,   # MIDI-Kanal 6 (Part 1); Parts 1-4 = Kanal 6-9 (Index 5-8)
    },
    "blofeld": {
        "out": "Blofeld",                  # Blofeld direkt per USB
        "in": "Blofeld",
        "channel": 4,   # MIDI-Kanal 5 (Global Channel)
    },
}

# Fallback-Kandidaten, falls die Standard-Ports nicht greifen
FALLBACK_OUT_PORTS = {
    "iridium": [
        "Iridium Keyboard (MIDI 2.0) MIDI 2.0",
        "Iridium Keyboard (MIDI 2.0) Synth",
    ],
    "blofeld": [
        "Blofeld",                          # USB
        "Launchpad Pro MK3 LPProMK3 DIN",   # Fallback: Launchpad Out2 (DIN) -> Blofeld In
    ],
}


def list_ports() -> dict:
    """Alle sichtbaren CoreMIDI-Ports auflisten."""
    return {"in": list(mido.get_input_names()), "out": list(mido.get_output_names())}


def match_port(available: list, wanted: str) -> str:
    """Exakter Treffer, sonst case-insensitive Teilstring-Match."""
    if wanted in available:
        return wanted
    wl = wanted.lower()
    for p in available:
        if wl in p.lower():
            return p
    raise RuntimeError(f"MIDI-Port nicht gefunden: {wanted!r} – verfügbar: {available}")


class Synth:
    """Eine MIDI-Verbindung zu einem Synthesizer (Out + optional In)."""

    def __init__(self, name: str, out_port: str, in_port: str | None = None, channel: int = 0):
        self.name = name
        self.channel = channel          # 0-basierter Standard-MIDI-Kanal des Synths
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

    # ---- Senden ------------------------------------------------------

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
        """SysEx senden; `data` ohne F0/F7, z.B. [0x7E, 0x7F, 0x06, 0x01]."""
        self.send(mido.Message("sysex", data=[int(b) & 0x7F for b in data]))

    def device_inquiry(self) -> None:
        """Universal Device Inquiry: F0 7E 7F 06 01 F7."""
        self.send_sysex([0x7E, 0x7F, 0x06, 0x01])

    # ---- Empfangen ---------------------------------------------------

    def receive(self, timeout: float = 1.0) -> list:
        """Sammelt alle MIDI-Nachrichten, die innerhalb von `timeout` s ankommen."""
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


def connect(name: str, ports: dict | None = None) -> Synth:
    """Verbindung zu einem Synth herstellen ('blofeld' oder 'iridium')."""
    ports = ports or DEFAULT_PORTS
    cfg = ports[name]
    return Synth(name, cfg["out"], cfg.get("in"), cfg.get("channel", 0))


def connect_all(ports: dict | None = None) -> dict:
    """Verbindungen zu beiden Synthesizern herstellen."""
    ports = ports or DEFAULT_PORTS
    return {name: connect(name, ports) for name in ports}
