#!/usr/bin/env python3
"""Measure A001-A100: Blofeld bank A vs. the qpats on the Iridium SD card.

This prepares/executes the next RF dataset run. The qpats are loaded directly
from the SD card via the Iridium shell (`load-patch 2:<sd_dir>/<file>`), never
from the silent 1-MB storage slots. Both synths play the same note; the
recordings are scored with the v2 similarity formula and appended to a JSONL
log that `bloridium prognose train` can consume.

Safety: without `--run` the script only prints the plan (no MIDI note, no
load-patch). `--verify-sd` is read-only (`ls`).

Prepare the SD folder first:
    python3 scripts/reconvert_rf.py --out transfer/rf100_v3 --sd-dir rf300
    cp -R transfer/rf100_v3 /Volumes/<SD>/rf300

Then, with the Iridium SD mounted as drive 2:
    python3 scripts/measure_rf100.py --verify-sd
    python3 scripts/measure_rf100.py --run

Training afterwards:
    python3 -m bloridium prognose entropy --log recordings/sim_log_v3.jsonl
    python3 -m bloridium prognose train --log recordings/sim_log_v3.jsonl \
        --dumps dumps --target score --model models/prognose_rf_v3.pkl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, midi, sim  # noqa: E402
from _quir import Iridium  # noqa: E402
import _measure as M  # noqa: E402

DEFAULT_MANIFEST = REPO / "transfer" / "rf100_v3" / "MANIFEST.json"
DEFAULT_LOG = REPO / "recordings" / "sim_log_v3.jsonl"


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"manifest not found: {path} (run scripts/reconvert_rf.py)")
    return json.loads(path.read_text(encoding="utf-8"))


def done_keys(log_path: Path) -> set[tuple[str, int]]:
    done: set[tuple[str, int]] = set()
    if not log_path.exists():
        return done
    for line in log_path.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        meta, res = e.get("meta") or {}, e.get("result") or {}
        loc, note = meta.get("blofeld"), meta.get("note")
        if loc and note is not None and res.get("score") is not None:
            done.add((loc, int(note)))
    return done


def verify_sd(irr: Iridium, sd_dir: str, entries: list[dict]) -> bool:
    out = irr.cmd(f"ls 2:{sd_dir}", wait=0.8, timeout=2.0)
    missing = [e["sd_name"] for e in entries if e["sd_name"] not in out]
    print(f"SD 2:{sd_dir}: {len(entries) - len(missing)}/{len(entries)} qpats found")
    for name in missing[:10]:
        print(f"  MISSING {name}")
    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more")
    return not missing


def select_blofeld(blo, loc: str) -> None:
    n = int(loc[1:])
    blo.control_change(0, 0, channel=blo.channel)    # bank A
    blo.control_change(32, 0, channel=blo.channel)
    blo.program_change(n - 1, channel=blo.channel)
    time.sleep(0.7)


def load_patch(irr: Iridium, sd_dir: str, sd_name: str) -> None:
    out = irr.cmd(f"load-patch 2:{sd_dir}/{sd_name}", wait=0.8, timeout=2.0)
    low = out.lower()
    if "error" in low or "not found" in low or "fail" in low:
        raise RuntimeError(f"load-patch {sd_name}: {out!r}")


def parse_only(value: str | None, entries: list[dict]) -> list[dict]:
    if not value:
        return entries
    wanted = {v.strip().upper() for v in value.split(",") if v.strip()}
    return [e for e in entries if e["loc"].upper() in wanted]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--notes", default="72,60")
    ap.add_argument("--only", help="comma-separated locations, e.g. A001,A043")
    ap.add_argument("--dur", type=float, default=1.5)
    ap.add_argument("--no-resume", action="store_true",
                    help="re-measure rows already present in the log")
    ap.add_argument("--verify-sd", action="store_true",
                    help="read-only check that all qpats are on 2:<sd_dir>")
    ap.add_argument("--run", action="store_true",
                    help="actually touch the hardware (load-patch + notes)")
    args = ap.parse_args(argv)

    manifest = load_manifest(args.manifest)
    entries = parse_only(args.only, manifest["entries"])
    sd_dir = manifest["sd_dir"]
    notes = [int(n) for n in args.notes.split(",")]
    done = set() if args.no_resume else done_keys(args.log)

    print(f"manifest: {args.manifest} ({len(entries)} sounds, SD 2:{sd_dir})")
    print(f"log:      {args.log} ({len(done)} (loc, note) rows already scored)")
    print(f"notes:    {notes}")

    if not args.run:
        for e in entries:
            print(f"  {e['loc']} {e['label'][:24]:24s} {e['sd_name']}")
        print("\ndry run only; add --run to measure (and --verify-sd for the SD check)")
        return 0

    irr = Iridium()
    blo = midi.connect("blofeld")
    try:
        if not verify_sd(irr, sd_dir, entries):
            raise SystemExit("SD verify failed - copy transfer/rf100_v3 to "
                             f"2:{sd_dir} first")
        scores = []
        for i, e in enumerate(entries, 1):
            loc, sd_name = e["loc"], e["sd_name"]
            pending = [n for n in notes if (loc, n) not in done]
            if not pending:
                continue
            load_patch(irr, sd_dir, sd_name)
            select_blofeld(blo, loc)
            for note in pending:
                data = M.capture(blo, irr, note=note, vel=100, dur=args.dur)
                bx = np.asarray(data[list(audio.CHANNELS["blofeld"]), :],
                                dtype=np.float64).mean(axis=0)
                ix = np.asarray(data[list(audio.CHANNELS["iridium"]), :],
                                dtype=np.float64).mean(axis=0)
                meta = {"mode": "rf100_v3", "blofeld": loc, "note": note,
                        "qpat": sd_name, "sd_dir": sd_dir}
                r = sim.score_pair(bx, ix, sr=audio.SAMPLERATE, meta=meta,
                                   log_path=args.log)
                if r.get("score") is not None:
                    scores.append(r["score"])
                print(f"{i:3d}/{len(entries)} {loc} note{note}: "
                      f"score={r.get('score')} verdict={r.get('verdict')} "
                      f"si={r.get('score_version')}", flush=True)
        if scores:
            arr = np.asarray(scores, dtype=float)
            print(f"\nscored {len(scores)} rows: mean {arr.mean():.1f}, "
                  f"min {arr.min():.1f}, max {arr.max():.1f}")
        print("training command:\n"
              f"  python3 -m bloridium prognose train --log {args.log} "
              f"--dumps dumps --target score --model models/prognose_rf_v3.pkl")
    finally:
        irr.close()
        blo.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
