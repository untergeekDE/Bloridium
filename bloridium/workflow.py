"""Workflow-Library – importierbare Logik aus den step-Skripten.

Keine prints in Kernfunktionen (progress-Callback stattdessen); die CLI und
die Wrapper-Skripte formatieren die Ausgabe. Hardware-Zugriff nur lesend;
All Notes Off (CC123) vor jeder Messung auf allen Kanaelen beider Synths.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from . import audio, blofeld_dump as bd, midi, qpat, qpat_map, waldorf

# Repo-Root (worktree-sicher): zwei Ebenen ueber diesem File
REPO = Path(__file__).resolve().parent.parent
DUMPS = REPO / "dumps"
TRANSFER = REPO / "transfer"
RECORDINGS = REPO / "recordings"
TEMPLATE_QPAT = REPO / "docs" / "refs" / "qpat" / "template_waveform.qpat"


# ---- Locations ------------------------------------------------------------

def parse_location(loc: str) -> tuple[int, int]:
    """'A043' -> (0x00, 0x2A); 'edit' -> (0x7F, 0x00). ValueError bei ungueltig."""
    loc = loc.strip()
    if loc.lower() in ("edit", "puffer", ""):
        return 0x7F, 0x00
    loc = loc.upper()
    bank = ord(loc[0]) - ord("A") if loc else -1
    try:
        num = int(loc[1:]) - 1
    except ValueError:
        raise ValueError(f"ungueltige Location: {loc!r} (z.B. A001..Z128)") from None
    if not (0 <= bank <= 0x19 and 0 <= num <= 0x7F):
        raise ValueError(f"ungueltige Location: {loc!r} (z.B. A001..Z128)")
    return bank, num


def location_str(bb: int, nn: int) -> str:
    if bb == 0x7F and nn == 0:
        return "edit"
    return f"{chr(ord('A') + bb)}{nn + 1:03d}"


# ---- Dump-Dateien ---------------------------------------------------------

def load_sndd_file(path) -> bytes:
    """SNDD aus .bin (roh) oder .hex (hex-Text) laden; inkl. F0/F7."""
    p = Path(path)
    if p.suffix.lower() == ".hex":
        return bytes.fromhex(p.read_text().replace(" ", "").replace("\n", ""))
    return p.read_bytes()


# ---- Blofeld live lesen ---------------------------------------------------

def read_sound(synth: midi.Synth, loc: str, timeout: float = 4.0,
               retries: int = 2) -> dict:
    """SNDR -> SNDD -> parse_sndd. Retry bei Timeout/Checksum-Fehler.

    Rueckgabe: parse_sndd-Ergebnis (dict mit name, params, sdata, ...).
    Wirft RuntimeError, wenn nach allen Retries kein gueltiges SNDD kam.
    """
    bb, nn = parse_location(loc)
    last_err: str | None = None
    for _ in range(max(1, retries)):
        synth.send_sysex(bd.build_sndr(bb=bb, nn=nn))
        for m in synth.receive(timeout=timeout):
            if m.type != "sysex":
                continue
            p = waldorf.parse_sysex(m.data)
            if p.get("cmd") != waldorf.CMD["sound_dump"]:
                continue
            raw = bytes([0xF0] + list(m.data) + [0xF7])
            try:
                parsed = bd.parse_sndd(raw)
            except ValueError as e:
                last_err = str(e)
                continue
            if not parsed["chk_ok"]:
                last_err = "Checksumme falsch"
                continue
            return parsed
        last_err = last_err or "kein SNDD empfangen (Timeout)"
    raise RuntimeError(f"kein gueltiges SNDD fuer {loc}: {last_err}")


def read_bank(synth: midi.Synth, banks, progress=None) -> dict:
    """Alle Locations der Bank(en) lesen. Nie Abbruch bei Einzelfehlern.

    Rueckgabe: {"sounds": {loc: parsed}, "errors": {loc: fehler}}.
    progress(loc, ok, parsed_or_err) wird pro Location aufgerufen.
    """
    sounds: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for bank in banks:
        bank = bank.strip().upper()
        if len(bank) != 1 or not "A" <= bank <= "Z":
            raise ValueError(f"ungueltige Bank: {bank!r}")
        for slot in range(1, 129):
            loc = f"{bank}{slot:03d}"
            try:
                parsed = read_sound(synth, loc)
                sounds[loc] = parsed
                if progress:
                    progress(loc, True, parsed)
            except Exception as e:  # noqa: BLE001 – Einzelfehler sammeln
                errors[loc] = str(e)
                if progress:
                    progress(loc, False, str(e))
    if not sounds and errors:
        raise RuntimeError(f"keine Sounds gelesen ({len(errors)} Fehler, z. B. {next(iter(errors.items()))})")
    return {"sounds": sounds, "errors": errors}


# ---- Konvertieren Blofeld -> qpat -----------------------------------------

def convert_parsed(parsed: dict, loc: str, out_dir, template_path=None) -> tuple[Path, int, list]:
    """parse_sndd-Ergebnis -> .qpat schreiben.

    Rueckgabe: (out_path, mapped_count, unmapped_liste).
    """
    template = qpat.load(template_path or TEMPLATE_QPAT)
    overrides, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    merged = qpat_map.apply_to_template(template, overrides, name=parsed["name"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in parsed["name"]).strip() or loc
    out_path = out_dir / f"{safe}_{loc}.qpat"
    out_path.write_bytes(qpat.build_qpat(
        merged["name"], merged["params"], creator=merged["creator"],
        description=merged["description"], categories=merged["categories"],
        version=merged["version"], sample_maps=merged.get("sample_maps")))
    return out_path, len(overrides), unmapped


# ---- Verbindungs-Check (ex step1) ------------------------------------------

def check_connection(do_audio: bool = False, note: int = 60, velocity: int = 100,
                     duration: float = 2.0) -> dict:
    """step1-Logik: Ports listen; pro Synth connect + Device-Inquiry (+ optional Pegelmessung).

    Rueckgabe: {"ports": {...}, "synths": {name: {"out_port", "in_port", "channel",
    "sysex": [[...], ...], "ok", ...}}}. Wirft RuntimeError, wenn ein Port fehlt.
    """
    result = {"ports": midi.list_ports(), "synths": {}}
    synths = {}
    try:
        for name in ("blofeld", "iridium"):
            synth = midi.connect(name)
            synths[name] = synth
            entry = {"out_port": synth.out_port_name, "in_port": synth.in_port_name,
                     "channel": synth.channel, "sysex": [], "other": []}
            synth.device_inquiry()
            for m in synth.receive(timeout=1.0):
                if m.type == "sysex":
                    entry["sysex"].append(list(m.data))
                else:
                    entry["other"].append(str(m))
            if do_audio:
                data, m = audio.play_and_measure(synth, audio.CHANNELS[name],
                                                 note=note, velocity=velocity, duration=duration)
                entry["samples"] = int(data.shape[1])
                entry["rms_dbfs"] = [float(x) for x in m["rms_dbfs"]]
                entry["peak_dbfs_list"] = [float(x) for x in m["peak_dbfs"]]
                entry["peak_dbfs"] = float(np.max(m["peak_dbfs"]))
                entry["ok"] = bool((m["peak_dbfs"] > -60.0).any())
            else:
                entry["ok"] = True
            result["synths"][name] = entry
    finally:
        for s in synths.values():
            s.close()
    return result


# ---- A/B-Messung (ex step4) ------------------------------------------------

def spectral_centroid(x: np.ndarray, sr: int = audio.SAMPLERATE) -> float:
    x = np.asarray(x, dtype=np.float64).mean(axis=0)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((f * X).sum() / max(X.sum(), 1e-12))


def band_energies(x: np.ndarray, sr: int = audio.SAMPLERATE, n_bands: int = 8,
                  f_lo: float = 40.0, f_hi: float = 12000.0) -> tuple[np.ndarray, np.ndarray]:
    """Log-spaced band energies (dB) + band edges. x: (channels, samples)."""
    x = np.asarray(x, dtype=np.float64).mean(axis=0)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    edges = np.geomspace(f_lo, f_hi, n_bands + 1)
    bands = []
    for i in range(n_bands):
        m = (f >= edges[i]) & (f < edges[i + 1])
        e = float(np.sqrt(np.sum(X[m] ** 2)))
        bands.append(20 * np.log10(max(e, 1e-12)))
    return np.array(bands), edges


def measure_ab(note: int = 36, dur: float = 3.0, label: str = "ab",
               rec_dir=None, sound_location: str | None = None) -> dict:
    """Spielt eine Note auf beiden Synths und misst A/B ueber das Scarlett.

    Macht vorher All Notes Off (CC123) auf allen 16 Kanaelen beider Synths.
    Speichert .npy + report.json nach rec_dir. Rueckgabe: report dict.
    """
    rec_dir = Path(rec_dir or RECORDINGS)
    rec_dir.mkdir(parents=True, exist_ok=True)
    with midi.connect("blofeld") as blo, midi.connect("iridium") as irr:
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
        time.sleep(0.5)
        blo.note_on(note=note, velocity=100)
        irr.note_on(note=note, velocity=100, channel=5)  # Part 1 = MIDI 6
        try:
            time.sleep(0.3)
            data = audio.record(duration=dur, channels=None)  # (20, samples)
        finally:
            blo.note_off(note=note)
            irr.note_off(note=note, channel=5)
            for ch in range(16):
                blo.control_change(123, 0, channel=ch)
                irr.control_change(123, 0, channel=ch)

    b_ch, i_ch = audio.CHANNELS["blofeld"], audio.CHANNELS["iridium"]
    blo_x, irr_x = data[b_ch, :], data[i_ch, :]
    mb, mi = audio.measure(blo_x), audio.measure(irr_x)
    pb, pi = float(np.max(mb["peak_dbfs"])), float(np.max(mi["peak_dbfs"]))
    cb, ci = spectral_centroid(blo_x), spectral_centroid(irr_x)
    bb, edges = band_energies(blo_x)
    ib, _ = band_energies(irr_x)
    ts = time.strftime("%Y%m%d_%H%M%S")
    blo_path = rec_dir / f"{label}_{ts}_blofeld.npy"
    irr_path = rec_dir / f"{label}_{ts}_iridium.npy"
    rep_path = rec_dir / f"{label}_{ts}_report.json"
    np.save(blo_path, blo_x)
    np.save(irr_path, irr_x)
    report = {
        "label": label, "sound_location": sound_location, "note": note, "dur": dur,
        "blofeld": {"peak_dbfs": pb, "rms_dbfs": float(np.max(mb["rms_dbfs"])), "centroid_hz": cb},
        "iridium": {"peak_dbfs": pi, "rms_dbfs": float(np.max(mi["rms_dbfs"])), "centroid_hz": ci},
        "band_edges_hz": edges.tolist(), "band_delta_db": (ib - bb).tolist(),
        "files": {"blofeld_npy": str(blo_path), "iridium_npy": str(irr_path),
                  "report": str(rep_path)},
    }
    rep_path.write_text(json.dumps(report, indent=2))
    return report
