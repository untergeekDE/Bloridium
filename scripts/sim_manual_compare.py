#!/usr/bin/env python3
"""sim_manual_compare.py – A/B-Vergleich EINES Presets im Manual-Panel-Modus.

Iridium-PC-Umschaltung ist derzeit defekt (HANDOVER-2026-11-14): der Human
waehlt den Favoriten am Iridium-Panel (Set 6, PC lt. DEFAULT_MAP aus
sim_sweep_pcs.py), das Skript sendet an den Iridium NUR Noten (ch6, Part 1).
Blofeld-PC (Bank A: CC0=0, CC32=0, PC = Location-Nummer - 1, ch5) setzt das
Skript selbst.

Aufruf:  python3 scripts/sim_manual_compare.py A001 --irr-pc 108 [--notes 72]
             [--dur 1.6] [--log PATH] [--no-embed] [--no-llm] [--wav-dir recordings]

Pro Note: CC123=0 auf allen 16 Kanaelen beider Synths, CC7=127 nur am Blofeld
(am Iridium ist CC7 mit rdb-Map = Filter1 Amount!), dann Note auf beiden Synths,
Aufnahme ueber Scarlett (Blofeld In3/4, Iridium In5/6), WAVs abgelegt
(<wav-dir>/ab_<LOC>_<ts>_n<note>_blo.wav / _irr.wav), Score Phase A + embed +
llm, ein JSONL-Eintrag pro Note im Log (meta mode="manual_panel").
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
    """CC1 (Mod Wheel) auf beiden Synths setzen. Iridium: CC1 ist in der rdb-.mimap
    NICHT belegt -> Mod Wheel bleibt Standard-CC1. Rueckgabe: CC-Wert 0..127."""
    v = int(round(pct / 100.0 * 127))
    blo.control_change(1, v, channel=blo.channel)   # Blofeld ch5
    irr.control_change(1, v, channel=5)             # Iridium ch6 (Part 1)
    return v


def measure(blo, irr, note: int, dur: float):
    """Eine Note auf beiden Synths spielen + aufnehmen -> (blofeld, iridium) mono."""
    for s in (blo, irr):
        for ch in range(16):
            s.control_change(123, 0, channel=ch)
    # CC7=127 nur am Blofeld (echtes Volume). Am Iridium ist CC7 mit rdb-.mimap
    # Filter1 Amount -- CC7=0/127 auf ch6 wuerde den Sound veraendern/stummen!
    for ch in range(16):
        blo.control_change(7, 127, channel=ch)
    time.sleep(0.3)
    blo.note_on(note=note, velocity=100, channel=blo.channel)
    irr.note_on(note=note, velocity=100, channel=5)   # Part 1 (ch6) - monophon
    time.sleep(0.25)                                   # Attack abwarten
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
    ap.add_argument("loc", help="Blofeld-Location, z. B. A001")
    ap.add_argument("--irr-pc", type=int, default=None,
                    help="Iridium Favorites-Set-6-PC (Default: DEFAULT_MAP[loc])")
    ap.add_argument("--notes", default="72", help="kommagetrennte Noten (Default 72 = C5)")
    ap.add_argument("--wheel", default="0",
                    help="Modwheel-Stufen in %% (CC1) auf beiden Synths, z. B. '0,50,100' "
                         "(Default '0'); pro Stufe eine Messung, Reset auf 0 am Ende")
    ap.add_argument("--full-all", action="store_true",
                    help="llm/profile nicht nur bei erster Wheel-Stufe, sondern bei allen")
    ap.add_argument("--dur", type=float, default=1.6)
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
    args = ap.parse_args(argv)

    loc = args.loc.upper()
    if loc not in DEFAULT_MAP:
        ap.error(f"{loc} nicht in DEFAULT_MAP (Set 6): {sorted(DEFAULT_MAP)}")
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
        # Blofeld: Bank A explizit + PC (CC0/CC32 = Bank select am BLOFELD).
        # Iridium: KEIN CC0/CC32/PC -- Favorit wird am Panel gewaehlt!
        blo.control_change(0, 0, channel=blo.channel)
        blo.control_change(32, 0, channel=blo.channel)
        blo.program_change(blo_pc, channel=blo.channel)
        time.sleep(0.7)
        wheel_pcts = [float(w) for w in args.wheel.split(",")]
        for pct in wheel_pcts:
            set_wheel(blo, irr, pct)
            time.sleep(0.5)                             # Mod-Settling abwarten
            full = args.full_all or pct == wheel_pcts[0]
            for note in notes:
                bx, ix = measure(blo, irr, note, args.dur)
                norm = not args.no_norm_pegel
                # WAVs pegel-angeglichen (Peak 0.5), damit A/B per Anhoeren vergleichbar ist
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
        set_wheel(blo, irr, 0.0)   # Mod Wheel auf beiden Synths zuruecksetzen
    finally:
        blo.close()
        irr.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
