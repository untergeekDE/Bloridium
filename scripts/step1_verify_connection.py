#!/usr/bin/env python3
"""Schritt 1: Verbindung zu beiden Synthesizern herstellen + Sound messen.

Wrapper ueber bloridium.workflow.check_connection (argv/Exit/Stdout unveraendert).

Testet pro Synthesizer (Blofeld, Iridium):
  1. MIDI-Verbindung: Port oeffnen, Universal Device Inquiry senden, mitlesen
  2. Sound-Messung: Note spielen und Pegel am Scarlett 18i8 messen
     (Blofeld: Eingaenge 3/4, Iridium: Eingaenge 5/6)

Aufruf:  python3 scripts/step1_verify_connection.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, workflow
from bloridium import waldorf

NOTE = 60          # C4
VELOCITY = 100
DURATION = 2.0     # Aufnahme-Dauer in s
PEAK_THRESHOLD_DB = -60.0


def fmt_db(v: float) -> str:
    return f"{v:.1f} dBFS" if v != float("-inf") else "-inf dBFS"


def describe_sysex(d: list) -> str:
    if len(d) >= 6 and d[0] == 0x7E and d[2] == 0x06 and d[3] == 0x02:
        manuf = d[4:7]
        return f"Identity Reply (Hersteller-ID {manuf[0]:02X} {manuf[1]:02X} {manuf[2]:02X}, Familie {d[7] if len(d) > 7 else '?'} ...)"
    return f"SysEx {bytes([0xF0, *d, 0xF7]).hex(' ')}"


DEVICE_DESC = {
    (2, 3): "Eingänge 3/4 (Kanäle c2/c3)",
    (4, 5): "Eingänge 5/6 (Kanäle c4/c5)",
}


def main() -> int:
    res = workflow.check_connection(do_audio=True, note=NOTE, velocity=VELOCITY, duration=DURATION)
    print("Verfügbare MIDI-Ports:")
    for p in res["ports"]["out"]:
        print(f"  OUT: {p}")
    for p in res["ports"]["in"]:
        print(f"  IN : {p}")
    print(f"\nAudio-Device: {audio.DEVICE} ({audio.SAMPLERATE} Hz, 20 Eingänge)")

    results = {}
    for name, e in res["synths"].items():
        print(f"\n=== {name.upper()} ===")
        print(f"  MIDI Out : {e['out_port']}")
        print(f"  MIDI In  : {e['in_port'] or '(kein Rückkanal)'}")
        print(f"  Audio In : Scarlett 18i8 {DEVICE_DESC[tuple(audio.CHANNELS[name])]}")
        print(f"  MIDI-Kanal (0-basiert): {e['channel']} (Kanal {e['channel'] + 1})")
        for d in e["sysex"]:
            print(f"  MIDI <- {describe_sysex(d)}")
        if not e["sysex"] and not e["other"]:
            print("  MIDI <- keine Antwort (Rückkanal evtl. nicht verdrahtet – prüfe per Audio)")
        elif e["other"]:
            print(f"  MIDI <- {len(e['other'])} Nachricht(en): {e['other'][:5]}")
        print(f"  Audio: {e['samples']} Samples @ {audio.SAMPLERATE} Hz aufgenommen")
        channels = audio.CHANNELS[name]
        labels = ["L", "R"] if len(channels) == 2 else [f"c{channels[0]}"]
        for i, lab in enumerate(labels):
            print(f"    Kanal {lab}: RMS {fmt_db(e['rms_dbfs'][i])}, Peak {fmt_db(e['peak_dbfs_list'][i])}")
        ok = e["ok"]
        print(f"  Ergebnis Sound-Messung: {'OK – Ton gemessen' if ok else 'KEIN TON gemessen!'}")
        results[name] = ok

    print("\n=== Zusammenfassung ===")
    all_ok = True
    for name, ok in results.items():
        print(f"  {name:9s}: {'VERBUNDEN, Sound messbar' if ok else 'PROBLEM'}")
        all_ok &= ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
