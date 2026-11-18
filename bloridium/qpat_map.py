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

# enum tables (display -> value) - filter values from own OS4 exports
# (dumps/export-001, qpat v14); ATTENTION: numbering differs from older files!
OSC_TYPE = {"Wavetable": 0.0, "Waveform": 1.0, "Particle": 2.0, "Resonator": 3.0, "Off": 4.0}
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
FX_TYPE = {"Off": 0.0, "Phaser": 1.0, "Chorus": 2.0, "Flanger": 3.0, "Delay": 4.0,
           "Reverb": 5.0, "EQ": 6.0, "Drive": 7.0, "Compressor": 8.0}

# Blofeld shape (Spec 4.1) -> Iridium (OscType, WF shape)
BLOFELD_SHAPE_TO_IRIDIUM = {
    "off": ("Off", None), "Pulse": ("Waveform", "Square"), "Saw": ("Waveform", "Sawtooth"),
    "Triangle": ("Waveform", "Triangle"), "Sine": ("Waveform", "Sine"),
}
# Blofeld wavetable (shape label, SHAPES from index 5) -> Iridium OscN WavetableTable ID.
# IDs v14 from own OS4 exports + factory dumps (e.g. dumps/00003-WT Probe.qpat:
# Osc1WavetableTable 2.0 = "Mallet Syn"). Names from the Blofeld side (SHAPES list).
BLOFELD_WAVETABLE_TO_IRIDIUM = {
    "Resonant": 0.0, "MalletSyn": 2.0, "Bellish": 4.0, "Saw-Sweep": 6.0, "Add Harm": 9.0,
    "Reso 3 HP": 10.0, "Clipper": 13.0, "Organ Syn": 14.0, "SquareSaw": 15.0,
    "Polated": 17.0, "Robotic": 20.0, "StrongHrm": 21.0, "2 Echoes": 25.0,
    "Formant 2": 26.0, "FmnVocal": 27.0, "SawSync 3": 34.0, "PulSync 1": 35.0,
    "PulSync 3": 37.0, "K+Strong1": 47.0, "1-2-3-4-5": 50.0, "Vibes": 62.0,
    "Glassy": 79.0,
}
# Blofeld filter type (Spec 4.4) -> Iridium Filter12Type (v14 values).
# Notch/Comb are approximations (the real Comb-/PPG models live in the DigiFormer,
# but selecting them would be a routing change of its own -> see unmapped).
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

# ---- Iridium routing/matrix enums (values from dumps/export-001 = own OS4 exports, qpat v14) ----
OSC_DESTINATION = {"Main": 0.0, "VCA": 1.0, "DF 0 Fil 100": 2.0, "DF 100 Fil 0": 22.0}
FILTER_FORMER_ROUTING = {"Former > Filter": 0.0, "Filter > Former": 1.0, "Parallel": 2.0}
FILTER_LINK = {"Single": 0.0, "Boost": 1.0, "Independent": 6.0, "Linked": 7.0}
# Filter2State (v14/v15 same values: 0=Active, 1=Bypass, 2=Off).
# ATTENTION: 'Bypass' leaked the dry signal past F1 - only 'Off' switches F2
# off cleanly (evidence: dumps/00202-SH Power.qpat, v15 Filter2State=2.0 'Off').
# That is why the mapping below sets Filter2State to 'Off', never 'Bypass',
# whenever filter 2 must not be heard.
FILTER2_STATE = {"Active": 0.0, "Bypass": 1.0, "Off": 2.0}
MATRIX_SRC = {"Off": 0.0, "Amp Env": 1.0, "Filter1 Env": 2.0, "Filter2 Env": 3.0,
              "Free Env1": 4.0, "Free Env2": 5.0, "Free Env3": 6.0,
              "LFO 1": 7.0, "LFO 2": 8.0, "LFO 3": 9.0, "LFO 4": 10.0, "LFO 5": 11.0, "LFO 6": 12.0,
              "Pitch Bend": 15.0, "Wheel": 14.0, "After Touch": 16.0,
              "Keytrack": 31.0, "Velocity": 32.0}
MATRIX_DST = {"Off": 0.0, "Pitch": 1.0, "Osc1 Pitch": 2.0, "Osc2 Pitch": 3.0, "Osc3 Pitch": 4.0,
              "Osc1 Mix": 5.0, "Osc2 Mix": 6.0, "Osc3 Mix": 7.0,
              "Filter1 Cutoff": 100.0, "Filter1 Reso": 101.0,
              # v14 values from own OS4 exports (dumps/export-0*/v14: 104='Filter2 Cutoff',
              # 105='Filter2 Reso'); v8 values 103/71 must NOT be used in v14
              # (P0-1, ANALYSIS-2026-11-15: otherwise the serial DF env slot lands on the
              # wrong destination -> DigiFormer stays closed, serial patches down to -64.8 dBFS)
              "Filter2 Cutoff": 104.0, "Filter2 Reso": 105.0,
              "Filt1Env Attack": 113.0, "Filt1Env Sustain": 114.0, "Filt1Env Decay": 123.0,
              # Volume: v14 exports are silent; v8 slot tables know both 112 AND 115,
              # v15=152 -> take 115.0, verify on the device (112 is v9 'Filt1Env Sustain')
              "Volume": 115.0, "Pan": 144.0,
              "DF Amount": 95.0,   # v14: 95 (v8 was 71/74)
              "DF Color": 96.0,    # v11: 96; not present in v14 exports -> verify on the device
              # wavetable position / waveform warp (v14 values from own OS4 exports)
              "WT1 Position": 11.0, "WT2 Position": 39.0, "WT3 Position": 67.0,
              "WF1 Warp": 18.0, "WF2 Warp": 46.0, "WF3 Warp": 74.0}
# Blofeld mod source -> Iridium MatrixSrc display (pressure combos approx. to After Touch)
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
# Blofeld mod destination -> Iridium MatrixDst display (FE = filter envelope -> Filt1Env)
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
    wheel/velocity do not fully add up on the Iridium."""
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
        setp(f"Osc{n}FinePitch", norm(p[f"Osc {n} Detune"]), "")
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
    unmapped += ["Osc 2 Sync to O3", "Osc Pitch Source", "Osc Pitch Amount"]

    # --- glide / unisono ---
    setp("GlideOnOff", 1.0 if p.get("Glide") else 0.0, "On" if p.get("Glide") else "Off")
    # Glide Rate time-calibrated (log scale), not linear: norm() mapped too high (see above)
    _gr = p.get("Glide Rate", 0)
    setp("GlideRate", glide_rate_norm(_gr), f"~{blofeld_glide_seconds(_gr):.3f}s")
    setp("UnisonoCount", norm((p.get("Allocation/Unisono", 0) >> 5) & 0x07 or 1))
    setp("UnisonoDetune", norm(p.get("Unisono Detune", 0)))
    # Aftertouch: the Blofeld sends channel AT, but the template (and all OS4 exports)
    # sit at AfterTouchDoPoly=1.0 'Poly AT' -> matrix src 'After Touch' then does NOT
    # listen to channel AT (P0-2, ANALYSIS-2026-11-15: A019 'does not react to AT',
    # A043 'strong AT bending'). Switch global to mono/channel AT.
    setp("AfterTouchDoPoly", 0.0, "Mono AT")

    # --- mixer extras ---
    # key is called "RingModOsc1ToOsc2" in the template/device (not "RingmodOsc12"!)
    setp("RingModOsc1ToOsc2", norm(p.get("Mixer RingMod Level", 0)))
    unmapped += ["Mixer Noise Level/Balance/Colour (no direct qpat key)"]

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
        unmapped.append(f"LFO {n} Shape/Delay/Fade/Keytrack")

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
        s_disp = BLOFELD_MOD_SRC.get(src)
        d_disp = BLOFELD_MOD_DST.get(dst)
        if d_disp is None and isinstance(dst, str) and dst.endswith("PW/Wave"):
            # Blofeld "O1 PW/Wave": wavetable position for a wavetable osc, else WF warp (PW)
            try:
                on = int(dst[1])
            except (ValueError, IndexError):
                on = 0
            if 1 <= on <= 3:
                d_disp = f"WT{on} Position" if osc_is_wavetable.get(on) else f"WF{on} Warp"
        if s_disp and d_disp:
            setp(f"MatrixSrc{slot}", MATRIX_SRC[s_disp], s_disp)
            setp(f"MatrixDst{slot}", MATRIX_DST[d_disp], d_disp)
            setp(f"MatrixAmount{slot}", amt_bipolar(amt))
            setp(f"MatrixOnOff{slot}", 1.0, "Active")
        else:
            unmapped.append(f"Modulation {m} ({src} -> {dst})")
    # direct filter modulation (Filter N Mod Source/Amount) -> extra matrix slots from 17
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
    # note: the wet/dry mix only lands on ChorusDryWet (FX1) / DelayDryWet (FX2);
    # the Iridium has no single mix key per FX slot
    for n, key in ((1, "FX1Type"), (2, "FX2Type")):
        t = p[f"Effect {n} Type"]
        ir = BLOFELD_FX_TO_IRIDIUM.get(t if isinstance(t, str) else "", "Off")
        setp(key, FX_TYPE[ir], ir)
        mixkey = {1: "ChorusDryWet", 2: "DelayDryWet"}.get(n)
        if mixkey:
            setp(mixkey, norm(p[f"Effect {n} Mix"]))

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
