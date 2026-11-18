#!/usr/bin/env python3
"""Blofeld: determine receiving MIDI channels + note on the operating mode.

IMPORTANT: a channel scan CANNOT reliably detect the mode (Single vs Multi) --
in Multi mode all 16 parts may sit on arbitrary channels
(in our case e.g. only channel 5 was occupied, yet Multi mode was ON).
The mode must be checked/set on the device: Shift+Sound/Multi.

Status: Blofeld has been switched to SINGLE MODE (only global channel 5 responds).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mido
from bloridium import audio, midi, waldorf

NOTE = 60


def responsive_channels(out, base, channels=range(16), settle=1.2):
    """Play one note per channel; a channel counts as receiving if the peak is
    clearly above the baseline AND absolute > -60 dBFS (avoids release tails)."""
    hot = []
    b = float(np.max(base))
    for ch in channels:
        out.send(mido.Message("note_on", note=NOTE, velocity=127, channel=ch))
        time.sleep(0.3)
        data = audio.record(duration=1.2, channels=audio.CHANNELS["blofeld"])
        out.send(mido.Message("note_off", note=NOTE, velocity=0, channel=ch))
        out.send(mido.Message("control_change", control=123, value=0, channel=ch))
        m = audio.measure(data)
        peak = float(np.max(m["peak_dbfs"]))
        if peak > -60 and peak - b > 15:
            hot.append(ch + 1)
        time.sleep(settle)
    return hot


def main() -> int:
    synth = midi.connect("blofeld")
    print(f"Port: {synth.out_port_name} / {synth.in_port_name}, global channel (0-based): {synth.channel}")

    synth.device_inquiry()
    for m in synth.receive(2.0):
        if m.type == "sysex":
            print("Identity:", waldorf.identity_reply_info(m.data))

    synth.send_sysex(waldorf.build_sysex(waldorf.MODEL_IDS["Blofeld"], waldorf.CMD["global_request"]))
    for m in synth.receive(3.0):
        if m.type == "sysex":
            p = waldorf.parse_sysex(m.data)
            if p.get("cmd") == waldorf.CMD["global_dump"]:
                print(f"GLBD received, {len(p['payload'])} data bytes")

    # mute + wait for release, then channel scan
    for ch in range(16):
        synth.out.send(mido.Message("control_change", control=123, value=0, channel=ch))
        synth.out.send(mido.Message("control_change", control=120, value=0, channel=ch))
    time.sleep(4)
    base = audio.measure(audio.record(duration=2.0, channels=audio.CHANNELS["blofeld"]))["peak_dbfs"]
    time.sleep(1.0)
    hot = responsive_channels(synth.out, base)
    print(f"Receiving MIDI channels: {hot}")
    print("\nNOTE: the mode (Single/Multi) cannot be detected from a channel scan alone,")
    print("because Multi parts may sit on arbitrary channels. Change on the device:")
    print("Shift+Sound/Multi. Status: SINGLE MODE active (only the global channel responds).")
    synth.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
