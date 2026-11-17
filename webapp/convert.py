"""Upload -> Parse -> Konvertieren -> ZIP/Report (offline, ohne MIDI-Hardware).

Nutzt die pure-python-Module aus dem bloridium-Paket (blofeld_dump, qpat,
qpat_map, waldorf) per Dateipfad – so braucht der Docker-Container weder
numpy noch mido/python-rtmidi (bloridium/__init__.py wuerde die importieren).
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import matching

WEBAPP = Path(__file__).resolve().parent
REPO = WEBAPP.parent

# Versionierung des Conversion-Tools (UI-Titel, report.json, MANIFEST)
CONVERSION_VERSION = "0.3"


class UploadError(ValueError):
    """Ungueltiger Upload – wird von der App als 400 gerendert."""


def load_core() -> SimpleNamespace:
    """blofeld_dump/qpat/qpat_map/waldorf als Module laden (ohne Paket-__init__)."""
    env = os.environ.get("BLORIDIUM_CORE_DIR")
    candidates = [Path(env)] if env else []
    candidates += [WEBAPP / "core", REPO / "bloridium"]
    for d in candidates:
        if (d / "blofeld_dump.py").exists():
            mods = {}
            for name in ("blofeld_dump", "qpat", "qpat_map", "waldorf"):
                spec = importlib.util.spec_from_file_location(name, d / f"{name}.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mods[name] = mod
            return SimpleNamespace(**mods)
    raise RuntimeError("bloridium-Core-Module nicht gefunden "
                       "(BLORIDIUM_CORE_DIR oder <repo>/bloridium erwartet)")


def default_template_path() -> Path:
    env = os.environ.get("BLORIDIUM_TEMPLATE")
    if env:
        return Path(env)
    for c in (WEBAPP / "template_waveform.qpat", REPO / "docs" / "refs" / "qpat" / "template_waveform.qpat"):
        if c.exists():
            return c
    raise RuntimeError("qpat-Template nicht gefunden (BLORIDIUM_TEMPLATE setzen)")


def split_sysex_messages(data: bytes) -> list[bytes]:
    """.syx in einzelne SysEx-Nachrichten (F0..F7) zerlegen. Ohne F0: [data]."""
    if not data:
        return []
    if 0xF0 not in data:
        return [bytes(data)]
    msgs, i, n = [], 0, len(data)
    while i < n:
        if data[i] != 0xF0:
            i += 1
            continue
        j = data.find(0xF7, i + 1)
        msgs.append(bytes(data[i:j + 1]) if j != -1 else bytes(data[i:]))
        i = j + 1 if j != -1 else n
    return msgs


def location_str(bb: int, nn: int) -> str:
    """Wie workflow.location_str: (0x7F, 0) -> 'edit', sonst z. B. (0, 42) -> 'A043'."""
    if bb == 0x7F and nn == 0:
        return "edit"
    return f"{chr(ord('A') + bb)}{nn + 1:03d}"


def parse_upload(filename: str, data: bytes) -> dict:
    """Upload parsen: .hex dekodieren, SysEx splitten, SNDDs parsen.

    Rueckgabe: {"sounds": [parse_sndd-Ergebnis...], "errors": [...], "skipped": int}
    """
    if filename.lower().endswith(".hex"):
        try:
            data = bytes.fromhex("".join(data.decode("ascii").split()))
        except (UnicodeDecodeError, ValueError) as e:
            raise UploadError(f".hex-Datei ungueltig: {e}") from None
    core = load_core()
    sounds, errors, skipped = [], [], 0
    for idx, msg in enumerate(split_sysex_messages(data)):
        try:
            parsed = core.blofeld_dump.parse_sndd(msg)
        except ValueError:
            skipped += 1  # Fremd-Nachricht (z. B. MULD, Identity) – nicht SNDD
            continue
        if not parsed["chk_ok"]:
            errors.append({"index": idx, "error": "Checksumme falsch"})
            continue
        sounds.append(parsed)
    return {"sounds": sounds, "errors": errors, "skipped": skipped}


def safe_name(name: str, loc: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip() or loc
    return safe


def convert_sound(core, template: dict, parsed: dict, loc: str) -> dict:
    """Ein parse_sndd-Ergebnis -> .qpat-Bytes (identisch zu workflow.convert_parsed)."""
    overrides, unmapped = core.qpat_map.blofeld_to_qpat_params(parsed)
    merged = core.qpat_map.apply_to_template(template, overrides, name=parsed["name"])
    qbytes = core.qpat.build_qpat(
        merged["name"], merged["params"], creator=merged["creator"],
        description=merged["description"], categories=merged["categories"],
        version=core.qpat.PRESET_VERSION,  # v14, Zielgeraet OS4
        sample_maps=merged.get("sample_maps"))
    return {"loc": loc, "name": parsed["name"], "qpat_bytes": qbytes,
            "mapped": len(overrides), "unmapped": unmapped}


def process_upload(filename: str, data: bytes, data_dir) -> dict:
    """Komplette Pipeline. Schreibt <data_dir>/<token>/{result.zip,report.json}.

    Rueckgabe: report-dict (inkl. token, zip_name, sounds mit score + features).
    Wirft UploadError bei ungueltigem/leerem Upload.
    """
    if not data:
        raise UploadError("leere Datei")
    core = load_core()
    template = core.qpat.load(default_template_path())
    parsed_up = parse_upload(filename, data)
    if not parsed_up["sounds"]:
        detail = "; ".join(f"Msg {e['index']}: {e['error']}" for e in parsed_up["errors"][:3])
        raise UploadError(
            f"keine gueltige Blofeld-SNDD-Nachricht gefunden "
            f"({len(parsed_up['errors'])} Checksum-Fehler, {parsed_up['skipped']} Fremd-Nachrichten)"
            + (f" – {detail}" if detail else ""))

    token = uuid.uuid4().hex
    tdir = Path(data_dir) / token
    tdir.mkdir(parents=True, exist_ok=True)

    zip_buf = io.BytesIO()
    manifest_lines = [
        f"# Bloridium Upload-Paket – {filename}",
        f"erstellt: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Sounds: {len(parsed_up['sounds'])}, Fehler: {len(parsed_up['errors'])}, "
        f"uebersprungen: {parsed_up['skipped']}",
        "",
        "Am Iridium: USB-Stick/SD -> Load > Actions > Import (Favorites Bank 6, CC0=6 + PC).",
        f"Conversion v{CONVERSION_VERSION}; Score = similarity v{matching.SIMILARITY_VERSION} "
        "(deterministischer Platzhalter, siehe webapp/matching.py).",
        "",
        "| Location | Name | qpat-Datei | gemappt | unmapped | Score |",
        "|---|---|---|---|---|---|",
    ]
    sounds_report = []
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for parsed in parsed_up["sounds"]:
            loc = location_str(parsed["bb"], parsed["nn"])
            conv = convert_sound(core, template, parsed, loc)
            est = matching.estimate_match(parsed, conv["unmapped"], core.qpat_map)
            fname = f"{loc}_{safe_name(conv['name'], loc)}.qpat"
            zf.writestr(fname, conv["qpat_bytes"])
            manifest_lines.append(
                f"| {loc} | {conv['name']} | `{fname}` | {conv['mapped']} "
                f"| {len(conv['unmapped'])} | {est['score']} |")
            sounds_report.append({
                "location": loc, "name": conv["name"],
                "category": str(parsed["params"].get("Category", "")),
                "chk_ok": parsed["chk_ok"], "qpat_file": fname,
                "mapped": conv["mapped"], "unmapped": conv["unmapped"],
                "score": est["score"], "score_parts": est["parts"],
                "penalties": est["penalties"],
                # Feature-Vektor fuer die spaetere (gelernte) Matching-Funktion:
                "features": {"params": parsed["params"]},
            })
        zf.writestr("MANIFEST.md", "\n".join(manifest_lines) + "\n")
        report = {
            "source_file": filename, "token": token,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "conversion_version": f"v{CONVERSION_VERSION}",
            "similarity_version": f"v{matching.SIMILARITY_VERSION}",
            "matcher": f"deterministic-placeholder-v{matching.SIMILARITY_VERSION} (webapp/matching.py)",
            "num_sounds": len(sounds_report), "num_errors": len(parsed_up["errors"]),
            "skipped_messages": parsed_up["skipped"],
            "avg_score": round(sum(s["score"] for s in sounds_report) / len(sounds_report), 1)
                         if sounds_report else None,
            "sounds": sounds_report, "errors": parsed_up["errors"],
        }
        zf.writestr("report.json", json.dumps(report, indent=2, ensure_ascii=False))

    zip_name = f"bloridium_{Path(filename).stem}_{token[:8]}.zip"
    (tdir / "result.zip").write_bytes(zip_buf.getvalue())
    (tdir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    report["zip_name"] = zip_name
    report["zip_path"] = str(tdir / "result.zip")
    return report
