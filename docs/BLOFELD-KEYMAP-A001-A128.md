# Blofeld keymap analysis A001-A128 (usage statistics + CC keymap proposal)

Created: 2026-11-10. Basis: all 128 factory sounds of bank A, read live via USB-MIDI
(port `Blofeld`, channel 5 / 0-based 4) as SNDR->SNDD and saved to
`dumps/banks/A/blofeld_sndd_Axxx_<ts>.bin` (chk_ok on all).
Raw data: `docs/midi-maps/blofeld_cc_usage_A001-A128.csv`.

## 1. Methodology

- **Data basis**: 128 SNDD dumps A001-A128 (each 392 B incl. F0/F7, 383 B SDATA, 290 named parameters per spec 3.1 / `bloridium/blofeld_dump.py`).
- **Init reference**: `dumps/blofeld_sndd_init_20261108_212711.bin` (chk_ok=True, name "Init") – valid init sound dump; used as default/reference.
- **"Used"**: raw value (SDATA byte 0..127) deviates from the init value. Enums are compared as raw index (label irrelevant).
- **Per parameter**: count (sounds with deviation), share = count/128 in %, min/max of the deviating raw values.
- **Categories** (by parameter type): Waveform (Osc N Shape), Mixer = Osc Volume (Mixer Osc N Level/Balance, Noise, RingMod), Tuning (Octave/Semitone/Detune/Bend Range/Pitch), Filter (F1/F2 + Routing), Env1 = Filter Envelope, Env2 = Amp Envelope, Env3/Env4, LFO, Mod-Matrix (Modulation+Modifier), Glide, FX (Effect 1/2), Arp, Amp (Amplifier), Unisono, plus `Osc (FM/PWM)` (FM/PWM/Pulsewidth/Brilliance/Sync) and Meta (Category).
- **Weighting** (requirement): ESSENTIAL k=3 = Waveform, Mixer (Osc Volume), Tuning, Filter, Env1, Env2. Medium k=2 = Env3, Env4, LFO, Mod-Matrix, Glide, Amp, Unisono. Rest k=1 = Osc (FM/PWM), FX, Arp, Meta.
- **Score** = share (0..1) x category_weight (0..3). Ranking = score descending.

## 2. Category overview

| Category | Weight | #Params | Params used (count>0) | mean share % |
|---|---|---|---|---|
| Env1 | 3 | 8 | 8 | 46.4 |
| Env2 | 3 | 8 | 8 | 43.6 |
| Filter | 3 | 31 | 31 | 42.3 |
| Mixer | 3 | 11 | 11 | 30.9 |
| Tuning | 3 | 14 | 14 | 34.3 |
| Waveform | 3 | 3 | 3 | 81.2 |
| Amp | 2 | 4 | 4 | 38.5 |
| Env3 | 2 | 8 | 8 | 30.4 |
| Env4 | 2 | 8 | 8 | 24.4 |
| Glide | 2 | 3 | 3 | 19.0 |
| LFO | 2 | 24 | 24 | 16.8 |
| Mod-Matrix | 2 | 64 | 64 | 29.5 |
| Unisono | 2 | 2 | 2 | 45.3 |
| Arp | 1 | 44 | 44 | 9.0 |
| FX | 1 | 32 | 32 | 37.4 |
| Meta | 1 | 1 | 1 | 93.0 |
| Osc (FM/PWM) | 1 | 25 | 24 | 22.7 |

## 3. Usage table per parameter (all 290, sorted by score)

| # | Parameter | Category | Weight | count | Share % | min-max (raw) | Score |
|---|---|---|---|---|---|---|---|
| 1 | Filter 1 Cutoff | Filter | 3 | 120 | 93.8 | 0-114 | 2.812 |
| 2 | Osc 2 Shape | Waveform | 3 | 117 | 91.4 | 1-71 | 2.742 |
| 3 | Osc 3 Shape | Waveform | 3 | 108 | 84.4 | 1-4 (Pulse, Saw, Triangle, Sine) | 2.531 |
| 4 | Filter Envelope Decay | Env1 | 3 | 106 | 82.8 | 1-127 | 2.484 |
| 5 | Filter 1 Resonance | Filter | 3 | 101 | 78.9 | 1-127 | 2.367 |
| 6 | Filter 2 Cutoff | Filter | 3 | 100 | 78.1 | 0-126 | 2.344 |
| 7 | Filter 2 Type | Filter | 3 | 100 | 78.1 | 1-11 | 2.344 |
| 8 | Amplifier Envelope Release | Env2 | 3 | 98 | 76.6 | 1-102 | 2.297 |
| 9 | Filter Envelope Release | Env1 | 3 | 97 | 75.8 | 3-127 | 2.273 |
| 10 | Filter 1 Env Amount | Filter | 3 | 92 | 71.9 | 0-127 | 2.156 |
| 11 | Osc 1 Shape | Waveform | 3 | 87 | 68.0 | 0-68 | 2.039 |
| 12 | Amplifier Envelope Decay | Env2 | 3 | 86 | 67.2 | 0-127 | 2.016 |
| 13 | Filter 1 Keytrack | Filter | 3 | 77 | 60.2 | 27-112 | 1.805 |
| 14 | Filter 2 Resonance | Filter | 3 | 75 | 58.6 | 1-127 | 1.758 |
| 15 | Filter Envelope Sustain | Env1 | 3 | 75 | 58.6 | 1-127 | 1.758 |
| 16 | Amplifier Envelope Sustain | Env2 | 3 | 74 | 57.8 | 0-122 | 1.734 |
| 17 | Filter 1 Drive | Filter | 3 | 72 | 56.2 | 6-108 | 1.688 |
| 18 | Modulation 2 Source | Mod-Matrix | 2 | 106 | 82.8 | 1-30 | 1.656 |
| 19 | Modulation 1 Amount | Mod-Matrix | 2 | 105 | 82.0 | 0-127 | 1.641 |
| 20 | Osc 2 Detune | Tuning | 3 | 70 | 54.7 | 0-105 | 1.641 |
| 21 | Modulation 2 Destination | Mod-Matrix | 2 | 102 | 79.7 | 1-50 | 1.594 |
| 22 | Filter 1 Type | Filter | 3 | 68 | 53.1 | 0-11 | 1.594 |
| 23 | Osc 2 Octave | Tuning | 3 | 68 | 53.1 | 40-112 | 1.594 |
| 24 | Osc 1 Octave | Tuning | 3 | 67 | 52.3 | 16-112 | 1.570 |
| 25 | Mixer Osc 2 Level | Mixer | 3 | 66 | 51.6 | 0-126 | 1.547 |
| 26 | Amplifier Envelope Attack | Env2 | 3 | 65 | 50.8 | 1-101 | 1.523 |
| 27 | Filter 2 Keytrack | Filter | 3 | 65 | 50.8 | 36-127 | 1.523 |
| 28 | Osc 3 Octave | Tuning | 3 | 65 | 50.8 | 16-112 | 1.523 |
| 29 | Modulation 2 Amount | Mod-Matrix | 2 | 97 | 75.8 | 0-127 | 1.516 |
| 30 | Modulation 3 Source | Mod-Matrix | 2 | 97 | 75.8 | 1-26 | 1.516 |
| 31 | LFO 1 Speed | LFO | 2 | 96 | 75.0 | 4-127 | 1.500 |
| 32 | Mixer Osc 3 Level | Mixer | 3 | 63 | 49.2 | 0-126 | 1.477 |
| 33 | Filter Envelope Attack | Env1 | 3 | 62 | 48.4 | 2-126 | 1.453 |
| 34 | Modulation 1 Destination | Mod-Matrix | 2 | 92 | 71.9 | 0-50 | 1.438 |
| 35 | Filter 2 Env Amount | Filter | 3 | 61 | 47.7 | 0-127 | 1.430 |
| 36 | Amplifier Velocity | Amp | 2 | 90 | 70.3 | 58-127 | 1.406 |
| 37 | Modulation 3 Amount | Mod-Matrix | 2 | 90 | 70.3 | 5-126 | 1.406 |
| 38 | Osc 3 Detune | Tuning | 3 | 59 | 46.1 | 0-95 | 1.383 |
| 39 | Modulation 3 Destination | Mod-Matrix | 2 | 88 | 68.8 | 1-41 | 1.375 |
| 40 | Osc 1 Detune | Tuning | 3 | 58 | 45.3 | 0-127 | 1.359 |
| 41 | Modulation 1 Source | Mod-Matrix | 2 | 84 | 65.6 | 0-30 | 1.312 |
| 42 | Filter 1 Mod Source | Filter | 3 | 56 | 43.8 | 0-25 | 1.312 |
| 43 | Filter Envelope Decay 2 | Env1 | 3 | 55 | 43.0 | 9-127 | 1.289 |
| 44 | LFO 2 Speed | LFO | 2 | 81 | 63.3 | 0-122 | 1.266 |
| 45 | Filter 2 Pan Source | Filter | 3 | 54 | 42.2 | 0-24 | 1.266 |
| 46 | Filter 1 Drive Curve | Filter | 3 | 52 | 40.6 | 1-12 | 1.219 |
| 47 | Filter 1 Mod Amount | Filter | 3 | 50 | 39.1 | 7-127 | 1.172 |
| 48 | Mixer Osc 2 Balance | Mixer | 3 | 50 | 39.1 | 1-127 | 1.172 |
| 49 | Modulation 4 Source | Mod-Matrix | 2 | 74 | 57.8 | 1-25 | 1.156 |
| 50 | Filter 1 Env Velocity | Filter | 3 | 49 | 38.3 | 23-125 | 1.148 |
| 51 | Amplifier Envelope Sustain 2 | Env2 | 3 | 47 | 36.7 | 0-112 | 1.102 |
| 52 | Filter 1 Pan | Filter | 3 | 47 | 36.7 | 0-120 | 1.102 |
| 53 | Filter 2 Mod Source | Filter | 3 | 47 | 36.7 | 1-26 | 1.102 |
| 54 | Mixer Osc 3 Balance | Mixer | 3 | 47 | 36.7 | 1-127 | 1.102 |
| 55 | LFO 3 Speed | LFO | 2 | 70 | 54.7 | 0-127 | 1.094 |
| 56 | Modulation 4 Destination | Mod-Matrix | 2 | 68 | 53.1 | 1-43 | 1.062 |
| 57 | Mixer Osc 1 Level | Mixer | 3 | 45 | 35.2 | 0-126 | 1.055 |
| 58 | Modulation 4 Amount | Mod-Matrix | 2 | 66 | 51.6 | 0-127 | 1.031 |
| 59 | Unisono Detune | Unisono | 2 | 66 | 51.6 | 1-45 | 1.031 |
| 60 | Filter 1 FM Source | Filter | 3 | 44 | 34.4 | 1-11 | 1.031 |
| 61 | Filter Routing | Filter | 3 | 44 | 34.4 | 1-1 | 1.031 |
| 62 | Osc Pitch Source | Tuning | 3 | 43 | 33.6 | 0-9 | 1.008 |
| 63 | Filter Envelope Sustain 2 | Env1 | 3 | 42 | 32.8 | 0-100 | 0.984 |
| 64 | Filter 2 Drive | Filter | 3 | 41 | 32.0 | 1-68 | 0.961 |
| 65 | Filter 2 Pan | Filter | 3 | 41 | 32.0 | 28-127 | 0.961 |
| 66 | Mixer Noise Balance | Mixer | 3 | 41 | 32.0 | 23-127 | 0.961 |
| 67 | Mixer RingMod Balance | Mixer | 3 | 41 | 32.0 | 10-127 | 0.961 |
| 68 | Category | Meta | 1 | 119 | 93.0 | 1-12 | 0.930 |
| 69 | Amplifier Envelope Decay 2 | Env2 | 3 | 39 | 30.5 | 12-116 | 0.914 |
| 70 | Envelope 3 Sustain | Env3 | 2 | 58 | 45.3 | 0-127 | 0.906 |
| 71 | Modulation 5 Destination | Mod-Matrix | 2 | 57 | 44.5 | 1-50 | 0.891 |
| 72 | Modulation 5 Source | Mod-Matrix | 2 | 57 | 44.5 | 1-27 | 0.891 |
| 73 | Amplifier Volume | Amp | 2 | 56 | 43.8 | 28-120 | 0.875 |
| 74 | Envelope 3 Attack Level | Env3 | 2 | 56 | 43.8 | 1-127 | 0.875 |
| 75 | Filter 2 Mod Amount | Filter | 3 | 37 | 28.9 | 8-127 | 0.867 |
| 76 | Envelope 3 Decay | Env3 | 2 | 54 | 42.2 | 0-127 | 0.844 |
| 77 | Filter 2 Env Velocity | Filter | 3 | 36 | 28.1 | 0-106 | 0.844 |
| 78 | Osc Pitch Amount | Tuning | 3 | 36 | 28.1 | 18-91 | 0.844 |
| 79 | Filter 2 Drive Curve | Filter | 3 | 35 | 27.3 | 1-11 | 0.820 |
| 80 | Modulation 5 Amount | Mod-Matrix | 2 | 51 | 39.8 | 7-127 | 0.797 |
| 81 | Osc 2 Semitone | Tuning | 3 | 34 | 26.6 | 52-76 | 0.797 |
| 82 | Effect 2 Mix | FX | 1 | 101 | 78.9 | 1-77 | 0.789 |
| 83 | Allocation/Unisono | Unisono | 2 | 50 | 39.1 | 1-81 | 0.781 |
| 84 | Modulation 6 Destination | Mod-Matrix | 2 | 50 | 39.1 | 4-43 | 0.781 |
| 85 | Modulation 6 Source | Mod-Matrix | 2 | 50 | 39.1 | 1-30 | 0.781 |
| 86 | Amplifier Mod Source | Amp | 2 | 49 | 38.3 | 0-12 | 0.766 |
| 87 | Modulation 9 Amount | Mod-Matrix | 2 | 49 | 38.3 | 3-125 | 0.766 |
| 88 | Modulation 6 Amount | Mod-Matrix | 2 | 47 | 36.7 | 1-127 | 0.734 |
| 89 | Modulation 9 Source | Mod-Matrix | 2 | 47 | 36.7 | 1-25 | 0.734 |
| 90 | Effect 1 Mix | FX | 1 | 93 | 72.7 | 3-127 | 0.727 |
| 91 | Modulation 9 Destination | Mod-Matrix | 2 | 46 | 35.9 | 1-50 | 0.719 |
| 92 | Mixer Osc 1 Balance | Mixer | 3 | 30 | 23.4 | 2-127 | 0.703 |
| 93 | Osc 1 Bend Range | Tuning | 3 | 30 | 23.4 | 40-88 | 0.703 |
| 94 | Filter 1 Pan Amount | Filter | 3 | 29 | 22.7 | 0-127 | 0.680 |
| 95 | Osc 2 Bend Range | Tuning | 3 | 29 | 22.7 | 59-88 | 0.680 |
| 96 | Glide Rate | Glide | 2 | 43 | 33.6 | 0-102 | 0.672 |
| 97 | Modulation 10 Destination | Mod-Matrix | 2 | 43 | 33.6 | 2-53 | 0.672 |
| 98 | Modulation 10 Amount | Mod-Matrix | 2 | 42 | 32.8 | 0-127 | 0.656 |
| 99 | Envelope 3 Sustain 2 | Env3 | 2 | 41 | 32.0 | 0-127 | 0.641 |
| 100 | Envelope 4 Attack Level | Env4 | 2 | 41 | 32.0 | 0-127 | 0.641 |
| 101 | Envelope 4 Sustain 2 | Env4 | 2 | 41 | 32.0 | 0-127 | 0.641 |
| 102 | Modulation 10 Source | Mod-Matrix | 2 | 41 | 32.0 | 4-27 | 0.641 |
| 103 | Filter 2 Pan Amount | Filter | 3 | 27 | 21.1 | 22-127 | 0.633 |
| 104 | Filter Envelope Attack Level | Env1 | 3 | 27 | 21.1 | 0-126 | 0.633 |
| 105 | Osc 1 Pulsewidth | Osc (FM/PWM) | 1 | 80 | 62.5 | 0-126 | 0.625 |
| 106 | Modulation 11 Destination | Mod-Matrix | 2 | 40 | 31.2 | 2-52 | 0.625 |
| 107 | Envelope 4 Decay | Env4 | 2 | 39 | 30.5 | 0-101 | 0.609 |
| 108 | Envelope 4 Sustain | Env4 | 2 | 39 | 30.5 | 0-127 | 0.609 |
| 109 | LFO 1 Shape | LFO | 2 | 39 | 30.5 | 1-5 (Triangle, Square, Saw, Random, S&H) | 0.609 |
| 110 | LFO 2 Shape | LFO | 2 | 39 | 30.5 | 1-5 (Triangle, Square, Saw, Random, S&H) | 0.609 |
| 111 | Modulation 7 Amount | Mod-Matrix | 2 | 39 | 30.5 | 13-127 | 0.609 |
| 112 | Modulation 7 Destination | Mod-Matrix | 2 | 39 | 30.5 | 1-41 | 0.609 |
| 113 | Amplifier Envelope Attack Level | Env2 | 3 | 26 | 20.3 | 0-112 | 0.609 |
| 114 | Modulation 7 Source | Mod-Matrix | 2 | 38 | 29.7 | 1-25 | 0.594 |
| 115 | Effect 2 Type | FX | 1 | 75 | 58.6 | 0-7 | 0.586 |
| 116 | Osc 3 Bend Range | Tuning | 3 | 25 | 19.5 | 52-88 | 0.586 |
| 117 | Envelope 3 Attack | Env3 | 2 | 37 | 28.9 | 2-127 | 0.578 |
| 118 | Modulation 8 Amount | Mod-Matrix | 2 | 37 | 28.9 | 0-125 | 0.578 |
| 119 | Osc 2 Pulsewidth | Osc (FM/PWM) | 1 | 72 | 56.2 | 0-124 | 0.562 |
| 120 | Modulation 11 Amount | Mod-Matrix | 2 | 36 | 28.1 | 0-119 | 0.562 |
| 121 | Effect 2 Parameter 1 | FX | 1 | 70 | 54.7 | 0-127 | 0.547 |
| 122 | Modulation 8 Source | Mod-Matrix | 2 | 35 | 27.3 | 1-26 | 0.547 |
| 123 | Modulation 8 Destination | Mod-Matrix | 2 | 34 | 26.6 | 2-55 | 0.531 |
| 124 | Effect 2 Parameter 9 | FX | 1 | 66 | 51.6 | 0-127 | 0.516 |
| 125 | Envelope 4 Attack | Env4 | 2 | 33 | 25.8 | 14-127 | 0.516 |
| 126 | LFO 3 Shape | LFO | 2 | 33 | 25.8 | 1-5 (Triangle, Square, Saw, Random, S&H) | 0.516 |
| 127 | Filter 2 FM Source | Filter | 3 | 22 | 17.2 | 1-8 | 0.516 |
| 128 | Modulation 11 Source | Mod-Matrix | 2 | 32 | 25.0 | 1-30 | 0.500 |
| 129 | Effect 2 Parameter 11 | FX | 1 | 63 | 49.2 | 3-127 | 0.492 |
| 130 | Mixer RingMod Level | Mixer | 3 | 21 | 16.4 | 11-127 | 0.492 |
| 131 | Effect 2 Parameter 6 | FX | 1 | 62 | 48.4 | 0-127 | 0.484 |
| 132 | Modulation 12 Destination | Mod-Matrix | 2 | 31 | 24.2 | 1-53 | 0.484 |
| 133 | Effect 1 Parameter 2 | FX | 1 | 61 | 47.7 | 15-127 | 0.477 |
| 134 | Envelope 3 Decay 2 | Env3 | 2 | 30 | 23.4 | 0-127 | 0.469 |
| 135 | Envelope 4 Decay 2 | Env4 | 2 | 30 | 23.4 | 0-126 | 0.469 |
| 136 | Effect 1 Parameter 1 | FX | 1 | 59 | 46.1 | 0-127 | 0.461 |
| 137 | Arpeggiator Pattern | Arp | 1 | 58 | 45.3 | 1-1 | 0.453 |
| 138 | Effect 2 Parameter 5 | FX | 1 | 58 | 45.3 | 0-100 | 0.453 |
| 139 | Arpeggiator Ptn Reset | Arp | 1 | 57 | 44.5 | 1-1 | 0.445 |
| 140 | Effect 2 Parameter 2 | FX | 1 | 57 | 44.5 | 0-127 | 0.445 |
| 141 | Effect 2 Parameter 3 | FX | 1 | 57 | 44.5 | 0-115 | 0.445 |
| 142 | Osc 3 Pulsewidth | Osc (FM/PWM) | 1 | 57 | 44.5 | 0-120 | 0.445 |
| 143 | Osc 3 Semitone | Tuning | 3 | 19 | 14.8 | 52-76 | 0.445 |
| 144 | Effect 2 Parameter 4 | FX | 1 | 55 | 43.0 | 4-127 | 0.430 |
| 145 | Effect 2 Parameter 8 | FX | 1 | 54 | 42.2 | 0-127 | 0.422 |
| 146 | Envelope 3 Release | Env3 | 2 | 27 | 21.1 | 0-119 | 0.422 |
| 147 | Mixer Noise Colour | Mixer | 3 | 18 | 14.1 | 0-127 | 0.422 |
| 148 | Effect 2 Parameter 10 | FX | 1 | 53 | 41.4 | 1-127 | 0.414 |
| 149 | Osc 2 PWM Amount | Osc (FM/PWM) | 1 | 52 | 40.6 | 0-127 | 0.406 |
| 150 | Glide | Glide | 2 | 26 | 20.3 | 1-1 | 0.406 |
| 151 | Arpeggiator Clock | Arp | 1 | 50 | 39.1 | 5-10 (1/16, 1/8T, 1/16., 1/8, 1/4T, 1/8.) | 0.391 |
| 152 | Arpeggiator Length | Arp | 1 | 50 | 39.1 | 2-8 | 0.391 |
| 153 | Effect 1 Parameter 9 | FX | 1 | 50 | 39.1 | 0-90 | 0.391 |
| 154 | Effect 2 Parameter 7 | FX | 1 | 50 | 39.1 | 6-127 | 0.391 |
| 155 | Osc 1 FM Source | Osc (FM/PWM) | 1 | 49 | 38.3 | 1-11 | 0.383 |
| 156 | Modulation 12 Amount | Mod-Matrix | 2 | 24 | 18.8 | 0-126 | 0.375 |
| 157 | Filter 1 Pan Source | Filter | 3 | 16 | 12.5 | 0-7 | 0.375 |
| 158 | Effect 1 Parameter 6 | FX | 1 | 47 | 36.7 | 0-124 | 0.367 |
| 159 | Osc 2 FM Source | Osc (FM/PWM) | 1 | 46 | 35.9 | 1-11 | 0.359 |
| 160 | Modulation 14 Destination | Mod-Matrix | 2 | 23 | 18.0 | 1-51 | 0.359 |
| 161 | Effect 1 Parameter 10 | FX | 1 | 45 | 35.2 | 0-64 | 0.352 |
| 162 | Osc 1 PWM Amount | Osc (FM/PWM) | 1 | 45 | 35.2 | 0-127 | 0.352 |
| 163 | Effect 1 Parameter 5 | FX | 1 | 44 | 34.4 | 0-109 | 0.344 |
| 164 | Envelope 4 Release | Env4 | 2 | 22 | 17.2 | 0-113 | 0.344 |
| 165 | Modifier 1 Source A | Mod-Matrix | 2 | 22 | 17.2 | 1-12 | 0.344 |
| 166 | Modulation 14 Amount | Mod-Matrix | 2 | 22 | 17.2 | 10-127 | 0.344 |
| 167 | Modulation 15 Destination | Mod-Matrix | 2 | 22 | 17.2 | 3-38 | 0.344 |
| 168 | Modulation 12 Source | Mod-Matrix | 2 | 21 | 16.4 | 3-25 | 0.328 |
| 169 | Modulation 13 Destination | Mod-Matrix | 2 | 21 | 16.4 | 2-53 | 0.328 |
| 170 | Modulation 15 Amount | Mod-Matrix | 2 | 21 | 16.4 | 15-127 | 0.328 |
| 171 | Modulation 15 Source | Mod-Matrix | 2 | 21 | 16.4 | 1-30 | 0.328 |
| 172 | Effect 1 Parameter 7 | FX | 1 | 41 | 32.0 | 0-123 | 0.320 |
| 173 | Osc 3 FM Source | Osc (FM/PWM) | 1 | 41 | 32.0 | 1-11 | 0.320 |
| 174 | Effect 1 Parameter 8 | FX | 1 | 40 | 31.2 | 0-100 | 0.312 |
| 175 | Modifier 1 Operation | Mod-Matrix | 2 | 20 | 15.6 | 2-7 (*, AND, OR, XOR, MAX, min) | 0.312 |
| 176 | Modifier 1 Source B | Mod-Matrix | 2 | 20 | 15.6 | 1-30 | 0.312 |
| 177 | Modulation 13 Amount | Mod-Matrix | 2 | 20 | 15.6 | 14-127 | 0.312 |
| 178 | Modulation 14 Source | Mod-Matrix | 2 | 20 | 15.6 | 3-27 | 0.312 |
| 179 | Mixer Noise Level | Mixer | 3 | 13 | 10.2 | 9-71 | 0.305 |
| 180 | Arpeggiator Tempo | Arp | 1 | 38 | 29.7 | 32-91 | 0.297 |
| 181 | LFO 1 Sync | LFO | 2 | 19 | 14.8 | 1-1 | 0.297 |
| 182 | Modulation 16 Source | Mod-Matrix | 2 | 19 | 14.8 | 1-26 | 0.297 |
| 183 | LFO 3 Keytrack | LFO | 2 | 18 | 14.1 | 68-100 | 0.281 |
| 184 | Modulation 16 Destination | Mod-Matrix | 2 | 18 | 14.1 | 1-51 | 0.281 |
| 185 | Filter 1 FM Amount | Filter | 3 | 12 | 9.4 | 1-106 | 0.281 |
| 186 | Osc 1 PWM Source | Osc (FM/PWM) | 1 | 34 | 26.6 | 0-13 | 0.266 |
| 187 | Modulation 13 Source | Mod-Matrix | 2 | 17 | 13.3 | 2-16 | 0.266 |
| 188 | Amplifier Envelope Mode | Env2 | 3 | 11 | 8.6 | 1-33 | 0.258 |
| 189 | Filter Envelope Mode | Env1 | 3 | 11 | 8.6 | 1-33 | 0.258 |
| 190 | Osc 1 Semitone | Tuning | 3 | 11 | 8.6 | 52-76 | 0.258 |
| 191 | Osc 3 PWM Amount | Osc (FM/PWM) | 1 | 32 | 25.0 | 10-119 | 0.250 |
| 192 | Osc 3 PWM Source | Osc (FM/PWM) | 1 | 30 | 23.4 | 0-13 | 0.234 |
| 193 | LFO 1 Keytrack | LFO | 2 | 15 | 11.7 | 0-104 | 0.234 |
| 194 | Effect 1 Type | FX | 1 | 29 | 22.7 | 0-5 (Bypass, Chorus, Flanger, Phaser, Overdrive, Triple FX) | 0.227 |
| 195 | Osc 2 FM Amount | Osc (FM/PWM) | 1 | 29 | 22.7 | 1-127 | 0.227 |
| 196 | Arpeggiator Octave | Arp | 1 | 27 | 21.1 | 1-9 | 0.211 |
| 197 | Effect 1 Parameter 11 | FX | 1 | 27 | 21.1 | 0-64 | 0.211 |
| 198 | Effect 1 Parameter 3 | FX | 1 | 27 | 21.1 | 0-127 | 0.211 |
| 199 | Osc 1 FM Amount | Osc (FM/PWM) | 1 | 27 | 21.1 | 1-127 | 0.211 |
| 200 | Effect 1 Parameter 4 | FX | 1 | 26 | 20.3 | 4-127 | 0.203 |
| 201 | Osc 2 PWM Source | Osc (FM/PWM) | 1 | 26 | 20.3 | 0-25 | 0.203 |
| 202 | Effect 2 Parameter 13 | FX | 1 | 24 | 18.8 | 0-64 | 0.188 |
| 203 | Effect 2 Parameter 14 | FX | 1 | 24 | 18.8 | 0-64 | 0.188 |
| 204 | LFO 1 Fade | LFO | 2 | 12 | 9.4 | 0-105 | 0.188 |
| 205 | Modifier 2 Source B | Mod-Matrix | 2 | 12 | 9.4 | 2-29 | 0.188 |
| 206 | Modulation 16 Amount | Mod-Matrix | 2 | 12 | 9.4 | 32-127 | 0.188 |
| 207 | Filter 2 FM Amount | Filter | 3 | 8 | 6.2 | 1-127 | 0.188 |
| 208 | Effect 1 Parameter 12 | FX | 1 | 23 | 18.0 | 0-64 | 0.180 |
| 209 | LFO 2 Keytrack | LFO | 2 | 11 | 8.6 | 66-100 | 0.172 |
| 210 | Modifier 2 Source A | Mod-Matrix | 2 | 11 | 8.6 | 1-25 | 0.172 |
| 211 | Effect 1 Parameter 13 | FX | 1 | 21 | 16.4 | 0-64 | 0.164 |
| 212 | Effect 1 Parameter 14 | FX | 1 | 21 | 16.4 | 0-64 | 0.164 |
| 213 | Osc 3 FM Amount | Osc (FM/PWM) | 1 | 20 | 15.6 | 2-127 | 0.156 |
| 214 | LFO 1 Start Phase | LFO | 2 | 10 | 7.8 | 1-93 | 0.156 |
| 215 | LFO 3 Sync | LFO | 2 | 10 | 7.8 | 1-1 | 0.156 |
| 216 | Osc 2 Sync to O3 | Osc (FM/PWM) | 1 | 19 | 14.8 | 1-1 | 0.148 |
| 217 | LFO 2 Start Phase | LFO | 2 | 9 | 7.0 | 1-99 | 0.141 |
| 218 | LFO 2 Sync | LFO | 2 | 9 | 7.0 | 1-1 | 0.141 |
| 219 | Modifier 1 Constant | Mod-Matrix | 2 | 9 | 7.0 | 50-127 | 0.141 |
| 220 | Osc 1 Brilliance | Osc (FM/PWM) | 1 | 17 | 13.3 | 7-127 | 0.133 |
| 221 | Envelope 3 Mode | Env3 | 2 | 8 | 6.2 | 1-34 | 0.125 |
| 222 | LFO 1 Delay | LFO | 2 | 8 | 6.2 | 2-38 | 0.125 |
| 223 | Modifier 2 Operation | Mod-Matrix | 2 | 8 | 6.2 | 1-7 | 0.125 |
| 224 | Arpeggiator Timing Factor | Arp | 1 | 15 | 11.7 | 0-127 | 0.117 |
| 225 | Arpeggiator Velocity | Arp | 1 | 15 | 11.7 | 0-2 (Each Note, First Note, Last Note) | 0.117 |
| 226 | Osc 2 Brilliance | Osc (FM/PWM) | 1 | 15 | 11.7 | 3-127 | 0.117 |
| 227 | Arp Pattern Timing/Length 16 | Arp | 1 | 14 | 10.9 | 36-84 | 0.109 |
| 228 | Arp Pattern Timing/Length 4 | Arp | 1 | 14 | 10.9 | 36-71 | 0.109 |
| 229 | LFO 3 Fade | LFO | 2 | 7 | 5.5 | 3-83 | 0.109 |
| 230 | LFO 3 Start Phase | LFO | 2 | 7 | 5.5 | 1-57 | 0.109 |
| 231 | Arp Pattern Timing/Length 10 | Arp | 1 | 13 | 10.2 | 36-71 | 0.102 |
| 232 | Arp Pattern Timing/Length 12 | Arp | 1 | 13 | 10.2 | 36-71 | 0.102 |
| 233 | Arp Pattern Timing/Length 14 | Arp | 1 | 13 | 10.2 | 36-71 | 0.102 |
| 234 | Arp Pattern Timing/Length 2 | Arp | 1 | 13 | 10.2 | 36-71 | 0.102 |
| 235 | Arp Pattern Timing/Length 6 | Arp | 1 | 13 | 10.2 | 36-71 | 0.102 |
| 236 | Arp Pattern Timing/Length 8 | Arp | 1 | 13 | 10.2 | 36-71 | 0.102 |
| 237 | LFO 1 Clocked | LFO | 2 | 6 | 4.7 | 1-1 | 0.094 |
| 238 | Osc 3 Brilliance | Osc (FM/PWM) | 1 | 10 | 7.8 | 1-127 | 0.078 |
| 239 | Envelope 4 Mode | Env4 | 2 | 5 | 3.9 | 1-64 | 0.078 |
| 240 | Arp Pattern Step/Glide/Accent 12 | Arp | 1 | 8 | 6.2 | 3-52 | 0.062 |
| 241 | Glide Mode | Glide | 2 | 4 | 3.1 | 1-3 (fingered P, Glissando, fingered G) | 0.062 |
| 242 | LFO 2 Clocked | LFO | 2 | 4 | 3.1 | 1-1 | 0.062 |
| 243 | LFO 2 Delay | LFO | 2 | 4 | 3.1 | 5-65 | 0.062 |
| 244 | LFO 3 Clocked | LFO | 2 | 4 | 3.1 | 1-1 | 0.062 |
| 245 | Modifier 3 Constant | Mod-Matrix | 2 | 4 | 3.1 | 0-127 | 0.062 |
| 246 | Modifier 3 Source A | Mod-Matrix | 2 | 4 | 3.1 | 1-30 | 0.062 |
| 247 | Modifier 3 Source B | Mod-Matrix | 2 | 4 | 3.1 | 1-10 | 0.062 |
| 248 | Arpeggiator Mode | Arp | 1 | 7 | 5.5 | 1-3 | 0.055 |
| 249 | Effect 2 Parameter 12 | FX | 1 | 7 | 5.5 | 0-127 | 0.055 |
| 250 | Osc 1 Limit WT | Osc (FM/PWM) | 1 | 7 | 5.5 | 1-1 | 0.055 |
| 251 | Osc 2 Keytrack | Osc (FM/PWM) | 1 | 6 | 4.7 | 64-127 | 0.047 |
| 252 | LFO 2 Fade | LFO | 2 | 3 | 2.3 | 12-88 | 0.047 |
| 253 | LFO 3 Delay | LFO | 2 | 3 | 2.3 | 3-54 | 0.047 |
| 254 | Modifier 3 Operation | Mod-Matrix | 2 | 3 | 2.3 | 2-4 (*, AND, OR) | 0.047 |
| 255 | Arp Pattern Step/Glide/Accent 3 | Arp | 1 | 5 | 3.9 | 2-116 | 0.039 |
| 256 | Arpeggiator Direction | Arp | 1 | 5 | 3.9 | 2-3 | 0.039 |
| 257 | Osc 3 Keytrack | Osc (FM/PWM) | 1 | 5 | 3.9 | 64-91 | 0.039 |
| 258 | Arp Pattern Step/Glide/Accent 14 | Arp | 1 | 4 | 3.1 | 3-20 | 0.031 |
| 259 | Arp Pattern Step/Glide/Accent 16 | Arp | 1 | 4 | 3.1 | 7-40 | 0.031 |
| 260 | Arp Pattern Step/Glide/Accent 6 | Arp | 1 | 4 | 3.1 | 7-116 | 0.031 |
| 261 | Arp Pattern Step/Glide/Accent 7 | Arp | 1 | 4 | 3.1 | 3-116 | 0.031 |
| 262 | Arp Pattern Step/Glide/Accent 8 | Arp | 1 | 4 | 3.1 | 3-36 | 0.031 |
| 263 | Arp Pattern Step/Glide/Accent 9 | Arp | 1 | 4 | 3.1 | 20-85 | 0.031 |
| 264 | Arp Pattern Timing/Length 1 | Arp | 1 | 4 | 3.1 | 36-112 | 0.031 |
| 265 | Arp Pattern Timing/Length 9 | Arp | 1 | 4 | 3.1 | 36-121 | 0.031 |
| 266 | Osc 2 Limit WT | Osc (FM/PWM) | 1 | 4 | 3.1 | 1-1 | 0.031 |
| 267 | Amplifier Mod Amount | Amp | 2 | 2 | 1.6 | 55-90 | 0.031 |
| 268 | Modifier 2 Constant | Mod-Matrix | 2 | 2 | 1.6 | 51-99 | 0.031 |
| 269 | Modifier 4 Constant | Mod-Matrix | 2 | 2 | 1.6 | 46-49 | 0.031 |
| 270 | Modifier 4 Operation | Mod-Matrix | 2 | 2 | 1.6 | 4-7 (OR, XOR, MAX, min) | 0.031 |
| 271 | Modifier 4 Source B | Mod-Matrix | 2 | 2 | 1.6 | 1-26 | 0.031 |
| 272 | Arp Pattern Step/Glide/Accent 10 | Arp | 1 | 3 | 2.3 | 6-36 | 0.023 |
| 273 | Arp Pattern Step/Glide/Accent 2 | Arp | 1 | 3 | 2.3 | 20-116 | 0.023 |
| 274 | Arp Pattern Step/Glide/Accent 4 | Arp | 1 | 3 | 2.3 | 12-36 | 0.023 |
| 275 | Arp Pattern Timing/Length 11 | Arp | 1 | 3 | 2.3 | 36-102 | 0.023 |
| 276 | Arp Pattern Timing/Length 5 | Arp | 1 | 3 | 2.3 | 36-84 | 0.023 |
| 277 | Osc 1 Keytrack | Osc (FM/PWM) | 1 | 3 | 2.3 | 0-64 | 0.023 |
| 278 | Arp Pattern Step/Glide/Accent 1 | Arp | 1 | 2 | 1.6 | 6-15 | 0.016 |
| 279 | Arp Pattern Step/Glide/Accent 11 | Arp | 1 | 2 | 1.6 | 20-20 | 0.016 |
| 280 | Arp Pattern Step/Glide/Accent 13 | Arp | 1 | 2 | 1.6 | 5-36 | 0.016 |
| 281 | Arp Pattern Step/Glide/Accent 5 | Arp | 1 | 2 | 1.6 | 20-20 | 0.016 |
| 282 | Arp Pattern Timing/Length 13 | Arp | 1 | 2 | 1.6 | 36-36 | 0.016 |
| 283 | Arp Pattern Timing/Length 15 | Arp | 1 | 2 | 1.6 | 36-36 | 0.016 |
| 284 | Arp Pattern Timing/Length 3 | Arp | 1 | 2 | 1.6 | 36-36 | 0.016 |
| 285 | Arp Pattern Timing/Length 7 | Arp | 1 | 2 | 1.6 | 36-36 | 0.016 |
| 286 | Arpeggiator Sort Order | Arp | 1 | 2 | 1.6 | 1-5 (reversed, Key Lo>Hi, Key Hi>Lo, Vel Lo>Hi, Vel Hi>Lo) | 0.016 |
| 287 | Modifier 4 Source A | Mod-Matrix | 2 | 1 | 0.8 | 2-2 | 0.016 |
| 288 | Arp Pattern Step/Glide/Accent 15 | Arp | 1 | 1 | 0.8 | 5-5 | 0.008 |
| 289 | Arpeggiator Ptn Length | Arp | 1 | 1 | 0.8 | 5-5 | 0.008 |
| 290 | Osc 3 Limit WT | Osc (FM/PWM) | 1 | 0 | 0.0 | - | 0.000 |

## 4. Ranking top 30

| Rank | Parameter | Category | Weight | Share % | Score | ESSENTIAL |
|---|---|---|---|---|---|---|
| 1 | Filter 1 Cutoff | Filter | 3 | 93.8 | 2.812 | **yes** |
| 2 | Osc 2 Shape | Waveform | 3 | 91.4 | 2.742 | **yes** |
| 3 | Osc 3 Shape | Waveform | 3 | 84.4 | 2.531 | **yes** |
| 4 | Filter Envelope Decay | Env1 | 3 | 82.8 | 2.484 | **yes** |
| 5 | Filter 1 Resonance | Filter | 3 | 78.9 | 2.367 | **yes** |
| 6 | Filter 2 Cutoff | Filter | 3 | 78.1 | 2.344 | **yes** |
| 7 | Filter 2 Type | Filter | 3 | 78.1 | 2.344 | **yes** |
| 8 | Amplifier Envelope Release | Env2 | 3 | 76.6 | 2.297 | **yes** |
| 9 | Filter Envelope Release | Env1 | 3 | 75.8 | 2.273 | **yes** |
| 10 | Filter 1 Env Amount | Filter | 3 | 71.9 | 2.156 | **yes** |
| 11 | Osc 1 Shape | Waveform | 3 | 68.0 | 2.039 | **yes** |
| 12 | Amplifier Envelope Decay | Env2 | 3 | 67.2 | 2.016 | **yes** |
| 13 | Filter 1 Keytrack | Filter | 3 | 60.2 | 1.805 | **yes** |
| 14 | Filter 2 Resonance | Filter | 3 | 58.6 | 1.758 | **yes** |
| 15 | Filter Envelope Sustain | Env1 | 3 | 58.6 | 1.758 | **yes** |
| 16 | Amplifier Envelope Sustain | Env2 | 3 | 57.8 | 1.734 | **yes** |
| 17 | Filter 1 Drive | Filter | 3 | 56.2 | 1.688 | **yes** |
| 18 | Modulation 2 Source | Mod-Matrix | 2 | 82.8 | 1.656 | no |
| 19 | Modulation 1 Amount | Mod-Matrix | 2 | 82.0 | 1.641 | no |
| 20 | Osc 2 Detune | Tuning | 3 | 54.7 | 1.641 | **yes** |
| 21 | Modulation 2 Destination | Mod-Matrix | 2 | 79.7 | 1.594 | no |
| 22 | Filter 1 Type | Filter | 3 | 53.1 | 1.594 | **yes** |
| 23 | Osc 2 Octave | Tuning | 3 | 53.1 | 1.594 | **yes** |
| 24 | Osc 1 Octave | Tuning | 3 | 52.3 | 1.570 | **yes** |
| 25 | Mixer Osc 2 Level | Mixer | 3 | 51.6 | 1.547 | **yes** |
| 26 | Amplifier Envelope Attack | Env2 | 3 | 50.8 | 1.523 | **yes** |
| 27 | Filter 2 Keytrack | Filter | 3 | 50.8 | 1.523 | **yes** |
| 28 | Osc 3 Octave | Tuning | 3 | 50.8 | 1.523 | **yes** |
| 29 | Modulation 2 Amount | Mod-Matrix | 2 | 75.8 | 1.516 | no |
| 30 | Modulation 3 Source | Mod-Matrix | 2 | 75.8 | 1.516 | no |

**Top 10 essential**: Filter 1 Cutoff (94%), Osc 2 Shape (91%), Osc 3 Shape (84%), Filter Envelope Decay (83%), Filter 1 Resonance (79%), Filter 2 Cutoff (78%), Filter 2 Type (78%), Amplifier Envelope Release (77%), Filter Envelope Release (76%), Filter 1 Env Amount (72%)

## 5. Filter Hapax keymap (Iridium L1 def -> Blofeld)

Template: `docs/midi-maps/iridium_hapax_L1.def.txt` ([CC] section). Entries that do
**not** exist on the Blofeld (Iridium-specific modules/parameters) are removed:
no compressor, no Digi Former, no Complex module, no Partial-Osc (PT), no WT-Stepped
option, no LFO/Free-Env amounts (only in the mod matrix), no ringmod pair routing, and
instead of separate Delay/Reverb/Chorus/Phaser/Flanger/Drive CC blocks only **FX1/FX2**
(type + mix CC93/94 + 14 parameters per slot, the latter only via SysEx).

| CC | Iridium parameter | Blofeld equivalent | verdict | Share % | Reason |
|---|---|---|---|---|---|
| 0 | Filter1 Cutoff | Filter 1 Cutoff | take over | 93.75 |  |
| 2 | Filter1 Reso | Filter 1 Resonance | take over | 78.90625 |  |
| 3 | Filter1 Attack | Filter Envelope Attack | take over | 48.4375 | Iridium Filter1-ADSR = Blofeld Filter Envelope (Env1) |
| 4 | Filter1 Decay | Filter Envelope Decay | take over | 82.8125 |  |
| 5 | Filter1 Sustain | Filter Envelope Sustain | take over | 58.59375 |  |
| 6 | Filter1 Release | Filter Envelope Release | take over | 75.78125 |  |
| 7 | Filter1 Amount | Filter 1 Env Amount | take over | 71.875 |  |
| 8 | Filter1 Velo Amount | Filter 1 Env Velocity | take over | 38.28125 |  |
| 9 | Filter2 Cutoff | Filter 2 Cutoff | take over | 78.125 |  |
| 10 | Filter2 Reso | Filter 2 Resonance | take over | 58.59375 |  |
| 11 | Filter2 Attack | Filter 2 Env -> Filter Envelope (gemeinsam) | take over | - | Blofeld hat EINE Filter-Envelope fuer F1+F2 |
| 12 | Filter2 Decay | Filter Envelope Decay | take over | 82.8125 | gemeinsame Filter-Envelope |
| 13 | Filter2 Sustain | Filter Envelope Sustain | take over | 58.59375 | gemeinsame Filter-Envelope |
| 14 | Filter2 Release | Filter Envelope Release | take over | 75.78125 | gemeinsame Filter-Envelope |
| 15 | Filter2 Amount | Filter 2 Env Amount | take over | 47.65625 |  |
| 16 | Filter2 Velo Amount | Filter 2 Env Velocity | take over | 28.125 |  |
| 17 | Amp Velo Amount | Amplifier Velocity | take over | 70.3125 |  |
| 18 | Amp Attack | Amplifier Envelope Attack | take over | 50.78125 | Iridium Amp-ADSR = Blofeld Amp Envelope (Env2) |
| 19 | Amp Decay | Amplifier Envelope Decay | take over | 67.1875 |  |
| 20 | Amp Sustain | Amplifier Envelope Sustain | take over | 57.8125 |  |
| 21 | Amp Release | Amplifier Envelope Release | take over | 76.5625 |  |
| 22 | Delay Dry Wet | Effect 1/2 Mix | drop | - | Blofeld: nur FX1/FX2 (Typ+Mix+14 Params), kein eigener Delay-CC-Block |
| 23 | Delay Feedback | - | drop | - | keine Einzel-CCs; nur per SysEx (Effect N Parameter) |
| 24 | Delay Time L | - | drop | - | s.o. |
| 25 | Delay Time R | - | drop | - | s.o. |
| 26 | Delay Sync L | - | drop | - | s.o. |
| 27 | Delay Sync R | - | drop | - | s.o. |
| 28 | Reverb Gain | - | drop | - | Blofeld FX-Typ Reverb ohne Einzel-CCs |
| 29 | Reverb Color | - | drop | - | s.o. |
| 30 | Reverb Time | - | drop | - | s.o. |
| 31 | Reverb Mod Depth | - | drop | - | s.o. |
| 32 | Osc1 Fine Pitch | Osc 1 Detune | take over | 45.3125 |  |
| 33 | Osc1 Vol | Mixer Osc 1 Level | take over | 35.15625 |  |
| 34 | Osc1 Pan | Filter 1 Pan | partial | 36.71875 | Blofeld hat kein Osc-Pan; naechstes: Filter-N-Pan (CC77/88) |
| 35 | Osc1 WT Position | Osc 1 Pulsewidth | partial | 62.5 | Blofeld PW/Wave = Wavetable-Position |
| 36 | Osc1 WT Spectrum | Osc 1 Brilliance | partial | 13.28125 | Naeherung; kein 1:1 |
| 37 | Osc1 WT Table | Osc 1 Shape | partial | 67.96875 | Wavetable-Auswahl laeuft ueber Blofeld Shape (Wavetable-Shapes) |
| 38 | Osc1 WT Stepped | - | drop | - | kein Stepped-Modus auf Blofeld |
| 39 | Osc1 WF Shape | Osc 1 Shape | take over | 67.96875 |  |
| 40 | Osc1 WF Desity | - | drop | - | kein Density-Parameter auf Blofeld |
| 41 | Osc1 WF Spread | - | drop | - | kein Spread-Parameter auf Blofeld |
| 42 | Osc1 WF PW | Osc 1 Pulsewidth | take over | 62.5 |  |
| 43 | Osc1 WF Sync | Osc 2 Sync to O3 | partial | 14.84375 | Blofeld: nur Osc2-Sync-zu-Osc3 (CC49), kein Sync pro Osc |
| 44 | Osc1 PT Position | - | drop | - | kein Partial/ additive Osc auf Blofeld |
| 45 | Osc1 PT Travel | - | drop | - | s.o. |
| 46 | Osc2 Fine Pitch | Osc 2 Detune | take over | 54.6875 |  |
| 47 | Osc2 Vol | Mixer Osc 2 Level | take over | 51.5625 |  |
| 48 | Osc2 Pan | Filter 2 Pan | partial | 32.03125 | s.o. |
| 49 | Osc2 WT Position | Osc 2 Pulsewidth | partial | 56.25 | s.o. |
| 50 | Osc2 WT Spectrum | Osc 2 Brilliance | partial | 11.71875 | s.o. |
| 51 | Osc2 WT Table | Osc 2 Shape | partial | 91.40625 | s.o. |
| 52 | Osc2 WT Stepped | - | drop | - | s.o. |
| 53 | Osc2 WF Shape | Osc 2 Shape | take over | 91.40625 |  |
| 54 | Osc2 WF Desity | - | drop | - | s.o. |
| 55 | Osc2 WF Spread | - | drop | - | s.o. |
| 56 | Osc2 WF PW | Osc 2 Pulsewidth | take over | 56.25 |  |
| 57 | Osc2 WF Sync | Osc 2 Sync to O3 | partial | 14.84375 | s.o. |
| 58 | Osc2 PT Position | - | drop | - | s.o. |
| 59 | Osc2 PT Travel | - | drop | - | s.o. |
| 60 | Osc3 Fine Pitch | Osc 3 Detune | take over | 46.09375 |  |
| 61 | Osc3 Vol | Mixer Osc 3 Level | take over | 49.21875 |  |
| 62 | Osc3 Pan | - | drop | - | kein Osc3-Pan auf Blofeld |
| 63 | Osc3 WT Position | Osc 3 Pulsewidth | partial | 44.53125 | s.o. |
| 64 | Osc3 WT Spectrum | Osc 3 Brilliance | partial | 7.8125 | s.o. |
| 65 | Osc3 WT Table | Osc 3 Shape | partial | 84.375 | s.o. (Osc3 nur Shapes 0..4) |
| 66 | Osc3 WT Stepped | - | drop | - | s.o. |
| 67 | Osc3 WF Shape | Osc 3 Shape | take over | 84.375 |  |
| 68 | Osc3 WF Desity | - | drop | - | s.o. |
| 69 | Osc3 WF Spread | - | drop | - | s.o. |
| 70 | Osc3 WF PW | Osc 3 Pulsewidth | take over | 44.53125 |  |
| 71 | Osc3 WF Sync | - | drop | - | s.o. |
| 72 | Osc3 PT Position | - | drop | - | s.o. |
| 73 | Osc3 PT Travel | - | drop | - | s.o. |
| 74 | Ringmod Osc1 To Osc2 | - | drop | - | Blofeld: nur RingMod Level/Balance im Mixer (CC54/55), kein Paar-Routing |
| 75 | Ringmod Osc1 To Osc3 | - | drop | - | s.o. |
| 76 | Digi Former Amount | - | drop | - | kein Digi-Former-Modul auf Blofeld |
| 77 | Digi Former Color | - | drop | - | s.o. |
| 78 | Digi Former Pan | - | drop | - | s.o. |
| 79 | Digi Former Level | - | drop | - | s.o. |
| 80 | Lfo1 Speed | LFO 1 Speed | take over | 75.0 |  |
| 81 | Lfo1 Amount | - | drop | - | Blofeld: LFO-Amount nur in Mod-Matrix-Slots (Modulation N Amount) |
| 82 | Lfo2 Speed | LFO 2 Speed | take over | 63.28125 |  |
| 83 | Lfo2 Amount | - | drop | - | s.o. |
| 84 | Lfo3 Speed | LFO 3 Speed | take over | 54.6875 |  |
| 85 | Lfo3 Amount | - | drop | - | s.o. |
| 86 | Komplex Speed | - | drop | - | kein Komplex-Modul auf Blofeld |
| 87 | Komplex Amount | - | drop | - | s.o. |
| 88 | Komplex Entropy | - | drop | - | s.o. |
| 89 | Glide Rate | Glide Rate | take over | 33.59375 | CC5 |
| 90 | Glide On Off | Glide | take over | 20.3125 | CC65 (SDATA 53) |
| 91 | Unisono Count | Allocation/Unisono | take over | 39.0625 | kein CC, nur SysEx |
| 92 | Unisono Detune | Unisono Detune | take over | 51.5625 | kein CC, nur SysEx |
| 93 | Chorus Dry Wet | - | drop | - | Blofeld FX1/FX2 Typ=Chorus, nur Mix per CC93/94 |
| 94 | Chorus Speed | - | drop | - | nur per SysEx (Effect N Parameter) |
| 95 | Chorus Feedback | - | drop | - | s.o. |
| 96 | Phaser Dry Wet | - | drop | - | s.o. |
| 97 | Phaser Depth | - | drop | - | s.o. |
| 98 | Phaser Feedback | - | drop | - | s.o. |
| 99 | Flanger Dry Wet | - | drop | - | s.o. |
| 100 | Flanger Speed | - | drop | - | s.o. |
| 101 | Flanger Feedback | - | drop | - | s.o. |
| 102 | Drive Amount | Filter 1 Drive | partial | 56.25 | Blofeld Drive sitzt in den Filtern (CC71/82) + Drive Curve; kein globaler Drive |
| 103 | Drive Dry Wet | - | drop | - | s.o. |
| 104 | Drive Gain | - | drop | - | s.o. |
| 105 | Free Env1 Attack | Envelope 3 Attack | take over | 28.90625 | CC107 |
| 106 | Free Env1 Decay | Envelope 3 Decay | take over | 42.1875 |  |
| 107 | Free Env1 Sustain | Envelope 3 Sustain | take over | 45.3125 |  |
| 108 | Free Env1 Release | Envelope 3 Release | take over | 21.09375 |  |
| 109 | Free Env1 Amount | - | drop | - | Blofeld Env3-Amount nur in Mod-Matrix |
| 110 | Free Env1 Velo Amount | - | drop | - | s.o. |
| 111 | Free Env2 Attack | Envelope 4 Attack | take over | 25.78125 | CC113 |
| 112 | Free Env2 Decay | Envelope 4 Decay | take over | 30.46875 |  |
| 113 | Free Env2 Sustain | Envelope 4 Sustain | take over | 30.46875 |  |
| 114 | Free Env2 Release | Envelope 4 Release | take over | 17.1875 |  |
| 115 | Free Env2 Amount | - | drop | - | s.o. |
| 116 | Free Env2 Velo Amount | - | drop | - | s.o. |

**Balance**: 116 Hapax CCs: 48 taken over, 14 partial, 54 dropped (not on the Blofeld).

## 6. Proposed MIDI CC keymap for the Blofeld

CC numbers from `docs/midi-maps/blofeld_midi_guide.csv` (official Waldorf CC list).
Noted: CC0/CC32 = bank select, CC5 = glide rate, CC7 = channel volume, CC65 = glide active,
CC64/66 = pedals, CC120-123 = controller reset/ANO. ESSENTIAL = marked.

| CC | Guide parameter | SNDD parameter | Category | Share % | Weight | Score | ESSENTIAL |
|---|---|---|---|---|---|---|---|
| 0 | Bank select MSB | - | - | - | - | - |  |
| 1 | Mod wheel | - | - | - | - | - |  |
| 2 | Breath control | - | - | - | - | - |  |
| 4 | Foot control | - | - | - | - | - |  |
| 5 | Glide rate | Glide Rate | Glide | 33.6 | 2 | 0.672 |  |
| 7 | Channel volume | Amplifier Volume | Amp | 43.8 | 2 | 0.875 |  |
| 10 | Pan | - | - | - | - | - |  |
| 12 | Arpeggiator range | Arpeggiator Octave | Arp | 21.1 | 1 | 0.211 |  |
| 13 | Arpeggiator length | Arpeggiator Length | Arp | 39.1 | 1 | 0.391 |  |
| 14 | Arpeggiator active | Arpeggiator Mode | Arp | 5.5 | 1 | 0.055 |  |
| 15 | LFO 1 shape | LFO 1 Shape | LFO | 30.5 | 2 | 0.609 |  |
| 16 | LFO 1 speed | LFO 1 Speed | LFO | 75.0 | 2 | 1.500 |  |
| 17 | LFO 1 sync | LFO 1 Sync | LFO | 14.8 | 2 | 0.297 |  |
| 18 | LFO 1 delay | LFO 1 Delay | LFO | 6.2 | 2 | 0.125 |  |
| 19 | LFO 2 shape | LFO 2 Shape | LFO | 30.5 | 2 | 0.609 |  |
| 20 | LFO 2 speed | LFO 2 Speed | LFO | 63.3 | 2 | 1.266 |  |
| 21 | LFO 2 sync | LFO 2 Sync | LFO | 7.0 | 2 | 0.141 |  |
| 22 | LFO 2 delay | LFO 2 Delay | LFO | 3.1 | 2 | 0.062 |  |
| 23 | LFO 3 shape | LFO 3 Shape | LFO | 25.8 | 2 | 0.516 |  |
| 24 | LFO 3 speed | LFO 3 Speed | LFO | 54.7 | 2 | 1.094 |  |
| 25 | LFO 3 sync | LFO 3 Sync | LFO | 7.8 | 2 | 0.156 |  |
| 26 | LFO 3 delay | LFO 3 Delay | LFO | 2.3 | 2 | 0.047 |  |
| 27 | OSC 1 octave | Osc 1 Octave | Tuning | 52.3 | 3 | 1.570 | ESSENTIAL |
| 28 | OSC 1 semitone | Osc 1 Semitone | Tuning | 8.6 | 3 | 0.258 | ESSENTIAL |
| 29 | OSC 1 detune | Osc 1 Detune | Tuning | 45.3 | 3 | 1.359 | ESSENTIAL |
| 30 | OSC 1 FM | Osc 1 FM Amount | Osc (FM/PWM) | 21.1 | 1 | 0.211 |  |
| 31 | OSC 1 shape | Osc 1 Shape | Waveform | 68.0 | 3 | 2.039 | ESSENTIAL |
| 33 | OSC 1 pulsewidth | Osc 1 Pulsewidth | Osc (FM/PWM) | 62.5 | 1 | 0.625 |  |
| 34 | OSC 1 PWM | Osc 1 PWM Amount | Osc (FM/PWM) | 35.2 | 1 | 0.352 |  |
| 35 | OSC 2 octave | Osc 2 Octave | Tuning | 53.1 | 3 | 1.594 | ESSENTIAL |
| 36 | OSC 2 semitone | Osc 2 Semitone | Tuning | 26.6 | 3 | 0.797 | ESSENTIAL |
| 37 | OSC 2 detune | Osc 2 Detune | Tuning | 54.7 | 3 | 1.641 | ESSENTIAL |
| 38 | OSC 2 FM | Osc 2 FM Amount | Osc (FM/PWM) | 22.7 | 1 | 0.227 |  |
| 39 | OSC 2 shape | Osc 2 Shape | Waveform | 91.4 | 3 | 2.742 | ESSENTIAL |
| 40 | OSC 2 pulsewidth | Osc 2 Pulsewidth | Osc (FM/PWM) | 56.2 | 1 | 0.562 |  |
| 41 | OSC 2 PWM | Osc 2 PWM Amount | Osc (FM/PWM) | 40.6 | 1 | 0.406 |  |
| 42 | OSC 3 octave | Osc 3 Octave | Tuning | 50.8 | 3 | 1.523 | ESSENTIAL |
| 43 | OSC 3 semitone | Osc 3 Semitone | Tuning | 14.8 | 3 | 0.445 | ESSENTIAL |
| 44 | OSC 3 detune | Osc 3 Detune | Tuning | 46.1 | 3 | 1.383 | ESSENTIAL |
| 45 | OSC 3 FM | Osc 3 FM Amount | Osc (FM/PWM) | 15.6 | 1 | 0.156 |  |
| 46 | OSC 3 shape | Osc 3 Shape | Waveform | 84.4 | 3 | 2.531 | ESSENTIAL |
| 47 | OSC 3 pulsewidth | Osc 3 Pulsewidth | Osc (FM/PWM) | 44.5 | 1 | 0.445 |  |
| 48 | OSC 3 PWM | Osc 3 PWM Amount | Osc (FM/PWM) | 25.0 | 1 | 0.250 |  |
| 49 | Sync | Osc 2 Sync to O3 | Osc (FM/PWM) | 14.8 | 1 | 0.148 |  |
| 50 | Pitchmod | Osc Pitch Amount | Tuning | 28.1 | 3 | 0.844 | ESSENTIAL |
| 51 | Glide mode | Glide Mode | Glide | 3.1 | 2 | 0.062 |  |
| 52 | OSC 1 level | Mixer Osc 1 Level | Mixer | 35.2 | 3 | 1.055 | ESSENTIAL |
| 53 | OSC 1 balance | Mixer Osc 1 Balance | Mixer | 23.4 | 3 | 0.703 | ESSENTIAL |
| 54 | Ringmod level | Mixer RingMod Level | Mixer | 16.4 | 3 | 0.492 | ESSENTIAL |
| 55 | Ringmod balance | Mixer RingMod Balance | Mixer | 32.0 | 3 | 0.961 | ESSENTIAL |
| 56 | OSC 2 level | Mixer Osc 2 Level | Mixer | 51.6 | 3 | 1.547 | ESSENTIAL |
| 57 | OSC 2 balance | Mixer Osc 2 Balance | Mixer | 39.1 | 3 | 1.172 | ESSENTIAL |
| 58 | OSC 3 level | Mixer Osc 3 Level | Mixer | 49.2 | 3 | 1.477 | ESSENTIAL |
| 59 | OSC 3 balance | Mixer Osc 3 Balance | Mixer | 36.7 | 3 | 1.102 | ESSENTIAL |
| 60 | Noise level | Mixer Noise Level | Mixer | 10.2 | 3 | 0.305 | ESSENTIAL |
| 61 | Noise balance | Mixer Noise Balance | Mixer | 32.0 | 3 | 0.961 | ESSENTIAL |
| 62 | Noise color | Mixer Noise Colour | Mixer | 14.1 | 3 | 0.422 | ESSENTIAL |
| 64 | Sustain pedal | - | - | - | - | - |  |
| 65 | Glide active | Glide | Glide | 20.3 | 2 | 0.406 |  |
| 66 | Sostenuto | - | - | - | - | - |  |
| 67 | Filter Routing | Filter Routing | Filter | 34.4 | 3 | 1.031 | ESSENTIAL |
| 68 | Filter 1 type | Filter 1 Type | Filter | 53.1 | 3 | 1.594 | ESSENTIAL |
| 69 | Filter 1 cutoff | Filter 1 Cutoff | Filter | 93.8 | 3 | 2.812 | ESSENTIAL |
| 70 | Filter 1 resonance | Filter 1 Resonance | Filter | 78.9 | 3 | 2.367 | ESSENTIAL |
| 71 | Filter 1 drive | Filter 1 Drive | Filter | 56.2 | 3 | 1.688 | ESSENTIAL |
| 72 | Filter 1 keytrack | Filter 1 Keytrack | Filter | 60.2 | 3 | 1.805 | ESSENTIAL |
| 73 | Filter 1 envelope amount | Filter 1 Env Amount | Filter | 71.9 | 3 | 2.156 | ESSENTIAL |
| 74 | Filter 1 envelope velocity | Filter 1 Env Velocity | Filter | 38.3 | 3 | 1.148 | ESSENTIAL |
| 75 | Filter 1 cutoff modulation | Filter 1 Mod Amount | Filter | 39.1 | 3 | 1.172 | ESSENTIAL |
| 76 | Filter 1 FM | Filter 1 FM Amount | Filter | 9.4 | 3 | 0.281 | ESSENTIAL |
| 77 | Filter 1 pan | Filter 1 Pan | Filter | 36.7 | 3 | 1.102 | ESSENTIAL |
| 78 | Filter 1 pan modulation | Filter 1 Pan Amount | Filter | 22.7 | 3 | 0.680 | ESSENTIAL |
| 79 | Filter 2 type | Filter 2 Type | Filter | 78.1 | 3 | 2.344 | ESSENTIAL |
| 80 | Filter 2 cutoff | Filter 2 Cutoff | Filter | 78.1 | 3 | 2.344 | ESSENTIAL |
| 81 | Filter 2 resonance | Filter 2 Resonance | Filter | 58.6 | 3 | 1.758 | ESSENTIAL |
| 82 | Filter 2 drive | Filter 2 Drive | Filter | 32.0 | 3 | 0.961 | ESSENTIAL |
| 83 | Filter 2 keytrack | Filter 2 Keytrack | Filter | 50.8 | 3 | 1.523 | ESSENTIAL |
| 84 | Filter 2 envelope amount | Filter 2 Env Amount | Filter | 47.7 | 3 | 1.430 | ESSENTIAL |
| 85 | Filter 2 envelope velocity | Filter 2 Env Velocity | Filter | 28.1 | 3 | 0.844 | ESSENTIAL |
| 86 | Filter 2 cutoff modulation | Filter 2 Mod Amount | Filter | 28.9 | 3 | 0.867 | ESSENTIAL |
| 87 | Filter 2 FM | Filter 2 FM Amount | Filter | 6.2 | 3 | 0.188 | ESSENTIAL |
| 88 | Filter 2 pan | Filter 2 Pan | Filter | 32.0 | 3 | 0.961 | ESSENTIAL |
| 89 | Filter 2 pan modulation | Filter 2 Pan Amount | Filter | 21.1 | 3 | 0.633 | ESSENTIAL |
| 90 | Amp volume | Amplifier Volume | Amp | 43.8 | 2 | 0.875 |  |
| 91 | Amp velocity | Amplifier Velocity | Amp | 70.3 | 2 | 1.406 |  |
| 92 | Amp modulation | Amplifier Mod Amount | Amp | 1.6 | 2 | 0.031 |  |
| 93 | FX 1 mix | Effect 1 Mix | FX | 72.7 | 1 | 0.727 |  |
| 94 | FX 2 mix | Effect 2 Mix | FX | 78.9 | 1 | 0.789 |  |
| 95 | Filter envelope attack | Filter Envelope Attack | Env1 | 48.4 | 3 | 1.453 | ESSENTIAL |
| 96 | Filter envelope decay | Filter Envelope Decay | Env1 | 82.8 | 3 | 2.484 | ESSENTIAL |
| 97 | Filter envelope sustain | Filter Envelope Sustain | Env1 | 58.6 | 3 | 1.758 | ESSENTIAL |
| 98 | Filter envelope decay 2 | Filter Envelope Decay 2 | Env1 | 43.0 | 3 | 1.289 | ESSENTIAL |
| 99 | Filter envelope sustain 2 | Filter Envelope Sustain 2 | Env1 | 32.8 | 3 | 0.984 | ESSENTIAL |
| 100 | Filter envelope release | Filter Envelope Release | Env1 | 75.8 | 3 | 2.273 | ESSENTIAL |
| 101 | Amp envelope attack | Amplifier Envelope Attack | Env2 | 50.8 | 3 | 1.523 | ESSENTIAL |
| 102 | Amp envelope decay | Amplifier Envelope Decay | Env2 | 67.2 | 3 | 2.016 | ESSENTIAL |
| 103 | Amp envelope sustain | Amplifier Envelope Sustain | Env2 | 57.8 | 3 | 1.734 | ESSENTIAL |
| 104 | Amp envelope decay 2 | Amplifier Envelope Decay 2 | Env2 | 30.5 | 3 | 0.914 | ESSENTIAL |
| 105 | Amp envelope sustain 2 | Amplifier Envelope Sustain 2 | Env2 | 36.7 | 3 | 1.102 | ESSENTIAL |
| 106 | Amp envelope release | Amplifier Envelope Release | Env2 | 76.6 | 3 | 2.297 | ESSENTIAL |
| 107 | Envelope 3 attack | Envelope 3 Attack | Env3 | 28.9 | 2 | 0.578 |  |
| 108 | Envelope 3 decay | Envelope 3 Decay | Env3 | 42.2 | 2 | 0.844 |  |
| 109 | Envelope 3 sustain | Envelope 3 Sustain | Env3 | 45.3 | 2 | 0.906 |  |
| 110 | Envelope 3 decay 2 | Envelope 3 Decay 2 | Env3 | 23.4 | 2 | 0.469 |  |
| 111 | Envelope 3 sustain 2 | Envelope 3 Sustain 2 | Env3 | 32.0 | 2 | 0.641 |  |
| 112 | Envelope 3 release | Envelope 3 Release | Env3 | 21.1 | 2 | 0.422 |  |
| 113 | Envelope 4 attack | Envelope 4 Attack | Env4 | 25.8 | 2 | 0.516 |  |
| 114 | Envelope 4 decay | Envelope 4 Decay | Env4 | 30.5 | 2 | 0.609 |  |
| 115 | Envelope 4 sustain | Envelope 4 Sustain | Env4 | 30.5 | 2 | 0.609 |  |
| 116 | Envelope 4 decay 2 | Envelope 4 Decay 2 | Env4 | 23.4 | 2 | 0.469 |  |
| 117 | Envelope 4 sustain 2 | Envelope 4 Sustain 2 | Env4 | 32.0 | 2 | 0.641 |  |
| 118 | Envelope 4 release | Envelope 4 Release | Env4 | 17.2 | 2 | 0.344 |  |
| 120 | All sound off | - | - | - | - | - |  |
| 121 | Reset all controllers | - | - | - | - | - |  |
| 122 | Local control on/off | - | - | - | - | - |  |
| 123 | All notes off | - | - | - | - | - |  |

### Keymap core (essential, by usage share)

| CC | Parameter | Share % | Score |
|---|---|---|---|
| 69 | Filter 1 Cutoff | 93.8 | 2.812 |
| 39 | Osc 2 Shape | 91.4 | 2.742 |
| 46 | Osc 3 Shape | 84.4 | 2.531 |
| 96 | Filter Envelope Decay | 82.8 | 2.484 |
| 70 | Filter 1 Resonance | 78.9 | 2.367 |
| 79 | Filter 2 Type | 78.1 | 2.344 |
| 80 | Filter 2 Cutoff | 78.1 | 2.344 |
| 106 | Amplifier Envelope Release | 76.6 | 2.297 |
| 100 | Filter Envelope Release | 75.8 | 2.273 |
| 73 | Filter 1 Env Amount | 71.9 | 2.156 |
| 31 | Osc 1 Shape | 68.0 | 2.039 |
| 102 | Amplifier Envelope Decay | 67.2 | 2.016 |
| 72 | Filter 1 Keytrack | 60.2 | 1.805 |
| 81 | Filter 2 Resonance | 58.6 | 1.758 |
| 97 | Filter Envelope Sustain | 58.6 | 1.758 |
| 103 | Amplifier Envelope Sustain | 57.8 | 1.734 |
| 71 | Filter 1 Drive | 56.2 | 1.688 |
| 37 | Osc 2 Detune | 54.7 | 1.641 |
| 35 | Osc 2 Octave | 53.1 | 1.594 |
| 68 | Filter 1 Type | 53.1 | 1.594 |
| 27 | Osc 1 Octave | 52.3 | 1.570 |
| 56 | Mixer Osc 2 Level | 51.6 | 1.547 |
| 42 | Osc 3 Octave | 50.8 | 1.523 |
| 83 | Filter 2 Keytrack | 50.8 | 1.523 |
| 101 | Amplifier Envelope Attack | 50.8 | 1.523 |
| 58 | Mixer Osc 3 Level | 49.2 | 1.477 |
| 95 | Filter Envelope Attack | 48.4 | 1.453 |
| 84 | Filter 2 Env Amount | 47.7 | 1.430 |
| 44 | Osc 3 Detune | 46.1 | 1.383 |
| 29 | Osc 1 Detune | 45.3 | 1.359 |
| 98 | Filter Envelope Decay 2 | 43.0 | 1.289 |
| 57 | Mixer Osc 2 Balance | 39.1 | 1.172 |
| 75 | Filter 1 Mod Amount | 39.1 | 1.172 |
| 74 | Filter 1 Env Velocity | 38.3 | 1.148 |
| 59 | Mixer Osc 3 Balance | 36.7 | 1.102 |
| 77 | Filter 1 Pan | 36.7 | 1.102 |
| 105 | Amplifier Envelope Sustain 2 | 36.7 | 1.102 |
| 52 | Mixer Osc 1 Level | 35.2 | 1.055 |
| 67 | Filter Routing | 34.4 | 1.031 |
| 99 | Filter Envelope Sustain 2 | 32.8 | 0.984 |
| 55 | Mixer RingMod Balance | 32.0 | 0.961 |
| 61 | Mixer Noise Balance | 32.0 | 0.961 |
| 82 | Filter 2 Drive | 32.0 | 0.961 |
| 88 | Filter 2 Pan | 32.0 | 0.961 |
| 104 | Amplifier Envelope Decay 2 | 30.5 | 0.914 |
| 86 | Filter 2 Mod Amount | 28.9 | 0.867 |
| 50 | Osc Pitch Amount | 28.1 | 0.844 |
| 85 | Filter 2 Env Velocity | 28.1 | 0.844 |
| 36 | Osc 2 Semitone | 26.6 | 0.797 |
| 53 | Mixer Osc 1 Balance | 23.4 | 0.703 |
| 78 | Filter 1 Pan Amount | 22.7 | 0.680 |
| 89 | Filter 2 Pan Amount | 21.1 | 0.633 |
| 54 | Mixer RingMod Level | 16.4 | 0.492 |
| 43 | Osc 3 Semitone | 14.8 | 0.445 |
| 62 | Mixer Noise Colour | 14.1 | 0.422 |
| 60 | Mixer Noise Level | 10.2 | 0.305 |
| 76 | Filter 1 FM Amount | 9.4 | 0.281 |
| 28 | Osc 1 Semitone | 8.6 | 0.258 |
| 87 | Filter 2 FM Amount | 6.2 | 0.188 |

## 7. Open points

- CCs without an SNDD counterpart (mod wheel CC1, breath CC2, foot CC4, pan CC10, pedals CC64/66,
  bank select CC0/32, CC120-123) control system/mod-matrix sources, not sound parameters –
  in a keymap assign them as mod sources if needed.
- Many Blofeld parameters have **no CC** (mod matrix 16 slots, modifier, FX parameters,
  arp pattern, unisono, env modes, filter drive curve...) – only via SysEx (SNDP) or the panel.
- Enums (shape/type/mode) are sent via CC as raw index 0..127; the keymap should respect the
  value range of the guide (e.g. shape CC31 only 0..5 per the guide, SysEx allows 0..74).
- The init reference is the stored init dump; if individual factory sounds are exactly init,
  they count as 'not used' (correct).
- No dumps were skipped because of chk errors.

