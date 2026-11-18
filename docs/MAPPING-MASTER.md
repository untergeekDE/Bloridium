# Master table: Blofeld parameters -> Iridium qpat (mapping status)

Created: 2026-11-09. Based on: `bloridium/blofeld_dump.py` (SDATA table, spec 3.1) + `bloridium/qpat_map.py`.
Reference sound: A043 "SH Power" (129 mapped / 75 unmapped of 290 set params after the 2026-11-18 rebuild).

**2026-11-18 rebuild (live-verified decisions + enum scans; device exports qpat v14):**
- Aftertouch: **Poly AT** — `AfterTouchDoPoly=1.0` (user, live). Matrix src "After Touch"=**17.0**.
  Enum values = OS 4.1.0b2 **runtime** values (param-info, 2026-11-18); qpat file values are read
  1:1 (controlled load test) — see `docs/refs/quir_runtime_enums_2026-11-18.md`.
- `Osc 2 Sync to O3` -> `Osc2WaveformSync=1.0`; serial F2 mods -> DF Amount(95)/DF Color(96);
  FX mix key by mapped type + FX params (spec 5.2-5.9); detune centered at 0.5;
  Amp Mod / Osc Pitch Mod -> matrix slots; new v14 dsts: AmpEnv Attack=109, LFO1-3 Speed=145-147.
- Still open (live clarification, see `docs/superpowers/plans/2026-11-18-converter-rebuild-polyat.md`):
  amt_bipolar divisor, FinePitch cent scale, LFO free-speed Hz, AE Decay/Sustain/Release + FE Release
  + F1/F2 Drive/Pan dsts (need `param-info 2480`), WT bridge by CLAP, qpat version v14 vs v15 on device.

**PC/Favorites mapping on the Iridium (which sound on which MIDI PC): see `docs/IRIDIUM-FAVORITES-MAP.md`**
(mido PC = display "MIDI" - 2; MIDI 100-106 = calib test sounds, 107-115 = the 9 converted sounds).

Legend: ✅ direct (1:1) · 🟡 approximation · ⚠️ mapped with known deviation · ❌ unmapped

## Oscillators (Osc 1-3) (SDATA 0-56)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 1 | Osc 1 Octave | OscNCoarsePitch | 🟡 approximation | reconstructed from raw SDATA values (64 = center) |
| 2 | Osc 1 Semitone | OscNCoarsePitch | 🟡 approximation | reconstructed from raw SDATA values (64 = center) |
| 3 | Osc 1 Detune | OscNFinePitch | ⚠️ deviation | centered `0.5+(raw-64)/254` (was norm(); cent scale live-TODO) |
| 4 | Osc 1 Bend Range | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 5 | Osc 1 Keytrack | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 6 | Osc 1 FM Source | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 7 | Osc 1 FM Amount | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 8 | Osc 1 Shape | OscNType + OscNWaveformShape | 🟡 approximation | VA shapes direct; wavetables -> Type + WavetableTable (bridge, e.g. MalletSyn=2) + WavetablePosition (from pulsewidth) + Brilliance; Spectrum unmapped |
| 9 | Osc 1 Pulsewidth | OscNWaveformPW | ✅ direct | Waveform mode -> WaveformPW; wavetable mode -> WavetablePosition (Blofeld 'PW/Wave') |
| 10 | Osc 1 PWM Source | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 11 | Osc 1 PWM Amount | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 14 | Osc 1 Limit WT | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 16 | Osc 1 Brilliance | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 17 | Osc 2 Octave | OscNCoarsePitch | 🟡 approximation | reconstructed from raw SDATA values (64 = center) |
| 18 | Osc 2 Semitone | OscNCoarsePitch | 🟡 approximation | reconstructed from raw SDATA values (64 = center) |
| 19 | Osc 2 Detune | OscNFinePitch | ⚠️ deviation | centered `0.5+(raw-64)/254` (was norm(); cent scale live-TODO) |
| 20 | Osc 2 Bend Range | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 21 | Osc 2 Keytrack | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 22 | Osc 2 FM Source | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 23 | Osc 2 FM Amount | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 24 | Osc 2 Shape | OscNType + OscNWaveformShape | 🟡 approximation | VA shapes direct; wavetables -> Type + WavetableTable (bridge, e.g. MalletSyn=2) + WavetablePosition (from pulsewidth) + Brilliance; Spectrum unmapped |
| 25 | Osc 2 Pulsewidth | OscNWaveformPW | ✅ direct | Waveform mode -> WaveformPW; wavetable mode -> WavetablePosition (Blofeld 'PW/Wave') |
| 26 | Osc 2 PWM Source | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 27 | Osc 2 PWM Amount | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 30 | Osc 2 Limit WT | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 32 | Osc 2 Brilliance | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 33 | Osc 3 Octave | OscNCoarsePitch | 🟡 approximation | reconstructed from raw SDATA values (64 = center) |
| 34 | Osc 3 Semitone | OscNCoarsePitch | 🟡 approximation | reconstructed from raw SDATA values (64 = center) |
| 35 | Osc 3 Detune | OscNFinePitch | ⚠️ deviation | centered `0.5+(raw-64)/254` (was norm(); cent scale live-TODO) |
| 36 | Osc 3 Bend Range | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 37 | Osc 3 Keytrack | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 38 | Osc 3 FM Source | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 39 | Osc 3 FM Amount | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 40 | Osc 3 Shape | OscNType + OscNWaveformShape | 🟡 approximation | VA shapes direct; wavetables -> Type + WavetableTable (bridge, e.g. MalletSyn=2) + WavetablePosition (from pulsewidth) + Brilliance; Spectrum unmapped |
| 41 | Osc 3 Pulsewidth | OscNWaveformPW | ✅ direct | Waveform mode -> WaveformPW; wavetable mode -> WavetablePosition (Blofeld 'PW/Wave') |
| 42 | Osc 3 PWM Source | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 43 | Osc 3 PWM Amount | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 46 | Osc 3 Limit WT | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 48 | Osc 3 Brilliance | - | ❌ unmapped | FM/PWM live in Kernels/mod matrix on the Iridium, no 1:1 |
| 49 | Osc 2 Sync to O3 | Osc2WaveformSync | 🟡 approximation | 1.0 = Sync on (A071/A008) |
| 50 | Osc Pitch Source | Matrix-Slot -> Pitch | 🟡 approximation | 2026-11-18: extra matrix slot (e.g. A008 LFO1*MW -> Wheel) |
| 51 | Osc Pitch Amount | MatrixAmount | 🟡 approximation | amt_bipolar |
| 53 | Glide | - | ❌ unmapped | Global/System/etc. |
| 56 | Glide Mode | - | ❌ unmapped | Global/System/etc. |

## Mixer (SDATA 57-72)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 57 | Glide Rate | GlideRate | 🟡 approximation | time-calibrated (exponential, anchors in `qpat_map.py`: raw 20 = norm 0.15 = 0.045 s; Iridium norm 0.378 = 0.29 s display; raw 127 ≈ 5 s). Linear norm() set too high (A073 raw 48: 0.378/0.29 s instead of correct ~0.30/~0.15 s) |
| 58 | Allocation/Unisono | UnisonoCount + UnisonoDetune | 🟡 approximation | bitfield decoded (count = bits 5-7) |
| 59 | Unisono Detune | UnisonoDetune | ✅ direct | norm |
| 61 | Mixer Osc 1 Level | OscNVol | ✅ direct | norm raw/127 |
| 62 | Mixer Osc 1 Balance | OscNPan | ⚠️ deviation | Blofeld Balance = F1/F2 share, Iridium Pan = stereo -> semantics differ |
| 63 | Mixer Osc 2 Level | OscNVol | ✅ direct | norm raw/127 |
| 64 | Mixer Osc 2 Balance | OscNPan | ⚠️ deviation | Blofeld Balance = F1/F2 share, Iridium Pan = stereo -> semantics differ |
| 65 | Mixer Osc 3 Level | OscNVol | ✅ direct | norm raw/127 |
| 66 | Mixer Osc 3 Balance | OscNPan | ⚠️ deviation | Blofeld Balance = F1/F2 share, Iridium Pan = stereo -> semantics differ |
| 67 | Mixer Noise Level | - | ❌ unmapped | no direct qpat key (Particle/Resonator noise) |
| 68 | Mixer Noise Balance | - | ❌ unmapped | no direct qpat key (Particle/Resonator noise) |
| 69 | Mixer Noise Colour | - | ❌ unmapped | no direct qpat key (Particle/Resonator noise) |
| 71 | Mixer RingMod Level | RingmodOsc12 | ✅ direct | only O1->O2; O1->O3 (CC75) unmapped |
| 72 | Mixer RingMod Balance | RingmodOsc12 | ✅ direct | only O1->O2; O1->O3 (CC75) unmapped |

## Filter 1/2 + Routing (SDATA 73-117)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 77 | Filter 1 Type | Filter12Type | 🟡 approximation | Enum table v14; Notch/Comb -> BP approximation |
| 78 | Filter 1 Cutoff | Filter1CutOff | ✅ direct | norm; device: no CC (only qpat/CC0 via .mimap) |
| 80 | Filter 1 Resonance | Filter1Reso | ✅ direct | norm |
| 81 | Filter 1 Drive | - | ❌ unmapped | Drive -> FX Drive possible, Pan -> DigiFormer PAN (CC78) |
| 82 | Filter 1 Drive Curve | - | ❌ unmapped | Global/System/etc. |
| 86 | Filter 1 Keytrack | Filter1Keytrack | ✅ direct | norm(raw): Blofeld 0..127 = -200%..+196% (offset binary, 64=0%), Iridium 0..1 = -200%..+200% (0.5=0%); old (kt-64)/64 gave -200% at 64 |
| 87 | Filter 1 Env Amount | FilterNEnvAmount | ✅ direct | norm |
| 88 | Filter 1 Env Velocity | FilterNVeloAmount | ✅ direct | norm |
| 89 | Filter 1 Mod Source | Matrix-Slot -> Filter1 Cutoff | 🟡 approximation | direct filter mod as extra matrix slot (dst 100) |
| 90 | Filter 1 Mod Amount | MatrixAmount | 🟡 approximation | amt_bipolar |
| 91 | Filter 1 FM Source | - | ❌ unmapped | Drive -> FX Drive possible, Pan -> DigiFormer PAN (CC78) |
| 92 | Filter 1 FM Amount | - | ❌ unmapped | Drive -> FX Drive possible, Pan -> DigiFormer PAN (CC78) |
| 93 | Filter 1 Pan | - | ❌ unmapped | Drive -> FX Drive possible, Pan -> DigiFormer PAN (CC78) |
| 94 | Filter 1 Pan Source | - | ❌ unmapped | Global/System/etc. |
| 95 | Filter 1 Pan Amount | - | ❌ unmapped | Global/System/etc. |
| 97 | Filter 2 Type | DigiFormerType | 🟡 approximation | Blofeld F2 model -> Former model (Nave/PPG/Largo/SVF), not identical |
| 98 | Filter 2 Cutoff | DigiFormerAmount + Filter2CutOff | 🟡 approximation | Cutoff -> Former Amount (approximation), F2 stage itself Off |
| 100 | Filter 2 Resonance | DigiFormerColor + Filter2Reso | 🟡 approximation | Reso -> Former Color |
| 101 | Filter 2 Drive | - | ❌ unmapped |  |
| 102 | Filter 2 Drive Curve | - | ❌ unmapped | Global/System/etc. |
| 106 | Filter 2 Keytrack | Filter2Keytrack | ✅ direct | norm(raw) like F1 keytrack (see 86) |
| 107 | Filter 2 Env Amount | FilterNEnvAmount | ✅ direct | norm |
| 108 | Filter 2 Env Velocity | FilterNVeloAmount | ✅ direct | norm |
| 109 | Filter 2 Mod Source | Matrix-Slot -> DF Amount (serial) / Filter2 Cutoff (parallel) | 🟡 approximation | serial: F2 lives in the DigiFormer -> dst 95 (P1-2, 2026-11-18) |
| 110 | Filter 2 Mod Amount | MatrixAmount | 🟡 approximation | amt_bipolar |
| 111 | Filter 2 FM Source | - | ❌ unmapped |  |
| 112 | Filter 2 FM Amount | - | ❌ unmapped |  |
| 113 | Filter 2 Pan | - | ❌ unmapped |  |
| 114 | Filter 2 Pan Source | - | ❌ unmapped | Global/System/etc. |
| 115 | Filter 2 Pan Amount | - | ❌ unmapped | Global/System/etc. |
| 117 | Filter Routing | FilterLink (Linked) + Filter2State Off | 🟡 approximation | serial -> Linked; F2 Bypass -> F2 Off + Former Bypass (bleed fix) |

## Effects (FX1/FX2 type/mix) (SDATA 118-127)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 121 | Amplifier Volume | MainVolume | ✅ direct | norm |
| 122 | Amplifier Velocity | Matrix-Slot Velocity->Volume (AmpVeloAmount=0) | 🟡 approximation | AmpVelo barely works on the device (CC17 ~0.4 dB); Vel->Volume in matrix, amount bipolar |
| 123 | Amplifier Mod Source | Matrix-Slot -> Volume | 🟡 approximation | 2026-11-18: extra matrix slot (A008 AmpEnv, others LFO3) |
| 124 | Amplifier Mod Amount | MatrixAmount | 🟡 approximation | amt_bipolar |

## Effect parameters (SDATA 128-159)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 128 | Effect 1 Type | FX1Type | 🟡 approximation | Enum v14; Triple FX -> Chorus; watch enum shift (v8/v14/v15, enum scan) |
| 129 | Effect 1 Mix | DryWet key of the MAPPED type | ✅ direct | 2026-11-18: by type not slot (Chorus->ChorusDryWet, Delay->DelayDryWet, Phaser/Flanger/Drive likewise; Reverb -> matrix slot Constant->FX DryWet) |
| 130-143 | Effect 1 Parameter 1-14 | per-FX keys | 🟡 approximation | 2026-11-18 per spec 5.2-5.9: Chorus Speed/Depth (p1/p2), Flanger +Feedback p5, Phaser +p5/p6 Center, Overdrive Drive p2/PostGain p3 -> DriveAmount/DriveGain, Clk.Delay Feedback p5/Cutoff p6/Length p11 -> DelayFeed/DelayHiCut/DelaySync+Sync, Reverb Shape/Decay -> ReverbColor/ReverbTime |
| 144 | Effect 2 Type | FX2Type | 🟡 approximation | as FX1 |
| 145 | Effect 2 Mix | DryWet key of the MAPPED type | ✅ direct | as 129 |
| 146-159 | Effect 2 Parameter 1-14 | per-FX keys | 🟡 approximation | as 130-143 (Delay: Length p4 free time not mapped; Reverb params unmapped) |

## LFO 1-3 (SDATA 160-194)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 160 | LFO 1 Shape | - | ❌ unmapped |  |
| 161 | LFO 1 Speed | LfoN Speed/Sync/SyncRatio | 🟡 approximation | Key is called Lfo1Speed (not LFO1Speed!); Sync=1 -> clock index (4.6, bars) -> SyncRatio (beats), else free Speed=norm (unchecked) |
| 163 | LFO 1 Sync | Lfo1Sync | ✅ direct | on -> SyncRatio from clock index; else free |
| 164 | LFO 1 Clocked | - | ❌ unmapped | Global/System/etc. |
| 165 | LFO 1 Start Phase | - | ❌ unmapped | Global/System/etc. |
| 166 | LFO 1 Delay | - | ❌ unmapped |  |
| 167 | LFO 1 Fade | - | ❌ unmapped |  |
| 170 | LFO 1 Keytrack | - | ❌ unmapped |  |
| 172 | LFO 2 Shape | - | ❌ unmapped |  |
| 173 | LFO 2 Speed | LFO NSpeed | ✅ direct | Clock-Index norm |
| 175 | LFO 2 Sync | - | ❌ unmapped |  |
| 176 | LFO 2 Clocked | - | ❌ unmapped | Global/System/etc. |
| 177 | LFO 2 Start Phase | - | ❌ unmapped | Global/System/etc. |
| 178 | LFO 2 Delay | - | ❌ unmapped |  |
| 179 | LFO 2 Fade | - | ❌ unmapped |  |
| 182 | LFO 2 Keytrack | - | ❌ unmapped |  |
| 184 | LFO 3 Shape | - | ❌ unmapped |  |
| 185 | LFO 3 Speed | LFO NSpeed | ✅ direct | Clock-Index norm |
| 187 | LFO 3 Sync | - | ❌ unmapped |  |
| 188 | LFO 3 Clocked | - | ❌ unmapped | Global/System/etc. |
| 189 | LFO 3 Start Phase | - | ❌ unmapped | Global/System/etc. |
| 190 | LFO 3 Delay | - | ❌ unmapped |  |
| 191 | LFO 3 Fade | - | ❌ unmapped |  |
| 194 | LFO 3 Keytrack | - | ❌ unmapped |  |

## Envelopes (Filter/Amp/Env3/Env4) (SDATA 195-244)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 196 | Filter Envelope Mode | - | ❌ unmapped | Global/System/etc. |
| 199 | Filter Envelope Attack | Filter1Env* + Filter2Env* | ⚠️ deviation | Blofeld: ONE filter env for F1+F2; Iridium: separate F1/F2 envs -> both set |
| 200 | Filter Envelope Attack Level | - | ❌ unmapped | Global/System/etc. |
| 201 | Filter Envelope Decay | Filter1Env* + Filter2Env* | ⚠️ deviation | Blofeld: ONE filter env for F1+F2; Iridium: separate F1/F2 envs -> both set |
| 202 | Filter Envelope Sustain | Filter1Env* + Filter2Env* | ⚠️ deviation | Blofeld: ONE filter env for F1+F2; Iridium: separate F1/F2 envs -> both set |
| 203 | Filter Envelope Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 204 | Filter Envelope Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 205 | Filter Envelope Release | Filter1Env* + Filter2Env* | ⚠️ deviation | Blofeld: ONE filter env for F1+F2; Iridium: separate F1/F2 envs -> both set |
| 208 | Amplifier Envelope Mode | - | ❌ unmapped | Global/System/etc. |
| 211 | Amplifier Envelope Attack | AmpEnv* | ✅ direct | norm |
| 212 | Amplifier Envelope Attack Level | - | ❌ unmapped | Global/System/etc. |
| 213 | Amplifier Envelope Decay | AmpEnv* | ✅ direct | norm |
| 214 | Amplifier Envelope Sustain | AmpEnv* | ✅ direct | norm |
| 215 | Amplifier Envelope Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 216 | Amplifier Envelope Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 217 | Amplifier Envelope Release | AmpEnv* | ✅ direct | norm |
| 220 | Envelope 3 Mode | - | ❌ unmapped | Global/System/etc. |
| 223 | Envelope 3 Attack | FreeEnv1/2* | ✅ direct | norm |
| 224 | Envelope 3 Attack Level | - | ❌ unmapped | Global/System/etc. |
| 225 | Envelope 3 Decay | FreeEnv1/2* | ✅ direct | norm |
| 226 | Envelope 3 Sustain | FreeEnv1/2* | ✅ direct | norm |
| 227 | Envelope 3 Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 228 | Envelope 3 Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 229 | Envelope 3 Release | FreeEnv1/2* | ✅ direct | norm |
| 232 | Envelope 4 Mode | - | ❌ unmapped | Global/System/etc. |
| 235 | Envelope 4 Attack | FreeEnv1/2* | ✅ direct | norm |
| 236 | Envelope 4 Attack Level | - | ❌ unmapped | Global/System/etc. |
| 237 | Envelope 4 Decay | FreeEnv1/2* | ✅ direct | norm |
| 238 | Envelope 4 Sustain | FreeEnv1/2* | ✅ direct | norm |
| 239 | Envelope 4 Decay 2 | - | ❌ unmapped | Global/System/etc. |
| 240 | Envelope 4 Sustain 2 | - | ❌ unmapped | Global/System/etc. |
| 241 | Envelope 4 Release | FreeEnv1/2* | ✅ direct | norm |

## Modifier (SDATA 245-260)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
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

## Modulation (16 slots) (SDATA 261-308)

2026-11-18 notes for all rows: src "After Touch" = **17.0** (Poly AT decision, see header); in serial
routing dst "F2 Cutoff"/"F2 Reson." are remapped to **DF Amount (95)** / **DF Color (96)** (P1-2);
new dsts mapped: "AE Attack" -> AmpEnv Attack (109), "LFO1-3Speed" -> LFO1-3 Speed (145-147).
Still unmapped dsts (need live `param-info 2480` for v14 enum values): AE Decay/Sustain/Release,
FE Release, F1/F2 Drive/Pan/FM, RMod Level/Bal., NoiseLevel/Bal., O1-3 FM/Balance, M1-4 Amount;
srcs without equivalent: Control W-Z, Unisono V., Modifier 1-4, Sustain/Foot/Breath.

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 261 | Modulation 1 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 262 | Modulation 1 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 263 | Modulation 1 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 264 | Modulation 2 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 265 | Modulation 2 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 266 | Modulation 2 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 267 | Modulation 3 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 268 | Modulation 3 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 269 | Modulation 3 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 270 | Modulation 4 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 271 | Modulation 4 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 272 | Modulation 4 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 273 | Modulation 5 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 274 | Modulation 5 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 275 | Modulation 5 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 276 | Modulation 6 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 277 | Modulation 6 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 278 | Modulation 6 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 279 | Modulation 7 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 280 | Modulation 7 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 281 | Modulation 7 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 282 | Modulation 8 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 283 | Modulation 8 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 284 | Modulation 8 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 285 | Modulation 9 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 286 | Modulation 9 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 287 | Modulation 9 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 288 | Modulation 10 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 289 | Modulation 10 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 290 | Modulation 10 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 291 | Modulation 11 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 292 | Modulation 11 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 293 | Modulation 11 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 294 | Modulation 12 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 295 | Modulation 12 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 296 | Modulation 12 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 297 | Modulation 13 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 298 | Modulation 13 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 299 | Modulation 13 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 300 | Modulation 14 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 301 | Modulation 14 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 302 | Modulation 14 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 303 | Modulation 15 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 304 | Modulation 15 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 305 | Modulation 15 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 306 | Modulation 16 Source | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 307 | Modulation 16 Destination | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |
| 308 | Modulation 16 Amount | Matrix-Slots (Src/Dst/Amount/OnOff) | 🟡 approximation | Press combos -> After Touch; amount bipolar centered at 0.5; 'On PW/Wave' -> WTn Position (wavetable osc) or WFn Warp (waveform) |

## Arpeggiator / pattern (SDATA 309-382)

| SDATA | Blofeld parameter | Iridium qpat target | Status | Deviation / Notes |
|---|---|---|---|---|
| 311 | Arpeggiator Mode | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 312 | Arpeggiator Pattern | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 314 | Arpeggiator Clock | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 315 | Arpeggiator Length | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 316 | Arpeggiator Octave | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 317 | Arpeggiator Direction | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 318 | Arpeggiator Sort Order | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 319 | Arpeggiator Velocity | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 320 | Arpeggiator Timing Factor | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 322 | Arpeggiator Ptn Reset | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 323 | Arpeggiator Ptn Length | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 326 | Arpeggiator Tempo | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 327 | Arp Pattern Step/Glide/Accent 1 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 328 | Arp Pattern Step/Glide/Accent 2 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 329 | Arp Pattern Step/Glide/Accent 3 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 330 | Arp Pattern Step/Glide/Accent 4 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 331 | Arp Pattern Step/Glide/Accent 5 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 332 | Arp Pattern Step/Glide/Accent 6 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 333 | Arp Pattern Step/Glide/Accent 7 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 334 | Arp Pattern Step/Glide/Accent 8 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 335 | Arp Pattern Step/Glide/Accent 9 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 336 | Arp Pattern Step/Glide/Accent 10 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 337 | Arp Pattern Step/Glide/Accent 11 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 338 | Arp Pattern Step/Glide/Accent 12 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 339 | Arp Pattern Step/Glide/Accent 13 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 340 | Arp Pattern Step/Glide/Accent 14 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 341 | Arp Pattern Step/Glide/Accent 15 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 342 | Arp Pattern Step/Glide/Accent 16 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 343 | Arp Pattern Timing/Length 1 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 344 | Arp Pattern Timing/Length 2 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 345 | Arp Pattern Timing/Length 3 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 346 | Arp Pattern Timing/Length 4 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 347 | Arp Pattern Timing/Length 5 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 348 | Arp Pattern Timing/Length 6 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 349 | Arp Pattern Timing/Length 7 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 350 | Arp Pattern Timing/Length 8 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 351 | Arp Pattern Timing/Length 9 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 352 | Arp Pattern Timing/Length 10 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 353 | Arp Pattern Timing/Length 11 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 354 | Arp Pattern Timing/Length 12 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 355 | Arp Pattern Timing/Length 13 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 356 | Arp Pattern Timing/Length 14 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 357 | Arp Pattern Timing/Length 15 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 358 | Arp Pattern Timing/Length 16 | - | ❌ unmapped | entire arpeggiator (mode/pattern/steps/tempo) not mapped |
| 379 | Category | - | ❌ unmapped | Global/System/etc. |

## Statistics

- ✅ direct: 37
- 🟡 approximation: 70
- ⚠️ deviation: 9
- ❌ unmapped: 174
- **total: 290 Blofeld parameters**

