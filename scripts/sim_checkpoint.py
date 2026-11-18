#!/usr/bin/env python3
"""sim_checkpoint.py – Checkpoint-Messrunde: alle Presets × 4 Noten × Wheel-Stufen.

Iridium-PC-Umschaltung ist defekt (HANDOVER-2026-11-14) -> Manual-Panel-Modus:
pro Preset meldet das Skript einen Prompt („Set 6 PC<irr_pc> am Panel einstellen“),
der Mensch bestaetigt per Enter; das Skript sendet an den Iridium NUR Noten (ch6,
Part 1) und CC1 (Wheel). Blofeld-PC (Bank A: CC0=0, CC32=0, PC = Location-1, ch5)
setzt das Skript selbst.

Aufruf:  python3 scripts/sim_checkpoint.py [--only A001] [--irr-pc 108]
              [--notes 36,48,60,72] [--wheel 0,50,100] [--dur 2.0] [--full-all]
              [--no-wait] [--no-embed] [--no-llm] [--no-norm-pegel] [--profile]
              [--log PATH] [--wav-dir recordings]

Pro Kombination (Preset × Note × Wheel): ein JSONL-Eintrag im Log
(meta mode="checkpoint" + blofeld/blofeld_pc/irr_pc/bank/note/wheel_pct) ueber
sim_embed.score_pair_embed (Phase A + embed + combined) und pegel-angeglichene WAVs
(<wav-dir>/ab_<LOC>_<ts>_n<note>_w<pct>_{blo,irr}.wav). llm/profile nur an der
Referenz-Kombination (erste Wheel-Stufe + Note 72, sonst letzte Note), ausser
--full-all. Wheel wird nach JEDEM Preset auf 0 zurueckgesetzt (CC1 ch5 + ch6).
Am Ende Summary-Pivot (combined pro Preset × Note ueber die Wheel-Stufen).
Exit 1, wenn mind. eine Messung score=None (stumm) lieferte, sonst 0.
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
from sim_manual_compare import measure, set_wheel   # kein Duplikat
from sim_sweep_pcs import DEFAULT_MAP

REPO = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="nur eine Location (z. B. A001)")
    ap.add_argument("--irr-pc", type=int, default=None,
                    help="nur mit --only; Default DEFAULT_MAP[loc]")
    ap.add_argument("--notes", default="36,48,60,72",
                    help="kommagetrennte Noten, eine pro Oktave (Default 36,48,60,72 = C2-C5)")
    ap.add_argument("--wheel", default="0,50,100",
                    help="Modwheel-Stufen in %% (CC1) auf beiden Synths (Default '0,50,100')")
    ap.add_argument("--dur", type=float, default=2.0,
                    help="Aufnahmedauer pro Note in s (Default 2.0; tiefe Noten brauchen Release-Zeit)")
    ap.add_argument("--full-all", action="store_true",
                    help="llm/profile nicht nur an Referenz-Kombination, sondern ueberall")
    ap.add_argument("--no-wait", action="store_true",
                    help="kein Panel-Prompt warten (Tests/Non-interactive)")
    ap.add_argument("--log", default=str(sim.DEFAULT_LOG))
    ap.add_argument("--no-embed", action="store_true", help="CLAP-Embedding abschalten")
    ap.add_argument("--no-llm", action="store_true", help="ollama-LLM abschalten")
    ap.add_argument("--no-norm-pegel", action="store_true",
                    help="embed/LLM auf Roh-Pegel lassen (Default: auf Peak 0.5 angleichen)")
    ap.add_argument("--profile", action="store_true",
                    help="d1-omni noul-Profil (Erklaer-Schicht) mitloggen")
    ap.add_argument("--d1-model", default=sim_embed.DEFAULT_D1_MODEL)
    ap.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ap.add_argument("--wav-dir", default=str(REPO / "recordings"))
    ap.add_argument("--spec-png-dir", default=str(REPO / "recordings" / "spec"),
                    help="Side-by-Side-Spektrogramm-PNGs (A|B|Delta dB) pro Messung, "
                         "im Log verlinkt (Default recordings/spec/)")
    ap.add_argument("--no-spec-png", action="store_true",
                    help="kein Spektrogramm-PNG rendern")
    args = ap.parse_args(argv)

    notes = [int(n) for n in args.notes.split(",")]
    wheel_pcts = [float(w) for w in args.wheel.split(",")]
    ref_note = 72 if 72 in notes else notes[-1]
    only = args.only.upper() if args.only else None
    if only and only not in DEFAULT_MAP:
        ap.error(f"{only} nicht in DEFAULT_MAP (Set 6): {sorted(DEFAULT_MAP)}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_dir = Path(args.wav_dir)
    wav_dir.mkdir(parents=True, exist_ok=True)

    clap, ollama = sim_embed.build_backends(args.models_dir,
                                            want_embed=not args.no_embed,
                                            want_llm=not args.no_llm)
    d1 = sim_embed.build_profile_backend(args.profile, args.d1_model)

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
            # Blofeld: Bank A explizit + PC (CC0/CC32 = Bank select am BLOFELD).
            # Iridium: KEIN CC0/CC32/PC -- Favorit wird am Panel gewaehlt!
            blo.control_change(0, 0, channel=blo.channel)
            blo.control_change(32, 0, channel=blo.channel)
            blo.program_change(blo_pc, channel=blo.channel)
            time.sleep(0.7)
            if not args.no_wait:
                input(f"== {loc}: bitte am Iridium Favorites Set 6 PC{irr_pc} "
                      f"einstellen, dann Enter ==")
            print(f"== {loc} (blo PC{blo_pc} / irr Set6 PC{irr_pc}) ==", flush=True)
            for pct in wheel_pcts:
                set_wheel(blo, irr, pct)
                time.sleep(0.5)                     # Mod-Settling abwarten
                for note in notes:
                    bx, ix = measure(blo, irr, note, args.dur)
                    norm = not args.no_norm_pegel
                    wtag = f"_w{pct:.0f}"
                    # WAVs pegel-angeglichen (Peak 0.5), damit A/B per Anhoeren vergleichbar
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
                    r = sim_embed.score_pair_embed(bx, ix, sr=audio.SAMPLERATE, meta=meta,
                                                   log_path=args.log, clap=clap, ollama=ollama,
                                                   use_llm=not args.no_llm and full,
                                                   norm_pegel=norm,
                                                   profile_backend=d1 if full else None,
                                                   spec_png_dir=None if args.no_spec_png
                                                   else args.spec_png_dir)
                    print(f"-- {loc} note{note} wheel={pct:.0f}% --")
                    sim_embed.print_result(r, f"blofeld:{loc}", f"iridium:set6pc{irr_pc}")
                    if r.get("peak_dbfs"):
                        print(f"  peak_dbfs: A={r['peak_dbfs']['a']} B={r['peak_dbfs']['b']}")
                    if r["score"] is None:
                        fehler += 1
                        print(f"  WARNUNG: {loc} note{note} wheel{pct:.0f}% -> "
                              f"{r.get('error')}", file=sys.stderr)
                    summary.setdefault((loc, note), {})[pct] = (
                        r["score"], r.get("embed_score"), r.get("combined"))
            set_wheel(blo, irr, 0.0)   # Mod Wheel nach jedem Preset zuruecksetzen
    finally:
        blo.close()
        irr.close()

    print("\n== Summary (combined; ohne embed = Phase-A-score) ==")
    for (loc, note), wheels in summary.items():
        line = " ".join(f"w{int(p)}={v[2] if v[2] is not None else v[0]}"
                        for p, v in sorted(wheels.items()))
        print(f"{loc} n{note}: {line}")
    if fehler:
        print(f"\n{fehler} Messung(en) mit score=None (stumm) – siehe WARNUNGEN.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
