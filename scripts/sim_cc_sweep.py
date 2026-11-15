#!/usr/bin/env python3
"""sim_cc_sweep.py – automatischer CC-Sweep gegen das Blofeld-Original.

Laedt einen konvertierten Sound im Iridium (Favorites Bank 6 per PC), spielt
den passenden Blofeld-Sound (Bank A, PC = Location-1) live mit und dreht
jeden CC aus der offiziellen MIDI-Guide-Map (docs/midi-maps/iridium_midi_guide.csv)
selbsttaetig durch. Pro CC-Wert wird der sim-Score (0-100) gegen den Blofeld
gemessen und geloggt (recordings/sim_log.jsonl, mode="cc_sweep").

Aufruf:
  python3 scripts/sim_cc_sweep.py --loc A043 --note 72 --values 0,64,127
  python3 scripts/sim_cc_sweep.py --loc A043 --ccs 2,9,33 --values fine

Zwischen den CCs wird der Sound per PC (hin und zurueck auf Bank 6) neu
geladen, damit CC-Ueberschreibungen nicht in die naechste Messung laufen.

WICHTIG (rdb-.mimap geladen, verifiziert 2026-11-09 via spike_verify_mimap.py):
- CC0 = Filter1 Cutoff (rdb), CC7 = Filter1 Amount, CC32 = OSC1 Fine Pitch --
  Bank-Select und Volume sind damit per CC nicht mehr erreichbar; Bank bleibt 6.
- Daher: KEIN CC0/CC32/CC7 in reset/reload senden! CC7=0 stummt NICHT mehr.
- CC0 (Cutoff) wird als zusaetzlicher Sweep-Kanal vorne angefuehrt.

Report: recordings/cc_sweep_<LOC>_<note>_<ts>.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, sim
from scripts.sim_sweep_pcs import DEFAULT_MAP  # noqa: E402  (scripts/ ist kein Paket -> sys.path oben)

REPO = Path(__file__).resolve().parent.parent
GUIDE = REPO / "docs" / "midi-maps" / "iridium_midi_guide.csv"

# Niemals sweepen: ModWheel (CC1, nicht in Guide), All-Notes-Off (CC123).
# Mit rdb-Map sind CC0/CC7/CC32 Parameter (Cutoff/Amount/FinePitch), keine
# Bank/Volume mehr -- siehe Modul-Docstring.
EXCLUDE_CCS = {1, 123}


def load_guide_ccs() -> list[tuple[int, str]]:
    out = [(0, "Filter1 Cutoff [rdb CC0]")]  # rdb-Map: CC0 -> Pid 966 Cutoff
    with open(GUIDE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("cc_msb"):
                cc = int(r["cc_msb"])
                if cc not in EXCLUDE_CCS:
                    out.append((cc, r["parameter_name"].strip()))
    return out


def reset_all(blo=None, irr=None) -> None:
    """CC123=0 ueberall. CC7=127 nur am Blofeld (echtes Volume); am Iridium
    ist CC7 mit rdb-Map Filter1 Amount -- dort nie anfassen!"""
    for s in (blo, irr):
        if s is None:
            continue
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    if blo is not None:
        for ch in range(16):
            blo.control_change(7, 127, channel=ch)


def reload_patch(irr, bank: int, pc: int, other_pc: int) -> None:
    """Sound per PC-Wechsel (hin/zurueck) frisch laden -> CC-Ueberschreibungen weg.
    Kein CC0/CC32 senden (rdb-Map: das sind Parameter, Bank bleibt 6)."""
    irr.program_change(other_pc, channel=5)
    time.sleep(0.5)
    irr.program_change(pc, channel=5)
    time.sleep(0.7)
    reset_all(irr=irr)


def measure(blo, irr, note: int, dur: float, sr: int):
    reset_all(blo=blo, irr=irr)
    time.sleep(0.3)
    blo.note_on(note=note, velocity=100, channel=blo.channel)
    irr.note_on(note=note, velocity=100, channel=5)   # Part 1 (ch6) - monophon
    time.sleep(0.3)
    d = audio.record(duration=dur, channels=None)
    blo.note_off(note=note, channel=blo.channel)
    irr.note_off(note=note, channel=5)
    reset_all(blo=blo, irr=irr)
    bx = np.asarray(d[list(audio.CHANNELS["blofeld"]), :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(d[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
    return bx, ix


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--loc", required=True, help="Blofeld-Location (z. B. A043)")
    ap.add_argument("--note", type=int, default=72)
    ap.add_argument("--bank", type=int, default=6)
    ap.add_argument("--dur", type=float, default=1.6)
    ap.add_argument("--values", default="0,64,127",
                    help="'0,64,127' oder 'fine' (0..127 Schritt 8)")
    ap.add_argument("--ccs", default=None,
                    help="nur diese CCs (z. B. '2,9,33'); Default: alle aus der Guide-Map")
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    ap.add_argument("--report-dir", default=str(REPO / "recordings"))
    args = ap.parse_args(argv)

    if args.loc not in DEFAULT_MAP:
        print(f"unbekannte Location {args.loc!r};bekannt: {sorted(DEFAULT_MAP)}", file=sys.stderr)
        return 2
    irr_pc = DEFAULT_MAP[args.loc]
    blo_pc = int(args.loc[1:]) - 1
    other_pc = next(p for l, p in DEFAULT_MAP.items() if p != irr_pc)

    if args.values.strip().lower() == "fine":
        values = list(range(0, 128, 8))
    else:
        values = [int(v) for v in args.values.split(",")]

    if args.ccs:
        wanted = {int(c) for c in args.ccs.split(",")}
        ccs = [(c, n) for c, n in load_guide_ccs() if c in wanted]
    else:
        ccs = load_guide_ccs()

    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {"loc": args.loc, "note": args.note, "bank": args.bank,
              "irr_pc": irr_pc, "blo_pc": blo_pc, "values": values, "ccs": []}
    try:
        # Bank A explizit waehlen (CC0/CC32 = Bank select am BLOFELD)!
        blo.control_change(0, 0, channel=blo.channel)
        blo.control_change(32, 0, channel=blo.channel)
        blo.program_change(blo_pc, channel=blo.channel)
        reload_patch(irr, args.bank, irr_pc, other_pc)

        # Baseline ohne CC-Eingriff (ein Retry, falls erste Aufnahme leer)
        base = None
        for attempt in range(2):
            bx, ix = measure(blo, irr, args.note, args.dur, audio.SAMPLERATE)
            base = sim.score_pair(bx, ix, sr=audio.SAMPLERATE,
                                  meta={"mode": "cc_sweep", "blofeld": args.loc,
                                        "irr_pc": irr_pc, "note": args.note,
                                        "cc": None, "value": "baseline"},
                                  log_path=args.log)
            if base["score"] is not None:
                break
            reload_patch(irr, args.bank, irr_pc, other_pc)
        report["baseline"] = base
        if base["score"] is None:
            print(f"ABBRUCH: Baseline stumm (score=None) fuer {args.loc} PC{irr_pc}. "
                  f"Wahrscheinlich FALSCHES FAVORITES-BANK am Iridium aktiv "
                  f"(mit rdb-.mimap laesst sich die Bank nicht per CC0 waehlen, "
                  f"nur am Geraet!). Bitte Bank mit den 8 Sounds waehlen "
                  f"(pre-map Bank 6, Display 06xx) und erneut starten.",
                  file=sys.stderr, flush=True)
            return 3
        print(f"BASELINE {args.loc} note{args.note}: score={base['score']} "
              f"cos={base.get('spec_cos')} dtw={base.get('env_dtw')}")

        for cc, pname in ccs:
            reload_patch(irr, args.bank, irr_pc, other_pc)
            rows = []
            for v in values:
                irr.control_change(cc, v, channel=5)
                time.sleep(0.15)
                bx, ix = measure(blo, irr, args.note, args.dur, audio.SAMPLERATE)
                r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE,
                                   meta={"mode": "cc_sweep", "blofeld": args.loc,
                                         "irr_pc": irr_pc, "note": args.note,
                                         "cc": cc, "param": pname, "value": v},
                                   log_path=args.log)
                rows.append({"value": v, "score": r["score"], "spec_cos": r.get("spec_cos"),
                             "env_dtw": r.get("env_dtw"), "verdict": r["verdict"]})
                print(f"  CC{cc:3d} {pname:24s} v={v:3d}: score={r['score']} "
                      f"cos={r.get('spec_cos')} dtw={r.get('env_dtw')} {r['verdict']}", flush=True)
            scored = [r for r in rows if r["score"] is not None]
            best = max(scored, key=lambda r: r["score"]) if scored else None
            entry = {"cc": cc, "param": pname, "rows": rows, "best": best,
                     "delta": (best["score"] - base["score"]) if best and base["score"] is not None else None}
            report["ccs"].append(entry)
        # aufraeumen: Sound frisch laden
        reload_patch(irr, args.bank, irr_pc, other_pc)
    finally:
        blo.close()
        irr.close()

    out = Path(args.report_dir) / f"cc_sweep_{args.loc}_{args.note}_{ts}.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\nReport: {out}")
    if report.get("baseline", {}).get("score") is not None:
        top = sorted((c for c in report["ccs"] if c["delta"] is not None),
                     key=lambda c: c["delta"], reverse=True)[:10]
        print("Top-Verbesserungen vs Baseline:")
        for c in top:
            print(f"  CC{c['cc']:3d} {c['param']:24s} best v={c['best']['value']:3d} "
                  f"score={c['best']['score']} delta={c['delta']:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
