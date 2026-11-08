"""Bloridium CLI – Terminal-Tool Phase 1 (klassische Subcommands).

Subcommands (Design: docs/superpowers/specs/2026-11-08-bloridium-cli-design.md):
  status | bank read/import/list/show | convert | ab | qpat info | edit

Exit-Codes: 0 ok, 1 Fehler, 2 Hardware nicht erreichbar (Port-Liste in stderr).
Safety: Tool aendert nie Geraeteeinstellungen; All Notes Off vor Messungen;
CC7=0 ist stumm am Iridium; Iridium-Import nur per .qpat auf USB-Stick/SD.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from . import audio, blofeld_dump as bd, db, editor, midi, qpat, workflow

REPO = workflow.REPO


def default_db_path() -> Path:
    return Path(os.environ.get("BLORIDIUM_DB") or (REPO / "bloridium.db"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bloridium",
        description="Blofeld -> Iridium Sound-Transfer (Terminal-Tool, Phase 1)",
    )
    p.add_argument("--db", default=None,
                   help="Pfad zur SQLite-Bank-DB (Default: $BLORIDIUM_DB oder <repo>/bloridium.db)")
    p.add_argument("--json", action="store_true", help="Ausgabe als JSON (wo unterstuetzt)")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("status", help="MIDI-Ports + Identity; --audio misst zusaetzlich Pegel (Scarlett)")
    sp.add_argument("--audio", action="store_true", help="ex step1: Note spielen + Pegel messen")
    sp.set_defaults(func=cmd_status)

    bp = sub.add_parser("bank", help="Blofeld-Bank-Manager (SQLite-Bank + dumps/banks/)")
    bsub = bp.add_subparsers(dest="bank_cmd", required=True)
    br = bsub.add_parser("read", help="Bank(en) live per SysEx auslesen (z. B. bank read A)")
    br.add_argument("banks", nargs="+", help="Bank-Buchstaben, z. B. A oder A B")
    br.add_argument("--only", default=None, help="nur diese Locations, z. B. --only A043,A044")
    br.add_argument("--banks-dir", default=None, help="Ziel fuer stabile .bin-Kopien (Default: dumps/banks/)")
    br.set_defaults(func=cmd_bank_read)
    bi = bsub.add_parser("import", help="OFFLINE: vorhandene SNDD-Dumps aus DIR in die Bank importieren")
    bi.add_argument("dir", help="Verzeichnis mit blofeld_sndd_*.bin/.hex")
    bi.add_argument("--banks-dir", default=None)
    bi.set_defaults(func=cmd_bank_import)
    bl = bsub.add_parser("list", help="Sounds der Bank auflisten (aus DB)")
    bl.add_argument("bank", nargs="?", default=None)
    bl.add_argument("--grep", default=None, help="Filter auf Name/Location (case-insensitive)")
    bl.set_defaults(func=cmd_bank_list)
    bs = bsub.add_parser("show", help="geparste Parameter eines Sounds anzeigen")
    bs.add_argument("loc", help="z. B. A043")
    bs.set_defaults(func=cmd_bank_show)

    cv = sub.add_parser("convert", help="Blofeld-Sound -> Iridium-.qpat (transfer/)")
    cv.add_argument("loc", help="z. B. A043 oder edit")
    cv.add_argument("--dump", default=None, help="OFFLINE: SNDD aus Datei statt live lesen")
    cv.add_argument("--out", default=None, help="Zielverzeichnis (Default: transfer/)")
    cv.add_argument("--template", default=None, help="qpat-Template (Default: docs/refs/qpat/template_waveform.qpat)")
    cv.set_defaults(func=cmd_convert)

    ab = sub.add_parser("ab", help="A/B-Klangmessung Blofeld (In3/4) vs Iridium (In5/6)")
    ab.add_argument("--note", type=int, default=36)
    ab.add_argument("--dur", type=float, default=3.0)
    ab.add_argument("--label", default="ab")
    ab.add_argument("--sound", default=None, help="Blofeld-Location, mit der der Run verknuepft wird")
    ab.add_argument("--list", action="store_true", help="statt messen: Runs auflisten")
    ab.add_argument("--diff", nargs=2, metavar=("ID1", "ID2"), default=None, help="zwei Runs vergleichen")
    ab.add_argument("--rec-dir", default=None, help="Ziel fuer .npy/.json (Default: recordings/)")
    ab.set_defaults(func=cmd_ab)

    qp = sub.add_parser("qpat", help=".qpat-Dateien inspizieren/registrieren")
    qsub = qp.add_subparsers(dest="qpat_cmd", required=True)
    qi = qsub.add_parser("info", help="parse + Roundtrip-Check + Parameter-Uebersicht")
    qi.add_argument("file")
    qi.add_argument("--register", action="store_true", help="in qpats-Tabelle eintragen")
    qi.set_defaults(func=cmd_qpat_info)

    ed = sub.add_parser("edit", help="Iridium-Editor: .qpat-Parameter bearbeiten")
    ed.add_argument("file")
    g = ed.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="Parameter-Tabelle")
    g.add_argument("--show", metavar="KEY")
    g.add_argument("--set", metavar="KEY=VALUE", help="Wert setzen (0..1); ohne --save in-place mit .bak")
    g.add_argument("--diff", metavar="OTHER", help="gegen andere .qpat diffen")
    ed.add_argument("--grep", default=None, help="Filter fuer --list")
    ed.add_argument("--display", default=None, help="Display-String beim --set")
    ed.add_argument("--save", default=None, metavar="OUT", help="statt in-place nach OUT schreiben")
    ed.set_defaults(func=cmd_edit)

    return p


# ---- Helfer ----------------------------------------------------------------

def _emit(args, data, text_fn):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, default=str))
    else:
        text_fn()


def _db(args):
    return db.connect(args.db or default_db_path())


def _connect_or_exit2(name: str):
    """midi.connect; bei Fehler Port-Liste nach stderr und None (Caller -> return 2)."""
    try:
        return midi.connect(name)
    except RuntimeError as e:
        ports = midi.list_ports()
        print(f"FEHLER: {e}", file=sys.stderr)
        print(f"verfuegbare MIDI-Ports OUT: {ports['out']}", file=sys.stderr)
        print(f"verfuegbare MIDI-Ports IN : {ports['in']}", file=sys.stderr)
        return None


def _store_sound(conn, loc: str, parsed: dict, banks_dir: Path) -> str:
    """Stabile .bin-Kopie unter banks_dir/<Bank>/<LOC>.bin + DB-Upsert. -> sndd_path"""
    bb, nn = workflow.parse_location(loc)
    raw = bytes([0xF0]) + bytes(bd.build_sndd(parsed["sdata"], bb=bb, nn=nn)) + bytes([0xF7])
    bank = workflow.location_str(bb, nn)[0] if loc.lower() != "edit" else "edit"
    dest = Path(banks_dir) / bank / f"{loc.upper() if loc.lower() != 'edit' else 'edit'}.bin"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    from datetime import datetime, timezone
    pj = dict(parsed)
    pj["sdata"] = parsed["sdata"].hex()  # bytes -> hex, damit JSON-serialisierbar
    db.upsert_sound(conn, {
        "location": loc.upper() if loc.lower() != "edit" else "edit",
        "bank": bank, "slot": nn + 1, "name": parsed["name"],
        "category": str(parsed["params"].get("Category", "")),
        "sndd_path": str(dest), "parsed_json": pj,
        "dumped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "import",
    })
    return str(dest)


_LOC_RE = re.compile(r"blofeld_sndd_([A-Za-z]\d{3}|edit)(?:_|$)", re.IGNORECASE)


# ---- status ----------------------------------------------------------------

def cmd_status(args) -> int:
    ports = midi.list_ports()
    print("Verfuegbare MIDI-Ports:")
    for p in ports["out"]:
        print(f"  OUT: {p}")
    for p in ports["in"]:
        print(f"  IN : {p}")
    results = {}
    synths = {}
    try:
        for name in ("blofeld", "iridium"):
            synth = _connect_or_exit2(name)
            if synth is None:
                return 2
            synths[name] = synth
            print(f"\n=== {name.upper()} ===")
            print(f"  MIDI Out : {synth.out_port_name}  Kanal {synth.channel + 1} (1-basiert)")
            synth.device_inquiry()
            for m in synth.receive(timeout=1.0):
                if m.type == "sysex":
                    info = __import__("bloridium.waldorf", fromlist=["identity_reply_info"]).identity_reply_info(m.data)
                    print(f"  MIDI <- Identity Reply: {info}" if info else f"  MIDI <- SysEx {bytes([0xF0, *m.data, 0xF7]).hex(' ')}")
            if args.audio:
                import numpy as np
                data, m = audio.play_and_measure(synth, audio.CHANNELS[name], note=60, velocity=100, duration=2.0)
                peak = float(np.max(m["peak_dbfs"]))
                print(f"  Audio In {audio.CHANNELS[name]}: Peak {peak:.1f} dBFS -> {'OK' if peak > -60 else 'KEIN TON'}")
                results[name] = peak > -60.0
            else:
                results[name] = True
    finally:
        for s in synths.values():
            s.close()
    ok = all(results.values())
    print("\n=== Zusammenfassung ===")
    for name, r in results.items():
        print(f"  {name:9s}: {'VERBUNDEN' + (', Sound messbar' if args.audio and r else '') if r else 'PROBLEM'}")
    return 0 if ok else 1


# ---- bank ------------------------------------------------------------------

def cmd_bank_read(args) -> int:
    conn = _db(args)
    banks_dir = Path(args.banks_dir) if args.banks_dir else (REPO / "dumps" / "banks")
    synth = _connect_or_exit2("blofeld")
    if synth is None:
        return 2
    if synth.inp is None:
        print("WARNUNG: Blofeld-Rueckkanal nicht verfuegbar – SNDD-Antworten koennen fehlen.", file=sys.stderr)
    only = None
    if args.only:
        only = [x.strip().upper() for x in args.only.split(",") if x.strip()]
    locs = []
    for bank in args.banks:
        bank = bank.strip().upper()
        if only:
            locs += [l for l in only if l.startswith(bank)]
        else:
            locs += [f"{bank}{slot:03d}" for slot in range(1, 129)]
    ok, fail = 0, 0
    try:
        for loc in locs:
            try:
                parsed = workflow.read_sound(synth, loc)
                _store_sound(conn, loc, parsed, banks_dir)
                ok += 1
                print(f"  {loc}: {parsed['name']!r}")
            except Exception as e:  # noqa: BLE001
                fail += 1
                print(f"  {loc}: FEHLER {e}", file=sys.stderr)
    finally:
        synth.close()
    print(f"bank read: {ok} ok, {fail} Fehler (stabile Kopien: {banks_dir})")
    if ok == 0:
        print("kein Sound gelesen – Blofeld erreichbar? (Port/Kanal 5, Single Mode)", file=sys.stderr)
        return 2
    return 0


def cmd_bank_import(args) -> int:
    conn = _db(args)
    banks_dir = Path(args.banks_dir) if args.banks_dir else (REPO / "dumps" / "banks")
    src = Path(args.dir)
    files = sorted([p for p in src.glob("blofeld_sndd_*.bin")] + [p for p in src.glob("blofeld_sndd_*.hex")])
    ok, skipped = 0, 0
    for f in files:
        m = _LOC_RE.search(f.name)
        if not m:
            skipped += 1
            continue
        loc = m.group(1).upper()
        parsed = bd.parse_sndd(workflow.load_sndd_file(f))
        _store_sound(conn, loc, parsed, banks_dir)
        ok += 1
        print(f"  {f.name} -> {loc}: {parsed['name']!r}")
    print(f"bank import: {ok} importiert, {skipped} ohne Location uebersprungen (aus {src})")
    return 0 if ok else 1


def cmd_bank_list(args) -> int:
    conn = _db(args)
    rows = db.list_sounds(conn, bank=args.bank, grep=args.grep)
    for r in rows:
        r["missing"] = not (r.get("sndd_path") and Path(r["sndd_path"]).exists())

    def text():
        print(f"{'LOC':6s} {'NAME':32s} {'KAT':8s} DATEI")
        for r in rows:
            print(f"{r['location']:6s} {r['name'][:32]:32s} {str(r.get('category') or '')[:8]:8s} "
                  f"{'ok' if not r['missing'] else 'FEHLT'}")
        print(f"({len(rows)} Sounds)")

    _emit(args, rows, text)
    return 0


def cmd_bank_show(args) -> int:
    conn = _db(args)
    s = db.get_sound(conn, args.loc.upper())
    if s is None:
        print(f"Location {args.loc.upper()} nicht in der Bank – erst 'bank read'/'bank import'?", file=sys.stderr)
        return 1

    def text():
        print(f"{s['location']}: {s['name']!r}  Kategorie={s.get('category')!r}  Quelle={s.get('source')}")
        for k, v in sorted(s["parsed_json"]["params"].items()):
            print(f"  {k:32s} = {v}")

    _emit(args, s, text)
    return 0


# ---- convert ---------------------------------------------------------------

def cmd_convert(args) -> int:
    conn = _db(args)
    if args.dump:
        parsed = bd.parse_sndd(workflow.load_sndd_file(args.dump))
        print(f"Dump geladen: {args.dump} -> {parsed['name']!r}")
    else:
        synth = _connect_or_exit2("blofeld")
        if synth is None:
            return 2
        try:
            parsed = workflow.read_sound(synth, args.loc)
        finally:
            synth.close()
    loc = args.loc.upper()
    banks_dir = REPO / "dumps" / "banks"
    _store_sound(conn, loc, parsed, banks_dir)
    out_dir = Path(args.out) if args.out else workflow.TRANSFER
    out_path, mapped, unmapped = workflow.convert_parsed(parsed, loc, out_dir, args.template)
    db.insert_conversion(conn, loc, str(out_path), mapped, unmapped)
    print(f"Blofeld-Sound: {parsed['name']!r} ({loc})")
    print(f"{mapped} qpat-Parameter gemappt, {len(unmapped)} unmapped")
    print(f"geschrieben: {out_path}")
    print("\n--- unmapped ---")
    for u in unmapped:
        print("  ", u)
    print("\nWeiter am Iridium: .qpat auf USB-Stick/SD kopieren -> Load>Actions>Import -> laden.")
    print("Danach: bloridium ab --sound " + loc + "   (A/B-Messung; Achtung CC7=0 ist stumm!)")
    if args.json:
        print(json.dumps({"out": str(out_path), "mapped": mapped, "unmapped": unmapped}, indent=2))
    return 0


# ---- ab --------------------------------------------------------------------

def cmd_ab(args) -> int:
    conn = _db(args)
    if args.list:
        runs = db.list_ab_runs(conn, sound=args.sound)

        def text():
            print(f"{'ID':4s} {'LABEL':16s} {'SOUND':6s} {'NOTE':5s} {'TS'}")
            for r in runs:
                print(f"{r['id']:<4d} {r['label'][:16]:16s} {str(r['sound_location'] or '-'):6s} "
                      f"{r['note']:<5d} {r['ts']}")

        _emit(args, runs, text)
        return 0
    if args.diff:
        r1, r2 = db.get_ab_run(conn, int(args.diff[0])), db.get_ab_run(conn, int(args.diff[1]))
        if not r1 or not r2:
            print("Run-ID nicht gefunden (siehe 'ab --list')", file=sys.stderr)
            return 1
        e = r1["report_json"]["band_edges_hz"]
        d1, d2 = r1["report_json"]["band_delta_db"], r2["report_json"]["band_delta_db"]
        print(f"Band-Vergleich Run {r1['id']} ({r1['label']}) vs Run {r2['id']} ({r2['label']}):")
        print(f"{'Band':22s} {'Run1 dB':>9s} {'Run2 dB':>9s} {'Diff':>7s}")
        for i in range(len(d1)):
            print(f"  {e[i]:7.0f}-{e[i+1]:7.0f} Hz: {d1[i]:+8.1f} {d2[i]:+8.1f} {d2[i]-d1[i]:+6.1f}")
        return 0
    # Messung
    rec_dir = Path(args.rec_dir) if args.rec_dir else workflow.RECORDINGS
    report = workflow.measure_ab(note=args.note, dur=args.dur, label=args.label,
                                 rec_dir=rec_dir, sound_location=args.sound)
    db.insert_ab_run(conn, args.label, args.sound, args.note, args.dur,
                     report["files"]["report"], report["files"]["blofeld_npy"],
                     report["files"]["iridium_npy"], report)
    b, i = report["blofeld"], report["iridium"]
    print(f"=== A/B note {args.note}, {args.dur}s, Label {args.label!r}"
          + (f", Sound {args.sound}" if args.sound else "") + " ===")
    print(f"Blofeld  In3/4: peak {b['peak_dbfs']:6.1f} dBFS  centroid {b['centroid_hz']:8.1f} Hz")
    print(f"Iridium  In5/6: peak {i['peak_dbfs']:6.1f} dBFS  centroid {i['centroid_hz']:8.1f} Hz")
    print(f"Delta peak: {i['peak_dbfs'] - b['peak_dbfs']:+.1f} dB   centroid: {i['centroid_hz'] - b['centroid_hz']:+.1f} Hz")
    print("Band-Vergleich (Iridium - Blofeld, dB):")
    edges = report["band_edges_hz"]
    for k, d in enumerate(report["band_delta_db"]):
        print(f"  {edges[k]:7.0f}-{edges[k+1]:7.0f} Hz: {d:+6.1f} dB {'#' * max(0, int(round(d)))}")
    print(f"gespeichert: {report['files']['report']}")
    print("Hinweis: naechster Schritt am Iridium ggf. 'edit' der .qpat -> neu importieren -> wieder 'ab'.")
    return 0


# ---- qpat info -------------------------------------------------------------

def cmd_qpat_info(args) -> int:
    path = Path(args.file)
    parsed = qpat.load(path)
    rebuilt = qpat.build_qpat(
        parsed["name"], {k: (v["value"], v["display"]) for k, v in parsed["params"].items()},
        creator=parsed["creator"], description=parsed["description"],
        categories=parsed["categories"], version=parsed["version"],
        sample_maps=parsed["sample_maps"])
    ok = qpat.parse_qpat(rebuilt)["params"] == parsed["params"]
    print(f"Datei     : {path}")
    print(f"Name      : {parsed['name']!r}  Creator: {parsed['creator']!r}  Version: {parsed['version']}")
    print(f"Kategorien: {parsed['categories']}")
    print(f"Parameter : {parsed['param_count']}  Roundtrip: {'OK' if ok else 'FAIL'}")
    for k, v in list(parsed["params"].items())[:20]:
        print(f"  {k:34s} value={v['value']:.4f}  display={v['display']!r}")
    if args.register:
        conn = _db(args)
        rid = db.register_qpat(conn, path, parsed, source=path.parent.name)
        print(f"registriert in qpats (id={rid}, source={path.parent.name})")
    return 0 if ok else 1


# ---- edit ------------------------------------------------------------------

def cmd_edit(args) -> int:
    path = Path(args.file)
    parsed = qpat.load(path)
    if args.list:
        rows = editor.list_params(parsed, args.grep)

        def text():
            print(f"{'KEY':34s} {'VALUE':>8s}  DISPLAY")
            for k, v, d in rows:
                print(f"{k:34s} {v:8.4f}  {d}")
            print(f"({len(rows)} Parameter)")

        _emit(args, [{"key": k, "value": v, "display": d} for k, v, d in rows], text)
        return 0
    if args.show:
        try:
            v, d = editor.show_param(parsed, args.show)
        except KeyError as e:
            print(str(e), file=sys.stderr)
            return 1
        print(f"{args.show}: value={v:.4f} display={d!r}")
        return 0
    if args.set:
        if "=" not in args.set:
            print(f"--set erwartet KEY=VALUE, z. B. --set Osc1Type=0.5 (bekam {args.set!r})", file=sys.stderr)
            return 1
        key, _, val = args.set.partition("=")
        try:
            value = float(val)
        except ValueError:
            print(f"Wert muss float 0..1 sein, bekam {val!r}", file=sys.stderr)
            return 1
        editor.set_param(parsed, key.strip(), value, display=args.display)
        out = Path(args.save) if args.save else path
        editor.save(parsed, out, backup=True)
        print(f"gesetzt: {key.strip()} = {value:.4f}" + (f" (display={args.display!r})" if args.display else ""))
        print(f"geschrieben: {out}" + ("" if args.save else f"  (Backup: {path}.bak)"))
        return 0
    if args.diff:
        other = qpat.load(args.diff)
        diff = editor.diff_params(parsed, other)
        print(f"Diff {path.name} -> {Path(args.diff).name} ({len(diff)} Unterschiede):")
        print(f"{'KEY':34s} {'ALT':>8s} {'NEU':>8s}  DISPLAY")
        for k, va, vb, da, db_ in diff:
            print(f"{k:34s} {str(round(va, 4)) if va is not None else '-':>8s} "
                  f"{str(round(vb, 4)) if vb is not None else '-':>8s}  {da!r} -> {db_!r}")
        return 0
    return 1


# ---- main ------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not getattr(args, "cmd", None):
        build_parser().print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
