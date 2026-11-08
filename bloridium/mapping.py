"""Mapping Blofeld-SNDD-Parameter -> Iridium-CC (siehe docs/MAPPING.md).

Quellen: Blofeld_sysex_v1_04.pdf (SDATA) + docs/midi-maps/iridium_midi_guide.csv.

Wichtig: Viele Blofeld-Parameter haben auf dem Iridium KEINEN CC (Mod-Matrix,
Filter-Typ, F1 Cutoff, Wavetable-Details, FM/Kernels). Diese landen im Report
als "unmapped". Werte-Skalierung: Blofeld bipolar (-64..+63, raw 0..127, Mitte 64)
wird 1:1 uebernommen (Iridium-CCs laut CSV ebenfalls 0..127, "0-based"); on/off
(0..1) -> 0..127.
"""

from __future__ import annotations

import csv
from pathlib import Path

IRIDIUM_CSV = Path(__file__).resolve().parent.parent / "docs" / "midi-maps" / "iridium_midi_guide.csv"


def load_iridium_cc() -> dict[str, int]:
    """name -> CC-Nummer aus der midi.guide-CSV."""
    out = {}
    with open(IRIDIUM_CSV) as f:
        for r in csv.DictReader(f):
            if r["cc_msb"]:
                out[r["parameter_name"]] = int(r["cc_msb"])
    return out


def _onoff(v: int) -> int:
    return 127 if v else 0


# Blofeld-OSC-VA-Shapes (Spec 4.1): 1 Pulse, 2 Saw, 3 Triangle, 4 Sine
VA_SHAPE_TO_WF = {"Pulse": 32, "Saw": 64, "Triangle": 96, "Sine": 127}  # ungefaehr, 0..127


def blofeld_to_iridium(parsed: dict, cc_map: dict[str, int] | None = None) -> tuple[list, list]:
    """parsed: Ergebnis von blofeld_dump.parse_sndd().

    Rückgabe: (messages, unmapped)
      messages: Liste von (iridium_param_name, cc, value, blofeld_name, note)
      unmapped: Liste von Blofeld-Parametern ohne CC-Mapping
    """
    cc = cc_map or load_iridium_cc()
    p = parsed["params"]
    sdata = parsed["sdata"]
    msgs: list[tuple[str, int, int, str, str]] = []
    unmapped: list[str] = []

    def add(ir_name: str, value: int, bf_name: str, note: str = ""):
        if ir_name == "__CC7__":  # CC7 = Output Level, nicht in CSV gelistet
            msgs.append(("CC7 Output Level", 7, max(0, min(127, int(value))), bf_name, note))
            return
        if ir_name not in cc:
            unmapped.append(f"{bf_name} -> {ir_name} (CC fehlt in CSV)")
            return
        msgs.append((ir_name, cc[ir_name], max(0, min(127, int(value))), bf_name, note))

    def skip(bf_name: str, reason: str):
        unmapped.append(f"{bf_name} ({reason})")

    # --- Oszillatoren ---
    osc_cc = {1: {"fine": "OSCN Fine Pitch", "vol": "OSCN VOL", "pan": "OSCN PAN",
                  "wt_table": "OSCN WT Table", "wt_pos": "OSCN WT Position",
                  "wf_shape": "OSCN WF Shape", "wf_pw": "OSCN WF PW"},
              2: {}, 3: {}}
    for n in (1, 2, 3):
        t = {k: v.replace("N", str(n)) for k, v in osc_cc[1].items()}
        # Detune -> Fine Pitch (bipolar, raw uebernehmen)
        add(t["fine"], p[f"Osc {n} Detune"], f"Osc {n} Detune")
        # Level -> VOL
        add(t["vol"], p[f"Mixer Osc {n} Level"], f"Mixer Osc {n} Level")
        # Balance -> PAN (Approx: F1/F2-Balance ~ Stereo-Pan)
        add(t["pan"], p[f"Mixer Osc {n} Balance"], f"Mixer Osc {n} Balance", "Balance->PAN approx")
        # Shape: VA-Shapes -> WF Shape, Wavetable-Shapes (>=5) -> WT Table
        shape = p[f"Osc {n} Shape"]
        idx = None
        for i, (name, _tbl) in enumerate([(k, None) for k in []]):
            pass
        # rohen Index zurueckgewinnen: parse_sndd gibt Label; wir brauchen den Rohwert
        raw_shape = sdata[[8, 24, 40][n - 1]]
        if isinstance(shape, str) and shape in VA_SHAPE_TO_WF:
            add(t["wf_shape"], VA_SHAPE_TO_WF[shape], f"Osc {n} Shape={shape}", "VA->WF approx")
        elif raw_shape >= 5:
            add(t["wt_table"], raw_shape, f"Osc {n} Shape=WT#{raw_shape}", "WT-Index->WT Table approx")
        else:
            skip(f"Osc {n} Shape={shape}", "off/unbekannt")
        # Pulsewidth -> WF PW
        add(t["wf_pw"], p[f"Osc {n} Pulsewidth"], f"Osc {n} Pulsewidth")
        for k in ("Octave", "Semitone", "Bend Range", "Keytrack", "FM Source", "FM Amount",
                  "PWM Source", "PWM Amount", "Limit WT", "Brilliance"):
            skip(f"Osc {n} {k}", "kein Iridium-CC")
    skip("Osc 2 Sync to O3", "kein CC (WF Sync evtl.)")
    for k in ("Osc Pitch Source", "Osc Pitch Amount", "Glide Mode"):
        skip(k, "kein CC")

    # --- Glide/Unisono/Allocation ---
    add("Glide ON OFF", _onoff(p.get("Glide", 0)), "Glide")
    add("Glide Rate", p.get("Glide Rate", 0), "Glide Rate")
    add("Unisono Count", p.get("Allocation/Unisono", 0), "Allocation/Unisono", "approx")
    add("Unisono Detune", p.get("Unisono Detune", 0), "Unisono Detune")

    # --- Mixer ---
    skip("Mixer Noise Level", "kein CC (Particle)")
    skip("Mixer Noise Balance", "kein CC")
    skip("Mixer Noise Colour", "kein CC")
    add("Ringmod OSC1 TO OSC2", p.get("Mixer RingMod Level", 0), "Mixer RingMod Level", "-> RM 1->2 approx")

    # --- Filter ---
    for n, base in ((1, "Filter1"), (2, "Filter2")):
        fcc = {"reso": f"{base} Reso", "amount": f"{base} Amount", "velo": f"{base} Velo Amount",
               "attack": f"{base} Attack", "decay": f"{base} Decay", "sustain": f"{base} Sustain",
               "release": f"{base} Release", "cutoff": f"{base} Cutoff"}
        add(fcc["reso"], p[f"Filter {n} Resonance"], f"Filter {n} Resonance")
        add(fcc["amount"], p[f"Filter {n} Env Amount"], f"Filter {n} Env Amount")
        add(fcc["velo"], p[f"Filter {n} Env Velocity"], f"Filter {n} Env Velocity")
        # Blofeld hat EINE Filter-Huelle -> auf F1-Env (und F2) mappen
        fe = "Filter Envelope"
        for key, ir in (("Attack", fcc["attack"]), ("Decay", fcc["decay"]),
                        ("Sustain", fcc["sustain"]), ("Release", fcc["release"])):
            add(ir, p[f"{fe} {key}"], f"{fe} {key}")
        if fcc["cutoff"] in cc:
            add(fcc["cutoff"], p[f"Filter {n} Cutoff"], f"Filter {n} Cutoff")
        else:
            skip(f"Filter {n} Cutoff", "kein CC in CSV")
        for k in ("Type", "Drive", "Drive Curve", "Keytrack", "Mod Source", "Mod Amount",
                  "FM Source", "FM Amount", "Pan", "Pan Source", "Pan Amount"):
            skip(f"Filter {n} {k}", "kein CC")
    skip("Filter Routing", "kein CC")

    # --- Amplifier ---
    add("AMP Velo Amount", p.get("Amplifier Velocity", 64), "Amplifier Velocity", "bipolar raw")
    ae = "Amplifier Envelope"
    for key, ir in (("Attack", "AMP Attack"), ("Decay", "AMP Decay"),
                    ("Sustain", "AMP Sustain"), ("Release", "AMP Release")):
        add(ir, p[f"{ae} {key}"], f"{ae} {key}")
    skip("Amplifier Mod Source", "kein CC")
    skip("Amplifier Mod Amount", "Mod-Matrix")
    # WICHTIG (empirisch): CC7 = Output/Main Level am Iridium; 0 = stumm!
    add("__CC7__", p.get("Amplifier Volume", 127), "Amplifier Volume", "CC7 = Output Level (0=stumm!)")

    # --- Envelopes 3/4 -> Free ENV1/2 ---
    for n, base in ((3, "Free ENV1"), (4, "Free ENV2")):
        for key, ir in (("Attack", f"{base} Attack"), ("Decay", f"{base} Decay"),
                        ("Sustain", f"{base} Sustain"), ("Release", f"{base} Release")):
            add(ir, p[f"Envelope {n} {key}"], f"Envelope {n} {key}")

    # --- LFO --- (Speed als Rohwert aus SDATA: LFO1=161, LFO2=173, LFO3=185)
    for n, ir in ((1, "LFO1 Speed"), (2, "LFO2 Speed"), (3, "LFO3 Speed")):
        raw = sdata[161 + (n - 1) * 12]
        add(ir, raw, f"LFO {n} Speed", "Clock-Index raw approx")
    for n in (1, 2, 3):
        for k in ("Shape", "Sync", "Clocked", "Start Phase", "Delay", "Fade", "Keytrack"):
            skip(f"LFO {n} {k}", "kein CC")

    # --- Modulation/Modifier ---
    for m in range(1, 17):
        for k in ("Source", "Destination", "Amount"):
            skip(f"Modulation {m} {k}", "Mod-Matrix, kein CC")
    for m in range(1, 5):
        for k in ("Source A", "Source B", "Operation", "Constant"):
            skip(f"Modifier {m} {k}", "kein CC")

    # --- FX (approximativ nach Typ) ---
    fx_map = {"Chorus": "Chorus DRY WET", "Flanger": "Flanger DRY WET", "Phaser": "Phaser DRY WET",
              "Overdrive": "Drive DRY WET", "Delay": "Delay DRY WET", "Clk.Delay": "Delay DRY WET",
              "Reverb": "Reverb Gain", "Triple FX": None, "Bypass": None}
    for n in (1, 2):
        t = p[f"Effect {n} Type"]
        mix = p[f"Effect {n} Mix"]
        target = fx_map.get(t) if isinstance(t, str) else None
        if target:
            add(target, mix, f"Effect {n} Mix ({t})")
        else:
            skip(f"Effect {n} Type={t}", "kein CC/passend")
        for k in range(1, 15):
            skip(f"Effect {n} Parameter {k}", "kein CC pro Parameter")

    # --- Arp ---
    for k in list(p.keys()):
        if k.startswith("Arp"):
            skip(k, "kein CC")

    return msgs, unmapped
