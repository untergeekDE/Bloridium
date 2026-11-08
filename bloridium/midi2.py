"""MIDI 2.0 / UMP direkt über CoreMIDI (ctypes) – für Geräte im MIDI-2.0-Modus.

python-rtmidi/mido senden nur MIDI-1.0-Bytestreams; an einem MIDI-2.0-Endpunkt
(macOS: "... MIDI 2.0") müssen UMP-Pakete (32/64/96/128 Bit) gesendet werden.
"""

from __future__ import annotations

import ctypes
from ctypes import (POINTER, Structure, c_char_p, c_int32, c_long, c_size_t,
                    c_uint8, c_uint16, c_uint32, c_uint64, c_void_p)
from pathlib import Path

CORE_MIDI = ctypes.CDLL("/System/Library/Frameworks/CoreMIDI.framework/CoreMIDI")
CORE_FOUNDATION = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")

kCFStringEncodingUTF8 = 0x08000100
kMIDIPropertyName = "name"


class MIDIPacket(Structure):
    _fields_ = [
        ("timeStamp", c_uint64),
        ("length", c_uint16),
        ("data", c_uint8 * 256),
    ]


class MIDIPacketList(Structure):
    _fields_ = [
        ("numPackets", c_uint32),
        ("packet", MIDIPacket * 1),
    ]


def _cfstring(s: str) -> c_void_p:
    CORE_FOUNDATION.CFStringCreateWithCString.restype = c_void_p
    CORE_FOUNDATION.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
    return CORE_FOUNDATION.CFStringCreateWithCString(None, s.encode("utf-8"), kCFStringEncodingUTF8)


# Signaturen
CORE_MIDI.MIDIClientCreate.restype = c_int32
CORE_MIDI.MIDIClientCreate.argtypes = [c_void_p, c_void_p, c_void_p, POINTER(c_void_p)]
CORE_MIDI.MIDIOutputPortCreate.restype = c_int32
CORE_MIDI.MIDIOutputPortCreate.argtypes = [c_void_p, c_void_p, POINTER(c_void_p)]
CORE_MIDI.MIDIGetNumberOfDestinations.restype = c_long
CORE_MIDI.MIDIGetDestination.restype = c_void_p
CORE_MIDI.MIDIGetDestination.argtypes = [c_long]
CORE_MIDI.MIDIObjectGetStringProperty.restype = c_int32
CORE_MIDI.MIDIObjectGetStringProperty.argtypes = [c_void_p, c_void_p, POINTER(c_void_p)]
CORE_MIDI.MIDIPacketListInit.argtypes = [POINTER(MIDIPacketList)]
CORE_MIDI.MIDIPacketListAdd.restype = POINTER(MIDIPacket)
CORE_MIDI.MIDIPacketListAdd.argtypes = [POINTER(MIDIPacketList), c_size_t, POINTER(MIDIPacket), c_uint64, c_uint16, POINTER(c_uint8)]
CORE_MIDI.MIDISend.restype = c_int32
CORE_MIDI.MIDISend.argtypes = [c_void_p, c_void_p, POINTER(MIDIPacketList)]
CORE_MIDI.MIDIGetNumberOfSources.restype = c_long
CORE_MIDI.MIDIGetSource.restype = c_void_p
CORE_MIDI.MIDIGetSource.argtypes = [c_long]


def list_destinations() -> list[str]:
    names = []
    for i in range(CORE_MIDI.MIDIGetNumberOfDestinations()):
        ep = CORE_MIDI.MIDIGetDestination(i)
        s = c_void_p()
        if CORE_MIDI.MIDIObjectGetStringProperty(ep, _cfstring(kMIDIPropertyName), ctypes.byref(s)) == 0 and s.value:
            CORE_FOUNDATION.CFStringGetCString.restype = ctypes.c_int
            CORE_FOUNDATION.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
            buf = ctypes.create_string_buffer(256)
            CORE_FOUNDATION.CFStringGetCString(s.value, buf, 256, kCFStringEncodingUTF8)
            names.append(buf.value.decode())
    return names


def list_sources() -> list[str]:
    names = []
    for i in range(CORE_MIDI.MIDIGetNumberOfSources()):
        ep = CORE_MIDI.MIDIGetSource(i)
        s = c_void_p()
        if CORE_MIDI.MIDIObjectGetStringProperty(ep, _cfstring(kMIDIPropertyName), ctypes.byref(s)) == 0 and s.value:
            CORE_FOUNDATION.CFStringGetCString.restype = ctypes.c_int
            CORE_FOUNDATION.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
            buf = ctypes.create_string_buffer(256)
            CORE_FOUNDATION.CFStringGetCString(s.value, buf, 256, kCFStringEncodingUTF8)
            names.append(buf.value.decode())
    return names


def find_destination(wanted: str) -> c_void_p:
    for i in range(CORE_MIDI.MIDIGetNumberOfDestinations()):
        ep = CORE_MIDI.MIDIGetDestination(i)
        s = c_void_p()
        CORE_MIDI.MIDIObjectGetStringProperty(ep, _cfstring(kMIDIPropertyName), ctypes.byref(s))
        if s.value:
            CORE_FOUNDATION.CFStringGetCString.restype = ctypes.c_int
            CORE_FOUNDATION.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
            buf = ctypes.create_string_buffer(256)
            CORE_FOUNDATION.CFStringGetCString(s.value, buf, 256, kCFStringEncodingUTF8)
            if buf.value.decode() == wanted:
                return ep
    raise RuntimeError(f"Destination nicht gefunden: {wanted!r} – verfügbar: {list_destinations()}")


# ---- UMP-Helfer ------------------------------------------------------------

def ump_midi2_note_on(group: int, ch: int, note: int, vel7: int = 127) -> list[int]:
    """MIDI 2.0 Note On (Message Type 0x4, 64 Bit)."""
    v16 = round(vel7 * 65535 / 127)
    w0 = (0x4 << 28) | ((group & 0xF) << 24) | ((0x9 << 4 | ch) << 16) | (note << 8) | 0x00
    w1 = (v16 << 16) & 0xFFFFFFFF
    return [(w0 >> s) & 0xFF for s in (24, 16, 8, 0)] + [(w1 >> s) & 0xFF for s in (24, 16, 8, 0)]


def ump_midi2_note_off(group: int, ch: int, note: int, vel7: int = 0) -> list[int]:
    v16 = round(vel7 * 65535 / 127)
    w0 = (0x4 << 28) | ((group & 0xF) << 24) | ((0x8 << 4 | ch) << 16) | (note << 8) | 0x00
    w1 = (v16 << 16) & 0xFFFFFFFF
    return [(w0 >> s) & 0xFF for s in (24, 16, 8, 0)] + [(w1 >> s) & 0xFF for s in (24, 16, 8, 0)]


def ump_midi1_cv(status_byte: int, data: list[int]) -> list[int]:
    """MIDI 1.0 Channel Voice in UMP (Message Type 0x2, 32 Bit) – z.B. [0x20,0x90,60,127]."""
    w0 = (0x2 << 28) | ((status_byte & 0xF0) << 16) | (((status_byte & 0x0F)) << 24)
    # korrekte Anordnung: byte0=0x2g, byte1=status, byte2/3=data
    w0 = (0x2 << 28) | (0 << 24) | (status_byte << 16) | ((data[0] if len(data) > 0 else 0) << 8) | (data[1] if len(data) > 1 else 0)
    return [(w0 >> s) & 0xFF for s in (24, 16, 8, 0)]


def ump_sysex7_complete(payload: list[int]) -> list[int]:
    """Komplette SysEx7 als 64-Bit-UMP (mt=0x3, Status 0 = complete).

    `payload` ohne F0/F7; F0 + payload + F7 müssen zusammen max. 6 Bytes sein.
    """
    b = [0xF0] + [d & 0x7F for d in payload] + [0xF7]
    if len(b) > 6:
        raise ValueError("SysEx7 payload zu lang für ein 64-Bit-UMP (max 4 Datenbytes)")
    b += [0] * (6 - len(b))
    w0 = (0x3 << 28) | (len(b) << 16) | (b[0] << 8) | b[1]
    w1 = (b[2] << 24) | (b[3] << 16) | (b[4] << 8) | b[5]
    return [(w0 >> s) & 0xFF for s in (24, 16, 8, 0)] + [(w1 >> s) & 0xFF for s in (24, 16, 8, 0)]


def ump_device_inquiry() -> list[int]:
    """Universal Device Inquiry als UMP: F0 7E 7F 06 01 F7."""
    return ump_sysex7_complete([0x7E, 0x7F, 0x06, 0x01])


class UMPOut:
    """Sendet rohe UMP-Pakete an einen CoreMIDI-Destination-Port.

    Nutzt das kompilierte Tool `tools/ump_send` (Objective-C/CoreMIDI),
    da das direkte MIDISend via ctypes auf diesem System keine Pakete zustellt.
    """

    TOOL = str(Path(__file__).resolve().parent.parent / "tools" / "ump_send")

    def __init__(self, dest_name: str, client_name: str = "bloridium-ump"):
        # Ziel verifizieren (wirft RuntimeError, wenn nicht vorhanden)
        find_destination(dest_name)
        self.dest_name = dest_name

    def send_ump(self, packets: list[list[int]]) -> None:
        import subprocess
        hexpkts = [" ".join(f"{b:02X}" for b in pkt) for pkt in packets]
        r = subprocess.run([self.TOOL, self.dest_name, *hexpkts], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"ump_send fehlgeschlagen: {r.stderr or r.stdout}")

    def note_on(self, ch: int = 0, note: int = 60, vel: int = 127, group: int = 0, midi2: bool = True):
        pkt = ump_midi2_note_on(group, ch, note, vel) if midi2 else ump_midi1_cv(0x90 | ch, [note, vel])
        self.send_ump([pkt])

    def note_off(self, ch: int = 0, note: int = 60, group: int = 0):
        self.send_ump([ump_midi2_note_off(group, ch, note)])

    def device_inquiry(self):
        self.send_ump([ump_device_inquiry()])

    def close(self):
        pass
