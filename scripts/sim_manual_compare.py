#!/usr/bin/env python3
"""sim_manual_compare.py – A/B comparison of ONE preset in manual-panel mode.

Iridium PC switching is currently broken (HANDOVER-2026-11-14): the human
selects the favorite on the Iridium panel (Set 6, PC per DEFAULT_MAP from
sim_sweep_pcs.py); the script sends ONLY notes (ch6, Part 1) to the Iridium.
The Blofeld PC (bank A: CC0=0, CC32=0, PC = location number - 1, ch5) is
set by the script itself.

Usage:  python3 scripts/sim_manual_compare.py A001 --irr-pc 108 [--notes 72]
             [--dur 1.6] [--log PATH] [--no-embed] [--no-llm] [--wav-dir recordings]

Per note: CC123=0 on all 16 channels of both synths, CC7=127 only on the Blofeld
(on the Iridium CC7 = Filter1 Amount with the rdb map!), then a note on both synths,
recording via Scarlett (Blofeld In3/4, Iridium In5/6), WAVs saved
(<wav-dir>/ab_<LOC>_<ts>_n<note>_blo.wav / _irr.wav), score Phase A + embed +
llm, one JSONL entry per note in the log (meta mode="manual_panel").
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import audio, midi, sim, sim_embed
from sim_sweep_pcs import DEFAULT_MAP

REPO = Path(__file__).resolve().parent.parent


def set_wheel(blo, irr, pct: float) -> int:
    """Set CC1 (mod wheel) on both synths. Iridium: CC1 is NOT assigned in the
    rdb-.mimap -> mod wheel stays standard CC1. Returns: CC value 0..127."""
    v = int(round(pct / 100.0 * 127))
    blo.control_change(1, v, channel=blo.channel)   # Blofeld ch5
    irr.control_change(1, v, channel=5)             # Iridium ch6 (Part 1)
    return v


def measure(blo, irr, note: int, dur: float):
    """Play one note on both synths + record -> (blofeld, iridium) mono."""
    for s in (blo, irr):
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    # CC7=127 only on the Blofeld (real volume). On the Iridium CC7 is Filter1 Amount
    # with the rdb-.mimap -- CC7=0/127 on ch6 would change/mute the sound!
    for ch in range(16):
        blo.control_change(7, 127, channel=ch)
    time.sleep(0.3)
    blo.note_on(note=note, velocity=100, channel=blo.channel)
    irr.note_on(note=note, velocity=100, channel=5)   # Part 1 (ch6) - monophonic
    time.sleep(0.25)                                   # wait for attack
    d = audio.record(duration=dur, channels=None)
    blo.note_off(note=note, channel=blo.channel)
    irr.note_off(note=note, channel=5)
    for s in (blo, irr):
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    bx = np.asarray(d[list(audio.CHANNELS["blofeld"]), :], dtype=np.float64).mean(axis=0)
    ix = np.asarray(d[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
    return bx, ix


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("loc", help="Blofeld location, e.g. A001")
    ap.add_argument("--irr-pc", type=int, default=None,
                    help="Iridium Favorites Set 6 PC (default: DEFAULT_MAP[loc])")
    ap.add_argument("--notes", default="72", help="comma-separated notes (default 72 = C5)")
    ap.add_argument("--wheel", default="0",
                    help="mod wheel steps in %% (CC1) on both synths, e.g. '0,50,100' "
                         "(default '0'); one measurement per step, reset to 0 at the end")
    ap.add_argument("--full-all", action="store_true",
                    help="llm/profile not only on the first wheel step, but on all")
    ap.add_argument("--dur", type=float, default=1.6)
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    ap.add_argument("--no-embed", action="store_true", help="disable CLAP embedding")
    ap.add_argument("--no-llm", action="store_true", help="disable ollama LLM")
    ap.add_argument("--no-norm-pegel", action="store_true",
                    help="leave embed/LLM at raw level (default: match to peak 0.5)")
    ap.add_argument("--profile", action="store_true",
                    help="log d1-omni noul profile (explanation layer)")
    ap.add_argument("--d1-model", default=sim_embed.DEFAULT_D1_MODEL)
    ap.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ap.add_argument("--wav-dir", default=str(REPO / "recordings"))
    args = ap.parse_args(argv)

    loc = args.loc.upper()
    if loc not in DEFAULT_MAP:
        ap.error(f"{loc} not in DEFAULT_MAP (Set 6): {sorted(DEFAULT_MAP)}")
    irr_pc = args.irr_pc if args.irr_pc is not None else DEFAULT_MAP[loc]
    blo_pc = int(loc[1:]) - 1
    notes = [int(n) for n in args.notes.split(",")]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_dir = Path(args.wav_dir)
    wav_dir.mkdir(parents=True, exist_ok=True)

    clap, ollama = sim_embed.build_backends(args.models_dir,
                                            want_embed=not args.no_embed,
                                            want_llm=not args.no_llm)
    d1 = sim_embed.build_profile_backend(args.profile, args.d1_model)

    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    try:
        # Blofeld: bank A explicitly + PC (CC0/CC32 = bank select on the BLOFELD).
        # Iridium: NO CC0/CC32/PC -- the favorite is selected on the panel!
        blo.control_change(0, 0, channel=blo.channel)
        blo.control_change(32, 0, channel=blo.channel)
        blo.program_change(blo_pc, channel=blo.channel)
        time.sleep(0.7)
        wheel_pcts = [float(w) for w in args.wheel.split(",")]
        for pct in wheel_pcts:
            set_wheel(blo, irr, pct)
            time.sleep(0.5)                             # wait for mod settling
            full = args.full_all or pct == wheel_pcts[0]
            for note in notes:
                bx, ix = measure(blo, irr, note, args.dur)
                norm = not args.no_norm_pegel
                # WAVs level-matched (peak 0.5) so A/B listening is comparable
                wtag = f"_w{pct:.0f}"
                if norm:
                    for arr, tag in ((bx, "blo"), (ix, "irr")):
                        p = sim_embed.peak_dbfs(arr)
                        if p > -120.0:
                            arr = arr * (0.5 / (10 ** (p / 20.0)))
                        sim_embed.write_wav(arr, audio.SAMPLERATE,
                                            wav_dir / f"ab_{loc}_{ts}_n{note}{wtag}_{tag}.wav")
                else:
                    sim_embed.write_wav(bx, audio.SAMPLERATE,
                                        wav_dir / f"ab_{loc}_{ts}_n{note}{wtag}_blo.wav")
                    sim_embed.write_wav(ix, audio.SAMPLERATE,
                                        wav_dir / f"ab_{loc}_{ts}_n{note}{wtag}_irr.wav")
                meta = {"mode": "manual_panel", "blofeld": loc, "blofeld_pc": blo_pc,
                        "wav": f"ab_{loc}_{ts}_n{note}{wtag}",
                        "irr_pc": irr_pc, "bank": 6, "note": note, "wheel_pct": pct}
                r = sim_embed.score_pair_embed(bx, ix, sr=audio.SAMPLERATE, meta=meta,
                                               log_path=args.log, clap=clap, ollama=ollama,
                                               use_llm=not args.no_llm and full,
                                               norm_pegel=norm,
                                               profile_backend=d1 if full else None)
                print(f"== {loc} (blo PC{blo_pc} / irr Set6 PC{irr_pc}) note{note} "
                      f"wheel={pct:.0f}% ==")
                sim_embed.print_result(r, f"blofeld:{loc}", f"iridium:set6pc{irr_pc}")
                if r.get("peak_dbfs"):
                    print(f"  peak_dbfs: A={r['peak_dbfs']['a']} B={r['peak_dbfs']['b']}")
                if r["score"] is None:
                    return 1
        set_wheel(blo, irr, 0.0)   # reset mod wheel on both synths
    finally:
        blo.close()
        irr.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
