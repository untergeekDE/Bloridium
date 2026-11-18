#!/usr/bin/env python3
"""sim_checkpoint.py – checkpoint measurement run: all presets x 4 notes x wheel steps.

Iridium PC switching is broken (HANDOVER-2026-11-14) -> manual panel mode:
per preset the script shows a prompt ("set Set 6 PC<irr_pc> on the panel"),
the human confirms with Enter; the script sends ONLY notes (ch6,
Part 1) and CC1 (wheel) to the Iridium. The Blofeld PC (bank A: CC0=0, CC32=0, PC = location-1, ch5)
is set by the script itself.

Usage:  python3 scripts/sim_checkpoint.py [--only A001] [--irr-pc 108]
              [--notes 36,48,60,72] [--wheel 0,50,100] [--dur 2.0] [--full-all]
              [--no-wait] [--no-embed] [--no-llm] [--no-norm-pegel] [--profile]
              [--log PATH] [--wav-dir recordings]

Per combination (preset x note x wheel): one JSONL entry in the log
(meta mode="checkpoint" + blofeld/blofeld_pc/irr_pc/bank/note/wheel_pct) via
sim_embed.score_pair_embed (Phase A + embed + combined) and level-matched WAVs
(<wav-dir>/ab_<LOC>_<ts>_n<note>_w<pct>_{blo,irr}.wav). llm/profile only on the
reference combination (first wheel step + note 72, else last note), unless
--full-all. Wheel is reset to 0 after EVERY preset (CC1 ch5 + ch6).
At the end a summary pivot (combined per preset x note across the wheel steps).
Exit 1 if at least one measurement returned score=None (silent), else 0.
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

from bloridium import audio, midi, sim, sim_embed, specdiff
from sim_manual_compare import measure, set_wheel   # no duplication
from sim_sweep_pcs import DEFAULT_MAP

REPO = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="only one location (e.g. A001)")
    ap.add_argument("--irr-pc", type=int, default=None,
                    help="only with --only; default DEFAULT_MAP[loc]")
    ap.add_argument("--notes", default="36,48,60,72",
                    help="comma-separated notes, one per octave (default 36,48,60,72 = C2-C5)")
    ap.add_argument("--wheel", default="0,50,100",
                    help="mod wheel steps in %% (CC1) on both synths (default '0,50,100')")
    ap.add_argument("--dur", type=float, default=2.0,
                    help="recording duration per note in s (default 2.0; low notes need release time)")
    ap.add_argument("--full-all", action="store_true",
                    help="llm/profile not only on the reference combination, but everywhere")
    ap.add_argument("--no-wait", action="store_true",
                    help="do not wait for the panel prompt (tests/non-interactive)")
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
    ap.add_argument("--spec-png-dir", default=str(REPO / "recordings" / "spec"),
                    help="side-by-side spectrogram PNGs (A|B|delta dB) per measurement, "
                         "linked in the log (default recordings/spec/)")
    ap.add_argument("--no-spec-png", action="store_true",
                    help="do not render a spectrogram PNG")
    ap.add_argument("--specdiff", action="store_true",
                    help="interpret the spectral diff per measurement (result.specdiff + "
                         "specdiff_score in the log); vision model only on the reference "
                         "combination, DSP elsewhere (like --profile)")
    ap.add_argument("--specdiff-backend", choices=["systemone", "chat"], default="systemone")
    ap.add_argument("--specdiff-model", default=specdiff.DEFAULT_SPECDIFF_MODEL)
    args = ap.parse_args(argv)

    notes = [int(n) for n in args.notes.split(",")]
    wheel_pcts = [float(w) for w in args.wheel.split(",")]
    ref_note = 72 if 72 in notes else notes[-1]
    only = args.only.upper() if args.only else None
    if only and only not in DEFAULT_MAP:
        ap.error(f"{only} not in DEFAULT_MAP (Set 6): {sorted(DEFAULT_MAP)}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_dir = Path(args.wav_dir)
    wav_dir.mkdir(parents=True, exist_ok=True)

    clap, ollama = sim_embed.build_backends(args.models_dir,
                                            want_embed=not args.no_embed,
                                            want_llm=not args.no_llm)
    d1 = sim_embed.build_profile_backend(args.profile, args.d1_model)
    sd_backend = (specdiff.build_backend(True, args.specdiff_model,
                                         args.specdiff_backend)
                  if args.specdiff else None)

    blo = midi.connect("blofeld")
    irr = midi.connect("iridium")
    fehler = 0
    summary: dict[tuple[str, int], dict[float, tuple]] = {}
    try:
        for loc, irr_pc_map in DEFAULT_MAP.items():
            if only and loc != only:
                continue
            irr_pc = args.irr_pc if (only and args.irr_pc is not None) else irr_pc_map
            blo_pc = int(loc[1:]) - 1
            # Blofeld: bank A explicitly + PC (CC0/CC32 = bank select on the BLOFELD).
            # Iridium: NO CC0/CC32/PC -- the favorite is selected on the panel!
            blo.control_change(0, 0, channel=blo.channel)
            blo.control_change(32, 0, channel=blo.channel)
            blo.program_change(blo_pc, channel=blo.channel)
            time.sleep(0.7)
            if not args.no_wait:
                input(f"== {loc}: please select Favorites Set 6 PC{irr_pc} on the Iridium, "
                      f"then Enter ==")
            print(f"== {loc} (blo PC{blo_pc} / irr Set6 PC{irr_pc}) ==", flush=True)
            for pct in wheel_pcts:
                set_wheel(blo, irr, pct)
                time.sleep(0.5)                     # wait for mod settling
                for note in notes:
                    bx, ix = measure(blo, irr, note, args.dur)
                    norm = not args.no_norm_pegel
                    wtag = f"_w{pct:.0f}"
                    # WAVs level-matched (peak 0.5) so A/B listening is comparable
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
                    meta = {"mode": "checkpoint", "blofeld": loc, "blofeld_pc": blo_pc,
                            "irr_pc": irr_pc, "bank": 6, "note": note, "wheel_pct": pct}
                    full = args.full_all or (pct == wheel_pcts[0] and note == ref_note)
                    sd_mode = ("vision" if full else "dsp") if args.specdiff else "off"
                    r = sim_embed.score_pair_embed(bx, ix, sr=audio.SAMPLERATE, meta=meta,
                                                   log_path=args.log, clap=clap, ollama=ollama,
                                                   use_llm=not args.no_llm and full,
                                                   norm_pegel=norm,
                                                   profile_backend=d1 if full else None,
                                                   spec_png_dir=None if args.no_spec_png
                                                   else args.spec_png_dir,
                                                   specdiff_mode=sd_mode,
                                                   specdiff_backend=sd_backend)
                    print(f"-- {loc} note{note} wheel={pct:.0f}% --")
                    sim_embed.print_result(r, f"blofeld:{loc}", f"iridium:set6pc{irr_pc}")
                    if r.get("peak_dbfs"):
                        print(f"  peak_dbfs: A={r['peak_dbfs']['a']} B={r['peak_dbfs']['b']}")
                    if r["score"] is None:
                        fehler += 1
                        print(f"  WARNING: {loc} note{note} wheel{pct:.0f}% -> "
                              f"{r.get('error')}", file=sys.stderr)
                    summary.setdefault((loc, note), {})[pct] = (
                        r["score"], r.get("embed_score"), r.get("combined"))
            set_wheel(blo, irr, 0.0)   # reset mod wheel after each preset (so presets don't influence each other)
    finally:
        blo.close()
        irr.close()

    print("\n== Summary (combined; without embed = Phase-A score) ==")
    for (loc, note), wheels in summary.items():
        line = " ".join(f"w{int(p)}={v[2] if v[2] is not None else v[0]}"
                        for p, v in sorted(wheels.items()))
        print(f"{loc} n{note}: {line}")
    if fehler:
        print(f"\n{fehler} measurement(s) with score=None (silent) – see WARNINGS.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
