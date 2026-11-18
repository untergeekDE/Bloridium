"""Workflow library - importable logic from the step scripts.

No prints in core functions (progress callback instead); the CLI and the
wrapper scripts format the output. Hardware access is read-only;
All Notes Off (CC123) before every measurement on all channels of both synths.

Pipeline (why these functions exist in this order):
  dump (read_sound/read_bank: SNDR -> SNDD via SysEx, stored as .bin + DB row)
    -> convert (convert_parsed: SNDD params -> .qpat overrides via qpat_map,
       written into transfer/ for USB-stick import on the Iridium)
    -> transfer (manual: copy .qpat to USB stick/SD, Load>Actions>Import on device)
    -> measure (record_ab_pair/measure_ab: both synths play the same note,
       Scarlett records both, report + .npy in recordings/, optional sim score)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from . import audio, blofeld_dump as bd, midi, qpat, qpat_map, sim_embed, waldorf

# repo root (worktree-safe): two levels above this file
REPO = Path(__file__).resolve().parent.parent
DUMPS = REPO / "dumps"
TRANSFER = REPO / "transfer"
RECORDINGS = REPO / "recordings"
TEMPLATE_QPAT = REPO / "docs" / "refs" / "qpat" / "template_waveform.qpat"


# ---- locations ------------------------------------------------------------

def parse_location(loc: str) -> tuple[int, int]:
    """'A043' -> (0x00, 0x2A); 'edit' -> (0x7F, 0x00). ValueError on invalid."""
    loc = loc.strip()
    if loc.lower() in ("edit", "puffer", ""):
        return 0x7F, 0x00
    loc = loc.upper()
    bank = ord(loc[0]) - ord("A") if loc else -1
    try:
        num = int(loc[1:]) - 1
    except ValueError:
        raise ValueError(f"invalid location: {loc!r} (e.g. A001..Z128)") from None
    if not (0 <= bank <= 0x19 and 0 <= num <= 0x7F):
        raise ValueError(f"invalid location: {loc!r} (e.g. A001..Z128)")
    return bank, num


def location_str(bb: int, nn: int) -> str:
    if bb == 0x7F and nn == 0:
        return "edit"
    return f"{chr(ord('A') + bb)}{nn + 1:03d}"


# ---- dump files -----------------------------------------------------------

def load_sndd_file(path) -> bytes:
    """Load SNDD from .bin (raw) or .hex (hex text); incl. F0/F7."""
    p = Path(path)
    if p.suffix.lower() == ".hex":
        return bytes.fromhex(p.read_text().replace(" ", "").replace("\n", ""))
    return p.read_bytes()


# ---- read Blofeld live ----------------------------------------------------

def read_sound(synth: midi.Synth, loc: str, timeout: float = 4.0,
               retries: int = 2) -> dict:
    """SNDR -> SNDD -> parse_sndd. Retry on timeout/checksum error.

    Returns: parse_sndd result (dict with name, params, sdata, ...).
    Raises RuntimeError if no valid SNDD arrived after all retries.
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
                last_err = "checksum mismatch"
                continue
            return parsed
        last_err = last_err or "no SNDD received (timeout)"
    raise RuntimeError(f"no valid SNDD for {loc}: {last_err}")


def read_bank(synth: midi.Synth, banks, progress=None) -> dict:
    """Read all locations of the bank(s). Never abort on individual errors.

    Returns: {"sounds": {loc: parsed}, "errors": {loc: error}}.
    progress(loc, ok, parsed_or_err) is called per location.
    """
    sounds: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for bank in banks:
        bank = bank.strip().upper()
        if len(bank) != 1 or not "A" <= bank <= "Z":
            raise ValueError(f"invalid bank: {bank!r}")
        for slot in range(1, 129):
            loc = f"{bank}{slot:03d}"
            try:
                parsed = read_sound(synth, loc)
                sounds[loc] = parsed
                if progress:
                    progress(loc, True, parsed)
            except Exception as e:  # noqa: BLE001 - collect individual errors
                errors[loc] = str(e)
                if progress:
                    progress(loc, False, str(e))
    if not sounds and errors:
        raise RuntimeError(f"no sounds read ({len(errors)} errors, e.g. {next(iter(errors.items()))})")
    return {"sounds": sounds, "errors": errors}


# ---- convert Blofeld -> qpat -----------------------------------------------

def convert_parsed(parsed: dict, loc: str, out_dir, template_path=None) -> tuple[Path, int, list]:
    """parse_sndd result -> write .qpat.

    Returns: (out_path, mapped_count, unmapped_list).
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
        version=qpat.PRESET_VERSION,  # target device OS4 expects v14 (template is v8)
        sample_maps=merged.get("sample_maps")))
    return out_path, len(overrides), unmapped


# ---- connection check (ex step1) -------------------------------------------

def _ckw(config_path) -> dict:
    """config_path kwarg only when explicitly set (keeps monkeypatched fakes working)."""
    return {"config_path": config_path} if config_path is not None else {}


def check_connection(do_audio: bool = False, note: int = 60, velocity: int = 100,
                     duration: float = 2.0, config_path=None) -> dict:
    """step1 logic: list ports; per synth connect + device inquiry (+ optional level measurement).

    Ports/channels come from the YAML config (`config_path`, default: ./bloridium.yaml).
    Returns: {"ports": {...}, "synths": {name: {"out_port", "in_port", "channel",
    "sysex": [[...], ...], "ok", ...}}}. Raises RuntimeError if a port is missing.
    """
    result = {"ports": midi.list_ports(), "synths": {}}
    a_settings = audio.settings(config_path)
    synths = {}
    try:
        for name in ("blofeld", "iridium"):
            synth = midi.connect(name, **_ckw(config_path))
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
                data, m = audio.play_and_measure(synth, a_settings["channels"][name],
                                                 note=note, velocity=velocity, duration=duration,
                                                 **_ckw(config_path))
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


# ---- A/B measurement (ex step4) --------------------------------------------

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


def record_ab_pair(note: int = 36, dur: float = 3.0, config_path=None):
    """Plays a note on both synths (part 1 = ch6 on the Iridium, monophonic) and
    records via the audio interface. All Notes Off (CC123) beforehand on all 16 channels.

    Returns: (blo_x, irr_x) - the stereo rows (2, samples) of the configured channels each.
    """
    with midi.connect("blofeld", **_ckw(config_path)) as blo, \
            midi.connect("iridium", **_ckw(config_path)) as irr:
        for s in (blo, irr):
            for ch in range(16):
                s.control_change(123, 0, channel=ch)
        time.sleep(0.5)
        blo.note_on(note=note, velocity=100)
        irr.note_on(note=note, velocity=100, channel=5)  # Part 1 = MIDI 6
        try:
            time.sleep(0.3)
            data = audio.record(duration=dur, channels=None, **_ckw(config_path))  # (raw, samples)
        finally:
            blo.note_off(note=note)
            irr.note_off(note=note, channel=5)
            for ch in range(16):
                blo.control_change(123, 0, channel=ch)
                irr.control_change(123, 0, channel=ch)
    a_ch = audio.settings(config_path)["channels"]
    b_ch, i_ch = a_ch["blofeld"], a_ch["iridium"]
    return data[b_ch, :], data[i_ch, :]


def measure_ab(note: int = 36, dur: float = 3.0, label: str = "ab",
               rec_dir=None, sound_location: str | None = None, *,
               embed: bool = False, llm: bool = False,
               models_dir=None, strict: bool = False, config_path=None) -> dict:
    """Plays a note on both synths and measures A/B via the Scarlett.

    Saves .npy + report.json to rec_dir. Returns: report dict.
    embed/llm (phase B): report additionally gets keys "sim" (phase A + combined),
    "embed" ({embed_cos, embed_score}|None) and "llm" (verdict|None) - as a JSON blob
    in report_json, without a DB schema change. log_path=None: no sim_log.jsonl entry.
    """
    rec_dir = Path(rec_dir or RECORDINGS)
    rec_dir.mkdir(parents=True, exist_ok=True)
    blo_x, irr_x = record_ab_pair(note, dur, **_ckw(config_path))
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
    if embed or llm:
        clap, ollama = sim_embed.build_backends(
            models_dir or sim_embed.DEFAULT_MODELS_DIR, embed, llm)
        bx = np.asarray(blo_x, dtype=np.float64).mean(axis=0)
        ix = np.asarray(irr_x, dtype=np.float64).mean(axis=0)
        r = sim_embed.score_pair_embed(
            bx, ix, sr=audio.SAMPLERATE,
            meta={"label": label, "sound_location": sound_location, "note": note,
                  "mode": "ab"},
            log_path=None, clap=clap, ollama=ollama, use_llm=llm, strict=strict)
        report["sim"] = {k: r[k] for k in ("score", "spec_cos", "env_dtw", "verdict",
                                           "combined", "backend_error")}
        report["embed"] = ({"embed_cos": r["embed_cos"], "embed_score": r["embed_score"]}
                           if r["embed_score"] is not None else None)
        report["llm"] = r["llm"]

    rep_path.write_text(json.dumps(report, indent=2))
    return report
