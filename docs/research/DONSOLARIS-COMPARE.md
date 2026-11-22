# Don Solaris "Analog Voltage" — Blofeld vs Iridium (namensgleiche Sounds)

Source: `dumps/DonSolarisAnalogVoltage/Single/*.mid` (Blofeld SNDD SysEx) vs `dumps/export-005/*.qpat` (Iridium, v8/v9).
Blofeld values: raw 0..127 (+ label); Iridium: norm 0..1 (+ display). Enums compared via display (version-independent).

## 'Michael Cretu'  (BLO `124-Michael_Cretu.mid` ↔ IRR v9 `02033-Michael Cretu.qpat`)

| Blofeld-Parameter | Blofeld-Wert | Iridium-Key | Iridium-Wert |
|---|---|---|---|
| Amplifier Envelope Attack | 70 | `AmpEnvAttack` | 0.5132 ('') |
| Amplifier Envelope Decay | 52 | `AmpEnvDecay` | 0.7000 ('') |
| Amplifier Envelope Release | 70 | `AmpEnvRelease` | 0.5171 ('') |
| Amplifier Envelope Sustain | 127 | `AmpEnvSustain` | 1.0000 ('') |
| Amplifier Velocity | 117 | `AmpVeloAmount` | 0.5000 ('') |
| Amplifier Volume | 86 | `MainVolume` | 1.0000 ('') |
| Effect 1 Mix | 0 | `ChorusDryWet` | 0.5000 ('') |
| Effect 1 Type | Chorus | `FX1Type` | 2.0000 ('Chorus') |
| Effect 2 Mix | 60 | `DelayDryWet` | 0.5000 ('') |
| Effect 2 Type | Clk.Delay | `FX2Type` | 4.0000 ('Delay') |
| Filter 1 Cutoff | 127 | `Filter1CutOff` | 1.0000 ('') |
| Filter 1 Env Amount | 64 | `Filter1EnvAmount` | 0.5000 ('') |
| Filter 1 Keytrack | 64 | `Filter1Keytrack` | 0.5000 ('') |
| Filter 1 Resonance | 0 | `Filter1Reso` | 0.0000 ('') |
| Filter 1 Type | Bypass | `Filter12Type` | 0.0000 ('12dB LP') |
| Filter 2 Cutoff | 127 | `Filter2CutOff` | 0.0000 ('') |
| Filter 2 Env Amount | 64 | `Filter2EnvAmount` | 0.5000 ('') |
| Filter 2 Resonance | 0 | `Filter2Reso` | 0.0000 ('') |
| Filter 2 Type | Bypass | `DigiFormerType` | 0.0000 ('Bypass') |
| Filter Envelope Attack | 0 | `Filter1EnvAttack` | 0.0100 ('') |
| Filter Envelope Decay | 50 | `Filter1EnvDecay` | 0.7000 ('') |
| Filter Envelope Release | 0 | `Filter1EnvRelease` | 0.5000 ('') |
| Filter Envelope Sustain | 0 | `Filter1EnvSustain` | 0.1000 ('') |
| Filter Routing | 0 | `FilterLink` | 0.0000 ('Single') |
| Glide Rate | 20 | `GlideRate` | 0.1500 ('') |
| Mixer Osc 1 Balance | 0 | `Osc1Pan` | 0.5000 ('') |
| Mixer Osc 1 Level | 60 | `Osc1Vol` | 0.5054 ('') |
| Mixer Osc 2 Balance | 0 | `Osc2Pan` | 0.5000 ('') |
| Mixer Osc 2 Level | 60 | `Osc2Vol` | 0.5200 ('') |
| Mixer Osc 3 Balance | 0 | `Osc3Pan` | 0.5000 ('') |
| Mixer Osc 3 Level | 60 | `Osc3Vol` | 0.0000 ('') |
| Osc 1 Shape | Sine | `Osc1Type` | 1.0000 ('Waveform') |
| Osc 1 Shape | Sine | `Osc1WaveformShape` | 1.0000 ('Sine') |
| Osc 2 Shape | Sine | `Osc2Type` | 1.0000 ('Waveform') |
| Osc 2 Shape | Sine | `Osc2WaveformShape` | 1.0000 ('Sine') |
| Osc 3 Shape | Sine | `Osc3Type` | 5.0000 ('Off') |
| Osc 3 Shape | Sine | `Osc3WaveformShape` | 0.0000 ('Sawtooth') |

**Cutoff-Check:** Blofeld raw 127/127 = 1.0000 vs Iridium norm 1.0000 -> Faktor 1.000

## 'MonoPoly Bass'  (BLO `023-MonoPoly_Bass.mid` ↔ IRR v9 `02086-MonoPoly Bass.qpat`)

| Blofeld-Parameter | Blofeld-Wert | Iridium-Key | Iridium-Wert |
|---|---|---|---|
| Amplifier Envelope Attack | 0 | `AmpEnvAttack` | 0.0000 ('') |
| Amplifier Envelope Decay | 33 | `AmpEnvDecay` | 0.2385 ('') |
| Amplifier Envelope Release | 66 | `AmpEnvRelease` | 0.1251 ('') |
| Amplifier Envelope Sustain | 54 | `AmpEnvSustain` | 0.5836 ('') |
| Amplifier Velocity | 64 | `AmpVeloAmount` | 0.5000 ('') |
| Amplifier Volume | 127 | `MainVolume` | 1.0000 ('') |
| Effect 1 Mix | 0 | `ChorusDryWet` | 0.7500 ('') |
| Effect 1 Type | Chorus | `FX1Type` | 8.0000 ('Compressor') |
| Effect 2 Mix | 7 | `DelayDryWet` | 0.0000 ('') |
| Effect 2 Type | Bypass | `FX2Type` | 0.0000 ('Off') |
| Filter 1 Cutoff | 43 | `Filter1CutOff` | 0.1476 ('') |
| Filter 1 Env Amount | 85 | `Filter1EnvAmount` | 0.8149 ('') |
| Filter 1 Keytrack | 80 | `Filter1Keytrack` | 0.7500 ('') |
| Filter 1 Resonance | 50 | `Filter1Reso` | 0.3900 ('') |
| Filter 1 Type | LP 24dB | `Filter12Type` | 3.0000 ('24dB LP') |
| Filter 2 Cutoff | 127 | `Filter2CutOff` | 0.0000 ('') |
| Filter 2 Env Amount | 64 | `Filter2EnvAmount` | 0.5000 ('') |
| Filter 2 Resonance | 0 | `Filter2Reso` | 0.0000 ('') |
| Filter 2 Type | Bypass | `DigiFormerType` | 0.0000 ('Bypass') |
| Filter Envelope Attack | 0 | `Filter1EnvAttack` | 0.0000 ('') |
| Filter Envelope Decay | 72 | `Filter1EnvDecay` | 0.3431 ('') |
| Filter Envelope Release | 72 | `Filter1EnvRelease` | 0.0000 ('') |
| Filter Envelope Sustain | 0 | `Filter1EnvSustain` | 0.3069 ('') |
| Filter Routing | 0 | `FilterLink` | 0.0000 ('Single') |
| Glide Rate | 20 | `GlideRate` | 0.1500 ('') |
| Mixer Osc 1 Balance | 0 | `Osc1Pan` | 0.5000 ('') |
| Mixer Osc 1 Level | 127 | `Osc1Vol` | 1.0000 ('') |
| Mixer Osc 2 Balance | 0 | `Osc2Pan` | 0.5000 ('') |
| Mixer Osc 2 Level | 127 | `Osc2Vol` | 0.4897 ('') |
| Mixer Osc 3 Balance | 0 | `Osc3Pan` | 0.5000 ('') |
| Mixer Osc 3 Level | 127 | `Osc3Vol` | 0.0000 ('') |
| Osc 1 Shape | Saw | `Osc1Type` | 1.0000 ('Waveform') |
| Osc 1 Shape | Saw | `Osc1WaveformShape` | 3.0000 ('Square') |
| Osc 2 Shape | Saw | `Osc2Type` | 5.0000 ('Off') |
| Osc 2 Shape | Saw | `Osc2WaveformShape` | 3.0000 ('Square') |
| Osc 3 Shape | Saw | `Osc3Type` | 5.0000 ('Off') |
| Osc 3 Shape | Saw | `Osc3WaveformShape` | 0.0000 ('Sawtooth') |

**Cutoff-Check:** Blofeld raw 43/127 = 0.3386 vs Iridium norm 0.1476 -> Faktor 0.436

## 'Moog Lead'  (BLO `017-Moog_Lead.mid` ↔ IRR v9 `02111-Moog Lead.qpat`)

| Blofeld-Parameter | Blofeld-Wert | Iridium-Key | Iridium-Wert |
|---|---|---|---|
| Amplifier Envelope Attack | 0 | `AmpEnvAttack` | 0.0000 ('') |
| Amplifier Envelope Decay | 52 | `AmpEnvDecay` | 0.0000 ('') |
| Amplifier Envelope Release | 0 | `AmpEnvRelease` | 0.1065 ('') |
| Amplifier Envelope Sustain | 127 | `AmpEnvSustain` | 1.0000 ('') |
| Amplifier Velocity | 64 | `AmpVeloAmount` | 0.5000 ('') |
| Amplifier Volume | 100 | `MainVolume` | 1.0000 ('') |
| Effect 1 Mix | 0 | `ChorusDryWet` | 0.7500 ('') |
| Effect 1 Type | Chorus | `FX1Type` | 4.0000 ('Delay') |
| Effect 2 Mix | 0 | `DelayDryWet` | 0.0600 ('') |
| Effect 2 Type | Reverb | `FX2Type` | 8.0000 ('Compressor') |
| Filter 1 Cutoff | 66 | `Filter1CutOff` | 0.5191 ('') |
| Filter 1 Env Amount | 84 | `Filter1EnvAmount` | 0.7494 ('') |
| Filter 1 Keytrack | 96 | `Filter1Keytrack` | 0.7500 ('') |
| Filter 1 Resonance | 68 | `Filter1Reso` | 0.6041 ('') |
| Filter 1 Type | LP 24dB | `Filter12Type` | 3.0000 ('24dB LP') |
| Filter 2 Cutoff | 127 | `Filter2CutOff` | 0.0000 ('') |
| Filter 2 Env Amount | 64 | `Filter2EnvAmount` | 0.5000 ('') |
| Filter 2 Resonance | 0 | `Filter2Reso` | 0.0000 ('') |
| Filter 2 Type | Bypass | `DigiFormerType` | 0.0000 ('Bypass') |
| Filter Envelope Attack | 65 | `Filter1EnvAttack` | 0.0567 ('') |
| Filter Envelope Decay | 66 | `Filter1EnvDecay` | 0.4545 ('') |
| Filter Envelope Release | 0 | `Filter1EnvRelease` | 0.5122 ('') |
| Filter Envelope Sustain | 0 | `Filter1EnvSustain` | 0.0000 ('') |
| Filter Routing | 0 | `FilterLink` | 0.0000 ('Single') |
| Glide Rate | 20 | `GlideRate` | 0.1500 ('') |
| Mixer Osc 1 Balance | 0 | `Osc1Pan` | 0.5000 ('') |
| Mixer Osc 1 Level | 127 | `Osc1Vol` | 0.6588 ('') |
| Mixer Osc 2 Balance | 0 | `Osc2Pan` | 0.5000 ('') |
| Mixer Osc 2 Level | 127 | `Osc2Vol` | 0.0000 ('') |
| Mixer Osc 3 Balance | 0 | `Osc3Pan` | 0.5000 ('') |
| Mixer Osc 3 Level | 127 | `Osc3Vol` | 0.0000 ('') |
| Osc 1 Shape | Saw | `Osc1Type` | 1.0000 ('Waveform') |
| Osc 1 Shape | Saw | `Osc1WaveformShape` | 0.0000 ('Sawtooth') |
| Osc 2 Shape | off | `Osc2Type` | 5.0000 ('Off') |
| Osc 2 Shape | off | `Osc2WaveformShape` | 0.0000 ('Sawtooth') |
| Osc 3 Shape | off | `Osc3Type` | 5.0000 ('Off') |
| Osc 3 Shape | off | `Osc3WaveformShape` | 0.0000 ('Sawtooth') |

**Cutoff-Check:** Blofeld raw 66/127 = 0.5197 vs Iridium norm 0.5191 -> Faktor 0.999

## 'Voyager Bass'  (BLO `038-Voyager_Bass.mid` ↔ IRR v9 `02115-Voyager Bass.qpat`)

| Blofeld-Parameter | Blofeld-Wert | Iridium-Key | Iridium-Wert |
|---|---|---|---|
| Amplifier Envelope Attack | 0 | `AmpEnvAttack` | 0.0000 ('') |
| Amplifier Envelope Decay | 52 | `AmpEnvDecay` | 0.0000 ('') |
| Amplifier Envelope Release | 30 | `AmpEnvRelease` | 0.1065 ('') |
| Amplifier Envelope Sustain | 127 | `AmpEnvSustain` | 1.0000 ('') |
| Amplifier Velocity | 117 | `AmpVeloAmount` | 0.5000 ('') |
| Amplifier Volume | 127 | `MainVolume` | 1.0000 ('') |
| Effect 1 Mix | 0 | `ChorusDryWet` | 0.7500 ('') |
| Effect 1 Type | Chorus | `FX1Type` | 0.0000 ('Off') |
| Effect 2 Mix | 0 | `DelayDryWet` | 0.0600 ('') |
| Effect 2 Type | Clk.Delay | `FX2Type` | 0.0000 ('Off') |
| Filter 1 Cutoff | 48 | `Filter1CutOff` | 0.5191 ('') |
| Filter 1 Env Amount | 82 | `Filter1EnvAmount` | 0.7494 ('') |
| Filter 1 Keytrack | 96 | `Filter1Keytrack` | 0.7500 ('') |
| Filter 1 Resonance | 42 | `Filter1Reso` | 0.4174 ('') |
| Filter 1 Type | LP 24dB | `Filter12Type` | 3.0000 ('24dB LP') |
| Filter 2 Cutoff | 48 | `Filter2CutOff` | 0.0000 ('') |
| Filter 2 Env Amount | 82 | `Filter2EnvAmount` | 0.5000 ('') |
| Filter 2 Resonance | 42 | `Filter2Reso` | 0.0000 ('') |
| Filter 2 Type | LP 24dB | `DigiFormerType` | 0.0000 ('Bypass') |
| Filter Envelope Attack | 0 | `Filter1EnvAttack` | 0.0567 ('') |
| Filter Envelope Decay | 59 | `Filter1EnvDecay` | 0.4545 ('') |
| Filter Envelope Release | 59 | `Filter1EnvRelease` | 0.5122 ('') |
| Filter Envelope Sustain | 0 | `Filter1EnvSustain` | 0.0000 ('') |
| Filter Routing | 0 | `FilterLink` | 0.0000 ('Single') |
| Glide Rate | 20 | `GlideRate` | 0.1500 ('') |
| Mixer Osc 1 Balance | 0 | `Osc1Pan` | 0.5000 ('') |
| Mixer Osc 1 Level | 127 | `Osc1Vol` | 1.0000 ('') |
| Mixer Osc 2 Balance | 127 | `Osc2Pan` | 0.5000 ('') |
| Mixer Osc 2 Level | 127 | `Osc2Vol` | 0.8358 ('') |
| Mixer Osc 3 Balance | 64 | `Osc3Pan` | 0.5000 ('') |
| Mixer Osc 3 Level | 100 | `Osc3Vol` | 0.0000 ('') |
| Osc 1 Shape | Saw | `Osc1Type` | 1.0000 ('Waveform') |
| Osc 1 Shape | Saw | `Osc1WaveformShape` | 0.0000 ('Sawtooth') |
| Osc 2 Shape | Saw | `Osc2Type` | 1.0000 ('Waveform') |
| Osc 2 Shape | Saw | `Osc2WaveformShape` | 0.0000 ('Sawtooth') |
| Osc 3 Shape | Pulse | `Osc3Type` | 5.0000 ('Off') |
| Osc 3 Shape | Pulse | `Osc3WaveformShape` | 0.0000 ('Sawtooth') |

**Cutoff-Check:** Blofeld raw 48/127 = 0.3780 vs Iridium norm 0.5191 -> Faktor 1.373


## Conclusion across all 4 pairs (Don Solaris' own scaling)

| Sound | F1 Cutoff BLO raw/127 -> IRR norm (Faktor) | AmpVol raw -> MainVolume | FE Decay raw/127 -> IRR norm | AmpVelo raw -> AmpVeloAmount | F1 Type -> Filter12Type |
|---|---|---|---|---|---|
| Michael Cretu | 127/127=1.000 -> 1.000 (x1.00) | 86 -> 1.000 | 50/127=0.394 -> 0.700 | 117 -> 0.500 | Bypass -> 0 ('12dB LP') |
| MonoPoly Bass | 43/127=0.339 -> 0.148 (x0.44) | 127 -> 1.000 | 72/127=0.567 -> 0.343 | 64 -> 0.500 | LP 24dB -> 3 ('24dB LP') |
| Moog Lead | 66/127=0.520 -> 0.519 (x1.00) | 100 -> 1.000 | 66/127=0.520 -> 0.455 | 64 -> 0.500 | LP 24dB -> 3 ('24dB LP') |
| Voyager Bass | 48/127=0.378 -> 0.519 (x1.37) | 127 -> 1.000 | 59/127=0.465 -> 0.455 | 117 -> 0.500 | LP 24dB -> 3 ('24dB LP') |

**Observations:**

- Cutoff: factor ~1 (linear norm), as long as BLO != 0.
- MainVolume is partly set to 1.0 by Don (AmpVol not taken over 1:1).
- Env times are NOT linear (raw/127 != norm) -> different time scale on the Iridium.
- F1 Type Bypass (Blofeld) lands as 12dB LP (v8 default), not as Bypass.

