"""Mapping Blofeld-SNDD -> Iridium/Quantum .qpat-Parameter (Key-Level).

Werte: Blofeld raw 0..127 -> Iridium norm = raw/127 (bei 0..1-Parametern);
bipolar (Mitte 64) -> raw/127 (0.5 ~ Mitte). Enums siehe Tabellen unten
(aus offiziellen Factory-.qpat extrahiert).
"""

from __future__ import annotations

# Enum-Tabellen (display -> value) – Filter-Werte aus eigenen OS4-Exporten
# (dumps/export-001, qpat v14); ACHTUNG: Nummerierung weicht von aelteren Files ab!
OSC_TYPE = {"Wavetable": 0.0, "Waveform": 1.0, "Particle": 2.0, "Resonator": 3.0, "Off": 4.0}
WF_SHAPE = {"Sawtooth": 0.0, "Sine": 1.0, "Triangle": 2.0, "Square": 3.0,
            "Pink Noise": 4.0, "White Noise": 5.0}
FILTER12_TYPE = {"12dB LP": 0.0, "12dB sat. LP": 1.0, "24dB LP": 3.0,
                 "24dB sat. LP": 4.0, "24dB dirty LP": 5.0,
                 "24dB HP": 9.0, "24dB BP": 15.0}
# DigiFormerType (v14, aus eigenen OS4-Exporten) – sitzt in der Kette NACH dem Filter
# (FilterFormerRouting 'Filter > Former') und entspricht damit Blofeld-Filter 2
DIGIFORMER_TYPE = {"Bypass": 0.0, "Drive": 1.0, "Comb+": 3.0, "Comb-": 4.0,
                   "Nave LP24": 7.0, "PPG LP24": 8.0, "Largo LP24": 9.0, "SVF LP24": 10.0,
                   "Nave LP12": 11.0, "Nave HP12": 18.0, "SVF HP12": 20.0}
# Blofeld-F2-Typ -> DigiFormer-Modell (charaktergetreuer als Filter12Type)
BLOFELD_FILTER2_TO_FORMER = {
    "LP 24dB": "Nave LP24", "LP 12dB": "Nave LP12", "PPG LP": "PPG LP24",
    "HP 24dB": "Nave HP12", "HP 12dB": "Nave HP12",
    "Comb+": "Comb+", "Comb-": "Comb-",
    "BP 24dB": "Nave LP24", "BP 12dB": "Nave LP24",      # Naeherung (kein BP24 in v14-Exporten gesehen)
    "Notch24dB": "Nave LP24", "Notch12dB": "Nave LP24",  # Naeherung
}
FX_TYPE = {"Off": 0.0, "Phaser": 1.0, "Chorus": 2.0, "Flanger": 3.0, "Delay": 4.0,
           "Reverb": 5.0, "EQ": 6.0, "Drive": 7.0, "Compressor": 8.0}

# Blofeld Shape (Spec 4.1) -> Iridium (OscType, WF-Shape)
BLOFELD_SHAPE_TO_IRIDIUM = {
    "off": ("Off", None), "Pulse": ("Waveform", "Square"), "Saw": ("Waveform", "Sawtooth"),
    "Triangle": ("Waveform", "Triangle"), "Sine": ("Waveform", "Sine"),
}
# Blofeld Filter-Type (Spec 4.4) -> Iridium Filter12Type (v14-Werte).
# Notch/Comb sind Naeherungen (echte Comb-/PPG-Modelle sitzen im DigiFormer,
# waeren aber ein eigener Routing-Eingriff -> siehe unmapped).
BLOFELD_FILTER_TO_IRIDIUM = {
    "Bypass": None, "LP 24dB": "24dB LP", "LP 12dB": "12dB LP", "PPG LP": "12dB LP",
    "BP 24dB": "24dB BP", "BP 12dB": "24dB BP",
    "HP 24dB": "24dB HP", "HP 12dB": "24dB HP",
    "Notch24dB": "24dB BP", "Notch12dB": "24dB BP",
    "Comb+": "24dB BP", "Comb-": "24dB BP",
}
# Blofeld FX-Type (Spec 5.1) -> Iridium FX1/FX2-Type
BLOFELD_FX_TO_IRIDIUM = {
    "Bypass": "Off", "Chorus": "Chorus", "Flanger": "Flanger", "Phaser": "Phaser",
    "Overdrive": "Drive", "Triple FX": "Chorus", "Delay": "Delay", "Clk.Delay": "Delay",
    "Reverb": "Reverb",
}

# ---- Iridium Routing/Matrix-Enums (Werte aus dumps/export-001 = eigene OS4-Exporte, qpat v14) ----
OSC_DESTINATION = {"Main": 0.0, "VCA": 1.0, "DF 0 Fil 100": 2.0, "DF 100 Fil 0": 22.0}
FILTER_FORMER_ROUTING = {"Former > Filter": 0.0, "Filter > Former": 1.0, "Parallel": 2.0}
FILTER_LINK = {"Single": 0.0, "Boost": 1.0, "Independent": 6.0, "Linked": 7.0}
MATRIX_SRC = {"Off": 0.0, "Amp Env": 1.0, "Filter1 Env": 2.0, "Filter2 Env": 3.0,
              "Free Env1": 4.0, "Free Env2": 5.0, "Free Env3": 6.0,
              "LFO 1": 7.0, "LFO 2": 8.0, "LFO 3": 9.0, "LFO 4": 10.0, "LFO 5": 11.0, "LFO 6": 12.0,
              "Pitch Bend": 15.0, "Wheel": 14.0, "After Touch": 16.0,
              "Keytrack": 31.0, "Velocity": 32.0}
MATRIX_DST = {"Off": 0.0, "Pitch": 1.0, "Osc1 Pitch": 2.0, "Osc2 Pitch": 3.0, "Osc3 Pitch": 4.0,
              "Osc1 Mix": 5.0, "Osc2 Mix": 6.0, "Osc3 Mix": 7.0,
              "Filter1 Cutoff": 100.0, "Filter1 Reso": 101.0,
              "Filter2 Cutoff": 103.0, "Filter2 Reso": 105.0,
              "Filt1Env Attack": 113.0, "Filt1Env Sustain": 114.0, "Filt1Env Decay": 123.0,
              "Volume": 112.0, "Pan": 144.0}
# Blofeld Mod-Source -> Iridium MatrixSrc-Display (Press-Kombis approx. auf After Touch)
BLOFELD_MOD_SRC = {
    "LFO 1": "LFO 1", "LFO 2": "LFO 2", "LFO 3": "LFO 3",
    "LFO1*MW": "Wheel", "LFO2*MW": "Wheel", "LFO3*MW": "Wheel",
    "LFO1*Press": "After Touch", "LFO2*Press": "After Touch", "LFO3*Press": "After Touch",
    "Mod Wheel": "Wheel", "Pressure": "After Touch", "Poly Press": "After Touch",
    "Velocity": "Velocity", "Rel. Velo": "Velocity",
    "Keytrack": "Keytrack", "Pitch Bend": "Pitch Bend",
    "FilterEnv": "Filter1 Env", "AmpEnv": "Amp Env",
    "Env3": "Free Env1", "Env4": "Free Env2",
}
# Blofeld Mod-Destination -> Iridium MatrixDst-Display (FE = Filter Envelope -> Filt1Env)
BLOFELD_MOD_DST = {
    "Pitch": "Pitch", "O1 Pitch": "Osc1 Pitch", "O2 Pitch": "Osc2 Pitch", "O3 Pitch": "Osc3 Pitch",
    "O1 Level": "Osc1 Mix", "O2 Level": "Osc2 Mix", "O3 Level": "Osc3 Mix",
    "F1 Cutoff": "Filter1 Cutoff", "F1 Reson.": "Filter1 Reso",
    "F2 Cutoff": "Filter2 Cutoff", "F2 Reson.": "Filter2 Reso",
    "FE Attack": "Filt1Env Attack", "FE Decay": "Filt1Env Decay", "FE Sustain": "Filt1Env Sustain",
    "Volume": "Volume",
}


def norm(raw: int) -> float:
    """Blofeld raw 0..127 -> Iridium norm 0..1."""
    return max(0.0, min(1.0, raw / 127.0))


def amt_bipolar(raw: int) -> float:
    """Blofeld Mod-Amount (bipolar, Mitte 64 = 0) -> Iridium Matrix-Amount 0..1
    zentriert um 0.5:  64 -> 0.5 (neutral), 127 -> 1.0, 0 -> 0.0.
    Verhindert, dass Wheel/Velocity auf dem Iridium voll aufaddieren."""
    return max(0.0, min(1.0, 0.5 + (raw - 64) / 254.0))


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
    f2_label = p["Filter 2 Type"]
    m1 = BLOFELD_FILTER_TO_IRIDIUM.get(f1_label if isinstance(f1_label, str) else "", "24dB LP")
    if m1:
        setp("Filter12Type", FILTER12_TYPE[m1], m1)
        setp("FilterState", 0.0, "Active")
    else:
        setp("FilterState", 1.0, "Bypass")  # F1 Bypass (0=Active, 1=Bypass in v14)
    # F2 -> DigiFormer (Kette: Filter(F1) > Former(F2)); Filter2-Stufe bleibt Bypass.
    # Umgekehrt ('Former > Filter') waere der Former die F1-Position.
    if BLOFELD_FILTER_TO_IRIDIUM.get(f2_label if isinstance(f2_label, str) else "") is None:
        # F2 Bypass: Former bypass UND FilterLink 'Single' – sonst leaked bei
        # parallelem Routing das Dry-Signal am F1 vorbei (Filter "zu offen")
        setp("DigiFormerType", DIGIFORMER_TYPE["Bypass"], "Bypass")
        setp("DigiFormerAmount", 0.0)
        setp("Filter2State", 1.0, "Bypass")
        setp("FilterLink", FILTER_LINK["Single"], "Single")
    else:
        former = BLOFELD_FILTER2_TO_FORMER.get(f2_label if isinstance(f2_label, str) else "", "Nave LP24")
        setp("DigiFormerType", DIGIFORMER_TYPE[former], former)
        setp("DigiFormerAmount", norm(p["Filter 2 Cutoff"]))    # approx: Cutoff -> Amount
        setp("DigiFormerColor", norm(p["Filter 2 Resonance"]))  # approx: Reso -> Color
        setp("Filter2State", 1.0, "Bypass")
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
    # (Filter-Routing/Keytrack/Mod siehe oben gemappt; Drive/Curve/FM/Pan ungemappt)

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

    # --- Routing: Blofeld Osc->Mixer->F1->F2->Amp entspricht Iridium
    #     Osc Destination 'DF 0 Fil 100' (100 % in den Filter) + 'Filter > Former' ---
    for n in (1, 2, 3):
        setp(f"Osc{n}Destination", OSC_DESTINATION["DF 0 Fil 100"], "DF 0 Fil 100")
    setp("FilterFormerRouting", FILTER_FORMER_ROUTING["Filter > Former"], "Filter > Former")
    if p.get("Filter Routing") == 1:  # Blofeld seriell -> F1/F2 linked
        setp("FilterLink", FILTER_LINK["Linked"], "Linked")
    # Filter-Keytrack bipolar (Blofeld Mitte 64 -> 0.5)
    for n in (1, 2):
        kt = p[f"Filter {n} Keytrack"]
        setp(f"Filter{n}Keytrack", max(0.0, min(1.0, (kt - 64) / 64.0)))

    # --- Modulation/Matrix: Blofeld 16 Slots -> Iridium Matrix-Slots ---
    slot = 0
    for m in range(1, 17):
        src = p[f"Modulation {m} Source"]
        dst = p[f"Modulation {m} Destination"]
        amt = p[f"Modulation {m} Amount"]
        if not isinstance(src, str) or src == "off":
            continue
        slot += 1
        s_disp = BLOFELD_MOD_SRC.get(src)
        d_disp = BLOFELD_MOD_DST.get(dst)
        if s_disp and d_disp:
            setp(f"MatrixSrc{slot}", MATRIX_SRC[s_disp], s_disp)
            setp(f"MatrixDst{slot}", MATRIX_DST[d_disp], d_disp)
            setp(f"MatrixAmount{slot}", amt_bipolar(amt))
            setp(f"MatrixOnOff{slot}", 1.0, "Active")
        else:
            unmapped.append(f"Modulation {m} ({src} -> {dst})")
    # direkte Filter-Modulation (Filter N Mod Source/Amount) -> Extra-Matrix-Slots ab 17
    for n in (1, 2):
        src = p[f"Filter {n} Mod Source"]
        if isinstance(src, str) and src != "off":
            slot += 1
            s_disp = BLOFELD_MOD_SRC.get(src)
            d_disp = "Filter1 Cutoff" if n == 1 else "Filter2 Cutoff"
            if s_disp:
                setp(f"MatrixSrc{slot}", MATRIX_SRC[s_disp], s_disp)
                setp(f"MatrixDst{slot}", MATRIX_DST[d_disp], d_disp)
                setp(f"MatrixAmount{slot}", amt_bipolar(p[f"Filter {n} Mod Amount"]))
                setp(f"MatrixOnOff{slot}", 1.0, "Active")
            else:
                unmapped.append(f"Filter {n} Mod Source {src!r}")

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
