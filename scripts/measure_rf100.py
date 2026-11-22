#!/usr/bin/env python3
"""Measure A001-A100: Blofeld bank A vs. the qpats stored on the Iridium.

The qpats must be loaded into the Iridium's patch slots (the transfer step
imports a whole directory in file order; `--slot-start` maps entry i to
slot-start+i when the manifest slots do not match what the device did). The
runner loads each sound by slot number and verifies the edit buffer via
`get-param` readback before playing a note.

`load-patch 2:<dir>/<file>.qpat` must NOT be used: the firmware accepts the
command but silently does nothing (verified 2026-11-22 by edit-buffer
readback; the 2026-11-22 v3 run was invalid because of this).

Both synths play the same note; the recording starts before the note and is
cropped from the detected onset (protocol "onset"), so percussive sustain-0
patches keep their attack and short decay. The segments are scored with the v2
score and appended to a JSONL log that `bloridium prognose train` consumes.

Safety: without `--run` the script only prints the plan (no MIDI note, no
load-patch). `--verify-sd` is read-only (`ls`).

Then, with the Iridium SD mounted as drive 2:
    python3 scripts/measure_rf100.py --verify-sd
    python3 scripts/measure_rf100.py --run --skip-verify

Training afterwards:
    python3 -m bloridium prognose entropy --log recordings/sim_log_v3.jsonl
    python3 -m bloridium prognose train --log recordings/sim_log_v3.jsonl \
        --dumps dumps --target score --model models/prognose_rf_v3.pkl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, midi, qpat, sim  # noqa: E402
from _device_tool import Iridium  # noqa: E402
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


def capture_onset(blo, irr, note: int = 60, vel: int = 100,
                  hold: float = 1.2, tail: float = 0.9, lead: float = 0.6):
    """Record from the note onset (not 0.35 s later): percussive patches count.

    Starts the recorder, plays the note in a thread, then crops both channels
    from just before the detected onset. This keeps the attack and the short
    decay of sustain-0 patches in the scored segment.
    """
    for ch in range(16):
        blo.control_change(123, 0, channel=ch)
        blo.control_change(7, 127, channel=ch)
    irr.silence_part()

    def play():
        time.sleep(lead)
        blo.note_on(note=note, velocity=vel)
        irr.note_on(note=note, velocity=vel)
        time.sleep(hold)
        blo.note_off(note=note)
        irr.note_off(note=note)

    th = threading.Thread(target=play)
    th.start()
    data = audio.record(duration=lead + hold + tail, channels=None)
    th.join()
    peak = float(np.abs(data).max())
    if peak <= 0:
        return data
    onset = int(np.argmax(np.abs(data).max(axis=0) > max(peak * 0.03, 1e-4)))
    start = max(0, onset - int(0.03 * audio.SAMPLERATE))
    end = min(data.shape[1], start + int((hold + tail) * audio.SAMPLERATE))
    return data[:, start:end]


def select_blofeld(blo, loc: str) -> None:
    n = int(loc[1:])
    blo.control_change(0, 0, channel=blo.channel)    # bank A
    blo.control_change(32, 0, channel=blo.channel)
    blo.program_change(n - 1, channel=blo.channel)
    time.sleep(0.7)


def find_pid(irr: Iridium, name: str) -> int:
    out = collect(irr, f"find-pid {name}", max_s=12.0)
    m = re.search(r"has pid\s+(-?\d+)", out)
    if not m or int(m.group(1)) < 0:
        raise SystemExit(f"cannot resolve device pid for {name!r}: {out!r}")
    return int(m.group(1))


def collect_many(irr: Iridium, lines: list[str], max_s: float = 20.0) -> str:
    """Queue several shell lines, then read until the `temp` sentinel arrives."""
    irr.drain(quiet=0.2, max_s=2.0)
    for line in lines:
        irr.line(line, wait=0.06)
    irr.line("temp", wait=0.05)
    buf = bytearray()
    t0 = time.time()
    last = time.time()
    while time.time() - t0 < max_s:
        time.sleep(0.11)
        irr._send(0x55)
        b = irr._read(0.25)
        if b:
            buf += b
            last = time.time()
        if b"CPU temp" in buf and time.time() - last > 0.8:
            break
    return bytes(buf).decode("ascii", "replace")


def verify_patch(irr: Iridium, expected: dict, pids: dict, tol: float = 0.002) -> None:
    """Read a few params back; abort if the edit buffer is not the expected qpat."""
    out = collect_many(irr, [f"get-param {pid}" for pid in pids.values()])
    got = {int(m.group(1)): float(m.group(2))
           for m in re.finditer(r"Param\s+(\d+)\s*=\s*(-?[\d.]+)", out)}
    bad = []
    for name, pid in pids.items():
        want = float(expected[name]["value"])
        if pid not in got:
            bad.append(f"{name}: no readback")
        elif abs(got[pid] - want) > tol:
            bad.append(f"{name}: got {got[pid]:.3f}, want {want:.3f}")
    if bad:
        raise SystemExit("patch verification failed (edit buffer != qpat): "
                         + "; ".join(bad))


def load_patch(irr: Iridium, slot: int) -> None:
    """Load stored patch `slot` into the edit buffer.

    IMPORTANT: `load-patch 2:<dir>/<file>.qpat` is accepted but silently does
    nothing on this firmware (verified 2026-11-22: edit-buffer readback stayed
    unchanged). Only the slot number actually loads the sound.
    """
    out = collect(irr, f"load-patch {slot}", max_empty=3, max_s=10.0,
                  sentinel_every=0.5)
    low = out.lower()
    if any(t in low for t in ("error", "not found", "fail", "f_opendir")):
        raise RuntimeError(f"load-patch {slot}: {out!r}")


VERIFY_PARAMS = ("Osc1FinePitch", "Filter1CutOff", "Filter1EnvAmount")


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
    ap.add_argument("--slot-start", type=int, default=None,
                    help="override the manifest slots: entry i is loaded from "
                         "slot-start+i (the Iridium numbers imported patches "
                         "by file order, e.g. 200)")
    ap.add_argument("--hold", type=float, default=1.2)
    ap.add_argument("--tail", type=float, default=0.9)
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
    all_entries = manifest["entries"]
    entries = parse_only(args.only, all_entries)
    if args.slot_start is not None:
        order = {e["loc"]: n for n, e in enumerate(all_entries)}
        for e in entries:
            e["slot"] = args.slot_start + order[e["loc"]]
        print(f"slot base {args.slot_start}: "
              f"{entries[0]['loc']} -> {entries[0]['slot']}, "
              f"{entries[-1]['loc']} -> {entries[-1]['slot']}")
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

    # `ls` stalls the device readout for a while, so verify in a throw-away
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
        pids = {name: find_pid(irr, name) for name in VERIFY_PARAMS}
        print("verify pids:", pids, flush=True)
        scores = []
        silent_streak = 0
        for i, e in enumerate(entries, 1):
            loc, sd_name = e["loc"], e["sd_name"]
            pending = [n for n in notes if (loc, n) not in done]
            if not pending:
                continue
            expected = qpat.load(args.manifest.parent / sd_name)["params"]
            load_patch(irr, int(e["slot"]))
            verify_patch(irr, expected, pids)
            select_blofeld(blo, loc)
            for note in pending:
                data = capture_onset(blo, irr, note=note, vel=100,
                                     hold=args.hold, tail=args.tail)
                bx = np.asarray(data[list(audio.CHANNELS["blofeld"]), :],
                                dtype=np.float64).mean(axis=0)
                ix = np.asarray(data[list(audio.CHANNELS["iridium"]), :],
                                dtype=np.float64).mean(axis=0)
                rms = float(np.sqrt(np.mean(ix ** 2)))
                brms = float(np.sqrt(np.mean(bx ** 2)))
                # Dead Iridium path = true silence or >60 dB below the Blofeld.
                # A quiet patch (e.g. A003) must still be measured; a patch whose
                # amp envelope decays too fast is logged as an error row and the
                # run continues (3 silent sounds in a row -> abort: dead cable).
                dead = rms < 2e-5 or (brms > 1e-4 and rms / brms < 1e-3)
                silent_streak = silent_streak + 1 if dead else 0
                meta = {"mode": "rf100_v5", "protocol": "onset", "blofeld": loc, "note": note,
                        "qpat": sd_name, "sd_dir": sd_dir, "slot": e["slot"]}
                if dead:
                    print(f"  {loc} note{note}: Iridium silent (rms {rms:.2e}, "
                          f"blofeld {brms:.2e}) - logged as error", flush=True)
                    if silent_streak >= 3:
                        raise SystemExit("3 silent sounds in a row - check the "
                                         "Iridium audio cable / MIDI settings")
                elif rms < 5e-4:
                    print(f"  {loc} note{note}: quiet Iridium (rms {rms:.2e})",
                          flush=True)
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
