"""Mapping Blofeld-SNDD -> Iridium/Quantum .qpat-Parameter (Key-Level).

Werte: Blofeld raw 0..127 -> Iridium norm = raw/127 (bei 0..1-Parametern);
bipolar (Mitte 64) -> raw/127 (0.5 ~ Mitte). Enums siehe Tabellen unten
(aus offiziellen Factory-.qpat extrahiert).
"""

from __future__ import annotations

# Enum-Tabellen (display -> value) aus docs/refs/qpat (Factory-Soundsets)
OSC_TYPE = {"Wavetable": 0.0, "Waveform": 1.0, "Particle": 2.0, "Resonator": 3.0, "Off": 4.0}
WF_SHAPE = {"Sawtooth": 0.0, "Sine": 1.0, "Triangle": 2.0, "Square": 3.0,
            "Pink Noise": 4.0, "White Noise": 5.0}
FILTER12_TYPE = {"12dB LP": 0.0, "24dB LP": 1.0, "12dB sat. LP": 2.0, "24dB sat. LP": 3.0}
FX_TYPE = {"Off": 0.0, "Phaser": 1.0, "Chorus": 2.0, "Flanger": 3.0, "Delay": 4.0,
           "Reverb": 5.0, "EQ": 6.0, "Drive": 7.0, "Compressor": 8.0}

# Blofeld Shape (Spec 4.1) -> Iridium (OscType, WF-Shape)
BLOFELD_SHAPE_TO_IRIDIUM = {
    "off": ("Off", None), "Pulse": ("Waveform", "Square"), "Saw": ("Waveform", "Sawtooth"),
    "Triangle": ("Waveform", "Triangle"), "Sine": ("Waveform", "Sine"),
}
# Blofeld Filter-Type (Spec 4.4) -> Iridium Filter12Type
BLOFELD_FILTER_TO_IRIDIUM = {
    "Bypass": None, "LP 24dB": "24dB LP", "LP 12dB": "12dB LP", "PPG LP": "12dB LP",
    "BP 24dB": "24dB LP", "BP 12dB": "12dB LP", "HP 24dB": "24dB LP", "HP 12dB": "12dB LP",
    "Notch24dB": "24dB LP", "Notch12dB": "12dB LP", "Comb+": "24dB LP", "Comb-": "24dB LP",
}
# Blofeld FX-Type (Spec 5.1) -> Iridium FX1/FX2-Type
BLOFELD_FX_TO_IRIDIUM = {
    "Bypass": "Off", "Chorus": "Chorus", "Flanger": "Flanger", "Phaser": "Phaser",
    "Overdrive": "Drive", "Triple FX": "Chorus", "Delay": "Delay", "Clk.Delay": "Delay",
    "Reverb": "Reverb",
}


def norm(raw: int) -> float:
    """Blofeld raw 0..127 -> Iridium norm 0..1."""
    return max(0.0, min(1.0, raw / 127.0))


def blofeld_to_qpat_params(parsed: dict) -> tuple[dict, list]:
    """parsed: blofeld_dump.parse_sndd(). -> (overrides, unmapped)

    overrides: {qpat_key: (value_float, display_str)}
    """
    p = parsed["params"]
    sdata = parsed["sdata"]
    ov: dict[str, tuple[float, str]] = {}
    unmapped: list[str] = []

    def setp(key, value, display=""):
        ov[key] = (float(value), display)

    # --- Oszillatoren ---
    shape_raw_idx = [8, 24, 40]     # SDATA-Indizes OscN Shape
    oct_idx = [1, 17, 33]
    semi_idx = [2, 18, 34]
    for n in (1, 2, 3):
        raw_shape = sdata[shape_raw_idx[n - 1]]
        # Shape-Label aus parsed params holen
        shape_label = p[f"Osc {n} Shape"]
        if isinstance(shape_label, str) and shape_label in BLOFELD_SHAPE_TO_IRIDIUM:
            otype, wf = BLOFELD_SHAPE_TO_IRIDIUM[shape_label]
        elif raw_shape >= 5:
            otype, wf = "Wavetable", None
        else:
            otype, wf = "Off", None
        setp(f"Osc{n}Type", OSC_TYPE[otype], otype)
        if wf:
            setp(f"Osc{n}WaveformShape", WF_SHAPE[wf], wf)
        # CoarsePitch: Blofeld Octave (raw 64 = 8', Schritte 12) + Semitone (raw 64 = 0)
        oct_up = (64 - sdata[oct_idx[n - 1]]) / 12.0
        semi = sdata[semi_idx[n - 1]] - 64
        setp(f"Osc{n}CoarsePitch", 24.0 + 12.0 * oct_up + semi, f"{semi:+.0f} semi")
        setp(f"Osc{n}FinePitch", norm(p[f"Osc {n} Detune"]), "")
        setp(f"Osc{n}Vol", norm(p[f"Mixer Osc {n} Level"]), "")
        setp(f"Osc{n}Pan", norm(p[f"Mixer Osc {n} Balance"]), "")
        setp(f"Osc{n}WaveformPW", norm(p[f"Osc {n} Pulsewidth"]), "")
        for k in ("Bend Range", "Keytrack", "FM Source", "FM Amount", "PWM Source",
                  "PWM Amount", "Limit WT", "Brilliance"):
            unmapped.append(f"Osc {n} {k}")
    unmapped += ["Osc 2 Sync to O3", "Osc Pitch Source", "Osc Pitch Amount"]

    # --- Glide / Unisono ---
    setp("GlideOnOff", 1.0 if p.get("Glide") else 0.0, "On" if p.get("Glide") else "Off")
    setp("GlideRate", norm(p.get("Glide Rate", 0)))
    setp("UnisonoCount", norm((p.get("Allocation/Unisono", 0) >> 5) & 0x07 or 1))
    setp("UnisonoDetune", norm(p.get("Unisono Detune", 0)))

    # --- Mixer extras ---
    setp("RingmodOsc12", norm(p.get("Mixer RingMod Level", 0))) if "RingmodOsc12" else None
    unmapped += ["Mixer Noise Level/Balance/Colour (kein direktes qpat-Key)"]

    # --- Filter ---
    f1_label = p["Filter 1 Type"]
    f12 = BLOFELD_FILTER_TO_IRIDIUM.get(f1_label if isinstance(f1_label, str) else "", "24dB LP")
    if f12:
        setp("Filter12Type", FILTER12_TYPE[f12], f12)
    else:
        setp("FilterState", 1.0, "Bypass")  # Bypass
    setp("Filter1CutOff", norm(p["Filter 1 Cutoff"]))
    setp("Filter1Reso", norm(p["Filter 1 Resonance"]))
    setp("Filter2CutOff", norm(p["Filter 2 Cutoff"]))
    setp("Filter2Reso", norm(p["Filter 2 Resonance"]))
    setp("Filter1EnvAmount", norm(p["Filter 1 Env Amount"]))
    setp("Filter1VeloAmount", norm(p["Filter 1 Env Velocity"]))
    setp("Filter2EnvAmount", norm(p["Filter 2 Env Amount"]))
    setp("Filter2VeloAmount", norm(p["Filter 2 Env Velocity"]))
    fe = "Filter Envelope"
    for bk, ik in (("Attack", "Filter1EnvAttack"), ("Decay", "Filter1EnvDecay"),
                   ("Sustain", "Filter1EnvSustain"), ("Release", "Filter1EnvRelease")):
        setp(ik, norm(p[f"{fe} {bk}"]))
        setp(ik.replace("Filter1", "Filter2"), norm(p[f"{fe} {bk}"]))
    unmapped += ["Filter N Drive/Curve/Keytrack/Mod/FM/Pan", "Filter Routing"]

    # --- Amp ---
    setp("MainVolume", norm(p.get("Amplifier Volume", 127)))
    setp("LayerVolume", 1.0)
    setp("AmpVeloAmount", norm(p.get("Amplifier Velocity", 64)))
    ae = "Amplifier Envelope"
    for bk, ik in (("Attack", "AmpEnvAttack"), ("Decay", "AmpEnvDecay"),
                   ("Sustain", "AmpEnvSustain"), ("Release", "AmpEnvRelease")):
        setp(ik, norm(p[f"{ae} {bk}"]))

    # --- Env 3/4 -> FreeEnv1/2 ---
    for n, base in ((3, "FreeEnv1"), (4, "FreeEnv2")):
        for bk, ik in (("Attack", f"{base}Attack"), ("Decay", f"{base}Decay"),
                       ("Sustain", f"{base}Sustain"), ("Release", f"{base}Release")):
            setp(ik, norm(p[f"Envelope {n} {bk}"]))

    # --- LFO ---
    for n in (1, 2, 3):
        raw = sdata[161 + (n - 1) * 12]  # LFO N Speed (Clock-Index)
        setp(f"LFO{n}Speed", norm(raw))
        unmapped.append(f"LFO {n} Shape/Sync/Delay/Fade/Keytrack")

    # --- Modulation/Matrix: Blofeld 16 Slots -> Iridium Matrix 1..16 ---
    mod_src = {"off": 0.0, "LFO 1": None, "LFO1*MW": None, "LFO 2": None, "LFO2*Press": None,
               "LFO 3": None, "FilterEnv": None, "AmpEnv": None, "Env3": None, "Env4": None,
               "Keytrack": None, "Velocity": None, "Rel. Velo": None, "Pressure": None,
               "Poly Press": None, "Pitch Bend": None, "Mod Wheel": None, "Sustain": None,
               "Foot Ctrl": None, "BreathCtrl": None}
    for m in range(1, 17):
        src = p[f"Modulation {m} Source"]
        if isinstance(src, str) and src != "off":
            unmapped.append(f"Modulation {m} ({src} -> {p[f'Modulation {m} Destination']})")
        setp(f"MatrixAmount{m}", norm(p[f"Modulation {m} Amount"]))

    # --- FX ---
    for n, key in ((1, "FX1Type"), (2, "FX2Type")):
        t = p[f"Effect {n} Type"]
        ir = BLOFELD_FX_TO_IRIDIUM.get(t if isinstance(t, str) else "", "Off")
        setp(key, FX_TYPE[ir], ir)
        mixkey = {1: "ChorusDryWet", 2: "DelayDryWet"}.get(n)
        if mixkey:
            setp(mixkey, norm(p[f"Effect {n} Mix"]))

    # --- Arp ---
    unmapped += [k for k in p if k.startswith("Arp")]

    return ov, unmapped


def apply_to_template(template: dict, overrides: dict, name: str,
                      creator: str = "bloridium") -> dict:
    """Template (parse_qpat-Ergebnis) + overrides -> neues params-Dict (alle Keys)."""
    params = {k: (v["value"], v["display"]) for k, v in template["params"].items()}
    params.update(overrides)
    return {
        "name": name[:32], "creator": creator, "description": template.get("description", ""),
        "categories": template.get("categories", ["", "", "", ""]), "version": template.get("version", 14),
        "params": params,
    }
