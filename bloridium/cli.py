"""Bloridium CLI - terminal tool phase 1 (classic subcommands).

Subcommands (design: docs/superpowers/specs/2026-11-08-bloridium-cli-design.md):
  discover | status | bank read/import/list/show | convert | ab | qpat info | edit
Hardware (MIDI ports, audio device, channels) is configured via the user-editable
YAML file bloridium.yaml - run `bloridium discover --write` once to fill it from
the actually connected interfaces.

Exit codes: 0 ok, 1 error, 2 hardware unreachable (port list on stderr).
Safety: the tool never changes device settings; All Notes Off before measurements;
CC7=0 is silent on the Iridium; Iridium import only via .qpat on USB stick/SD.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

from . import audio, blofeld_dump as bd, config, db, discover, editor, midi, prognose, qpat, sim, sim_embed, specdiff, workflow

REPO = workflow.REPO


def default_db_path() -> Path:
    return Path(os.environ.get("BLORIDIUM_DB") or (REPO / "bloridium.db"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bloridium",
        description="Blofeld -> Iridium Sound-Transfer (Terminal-Tool, Phase 1)",
    )
    p.add_argument("--db", default=None,
                   help="path to the SQLite bank DB (default: $BLORIDIUM_DB or <repo>/bloridium.db)")
    p.add_argument("--json", action="store_true", help="output as JSON (where supported)")
    p.add_argument("--config", default=None,
                   help="YAML config file (default: $BLORIDIUM_CONFIG or ./bloridium.yaml)")
    sub = p.add_subparsers(dest="cmd")

    dsp = sub.add_parser("discover", help="scan MIDI ports + audio devices; --write merges them into the YAML config")
    # SUPPRESS: only override the global --json when given after the subcommand
    dsp.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                     help="JSON output (same as the global --json)")
    dsp.add_argument("--write", action="store_true",
                     help="write discovered values into the config file (existing user edits are kept)")
    dsp.add_argument("--probe", action="store_true",
                     help="send a MIDI Device Inquiry to every output port (identity reply)")
    dsp.set_defaults(func=cmd_discover)

    sp = sub.add_parser("status", help="MIDI ports + identity; --audio additionally measures level (audio interface)")
    sp.add_argument("--audio", action="store_true", help="ex step1: play note + measure level")
    sp.set_defaults(func=cmd_status)

    bp = sub.add_parser("bank", help="Blofeld bank manager (SQLite bank + dumps/banks/)")
    bsub = bp.add_subparsers(dest="bank_cmd", required=True)
    br = bsub.add_parser("read", help="read bank(s) live via SysEx (e.g. bank read A)")
    br.add_argument("banks", nargs="+", help="bank letters, e.g. A or A B")
    br.add_argument("--only", default=None, help="only these locations, e.g. --only A043,A044")
    br.add_argument("--banks-dir", default=None, help="target for stable .bin copies (default: dumps/banks/)")
    br.set_defaults(func=cmd_bank_read)
    bi = bsub.add_parser("import", help="OFFLINE: import existing SNDD dumps from DIR into the bank")
    bi.add_argument("dir", help="directory with blofeld_sndd_*.bin/.hex")
    bi.add_argument("--banks-dir", default=None)
    bi.set_defaults(func=cmd_bank_import)
    bl = bsub.add_parser("list", help="list sounds of the bank (from DB)")
    bl.add_argument("bank", nargs="?", default=None)
    bl.add_argument("--grep", default=None, help="filter on name/location (case-insensitive)")
    bl.set_defaults(func=cmd_bank_list)
    bs = bsub.add_parser("show", help="show parsed parameters of a sound")
    bs.add_argument("loc", help="e.g. A043")
    bs.set_defaults(func=cmd_bank_show)

    cv = sub.add_parser("convert", help="Blofeld-Sound -> Iridium-.qpat (transfer/)")
    cv.add_argument("loc", help="e.g. A043 or edit")
    cv.add_argument("--dump", default=None, help="OFFLINE: SNDD from file instead of live read")
    cv.add_argument("--out", default=None, help="target directory (default: transfer/)")
    cv.add_argument("--template", default=None, help="qpat template (default: docs/refs/qpat/template_waveform.qpat)")
    cv.set_defaults(func=cmd_convert)

    ab = sub.add_parser("ab", help="A/B sound measurement Blofeld (In3/4) vs Iridium (In5/6)")
    ab.add_argument("--note", type=int, default=36)
    ab.add_argument("--dur", type=float, default=3.0)
    ab.add_argument("--label", default="ab")
    ab.add_argument("--sound", default=None, help="Blofeld location the run is linked to")
    ab.add_argument("--list", action="store_true", help="instead of measuring: list runs")
    ab.add_argument("--diff", nargs=2, metavar=("ID1", "ID2"), default=None, help="compare two runs")
    ab.add_argument("--rec-dir", default=None, help="target for .npy/.json (default: recordings/)")
    ab.add_argument("--embed", action="store_true", help="phase B: CLAP embedding score into report.json")
    ab.add_argument("--llm", action="store_true", help="phase B: ollama LLM verdict into report.json")
    ab.add_argument("--strict", action="store_true", help="missing backend -> exit 3 instead of degrade")
    ab.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ab.set_defaults(func=cmd_ab)

    sm = sub.add_parser("sim", help="sound similarity Blofeld vs Iridium (phase A + phase B)")
    ssub = sm.add_subparsers(dest="sim_cmd", required=True)
    sc = ssub.add_parser("compare", help="compare two signals (--npy offline or --live)")
    sc.add_argument("--npy", nargs=2, metavar=("A", "B"), help="offline: compare two .npy")
    sc.add_argument("--live", action="store_true", help="measure live (both synths play)")
    sc.add_argument("--note", type=int, default=60)
    sc.add_argument("--dur", type=float, default=1.6)
    sc.add_argument("--blofeld", default="A043")
    sc.add_argument("--iridium-slot", default="?")
    sc.add_argument("--log", default=str(sim.DEFAULT_LOG))
    sc.add_argument("--embed", action="store_true", help="phase B: CLAP embedding score")
    sc.add_argument("--llm", action="store_true", help="phase B: ollama LLM verdict")
    sc.add_argument("--profile", action="store_true",
                    help="phase B: d1-omni noul profile (explanation layer) via /v1/systemone")
    sc.add_argument("--d1-model", default=sim_embed.DEFAULT_D1_MODEL)
    sc.add_argument("--specdiff", choices=["off", "dsp", "vision"], default="off",
                    help="Spektral-Diff interpretieren: dsp = nur DSP, vision = + Modell")
    sc.add_argument("--specdiff-backend", choices=["systemone", "chat"], default="systemone")
    sc.add_argument("--specdiff-model", default=specdiff.DEFAULT_SPECDIFF_MODEL)
    sc.add_argument("--strict", action="store_true", help="missing backend -> exit 3")
    sc.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    sc.set_defaults(func=cmd_sim_compare)

    pg = sub.add_parser("prognose", help="Prognose: RF aus Blofeld-SNDD-Parametern -> "
                                         "erwartete Konvertierguete (0-100)")
    psub = pg.add_subparsers(dest="prognose_cmd", required=True)
    pt = psub.add_parser("train", help="Modell trainieren aus sim-Log (JSONL) + SNDD-Dumps")
    pt.add_argument("--log", default=str(sim.DEFAULT_LOG), help="sim_log.jsonl mit meta.blofeld + result")
    pt.add_argument("--dumps", default=str(prognose.DEFAULT_DUMPS), help="DIR mit blofeld_sndd_<LOC>_*.bin")
    pt.add_argument("--target", default="combined", help="Label: combined|score|embed_score (Fallback score)")
    pt.add_argument("--model", default=str(prognose.DEFAULT_MODEL), help="Output-Modell (pickle) in models/")
    pt.add_argument("--seed", type=int, default=42)
    pt.add_argument("--n-estimators", type=int, default=200)
    pt.set_defaults(func=cmd_prognose_train)
    pp = psub.add_parser("predict", help="Vorhersage fuer eine Blofeld-Location (z. B. A043)")
    pp.add_argument("loc")
    pp.add_argument("--dumps", default=str(prognose.DEFAULT_DUMPS))
    pp.add_argument("--model", default=str(prognose.DEFAULT_MODEL))
    pp.set_defaults(func=cmd_prognose_predict)

    sd = sub.add_parser("specdiff", help="Spektral-Diff interpretieren (DSP + optional "
                                         "Vision-Model d1-omni/gemma4)")
    sd.add_argument("--wav", nargs=2, metavar=("A", "B"), help="einzelnes WAV-Paar")
    sd.add_argument("--log", default=str(sim.DEFAULT_LOG), help="sim_log.jsonl (Batch-Modus)")
    sd.add_argument("--recordings", default=str(REPO / "recordings"),
                    help="DIR mit ab_<LOC>_<ts>_n<note>[_w<pct>]_blo|irr.wav")
    sd.add_argument("--png", default=None, help="Single-Modus: PNG speichern")
    sd.add_argument("--only", default=None, help="Batch: nur eine Location (z. B. A043)")
    sd.add_argument("--write", action="store_true",
                    help="Batch: specdiff + specdiff_score ins JSONL zurueckschreiben")
    sd.add_argument("--no-vision", action="store_true", help="nur DSP, kein Vision-Model")
    sd.add_argument("--backend", choices=["systemone", "chat"], default="systemone",
                    help="systemone = d1-omni via /v1/systemone, chat = /api/chat (gemma4)")
    sd.add_argument("--model", default=specdiff.DEFAULT_SPECDIFF_MODEL)
    sd.set_defaults(func=cmd_specdiff)

    qp = sub.add_parser("qpat", help=".qpat files: inspect/register")
    qsub = qp.add_subparsers(dest="qpat_cmd", required=True)
    qi = qsub.add_parser("info", help="parse + roundtrip check + parameter overview")
    qi.add_argument("file")
    qi.add_argument("--register", action="store_true", help="register in qpats table")
    qi.set_defaults(func=cmd_qpat_info)

    ed = sub.add_parser("edit", help="Iridium editor: edit .qpat parameters")
    ed.add_argument("file")
    g = ed.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="parameter table")
    g.add_argument("--show", metavar="KEY")
    g.add_argument("--set", metavar="KEY=VALUE", help="set value (0..1); without --save in-place with .bak")
    g.add_argument("--diff", metavar="OTHER", help="diff against another .qpat")
    ed.add_argument("--grep", default=None, help="filter for --list")
    ed.add_argument("--display", default=None, help="display string for --set")
    ed.add_argument("--save", default=None, metavar="OUT", help="write to OUT instead of in-place")
    ed.set_defaults(func=cmd_edit)

    ccp = sub.add_parser("cc", help="send live CC to the synth (name from midi.guide CSV) - for adjusting on the loaded patch")
    ccp.add_argument("name", nargs="?", help="parameter name, e.g. 'Filter1 Reso'")
    ccp.add_argument("value", nargs="?", help="CC value 0..127")
    ccp.add_argument("--raw", metavar="CC", default=None, help="instead of name: raw CC number (then VALUE as first positional)")
    ccp.add_argument("--part", type=int, default=1, help="Iridium part 1-4 (default 1 = MIDI ch6)")
    ccp.add_argument("--synth", default="iridium", choices=["iridium", "blofeld"])
    ccp.add_argument("--list", action="store_true", help="show CC table")
    ccp.add_argument("--grep", default=None, help="filter for --list")
    ccp.add_argument("--force", action="store_true", help="allows CC7=0 (Output Level -> silent!)")
    ccp.set_defaults(func=cmd_cc)

    ex = sub.add_parser("explore", help="OS4 pid exploration on the Iridium: tells you which parameter to "
                                        "turn on the panel, captures the NRPN and books it into the CC list "
                                        "(read-only - sends no MIDI)")
    ex.add_argument("--csv", default=str(REPO / "docs" / "midi-maps" / "iridium_os4_cc_list.csv"),
                    help="CC list (default: docs/midi-maps/iridium_os4_cc_list.csv)")
    ex.add_argument("--log", default=str(REPO / "recordings" / "explore_log.jsonl"),
                    help="JSONL log (default: recordings/explore_log.jsonl)")
    ex.add_argument("--essential", action="store_true", help="explore only essential=yes parameters")
    ex.add_argument("--grep", default=None, help="filter on parameter names (case-insensitive)")
    ex.add_argument("--only-cc", default=None, help="only these CCs, e.g. 0,2,7")
    ex.add_argument("--list", action="store_true", help="status table of all CCs (needs no MIDI)")
    ex.add_argument("--port", default=None,
                    help="MIDI in port (default: Iridium in-port from the YAML config, currently Launchpad DIN)")
    ex.add_argument("--channel", type=int, default=5,
                    help="0-based MIDI channel of the part (default 5 = ch6 = part 1)")
    ex.add_argument("--listen", type=float, default=1.5,
                    help="silence in s that ends a capture (default 1.5)")
    ex.set_defaults(func=cmd_explore)

    return p


# ---- helpers ----------------------------------------------------------------

def _emit(args, data, text_fn):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, default=str))
    else:
        text_fn()


def _db(args):
    return db.connect(args.db or default_db_path())


def _connect_or_exit2(name: str, args=None):
    """midi.connect with ports from the YAML config; on error print the port list
    to stderr and return None (caller -> return 2)."""
    try:
        ports = midi.ports_from_config(getattr(args, "config", None))
        return midi.connect(name, ports)
    except RuntimeError as e:
        ports = midi.list_ports()
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"available MIDI ports OUT: {ports['out']}", file=sys.stderr)
        print(f"available MIDI ports IN : {ports['in']}", file=sys.stderr)
        return None


def _canon_loc(loc: str) -> str:
    """Canonical location ('a043' -> 'A043', ' edit ' -> 'edit')."""
    return workflow.location_str(*workflow.parse_location(loc))


def _store_sound(conn, loc: str, parsed: dict, banks_dir: Path) -> str:
    """Stable .bin copy under banks_dir/<Bank>/<LOC>.bin + DB upsert. -> sndd_path"""
    loc = _canon_loc(loc)
    bb, nn = workflow.parse_location(loc)
    raw = bytes([0xF0]) + bytes(bd.build_sndd(parsed["sdata"], bb=bb, nn=nn)) + bytes([0xF7])
    bank = "edit" if loc == "edit" else loc[0]
    dest = Path(banks_dir) / bank / f"{loc}.bin"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    from datetime import datetime, timezone
    pj = dict(parsed)
    pj["sdata"] = parsed["sdata"].hex()  # bytes -> hex, so it is JSON-serializable
    db.upsert_sound(conn, {
        "location": loc,
        "bank": bank, "slot": nn + 1, "name": parsed["name"],
        "category": str(parsed["params"].get("Category", "")),
        "sndd_path": str(dest), "parsed_json": pj,
        "dumped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "import",
    })
    return str(dest)


_LOC_RE = re.compile(r"blofeld_sndd_([A-Za-z]\d{3}|edit)(?:_|$)", re.IGNORECASE)


# ---- status ----------------------------------------------------------------

def cmd_discover(args) -> int:
    """Scan MIDI + audio interfaces; with --write merge them into the YAML config."""
    result = discover.discover(write=args.write, path=args.config, probe=args.probe)
    data = {
        "midi_ports": result["midi"],
        "audio_devices": result["audio_devices"],
        "identities": result["identities"],
        "config": result["config"],
        "config_path": str(result["config_path"]) if result["config_path"] else None,
    }

    def text():
        src = result["config_path"] or config.find_config_path(args.config)
        print(f"Config: {src if src else '(none yet)'}" + ("  [written]" if args.write else ""))
        print("MIDI ports:")
        for p in result["midi"]["out"]:
            print(f"  OUT: {p}")
        for p in result["midi"]["in"]:
            print(f"  IN : {p}")
        print("Audio devices:")
        for d in result["audio_devices"]:
            print(f"  [{d['index']}] {d['name']} ({d['api']})")
        if result["identities"]:
            print("Identity replies:")
            for port, ident in result["identities"].items():
                print(f"  {port}: manufacturer {ident['manufacturer']} model {ident['model']}")
        print("Effective config (precedence: user YAML > discovered > built-in defaults):")
        print(json.dumps(result["config"], indent=2, default=str))

    _emit(args, data, text)
    return 0


def cmd_status(args) -> int:
    cfg_path = config.find_config_path(getattr(args, "config", None))
    print(f"Config: {cfg_path if cfg_path else 'built-in defaults'}")
    a_settings = audio.settings(getattr(args, "config", None))
    ports = midi.list_ports()
    print("Available MIDI ports:")
    for p in ports["out"]:
        print(f"  OUT: {p}")
    for p in ports["in"]:
        print(f"  IN : {p}")
    results = {}
    synths = {}
    try:
        for name in ("blofeld", "iridium"):
            synth = _connect_or_exit2(name, args)
            if synth is None:
                return 2
            synths[name] = synth
            print(f"\n=== {name.upper()} ===")
            print(f"  MIDI Out : {synth.out_port_name}  channel {synth.channel + 1} (1-based)")
            synth.device_inquiry()
            for m in synth.receive(timeout=1.0):
                if m.type == "sysex":
                    info = __import__("bloridium.waldorf", fromlist=["identity_reply_info"]).identity_reply_info(m.data)
                    print(f"  MIDI <- Identity Reply: {info}" if info else f"  MIDI <- SysEx {bytes([0xF0, *m.data, 0xF7]).hex(' ')}")
            if args.audio:
                import numpy as np
                try:
                    data, m = audio.play_and_measure(synth, a_settings["channels"][name], note=60,
                                                     velocity=100, duration=2.0, config_path=args.config)
                except RuntimeError as e:
                    # I2: e.g. ffmpeg/audio interface not available -> graceful degradation
                    print(f"  Audio measurement failed: {e}", file=sys.stderr)
                    results[name] = False
                    continue
                peak = float(np.max(m["peak_dbfs"]))
                print(f"  Audio In {a_settings['channels'][name]}: Peak {peak:.1f} dBFS -> {'OK' if peak > -60 else 'NO SOUND'}")
                results[name] = peak > -60.0
            else:
                results[name] = True
    finally:
        for s in synths.values():
            s.close()
    ok = all(results.values())
    print("\n=== Summary ===")
    for name, r in results.items():
        print(f"  {name:9s}: {'CONNECTED' + (', sound measurable' if args.audio and r else '') if r else 'PROBLEM'}")
    return 0 if ok else 1


# ---- bank ------------------------------------------------------------------

def cmd_bank_read(args) -> int:
    conn = _db(args)
    banks_dir = Path(args.banks_dir) if args.banks_dir else (REPO / "dumps" / "banks")
    synth = _connect_or_exit2("blofeld", args)
    if synth is None:
        return 2
    if synth.inp is None:
        print("WARNING: Blofeld return channel not available - SNDD replies may be missing.", file=sys.stderr)
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
                print(f"  {loc}: ERROR {e}", file=sys.stderr)
    finally:
        synth.close()
    print(f"bank read: {ok} ok, {fail} errors (stable copies: {banks_dir})")
    if ok == 0:
        print("no sound read - Blofeld reachable? (port/channel 5, single mode)", file=sys.stderr)
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
    print(f"bank import: {ok} imported, {skipped} skipped without location (from {src})")
    return 0 if ok else 1


def cmd_bank_list(args) -> int:
    conn = _db(args)
    rows = db.list_sounds(conn, bank=args.bank, grep=args.grep)
    for r in rows:
        r["missing"] = not (r.get("sndd_path") and Path(r["sndd_path"]).exists())

    def text():
        print(f"{'LOC':6s} {'NAME':32s} {'CAT':8s} FILE")
        for r in rows:
            print(f"{r['location']:6s} {r['name'][:32]:32s} {str(r.get('category') or '')[:8]:8s} "
                  f"{'ok' if not r['missing'] else 'MISSING'}")
        print(f"({len(rows)} sounds)")

    _emit(args, rows, text)
    return 0


def cmd_bank_show(args) -> int:
    conn = _db(args)
    loc = _canon_loc(args.loc)
    s = db.get_sound(conn, loc)
    if s is None:
        print(f"Location {loc} not in the bank - run 'bank read'/'bank import' first?", file=sys.stderr)
        return 1
    s["missing"] = not (s.get("sndd_path") and Path(s["sndd_path"]).exists())

    def text():
        print(f"{s['location']}: {s['name']!r}  Category={s.get('category')!r}  Source={s.get('source')}")
        if s["missing"]:
            print(f"  WARNING: file missing (MISSING): {s.get('sndd_path')} - data from DB cache")
        for k, v in sorted(s["parsed_json"]["params"].items()):
            print(f"  {k:32s} = {v}")

    _emit(args, s, text)
    return 0


# ---- convert ---------------------------------------------------------------

def cmd_convert(args) -> int:
    conn = _db(args)
    loc = _canon_loc(args.loc)
    if args.dump:
        parsed = bd.parse_sndd(workflow.load_sndd_file(args.dump))
        print(f"Dump loaded: {args.dump} -> {parsed['name']!r}")
    else:
        synth = _connect_or_exit2("blofeld", args)
        if synth is None:
            return 2
        try:
            parsed = workflow.read_sound(synth, loc)
        except RuntimeError as e:
            # I1: Blofeld does not answer -> clean error, no traceback
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        finally:
            synth.close()
    banks_dir = REPO / "dumps" / "banks"
    _store_sound(conn, loc, parsed, banks_dir)
    out_dir = Path(args.out) if args.out else workflow.TRANSFER
    out_path, mapped, unmapped = workflow.convert_parsed(parsed, loc, out_dir, args.template)
    db.insert_conversion(conn, loc, str(out_path), mapped, unmapped)
    print(f"Blofeld sound: {parsed['name']!r} ({loc})")
    print(f"{mapped} qpat parameters mapped, {len(unmapped)} unmapped")
    print(f"written: {out_path}")
    print("\n--- unmapped ---")
    for u in unmapped:
        print("  ", u)
    print("\nNext on the Iridium: copy .qpat to USB stick/SD -> Load>Actions>Import -> load.")
    print("Then: bloridium ab --sound " + loc + "   (A/B measurement; caution CC7=0 is silent!)")
    if args.json:
        print(json.dumps({"out": str(out_path), "mapped": mapped, "unmapped": unmapped}, indent=2))
    return 0


# ---- ab --------------------------------------------------------------------
# A/B measurement: Blofeld (Scarlett In3/4) vs Iridium (In5/6), report into recordings/ + DB

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
            print("run ID not found (see 'ab --list')", file=sys.stderr)
            return 1
        e = r1["report_json"]["band_edges_hz"]
        d1, d2 = r1["report_json"]["band_delta_db"], r2["report_json"]["band_delta_db"]
        print(f"Band comparison run {r1['id']} ({r1['label']}) vs run {r2['id']} ({r2['label']}):")
        print(f"{'Band':22s} {'Run1 dB':>9s} {'Run2 dB':>9s} {'Diff':>7s}")
        for i in range(len(d1)):
            print(f"  {e[i]:7.0f}-{e[i+1]:7.0f} Hz: {d1[i]:+8.1f} {d2[i]:+8.1f} {d2[i]-d1[i]:+6.1f}")
        return 0
    # measurement
    rec_dir = Path(args.rec_dir) if args.rec_dir else workflow.RECORDINGS
    try:
        report = workflow.measure_ab(note=args.note, dur=args.dur, label=args.label,
                                     rec_dir=rec_dir, sound_location=_canon_loc(args.sound) if args.sound else None,
                                     embed=args.embed, llm=args.llm,
                                     models_dir=args.models_dir, strict=args.strict,
                                     **workflow._ckw(getattr(args, "config", None)))
    except sim_embed.BackendError as e:
        print(f"ERROR (strict, backend): {e}", file=sys.stderr)
        return 3
    except RuntimeError as e:
        # I1: MIDI port or audio device unreachable -> exit 2 + port list
        print(f"ERROR: {e}", file=sys.stderr)
        ports = midi.list_ports()
        print(f"available MIDI ports OUT: {ports['out']}", file=sys.stderr)
        print(f"available MIDI ports IN : {ports['in']}", file=sys.stderr)
        return 2
    db.insert_ab_run(conn, args.label, args.sound, args.note, args.dur,
                     report["files"]["report"], report["files"]["blofeld_npy"],
                     report["files"]["iridium_npy"], report)
    b, i = report["blofeld"], report["iridium"]
    print(f"=== A/B note {args.note}, {args.dur}s, Label {args.label!r}"
          + (f", Sound {args.sound}" if args.sound else "") + " ===")
    print(f"Blofeld  In3/4: peak {b['peak_dbfs']:6.1f} dBFS  centroid {b['centroid_hz']:8.1f} Hz")
    print(f"Iridium  In5/6: peak {i['peak_dbfs']:6.1f} dBFS  centroid {i['centroid_hz']:8.1f} Hz")
    print(f"Delta peak: {i['peak_dbfs'] - b['peak_dbfs']:+.1f} dB   centroid: {i['centroid_hz'] - b['centroid_hz']:+.1f} Hz")
    print("Band comparison (Iridium - Blofeld, dB):")
    edges = report["band_edges_hz"]
    for k, d in enumerate(report["band_delta_db"]):
        print(f"  {edges[k]:7.0f}-{edges[k+1]:7.0f} Hz: {d:+6.1f} dB {'#' * max(0, int(round(d)))}")
    if report.get("embed") is not None:
        print(f"Phase B embed: cos {report['embed']['embed_cos']} "
              f"embed_score {report['embed']['embed_score']} "
              f"combined {report['sim']['combined']}")
    if report.get("llm"):
        l = report["llm"]
        print(f"Phase B llm[{l.get('mode')}] score={l.get('score')}: {l.get('summary')} "
              f"diff={l.get('differences')}")
    if report.get("sim", {}).get("backend_error"):
        print(f"backend_error: {report['sim']['backend_error']}", file=sys.stderr)
    print(f"saved: {report['files']['report']}")
    print("Note: next step on the Iridium maybe 'edit' the .qpat -> re-import -> 'ab' again.")
    return 0


# ---- sim compare (Phase A + Phase B) ---------------------------------------

def cmd_sim_compare(args) -> int:
    if args.npy:
        a = np_load_mono(args.npy[0])
        b = np_load_mono(args.npy[1])
        meta = {"mode": "npy"}
        names = (str(args.npy[0]), str(args.npy[1]))
    elif args.live:
        try:
            blo_x, irr_x = workflow.record_ab_pair(note=args.note, dur=args.dur,
                                                   **workflow._ckw(getattr(args, "config", None)))
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            ports = midi.list_ports()
            print(f"available MIDI ports OUT: {ports['out']}", file=sys.stderr)
            print(f"available MIDI ports IN : {ports['in']}", file=sys.stderr)
            return 2
        a = np.asarray(blo_x, dtype=np.float64).mean(axis=0)
        b = np.asarray(irr_x, dtype=np.float64).mean(axis=0)
        meta = {"mode": "live", "note": args.note, "blofeld": args.blofeld,
                "iridium_slot": args.iridium_slot}
        names = (f"blofeld:{args.blofeld}", f"iridium:{args.iridium_slot}")
    else:
        print("either --npy A B or --live", file=sys.stderr)
        return 2
    clap, ollama = sim_embed.build_backends(args.models_dir, args.embed, args.llm)
    d1 = sim_embed.build_profile_backend(getattr(args, "profile", False),
                                         getattr(args, "d1_model", sim_embed.DEFAULT_D1_MODEL))
    sd_backend = (specdiff.build_backend(args.specdiff == "vision", args.specdiff_model,
                                         args.specdiff_backend)
                  if args.specdiff != "off" else None)
    try:
        r = sim_embed.score_pair_embed(a, b, sr=audio.SAMPLERATE, meta=meta,
                                       log_path=args.log, clap=clap, ollama=ollama,
                                       use_llm=args.llm, strict=args.strict,
                                       profile_backend=d1,
                                       specdiff_mode=args.specdiff,
                                       specdiff_backend=sd_backend)
    except sim_embed.BackendError as e:
        print(f"ERROR (strict, backend): {e}", file=sys.stderr)
        return 3
    sim_embed.print_result(r, *names)
    return 0 if r["score"] is not None else 1


def np_load_mono(p) -> np.ndarray:
    x = np.asarray(np.load(p), dtype=np.float64)
    return x.mean(axis=0) if x.ndim > 1 else x.ravel()


# ---- prognose (RF: SNDD-Parameter -> Konvertierguete) ----------------------

def cmd_prognose_train(args) -> int:
    X, y, locs, skipped = prognose.load_training_rows(args.log, args.dumps, args.target)
    if not locs:
        print(f"FEHLER: keine Trainingsdaten (log={args.log}, dumps={args.dumps}); "
              f"skipped: {skipped[:5]}", file=sys.stderr)
        return 2
    bundle = prognose.train_model(X, y, seed=args.seed, n_estimators=args.n_estimators,
                                  target=args.target)
    prognose.save_model(bundle, args.model)
    m = bundle["metrics"]
    r2cv = f"{m['r2_cv']:.3f}" if m["r2_cv"] is not None else "n/a"
    print(f"trainiert: n={m['n']} target={args.target} holdout={m['holdout']} "
          f"MAE={m['mae']:.2f} RMSE={m['rmse']:.2f} R2={m['r2']:.3f} R2_cv={r2cv}")
    print(f"Modell gespeichert: {args.model}")
    print("Top-10 Feature-Importances (Blofeld-Parameter):")
    for name, imp in bundle["importances"][:10]:
        print(f"  {imp:.4f}  {name}")
    print("locs: " + ", ".join(locs))
    if skipped:
        print(f"skipped ({len(skipped)}): " + "; ".join(skipped[:10]), file=sys.stderr)
    return 0


def cmd_prognose_predict(args) -> int:
    try:
        r = prognose.predict_loc(args.loc.upper(), args.dumps, args.model)
    except (FileNotFoundError, ValueError) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    print(f"predicted {r['loc']}: {r['predicted']:.1f} ± {r['std']:.1f} "
          f"(target={r['target']}, model={r['model']}, dump={r['dump']})")
    return 0


# ---- specdiff (Spektral-Diff interpretieren) --------------------------------

def cmd_specdiff(args) -> int:
    backend = specdiff.build_backend(not args.no_vision, args.model, args.backend)
    if args.wav:
        try:
            a, sr = specdiff.read_wav(args.wav[0])
            b, sr_b = specdiff.read_wav(args.wav[1])
        except (ValueError, OSError) as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            return 2
        if sr != sr_b:
            print(f"FEHLER: sample rates differ ({sr} vs {sr_b})", file=sys.stderr)
            return 2
        png = Path(args.png) if args.png else None
        r = specdiff.interpret_pair(a, b, sr, backend=backend, png_path=png)
        print(json.dumps({"labels": r["labels"], "score": round(r["score"], 2),
                          "source": r["source"], "confidence": r["confidence"],
                          "spec_png": r["spec_png"], "dsp": r["dsp"]},
                         indent=1, default=str))
        return 0
    # Batch ueber sim_log.jsonl + WAV-Paare
    log = Path(args.log)
    rec = Path(args.recordings)
    if not log.exists():
        print(f"FEHLER: log nicht gefunden: {log}", file=sys.stderr)
        return 2
    lines = log.read_text().splitlines()
    out_lines = list(lines)
    idx = specdiff.index_wavs(rec)
    n_done = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        e = json.loads(line)
        meta = e.get("meta") or {}
        loc, ts = meta.get("blofeld"), e.get("ts")
        if not loc:
            continue
        if args.only and loc != args.only:
            continue
        note = meta.get("note")
        w = meta.get("wheel_pct")
        wtag = f"_w{float(w):.0f}" if w is not None else ""
        pair = None
        if meta.get("wav"):  # exakter Pfad aus der Messung (neuere Logs)
            base = rec / meta["wav"]
            for suf_a, suf_b in (("_blo.wav", "_irr.wav"), ("_blofeld.npy", "_iridium.npy")):
                if Path(str(base) + suf_a).exists() and Path(str(base) + suf_b).exists():
                    pair = (Path(str(base) + suf_a), Path(str(base) + suf_b))
                    break
        if pair is None:
            pair = specdiff.pick_wav_pair(idx, loc, ts, note, w)
        if pair is None:
            continue
        try:
            a, b, sr = specdiff.load_pair(*pair)
            r = specdiff.interpret_pair(a, b, sr, backend=backend)
        except ValueError as ex:
            print(f"skip {loc} {ts}: {ex}", file=sys.stderr)
            continue
        e.setdefault("result", {})["specdiff"] = {
            "labels": r["labels"], "score": round(r["score"], 2), "source": r["source"],
            "confidence": r["confidence"], "dsp": r["dsp"], "probs": r["probs"]}
        e["result"]["specdiff_score"] = round(r["score"], 2)
        if args.write:
            out_lines[i] = json.dumps(e)
        n_done += 1
        lab = r["labels"]
        print(f"{loc} {ts} n{note}{wtag}: {lab['severity']}/{lab['spread']}/"
              f"{lab['temporal']} bands={lab['bands']} score={r['score']:.0f} ({r['source']})")
    if args.write and n_done:
        log.write_text("\n".join(out_lines) + "\n")
        print(f"geschrieben: {n_done} Eintraege -> {log}")
    if n_done == 0:
        print(f"FEHLER: keine WAV-Paare gefunden (log={log}, recordings={rec})",
              file=sys.stderr)
        return 2
    return 0


# ---- qpat info -------------------------------------------------------------

def cmd_qpat_info(args) -> int:
    path = Path(args.file)
    parsed = qpat.load(path)
    rebuilt = qpat.build_qpat(
        parsed["name"], {k: (v["value"], v["display"]) for k, v in parsed["params"].items()},
        creator=parsed["creator"], description=parsed["description"],
        categories=parsed["categories"], version=parsed["version"],
        sample_maps=parsed["sample_maps"], tail=parsed.get("_tail"),
        resources=parsed["resources"], layer2=parsed.get("layer2", (0, 0, 0)),
        instrument=parsed.get("instrument", 0), raw_fields=parsed.get("_raw_fields"),
        records_raw=parsed.get("_records_raw"), header_pad=parsed.get("_header_pad"))
    ok = rebuilt == path.read_bytes()  # byte-faithful incl. tail (C1)
    print(f"File      : {path}")
    print(f"Name      : {parsed['name']!r}  Creator: {parsed['creator']!r}  Version: {parsed['version']}")
    print(f"Categories: {parsed['categories']}")
    print(f"Parameters: {parsed['param_count']}  Roundtrip: {'OK' if ok else 'FAIL'}")
    for k, v in list(parsed["params"].items())[:20]:
        print(f"  {k:34s} value={v['value']:.4f}  display={v['display']!r}")
    if args.register:
        conn = _db(args)
        rid = db.register_qpat(conn, path, parsed, source=path.parent.name)
        print(f"registered in qpats (id={rid}, source={path.parent.name})")
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
            print(f"--set expects KEY=VALUE, e.g. --set Osc1Type=0.5 (got {args.set!r})", file=sys.stderr)
            return 1
        key, _, val = args.set.partition("=")
        try:
            value = float(val)
        except ValueError:
            print(f"value must be a float 0..1, got {val!r}", file=sys.stderr)
            return 1
        try:
            editor.set_param(parsed, key.strip(), value, display=args.display)
        except KeyError as e:
            print(str(e), file=sys.stderr)
            return 1
        out = Path(args.save) if args.save else path
        editor.save(parsed, out, backup=True)
        print(f"set: {key.strip()} = {value:.4f}" + (f" (display={args.display!r})" if args.display else ""))
        print(f"written: {out}" + ("" if args.save else f"  (backup: {path}.bak)"))
        return 0
    if args.diff:
        other = qpat.load(args.diff)
        diff = editor.diff_params(parsed, other)
        print(f"Diff {path.name} -> {Path(args.diff).name} ({len(diff)} differences):")
        print(f"{'KEY':34s} {'OLD':>8s} {'NEW':>8s}  DISPLAY")
        for k, va, vb, da, db_ in diff:
            print(f"{k:34s} {str(round(va, 4)) if va is not None else '-':>8s} "
                  f"{str(round(vb, 4)) if vb is not None else '-':>8s}  {da!r} -> {db_!r}")
        return 0
    return 1


# ---- cc (live adjustment on the loaded patch) ------------------------------

CC_CSV = {
    "iridium": REPO / "docs" / "midi-maps" / "iridium_midi_guide.csv",
    "blofeld": REPO / "docs" / "midi-maps" / "blofeld_midi_guide.csv",
}


def cmd_cc(args) -> int:
    from . import ccmap

    table = ccmap.load_cc_map(CC_CSV[args.synth])
    if args.list:
        rows = [r for r in table if r.get("cc_msb")
                and (not args.grep or args.grep.lower() in r["parameter_name"].lower())]
        print(f"{'CC':>5s}  PARAMETER   ({args.synth})")
        for r in rows:
            cc = int(r["cc_msb"])
            warn = "   (!! empirically Output Level: 0 = silent)" if cc == 7 else ""
            print(f"CC{cc:<4d}  {r['parameter_name']}{warn}")
        print(f"({len(rows)} parameters with CC; NRPN-only parameters hidden - NRPN is ignored)")
        return 0

    if args.raw is not None:
        cc_num, pname = int(args.raw), f"CC{args.raw}"
        value_str = args.value if args.value is not None else args.name
    else:
        if not args.name or args.value is None:
            print("usage: bloridium cc <Name> <Value> [--part N] | bloridium cc --raw <CC> <Value> | bloridium cc --list",
                  file=sys.stderr)
            return 1
        try:
            cc_num, pname = ccmap.find_cc(args.name, table)
        except (KeyError, ValueError) as e:
            print(str(e), file=sys.stderr)
            return 1
        value_str = args.value
    try:
        value = int(value_str)
    except (TypeError, ValueError):
        print(f"value must be 0..127, got {value_str!r}", file=sys.stderr)
        return 1
    if not 0 <= value <= 127:
        print(f"value must be 0..127, got {value}", file=sys.stderr)
        return 1

    # safety: CC7=0 on the Iridium silences the output entirely - refuse without --force
    if cc_num == 7 and not args.force and value == 0:
        print("ABORT: CC7 = Output Level, 0 = SILENT! (--force to send anyway)", file=sys.stderr)
        return 1

    if args.synth == "iridium":
        if not 1 <= args.part <= 4:
            print(f"part must be 1..4, got {args.part}", file=sys.stderr)
            return 1
        channel = 5 + args.part - 1  # parts 1-4 = MIDI 6-9 (0-based 5-8)
    else:
        channel = 4  # Blofeld Global Channel = MIDI 5 (0-based 4), Single Mode

    synth = _connect_or_exit2(args.synth, args)
    if synth is None:
        return 2
    try:
        synth.control_change(cc_num, value, channel=channel)
    finally:
        synth.close()
    if cc_num == 7:
        print(f"WARNING: CC7 = Output Level was sent (value {value})")
    print(f"{args.synth} MIDI ch{channel + 1}: {pname} (CC{cc_num}) = {value}")
    return 0


# ---- explore (OS4 pid exploration on the Iridium, read-only) ----------------
# listens for NRPN the device sends while turning a panel knob; no MIDI is sent

def cmd_explore(args) -> int:
    import time
    from datetime import datetime, timezone

    from . import explore as ex

    csv_path = Path(args.csv)
    log_path = Path(args.log)
    fieldnames, rows = ex.load_cc_list(csv_path)

    if args.list:
        cols = ["cc", "iridium_param", "pid", "os4_verified", "pid_os4", "nrpn_last"]
        data = [{k: r.get(k, "") for k in cols} for r in sorted(rows, key=lambda r: int(r["cc"]))]

        def text():
            print(f"{'CC':>6s}  {'PARAM':28s} {'PID_RDB':>7s} {'VERIF':>6s} {'PID_OS4':>7s}  LAST")
            for r in data:
                print(f"CC{int(r['cc']):>4d}  {r['iridium_param'][:28]:28s} {r['pid']:>7s} "
                      f"{(r['os4_verified'] or '-'):>6s} {(r['pid_os4'] or '-'):>7s}  {r['nrpn_last']}")
            n_ok = sum(1 for r in rows if (r.get("os4_verified") or "").lower() == "ja")
            print(f"({len(rows)} CCs, {n_ok} verified)")

        _emit(args, data, text)
        return 0

    pending = ex.pending_rows(rows, essential=args.essential, grep=args.grep, only_cc=args.only_cc)
    if not pending:
        print("no open parameters (all os4_verified != 'nein') - nothing to do.")
        return 0

    port = args.port or midi.ports_from_config(getattr(args, "config", None))["iridium"]["in"]
    try:
        in_name, inp = midi.open_input(port)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        ports = midi.list_ports()
        print(f"available MIDI ports IN : {ports['in']}", file=sys.stderr)
        return 2

    print(f"explore: {len(pending)} open parameters | in port {in_name!r} | channel ch{args.channel + 1} "
          f"(default ch6 = part 1) | on the Iridium: Global > MIDI = on, Send NRPN = on")
    decoder = ex.NrpnDecoder()
    total = len(rows)
    done_total = sum(1 for r in rows if (r.get("os4_verified") or "").lower() == "ja")
    done = 0
    backup_done = False
    idx = 0
    try:
        while idx < len(pending):
            row = pending[idx]
            print(f"\n[{done_total}/{total}] next: CC{row['cc']}  {row.get('iridium_param', '')}")
            print(f"  expected rdb pid {row.get('pid', '?')}  |  Blofeld counterpart: "
                  f"{row.get('zugehoeriger_blofeld_param') or '-'} "
                  f"({row.get('nutzung_pct') or '-'}%, essential={row.get('essential') or '-'})")
            print(f"  turn the panel now, then press Enter  [s=skip without booking, q=quit]")
            while inp.poll() is not None:
                pass  # drain input buffer
            try:
                cmd_in = input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n(quit - what was booked so far is saved)")
                break
            if cmd_in == "q":
                print("(quit - what was booked so far is saved)")
                break
            if cmd_in == "s":
                idx += 1
                continue
            # capture: until args.listen s of silence
            events: list = []
            stats = {"n": 0, "cc": 0, "nrpn_other_ch": None}
            last = time.time()
            while True:
                m = inp.poll()
                if m is None:
                    if time.time() - last > args.listen:
                        break
                    time.sleep(0.005)
                    continue
                last = time.time()
                stats["n"] += 1
                if m.type == "control_change" and m.channel == args.channel:
                    stats["cc"] += 1
                    ev = decoder.feed(m)
                    if ev:
                        events.append(ev)
                elif m.type == "control_change" and m.control in (99, 98, 6, 38):
                    stats["nrpn_other_ch"] = m.channel
            if not events:
                if stats["n"] == 0:
                    print("  no NRPN received - no MIDI message on the port at all.")
                    print("  check: Global > MIDI = on? Send NRPN = on? maybe plug Iridium USB in briefly")
                    print("  and set --port \"Iridium Keyboard (MIDI 2.0) MIDI 2.0\" (DIN check: docs/HANDOVER-2026-11-12.md).")
                elif stats["nrpn_other_ch"] is not None:
                    print(f"  NRPN arrived on ch{stats['nrpn_other_ch'] + 1} - try --channel {stats['nrpn_other_ch']}?")
                else:
                    print("  messages received, but no NRPN among them - Send NRPN = on? "
                          "right part (default ch6 = part 1)?")
                continue  # same parameter stays selected
            ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            entry = ex.book_row(row, events, ts)
            entry["cc_gesehen"] = stats["cc"]
            entry["port"] = in_name
            entry["channel"] = args.channel
            ex.append_log(log_path, entry)
            ex.save_cc_list(csv_path, fieldnames, rows, backup=not backup_done)
            backup_done = True
            dev = f"  *** DEVIATION from rdb pid {row.get('pid')} ***" if entry["abweichung"] else ""
            print(f"  NRPN: pid {entry['pid_os4']}{dev}  values {entry['nrpn_min']}..{entry['nrpn_max']} "
                  f"(last {entry['nrpn_last']}), {entry['n_msgs']} NRPNs")
            print(f"  booked: {csv_path.name} (os4_verified=ja, pid_os4={entry['pid_os4']}) + {log_path.name}")
            done += 1
            done_total += 1  # display counts verified rows (incl. earlier sessions)
            idx += 1
    finally:
        inp.close()
    print(f"\nSession end: {done} parameters captured.")
    return 0


# ---- main ------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not getattr(args, "cmd", None):
        build_parser().print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
