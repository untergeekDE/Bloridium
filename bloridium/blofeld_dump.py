"""Blofeld SNDD (Sound Dump) Parser/Builder – offizielle Spec: Blofeld_sysex_v1_04.pdf.

Message:  F0 3E 13 DEV 10 BB NN <SDATA 383 B> CHK F7
  SDATA  : Parameter-Indizes 0..382 (siehe Spec 3.1)
  CHK    : Summe aller SDATA-Bytes, auf 7 Bit maskiert (Status/IDs nicht mitgerechnet)

SNDP (Parameter Change): F0 3E 13 DEV 20 LL HH PP XX F7  (HH PP = Parameterindex 0..382)
SNDR (Request):          F0 3E 13 DEV 00 BB NN F7        (BB NN = Location, z.B. 7F 00 = Edit Buffer)
"""

from __future__ import annotations

# ---- Wertetabellen (Spec 4.x / 5.x) ----------------------------------------

SHAPES = ["off", "Pulse", "Saw", "Triangle", "Sine", "Alt 1", "Alt 2", "Resonant",
          "Resonant2", "MalletSyn", "Sqr-Sweep", "Bellish", "Pul-Sweep", "Saw-Sweep",
          "MellowSaw", "Feedback", "Add Harm", "Reso 3 HP", "Wind Syn", "High Harm",
          "Clipper", "Organ Syn", "SquareSaw", "Formant 1", "Polated", "Transient",
          "ElectricP", "Robotic", "StrongHrm", "PercOrgan", "ClipSweep", "ResoHarms",
          "2 Echoes", "Formant 2", "FmnVocal", "MicroSync", "Micro PWM", "Glassy",
          "Square HP", "SawSync 1", "SawSync 2", "SawSync 3", "PulSync 1", "PulSync 2",
          "PulSync 3", "SinSync 1", "SinSync 2", "SinSync 3", "PWM Pulse", "PWM Saw",
          "Fuzz Wave", "Distorted", "HeavyFuzz", "Fuzz Sync", "K+Strong1", "K+Strong2",
          "K+Strong3", "1-2-3-4-5", "19/twenty", "Wavetrip1", "Wavetrip2", "Wavetrip3",
          "Wavetrip4", "MaleVoice", "Low Piano", "ResoSweep", "Xmas Bell", "FM Piano",
          "Fat Organ", "Vibes", "Chorus 2", "True PWM", "UpperWaves"]

FM_SOURCES = ["off", "Osc 1", "Osc 2", "Osc 3", "Noise", "LFO 1", "LFO 2", "LFO 3",
              "FilterEnv", "AmpEnv", "Env3", "Env4"]

GLIDE_MODES = ["Portamento", "fingered P", "Glissando", "fingered G"]

FILTER_TYPES = ["Bypass", "LP 24dB", "LP 12dB", "BP 24dB", "BP 12dB", "HP 24dB", "HP 12dB",
                "Notch24dB", "Notch12dB", "Comb+", "Comb-", "PPG LP"]

LFO_SHAPES = ["Sine", "Triangle", "Square", "Saw", "Random", "S&H"]

MOD_SOURCES = ["off", "LFO 1", "LFO1*MW", "LFO 2", "LFO2*Press", "LFO 3", "FilterEnv",
               "AmpEnv", "Env3", "Env4", "Keytrack", "Velocity", "Rel. Velo", "Pressure",
               "Poly Press", "Pitch Bend", "Mod Wheel", "Sustain", "Foot Ctrl", "BreathCtrl",
               "Control W", "Control X", "Control Y", "Control Z", "Unisono V.",
               "Modifier 1", "Modifier 2", "Modifier 3", "Modifier 4", "minimum", "MAXIMUM"]

MOD_DESTS = ["Pitch", "O1 Pitch", "O1 FM", "O1 PW/Wave", "O2 Pitch", "O2 FM", "O2 PW/Wave",
             "O3 Pitch", "O3 FM", "O3 PW", "O1 Level", "O1 Balance", "O2 Level", "O2 Balance",
             "O3 Level", "O3 Balance", "RMod Level", "RMod Bal.", "NoiseLevel", "Noise Bal.",
             "F1 Cutoff", "F1 Reson.", "F1 FM", "F1 Drive", "F1 Pan", "F2 Cutoff", "F2 Reson.",
             "F2 FM", "F2 Drive", "F2 Pan", "Volume", "LFO1Speed", "LFO2Speed", "LFO3Speed",
             "FE Attack", "FE Decay", "FE Sustain", "FE Release", "AE Attack", "AE Decay",
             "AE Sustain", "AE Release", "E3 Attack", "E3 Decay", "E3 Sustain", "E3 Release",
             "E4 Attack", "E4 Decay", "E4 Sustain", "E4 Release", "M1 Amount", "M2 Amount",
             "M3 Amount", "M4 Amount"]

MODIFIER_OPS = ["+", "-", "*", "AND", "OR", "XOR", "MAX", "min"]

DRIVE_CURVES = ["Clipping", "Tube", "Hard", "Medium", "Soft", "Pickup 1", "Pickup 2",
                "Rectifier", "Square", "Binary", "Overflow", "Sine Shaper", "Osc 1 Mod"]

ENV_MODES = ["ADSR", "ADS1DS2R", "One Shot", "Loop S1S2", "Loop All"]
ENV_TRIGGERS = ["normal", "single"]

ARP_CLOCKS = ["1/96", "1/48", "1/32", "1/16T", "1/32.", "1/16", "1/8T", "1/16.", "1/8",
              "1/4T", "1/8.", "1/4", "1/2T", "1/4.", "1/2", "1/1T", "1/2.", "1 bar",
              "1.5 bars", "2 bars", "2.5 bars", "3 bars", "3.5 bars", "4 bars", "5 bars",
              "6 bars", "7 bars", "8 bars", "9 bars", "10 bars", "12 bars", "14 bars",
              "16 bars", "18 bars", "20 bars", "24 bars", "28 bars", "32 bars", "36 bars",
              "40 bars", "48 bars", "56 bars", "64 bars"]

ARP_SORT = ["as played", "reversed", "Key Lo>Hi", "Key Hi>Lo", "Vel Lo>Hi", "Vel Hi>Lo"]
ARP_VEL = ["Each Note", "First Note", "Last Note", "fix 32", "fix 64", "fix 100", "fix 127"]

CATEGORIES = ["Init", "Arp", "Atmo", "Bass", "Drum", "FX", "Keys", "Lead", "Mono", "Pad",
              "Perc", "Poly", "Seq"]

CTRL_SEND = ["off", "Ctrl", "SysEx", "Ctrl+SysEx"]

FX_TYPES = ["Bypass", "Chorus", "Flanger", "Phaser", "Overdrive", "Triple FX",
            "Delay", "Clk.Delay", "Reverb"]

# LFO-Clocks (4.6): Index-Paare -> Name
LFO_CLOCKS = {}
_lfo_bars = ["1280", "1152", "1024", "896", "768", "640", "576", "512", "448", "384",
             "320", "288", "256", "224", "192", "160", "144", "128", "112", "96", "80",
             "72", "64", "56", "48", "40", "36", "32", "28", "24", "20", "18", "16",
             "14", "12", "10", "9", "8", "7", "6", "5", "4", "3.5", "3", "2.5", "2",
             "1.5", "1", "1/1T", "1/2", "1/4.", "1/2T", "1/4", "1/8.", "1/4T", "1/8",
             "1/16.", "1/8T", "1/16", "1/32.", "1/16T", "1/32", "1/48"]
for _i, _b in enumerate(_lfo_bars):
    LFO_CLOCKS[2 * _i] = f"{_b} bars"
    LFO_CLOCKS[2 * _i + 1] = f"{_b} bars"

# ---- SDATA-Tabelle (Spec 3.1): index -> (name, value_table) ------------------
# value_table: None = Rohwert, sonst Name der Tabelle oben
SDATA = {}

def _add(idx, name, table=None):
    SDATA[idx] = (name, table)

# Osc 1 (0..16), Osc 2 (17..32), Osc 3 (33..48)
_osc_names = ["Octave", "Semitone", "Detune", "Bend Range", "Keytrack", "FM Source",
              "FM Amount", "Shape", "Pulsewidth", "PWM Source", "PWM Amount", None, None,
              "Limit WT", None, "Brilliance"]
for _o in range(3):
    for _k, _n in enumerate(_osc_names):
        if _n is None:
            continue
        _t = None
        if _n == "FM Source":
            _t = FM_SOURCES
        elif _n == "PWM Source" or _n == "Osc Pitch Source":
            _t = MOD_SOURCES
        elif _n == "Shape":
            _t = SHAPES
        _add(_o * 16 + 1 + _k, f"Osc {_o + 1} {_n}", _t)  # Spec: Index 0 reserved, ab 1 Octave
# Korrekturen laut Spec: Osc3 Shape nur 0..4; Indizes 12,13,15 reserved -> SDATA oben
# hat 12/13/15 als reserved markiert (None) – passt.
_add(49, "Osc 2 Sync to O3")
_add(50, "Osc Pitch Source", MOD_SOURCES)
_add(51, "Osc Pitch Amount")
_add(53, "Glide")
_add(56, "Glide Mode", GLIDE_MODES)
_add(57, "Glide Rate")
_add(58, "Allocation/Unisono")   # 0uuu000a
_add(59, "Unisono Detune")
# Mixer 61..72
_add(61, "Mixer Osc 1 Level"); _add(62, "Mixer Osc 1 Balance")
_add(63, "Mixer Osc 2 Level"); _add(64, "Mixer Osc 2 Balance")
_add(65, "Mixer Osc 3 Level"); _add(66, "Mixer Osc 3 Balance")
_add(67, "Mixer Noise Level"); _add(68, "Mixer Noise Balance")
_add(69, "Mixer Noise Colour")
_add(71, "Mixer RingMod Level"); _add(72, "Mixer RingMod Balance")
# Filter 1: 77..95, Filter 2: 97..115, Routing 117
for _f in (1, 2):
    _b = 77 if _f == 1 else 97
    _add(_b + 0, f"Filter {_f} Type", FILTER_TYPES)
    _add(_b + 1, f"Filter {_f} Cutoff")
    _add(_b + 3, f"Filter {_f} Resonance")
    _add(_b + 4, f"Filter {_f} Drive")
    _add(_b + 5, f"Filter {_f} Drive Curve", DRIVE_CURVES)
    _add(_b + 9, f"Filter {_f} Keytrack")
    _add(_b + 10, f"Filter {_f} Env Amount")
    _add(_b + 11, f"Filter {_f} Env Velocity")
    _add(_b + 12, f"Filter {_f} Mod Source", MOD_SOURCES)
    _add(_b + 13, f"Filter {_f} Mod Amount")
    _add(_b + 14, f"Filter {_f} FM Source", FM_SOURCES)
    _add(_b + 15, f"Filter {_f} FM Amount")
    _add(_b + 16, f"Filter {_f} Pan")
    _add(_b + 17, f"Filter {_f} Pan Source", MOD_SOURCES)
    _add(_b + 18, f"Filter {_f} Pan Amount")
_add(117, "Filter Routing")      # 0..1 parallel,serial
# Amplifier 121..124
_add(121, "Amplifier Volume")
_add(122, "Amplifier Velocity")
_add(123, "Amplifier Mod Source", MOD_SOURCES)
_add(124, "Amplifier Mod Amount")
# FX 128..159
for _f in (1, 2):
    _b = 128 if _f == 1 else 144
    _add(_b, f"Effect {_f} Type", FX_TYPES)
    _add(_b + 1, f"Effect {_f} Mix")
    for _p in range(2, 16):
        _add(_b + _p, f"Effect {_f} Parameter {_p - 1}")
# LFOs 160..194
for _l in (1, 2, 3):
    _b = [160, 172, 184][_l - 1]  # LFO-Bloecke laut Spec
    _add(_b, f"LFO {_l} Shape", LFO_SHAPES)
    _add(_b + 1, f"LFO {_l} Speed", LFO_CLOCKS)
    _add(_b + 3, f"LFO {_l} Sync")
    _add(_b + 4, f"LFO {_l} Clocked")
    _add(_b + 5, f"LFO {_l} Start Phase")
    _add(_b + 6, f"LFO {_l} Delay")
    _add(_b + 7, f"LFO {_l} Fade")
    _add(_b + 10, f"LFO {_l} Keytrack")
# Envelopes 196..241
_env = [("Filter Envelope", 196), ("Amplifier Envelope", 208), ("Envelope 3", 220), ("Envelope 4", 232)]
for _n, _b in _env:
    _add(_b, f"{_n} Mode")      # 0ttmmmmm
    _add(_b + 3, f"{_n} Attack")
    _add(_b + 4, f"{_n} Attack Level")
    _add(_b + 5, f"{_n} Decay")
    _add(_b + 6, f"{_n} Sustain")
    _add(_b + 7, f"{_n} Decay 2")
    _add(_b + 8, f"{_n} Sustain 2")
    _add(_b + 9, f"{_n} Release")
# Modifier 245..260
for _m in range(1, 5):
    _b = 245 + (_m - 1) * 4
    _add(_b, f"Modifier {_m} Source A", MOD_SOURCES)
    _add(_b + 1, f"Modifier {_m} Source B", MOD_SOURCES)
    _add(_b + 2, f"Modifier {_m} Operation", MODIFIER_OPS)
    _add(_b + 3, f"Modifier {_m} Constant")
# Modulation 261..308 (16 Slots à 3)
for _m in range(1, 17):
    _b = 261 + (_m - 1) * 3
    _add(_b, f"Modulation {_m} Source", MOD_SOURCES)
    _add(_b + 1, f"Modulation {_m} Destination", MOD_DESTS)
    _add(_b + 2, f"Modulation {_m} Amount")
# Arp 311..358
_add(311, "Arpeggiator Mode")
_add(312, "Arpeggiator Pattern")
_add(314, "Arpeggiator Clock", ARP_CLOCKS)
_add(315, "Arpeggiator Length")
_add(316, "Arpeggiator Octave")
_add(317, "Arpeggiator Direction")
_add(318, "Arpeggiator Sort Order", ARP_SORT)
_add(319, "Arpeggiator Velocity", ARP_VEL)
_add(320, "Arpeggiator Timing Factor")
_add(322, "Arpeggiator Ptn Reset")
_add(323, "Arpeggiator Ptn Length")
_add(326, "Arpeggiator Tempo")
for _s in range(1, 17):
    _add(326 + _s, f"Arp Pattern Step/Glide/Accent {_s}")
for _s in range(1, 17):
    _add(342 + _s, f"Arp Pattern Timing/Length {_s}")
# Name 363..378 (16 ASCII), Category 379
_add(379, "Category", CATEGORIES)

SDATA_SIZE = 383  # Indizes 0..382


def checksum(sdata: bytes) -> int:
    """CHK = Summe der SDATA-Bytes & 0x7F (Spec: Status/IDs nicht mitgerechnet)."""
    return sum(sdata) & 0x7F


def build_sndd(sdata: bytes, bb: int = 0x7F, nn: int = 0x00, device: int = 0) -> list[int]:
    """Komplette SNDD-SysEx-Datenbytes fuer mido (ohne F0/F7)."""
    assert len(sdata) == SDATA_SIZE, f"SDATA muss {SDATA_SIZE} Bytes haben, hat {len(sdata)}"
    body = [0x3E, 0x13, device & 0x7F, 0x10, bb & 0x7F, nn & 0x7F] + [b & 0x7F for b in sdata]
    return body + [checksum(sdata)]


def parse_sndd(data: bytes) -> dict:
    """Komplette SysEx-Nachricht (mit F0/F7) oder mido-Daten (ohne F0/F7) parsen.

    Rückgabe: {"bb", "nn", "sdata", "chk", "chk_ok", "params": {name: value-or-label}}
    """
    d = list(data)
    if d and d[0] == 0xF0:
        d = d[1:]
    if d and d[-1] == 0xF7:
        d = d[:-1]
    # d = [3E, 13, DEV, 10, BB, NN, SDATA..., CHK]
    if len(d) < 8 or d[0] != 0x3E or d[1] != 0x13 or d[3] != 0x10:
        raise ValueError(f"keine SNDD-Nachricht: {bytes(d[:8]).hex(' ')}")
    bb, nn = d[4], d[5]
    sdata = bytes(d[6:-1])
    chk = d[-1]
    params = {}
    for idx, (name, table) in SDATA.items():
        if idx >= len(sdata):
            break
        v = sdata[idx]
        if idx in range(363, 379):  # Name-Chars
            continue
        if table is not None and v < len(table):
            params[name] = table[v]
        else:
            params[name] = v
    name = bytes(sdata[363:379]).decode("ascii", "replace").rstrip()
    return {"bb": bb, "nn": nn, "sdata": sdata, "chk": chk,
            "chk_ok": chk == checksum(sdata), "name": name, "params": params}


def build_sndp(param_index: int, value: int, ll: int = 0x00, device: int = 0) -> list[int]:
    """SNDP (Sound Parameter Change): F0 3E 13 DEV 20 LL HH PP XX F7 (ohne F0/F7)."""
    hh, pp = (param_index >> 7) & 0x7F, param_index & 0x7F
    return [0x3E, 0x13, device & 0x7F, 0x20, ll & 0x7F, hh, pp, value & 0x7F]


def build_sndr(bb: int = 0x7F, nn: int = 0x00, device: int = 0) -> list[int]:
    """SNDR (Sound Request): F0 3E 13 DEV 00 BB NN F7 (ohne F0/F7; Checksum weglassen)."""
    return [0x3E, 0x13, device & 0x7F, 0x00, bb & 0x7F, nn & 0x7F]
