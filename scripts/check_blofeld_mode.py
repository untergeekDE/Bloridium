#!/usr/bin/env python3
"""Blofeld: empfangende MIDI-Kanaele ermitteln + Hinweis zum Betriebsmodus.

WICHTIG: Ein Kanal-Scan kann den Modus (Single vs Multi) NICHT zuverlaessig
erkennen – im Multi Mode duerfen alle 16 Parts auf beliebigen Kanaelen liegen
(bei uns z.B. nur Kanal 5 belegt, trotzdem war der Multi Mode AN).
Der Modus muss am Geraet geprueft/gesetzt werden: Shift+Sound/Multi.

Stand: Blofeld ist auf SINGLE MODE umgeschaltet (nur Global-Kanal 5 antwortet).
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
    """Pro Kanal eine Note spielen; Kanal gilt als empfangend, wenn Peak deutlich
    ueber Baseline UND absolut > -60 dBFS (vermeidet Release-Reste)."""
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
    print(f"Port: {synth.out_port_name} / {synth.in_port_name}, Global-Kanal (0-basiert): {synth.channel}")

    synth.device_inquiry()
    for m in synth.receive(2.0):
        if m.type == "sysex":
            print("Identity:", waldorf.identity_reply_info(m.data))

    synth.send_sysex(waldorf.build_sysex(waldorf.MODEL_IDS["Blofeld"], waldorf.CMD["global_request"]))
    for m in synth.receive(3.0):
        if m.type == "sysex":
            p = waldorf.parse_sysex(m.data)
            if p.get("cmd") == waldorf.CMD["global_dump"]:
                print(f"GLBD empfangen, {len(p['payload'])} Datenbytes")

    # Stumm + Release abwarten, dann Kanal-Scan
    for ch in range(16):
        synth.out.send(mido.Message("control_change", control=123, value=0, channel=ch))
        synth.out.send(mido.Message("control_change", control=120, value=0, channel=ch))
    time.sleep(4)
    base = audio.measure(audio.record(duration=2.0, channels=audio.CHANNELS["blofeld"]))["peak_dbfs"]
    time.sleep(1.0)
    hot = responsive_channels(synth.out, base)
    print(f"Empfangende MIDI-Kanaele: {hot}")
    print("\nHINWEIS: Modus (Single/Multi) ist per Kanal-Scan NICHT allein erkennbar,")
    print("da Multi-Parts auf beliebigen Kanaelen liegen duerfen. Am Geraet aendern:")
    print("Shift+Sound/Multi. Stand: SINGLE MODE aktiv (nur Global-Kanal antwortet).")
    synth.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
