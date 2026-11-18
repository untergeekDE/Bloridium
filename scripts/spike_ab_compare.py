#!/usr/bin/env python3
"""Spike: A/B comparison Blofeld A043 'SH Power' vs Iridium (loaded converted patch).

Measurement series (both synths simultaneously, Scarlett all 20 channels):
  1. Velocity curve:  note 36 at vel [1, 32, 64, 96, 127]
  2. Modwheel (CC1):   note 36 vel 100, CC1 [0, 32, 64, 96, 127]
  3. Aftertouch (Channel Pressure): note 36 vel 100, Pressure [0, 32, 64, 96, 127]
Per take: peak/rms dBFS + spectral centroid per synth (Blofeld In3/4, Iridium In5/6).
Output: JSON report + .npy per take under OUT.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/Users/jan/Code/Bloridium")

import mido
import numpy as np

from bloridium import audio, blofeld_dump as bd, midi, waldorf, workflow

OUT = Path("/private/var/folders/kg/zkn9b6n546vfmpb6qd3n4pdr0000gn/T/opencode/ab_spike")
OUT.mkdir(parents=True, exist_ok=True)
NOTE = 36
IRR_CH = 5  # 0-based = MIDI 6 (Part 1)


def all_notes_off(synths):
    for s in synths:
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    time.sleep(0.5)


def blofeld_edit_name(blo):
    blo.send_sysex(bd.build_sndr(bb=0x7F, nn=0x00))
    for m in blo.receive(timeout=3.0):
        if m.type == "sysex":
            p = waldorf.parse_sysex(m.data)
            if p.get("cmd") == 0x10:
                return bd.parse_sndd(bytes([0xF0] + list(m.data) + [0xF7]))["name"]
    return None


def take(blo, irr, vel, dur=1.2, cc=None, pressure=None):
    if cc is not None:
        blo.control_change(cc[0], cc[1])
        irr.control_change(cc[0], cc[1], channel=IRR_CH)
    if pressure is not None:
        blo.send(mido.Message("aftertouch", channel=blo.channel, value=pressure))
        irr.send(mido.Message("aftertouch", channel=IRR_CH, value=pressure))
    blo.note_on(note=NOTE, velocity=vel)
    irr.note_on(note=NOTE, velocity=vel, channel=IRR_CH)
    try:
        time.sleep(0.3)
        data = audio.record(duration=dur, channels=None)
    finally:
        blo.note_off(note=NOTE)
        irr.note_off(note=NOTE, channel=IRR_CH)
    all_notes_off([blo, irr])
    bx = data[audio.CHANNELS["blofeld"], :]
    ix = data[audio.CHANNELS["iridium"], :]
    mb, mi = audio.measure(bx), audio.measure(ix)
    return {
        "blofeld": {"peak_dbfs": float(np.max(mb["peak_dbfs"])),
                    "rms_dbfs": float(np.max(mb["rms_dbfs"])),
                    "centroid_hz": workflow.spectral_centroid(bx)},
        "iridium": {"peak_dbfs": float(np.max(mi["peak_dbfs"])),
                    "rms_dbfs": float(np.max(mi["rms_dbfs"])),
                    "centroid_hz": workflow.spectral_centroid(ix)},
        "npy": (bx, ix),
    }


def main():
    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    report = {"note": NOTE, "blofeld_edit": blofeld_edit_name(blo), "series": {}}
    print("Blofeld edit buffer:", repr(report["blofeld_edit"]))
    all_notes_off([blo, irr])
    ts = time.strftime("%Y%m%d_%H%M%S")

    for series, levels, kw in (
        ("velocity", [1, 32, 64, 96, 127], lambda lv: {"vel": lv}),
        ("modwheel_cc1", [0, 32, 64, 96, 127], lambda lv: {"vel": 100, "cc": (1, lv)}),
        ("aftertouch", [0, 32, 64, 96, 127], lambda lv: {"vel": 100, "pressure": lv}),
    ):
        rows = []
        for lv in levels:
            r = take(blo, irr, dur=1.2, **kw(lv))
            bx, ix = r.pop("npy")
            np.save(OUT / f"{ts}_{series}_{lv}_blofeld.npy", bx)
            np.save(OUT / f"{ts}_{series}_{lv}_iridium.npy", ix)
            rows.append({"level": lv, **r})
            b, i = r["blofeld"], r["iridium"]
            print(f"{series:16s} lv={lv:3d}  BLO peak {b['peak_dbfs']:6.1f} rms {b['rms_dbfs']:6.1f} cent {b['centroid_hz']:7.1f} | "
                  f"IRR peak {i['peak_dbfs']:6.1f} rms {i['rms_dbfs']:6.1f} cent {i['centroid_hz']:7.1f} | "
                  f"dPeak {i['peak_dbfs']-b['peak_dbfs']:+5.1f} dB dCent {i['centroid_hz']-b['centroid_hz']:+7.1f} Hz")
        report["series"][series] = rows

    blo.close()
    irr.close()
    (OUT / f"report_{ts}.json").write_text(json.dumps(report, indent=2))
    print("Report:", OUT / f"report_{ts}.json")


if __name__ == "__main__":
    main()
