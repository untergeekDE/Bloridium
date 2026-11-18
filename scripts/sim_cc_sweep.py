#!/usr/bin/env python3
"""sim_cc_sweep.py – automatic CC sweep against the Blofeld original.

Loads a converted sound in the Iridium (Favorites bank 6 via PC), plays the
matching Blofeld sound (bank A, PC = location-1) live along and turns every CC
from the official MIDI guide map (docs/midi-maps/iridium_midi_guide.csv)
automatically. For each CC value the sim score (0-100) against the Blofeld is
measured and logged (recordings/sim_log.jsonl, mode="cc_sweep").

Usage:
  python3 scripts/sim_cc_sweep.py --loc A043 --note 72 --values 0,64,127
  python3 scripts/sim_cc_sweep.py --loc A043 --ccs 2,9,33 --values fine

Between CCs the sound is reloaded via PC (there and back on bank 6) so that CC
overrides do not leak into the next measurement.

IMPORTANT (rdb-.mimap loaded, verified 2026-11-09 via spike_verify_mimap.py):
- CC0 = Filter1 Cutoff (rdb), CC7 = Filter1 Amount, CC32 = OSC1 Fine Pitch --
  bank select and volume are no longer reachable via CC; bank stays 6.
- Therefore: NEVER send CC0/CC32/CC7 in reset/reload! CC7=0 no longer mutes.
- CC0 (cutoff) is prepended as an additional sweep channel.

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
from scripts.sim_sweep_pcs import DEFAULT_MAP  # noqa: E402  (scripts/ is not a package -> sys.path above)

REPO = Path(__file__).resolve().parent.parent
GUIDE = REPO / "docs" / "midi-maps" / "iridium_midi_guide.csv"

# Never sweep: ModWheel (CC1, not in guide), All-Notes-Off (CC123).
# With the rdb map, CC0/CC7/CC32 are parameters (cutoff/amount/fine pitch), no
# longer bank/volume -- see module docstring.
EXCLUDE_CCS = {1, 123}


def load_guide_ccs() -> list[tuple[int, str]]:
    out = [(0, "Filter1 Cutoff [rdb CC0]")]  # rdb map: CC0 -> Pid 966 cutoff
    with open(GUIDE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("cc_msb"):
                cc = int(r["cc_msb"])
                if cc not in EXCLUDE_CCS:
                    out.append((cc, r["parameter_name"].strip()))
    return out


def reset_all(blo=None, irr=None) -> None:
    """CC123=0 everywhere. CC7=127 only on the Blofeld (real volume); on the Iridium
    CC7 is Filter1 Amount with the rdb map -- never touch it there (it would
    change/mute the sound)!"""
    for s in (blo, irr):
        if s is None:
            continue
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    if blo is not None:
        for ch in range(16):
            blo.control_change(7, 127, channel=ch)


def reload_patch(irr, bank: int, pc: int, other_pc: int) -> None:
    """Reload the sound via PC change (there and back) -> CC overrides gone.
    Do not send CC0/CC32 (rdb map: those are parameters, bank stays 6)."""
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
    ap.add_argument("--loc", required=True, help="Blofeld location (e.g. A043)")
    ap.add_argument("--note", type=int, default=72)
    ap.add_argument("--bank", type=int, default=6)
    ap.add_argument("--dur", type=float, default=1.6)
    ap.add_argument("--values", default="0,64,127",
                    help="'0,64,127' or 'fine' (0..127 step 8)")
    ap.add_argument("--ccs", default=None,
                    help="only these CCs (e.g. '2,9,33'); default: all from the guide map")
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    ap.add_argument("--report-dir", default=str(REPO / "recordings"))
    args = ap.parse_args(argv)

    if args.loc not in DEFAULT_MAP:
        print(f"unknown location {args.loc!r}; known: {sorted(DEFAULT_MAP)}", file=sys.stderr)
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
        # Select bank A explicitly (CC0/CC32 = bank select on the BLOFELD) --
        # otherwise the PC lands in whatever bank is active on the device!
        blo.control_change(0, 0, channel=blo.channel)
        blo.control_change(32, 0, channel=blo.channel)
        blo.program_change(blo_pc, channel=blo.channel)
        reload_patch(irr, args.bank, irr_pc, other_pc)

        # Baseline without CC intervention (one retry if the first recording is empty)
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
            print(f"ABORT: baseline silent (score=None) for {args.loc} PC{irr_pc}. "
                  f"Probably the WRONG FAVORITES BANK is active on the Iridium "
                  f"(with the rdb-.mimap the bank cannot be selected via CC0, "
                  f"only on the device!). Please select the bank with the 8 sounds "
                  f"(pre-map bank 6, display 06xx) and start again.",
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
        # cleanup: reload the sound fresh
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
        print("Top improvements vs baseline:")
        for c in top:
            print(f"  CC{c['cc']:3d} {c['param']:24s} best v={c['best']['value']:3d} "
                  f"score={c['best']['score']} delta={c['delta']:+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
