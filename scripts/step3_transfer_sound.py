#!/usr/bin/env python3
"""Schritt 3: Einen Blofeld-Sound auf den Iridium uebertragen + A/B-Klangmessung.

Ablauf:
  1. Blofeld-SNDD lesen (Location, z.B. A043) und parsen
  2. Parameter per docs/MAPPING.md auf Iridium-CCs mappen (bloridium/mapping.py)
  3. CCs an den Iridium senden (Part-Kanaele, default 6-9)
  4. Gleichzeitig Note auf beiden Synths spielen (Blofeld ch5, Iridium ch6),
     alle 20 Scarlett-Kanaele aufnehmen, In3/4 (Blofeld) vs In5/6 (Iridium) vergleichen

Aufruf:  python3 scripts/step3_transfer_sound.py [A043] [--channels 6] [--note 60]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, blofeld_dump as bd, mapping, midi

REC = Path(__file__).resolve().parent.parent / "recordings"


def read_blofeld(location: str) -> dict:
    bb, nn = bd_parse_loc(location)
    synth = midi.connect("blofeld")
    try:
        synth.send_sysex(bd.build_sndr(bb=bb, nn=nn))
        for m in synth.receive(timeout=4.0):
            if m.type == "sysex":
                from bloridium import waldorf
                p = waldorf.parse_sysex(m.data)
                if p.get("cmd") == 0x10:
                    return bd.parse_sndd(bytes([0xF0] + list(m.data) + [0xF7]))
        raise RuntimeError("kein SNDD empfangen")
    finally:
        synth.close()


def bd_parse_loc(arg: str):
    if arg.lower() in ("edit", ""):
        return 0x7F, 0x00
    arg = arg.strip().upper()
    return ord(arg[0]) - ord("A"), int(arg[1:]) - 1


def spectral_centroid(x: np.ndarray, sr: int = audio.SAMPLERATE) -> float:
    x = np.asarray(x, dtype=np.float64).mean(axis=0)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((f * X).sum() / max(X.sum(), 1e-12))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    loc = args[0] if args else "A043"
    note = 60
    dur = 3.0
    part_channels = [5, 6, 7, 8]  # 0-basiert: MIDI 6-9
    for i, a in enumerate(sys.argv):
        if a == "--note":
            note = int(sys.argv[i + 1])
        if a == "--channels":
            part_channels = [int(c) - 1 for c in sys.argv[i + 1].split(",")]
        if a == "--dur":
            dur = float(sys.argv[i + 1])

    REC.mkdir(exist_ok=True)

    # 1+2: Blofeld-Dump lesen + mappen
    parsed = read_blofeld(loc)
    msgs, unmapped = mapping.blofeld_to_iridium(parsed)
    print(f"Blofeld-Sound: {parsed['name']!r} ({loc})  -> {len(msgs)} Iridium-CCs, {len(unmapped)} unmapped")

    # 3+4: beide Synths verbinden, CCs senden, dann gleichzeitig aufnehmen
    with midi.connect("blofeld") as blo, midi.connect("iridium") as irr:
        # Ruhezustand
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
        time.sleep(0.5)

        print(f"Sende {len(msgs)} CCs an Iridium (Kanaele 0-basiert {part_channels})...")
        for ir_name, cc, val, bf, note_txt in msgs:
            for ch in part_channels:
                irr.control_change(cc, val, channel=ch)
            time.sleep(0.005)
        time.sleep(0.5)

        # gleichzeitig aufnehmen waehrend beide spielen
        blo.note_on(note=note, velocity=100)
        irr.note_on(note=note, velocity=100, channel=part_channels[0])
        try:
            time.sleep(0.3)
            data = audio.record(duration=dur, channels=None)  # alle 20 Kanaele
        finally:
            blo.note_off(note=note)
            irr.note_off(note=note, channel=part_channels[0])
            for ch in range(16):
                blo.control_change(123, 0, channel=ch)
                irr.control_change(123, 0, channel=ch)

    # record(channels=None) liefert (20, samples)
    b_ch = audio.CHANNELS["blofeld"]   # (2,3)
    i_ch = audio.CHANNELS["iridium"]   # (4,5)
    blo_x = data[b_ch, :]      # (2, samples)
    irr_x = data[i_ch, :]

    mb, mi = audio.measure(blo_x), audio.measure(irr_x)
    print("\n=== A/B-Messung (Note %d, %.1fs) ===" % (note, dur))
    print(f"Blofeld  In3/4: peak {np.max(mb['peak_dbfs']):6.1f} dBFS, rms {np.max(mb['rms_dbfs']):6.1f} dBFS, centroid {spectral_centroid(blo_x):8.1f} Hz")
    print(f"Iridium  In5/6: peak {np.max(mi['peak_dbfs']):6.1f} dBFS, rms {np.max(mi['rms_dbfs']):6.1f} dBFS, centroid {spectral_centroid(irr_x):8.1f} Hz")
    print(f"Delta peak: {np.max(mi['peak_dbfs']) - np.max(mb['peak_dbfs']):+.1f} dB, centroid: {spectral_centroid(irr_x) - spectral_centroid(blo_x):+.1f} Hz")

    ts = time.strftime("%Y%m%d_%H%M%S")
    np.save(REC / f"ab_{loc}_{ts}_blofeld.npy", blo_x)
    np.save(REC / f"ab_{loc}_{ts}_iridium.npy", irr_x)
    print(f"\nAufnahmen gespeichert: recordings/ab_{loc}_{ts}_*.npy")
    print(f"Unmapped ({len(unmapped)}): {unmapped[:15]} ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
