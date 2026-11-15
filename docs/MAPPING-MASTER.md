# Master-Tabelle: Blofeld-Parameter → Iridium-qpat (Mapping-Status)

Erstellt: 2026-11-09. Basis: `bloridium/blofeld_dump.py` (SDATA-Tabelle, Spec 3.1) + `bloridium/qpat_map.py`.
Referenz-Sound: A043 "SH Power" (107 gemappt / 75 unmapped bei 290 gesetzten Params).

**PC/Favorites-Mapping am Iridium (welcher Sound auf welchem MIDI PC): siehe `docs/IRIDIUM-FAVORITES-MAP.md`**
(mido-PC = Display-"MIDI" − 2; MIDI 100–106 = Kalib-Testsounds, 107–115 = die 9 konvertierten Sounds).

Legende: ✅ direkt (1:1) · 🟡 Näherung · ⚠️ gemappt mit bekannter Abweichung · ❌ unmapped

## Oszillatoren (Osc 1-3) (SDATA 0–56)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 1 | Osc 1 Octave | OscNCoarsePitch | 🟡 Näherung | aus SDATA-Rohwerten rekonstruiert (64 = Mitte) |
| 2 | Osc 1 Semitone | OscNCoarsePitch | 🟡 Näherung | aus SDATA-Rohwerten rekonstruiert (64 = Mitte) |
| 3 | Osc 1 Detune | OscNFinePitch | ✅ direkt | norm raw/127 |
| 4 | Osc 1 Bend Range | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 5 | Osc 1 Keytrack | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 6 | Osc 1 FM Source | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 7 | Osc 1 FM Amount | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 8 | Osc 1 Shape | OscNType + OscNWaveformShape | 🟡 Näherung | VA-Shapes direkt; Wavetables -> Type + WavetableTable (Bridge, z.B. MalletSyn=2) + WavetablePosition (aus Pulsewidth) + Brilliance; Spectrum ungemappt |
| 9 | Osc 1 Pulsewidth | OscNWaveformPW | ✅ direkt | Waveform-Modus -> WaveformPW; Wavetable-Modus -> WavetablePosition (Blofeld 'PW/Wave') |
| 10 | Osc 1 PWM Source | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 11 | Osc 1 PWM Amount | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 14 | Osc 1 Limit WT | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 16 | Osc 1 Brilliance | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 17 | Osc 2 Octave | OscNCoarsePitch | 🟡 Näherung | aus SDATA-Rohwerten rekonstruiert (64 = Mitte) |
| 18 | Osc 2 Semitone | OscNCoarsePitch | 🟡 Näherung | aus SDATA-Rohwerten rekonstruiert (64 = Mitte) |
| 19 | Osc 2 Detune | OscNFinePitch | ✅ direkt | norm raw/127 |
| 20 | Osc 2 Bend Range | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 21 | Osc 2 Keytrack | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 22 | Osc 2 FM Source | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 23 | Osc 2 FM Amount | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 24 | Osc 2 Shape | OscNType + OscNWaveformShape | 🟡 Näherung | VA-Shapes direkt; Wavetables -> Type + WavetableTable (Bridge, z.B. MalletSyn=2) + WavetablePosition (aus Pulsewidth) + Brilliance; Spectrum ungemappt |
| 25 | Osc 2 Pulsewidth | OscNWaveformPW | ✅ direkt | Waveform-Modus -> WaveformPW; Wavetable-Modus -> WavetablePosition (Blofeld 'PW/Wave') |
| 26 | Osc 2 PWM Source | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 27 | Osc 2 PWM Amount | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 30 | Osc 2 Limit WT | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 32 | Osc 2 Brilliance | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 33 | Osc 3 Octave | OscNCoarsePitch | 🟡 Näherung | aus SDATA-Rohwerten rekonstruiert (64 = Mitte) |
| 34 | Osc 3 Semitone | OscNCoarsePitch | 🟡 Näherung | aus SDATA-Rohwerten rekonstruiert (64 = Mitte) |
| 35 | Osc 3 Detune | OscNFinePitch | ✅ direkt | norm raw/127 |
| 36 | Osc 3 Bend Range | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 37 | Osc 3 Keytrack | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 38 | Osc 3 FM Source | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 39 | Osc 3 FM Amount | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 40 | Osc 3 Shape | OscNType + OscNWaveformShape | 🟡 Näherung | VA-Shapes direkt; Wavetables -> Type + WavetableTable (Bridge, z.B. MalletSyn=2) + WavetablePosition (aus Pulsewidth) + Brilliance; Spectrum ungemappt |
| 41 | Osc 3 Pulsewidth | OscNWaveformPW | ✅ direkt | Waveform-Modus -> WaveformPW; Wavetable-Modus -> WavetablePosition (Blofeld 'PW/Wave') |
| 42 | Osc 3 PWM Source | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 43 | Osc 3 PWM Amount | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 46 | Osc 3 Limit WT | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 48 | Osc 3 Brilliance | - | ❌ unmapped | FM/PWM liegen beim Iridium in Kernels/Mod-Matrix, kein 1:1 |
| 49 | Osc 2 Sync to O3 | - | ❌ unmapped |  |
| 50 | Osc Pitch Source | - | ❌ unmapped |  |
| 51 | Osc Pitch Amount | - | ❌ unmapped |  |
| 53 | Glide | - | ❌ unmapped | Global/System/etc. |
| 56 | Glide Mode | - | ❌ unmapped | Global/System/etc. |

## Mixer (SDATA 57–72)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 57 | Glide Rate | GlideRate | 🟡 Näherung | zeit-kalibriert (exponential, Anker in `qpat_map.py`: raw 20 = norm 0.15 = 0.045 s; Iridium norm 0.378 = 0.29 s Display; raw 127 ≈ 5 s). Lineares norm() setzte zu hoch (A073 raw 48: 0.378/0.29 s statt korrekt ~0.30/~0.15 s) |
| 58 | Allocation/Unisono | UnisonoCount + UnisonoDetune | 🟡 Näherung | Bitfeld dekodiert (Count = bits 5-7) |
| 59 | Unisono Detune | UnisonoDetune | ✅ direkt | norm |
| 61 | Mixer Osc 1 Level | OscNVol | ✅ direkt | norm raw/127 |
| 62 | Mixer Osc 1 Balance | OscNPan | ⚠️ Abweichung | Blofeld Balance = F1/F2-Anteil, Iridium Pan = Stereo -> Semantik abweichend |
| 63 | Mixer Osc 2 Level | OscNVol | ✅ direkt | norm raw/127 |
| 64 | Mixer Osc 2 Balance | OscNPan | ⚠️ Abweichung | Blofeld Balance = F1/F2-Anteil, Iridium Pan = Stereo -> Semantik abweichend |
| 65 | Mixer Osc 3 Level | OscNVol | ✅ direkt | norm raw/127 |
| 66 | Mixer Osc 3 Balance | OscNPan | ⚠️ Abweichung | Blofeld Balance = F1/F2-Anteil, Iridium Pan = Stereo -> Semantik abweichend |
| 67 | Mixer Noise Level | - | ❌ unmapped | kein direktes qpat-Key (Particle/Resonator-Noise) |
| 68 | Mixer Noise Balance | - | ❌ unmapped | kein direktes qpat-Key (Particle/Resonator-Noise) |
| 69 | Mixer Noise Colour | - | ❌ unmapped | kein direktes qpat-Key (Particle/Resonator-Noise) |
| 71 | Mixer RingMod Level | RingmodOsc12 | ✅ direkt | nur O1->O2; O1->O3 (CC75) unmapped |
| 72 | Mixer RingMod Balance | RingmodOsc12 | ✅ direkt | nur O1->O2; O1->O3 (CC75) unmapped |

## Filter 1/2 + Routing (SDATA 73–117)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 77 | Filter 1 Type | Filter12Type | 🟡 Näherung | Enum-Tabelle v14; Notch/Comb -> BP-Naeherung |
| 78 | Filter 1 Cutoff | Filter1CutOff | ✅ direkt | norm; Geraet: kein CC (nur qpat/CC0 via .mimap) |
| 80 | Filter 1 Resonance | Filter1Reso | ✅ direkt | norm |
| 81 | Filter 1 Drive | - | ❌ unmapped | Drive -> FX Drive moeglich, Pan -> DigiFormer PAN (CC78) |
| 82 | Filter 1 Drive Curve | - | ❌ unmapped | Global/System/etc. |
| 86 | Filter 1 Keytrack | Filter1Keytrack | ✅ direkt | norm(raw): Blofeld 0..127 = -200%..+196% (Offset-Binaer, 64=0%), Iridium 0..1 = -200%..+200% (0.5=0%); alt (kt-64)/64 ergab -200% bei 64 |
| 87 | Filter 1 Env Amount | FilterNEnvAmount | ✅ direkt | norm |
| 88 | Filter 1 Env Velocity | FilterNVeloAmount | ✅ direkt | norm |
| 89 | Filter 1 Mod Source | Matrix-Slot -> Filter1/2 Cutoff | 🟡 Näherung | direkte Filter-Mod als Extra-Matrix-Slot |
| 90 | Filter 1 Mod Amount | Matrix-Slot -> Filter1/2 Cutoff | 🟡 Näherung | direkte Filter-Mod als Extra-Matrix-Slot |
| 91 | Filter 1 FM Source | - | ❌ unmapped | Drive -> FX Drive moeglich, Pan -> DigiFormer PAN (CC78) |
| 92 | Filter 1 FM Amount | - | ❌ unmapped | Drive -> FX Drive moeglich, Pan -> DigiFormer PAN (CC78) |
| 93 | Filter 1 Pan | - | ❌ unmapped | Drive -> FX Drive moeglich, Pan -> DigiFormer PAN (CC78) |
| 94 | Filter 1 Pan Source | - | ❌ unmapped | Global/System/etc. |
| 95 | Filter 1 Pan Amount | - | ❌ unmapped | Global/System/etc. |
| 97 | Filter 2 Type | DigiFormerType | 🟡 Näherung | Blofeld-F2-Modell -> Former-Modell (Nave/PPG/Largo/SVF), nicht identisch |
| 98 | Filter 2 Cutoff | DigiFormerAmount + Filter2CutOff | 🟡 Näherung | Cutoff -> Former Amount (Näherung), F2-Stufe selbst Off |
| 100 | Filter 2 Resonance | DigiFormerColor + Filter2Reso | 🟡 Näherung | Reso -> Former Color |
| 101 | Filter 2 Drive | - | ❌ unmapped |  |
| 102 | Filter 2 Drive Curve | - | ❌ unmapped | Global/System/etc. |
| 106 | Filter 2 Keytrack | Filter2Keytrack | ✅ direkt | norm(raw) wie F1 Keytrack (siehe 86) |
| 107 | Filter 2 Env Amount | FilterNEnvAmount | ✅ direkt | norm |
| 108 | Filter 2 Env Velocity | FilterNVeloAmount | ✅ direkt | norm |
| 109 | Filter 2 Mod Source | Matrix-Slot -> Filter1/2 Cutoff | 🟡 Näherung | direkte Filter-Mod als Extra-Matrix-Slot |
| 110 | Filter 2 Mod Amount | Matrix-Slot -> Filter1/2 Cutoff | 🟡 Näherung | direkte Filter-Mod als Extra-Matrix-Slot |
| 111 | Filter 2 FM Source | - | ❌ unmapped |  |
| 112 | Filter 2 FM Amount | - | ❌ unmapped |  |
| 113 | Filter 2 Pan | - | ❌ unmapped |  |
| 114 | Filter 2 Pan Source | - | ❌ unmapped | Global/System/etc. |
| 115 | Filter 2 Pan Amount | - | ❌ unmapped | Global/System/etc. |
| 117 | Filter Routing | FilterLink (Linked) + Filter2State Off | 🟡 Näherung | seriell -> Linked; F2 Bypass -> F2 Off + Former Bypass (Bleed-Fix) |

## Effekte (FX1/FX2 Type/Mix) (SDATA 118–127)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 121 | Amplifier Volume | MainVolume | ✅ direkt | norm |
| 122 | Amplifier Velocity | Matrix-Slot Velocity->Volume (AmpVeloAmount=0) | 🟡 Näherung | AmpVelo wirkt am Geraet kaum (CC17 ~0.4 dB); Vel->Volume in Matrix, Amount bipolar |
| 123 | Amplifier Mod Source | - | ❌ unmapped | Global/System/etc. |
| 124 | Amplifier Mod Amount | - | ❌ unmapped | Global/System/etc. |

## Effekt-Parameter (SDATA 128–159)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 128 | Effect 1 Type | FX1Type/FX2Type | 🟡 Näherung | Enum v14; Triple FX -> Chorus; Enum-Shift beachten (v8 vs v14 vs v15) |
| 129 | Effect 1 Mix | ChorusDryWet / DelayDryWet | ✅ direkt | nur bei Chorus/Delay; andere FX-Typen ohne Mix-Key |
| 130 | Effect 1 Parameter 1 | - | ❌ unmapped | Global/System/etc. |
| 131 | Effect 1 Parameter 2 | - | ❌ unmapped | Global/System/etc. |
| 132 | Effect 1 Parameter 3 | - | ❌ unmapped | Global/System/etc. |
| 133 | Effect 1 Parameter 4 | - | ❌ unmapped | Global/System/etc. |
| 134 | Effect 1 Parameter 5 | - | ❌ unmapped | Global/System/etc. |
| 135 | Effect 1 Parameter 6 | - | ❌ unmapped | Global/System/etc. |
| 136 | Effect 1 Parameter 7 | - | ❌ unmapped | Global/System/etc. |
| 137 | Effect 1 Parameter 8 | - | ❌ unmapped | Global/System/etc. |
| 138 | Effect 1 Parameter 9 | - | ❌ unmapped | Global/System/etc. |
| 139 | Effect 1 Parameter 10 | - | ❌ unmapped | Global/System/etc. |
| 140 | Effect 1 Parameter 11 | - | ❌ unmapped | Global/System/etc. |
| 141 | Effect 1 Parameter 12 | - | ❌ unmapped | Global/System/etc. |
| 142 | Effect 1 Parameter 13 | - | ❌ unmapped | Global/System/etc. |
| 143 | Effect 1 Parameter 14 | - | ❌ unmapped | Global/System/etc. |
| 144 | Effect 2 Type | FX1Type/FX2Type | 🟡 Näherung | Enum v14; Triple FX -> Chorus; Enum-Shift beachten (v8 vs v14 vs v15) |
| 145 | Effect 2 Mix | ChorusDryWet / DelayDryWet | ✅ direkt | nur bei Chorus/Delay; andere FX-Typen ohne Mix-Key |
| 146 | Effect 2 Parameter 1 | - | ❌ unmapped | Global/System/etc. |
| 147 | Effect 2 Parameter 2 | - | ❌ unmapped | Global/System/etc. |
| 148 | Effect 2 Parameter 3 | - | ❌ unmapped | Global/System/etc. |
| 149 | Effect 2 Parameter 4 | - | ❌ unmapped | Global/System/etc. |
| 150 | Effect 2 Parameter 5 | - | ❌ unmapped | Global/System/etc. |
| 151 | Effect 2 Parameter 6 | - | ❌ unmapped | Global/System/etc. |
| 152 | Effect 2 Parameter 7 | - | ❌ unmapped | Global/System/etc. |
| 153 | Effect 2 Parameter 8 | - | ❌ unmapped | Global/System/etc. |
| 154 | Effect 2 Parameter 9 | - | ❌ unmapped | Global/System/etc. |
| 155 | Effect 2 Parameter 10 | - | ❌ unmapped | Global/System/etc. |
| 156 | Effect 2 Parameter 11 | - | ❌ unmapped | Global/System/etc. |
| 157 | Effect 2 Parameter 12 | - | ❌ unmapped | Global/System/etc. |
| 158 | Effect 2 Parameter 13 | - | ❌ unmapped | Global/System/etc. |
| 159 | Effect 2 Parameter 14 | - | ❌ unmapped | Global/System/etc. |

## LFO 1-3 (SDATA 160–194)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 160 | LFO 1 Shape | - | ❌ unmapped |  |
| 161 | LFO 1 Speed | LfoN Speed/Sync/SyncRatio | 🟡 Näherung | Key heisst Lfo1Speed (nicht LFO1Speed!); Sync=1 -> Clock-Index (4.6, bars) -> SyncRatio (beats), sonst free Speed=norm (ungeprueft) |
| 163 | LFO 1 Sync | Lfo1Sync | ✅ direkt | on -> SyncRatio aus Clock-Index; sonst free |
| 164 | LFO 1 Clocked | - | ❌ unmapped | Global/System/etc. |
| 165 | LFO 1 Start Phase | - | ❌ unmapped | Global/System/etc. |
| 166 | LFO 1 Delay | - | ❌ unmapped |  |
| 167 | LFO 1 Fade | - | ❌ unmapped |  |
| 170 | LFO 1 Keytrack | - | ❌ unmapped |  |
| 172 | LFO 2 Shape | - | ❌ unmapped |  |
| 173 | LFO 2 Speed | LFO NSpeed | ✅ direkt | Clock-Index norm |
| 175 | LFO 2 Sync | - | ❌ unmapped |  |
| 176 | LFO 2 Clocked | - | ❌ unmapped | Global/System/etc. |
| 177 | LFO 2 Start Phase | - | ❌ unmapped | Global/System/etc. |
| 178 | LFO 2 Delay | - | ❌ unmapped |  |
| 179 | LFO 2 Fade | - | ❌ unmapped |  |
| 182 | LFO 2 Keytrack | - | ❌ unmapped |  |
| 184 | LFO 3 Shape | - | ❌ unmapped |  |
| 185 | LFO 3 Speed | LFO NSpeed | ✅ direkt | Clock-Index norm |
| 187 | LFO 3 Sync | - | ❌ unmapped |  |
| 188 | LFO 3 Clocked | - | ❌ unmapped | Global/System/etc. |
| 189 | LFO 3 Start Phase | - | ❌ unmapped | Global/System/etc. |
| 190 | LFO 3 Delay | - | ❌ unmapped |  |
| 191 | LFO 3 Fade | - | ❌ unmapped |  |
| 194 | LFO 3 Keytrack | - | ❌ unmapped |  |

## Envelopes (Filter/Amp/Env3/Env4) (SDATA 195–244)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 196 | Filter Envelope Mode | - | ❌ unmapped | Global/System/etc. |
| 199 | Filter Envelope Attack | Filter1Env* + Filter2Env* | ⚠️ Abweichung | Blofeld: EINE Filter-Env fuer F1+F2; Iridium: getrennte F1/F2-Envs -> beide gesetzt |
| 200 | Filter Envelope Attack Level | - | ❌ unmapped | Global/System/etc. |
| 201 | Filter Envelope Decay | Filter1Env* + Filter2Env* | ⚠️ Abweichung | Blofeld: EINE Filter-Env fuer F1+F2; Iridium: getrennte F1/F2-Envs -> beide gesetzt |
| 202 | Filter Envelope Sustain | Filter1Env* + Filter2Env* | ⚠️ Abweichung | Blofeld: EINE Filter-Env fuer F1+F2; Iridium: getrennte F1/F2-Envs -> beide gesetzt |
| 203 | Filter Envelope Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 204 | Filter Envelope Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 205 | Filter Envelope Release | Filter1Env* + Filter2Env* | ⚠️ Abweichung | Blofeld: EINE Filter-Env fuer F1+F2; Iridium: getrennte F1/F2-Envs -> beide gesetzt |
| 208 | Amplifier Envelope Mode | - | ❌ unmapped | Global/System/etc. |
| 211 | Amplifier Envelope Attack | AmpEnv* | ✅ direkt | norm |
| 212 | Amplifier Envelope Attack Level | - | ❌ unmapped | Global/System/etc. |
| 213 | Amplifier Envelope Decay | AmpEnv* | ✅ direkt | norm |
| 214 | Amplifier Envelope Sustain | AmpEnv* | ✅ direkt | norm |
| 215 | Amplifier Envelope Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 216 | Amplifier Envelope Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 217 | Amplifier Envelope Release | AmpEnv* | ✅ direkt | norm |
| 220 | Envelope 3 Mode | - | ❌ unmapped | Global/System/etc. |
| 223 | Envelope 3 Attack | FreeEnv1/2* | ✅ direkt | norm |
| 224 | Envelope 3 Attack Level | - | ❌ unmapped | Global/System/etc. |
| 225 | Envelope 3 Decay | FreeEnv1/2* | ✅ direkt | norm |
| 226 | Envelope 3 Sustain | FreeEnv1/2* | ✅ direkt | norm |
| 227 | Envelope 3 Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 228 | Envelope 3 Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 229 | Envelope 3 Release | FreeEnv1/2* | ✅ direkt | norm |
| 232 | Envelope 4 Mode | - | ❌ unmapped | Global/System/etc. |
| 235 | Envelope 4 Attack | FreeEnv1/2* | ✅ direkt | norm |
| 236 | Envelope 4 Attack Level | - | ❌ unmapped | Global/System/etc. |
| 237 | Envelope 4 Decay | FreeEnv1/2* | ✅ direkt | norm |
| 238 | Envelope 4 Sustain | FreeEnv1/2* | ✅ direkt | norm |
| 239 | Envelope 4 Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 240 | Envelope 4 Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 241 | Envelope 4 Release | FreeEnv1/2* | ✅ direkt | norm |

## Modifier (SDATA 245–260)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 245 | Modifier 1 Source A | - | ❌ unmapped |  |
| 246 | Modifier 1 Source B | - | ❌ unmapped |  |
| 247 | Modifier 1 Operation | - | ❌ unmapped |  |
| 248 | Modifier 1 Constant | - | ❌ unmapped |  |
| 249 | Modifier 2 Source A | - | ❌ unmapped |  |
| 250 | Modifier 2 Source B | - | ❌ unmapped |  |
| 251 | Modifier 2 Operation | - | ❌ unmapped |  |
| 252 | Modifier 2 Constant | - | ❌ unmapped |  |
| 253 | Modifier 3 Source A | - | ❌ unmapped |  |
| 254 | Modifier 3 Source B | - | ❌ unmapped |  |
| 255 | Modifier 3 Operation | - | ❌ unmapped |  |
| 256 | Modifier 3 Constant | - | ❌ unmapped |  |
| 257 | Modifier 4 Source A | - | ❌ unmapped |  |
| 258 | Modifier 4 Source B | - | ❌ unmapped |  |
| 259 | Modifier 4 Operation | - | ❌ unmapped |  |
| 260 | Modifier 4 Constant | - | ❌ unmapped |  |

## Modulation (16 Slots) (SDATA 261–308)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 261 | Modulation 1 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 262 | Modulation 1 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 263 | Modulation 1 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 264 | Modulation 2 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 265 | Modulation 2 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 266 | Modulation 2 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 267 | Modulation 3 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 268 | Modulation 3 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 269 | Modulation 3 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 270 | Modulation 4 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 271 | Modulation 4 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 272 | Modulation 4 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 273 | Modulation 5 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 274 | Modulation 5 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 275 | Modulation 5 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 276 | Modulation 6 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 277 | Modulation 6 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 278 | Modulation 6 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 279 | Modulation 7 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 280 | Modulation 7 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 281 | Modulation 7 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 282 | Modulation 8 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 283 | Modulation 8 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 284 | Modulation 8 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 285 | Modulation 9 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 286 | Modulation 9 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 287 | Modulation 9 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 288 | Modulation 10 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 289 | Modulation 10 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 290 | Modulation 10 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 291 | Modulation 11 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 292 | Modulation 11 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 293 | Modulation 11 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 294 | Modulation 12 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 295 | Modulation 12 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 296 | Modulation 12 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 297 | Modulation 13 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 298 | Modulation 13 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 299 | Modulation 13 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 300 | Modulation 14 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 301 | Modulation 14 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 302 | Modulation 14 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 303 | Modulation 15 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 304 | Modulation 15 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 305 | Modulation 15 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 306 | Modulation 16 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 307 | Modulation 16 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |
| 308 | Modulation 16 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 Näherung | Press-Kombis -> After Touch; Amount bipolar um 0.5 zentriert; 'On PW/Wave' -> WTn Position (Wavetable-Osc) bzw. WFn Warp (Waveform) |

## Arpeggiator / Pattern (SDATA 309–382)

| SDATA | Blofeld-Parameter | Iridium-qpat-Ziel | Status | Abweichung / Bemerkung |
|---|---|---|---|---|
| 311 | Arpeggiator Mode | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 312 | Arpeggiator Pattern | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 314 | Arpeggiator Clock | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 315 | Arpeggiator Length | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 316 | Arpeggiator Octave | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 317 | Arpeggiator Direction | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 318 | Arpeggiator Sort Order | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 319 | Arpeggiator Velocity | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 320 | Arpeggiator Timing Factor | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 322 | Arpeggiator Ptn Reset | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 323 | Arpeggiator Ptn Length | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 326 | Arpeggiator Tempo | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 327 | Arp Pattern Step/Glide/Accent 1 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 328 | Arp Pattern Step/Glide/Accent 2 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 329 | Arp Pattern Step/Glide/Accent 3 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 330 | Arp Pattern Step/Glide/Accent 4 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 331 | Arp Pattern Step/Glide/Accent 5 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 332 | Arp Pattern Step/Glide/Accent 6 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 333 | Arp Pattern Step/Glide/Accent 7 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 334 | Arp Pattern Step/Glide/Accent 8 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 335 | Arp Pattern Step/Glide/Accent 9 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 336 | Arp Pattern Step/Glide/Accent 10 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 337 | Arp Pattern Step/Glide/Accent 11 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 338 | Arp Pattern Step/Glide/Accent 12 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 339 | Arp Pattern Step/Glide/Accent 13 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 340 | Arp Pattern Step/Glide/Accent 14 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 341 | Arp Pattern Step/Glide/Accent 15 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 342 | Arp Pattern Step/Glide/Accent 16 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 343 | Arp Pattern Timing/Length 1 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 344 | Arp Pattern Timing/Length 2 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 345 | Arp Pattern Timing/Length 3 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 346 | Arp Pattern Timing/Length 4 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 347 | Arp Pattern Timing/Length 5 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 348 | Arp Pattern Timing/Length 6 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 349 | Arp Pattern Timing/Length 7 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 350 | Arp Pattern Timing/Length 8 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 351 | Arp Pattern Timing/Length 9 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 352 | Arp Pattern Timing/Length 10 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 353 | Arp Pattern Timing/Length 11 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 354 | Arp Pattern Timing/Length 12 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 355 | Arp Pattern Timing/Length 13 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 356 | Arp Pattern Timing/Length 14 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 357 | Arp Pattern Timing/Length 15 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 358 | Arp Pattern Timing/Length 16 | - | ❌ unmapped | gesamter Arpeggiator (Mode/Pattern/Steps/Tempo) nicht gemappt |
| 379 | Category | - | ❌ unmapped | Global/System/etc. |

## Statistik

- ✅ direkt: 37
- 🟡 Näherung: 70
- ⚠️ Abweichung: 9
- ❌ unmapped: 174
- **gesamt: 290 Blofeld-Parameter**

