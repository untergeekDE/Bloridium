#!/usr/bin/env python3
"""CC-Sweep mit Init auf beiden Geraeten: Filter/Mod-CCs, je 0/64/127, simultan messen."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/jan/Code/Bloridium")
import numpy as np
from bloridium import midi, audio, workflow

OUT = Path("/private/var/folders/kg/zkn9b6n546vfmpb6qd3n4pdr0000gn/T/opencode/ab_spike")
OUT.mkdir(parents=True, exist_ok=True)
NOTE = 36

# (label, blofeld_cc, iridium_cc, values)
SWEEPS = [
    ("Filter-Cutoff  BLO CC69 / IRR CC9(F2)", 69, 9, [0, 32, 64, 96, 127]),
    ("Filter-Reso    BLO CC70 / IRR CC2",     70, 2, [0, 64, 127]),
    ("Filter-EnvSust BLO CC?  / IRR CC5",      None, 5, [0, 64, 127]),
    ("ModWheel       BLO CC1  / IRR CC1",      1, 1, [0, 64, 127]),
    ("Amp-Velo       BLO CC91 / IRR CC17",     91, 17, [0, 64, 127]),
]

def rec(dur=1.0):
    for _ in range(3):
        d = audio.record(duration=dur, channels=None)
        if d.size: return d
        time.sleep(1.0)
    raise RuntimeError("leer")

blo = midi.connect("blofeld")
irr = midi.connect("iridium")
for s in (blo, irr):
    for ch in range(16):
        s.control_change(123, 0, channel=ch)
irr.control_change(7, 127, channel=5)  # Sicherheit: Iridium Output an
time.sleep(0.5)

report = {"note": NOTE, "blofeld": "Init (A66)", "iridium": "Init (00000, v15)", "sweeps": []}
ts = time.strftime("%Y%m%d_%H%M%S")
for label, bcc, icc, values in SWEEPS:
    rows = []
    for v in values:
        if bcc: blo.control_change(bcc, v)
        irr.control_change(icc, v, channel=5)
        blo.note_on(note=NOTE, velocity=100)
        irr.note_on(note=NOTE, velocity=100, channel=5)
        time.sleep(0.3)
        data = rec(1.0)
        blo.note_off(note=NOTE); irr.note_off(note=NOTE, channel=5)
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
        bx = data[audio.CHANNELS["blofeld"], :]
        ix = data[audio.CHANNELS["iridium"], :]
        mb, mi = audio.measure(bx), audio.measure(ix)
        row = {"value": v,
               "blofeld": {"peak_dbfs": float(np.max(mb["peak_dbfs"])), "centroid_hz": workflow.spectral_centroid(bx)},
               "iridium": {"peak_dbfs": float(np.max(mi["peak_dbfs"])), "centroid_hz": workflow.spectral_centroid(ix)}}
        rows.append(row)
        np.save(OUT / f"{ts}_sweep_{bcc}_{icc}_{v}_blofeld.npy", bx)
        np.save(OUT / f"{ts}_sweep_{bcc}_{icc}_{v}_iridium.npy", ix)
        b, i = row["blofeld"], row["iridium"]
        print(f"{label:36s} v={v:3d} | BLO peak {b['peak_dbfs']:6.1f} cent {b['centroid_hz']:7.1f} | IRR peak {i['peak_dbfs']:6.1f} cent {i['centroid_hz']:7.1f}")
        time.sleep(0.2)
    report["sweeps"].append({"label": label, "blo_cc": bcc, "irr_cc": icc, "rows": rows})
    # neutral zuruecksetzen
    if bcc: blo.control_change(bcc, 127 if bcc in (69,) else 64)
    irr.control_change(icc, 127 if icc == 9 else (64 if icc in (2, 5, 1, 17) else 127), channel=5)

blo.close(); irr.close()
(OUT / f"cc_sweep_init_{ts}.json").write_text(json.dumps(report, indent=2))
print("Report:", OUT / f"cc_sweep_init_{ts}.json")
