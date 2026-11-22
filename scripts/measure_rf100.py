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


def collect(irr: Iridium, text: str, max_empty: int = 5,
            max_s: float = 60.0, strip_sentinel: bool = True,
            sentinel_every: float = 4.0) -> str:
    """Send one shell line and poll the readout until it stays quiet.

    One poll returns at most 256 bytes and the shell answers lazily, so a single
    `irr.cmd()` truncates listings and can return nothing at all. A periodic
    `temp` acts as a FIFO sentinel: once "CPU temp" arrives after our first
    byte, all output of the command has been delivered.
    """
    irr.drain(quiet=0.25, max_s=2.0)
    irr.line(text, wait=0.25)
    buf = bytearray()
    t0 = time.time()
    last_byte = last_sentinel = time.time()
    first_byte = None
    sentinel = False
    while time.time() - t0 < max_s:
        time.sleep(0.11)
        irr._send(0x55)
        b = irr._read(0.25)
        if b:
            buf += b
            last_byte = time.time()
            if first_byte is None:
                first_byte = time.time()
            if b"CPU temp" in buf:
                sentinel = True
        if time.time() - last_sentinel > sentinel_every:
            irr.line("temp", wait=0.05)
            last_sentinel = time.time()
        if sentinel and time.time() - last_byte > 1.2:
            break
        if not b and first_byte is None and time.time() - t0 > min(max_s, 20.0):
            break
    raw = bytes(buf).decode("ascii", "replace")
    if not strip_sentinel:
        return raw
    keep = [ln for ln in raw.splitlines()
            if "CPU temp" not in ln and not any(
                n in ln for n in ("SET_INTERFACE", "parseMidi", "Switch to MIDI",
                                  "Active descriptor", "SysexManager::check"))]
    return "\n".join(keep)


def shell_alive(irr: Iridium, tries: int = 2) -> bool:
    """Probe the shell with `temp` (short output). False after the USB stall."""
    for _ in range(tries):
        if "CPU temp" in collect(irr, "temp", max_s=12.0, strip_sentinel=False,
                                 sentinel_every=0.5):
            return True
        time.sleep(1.0)
    return False


def verify_sd(irr: Iridium, sd_dir: str, entries: list[dict],
              out_dir: Path) -> bool:
    """Check names *and* byte sizes against the local package.

    Size comparison is what proves the SD copy is the current conversion: names
    are identical between v2 and v3.
    """
    out = collect(irr, f"ls 2:{sd_dir}")
    found: dict[str, int] = {}
    for line in out.splitlines():
        line = line.strip()
        if ".qpat --" not in line or line.startswith("._"):
            continue
        name, _, size = line.partition(" -- ")
        try:
            found[name.strip()] = int(size.split()[0])
        except (ValueError, IndexError):
            continue
    missing, stale = [], []
    for e in entries:
        got = found.get(e["sd_name"])
        want = (out_dir / e["sd_name"]).stat().st_size
        if got is None:
            missing.append(e["sd_name"])
        elif got != want:
            stale.append(f"{e['sd_name']} ({got} != {want})")
    print(f"SD 2:{sd_dir}: {len(entries) - len(missing) - len(stale)}/"
          f"{len(entries)} qpats present and size-matched")
    for name in missing[:10]:
        print(f"  MISSING {name}")
    for name in stale[:10]:
        print(f"  STALE   {name}")
    if len(missing) + len(stale) > 10:
        print(f"  ... and {len(missing) + len(stale) - 10} more")
    return not missing and not stale


def select_blofeld(blo, loc: str) -> None:
    n = int(loc[1:])
    blo.control_change(0, 0, channel=blo.channel)    # bank A
    blo.control_change(32, 0, channel=blo.channel)
    blo.program_change(n - 1, channel=blo.channel)
    time.sleep(0.7)


def load_patch(irr: Iridium, sd_dir: str, sd_name: str) -> None:
    """Load a qpat from the SD card into the edit buffer.

    A successful load-patch prints nothing, so only errors are detectable; the
    caller probes the shell separately (`shell_alive`).
    """
    out = collect(irr, f"load-patch 2:{sd_dir}/{sd_name}", max_empty=3, max_s=8.0,
                  sentinel_every=0.5)
    low = out.lower()
    if any(t in low for t in ("error", "not found", "fail", "f_opendir")):
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
    ap.add_argument("--skip-verify", action="store_true",
                    help="skip the SD check (the Iridium readout stalls after `ls`; "
                         "use once --verify-sd passed and no new copy was made)")
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
        if args.verify_sd:
            irr = Iridium()
            try:
                ok = verify_sd(irr, sd_dir, entries, args.manifest.parent)
            finally:
                irr.close()
            return 0 if ok else 1
        for e in entries:
            print(f"  {e['loc']} {e['label'][:24]:24s} {e['sd_name']}")
        print("\ndry run only; add --run to measure (and --verify-sd for the SD check)")
        return 0

    # `ls` stalls the QUIR readout for a while, so verify in a throw-away
    # session (or skip it once it has passed) and measure in a fresh one.
    if not args.skip_verify:
        irr = Iridium()
        try:
            ok = verify_sd(irr, sd_dir, entries, args.manifest.parent)
        finally:
            irr.close()
        if not ok:
            raise SystemExit(f"SD verify failed - copy {args.manifest.parent} to "
                             f"2:{sd_dir} first")
        time.sleep(1.0)
    else:
        print("SD verify skipped (--skip-verify)")

    irr = Iridium()
    blo = midi.connect("blofeld")
    try:
        if not shell_alive(irr):
            raise SystemExit("Iridium shell is not responding (no `temp` output); "
                             "power-cycle the Iridium and retry")
        scores = []
        for i, e in enumerate(entries, 1):
            loc, sd_name = e["loc"], e["sd_name"]
            pending = [n for n in notes if (loc, n) not in done]
            if not pending:
                continue
            load_patch(irr, sd_dir, sd_name)
            if not shell_alive(irr, tries=1):
                raise SystemExit(f"{loc}: Iridium shell stopped answering after "
                                 "load-patch; rerun to resume (already logged rows "
                                 "are skipped)")
            select_blofeld(blo, loc)
            for note in pending:
                data = M.capture(blo, irr, note=note, vel=100, dur=args.dur)
                bx = np.asarray(data[list(audio.CHANNELS["blofeld"]), :],
                                dtype=np.float64).mean(axis=0)
                ix = np.asarray(data[list(audio.CHANNELS["iridium"]), :],
                                dtype=np.float64).mean(axis=0)
                rms = float(np.sqrt(np.mean(ix ** 2)))
                if rms < 1e-3:      # -60 dBFS: Iridium path dead, not a patch
                    raise SystemExit(f"{loc}: Iridium silent (rms {rms:.2e}); "
                                     "check its audio cable / MIDI settings")
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
