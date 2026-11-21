"""Mapping Blofeld SNDD -> Iridium/Quantum .qpat parameters (key level).

Values: Blofeld raw 0..127 -> Iridium norm = raw/127 (for 0..1 parameters);
bipolar (center 64) -> raw/127 (0.5 ~ center). Enums see tables below
(extracted from official factory .qpat files).

General polarity rule: unipolar Blofeld values (0..127 = 0..100 %) map to
norm = raw/127; bipolar values (center 64 = 0) also map via raw/127, because
the Iridium represents bipolar ranges as norm 0..1 centered at 0.5 - EXCEPT
matrix amounts, see amt_bipolar().
"""

from __future__ import annotations

import math
import re

# Enum tables (display -> value) = RUNTIME values of OS 4.1.0b2, live-verified via QUIR
# `param-info` on 2026-11-18 (docs/refs/quir_runtime_enums_2026-11-18.md). KEY FINDING
# 2026-11-18 (controlled load test, v14 file written by us, loaded via load-patch):
# the loader interprets qpat enum values with the CURRENT runtime layout
# (file value == runtime value, e.g. file dst 109 -> runtime 109; device saves of
# v11 patches are identity too: 17->17). The old displays in dumps/export-001
# (v14 files from an older OS build, e.g. 95='DF Amount') are STALE - do not use them.
OSC_TYPE = {"Wavetable": 0.0, "Waveform": 1.0, "Particle": 2.0, "Resonator": 3.0,
            "Kernels": 4.0, "Seeds": 5.0, "Off": 6.0}
WF_SHAPE = {"Sawtooth": 0.0, "Sine": 1.0, "Triangle": 2.0, "Square": 3.0,
            "Pink Noise": 4.0, "White Noise": 5.0}
FILTER12_TYPE = {"12dB LP": 0.0, "12dB sat. LP": 1.0, "24dB LP": 3.0,
                 "24dB sat. LP": 4.0, "24dB dirty LP": 5.0,
                 "24dB HP": 9.0, "24dB BP": 15.0}
# DigiFormerType (v14, from own OS4 exports) - sits in the chain AFTER the filter
# (FilterFormerRouting 'Filter > Former') and thus corresponds to Blofeld filter 2
DIGIFORMER_TYPE = {"Bypass": 0.0, "Drive": 1.0, "Comb+": 3.0, "Comb-": 4.0,
                   "Nave LP24": 7.0, "PPG LP24": 8.0, "Largo LP24": 9.0, "SVF LP24": 10.0,
                   "Nave LP12": 11.0, "Nave HP12": 18.0, "SVF HP12": 20.0}
# Blofeld F2 type -> DigiFormer model (more faithful to the character than Filter12Type)
BLOFELD_FILTER2_TO_FORMER = {
    "LP 24dB": "Nave LP24", "LP 12dB": "Nave LP12", "PPG LP": "PPG LP24",
    "HP 24dB": "Nave HP12", "HP 12dB": "Nave HP12",
    "Comb+": "Comb+", "Comb-": "Comb-",
    "BP 24dB": "Nave LP24", "BP 12dB": "Nave LP24",      # approximation (no BP24 seen in v14 exports)
    "Notch24dB": "Nave LP24", "Notch12dB": "Nave LP24",  # approximation
}
# FX1Type/FX2Type runtime enum (param-info 2754/2756): Tremolo was inserted at 1,
# so everything from Phaser on shifts +1 vs the old tables.
FX_TYPE = {"Off": 0.0, "Tremolo": 1.0, "Phaser": 2.0, "Chorus": 3.0, "Flanger": 4.0,
           "Delay": 5.0, "Reverb": 6.0, "EQ": 7.0, "Drive": 8.0, "Compressor": 9.0}

# Blofeld shape (Spec 4.1) -> Iridium (OscType, WF shape)
BLOFELD_SHAPE_TO_IRIDIUM = {
    "off": ("Off", None), "Pulse": ("Waveform", "Square"), "Saw": ("Waveform", "Sawtooth"),
    "Triangle": ("Waveform", "Triangle"), "Sine": ("Waveform", "Sine"),
}
# Blofeld wavetable (SHAPES label, spec 4.1 from index 5) -> Iridium OscN WavetableTable
# ID = RUNTIME enum (param-info 19, 2026-11-18). The Iridium table names match the
# Blofeld SHAPES 1:1 for almost every entry -> near-complete bridge (P2-4 solved).
BLOFELD_WAVETABLE_TO_IRIDIUM = {
    "Alt 1": 66.0, "Alt 2": 67.0, "Resonant": 0.0, "Resonant2": 1.0, "MalletSyn": 2.0,
    "Sqr-Sweep": 3.0, "Bellish": 4.0, "Pul-Sweep": 5.0, "Saw-Sweep": 6.0,
    "MellowSaw": 7.0, "Feedback": 8.0, "Add Harm": 9.0, "Reso 3 HP": 10.0,
    "Wind Syn": 11.0, "High Harm": 12.0, "Clipper": 13.0, "Organ Syn": 14.0,
    "SquareSaw": 15.0, "Formant 1": 16.0, "Polated": 17.0, "Transient": 18.0,
    "ElectricP": 19.0, "Robotic": 20.0, "StrongHrm": 21.0, "PercOrgan": 22.0,
    "ClipSweep": 23.0, "ResoHarms": 24.0, "2 Echoes": 25.0, "Formant 2": 26.0,
    "FmnVocal": 27.0, "MicroSync": 28.0, "Micro PWM": 29.0, "Glassy": 30.0,
    "Square HP": 31.0, "SawSync 1": 32.0, "SawSync 2": 33.0, "SawSync 3": 34.0,
    "PulSync 1": 35.0, "PulSync 2": 36.0, "PulSync 3": 37.0,
    "SinSync 1": 38.0, "SinSync 2": 39.0, "SinSync 3": 40.0,
    "PWM Pulse": 41.0, "PWM Saw": 42.0, "Fuzz Wave": 43.0, "Distorted": 44.0,
    "HeavyFuzz": 45.0, "Fuzz Sync": 46.0, "K+Strong1": 47.0, "K+Strong2": 48.0,
    "K+Strong3": 49.0, "1-2-3-4-5": 50.0, "19/twenty": 51.0,
    "Wavetrip1": 52.0, "Wavetrip2": 53.0, "Wavetrip3": 54.0, "Wavetrip4": 55.0,
    "MaleVoice": 56.0, "Low Piano": 57.0, "ResoSweep": 58.0, "Xmas Bell": 59.0,
    "FM Piano": 60.0, "Fat Organ": 61.0, "Vibes": 62.0, "Chorus 2": 63.0,
    "True PWM": 64.0, "UpperWaves": 65.0,
}
# Blofeld filter type (Spec 4.4) -> Iridium Filter12Type (v14 values).
# Notch/Comb are approximations (the real Comb-/PPG models live in the DigiFormer,
# but selecting them would be a routing change of its own -> see unmapped).
BLOFELD_FILTER_TO_IRIDIUM = {
    # PPG LP is a 24dB ladder-type on the Blofeld -> "24dB LP" (NOT 12dB LP:
    # user finding 2026-11-21, A005 @ Iridium slot 204 showed FilterModel=svf /
    # FilterType=12dB LP and sounded wrong; 24dB LP is a valid Filter12Type in
    # factory qpats without touching Filter1Model).
    "Bypass": None, "LP 24dB": "24dB LP", "LP 12dB": "12dB LP", "PPG LP": "24dB LP",
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

# ---- Iridium routing/matrix enums (values from dumps/export-001 = own OS4 exports, qpat v14) ----
OSC_DESTINATION = {"Main": 0.0, "VCA": 1.0, "DF 0 Fil 100": 2.0, "DF 100 Fil 0": 22.0}
# Blofeld LFO shape -> Iridium LfoNShape. Enum aus 1186 Factory-qpats
# (docs/refs/Quantum_Factories.zip, Histogramm): 0 Sine, 1 Triangle, 2 Square,
# 3 Saw (down), 4 Saw (up), 5 S&H. Blofeld "Saw" -> Saw (up); Blofeld "Random"
# hat kein Iridium-Pendant -> S&H als Naeherung (2026-11-20).
BLO_LFO_SHAPE_TO_IRIDIUM = {"Sine": 0.0, "Triangle": 1.0, "Square": 2.0,
                           "Saw": 4.0, "S&H": 5.0, "Random": 5.0}
FILTER_FORMER_ROUTING = {"Former > Filter": 0.0, "Filter > Former": 1.0, "Parallel": 2.0}
FILTER_LINK = {"Single": 0.0, "Boost": 1.0, "Independent": 6.0, "Linked": 7.0}
# Filter2State (v14/v15 same values: 0=Active, 1=Bypass, 2=Off).
# ATTENTION: 'Bypass' leaked the dry signal past F1 - only 'Off' switches F2
# off cleanly (evidence: dumps/00202-SH Power.qpat, v15 Filter2State=2.0 'Off').
# That is why the mapping below sets Filter2State to 'Off', never 'Bypass',
# whenever filter 2 must not be heard.
FILTER2_STATE = {"Active": 0.0, "Bypass": 1.0, "Off": 2.0}
# MATRIX_SRC/DST = OS 4.1.0b2 runtime enum (param-info 2478/2480, 2026-11-18; qpat file
# values are read 1:1 - see docs/refs/quir_runtime_enums_2026-11-18.md).
# After Touch = 17 (Poly AT decision 2026-11-18: AfterTouchDoPoly=1.0).
MATRIX_SRC = {"Off": 0.0, "Amp Env": 1.0, "Filter1 Env": 2.0, "Filter2 Env": 3.0,
              "Free Env1": 4.0, "Free Env2": 5.0, "Free Env3": 6.0,
              "LFO 1": 7.0, "LFO 2": 8.0, "LFO 3": 9.0, "LFO 4": 10.0, "LFO 5": 11.0, "LFO 6": 12.0,
              "Wheel": 14.0, "Pitch Bend": 15.0, "After Touch": 17.0, "Pedal": 19.0,
              "Breath Control": 21.0, "CC 22": 22.0, "CC 23": 23.0, "CC 24": 24.0, "CC 25": 25.0,
              "Keytrack": 32.0, "Velocity": 33.0, "Release Velocity": 34.0, "Constant": 40.0}
MATRIX_DST = {"Off": 0.0, "Pitch": 1.0, "Osc1 Pitch": 2.0, "Osc2 Pitch": 3.0, "Osc3 Pitch": 4.0,
              "Osc1 Mix": 5.0, "Osc2 Mix": 6.0, "Osc3 Mix": 7.0,
              "Osc1 Pan": 8.0, "Osc2 Pan": 9.0, "Osc3 Pan": 10.0,
              "WT1 Position": 11.0, "WF1 Warp": 18.0, "WT2 Position": 42.0, "WF2 Warp": 49.0,
              "WT3 Position": 73.0, "WF3 Warp": 80.0,
              "DF Amount": 104.0, "DF Color": 105.0, "DF Pan": 107.0, "DF Level": 108.0,
              "Filter1 Cutoff": 109.0, "Filter1 Reso": 110.0, "Filter1 Pan": 111.0,
              "Filter1 Level": 112.0, "Filter2 Cutoff": 113.0, "Filter2 Reso": 114.0,
              "Filter2 Pan": 115.0, "Filter2 Level": 116.0, "VCA": 117.0,
              "AmpEnv Attack": 118.0, "AmpEnv Decay": 119.0, "AmpEnv Sustain": 120.0,
              "AmpEnv Release": 121.0,
              "Filt1Env Attack": 122.0, "Filt1Env Decay": 123.0, "Filt1Env Sustain": 124.0,
              "Filt1Env Release": 125.0,
              "Free1Env Attack": 130.0, "Free1Env Decay": 131.0, "Free1Env Sustain": 132.0,
              "Free1Env Release": 133.0, "Free2Env Attack": 134.0, "Free2Env Decay": 135.0,
              "Free2Env Sustain": 136.0, "Free2Env Release": 137.0,
              "FX1 DryWet": 142.0, "FX2 DryWet": 144.0,
              "Volume": 152.0, "Pan": 153.0,
              "LFO1 Speed": 154.0, "LFO2 Speed": 155.0, "LFO3 Speed": 156.0,
              "Chorus DryWet": 174.0, "Delay DryWet": 190.0, "Drive DryWet": 196.0}
# All MATRIX_* values above are the OS 4.1.0b2 RUNTIME enum (param-info 2478/2480,
# 2026-11-18) - the qpat loader uses them 1:1 (controlled load test 2026-11-18).
# Blofeld mod source -> Iridium MatrixSrc display (pressure combos approx. to After Touch)
BLOFELD_MOD_SRC = {
    "LFO 1": "LFO 1", "LFO 2": "LFO 2", "LFO 3": "LFO 3",
    # NOTE: products "LFO1*MW"/"LFO2*Press"/... are deliberately NOT here — they are
    # resolved by _resolve_mod_source() to Src=LFO x + matrix Ctrl (see below).
    "Mod Wheel": "Wheel", "Pressure": "After Touch", "Poly Press": "After Touch",
    "Velocity": "Velocity", "Rel. Velo": "Release Velocity",
    "Keytrack": "Keytrack", "Pitch Bend": "Pitch Bend",
    "FilterEnv": "Filter1 Env", "AmpEnv": "Amp Env",
    "Env3": "Free Env1", "Env4": "Free Env2",
    "Sustain": "Pedal", "BreathCtrl": "Breath Control",
    # approx: Blofeld Control W-Z (assignable controllers) -> generic CC sources;
    # exact CC numbers unverified. MAXIMUM/minimum -> Constant.
    "Control W": "CC 22", "Control X": "CC 23", "Control Y": "CC 24", "Control Z": "CC 25",
    "MAXIMUM": "Constant", "minimum": "Constant",
}
# Blofeld mod destination -> Iridium MatrixDst display (FE = filter envelope -> Filt1Env)
BLOFELD_MOD_DST = {
    "Pitch": "Pitch", "O1 Pitch": "Osc1 Pitch", "O2 Pitch": "Osc2 Pitch", "O3 Pitch": "Osc3 Pitch",
    "O1 Level": "Osc1 Mix", "O2 Level": "Osc2 Mix", "O3 Level": "Osc3 Mix",
    "F1 Cutoff": "Filter1 Cutoff", "F1 Reson.": "Filter1 Reso",
    "F2 Cutoff": "Filter2 Cutoff", "F2 Reson.": "Filter2 Reso",
    "FE Attack": "Filt1Env Attack", "FE Decay": "Filt1Env Decay", "FE Sustain": "Filt1Env Sustain",
    "FE Release": "Filt1Env Release",
    "AE Attack": "AmpEnv Attack", "AE Decay": "AmpEnv Decay",
    "AE Sustain": "AmpEnv Sustain", "AE Release": "AmpEnv Release",
    "E3 Attack": "Free1Env Attack", "E3 Decay": "Free1Env Decay",
    "E3 Sustain": "Free1Env Sustain", "E3 Release": "Free1Env Release",
    "E4 Attack": "Free2Env Attack", "E4 Decay": "Free2Env Decay",
    "E4 Sustain": "Free2Env Sustain", "E4 Release": "Free2Env Release",
    "F1 Pan": "Filter1 Pan", "F2 Pan": "Filter2 Pan",
    "LFO1Speed": "LFO1 Speed", "LFO2Speed": "LFO2 Speed", "LFO3Speed": "LFO3 Speed",
    "Volume": "Volume",
    # no Iridium matrix dst exists for: F1/F2 Drive, F1/F2 FM, O1-3 FM, RMod Level/Bal.,
    # NoiseLevel/Bal., O1-3 Balance, M1-4 Amount (runtime dst list, param-info 2480)
}


def _resolve_mod_source(p: dict, src) -> tuple[str | None, str | None]:
    """Blofeld mod source -> (MATRIX_SRC key, matrix Ctrl key or None).

    Products like "LFO2*MW" or "Modifier 1" (= LFO 2 * Mod Wheel, op "*") are
    represented on the Iridium as a matrix row with Src=LFO x AND Ctrl
    (MatrixControlN)=Wheel — the "LFO2 CTRL: ModWheel" structure
    (user finding 2026-11-21, A006 @ Iridium slot 205, Mod 10-12 via Modifier 1).
    """
    if not isinstance(src, str) or src == "off":
        return None, None
    m = re.match(r"^LFO\s*([1-3])\s*\*\s*(MW|Mod\s*Wheel)$", src, re.IGNORECASE)
    if m:
        return f"LFO {m.group(1)}", "Wheel"
    m = re.match(r"^LFO\s*([1-3])\s*\*\s*Press", src, re.IGNORECASE)
    if m:
        return f"LFO {m.group(1)}", "After Touch"
    m = re.match(r"^Modifier\s*([1-4])$", src, re.IGNORECASE)
    if m:
        mi = m.group(1)
        op = p.get(f"Modifier {mi} Operation")
        sa = p.get(f"Modifier {mi} Source A")
        sb = p.get(f"Modifier {mi} Source B")
        if op == "*" and isinstance(sa, str) and re.fullmatch(r"LFO\s*[1-3]", sa):
            if sb == "Mod Wheel":
                return sa, "Wheel"
            if sb == "Pressure":
                return sa, "After Touch"
            return None, None
        if op == "+" and isinstance(sa, str):
            # Modifier = SourceA + Constant: map SourceA alone, constant offset lost
            return BLOFELD_MOD_SRC.get(sa), None
        return None, None
    return BLOFELD_MOD_SRC.get(src), None


def norm(raw: int) -> float:
    """Blofeld raw 0..127 -> Iridium norm 0..1."""
    return max(0.0, min(1.0, raw / 127.0))


# ---- Glide Rate: time calibration (both sides are log-scaled in time) ----
# Why not plain norm(): Blofeld "Glide Rate" raw 0..127 is NOT linear in time
# (Blofeld manual: low values = milliseconds, high = several seconds); the
# Iridium "GlideRate" norm 0..1 is not either. Linear norm() therefore maps too
# high (observation 2026-11-09: A073 Chord Hose raw 48 -> norm 0.378 ->
# "Glide Rate 0.29sec" on the Iridium, clearly longer than on the Blofeld).
# Anchors (measured/documented):
#   - Blofeld raw 20 <-> Iridium norm 0.15: Don Solaris factory pairs (Blofeld
#     Rate 20 = Iridium GlideRate 0.15); 0.15 is the Iridium default = 0.045 s
#     (manual) -> t_blo(20) = 0.045 s.
#   - Iridium norm 0.378 shows "0.29 s" on the device (display read during A073 import).
#   - Blofeld raw 127 = "several seconds" (manual) -> conservatively 5 s.
# Both curves are exponential in time; mapping raw -> norm via t_blo(raw) = t_irr(norm)
# keeps the audible glide time identical on both synths.
GLIDE_BLO_T_AT_20 = 0.045   # s at raw 20 (Don Solaris anchor)
GLIDE_BLO_T_MAX = 5.0       # s at raw 127 ("several seconds", conservative)
GLIDE_IRR_ANCHORS = ((0.15, 0.045), (0.378, 0.29))   # (norm, s on device)


def blofeld_glide_seconds(raw: int) -> float:
    """Blofeld Glide Rate raw 0..127 -> glide time in s (exponential)."""
    raw = max(0, min(127, int(raw)))
    return GLIDE_BLO_T_AT_20 * (GLIDE_BLO_T_MAX / GLIDE_BLO_T_AT_20) ** ((raw - 20) / 107.0)


def iridium_glide_seconds(norm_v: float) -> float:
    """Iridium GlideRate norm 0..1 -> glide time in s (exponential through the anchors)."""
    (n0, t0), (n1, t1) = GLIDE_IRR_ANCHORS
    return t0 * (t1 / t0) ** ((norm_v - n0) / (n1 - n0))


def glide_rate_norm(raw: int) -> float:
    """Blofeld Glide Rate raw -> Iridium GlideRate norm via equal glide time."""
    t = blofeld_glide_seconds(raw)
    (n0, t0), (n1, t1) = GLIDE_IRR_ANCHORS
    n = n0 + (n1 - n0) * math.log(t / t0) / math.log(t1 / t0)
    return max(0.0, min(1.0, n))


# ---- LFO clock: Blofeld sync speed (SysEx doc 4.6) -> Iridium SyncRatio ----
# Blofeld LFO speed raw (Sync=1): raw//2 -> bars per cycle (fractions < 1 bar decimal)
BLO_LFO_BARS = [1280, 1152, 1024, 896, 768, 640, 576, 512, 448, 384, 320, 288, 256, 224, 192,
                160, 144, 128, 112, 96, 80, 72, 64, 56, 48, 40, 36, 32, 28, 24, 20, 18, 16,
                14, 12, 10, 9, 8, 7, 6, 5, 4, 3.5, 3, 2.5, 2, 1.5, 1,
                0.5, 2/3, 0.5, 0.375, 1/3, 0.25, 0.1875, 1/6, 0.125, 0.09375, 1/12, 0.0625,
                0.046875, 1/24, 0.03125, 1/48]
# Iridium LfoN SyncRatio index -> beats per cycle (display values of own OS4 exports:
# 0->1024, 11->24, 12->16, 15->6, 16->1/1=4 beats, 22->1/8=.5, 23->1/16 dot=.375, 24->1/16=.25)
IRR_SYNC_BEATS = [1024, 768, 512, 384, 256, 192, 128, 96, 64, 48, 32, 24, 16, 12, 8, 6, 4,
                  3, 2, 1.5, 1, 0.75, 0.5, 0.375, 0.25, 0.1875, 0.125, 0.0833]


def blofeld_lfo_clock_beats(raw: int) -> float:
    """Blofeld LFO clock index (Sync=1) -> beats per cycle (1 bar = 4 beats)."""
    bars = BLO_LFO_BARS[min(max(raw, 0) // 2, len(BLO_LFO_BARS) - 1)]
    return bars * 4.0


def iridium_sync_ratio_index(beats: float) -> int:
    """Nearest Iridium SyncRatio index for a beats/cycle count (log distance)."""
    lb = [math.log(b) for b in IRR_SYNC_BEATS]
    t = math.log(max(beats, 1e-6))
    return min(range(len(lb)), key=lambda i: abs(lb[i] - t))


def amt_bipolar(raw: int) -> float:
    """Blofeld mod amount (bipolar, center 64 = 0) -> Iridium MatrixAmount 0..1
    centered around 0.5: 64 -> 0.5 (neutral), 127 -> 1.0, 0 -> 0.0.
    Unlike plain norm() this keeps the center at the neutral point, so
    wheel/velocity do not fully add up on the Iridium.
    NOTE: the divisor 254 (i.e. Iridium range = +/-200% at 0/1) is an assumption -
    calibrate live via audio sweep (plan 2026-11-18)."""
    return max(0.0, min(1.0, 0.5 + (raw - 64) / 254.0))


def fine_pitch_norm(raw: int) -> float:
    """Blofeld osc detune (bipolar, center 64 = 0, range +/-64 cent) -> Iridium
    OscNFinePitch norm 0..1 centered at 0.5. Divisor 254 assumes the Iridium full
    range is +/-127 cent - live-calibration TODO (audio pitch sweep)."""
    raw = max(0, min(127, int(raw)))
    return max(0.0, min(1.0, 0.5 + (raw - 64) / 254.0))


# ---- filter cutoff calibration (2026-11-14) ----
# Blofeld manual: cutoff raw 0..127 scales in SEMITONE steps, anchor raw 64 = 440 Hz
# ("At a value of 64 and a Resonance value of 114, the filter oscillates with 440 Hz").
# Iridium (calib 200-205, HANDOVER-2026-11-09): 17.8 Hz @ norm 0.10, 19912 Hz @ 1.00
# -> log10(f) = 0.9117 + 3.387*norm.  Direct norm(raw) was wrong (finding 2026-11-14:
# A001 raw 64 -> 416 Hz instead of 440 Hz; serially with DF 199 Hz this attenuates
# note C5 by ~40 dB -> Iridium -66 dBFS, "filter lets almost nothing through").
# Both scales are logarithmic in Hz, so the mapping goes through the Hz bridge.
IRIDIUM_CUTOFF_LOG_A = 0.9117   # log10(Hz) at Iridium norm 0
IRIDIUM_CUTOFF_LOG_B = 3.387    # decades per norm
BLOFELD_CUTOFF_ANCHOR_RAW = 64.0
BLOFELD_CUTOFF_ANCHOR_HZ = 440.0


def blofeld_cutoff_norm(raw) -> float:
    """Blofeld filter cutoff raw 0..127 -> Iridium FilterCutOff/DigiFormerAmount norm 0..1
    via the Hz bridge (both scales log; Blofeld in semitone steps around 440 Hz @ raw 64)."""
    raw = max(0, min(127, raw))
    logf = math.log10(BLOFELD_CUTOFF_ANCHOR_HZ) \
        + (raw - BLOFELD_CUTOFF_ANCHOR_RAW) / 12.0 * math.log10(2.0)
    x = (logf - IRIDIUM_CUTOFF_LOG_A) / IRIDIUM_CUTOFF_LOG_B
    return max(0.0, min(1.0, x))


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

    def mrow(slot: int, s_disp: str, ctrl_disp: str | None, d_disp: str, amt) -> None:
        """One Iridium matrix row; ctrl_disp -> MatrixControlN (row 'Ctrl', e.g. Wheel
        for Blofeld LFOx*MW products, 2026-11-21)."""
        setp(f"MatrixSrc{slot}", MATRIX_SRC[s_disp], s_disp)
        if ctrl_disp:
            setp(f"MatrixControl{slot}", MATRIX_SRC[ctrl_disp], f"Ctrl {ctrl_disp}")
            setp(f"MatrixControlAmount{slot}", 1.0, "full")
        setp(f"MatrixDst{slot}", MATRIX_DST[d_disp], d_disp)
        setp(f"MatrixAmount{slot}", amt)
        setp(f"MatrixOnOff{slot}", 1.0, "Active")

    # --- oscillators ---
    shape_raw_idx = [8, 24, 40]     # SDATA indices OscN Shape
    oct_idx = [1, 17, 33]
    semi_idx = [2, 18, 34]
    osc_is_wavetable = {}
    for n in (1, 2, 3):
        raw_shape = sdata[shape_raw_idx[n - 1]]
        # get the shape label from the parsed params
        shape_label = p[f"Osc {n} Shape"]
        if isinstance(shape_label, str) and shape_label in BLOFELD_SHAPE_TO_IRIDIUM:
            otype, wf = BLOFELD_SHAPE_TO_IRIDIUM[shape_label]
        elif raw_shape >= 5:
            otype, wf = "Wavetable", None
        else:
            otype, wf = "Off", None
        osc_is_wavetable[n] = (otype == "Wavetable")
        setp(f"Osc{n}Type", OSC_TYPE[otype], otype)
        if wf:
            setp(f"Osc{n}WaveformShape", WF_SHAPE[wf], wf)
        if otype == "Wavetable":
            # wavetable selection: Blofeld wavetable name -> Iridium OscN WavetableTable ID
            # (IDs v14 from own OS4 exports, e.g. MalletSyn -> 2 "Mallet Syn").
            # Without a bridge entry the template table (0 "Resonant") stays.
            tbl = BLOFELD_WAVETABLE_TO_IRIDIUM.get(shape_label if isinstance(shape_label, str) else "")
            if tbl is not None:
                setp(f"Osc{n}WavetableTable", tbl, shape_label)
            else:
                unmapped.append(f"Osc {n} Wavetable {shape_label!r} (no Iridium equivalent)")
            # on the Blofeld, "Pulsewidth" of a wavetable osc is the wave position
            setp(f"Osc{n}WavetablePosition", norm(p[f"Osc {n} Pulsewidth"]))
            setp(f"Osc{n}WavetableBrilliance", norm(p[f"Osc {n} Brilliance"]))
        else:
            # Blofeld manual: pulsewidth only acts on shape 'Pulse' (raw 0 = <1%,
            # raw 127 = 50%); on Saw/Triangle/Sine "this parameter has no function".
            # On the Iridium, WaveformPW is the warp and acts ALSO on Saw ->
            # keep it neutral 0.5 there, otherwise a saw becomes a square wave
            # (finding 2026-11-14: A001 PW raw 100 -> norm=0.7874 = square instead of saw).
            # The *0.5 for Pulse is because Blofeld raw 127 already means 50% duty.
            if shape_label == "Pulse":
                setp(f"Osc{n}WaveformPW", norm(p[f"Osc {n} Pulsewidth"]) * 0.5, "")
            else:
                setp(f"Osc{n}WaveformPW", 0.5, "neutral (Blofeld PW has no function)")
            # Kernels count (OS4 shows WaveformDesity as "Kernels"): the Blofeld has no
            # kernel parameter -> 0.0 = 1 wave, no copies. Template default 0.22 made
            # A001 OSC2 run as "Kernels 2.5" (finding 2026-11-14).
            setp(f"Osc{n}WaveformDesity", 0.0, "1 kernel (off)")
        # CoarsePitch: Blofeld Octave (raw 64 = 8', steps of 12; raw > 64 = higher octave)
        # ATTENTION sign: raw 52 = -12 semi (16'), raw 76 = +12 semi (4')!
        # (old: 64 - raw gave +12 instead of -12 for Osc3 raw 52, one octave too high)
        oct_up = (sdata[oct_idx[n - 1]] - 64) / 12.0
        semi = sdata[semi_idx[n - 1]] - 64
        setp(f"Osc{n}CoarsePitch", 24.0 + 12.0 * oct_up + semi, f"{semi:+.0f} semi")
        # Detune is bipolar around raw 64 (Blofeld: +/-64 cent) -> center at 0.5 on the
        # Iridium, NOT norm(raw) (old: A008 Osc1 Detune 126 -> 0.992 ~ full range instead
        # of near-center). The Iridium cent-per-norm scale is a live-calibration TODO
        # (audio pitch sweep, see plan 2026-11-18); divisor 254 assumes +/-127 cent range.
        setp(f"Osc{n}FinePitch", fine_pitch_norm(p[f"Osc {n} Detune"]), "")
        setp(f"Osc{n}Vol", norm(p[f"Mixer Osc {n} Level"]), "")
        # Pan: the Blofeld has NO osc pan - 'Mixer Osc N Balance' is the F1/F2 share
        # (MAPPING-MASTER), not a stereo pan. Mapped wrongly, Pan 0.0 = hard left
        # on the Iridium (user finding 2026-11-15, stereo image, e.g. A043 Balance=0).
        # -> Pan always center; Balance goes to the unmapped log below.
        setp(f"Osc{n}Pan", 0.5, "center (Blofeld Balance is F1/F2 share, not pan)")
        for k in ("Bend Range", "Keytrack", "FM Source", "FM Amount", "PWM Source",
                  "PWM Amount", "Limit WT"):
            unmapped.append(f"Osc {n} {k}")
        unmapped.append(f"Mixer Osc {n} Balance (F1/F2 share, not pan; later maybe OscNDestination)")
        if otype != "Wavetable":
            unmapped.append(f"Osc {n} Brilliance")
    # Hard sync (P1-1, ANALYSIS-2026-11-15): Blofeld "Osc 2 Sync to O3" -> Osc2WaveformSync
    # (A071/A008 had sync=1 and landed unmapped -> "no sync on the Iridium").
    if p.get("Osc 2 Sync to O3"):
        setp("Osc2WaveformSync", 1.0, "Sync on")
    # --- Mixer-Noise -> freier Iridium-Osc als Noise-Quelle (2026-11-20) ---
    # Blofeld "Mixer Noise Level/Balance/Colour" hat keinen direkten qpat-Key; der
    # Iridium hat keinen eigenen Noise-Mixer-Eintrag, aber ein Osc KANN Noise sein
    # (OscNType=Waveform + WaveformShape White/Pink). Nur einen FREIEN Osc-Slot
    # verwenden (bevorzugt Osc3) - einen klingenden Osc nie ueberschreiben.
    # Colour: <=64 dunkler -> Pink, >64 -> White. Balance bipolar um 64 -> Pan.
    noise_level = p.get("Mixer Noise Level", 0)
    noise_osc = None
    if noise_level:
        # frei = Osc aus (Shape off) ODER stumm (Mixer Osc N Level == 0)
        free = next((n for n in (3, 2, 1)
                     if ov.get(f"Osc{n}Type", (None,))[0] == OSC_TYPE["Off"]
                     or p.get(f"Mixer Osc {n} Level", 127) == 0), None)
        noise_osc = free
        if free is None:
            unmapped.append("Mixer Noise Level (all 3 oscillators in use - "
                            "no free Iridium osc slot)")
        else:
            colour = p.get("Mixer Noise Colour", 64)
            white = colour > 64
            setp(f"Osc{free}Type", OSC_TYPE["Waveform"], "Waveform (noise)")
            setp(f"Osc{free}WaveformShape", 5.0 if white else 4.0,
                 "White Noise" if white else "Pink Noise")
            setp(f"Osc{free}Vol", norm(noise_level))
            setp(f"Osc{free}Pan", norm(p.get("Mixer Noise Balance", 64)))
            setp(f"Osc{free}Destination", OSC_DESTINATION["DF 0 Fil 100"], "DF 0 Fil 100")
    # (Osc Pitch Source/Amount now mapped as matrix slot -> Pitch, see below)

    # --- glide / unisono ---
    setp("GlideOnOff", 1.0 if p.get("Glide") else 0.0, "On" if p.get("Glide") else "Off")
    # Glide Rate time-calibrated (log scale), not linear: norm() mapped too high (see above)
    _gr = p.get("Glide Rate", 0)
    setp("GlideRate", glide_rate_norm(_gr), f"~{blofeld_glide_seconds(_gr):.3f}s")
    # UnisonoCount is an enum (runtime: 0=Off, 1=2 voices ... 7=8), not a norm.
    # Blofeld Allocation/Unisono bits 5-7 = voices-1 (0 = mono) -> pass through as enum.
    setp("UnisonoCount", float((p.get("Allocation/Unisono", 0) >> 5) & 0x07))
    setp("UnisonoDetune", norm(p.get("Unisono Detune", 0)))
    # Aftertouch (user decision 2026-11-18, live-verified): the Iridium reacts to
    # CHANNEL AT, but the keyboard produces POLY AT in general -> the conversion
    # targets POLY AT: AfterTouchDoPoly=1.0 ('Poly AT'; runtime enum param-info 2876:
    # 0=Mono AT, 1=Poly AT) and matrix src "After Touch"=17 (param-info 2478).
    # Earlier setting was 0.0 'Mono AT' (P0-2, ANALYSIS-2026-11-15).
    setp("AfterTouchDoPoly", 1.0, "Poly AT")

    # --- mixer extras ---
    # key is called "RingModOsc1ToOsc2" in the template/device (not "RingmodOsc12"!)
    setp("RingModOsc1ToOsc2", norm(p.get("Mixer RingMod Level", 0)))
    # Mixer Noise wird unten behandelt (freier Osc als Noise-Quelle, 2026-11-20)

    # --- Filter ---
    f1_label = p["Filter 1 Type"]
    f2_label = p["Filter 2 Type"]
    m1 = BLOFELD_FILTER_TO_IRIDIUM.get(f1_label if isinstance(f1_label, str) else "", "24dB LP")
    if m1:
        setp("Filter12Type", FILTER12_TYPE[m1], m1)
        setp("FilterState", 0.0, "Active")
    else:
        setp("FilterState", 1.0, "Bypass")  # F1 Bypass (0=Active, 1=Bypass in v14)
    # F2 routing depends on the Blofeld "Filter Routing" (finding HANDOVER 2026-11-14):
    # serial (1): chain F1 -> F2 -> Amp. Iridium: F2 moves into the DigiFormer
    #   (routing 'Filter > Former', filter2 stage 'Off', FilterLink 'Single' -
    #   'Linked' silenced B, e.g. A008 FilterLink 7.0).
    # parallel (0): F1 and F2 parallel. Iridium: F2 stays filter 2 (Active),
    #   Former = Bypass, routing 'Parallel'.
    seriell = p.get("Filter Routing") == 1
    f2_bypass = BLOFELD_FILTER_TO_IRIDIUM.get(f2_label if isinstance(f2_label, str) else "") is None
    if seriell:
        if f2_bypass:
            # F2 Bypass: Former bypass AND Filter2State 'Off' - 'Bypass' alone leaked
            # the dry signal past F1 (filter "too open"); see FILTER2_STATE above
            setp("DigiFormerType", DIGIFORMER_TYPE["Bypass"], "Bypass")
            setp("DigiFormerAmount", 0.0)
        else:
            former = BLOFELD_FILTER2_TO_FORMER.get(f2_label if isinstance(f2_label, str) else "", "Nave LP24")
            setp("DigiFormerType", DIGIFORMER_TYPE[former], former)
            setp("DigiFormerAmount", blofeld_cutoff_norm(p["Filter 2 Cutoff"]))  # cutoff -> amount (Hz calibration)
            setp("DigiFormerColor", norm(p["Filter 2 Resonance"]))  # approx: reso -> color
        setp("Filter2State", FILTER2_STATE["Off"], "Off")
        setp("FilterLink", FILTER_LINK["Single"], "Single")
        setp("FilterFormerRouting", FILTER_FORMER_ROUTING["Filter > Former"], "Filter > Former")
    else:
        setp("FilterFormerRouting", FILTER_FORMER_ROUTING["Parallel"], "Parallel")
        setp("DigiFormerType", DIGIFORMER_TYPE["Bypass"], "Bypass")
        setp("DigiFormerAmount", 0.0)
        if f2_bypass:
            setp("Filter2State", FILTER2_STATE["Off"], "Off")
            setp("FilterLink", FILTER_LINK["Single"], "Single")
        else:
            setp("Filter2State", FILTER2_STATE["Active"], "Active")
    setp("Filter1CutOff", blofeld_cutoff_norm(p["Filter 1 Cutoff"]))
    setp("Filter1Reso", norm(p["Filter 1 Resonance"]))
    setp("Filter2CutOff", blofeld_cutoff_norm(p["Filter 2 Cutoff"]))
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
    # (filter routing/keytrack/mod mapped above; drive/curve/FM/pan unmapped)

    # --- amp ---
    setp("MainVolume", norm(p.get("Amplifier Volume", 127)))
    setp("LayerVolume", 1.0)
    amp_velo = p.get("Amplifier Velocity", 64)
    if not isinstance(amp_velo, (int, float)):
        amp_velo = 64
    # AmpVelo is unipolar 0..127 -> norm. ATTENTION bipolar trap: matrix amounts are
    # centered at 0.5 (0.5 = neutral) -> Vel->Volume needs 0.5 + 0.5*norm (64 -> 0.75),
    # which is why the matrix slot below does NOT use amt_bipolar()
    setp("AmpVeloAmount", norm(amp_velo))
    ae = "Amplifier Envelope"
    for bk, ik in (("Attack", "AmpEnvAttack"), ("Decay", "AmpEnvDecay"),
                   ("Sustain", "AmpEnvSustain"), ("Release", "AmpEnvRelease")):
        setp(ik, norm(p[f"{ae} {bk}"]))

    # --- env 3/4 -> FreeEnv1/2 ---
    for n, base in ((3, "FreeEnv1"), (4, "FreeEnv2")):
        for bk, ik in (("Attack", f"{base}Attack"), ("Decay", f"{base}Decay"),
                       ("Sustain", f"{base}Sustain"), ("Release", f"{base}Release")):
            setp(ik, norm(p[f"Envelope {n} {bk}"]))

    # --- envelope curves: Blofeld ADSRs are LINEAR, but the Iridium template defaults
    # Attack=RC (1.0) — massive audible difference (user finding 2026-11-21).
    # Curve enum (factory qpats): 0=Exp, 1=RC resp. 'Exp alt', 2=Lin -> set all to Lin.
    for grp in ("AmpEnv", "Filter1", "Filter2", "FreeEnv1", "FreeEnv2"):
        for ph in ("Attack", "Decay", "Release"):
            setp(f"{grp}{ph}Curve", 2.0, "Lin")

    # --- LFO ---
    # ATTENTION key names: template/device know "Lfo1Speed" (lowercase), NOT "LFO1Speed"!
    # (wrong: LFO1Speed -> own key, device ignores it, LFO ran on template default
    # 0.5 -> audible tremolo, e.g. A022 slot 14 LFO2->Volume). Also: Blofeld speed raw
    # is a clock index when Sync=1 (SysEx doc 4.6, bars/cycle, e.g. raw 14 = 512 bars =
    # practically static) -> mapped as free speed this became norm(14)=0.11 -> tremolo.
    # Iridium: LfoN Sync + SyncRatio (beats/cycle, index) + Speed (free only).
    for n in (1, 2, 3):
        raw = sdata[161 + (n - 1) * 12]  # LFO N Speed (Clock-Index)
        sync = p.get(f"LFO {n} Sync", 0)
        setp(f"Lfo{n}Sync", 1.0 if sync else 0.0, "On" if sync else "Off")
        if sync:
            beats = blofeld_lfo_clock_beats(raw)
            idx = iridium_sync_ratio_index(beats)
            setp(f"Lfo{n}SyncRatio", float(idx), f"{beats:.2f} beats")
            setp(f"Lfo{n}Speed", norm(raw))
        else:
            setp(f"Lfo{n}Speed", norm(raw))
        shape = p.get(f"LFO {n} Shape")
        if isinstance(shape, str) and shape in BLO_LFO_SHAPE_TO_IRIDIUM:
            setp(f"Lfo{n}Shape", BLO_LFO_SHAPE_TO_IRIDIUM[shape], shape)
        setp(f"Lfo{n}Phase", norm(p.get(f"LFO {n} Start Phase", 64)))
        setp(f"Lfo{n}Delay", norm(p.get(f"LFO {n} Delay", 0)))
        # Fade/Keytrack haben kein Iridium-LFO-Pendant (verbleiben unmapped)
        unmapped.append(f"LFO {n} Fade/Keytrack")

    # --- routing: Blofeld Osc->Mixer->F1->F2->Amp corresponds to Iridium
    #     Osc Destination 'DF 0 Fil 100' (100 % into the filter; Former share 0 -
    #     Former is serial F2 resp. parallel Bypass, see filter block above) ---
    for n in (1, 2, 3):
        setp(f"Osc{n}Destination", OSC_DESTINATION["DF 0 Fil 100"], "DF 0 Fil 100")
    # Filter keytrack: Blofeld raw 0..127 = -200%..+196% (64 = 0%, offset binary!),
    # Iridium FilterNKeytrack norm 0..1 = -200%..+200% (0.5 = 0%) -> directly norm(raw).
    # ATTENTION: the earlier (kt-64)/64 gave -1..+1 (raw 64 -> 0.0 = "-200%" on the Iridium!)
    # Anchors: Don Solaris pairs raw 64 -> 0.5000, raw 96 -> 0.7500 (norm(96)=0.756).
    for n in (1, 2):
        kt = p[f"Filter {n} Keytrack"]
        setp(f"Filter{n}Keytrack", norm(kt))

    # --- modulation/matrix: Blofeld 16 slots -> Iridium matrix slots ---
    slot = 0
    for m in range(1, 17):
        src = p[f"Modulation {m} Source"]
        dst = p[f"Modulation {m} Destination"]
        amt = p[f"Modulation {m} Amount"]
        if not isinstance(src, str) or src == "off":
            continue
        slot += 1
        s_disp, ctrl_disp = _resolve_mod_source(p, src)
        d_disp = BLOFELD_MOD_DST.get(dst)
        if d_disp is None and noise_osc and dst in ("NoiseLevel", "Noise Bal."):
            # Blofeld-Modulation auf den Noise-Mixer -> Iridium Osc-Mix/Pan des Noise-Osc
            d_disp = f"Osc{noise_osc} Mix" if dst == "NoiseLevel" else f"Osc{noise_osc} Pan"
        if d_disp is None and isinstance(dst, str) and dst.endswith("PW/Wave"):
            # Blofeld "O1 PW/Wave": wavetable position for a wavetable osc, else WF warp (PW)
            try:
                on = int(dst[1])
            except (ValueError, IndexError):
                on = 0
            if 1 <= on <= 3:
                d_disp = f"WT{on} Position" if osc_is_wavetable.get(on) else f"WF{on} Warp"
        if seriell and not f2_bypass:
            # P1-2 (ANALYSIS-2026-11-15): in serial mode the audible F2 is the DigiFormer
            # (Filter2State 'Off') -> modulations to F2 must target the Former instead,
            # otherwise they go nowhere (A001 Velocity->F2 Cutoff etc.).
            d_disp = {"Filter2 Cutoff": "DF Amount", "Filter2 Reso": "DF Color",
                      "Filter2 Pan": "DF Pan"}.get(d_disp, d_disp)
        if s_disp and d_disp:
            mrow(slot, s_disp, ctrl_disp, d_disp, amt_bipolar(amt))
        else:
            unmapped.append(f"Modulation {m} ({src} -> {dst})")
    # direct filter modulation (Filter N Mod Source/Amount) -> extra matrix slots from 17
    for n in (1, 2):
        src = p[f"Filter {n} Mod Source"]
        if isinstance(src, str) and src != "off":
            slot += 1
            s_disp, ctrl_disp = _resolve_mod_source(p, src)
            d_disp = "Filter1 Cutoff" if n == 1 else "Filter2 Cutoff"
            if n == 2 and seriell and not f2_bypass:
                d_disp = "DF Amount"   # serial: F2 lives in the DigiFormer (P1-2)
            if s_disp:
                mrow(slot, s_disp, ctrl_disp, d_disp, amt_bipolar(p[f"Filter {n} Mod Amount"]))
            else:
                unmapped.append(f"Filter {n} Mod Source {src!r}")
    # Blofeld amplifier velocity (level dynamics, unipolar) -> own matrix slot
    # Velocity -> Volume. Amount 0.5 + 0.5*norm(raw) instead of
    # amt_bipolar (0.5 would be neutral/ineffective), because velocity is unipolar:
    # raw 0 = no effect, raw 127 = full effect. Additionally AmpVeloAmount (above).
    if amp_velo > 0:
        slot += 1
        setp(f"MatrixSrc{slot}", MATRIX_SRC["Velocity"], "Velocity")
        setp(f"MatrixDst{slot}", MATRIX_DST["Volume"], "Volume")
        setp(f"MatrixAmount{slot}", 0.5 + 0.5 * norm(amp_velo))
        setp(f"MatrixOnOff{slot}", 1.0, "Active")
    # Blofeld "Amplifier Mod Source/Amount" -> matrix slot -> Volume (previously unmapped;
    # A008 AmpEnv, A019/A043/A010/... LFO3 amt 64)
    amp_mod_src = p.get("Amplifier Mod Source")
    if isinstance(amp_mod_src, str) and amp_mod_src != "off":
        s_disp, ctrl_disp = _resolve_mod_source(p, amp_mod_src)
        if s_disp:
            slot += 1
            mrow(slot, s_disp, ctrl_disp, "Volume", amt_bipolar(p.get("Amplifier Mod Amount", 64)))
        else:
            unmapped.append(f"Amplifier Mod Source {amp_mod_src!r}")
    # Blofeld "Osc Pitch Source/Amount" (global pitch mod) -> matrix slot -> Pitch
    # (A008 LFO1*MW amt 74, several others amt 64; previously unmapped)
    osc_pitch_src = p.get("Osc Pitch Source")
    if isinstance(osc_pitch_src, str) and osc_pitch_src != "off":
        s_disp, ctrl_disp = _resolve_mod_source(p, osc_pitch_src)
        if s_disp:
            slot += 1
            mrow(slot, s_disp, ctrl_disp, "Pitch", amt_bipolar(p.get("Osc Pitch Amount", 64)))
        else:
            unmapped.append(f"Osc Pitch Source {osc_pitch_src!r}")
    # Serial: the Blofeld filter env opens BOTH filters (F1 -> F2). On the Iridium
    # filter1 gets the env (Filter1EnvAmount above), the DigiFormer (F2 replacement) needs
    # its own matrix slot -- otherwise it stays statically closed (finding 2026-11-14:
    # A001 DF 199 Hz -> serial ~40 dB attenuation at C5 -> Iridium -66 dBFS).
    if seriell and not f2_bypass:
        slot += 1
        setp(f"MatrixSrc{slot}", MATRIX_SRC["Filter1 Env"], "Filter1 Env")
        setp(f"MatrixDst{slot}", MATRIX_DST["DF Amount"], "DF Amount")
        setp(f"MatrixAmount{slot}", amt_bipolar(p["Filter 1 Env Amount"]))
        setp(f"MatrixOnOff{slot}", 1.0, "Active")

    # --- FX ---
    # P1-3 (ANALYSIS-2026-11-15): the mix key depends on the mapped FX TYPE, not on the
    # slot (old: FX2=Chorus mix landed in DelayDryWet). Blofeld effect parameters per
    # SysEx spec 5.2-5.9 (param k of FX n = parsed[f"Effect {n} Parameter {k}"]):
    #   Chorus: p1 Speed, p2 Depth | Flanger: p1/p2 + p5 Feedback | Phaser: + p5 Feedback,
    #   p6 Center | Overdrive: p2 Drive, p3 Post Gain | Delay (FX2): p4 Length, p5 Feedback,
    #   p6 Cutoff | Clk.Delay (FX2): p5 Feedback, p6 Cutoff, p11 Length (0..29 = 1/96..10 bars)
    FX_MIX_KEY = {"Chorus": "ChorusDryWet", "Flanger": "FlangerDryWet",
                  "Phaser": "PhaserDryWet", "Delay": "DelayDryWet", "Drive": "DriveDryWet"}
    FX_PARAMS = {
        "Chorus": {"ChorusSpeed": 1, "ChorusDepth": 2},
        "Flanger": {"FlangerSpeed": 1, "FlangerDepth": 2, "FlangerFeedback": 5},
        "Phaser": {"PhaserSpeed": 1, "PhaserDepth": 2, "PhaserFeedback": 5, "PhaserFreq": 6},
        "Overdrive": {"DriveAmount": 2, "DriveGain": 3},
        "Delay": {"DelayFeed": 5, "DelayHiCut": 6},
        "Clk.Delay": {"DelayFeed": 5, "DelayHiCut": 6},
    }
    for n, key in ((1, "FX1Type"), (2, "FX2Type")):
        t = p[f"Effect {n} Type"]
        t = t if isinstance(t, str) else ""
        ir = BLOFELD_FX_TO_IRIDIUM.get(t, "Off")
        setp(key, FX_TYPE[ir], ir)
        mixkey = FX_MIX_KEY.get(ir)
        if mixkey:
            setp(mixkey, norm(p[f"Effect {n} Mix"]))
        elif ir not in ("Off", "Reverb") and p.get(f"Effect {n} Mix", 0):
            unmapped.append(f"Effect {n} Mix for {ir} (no per-FX DryWet key)")
        for ikey, pnum in FX_PARAMS.get(t, {}).items():
            setp(ikey, norm(p.get(f"Effect {n} Parameter {pnum}", 0)))
        if ir == "Reverb":
            # no ReverbDryWet key exists -> mix via matrix slot Constant -> 'FX2 DryWet'
            # (runtime dst 144); Reverb params (spec 5.9): p2 Shape -> Color, p3 Decay -> Time
            setp("ReverbColor", norm(p.get(f"Effect {n} Parameter 2", 0)))
            setp("ReverbTime", norm(p.get(f"Effect {n} Parameter 3", 0)))
            mix = p.get(f"Effect {n} Mix", 0)
            if isinstance(mix, (int, float)) and mix > 0 and n == 2:
                slot += 1
                setp(f"MatrixSrc{slot}", MATRIX_SRC["Constant"], "Constant")
                setp(f"MatrixDst{slot}", MATRIX_DST["FX2 DryWet"], "FX2 DryWet")
                setp(f"MatrixAmount{slot}", 0.5 + 0.5 * norm(mix))
                setp(f"MatrixOnOff{slot}", 1.0, "Active")
        if t == "Clk.Delay":
            # clock-synced delay: Length raw 0..29 (1/96..10 bars) -> sync index (approx)
            setp("DelaySync", 1.0, "On")
            setp("DelayLeftSync", min(1.0, p.get("Effect 2 Parameter 11", 0) / 29.0))
            setp("DelayRightSync", min(1.0, p.get("Effect 2 Parameter 11", 0) / 29.0))

    # --- Filter-Drive -> FX1 Drive (2026-11-21, user finding A005 @ Iridium slot 204):
    # Blofeld "Filter 1/2 Drive" has no Iridium filter pendant (no matrix dst either) ->
    # simulate it as Effect 1 = Drive. DriveType from the Blofeld drive curve
    # (Iridium enum: 0 PNP, 1 Tube, 2 PickUp; Blofeld DRIVE_CURVES in blofeld_dump.py):
    # Tube -> Tube, Pickup 1/2 -> PickUp, all clip-like curves -> PNP (approx).
    DRIVE_CURVE_TO_IRIDIUM = {"Tube": 1.0, "Pickup 1": 2.0, "Pickup 2": 2.0}
    drives = []
    for fn in (1, 2):
        dv = p.get(f"Filter {fn} Drive", 0)
        if isinstance(dv, (int, float)) and dv > 0:
            drives.append((fn, dv, p.get(f"Filter {fn} Drive Curve", "")))
    if drives:
        fno, drive, curve = max(drives, key=lambda d: d[1])
        fx1_label = p.get("Effect 1 Type", "")
        fx1_mix = p.get("Effect 1 Mix", 0)
        if isinstance(fx1_label, str) and fx1_label != "Bypass" \
                and isinstance(fx1_mix, (int, float)) and fx1_mix > 0:
            unmapped.append(f"Effect 1 {fx1_label!r} (mix {fx1_mix}) replaced by "
                            "filter-drive simulation FX1=Drive")
        setp("FX1Type", FX_TYPE["Drive"], f"Drive (Filter {fno} Drive {int(drive)} simulation)")
        setp("DriveType", DRIVE_CURVE_TO_IRIDIUM.get(curve if isinstance(curve, str) else "", 0.0),
              f"{curve} -> DriveType")
        setp("DriveAmount", norm(int(drive)))
        setp("DriveGain", 0.5, "neutral")
        setp("DriveDryWet", norm(int(drive)))

    # --- arp ---
    unmapped += [k for k in p if k.startswith("Arp")]

    return ov, unmapped


def apply_to_template(template: dict, overrides: dict, name: str,
                      creator: str = "bloridium") -> dict:
    """Template (parse_qpat result) + overrides -> new params dict (all keys)."""
    params = {k: (v["value"], v["display"]) for k, v in template["params"].items()}
    params.update(overrides)
    # v8 template leak (P0-1, ANALYSIS-2026-11-15): matrix slots the mapping does NOT
    # overwrite keep their v8 enum values (e.g. Dst 71 'DF Amount', 145 'Reverb
    # Gain'), which point at wrong destinations in a v14 file -> neutralize them.
    for i in range(1, 41):
        if f"MatrixDst{i}" not in overrides:
            params[f"MatrixDst{i}"] = (0.0, "Off")
            params[f"MatrixOnOff{i}"] = (0.0, "Off")
    return {
        "name": name[:32], "creator": creator, "description": template.get("description", ""),
        "categories": template.get("categories", ["", "", "", ""]), "version": template.get("version", 14),
        "params": params,
    }
