"""Mapping Blofeld-SNDD -> Iridium/Quantum .qpat-Parameter (Key-Level).

Werte: Blofeld raw 0..127 -> Iridium norm = raw/127 (bei 0..1-Parametern);
bipolar (Mitte 64) -> raw/127 (0.5 ~ Mitte). Enums siehe Tabellen unten
(aus offiziellen Factory-.qpat extrahiert).
"""

from __future__ import annotations

import math

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
# Blofeld-Wavetable (Shape-Label, SHAPES ab Index 5) -> Iridium OscN WavetableTable-ID.
# IDs v14 aus eigenen OS4-Exporten + Factory-Dumps (z. B. dumps/00003-WT Probe.qpat:
# Osc1WavetableTable 2.0 = "Mallet Syn"). Namen von Blofeld-Seite (SHAPES-Liste).
BLOFELD_WAVETABLE_TO_IRIDIUM = {
    "Resonant": 0.0, "MalletSyn": 2.0, "Bellish": 4.0, "Saw-Sweep": 6.0, "Add Harm": 9.0,
    "Reso 3 HP": 10.0, "Clipper": 13.0, "Organ Syn": 14.0, "SquareSaw": 15.0,
    "Polated": 17.0, "Robotic": 20.0, "StrongHrm": 21.0, "2 Echoes": 25.0,
    "Formant 2": 26.0, "FmnVocal": 27.0, "SawSync 3": 34.0, "PulSync 1": 35.0,
    "PulSync 3": 37.0, "K+Strong1": 47.0, "1-2-3-4-5": 50.0, "Vibes": 62.0,
    "Glassy": 79.0,
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
# Filter2State (v14/v15 gleiche Werte: 0=Active, 1=Bypass, 2=Off).
# ACHTUNG: 'Bypass' leaked das Dry-Signal am F1 vorbei – erst 'Off' schaltet F2
# sauber ab (Beleg: dumps/00202-SH Power.qpat, v15 Filter2State=2.0 'Off').
FILTER2_STATE = {"Active": 0.0, "Bypass": 1.0, "Off": 2.0}
MATRIX_SRC = {"Off": 0.0, "Amp Env": 1.0, "Filter1 Env": 2.0, "Filter2 Env": 3.0,
              "Free Env1": 4.0, "Free Env2": 5.0, "Free Env3": 6.0,
              "LFO 1": 7.0, "LFO 2": 8.0, "LFO 3": 9.0, "LFO 4": 10.0, "LFO 5": 11.0, "LFO 6": 12.0,
              "Pitch Bend": 15.0, "Wheel": 14.0, "After Touch": 16.0,
              "Keytrack": 31.0, "Velocity": 32.0}
MATRIX_DST = {"Off": 0.0, "Pitch": 1.0, "Osc1 Pitch": 2.0, "Osc2 Pitch": 3.0, "Osc3 Pitch": 4.0,
              "Osc1 Mix": 5.0, "Osc2 Mix": 6.0, "Osc3 Mix": 7.0,
              "Filter1 Cutoff": 100.0, "Filter1 Reso": 101.0,
              # v14-Werte aus eigenen OS4-Exporten (dumps/export-0*/v14: 104='Filter2 Cutoff',
              # 105='Filter2 Reso'); v8-Werte 103/71 duerfen in v14 NICHT verwendet werden
              # (P0-1, ANALYSIS-2026-11-15: sonst landet der serielle DF-Env-Slot auf falschem
              # Ziel -> DigiFormer bleibt zu, serielle Patches bis -64.8 dBFS)
              "Filter2 Cutoff": 104.0, "Filter2 Reso": 105.0,
              "Filt1Env Attack": 113.0, "Filt1Env Sustain": 114.0, "Filt1Env Decay": 123.0,
              # Volume: v14-Exporte schweigen; v8-Slot-Tabellen kennen 112 UND 115,
              # v15=152 -> 115.0 nehmen, am Geraet verifizieren (112 ist v9 'Filt1Env Sustain')
              "Volume": 115.0, "Pan": 144.0,
              "DF Amount": 95.0,   # v14: 95 (v8 war 71/74)
              "DF Color": 96.0,    # v11: 96; in v14-Exporten nicht belegt -> am Geraet verifizieren
              # Wavetable-Position / Waveform-Warp (v14-Werte aus eigenen OS4-Exporten)
              "WT1 Position": 11.0, "WT2 Position": 39.0, "WT3 Position": 67.0,
              "WF1 Warp": 18.0, "WF2 Warp": 46.0, "WF3 Warp": 74.0}
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


# ---- Glide Rate: Zeit-Kalibrierung (beide Seiten log-Skala in der Zeit) ----
# Blofeld "Glide Rate" raw 0..127 ist NICHT linear in der Zeit (Blofeld-Handbuch: niedrige
# Werte = Millisekunden, hohe = mehrere Sekunden). Iridium "GlideRate" norm 0..1 ebenso
# nicht. Lineares norm() setzt deshalb zu hohe Werte (Beobachtung 2026-11-09: A073 Chord
# Hose raw 48 -> norm 0.378 -> "Glide Rate 0.29sec" am Iridium, deutlich laenger als am
# Blofeld). Anker (gemessen/dokumentiert):
#   - Blofeld raw 20 <-> Iridium norm 0.15: Don-Solaris-Factory-Paare (Blofeld Rate 20 =
#     Iridium GlideRate 0.15); 0.15 ist das Iridium-Default = 0.045 s (Handbuch) ->
#     t_blo(20) = 0.045 s.
#   - Iridium norm 0.378 zeigt am Geraet "0.29 s" (Display abgelesen bei A073-Import).
#   - Blofeld raw 127 = "several seconds" (Handbuch) -> konservativ 5 s.
# Beide Kurven exponential in der Zeit; Mapping raw -> norm ueber t_blo(raw) = t_irr(norm).
GLIDE_BLO_T_AT_20 = 0.045   # s bei raw 20 (Don-Solaris-Anker)
GLIDE_BLO_T_MAX = 5.0       # s bei raw 127 ("several seconds", konservativ)
GLIDE_IRR_ANCHORS = ((0.15, 0.045), (0.378, 0.29))   # (norm, s am Geraet)


def blofeld_glide_seconds(raw: int) -> float:
    """Blofeld Glide Rate raw 0..127 -> Gleitzeit in s (exponential)."""
    raw = max(0, min(127, int(raw)))
    return GLIDE_BLO_T_AT_20 * (GLIDE_BLO_T_MAX / GLIDE_BLO_T_AT_20) ** ((raw - 20) / 107.0)


def iridium_glide_seconds(norm_v: float) -> float:
    """Iridium GlideRate norm 0..1 -> Gleitzeit in s (exponential durch die Anker)."""
    (n0, t0), (n1, t1) = GLIDE_IRR_ANCHORS
    return t0 * (t1 / t0) ** ((norm_v - n0) / (n1 - n0))


def glide_rate_norm(raw: int) -> float:
    """Blofeld Glide Rate raw -> Iridium GlideRate norm ueber gleiche Gleitzeit."""
    t = blofeld_glide_seconds(raw)
    (n0, t0), (n1, t1) = GLIDE_IRR_ANCHORS
    n = n0 + (n1 - n0) * math.log(t / t0) / math.log(t1 / t0)
    return max(0.0, min(1.0, n))


# ---- LFO-Clock: Blofeld Sync-Speed (SysEx-Doc 4.6) -> Iridium SyncRatio ----
# Blofeld LFO Speed raw (Sync=1): raw//2 -> bars pro Zyklus (Fraktionen < 1 bar dezimal)
BLO_LFO_BARS = [1280, 1152, 1024, 896, 768, 640, 576, 512, 448, 384, 320, 288, 256, 224, 192,
                160, 144, 128, 112, 96, 80, 72, 64, 56, 48, 40, 36, 32, 28, 24, 20, 18, 16,
                14, 12, 10, 9, 8, 7, 6, 5, 4, 3.5, 3, 2.5, 2, 1.5, 1,
                0.5, 2/3, 0.5, 0.375, 1/3, 0.25, 0.1875, 1/6, 0.125, 0.09375, 1/12, 0.0625,
                0.046875, 1/24, 0.03125, 1/48]
# Iridium LfoN SyncRatio-Index -> beats pro Zyklus (Display-Werte eigener OS4-Exporte:
# 0->1024, 11->24, 12->16, 15->6, 16->1/1=4 beats, 22->1/8=.5, 23->1/16 dot=.375, 24->1/16=.25)
IRR_SYNC_BEATS = [1024, 768, 512, 384, 256, 192, 128, 96, 64, 48, 32, 24, 16, 12, 8, 6, 4,
                  3, 2, 1.5, 1, 0.75, 0.5, 0.375, 0.25, 0.1875, 0.125, 0.0833]


def blofeld_lfo_clock_beats(raw: int) -> float:
    """Blofeld LFO Clock-Index (Sync=1) -> beats pro Zyklus (1 bar = 4 beats)."""
    bars = BLO_LFO_BARS[min(max(raw, 0) // 2, len(BLO_LFO_BARS) - 1)]
    return bars * 4.0


def iridium_sync_ratio_index(beats: float) -> int:
    """Naechster Iridium SyncRatio-Index fuer eine beats/Zyklus-Zahl (log-Distanz)."""
    lb = [math.log(b) for b in IRR_SYNC_BEATS]
    t = math.log(max(beats, 1e-6))
    return min(range(len(lb)), key=lambda i: abs(lb[i] - t))


def amt_bipolar(raw: int) -> float:
    """Blofeld Mod-Amount (bipolar, Mitte 64 = 0) -> Iridium Matrix-Amount 0..1
    zentriert um 0.5:  64 -> 0.5 (neutral), 127 -> 1.0, 0 -> 0.0.
    Verhindert, dass Wheel/Velocity auf dem Iridium voll aufaddieren."""
    return max(0.0, min(1.0, 0.5 + (raw - 64) / 254.0))


# ---- Filter-Cutoff-Kalibrierung (2026-11-14) ----
# Blofeld-Handbuch: Cutoff raw 0..127 skaliert in HALBTONSCHRITTEN, Anker raw 64 = 440 Hz
# ("At a value of 64 and a Resonance value of 114, the filter oscillates with 440 Hz").
# Iridium (calib 200-205, HANDOVER-2026-11-09): 17.8 Hz @ norm 0.10, 19912 Hz @ 1.00
# -> log10(f) = 0.9117 + 3.387*norm.  Direkt norm(raw) war falsch (Befund 2026-11-14:
# A001 raw 64 -> 416 Hz statt 440 Hz; seriell mit DF 199 Hz daempft das Note C5 um
# ~40 dB -> Iridium -66 dBFS, "Filter laesst kaum etwas durch").
IRIDIUM_CUTOFF_LOG_A = 0.9117   # log10(Hz) bei Iridium-norm 0
IRIDIUM_CUTOFF_LOG_B = 3.387    # Dekaden pro norm
BLOFELD_CUTOFF_ANCHOR_RAW = 64.0
BLOFELD_CUTOFF_ANCHOR_HZ = 440.0


def blofeld_cutoff_norm(raw) -> float:
    """Blofeld Filter-Cutoff raw 0..127 -> Iridium FilterCutOff/DigiFormerAmount norm 0..1
    ueber Hz-Bruecke (beide Skalen log; Blofeld in Halbtonschritten um 440 Hz @ raw 64)."""
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

    # --- Oszillatoren ---
    shape_raw_idx = [8, 24, 40]     # SDATA-Indizes OscN Shape
    oct_idx = [1, 17, 33]
    semi_idx = [2, 18, 34]
    osc_is_wavetable = {}
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
        osc_is_wavetable[n] = (otype == "Wavetable")
        setp(f"Osc{n}Type", OSC_TYPE[otype], otype)
        if wf:
            setp(f"Osc{n}WaveformShape", WF_SHAPE[wf], wf)
        if otype == "Wavetable":
            # Wavetable-Auswahl: Blofeld-Wavetable-Name -> Iridium OscN WavetableTable-ID
            # (IDs v14 aus eigenen OS4-Exporten, z. B. MalletSyn -> 2 "Mallet Syn").
            # Ohne Bridge-Eintrag bleibt das Template-Table (0 "Resonant") stehen.
            tbl = BLOFELD_WAVETABLE_TO_IRIDIUM.get(shape_label if isinstance(shape_label, str) else "")
            if tbl is not None:
                setp(f"Osc{n}WavetableTable", tbl, shape_label)
            else:
                unmapped.append(f"Osc {n} Wavetable {shape_label!r} (kein Iridium-Aequivalent)")
            # Beim Blofeld ist "Pulsewidth" bei Wavetable-Osc die Wave-Position
            setp(f"Osc{n}WavetablePosition", norm(p[f"Osc {n} Pulsewidth"]))
            setp(f"Osc{n}WavetableBrilliance", norm(p[f"Osc {n} Brilliance"]))
        else:
            # Blofeld-Handbuch: Pulsewidth wirkt NUR bei Shape 'Pulse' (raw 0 = <1%,
            # raw 127 = 50%); bei Saw/Triangle/Sine "hat dieser Parameter keine Funktion".
            # Am Iridium ist WaveformPW dagegen der Warp und wirkt AUCH bei Saw ->
            # dort neutral 0.5, sonst wird aus Saegezahn eine Rechteckwelle
            # (Befund 2026-11-14: A001 PW raw 100 -> norm=0.7874 = Rechteck statt Saw).
            if shape_label == "Pulse":
                setp(f"Osc{n}WaveformPW", norm(p[f"Osc {n} Pulsewidth"]) * 0.5, "")
            else:
                setp(f"Osc{n}WaveformPW", 0.5, "neutral (Blofeld PW ohne Funktion)")
            # Kernels Count (OS4 zeigt WaveformDesity als "Kernels"): Blofeld hat keinen
            # Kernel-Parameter -> 0.0 = 1 Welle, keine Kopien. Template-Default 0.22 liess
            # A001 OSC2 als "Kernels 2.5" laufen (Befund 2026-11-14).
            setp(f"Osc{n}WaveformDesity", 0.0, "1 Kernel (aus)")
        # CoarsePitch: Blofeld Octave (raw 64 = 8', Schritte 12; raw > 64 = hoehere Oktave)
        # ACHTUNG Vorzeichen: raw 52 = -12 semi (16'), raw 76 = +12 semi (4')!
        # (alt: 64 - raw lieferte bei Osc3 raw 52 -> +12 statt -12, eine Oktave zu hoch)
        oct_up = (sdata[oct_idx[n - 1]] - 64) / 12.0
        semi = sdata[semi_idx[n - 1]] - 64
        setp(f"Osc{n}CoarsePitch", 24.0 + 12.0 * oct_up + semi, f"{semi:+.0f} semi")
        setp(f"Osc{n}FinePitch", norm(p[f"Osc {n} Detune"]), "")
        setp(f"Osc{n}Vol", norm(p[f"Mixer Osc {n} Level"]), "")
        setp(f"Osc{n}Pan", norm(p[f"Mixer Osc {n} Balance"]), "")
        for k in ("Bend Range", "Keytrack", "FM Source", "FM Amount", "PWM Source",
                  "PWM Amount", "Limit WT"):
            unmapped.append(f"Osc {n} {k}")
        if otype != "Wavetable":
            unmapped.append(f"Osc {n} Brilliance")
    unmapped += ["Osc 2 Sync to O3", "Osc Pitch Source", "Osc Pitch Amount"]

    # --- Glide / Unisono ---
    setp("GlideOnOff", 1.0 if p.get("Glide") else 0.0, "On" if p.get("Glide") else "Off")
    # Glide Rate zeit-kalibriert (log-Skala), nicht linear: norm() setzte zu hohe Werte
    _gr = p.get("Glide Rate", 0)
    setp("GlideRate", glide_rate_norm(_gr), f"~{blofeld_glide_seconds(_gr):.3f}s")
    setp("UnisonoCount", norm((p.get("Allocation/Unisono", 0) >> 5) & 0x07 or 1))
    setp("UnisonoDetune", norm(p.get("Unisono Detune", 0)))
    # Aftertouch: Blofeld sendet Channel AT, aber das Template (und alle OS4-Exporte)
    # steht auf AfterTouchDoPoly=1.0 'Poly AT' -> Matrix-Src 'After Touch' hoert dann
    # NICHT auf Channel AT (P0-2, ANALYSIS-2026-11-15: A019 'reagiert nicht auf AT',
    # A043 'starkes AT-Bending'). Global auf Mono/Channel AT stellen.
    setp("AfterTouchDoPoly", 0.0, "Mono AT")

    # --- Mixer extras ---
    # Key heisst im Template/Device "RingModOsc1ToOsc2" (nicht "RingmodOsc12"!)
    setp("RingModOsc1ToOsc2", norm(p.get("Mixer RingMod Level", 0)))
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
    # F2-Routing haengt vom Blofeld "Filter Routing" ab (Befund HANDOVER 2026-11-14):
    # seriell (1): Kette F1 -> F2 -> Amp. Iridium: F2 wandert in den DigiFormer
    #   (Routing 'Filter > Former', Filter2-Stufe 'Off', FilterLink 'Single' –
    #   'Linked' machte B stumm, z.B. A008 FilterLink 7.0).
    # parallel (0): F1 und F2 parallel. Iridium: F2 bleibt Filter 2 (Active),
    #   Former = Bypass, Routing 'Parallel'.
    seriell = p.get("Filter Routing") == 1
    f2_bypass = BLOFELD_FILTER_TO_IRIDIUM.get(f2_label if isinstance(f2_label, str) else "") is None
    if seriell:
        if f2_bypass:
            # F2 Bypass: Former bypass UND Filter2State 'Off' – 'Bypass' allein leaked
            # das Dry-Signal am F1 vorbei (Filter "zu offen")
            setp("DigiFormerType", DIGIFORMER_TYPE["Bypass"], "Bypass")
            setp("DigiFormerAmount", 0.0)
        else:
            former = BLOFELD_FILTER2_TO_FORMER.get(f2_label if isinstance(f2_label, str) else "", "Nave LP24")
            setp("DigiFormerType", DIGIFORMER_TYPE[former], former)
            setp("DigiFormerAmount", blofeld_cutoff_norm(p["Filter 2 Cutoff"]))  # Cutoff -> Amount (Hz-Kalib)
            setp("DigiFormerColor", norm(p["Filter 2 Resonance"]))  # approx: Reso -> Color
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
    # (Filter-Routing/Keytrack/Mod siehe oben gemappt; Drive/Curve/FM/Pan ungemappt)

    # --- Amp ---
    setp("MainVolume", norm(p.get("Amplifier Volume", 127)))
    setp("LayerVolume", 1.0)
    amp_velo = p.get("Amplifier Velocity", 64)
    if not isinstance(amp_velo, (int, float)):
        amp_velo = 64
    # AmpVelo unipolar 0..127 -> norm. ACHTUNG bipolar-Falle: Matrix-Amounts sind
    # um 0.5 zentriert (0.5 = neutral) -> Vel->Volume braucht 0.5 + 0.5*norm (64 -> 0.75)
    setp("AmpVeloAmount", norm(amp_velo))
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
    # ACHTUNG Key-Namen: Template/Device kennen "Lfo1Speed" (klein), NICHT "LFO1Speed"!
    # (falsch: LFO1Speed -> eigener Key, Device ignoriert ihn, LFO lief auf Template-Default
    # 0.5 -> hörbares Tremolo, z.B. A022 Slot 14 LFO2->Volume). Ausserdem: Blofeld Speed raw
    # ist bei Sync=1 ein Clock-Index (SysEx-Doc 4.6, bars/Zyklus, z.B. raw 14 = 512 bars =
    # praktisch statisch) -> als free Speed gemappt wurde daraus norm(14)=0.11 -> Tremolo.
    # Iridium: LfoN Sync + SyncRatio (beats/Zyklus, Index) + Speed (nur free).
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

    # --- Routing: Blofeld Osc->Mixer->F1->F2->Amp entspricht Iridium
    #     Osc Destination 'DF 0 Fil 100' (100 % in den Filter; Former-Anteil 0 –
    #     Former ist seriell F2 bzw. parallel Bypass, siehe Filter-Block oben) ---
    for n in (1, 2, 3):
        setp(f"Osc{n}Destination", OSC_DESTINATION["DF 0 Fil 100"], "DF 0 Fil 100")
    # Filter-Keytrack: Blofeld raw 0..127 = -200%..+196% (64 = 0%, Offset-Binaer!),
    # Iridium FilterNKeytrack norm 0..1 = -200%..+200% (0.5 = 0%) -> direkt norm(raw).
    # ACHTUNG: frueheres (kt-64)/64 lieferte -1..+1 (raw 64 -> 0.0 = "-200%" am Iridium!)
    # Anker: Don-Solaris-Paare raw 64 -> 0.5000, raw 96 -> 0.7500 (norm(96)=0.756).
    for n in (1, 2):
        kt = p[f"Filter {n} Keytrack"]
        setp(f"Filter{n}Keytrack", norm(kt))

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
        if d_disp is None and isinstance(dst, str) and dst.endswith("PW/Wave"):
            # Blofeld "O1 PW/Wave": bei Wavetable-Osc die WT-Position, sonst WF-Warp (PW)
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
    # Blofeld Amplifier Velocity (Pegel-Dynamik, unipolar) -> eigener Matrix-Slot
    # Velocity -> Volume. Amount bipolar um 0.5: 0.5 + 0.5*norm(raw) statt
    # amt_bipolar (0.5 waere neutral/wirkungslos). Zusaetzlich AmpVeloAmount (oben).
    if amp_velo > 0:
        slot += 1
        setp(f"MatrixSrc{slot}", MATRIX_SRC["Velocity"], "Velocity")
        setp(f"MatrixDst{slot}", MATRIX_DST["Volume"], "Volume")
        setp(f"MatrixAmount{slot}", 0.5 + 0.5 * norm(amp_velo))
        setp(f"MatrixOnOff{slot}", 1.0, "Active")
    # Seriell: Blofeld-Filter-Env oeffnet BEIDE Filter (F1 -> F2). Am Iridium bekommt
    # Filter1 die Env (Filter1EnvAmount oben), der DigiFormer (F2-Ersatz) braucht einen
    # eigenen Matrix-Slot -- sonst bleibt er statisch zu (Befund 2026-11-14: A001
    # DF 199 Hz -> seriell ~40 dB Daempfung bei C5 -> Iridium -66 dBFS).
    if seriell and not f2_bypass:
        slot += 1
        setp(f"MatrixSrc{slot}", MATRIX_SRC["Filter1 Env"], "Filter1 Env")
        setp(f"MatrixDst{slot}", MATRIX_DST["DF Amount"], "DF Amount")
        setp(f"MatrixAmount{slot}", amt_bipolar(p["Filter 1 Env Amount"]))
        setp(f"MatrixOnOff{slot}", 1.0, "Active")

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
    # v8-Template-Leck (P0-1, ANALYSIS-2026-11-15): Matrix-Slots, die das Mapping NICHT
    # ueberschreibt, behalten ihre v8-Enum-Werte (z. B. Dst 71 'DF Amount', 145 'Reverb
    # Gain'), die in einer v14-Datei auf falsche Ziele zeigen -> neutralisieren.
    for i in range(1, 41):
        if f"MatrixDst{i}" not in overrides:
            params[f"MatrixDst{i}"] = (0.0, "Off")
            params[f"MatrixOnOff{i}"] = (0.0, "Off")
    return {
        "name": name[:32], "creator": creator, "description": template.get("description", ""),
        "categories": template.get("categories", ["", "", "", ""]), "version": template.get("version", 14),
        "params": params,
    }
