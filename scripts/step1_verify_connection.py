#!/usr/bin/env python3
"""Schritt 1: Verbindung zu beiden Synthesizern herstellen + Sound messen.

Testet pro Synthesizer (Blofeld, Iridium):
  1. MIDI-Verbindung: Port öffnen, Universal Device Inquiry senden,
     eingehende MIDI-Nachrichten mitlesen
  2. Sound-Messung: Note spielen und Pegel am Scarlett 18i8 messen
     (Blofeld: Eingänge 3/4, Iridium: Eingänge 5/6)

Aufruf:  python3 scripts/step1_verify_connection.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi

NOTE = 60          # C4
VELOCITY = 100
DURATION = 2.0     # Aufnahme-Dauer in s
PEAK_THRESHOLD_DB = -60.0   # Aufnahme gilt als "Ton vorhanden", wenn Peak darüber


def fmt_db(v: float) -> str:
    return f"{v:.1f} dBFS" if v != float("-inf") else "-inf dBFS"


def describe_sysex(m) -> str:
    d = list(m.data)
    if len(d) >= 6 and d[0] == 0x7E and d[2] == 0x06 and d[3] == 0x02:
        manuf = d[4:7]
        return f"Identity Reply (Hersteller-ID {manuf[0]:02X} {manuf[1]:02X} {manuf[2]:02X}, Familie {d[7] if len(d) > 7 else '?'} ...)"
    return f"SysEx {bytes([0xF0, *d, 0xF7]).hex(' ')}"


def test_synth(name: str, synth: midi.Synth, channels) -> bool:
    print(f"\n=== {name.upper()} ===")
    print(f"  MIDI Out : {synth.out_port_name}")
    print(f"  MIDI In  : {synth.in_port_name or '(kein Rückkanal)'}")
    print(f"  Audio In : Scarlett 18i8 {DEVICE_DESC[channels]}")

    # --- 1) MIDI: Device Inquiry --------------------------------------
    synth.device_inquiry()
    replies = synth.receive(timeout=1.0)
    sysex = [m for m in replies if m.type == "sysex"]
    if sysex:
        for m in sysex:
            print(f"  MIDI <- {describe_sysex(m)}")
    elif replies:
        print(f"  MIDI <- {len(replies)} Nachricht(en): {[str(m) for m in replies[:5]]}")
    else:
        print("  MIDI <- keine Antwort (Rückkanal evtl. nicht verdrahtet – prüfe per Audio)")

    # --- 2) Sound: Note spielen + Pegel messen -------------------------
    # Kanal kommt vom Synth-Objekt (empirisch ermittelt: Blofeld Kanal 5, Iridium Kanal 6)
    print(f"  MIDI-Kanal (0-basiert): {synth.channel} (Kanal {synth.channel + 1})")
    data, m = audio.play_and_measure(
        synth, channels, note=NOTE, velocity=VELOCITY, duration=DURATION
    )
    labels = ["L", "R"] if len(channels) == 2 else [f"c{channels[0]}"]
    print(f"  Audio: {data.shape[1]} Samples @ {audio.SAMPLERATE} Hz aufgenommen")
    for i, lab in enumerate(labels):
        print(f"    Kanal {lab}: RMS {fmt_db(m['rms_dbfs'][i])}, Peak {fmt_db(m['peak_dbfs'][i])}")
    ok = bool((m["peak_dbfs"] > PEAK_THRESHOLD_DB).any())
    print(f"  Ergebnis Sound-Messung: {'OK – Ton gemessen' if ok else 'KEIN TON gemessen!'}")
    return ok


DEVICE_DESC = {
    (2, 3): "Eingänge 3/4 (Kanäle c2/c3)",
    (4, 5): "Eingänge 5/6 (Kanäle c4/c5)",
}


def main() -> int:
    print("Verfügbare MIDI-Ports:")
    ports = midi.list_ports()
    for p in ports["out"]:
        print(f"  OUT: {p}")
    for p in ports["in"]:
        print(f"  IN : {p}")
    print(f"\nAudio-Device: {audio.DEVICE} ({audio.SAMPLERATE} Hz, 20 Eingänge)")

    results = {}
    synths = {}
    try:
        for name in ("blofeld", "iridium"):
            synth = midi.connect(name)
            synths[name] = synth
            results[name] = test_synth(name, synth, audio.CHANNELS[name])
    finally:
        for s in synths.values():
            s.close()

    print("\n=== Zusammenfassung ===")
    all_ok = True
    for name, ok in results.items():
        print(f"  {name:9s}: {'VERBUNDEN, Sound messbar' if ok else 'PROBLEM'}")
        all_ok &= ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
