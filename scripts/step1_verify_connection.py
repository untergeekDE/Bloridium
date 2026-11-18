#!/usr/bin/env python3
"""Step 1: connect to both synthesizers + measure sound.

Wrapper around bloridium.workflow.check_connection (argv/exit/stdout unchanged).

Tests per synthesizer (Blofeld, Iridium):
  1. MIDI connection: open port, send Universal Device Inquiry, listen along
  2. Sound measurement: play a note and measure the level on the Scarlett 18i8
     (Blofeld: inputs 3/4, Iridium: inputs 5/6)

Usage:  python3 scripts/step1_verify_connection.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, workflow
from bloridium import waldorf

NOTE = 60          # C4
VELOCITY = 100
DURATION = 2.0     # recording duration in s
PEAK_THRESHOLD_DB = -60.0


def fmt_db(v: float) -> str:
    return f"{v:.1f} dBFS" if v != float("-inf") else "-inf dBFS"


def describe_sysex(d: list) -> str:
    if len(d) >= 6 and d[0] == 0x7E and d[2] == 0x06 and d[3] == 0x02:
        manuf = d[4:7]
        return f"Identity Reply (manufacturer ID {manuf[0]:02X} {manuf[1]:02X} {manuf[2]:02X}, family {d[7] if len(d) > 7 else '?'} ...)"
    return f"SysEx {bytes([0xF0, *d, 0xF7]).hex(' ')}"


DEVICE_DESC = {
    (2, 3): "Inputs 3/4 (channels c2/c3)",
    (4, 5): "Inputs 5/6 (channels c4/c5)",
}


def main() -> int:
    res = workflow.check_connection(do_audio=True, note=NOTE, velocity=VELOCITY, duration=DURATION)
    print("Available MIDI ports:")
    for p in res["ports"]["out"]:
        print(f"  OUT: {p}")
    for p in res["ports"]["in"]:
        print(f"  IN : {p}")
    print(f"\nAudio-Device: {audio.DEVICE} ({audio.SAMPLERATE} Hz, 20 inputs)")

    results = {}
    for name, e in res["synths"].items():
        print(f"\n=== {name.upper()} ===")
        print(f"  MIDI Out : {e['out_port']}")
        print(f"  MIDI In  : {e['in_port'] or '(no return channel)'}")
        print(f"  Audio In : Scarlett 18i8 {DEVICE_DESC[tuple(audio.CHANNELS[name])]}")
        print(f"  MIDI channel (0-based): {e['channel']} (channel {e['channel'] + 1})")
        for d in e["sysex"]:
            print(f"  MIDI <- {describe_sysex(d)}")
        if not e["sysex"] and not e["other"]:
            print("  MIDI <- no reply (return channel maybe not wired - check via audio)")
        elif e["other"]:
            print(f"  MIDI <- {len(e['other'])} message(s): {e['other'][:5]}")
        print(f"  Audio: {e['samples']} samples @ {audio.SAMPLERATE} Hz recorded")
        channels = audio.CHANNELS[name]
        labels = ["L", "R"] if len(channels) == 2 else [f"c{channels[0]}"]
        for i, lab in enumerate(labels):
            print(f"    Channel {lab}: RMS {fmt_db(e['rms_dbfs'][i])}, Peak {fmt_db(e['peak_dbfs_list'][i])}")
        ok = e["ok"]
        print(f"  Sound measurement result: {'OK – tone measured' if ok else 'NO TONE measured!'}")
        results[name] = ok

    print("\n=== Summary ===")
    all_ok = True
    for name, ok in results.items():
        print(f"  {name:9s}: {'CONNECTED, sound measurable' if ok else 'PROBLEM'}")
        all_ok &= ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
