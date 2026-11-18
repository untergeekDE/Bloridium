"""CP70 (EXS24 sample pack) -> Waldorf Iridium .qpat + sample folder.

Source: CP70-Exs24-v1.2.zip (Logic EXS24: CP70.exs + CP70/*.wav, 44.1 kHz/16-bit/mono).
Target: transfer/cp70/ with
        - 220_CP70_Piano.qpat   (v14, OSC1=Particle, sample map embedded as Resource 4)
        - CP70.map              (identical map as standalone file for Actions>Load Map)
        - samples/CP70/*.wav    ( USB stick -> Iridium Timbre>Actions>Add>Copy -> internal /samples/CP70/ )
        - MANIFEST.md           (import instructions)

Layout of the EXS24 instrument (reverse-engineered, see parse_exs docstring):
  groups CP70B-* = bass (keys 29..52), CP70_* = mid (53..78), CP70H_* = high (79..127),
  each with 6 velocity layers (e.g. CP70_40 = vel 0-40), *_OFF = release samples (b44==1, skipped),
  *_1.wav = alternate takes (skipped). Per zone: key_lo/hi, root, vel_lo/hi.

Sample preparation (analogous to undergeek.de/2024/12/cp70-piano-for-the-iridium):
  trim leading silence, normalize peak to -6 dBFS (all samples at the same level --
  dynamics come from the VCA via AmpVeloAmount), map gain = 1.0.

Map format (16 TSV columns, "3:" = internal memory):
  "3:/samples/CP70/<file>.wav"  pitch  note_lo  note_hi  gain  vel_lo  vel_hi
  NN(0.5)  start(0)  end(1)  dir(0)  loop_start(0)  loop_end(1)  loop_mode(0)  xfade(0.5)  track_pitch(1)

Run:  python3 scripts/build_cp70_iridium.py
"""

from __future__ import annotations

import io
import json
import math
import re
import struct
import wave
import zipfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
ZIP_PATH = Path("/Users/jan/Nextcloud/AAA Musik/01 Sounds/SAMPLES/CP70-Exs24-v1.2.zip")
TEMPLATE = REPO / "dumps/export-001/00000-NotSoGrand.qpat"  # v14 device export with Particle OSC + maps
OUT_DIR = REPO / "transfer/cp70"
SAMPLE_DIR = OUT_DIR / "samples/CP70"          # USB-stick layout: <stick>/samples/CP70/
INTERNAL_SAMPLE_PATH = "3:/samples/CP70"       # this is where the samples live in the Iridium's internal memory
QPAT_NAME = "220_CP70_Piano.qpat"              # Slot 0220 (0200-0215 occupied, see IRIDIUM-FAVORITES-MAP)
SOUND_NAME = "CP70 Piano"
PEAK = 0.5                                      # -6 dBFS
TRIM_THRESHOLD = 0.004                          # ~ -48 dBFS
TRIM_BACKOFF = 88                               # 2 ms @44.1k


# ---- EXS24 parsen -----------------------------------------------------------

def parse_exs(data: bytes) -> list[dict]:
    """CP70.exs -> Zonenliste [{sample, frames, zname, klo, khi, root, vlo, vhi, b44}]."""
    pos = [m.start() for m in re.finditer(b"TBOS", data)]
    # Sample table: TBOS records starting at the first sample entry "*.wav" (676 B stride)
    sbase = next(p for p in pos
                 if re.match(rb"CP70\S* \d\d(_1)?\.wav", data[p + 4:p + 28]))
    samps = []
    p = sbase
    while p + 676 <= len(data) and data[p:p + 4] == b"TBOS":
        rec = data[p:p + 676]
        name = rec[4:28].split(b"\0")[0].decode()
        if not name.endswith(".wav"):
            break
        samps.append({"name": name, "frames": struct.unpack("<I", rec[0x48:0x4C])[0]})
        p += 676
    # Zone table: 220-byte records from 0xb4 (after the header)
    zbase = 0xB4
    zones = []
    p = zbase
    while p + 220 <= sbase and data[p:p + 4] == b"TBOS":
        rec = data[p:p + 220]
        name = rec[4:28].split(b"\0")[0].decode("ascii", "replace")
        idx = struct.unpack("<I", rec[0xA0:0xA4])[0]
        if idx < len(samps) and re.match(r"^[A-G]#?-?\d", name):
            s = samps[idx]
            zones.append({
                "sample": s["name"], "frames": s["frames"], "zname": name,
                "klo": rec[0x45], "khi": rec[0x4B], "root": rec[0x4A],
                "vlo": rec[0x4D], "vhi": rec[0x4E], "b44": rec[0x44],
            })
        p += 220
    return zones


def select_zones(zones: list[dict]) -> list[dict]:
    """Select main takes: no OFF (b44==1), no _1 takes, register per group name."""
    out = []
    for z in zones:
        if z["b44"] != 8 or z["sample"].endswith("_1.wav"):
            continue
        g = z["sample"].split(" ")[0]
        if g.startswith("CP70B-") and 29 <= z["klo"] <= 52:
            out.append(z)
        elif g.startswith("CP70H_") and z["klo"] >= 79:
            out.append(z)
        elif re.fullmatch(r"CP70_\d+", g) and 53 <= z["klo"] <= 78:
            out.append(z)
    out.sort(key=lambda z: (z["klo"], z["vlo"]))
    return out


# ---- Audio ------------------------------------------------------------------

def read_wav_mono(zf: zipfile.ZipFile, name: str) -> tuple[np.ndarray, int]:
    raw = zf.read("CP70/" + name)
    w = wave.open(io.BytesIO(raw))
    assert w.getnchannels() == 1 and w.getsampwidth() == 2, name
    rate = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768.0
    return x, rate


def trim_and_normalize(x: np.ndarray, rate: int) -> np.ndarray:
    onset = int(np.argmax(np.abs(x) > TRIM_THRESHOLD)) if np.any(np.abs(x) > TRIM_THRESHOLD) else 0
    start = max(0, onset - TRIM_BACKOFF)
    x = x[start:]
    peak = np.max(np.abs(x)) if x.size else 0.0
    if peak > 0:
        x = x * (PEAK / peak)
    return x


def detect_pitch_midi(x: np.ndarray, rate: int) -> float | None:
    """Autocorrelation on 0.4 s after the attack -> MIDI note (float), 25..1200 Hz."""
    n0 = min(len(x), int(rate * 0.05))
    seg = x[n0:n0 + int(rate * 0.4)]
    if seg.size < 4096:
        return None
    seg = seg - seg.mean()
    if np.max(np.abs(seg)) < 0.01:
        return None
    lo, hi = int(rate / 1200.0), int(rate / 25.0)
    ac = np.correlate(seg, seg, mode="full")[len(seg) - 1:]
    ac /= (ac[0] + 1e-12)
    lag = lo + int(np.argmax(ac[lo:hi]))
    if 0 < lag < len(ac) - 1:  # parabolic interpolation around the peak (sub-sample accuracy)
        y0, y1, y2 = ac[lag - 1], ac[lag], ac[lag + 1]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
        lag += d
    f0 = rate / lag
    return 69.0 + 12.0 * math.log2(f0 / 440.0)


def write_wav_mono(path: Path, x: np.ndarray, rate: int) -> None:
    y = np.clip(x, -1.0, 1.0)
    path.write_bytes(b"")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((y * 32767.0).astype("<i2").tobytes())


# ---- Map + qpat -------------------------------------------------------------

def map_line(fname: str, root: float, klo: int, khi: int, vlo: int, vhi: int) -> str:
    return (f'"{INTERNAL_SAMPLE_PATH}/{fname}"\t{root:.8f}\t{klo}\t{khi}\t1.00000000\t'
            f'{vlo}\t{vhi}\t0.50000000\t0.00000000\t1.00000000\t0\t'
            f'0.00000000\t1.00000000\t0\t0.50000000\t1')


def main() -> None:
    from bloridium import qpat

    zf = zipfile.ZipFile(ZIP_PATH)
    zones = select_zones(parse_exs(zf.read("CP70.exs")))
    print(f"Zones selected: {len(zones)}")

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    entries = []          # (fname, root, klo, khi, vlo, vhi)
    used = {}
    for z in zones:
        src = z["sample"]
        fname = src.replace(" ", "_")               # USB-stick/FAT32-safe
        x, rate = read_wav_mono(zf, src)
        x = trim_and_normalize(x, rate)
        root = float(z["root"])
        if root <= 0:                                # C-1 zones: determine root from f0 (no valid EXS root key)
            det = detect_pitch_midi(x, rate)
            if det is not None:
                root = det
        if src not in used:
            write_wav_mono(SAMPLE_DIR / fname, x, rate)
            used[src] = fname
        entries.append((used[src], root, z["klo"], z["khi"], z["vlo"], z["vhi"]))
        if z["zname"] in ("F3-F#3", "C4-C#4", "C-1-F#1", "E7-G9"):
            det = detect_pitch_midi(x, rate)
            print(f"  {src:22s} root_exs={z['root']:3d} f0={det if det is None else round(det, 2)} "
                  f"key {z['klo']}-{z['khi']} vel {z['vlo']}-{z['vhi']}")

    # Fill gaps in the pack (e.g. keys 65-66 in layer CP70_75): cover missing (key, vel)
    # cells with a donor zone of the same key from a neighboring vel range, so every
    # (key, vel) cell is playable.
    cov = set()
    for _, _, klo, khi, vlo, vhi in entries:
        for k in range(klo, khi + 1):
            for v in range(vlo, vhi + 1):
                cov.add((k, v))
    missing = [(k, v) for k in range(29, 128) for v in range(128) if (k, v) not in cov]
    filled = 0
    by_key = {}
    for e in entries:
        for k in range(e[2], e[3] + 1):
            by_key.setdefault(k, []).append(e)
    for k, v in missing:
        donors = by_key.get(k, [])
        if not donors:
            continue
        # Donor = zone with the nearest vel range (least audible difference)
        donor = min(donors, key=lambda e: min(abs(e[4] - v), abs(e[5] - v)))
        entries.append((donor[0], donor[1], k, k, v, v))
        cov.add((k, v))
        filled += 1
    print(f"Gap fill: {filled} cells added")
    lines = [map_line(*e) for e in sorted(entries, key=lambda e: (e[2], e[4]))]
    map_text = "\n".join(lines) + "\n"
    total = sum((SAMPLE_DIR / f).stat().st_size for f in used.values())
    print(f"Samples: {len(used)} files, {total/1e6:.1f} MB; map lines: {len(lines)}")

    (OUT_DIR / "CP70.map").write_text(map_text)

    # --- qpat from the device-export template (v14, OSC1=Particle) ---
    tpl = qpat.load(TEMPLATE)
    params = {k: (v["value"], v["display"]) for k, v in tpl["params"].items()}
    params.update({
        "Osc1Type": (2.0, "Particle"),
        "Osc2Type": (5.0, "Off"),                    # v14 device enum: Off=5 (v15: 6)
        "Osc3Type": (5.0, "Off"),
        "Osc1ParticleSampleMode": (2.0, "Normal"),
        "Osc1Vol": (1.0, ""),
        "Osc1Pan": (0.5, ""),
        "AmpVeloAmount": (0.75, ""),                 # dynamics via VCA (samples are normalized to equal peak)
        "AmpEnvAttack": (0.0, ""),
        "AmpEnvDecay": (0.9, ""),
        "AmpEnvSustain": (1.0, ""),
        "AmpEnvRelease": (0.25, ""),
        "DigiFormerType": (0.0, "Bypass"),
        "Filter2State": (2.0, "Off"),
        "Filter12Type": (0.0, "12dB LP"),
        "Filter1CutOff": (1.0, ""),
        "Filter1Reso": (0.0, ""),
        "FilterState": (0.0, "Active"),
        "MainVolume": (0.9, ""),
        "GlideOnOff": (0.0, "Off"),
    })
    # Resource 4 (USER_SAMPLE_MAP1) + tail exactly as in the device export:
    # tail = map_text + NUL, resource = (type 4, offset=0, length=len(map_text)+1)
    resources = [{"type": 0, "offset": 0, "length": 0}] * 16
    resources[0] = {"type": 4, "offset": 0, "length": len(map_text.encode()) + 1}
    tail = map_text.encode() + b"\x00"
    # write changed params with their new display (raw_fields without these keys)
    changed = {"Osc1Vol", "Osc1Pan", "Osc2Type", "DigiFormerType", "Filter1CutOff", "Filter1Reso",
               "Filter2State", "AmpVeloAmount", "AmpEnvAttack", "AmpEnvDecay", "AmpEnvRelease",
               "MainVolume"}
    raw_fields = {k: v for k, v in tpl["_raw_fields"].items() if k not in changed}
    out = qpat.build_qpat(
        SOUND_NAME, params, creator="bloridium",
        description="Yamaha CP70 (EXS24 pack) as Iridium sampler: OSC1 Particle, "
                    "6 velocity layers, keys 29-127, samples in /samples/CP70",
        categories=["Piano", "Sample", "CP70", ""],
        version=tpl["version"],
        resources=resources, tail=tail,
        records_raw=tpl["_records_raw"], raw_fields=raw_fields,
    )
    qpat_path = OUT_DIR / QPAT_NAME
    qpat_path.write_bytes(out)

    # --- verify (re-parse and assert the structures we just built) ---
    chk = qpat.parse_qpat(qpat_path.read_bytes())
    assert chk["name"] == SOUND_NAME and chk["version"] == 14
    assert chk["resources"][0]["type"] == 4 and chk["resources"][0]["length"] == len(map_text) + 1
    assert len(chk["sample_maps"]) == 1 and chk["sample_maps"][0].strip() == map_text.strip()
    assert chk["params"]["Osc1Type"]["value"] == 2.0
    assert chk["params"]["Osc2Type"]["value"] == 5.0
    n_lines = len([l for l in chk["sample_maps"][0].splitlines() if l.strip()])
    print(f"OK: {qpat_path} ({len(out)} B), map {n_lines} lines, "
          f"res4 len {chk['resources'][0]['length']}, tail {len(chk['_tail'])} B")
    (OUT_DIR / "zones.json").write_text(json.dumps(
        [{k: z[k] for k in ("sample", "zname", "klo", "khi", "root", "vlo", "vhi")} for z in zones],
        indent=1))


if __name__ == "__main__":
    main()
