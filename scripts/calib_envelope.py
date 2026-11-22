#!/usr/bin/env python3
"""Envelope time calibration: Blofeld raw <-> Iridium norm.

Measures attack / decay / release times on both synths with a clean test patch
(single saw oscillator, filter open, FX off) and prints the time curves.

Usage:
    python3 scripts/calib_envelope.py blo [--param attack] [--values 0,32,64,96,127]
    python3 scripts/calib_envelope.py irr --param decay
    python3 scripts/calib_envelope.py all           # both synths, all params
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, blofeld_dump as bd, midi  # noqa: E402
from _device_tool import Iridium  # noqa: E402
import measure_rf100 as R  # noqa: E402

SR = audio.SAMPLERATE
DEFAULT_VALUES = {"attack": [0, 16, 32, 48, 64, 80, 96, 112, 127],
                  "decay": [0, 16, 32, 48, 64, 80, 96, 112, 127],
                  "release": [0, 16, 32, 48, 64, 80, 96, 112, 127]}


# ---------------------------------------------------------------- setup ----
def setup_blofeld(bl, attack: int, decay: int, sustain: int, release: int) -> None:
    """Clean init-style patch via SNDP (indices == SDATA indices)."""
    bl.control_change(0, 0, channel=bl.channel)
    bl.control_change(32, 0, channel=bl.channel)
    bl.program_change(81, channel=bl.channel)   # A082 Init
    time.sleep(0.6)
    vals = {
        61: 127, 63: 0, 65: 0, 67: 0, 71: 0,       # oscillator levels
        8: 2, 24: 0, 40: 0,                       # shapes
        117: 1, 77: 1, 78: 127, 80: 0, 81: 0, 87: 64,  # filter 1 open, serial
        97: 0,                                    # F2 bypass
        128: 0, 129: 0, 144: 0, 145: 0,           # FX off
        121: 127, 122: 64,                        # amp volume/velocity
        208: 0, 211: attack, 213: decay, 214: sustain, 217: release,
    }
    for idx, value in vals.items():
        bl.send_sysex(bd.build_sndp(idx, value))
        time.sleep(0.012)
    time.sleep(0.4)


def setup_iridium(irr: Iridium, attack: float, decay: float, sustain: float,
                  release: float) -> None:
    R.collect(irr, "init-patch", max_s=15)
    cmds = [
        "set-param Osc1Type 1", "set-param Osc1WaveformShape 0",
        "set-param Osc1Vol 1", "set-param Osc2Vol 0", "set-param Osc3Vol 0",
        "set-param Osc1Destination 0",
        "set-param FilterState 1", "set-param Filter2State 2",
        "set-param FilterLink 0", "set-param FilterLevel 1",
        "set-param Filter2Level 0", "set-param FilterFormerRouting 0",
        "set-param DigiFormerType 0", "set-param FX1Type 0", "set-param FX2Type 0",
        "set-param MainVolume 1",
        f"set-param AmpEnvAttack {attack}", f"set-param AmpEnvDecay {decay}",
        f"set-param AmpEnvSustain {sustain}", f"set-param AmpEnvRelease {release}",
    ]
    R.collect_many(irr, cmds, max_s=30)


# ------------------------------------------------------------ measurement ----
def play_and_record(synth, hold: float, record_s: float, note: int = 60) -> np.ndarray:
    def play():
        time.sleep(0.4)                    # capture start latency
        synth.note_on(note=note, velocity=100)
        time.sleep(hold)
        synth.note_off(note=note)
    th = threading.Thread(target=play)
    th.start()
    data = audio.record(duration=record_s, channels=None)
    th.join()
    return data


def envelope_db(x: np.ndarray, win: float = 0.01) -> tuple[np.ndarray, float]:
    n = max(1, int(win * SR))
    x = np.asarray(x, dtype=np.float64)
    m = len(x) // n
    rms = np.sqrt(np.mean(x[:m * n].reshape(m, n) ** 2, axis=1))
    return 20 * np.log10(rms + 1e-12), win


def measure_times(x: np.ndarray, hold: float) -> dict:
    env, win = envelope_db(x)
    peak = float(env.max())
    if peak < -70:
        return {"peak": peak, "attack": None, "decay": None, "release": None}
    onset_i = int(np.argmax(env > peak - 40))
    peak_i = int(np.argmax(env))
    # onset is the last index below -40 dB before the peak
    before = np.where(env[:peak_i + 1] > peak - 40)[0]
    onset_i = int(before[0]) if len(before) else 0
    attack = (peak_i - onset_i) * win

    # sustain level = median at the end of the hold (before note off)
    note_off_i = int((0.4 + hold) / win)
    note_off_i = min(note_off_i, len(env) - 1)
    sustain = float(np.median(env[max(0, note_off_i - 20):note_off_i])) if note_off_i > 20 else peak
    # decay: peak -> sustain + 5% of the drop (or -26 dB below peak if sustain is low)
    target = max(sustain + (peak - sustain) * 0.05, peak - 26)
    after = np.where(env[peak_i:] < target)[0]
    decay = (after[0]) * win if len(after) else None
    # release: note off -> -26 dB below the sustain level
    rel_target = sustain - 26
    rel = np.where(env[note_off_i:] < rel_target)[0]
    release = rel[0] * win if len(rel) else None
    return {"peak": peak, "attack": attack, "decay": decay, "release": release,
            "sustain_db": sustain}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("synth", choices=("blo", "irr", "all"))
    ap.add_argument("--param", choices=("attack", "decay", "release", "all"),
                    default="all")
    ap.add_argument("--values", default=None, help="comma-separated")
    args = ap.parse_args(argv)
    params = ["attack", "decay", "release"] if args.param == "all" else [args.param]

    irr = Iridium() if args.synth in ("irr", "all") else None
    bl = midi.connect("blofeld") if args.synth in ("blo", "all") else None
    try:
        for param in params:
            values = ([int(v) for v in args.values.split(",")] if args.values
                      else DEFAULT_VALUES[param])
            print(f"\n## {param}  ({args.synth})", flush=True)
            for raw in values:
                if args.synth in ("blo", "all"):
                    attack, decay, sustain, release = 0, 64, 127, 64
                    if param == "attack":
                        attack, sustain = raw, 127
                    elif param == "decay":
                        decay, sustain = raw, 0
                    else:
                        release, sustain = raw, 127
                    setup_blofeld(bl, attack, decay, sustain, release)
                    hold = 1.2 if param != "release" else 1.2
                    rec = play_and_record(bl, hold=hold, record_s=5.0)
                    x = np.asarray(rec[list(audio.CHANNELS["blofeld"]), :],
                                   dtype=np.float64).mean(axis=0)
                    t = measure_times(x, hold)
                    print(f"  raw {raw:3d}: peak {t['peak']:6.1f} dB  "
                          f"A {fmt(t['attack'])}  D {fmt(t['decay'])}  "
                          f"R {fmt(t['release'])}", flush=True)
                if args.synth in ("irr", "all"):
                    attack, decay, sustain, release = 0.0, 0.5, 1.0, 0.5
                    norm = raw / 127.0
                    if param == "attack":
                        attack, sustain = norm, 1.0
                    elif param == "decay":
                        decay, sustain = norm, 0.0
                    else:
                        release, sustain = norm, 1.0
                    setup_iridium(irr, attack, decay, sustain, release)
                    hold = 1.2
                    rec = play_and_record(irr, hold=hold, record_s=5.0)
                    x = np.asarray(rec[list(audio.CHANNELS["iridium"]), :],
                                   dtype=np.float64).mean(axis=0)
                    t = measure_times(x, hold)
                    print(f"  norm {norm:.3f} (raw {raw:3d}): peak {t['peak']:6.1f} dB  "
                          f"A {fmt(t['attack'])}  D {fmt(t['decay'])}  "
                          f"R {fmt(t['release'])}", flush=True)
    finally:
        if irr:
            irr.close()
        if bl:
            bl.close()
    return 0


def fmt(v):
    return "  n/a" if v is None else f"{v:5.2f}s"


if __name__ == "__main__":
    sys.exit(main())
