"""Upload -> parse -> convert -> ZIP/report (offline, without MIDI hardware).

Uses the pure-Python modules from the bloridium package (blofeld_dump, qpat,
qpat_map, waldorf, prognose) via file path as a synthetic package – so the
container needs no mido/python-rtmidi (bloridium/__init__.py would import them
via audio/midi); prognose needs numpy only.
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
import midi_file

WEBAPP = Path(__file__).resolve().parent
REPO = WEBAPP.parent

# Versioning (UI title, report.json, MANIFEST): one version, see bloridium/version.py
CONVERSION_VERSION = matching.VERSION


class UploadError(ValueError):
    """Invalid upload – rendered by the app as HTTP 400."""


def load_core() -> SimpleNamespace:
    """Load the core modules under the real package name "bloridium" (without
    executing bloridium/__init__.py, which would pull in audio/midi -> mido).

    The package name MUST be "bloridium": prognose.py does `from . import
    blofeld_dump`, and the pickled RF model references bloridium.prognose.*
    classes, so unpickling only works under the real package name.
    prognose is optional – without it the RF prognosis is off.
    """
    import sys
    import types

    env = os.environ.get("BLORIDIUM_CORE_DIR")
    candidates = [Path(env)] if env else []
    candidates += [WEBAPP / "core", REPO / "bloridium"]
    for d in candidates:
        if (d / "blofeld_dump.py").exists():
            pkg = sys.modules.get("bloridium")
            if pkg is None or not hasattr(pkg, "__path__"):
                pkg = types.ModuleType("bloridium")
                pkg.__path__ = [str(d)]
                sys.modules["bloridium"] = pkg
            elif str(d) not in pkg.__path__:
                pkg.__path__.append(str(d))
            mods = {}
            for name in ("blofeld_dump", "qpat", "qpat_map", "waldorf", "prognose"):
                full = f"bloridium.{name}"
                if full in sys.modules:  # real package already imported -> reuse
                    mods[name] = sys.modules[full]
                    continue
                f = d / f"{name}.py"
                if not f.exists():
                    if name == "prognose":
                        continue  # optional: RF prognosis disabled without it
                    raise RuntimeError(f"core module missing: {f}")
                spec = importlib.util.spec_from_file_location(full, f)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[full] = mod
                spec.loader.exec_module(mod)
                mods[name] = mod
            return SimpleNamespace(**mods)
    raise RuntimeError("bloridium core modules not found "
                       "(BLORIDIUM_CORE_DIR or <repo>/bloridium expected)")


def default_template_path() -> Path:
    env = os.environ.get("BLORIDIUM_TEMPLATE")
    if env:
        return Path(env)
    for c in (WEBAPP / "template_waveform.qpat", REPO / "docs" / "refs" / "qpat" / "template_waveform.qpat"):
        if c.exists():
            return c
    raise RuntimeError("qpat template not found (set BLORIDIUM_TEMPLATE)")


def split_sysex_messages(data: bytes) -> list[bytes]:
    """Split .syx into individual SysEx messages (F0..F7). Without F0: [data]."""
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
    """Like workflow.location_str: (0x7F, 0) -> 'edit', else e.g. (0, 42) -> 'A043'."""
    if bb == 0x7F and nn == 0:
        return "edit"
    return f"{chr(ord('A') + bb)}{nn + 1:03d}"


def upload_messages(filename: str, data: bytes) -> list[bytes]:
    """Complete SysEx messages (F0..F7) contained in the upload.

    .mid/.midi (Standard MIDI File, e.g. a bank exported from Sysex Librarian):
    SysEx events are extracted from the SMF track data (notes/meta are skipped).
    Everything else (.syx/.bin): raw scan for F0..F7.
    """
    if midi_file.is_smf(data) or filename.lower().endswith((".mid", ".midi")):
        try:
            return midi_file.extract_sysex(data)
        except midi_file.MidiFileError as e:
            raise UploadError(f"invalid MIDI file: {e}") from None
    return split_sysex_messages(data)


def parse_upload(filename: str, data: bytes) -> dict:
    """Parse upload: decode .hex, extract SysEx (.mid via SMF, else raw), parse SNDDs.

    Returns: {"sounds": [parse_sndd results...], "errors": [...], "skipped": int}
    """
    if filename.lower().endswith(".hex"):
        try:
            data = bytes.fromhex("".join(data.decode("ascii").split()))
        except (UnicodeDecodeError, ValueError) as e:
            raise UploadError(f"invalid .hex file: {e}") from None
    core = load_core()
    sounds, errors, skipped = [], [], 0
    for idx, msg in enumerate(upload_messages(filename, data)):
        try:
            parsed = core.blofeld_dump.parse_sndd(msg)
        except ValueError:
            skipped += 1  # foreign message (e.g. MULD, Identity) – not SNDD
            continue
        if not parsed["chk_ok"]:
            errors.append({"index": idx, "error": "checksum wrong"})
            continue
        sounds.append(parsed)
    return {"sounds": sounds, "errors": errors, "skipped": skipped}


def safe_name(name: str, loc: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip() or loc
    return safe


IGNORED_PREFIX = "Ignored: "


def split_unmapped(unmapped: list[str]) -> tuple[list[str], list[str]]:
    """Separate deliberate ignores from real mapping gaps.

    qpat_map marks parameters that the Blofeld itself ignores (e.g. PWM on a
    sawtooth) with `Ignored: …`. Those must not show up as "not in MIDI map".
    """
    ignored = [u for u in unmapped if u.startswith(IGNORED_PREFIX)]
    gaps = [u for u in unmapped if not u.startswith(IGNORED_PREFIX)]
    return gaps, ignored


def convert_sound(core, template: dict, parsed: dict, loc: str) -> dict:
    """One parse_sndd result -> .qpat bytes (identical to workflow.convert_parsed)."""
    overrides, unmapped_all = core.qpat_map.blofeld_to_qpat_params(parsed)
    unmapped, ignored = split_unmapped(unmapped_all)
    merged = core.qpat_map.apply_to_template(template, overrides, name=parsed["name"])
    qbytes = core.qpat.build_qpat(
        merged["name"], merged["params"], creator=merged["creator"],
        description=merged["description"], categories=merged["categories"],
        version=core.qpat.PRESET_VERSION,  # v14, target device OS4
        sample_maps=merged.get("sample_maps"))
    return {"loc": loc, "name": parsed["name"], "qpat_bytes": qbytes,
            "mapped": len(overrides), "unmapped": unmapped, "ignored": ignored}


def process_upload(filename: str, data: bytes, data_dir, model_path=None) -> dict:
    """Full pipeline. Writes <data_dir>/<token>/{result.zip,report.json}.

    model_path: RF model for the score prognosis (None -> auto-detect via
    matching.resolve_model_path; missing model -> deterministic placeholder).

    Returns: report dict (incl. token, zip_name, sounds with score + features).
    Raises UploadError on invalid/empty upload.
    """
    if not data:
        raise UploadError("empty file")
    core = load_core()
    template = core.qpat.load(default_template_path())
    bundle, resolved_model = matching.load_model_bundle(core, model_path)
    parsed_up = parse_upload(filename, data)
    if not parsed_up["sounds"]:
        detail = "; ".join(f"Msg {e['index']}: {e['error']}" for e in parsed_up["errors"][:3])
        raise UploadError(
            f"no valid Blofeld SNDD message found "
            f"({len(parsed_up['errors'])} checksum errors, {parsed_up['skipped']} foreign messages)"
            + (f" – {detail}" if detail else ""))

    token = uuid.uuid4().hex
    tdir = Path(data_dir) / token
    tdir.mkdir(parents=True, exist_ok=True)

    matcher_desc = (f"rf-prognose-v{matching.SIMILARITY_VERSION}" if bundle is not None
                    else f"deterministic-placeholder-v{matching.PLACEHOLDER_VERSION}")
    sim_version = matching.SIMILARITY_VERSION if bundle is not None else matching.PLACEHOLDER_VERSION

    zip_buf = io.BytesIO()
    manifest_lines = [
        f"# Bloridium upload package – {filename}",
        f"created: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Sounds: {len(parsed_up['sounds'])}, errors: {len(parsed_up['errors'])}, "
        f"skipped: {parsed_up['skipped']}",
        "",
        "On the Iridium: USB stick/SD -> Load > Actions > Import (Favorites Bank 6, CC0=6 + PC).",
        f"Conversion v{CONVERSION_VERSION}; Score = {matcher_desc}"
        + (f" (model: {resolved_model.name})" if resolved_model else ""),
        "",
        "| Location | Name | qpat file | not in MIDI map | Score |",
        "|---|---|---|---|---|",
    ]
    sounds_report = []
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for parsed in parsed_up["sounds"]:
            loc = location_str(parsed["bb"], parsed["nn"])
            conv = convert_sound(core, template, parsed, loc)
            est = matching.score_sound(parsed, conv["unmapped"], core.qpat_map, core, bundle)
            fname = f"{loc}_{safe_name(conv['name'], loc)}.qpat"
            zf.writestr(fname, conv["qpat_bytes"])
            manifest_lines.append(
                f"| {loc} | {conv['name']} | `{fname}` | {len(conv['unmapped'])} "
                f"| {est['score']} |")
            sounds_report.append({
                "location": loc, "name": conv["name"],
                "category": str(parsed["params"].get("Category", "")),
                "chk_ok": parsed["chk_ok"], "qpat_file": fname,
                "mapped": conv["mapped"], "unmapped": conv["unmapped"],
                "ignored": conv["ignored"],
                "score": est["score"], "std": est.get("std"), "matcher": est["matcher"],
                "score_parts": est.get("parts"), "penalties": est.get("penalties"),
                # Feature vector for (re-)training the RF prognosis:
                "features": {"params": parsed["params"]},
            })
        zf.writestr("MANIFEST.md", "\n".join(manifest_lines) + "\n")
        report = {
            "source_file": filename, "token": token,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "conversion_version": f"v{CONVERSION_VERSION}",
            "similarity_version": f"v{sim_version}",
            "matcher": f"{matcher_desc} (webapp/matching.py)",
            "model": str(resolved_model) if bundle is not None else None,
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
