# Architectural Differences Blofeld ↔ Iridium — and What They Mean for the Conversion

*English translation of [`ARCHITEKTUR-DIFFERENZEN.md`](ARCHITEKTUR-DIFFERENZEN.md). Technical identifiers, parameter names and file paths are kept unchanged.* 2026-11-21 (translation: 2026-11-22)

**Basis:** Blofeld operation manual, Iridium OS 4 parameter dump
(`dumps/00000-.qpat`), converter (`bloridium/qpat_map.py`) and the profiling sweep
(`docs/PROFILING-INIT-2026-11-21.md`, 752 individual measurements).

The two synths are not siblings in a different enclosure. The Blofeld is a
classic subtractive synth with two multimode filters and its own noise mixer;
the Iridium is a wavetable/kernel synth in which many building blocks exist as an
*oscillator, filter or matrix destination*, but not as a dedicated menu item. Every
parameter therefore falls into one of three cases:

1. **Directly mappable** (same function, different scale) — e.g. filter cutoff, envelopes.
2. **Architecturally different, but with a workaround** — e.g. noise as a waveform,
   PWM via the modulation matrix.
3. **Not mappable** — e.g. filter FM, modifier arithmetic operators, arpeggiator patterns.

---

## 1. Summary

| Area | Blofeld | Iridium | Consequence | Workaround | Measurement 2026-11-21 |
|---|---|---|---|---|---|
| **Noise** | dedicated noise generator in the mixer (level, balance, colour 0–127) | **no noise mixer**; noise is an oscillator waveform (white/pink) or particle/resonator "dirt" | noise needs an oscillator slot | free osc as noise: `OscNType=Waveform`, `WaveformShape=White/Pink`, level→`OscNVol`, balance→`OscNPan` | level follows the trend (cos 0.77–0.93), response curve deviates; **colour defective** (only 2 steps) |
| **PWM** | oscillator PWM with source + amount, affects the **pulse width** | static PW (`OscNWaveformPW`); modulation via matrix destination `WFn Warp` / `WTn Position` | warp changes the **entire waveform**, not just the pulse width | matrix row `Source → WFn Warp` only for pulse-like shapes, wavetable → `WTn Position`; otherwise deliberately ignore | **fixed (A1, 2026-11-21):** saw/triangle/sine no longer generate a warp row; re-measurement pending |
| **FM** | osc FM with source + amount per oscillator | **no FM input per osc**; FM lives in the 6 kernels (`V4OscNKernel*`) or as matrix→pitch | not 1:1 | kernels for real FM sounds; matrix→`OscN Pitch` only for vibrato-like effects | not testable in Init (no FM in Init) |
| **Sync** | a switch "Osc 2 Sync to O3" | `Osc2WaveformSync` (waveform osc only); wavetable sync via `WavetableTravel(SyncRatio)` | sync directly only for waveform osc | `Osc2WaveformSync=1`; for wavetable osc WT travel/sync ratio | Test D sync not reliable (two sounding oscs → high variance) |
| **Filter topology** | 2 multimode filters; **balance per sound source** (osc/ring/noise) distributed to F1/F2; routing parallel/serial | 2 filters with `FilterLink` (Single/Boost/Independent/Linked) and `OscNDestination` (DF/F1/F2 share) | balance is not pan, but a filter assignment | balance → `OscNDestination` shares, routing → `FilterLink`, F2 model → DigiFormer | direct test: **balance 0 = F1, 127 = F2; routing 0 = parallel, 1 = serial**. Converter mapping for F2 not yet reliable (sweep variant inconsistent) |
| **Filter drive** | drive + 13 drive curves per filter | no filter drive; drive is an FX (`DriveAmount`, `DriveGain`) | consumes an FX slot | `FX1/FX2 = Drive`, approximate the curve via drive type | Filter 1 drive partial (cos 0.96; 0.81×) |
| **Filter FM / filter pan** | FM and pan with source/amount per filter | no filter FM; pan only as matrix destination `FilterN Pan` | FM not mappable | pan via matrix; mark FM as "not supported" | Filter 1 pan amount: at 100% OK (cos 1.0), at 0% **no** Iridium effect → amount asymmetric |
| **Pan vs. balance** | balance distributed to **F1/F2**, no stereo pan | `OscNPan` is true stereo pan | balance ≠ pan | balance → `OscNDestination`, **not** → pan | L/R test: Blofeld image unchanged (B≈0), Iridium drifts (I 5–12) → Mismatch |
| **Ring modulation** | O1×O2 **and** O1×O3, each with balance | `RingModOsc1ToOsc2` **and** `RingModOsc1ToOsc3` exist | O1×O3 is **mappable**, but not used | also set `RingModOsc1ToOsc3` | not audible in Init (osc 2/3 off) |
| **Waveforms** | ~70 shapes incl. sync, fuzz and wavetable variants | wavetable (many tables) + waveform (saw/sine/tri/square/noise) + particle/resonator/kernels/seeds | only a subset is 1:1 | bridge table for wavetables; VA shapes directly | osc 1/2/3 shape mostly OK (cos 0.93–0.99); individual tables mismatch |
| **Unison** | up to 8 voices, detune; no pan/delay | `UnisonoCount`, `UnisonoDetune`, **`UnisonoPan`, `UnisonoDelay`** | count/detune are not enough | count from bitfield **4–6** (spec 4.10), detune norm; keep pan 0.5 / delay 0 neutral | **fixed (A4, 2026-11-21):** bits 4–6 instead of 5–7 (voice count was halved); re-measurement pending |
| **Glide** | mono/poly, 4 modes (Portamento/fingered P/Glissando/fingered G), rate 0–127 | `GlideOnOff`, `GlideRate`, `GlideType` (Onset/Legato only), **no mono mode** | modes and mono cannot be mapped 1:1; rate curve deviates | `GlideType` from the mode (Portamento→Onset, fingered→Legato); rate via measured anchors; clamp high rates to 1.0 | **Block 5 (2026-11-21):** Portamento OK (155/144 ms); rate above raw 70 too short (1013/315 ms, 2117/384 ms); Glissando/fingered not transferred; Iridium max ~1.6 s |
| **Envelopes** | 4 envelopes, modes ADSR/ADS1DS2R/OneShot/Loop, attack level, decay2/sustain2 | envelopes with curves (RC/Exp/Lin), loop modes, delay | second decay/sustain stage missing | ADSR 1:1; approximate ADS1DS2R with ADSR (stage 2 is lost) | FE env amount/attack/sustain OK (cos 0.90–0.99); amp attack/sustain partial; FE decay only at long times |
| **LFOs** | 3 LFOs: shape, speed, sync, clocked, phase, delay, **fade** (rate), keytrack | 6 LFOs: shape, speed, sync, phase, **delay, attack, decay**, slew, warp | fade/keytrack have no direct counterpart; speed curves deviate | fade → `LfoNAttack`/`LfoNDecay` (invert direction); keytrack → matrix `Keytrack → LFO Speed` | **2026-11-22:** speed Iridium 2–4× too slow (raw 40: 2.63/1.09 Hz); fade is a rate, attack/decay on the Iridium without measurable effect |
| **Modifier** | 4 arithmetic modifiers (+ − × AND OR XOR MAX min) | matrix control (src + ctrl), no free arithmetic operators | only × products and + with a constant can be approximated | `LFO × ModWheel` as src+ctrl; other operators "not supported" | — |
| **Arpeggiator** | arp with 16-step pattern, glide/accent, timing | arp/sequencer (`ArpOn`, `ArpStepLength`, `ArpGate`, …) | separate block, fully unmapped | basic arp function could be mapped (step length, octaves, sorting) | not tested |
| **FX** | 2 slots, fixed types, dry/wet per type | 5 FX slots + mod FX, more types | type mapping needed; parameter indices deviate | dry/wet key per type; parameter 1:1 by index | FX mix partial; parameters 1/2 partial; **parameter 5 heavily overdriven at 64/127** |
| **Voices** | 16 parts, multitimbral | 4 parts/layers | irrelevant for sound conversion | one part (Part 1, channel 6) | — |

---

## 2. The Most Important Differences in Detail

### 2.1 Noise: Mixer Channel vs. Oscillator Waveform

The Blofeld has its own noise generator whose level, filter balance and
**colour** (Colour, continuous) live in the mixer. The Iridium has no "noise" module;
noise is created as a **waveform of an oscillator** (`OscNType=Waveform`,
`WaveformShape` = Pink/White Noise) or as a dirt component in Particle/Resonator.

- **Workaround (implemented in the converter):** use a free oscillator as the noise source
  (preferably Osc 3), level → `OscNVol`, balance → `OscNPan`,
  destination → `DF 0 Fil 100`.
- **Limits:** (a) an oscillator must be free, otherwise the noise component cannot be
  mapped; (b) the continuous colour is reduced to **two steps** (pink ≤ 64, white > 64).
  For intermediate values only a filter (cutoff/type) or particle dirt helps.
- **Measurement:** noise level follows the trend (cosine 0.77–0.93, but with a deviating
  response curve), **noise colour is defective** — the Iridium only switches between pink
  and white, while the Blofeld is continuous.

### 2.2 PWM: Pulse Width vs. Waveform Warp

On the Blofeld, PWM modulates the **pulse width** — and only for pulse-like waveforms.
The Iridium has a static PW (`OscNWaveformPW`) and, as a modulation destination,
`WFn Warp` (waveform osc) or `WTn Position` (wavetable osc).

- **Workaround (implemented in the converter):** matrix row `PWM Source → WFn Warp`
  with a bipolar amount, but **only for pulse-like shapes**; for wavetable oscs
  use `WTn Position` instead. For saw/triangle/sine the row is deliberately not
  created and is noted as "ignored" in the `unmapped` report (A1, 2026-11-21).
- **Limit:** warp changes the entire waveform. With a sawtooth template,
  Blofeld PWM has **no effect**, but the Iridium warp does. That is exactly what the
  measurement showed: **PWM amount on Osc 1/2/3 was "only the Iridium reacts"**.
- **Status:** fix + unit tests exist (`has_pulse_width`, A066/A007); the
  re-measurement with the filtered mapping is still pending.

### 2.3 FM: Oscillator Input vs. Kernel Engine

Blofeld FM is a real oscillator input (source + amount per osc). The Iridium
has no FM input on the oscillator; FM is created in the **6 kernels** per oscillator
(`V4OscNKernel1..6`: ratio, level, feedback, mod source, envelopes) or as a
matrix destination `OscN Pitch`.

- **Workaround:** for FM sounds, rebuild the kernel engine (kernel 1 = carrier,
  kernel 2 = modulator, ratio/level from the Blofeld FM amount); for vibrato-like
  effects, matrix→pitch is sufficient.
- **Not 1:1:** the sonic character (feedback, modulator waveform)
  is different. Not testable in the Init sound because no FM is active there.

### 2.4 Filter: Balance Topology vs. FilterLink

This is the most frequently underestimated difference. The Blofeld distributes **every
sound source** to Filter 1 and Filter 2 via its own balance control
(direct test: 0 = F1, 127 = F2; the manual display "F1 64 … F2 63" is misleading).
The Iridium distributes via `OscNDestination` ("DF 0 Fil 100" … "DF 100 Fil 0") and
connects the filters via `FilterLink`.

- **Workaround:** balance → `OscNDestination` shares; routing → `FilterLink`;
  Filter 2 model → DigiFormer (`Nave/PPG/Largo/SVF/Comb`) after Filter 1
  (`FilterFormerRouting = Filter > Former`), because the Blofeld F2 is often a
  character filter.
- **Measurement evidence (direct test, 12 recordings):** with routing 0 (parallel), Filter 2
  is only audible when the balance is on F2 (balance 127: F2 cutoff changes the
  sound strongly, centroid 1663 → 3511 Hz); with balance 0 (F1), F2 remains ineffective.
  With routing 1 (serial), Filter 2 is always in the signal path, regardless of the
  balance (centroid 1795 → 3550 Hz). This confirms the manual description:
  **balance 0 = F1, 127 = F2; routing 0 = parallel, 1 = serial.**
- **Status after the routing correction (2026-11-21):** the converter now maps the
  balance depending on the routing — **serial** via `OscNDestination`
  (2 = F1 … 22 = Former/F2), **parallel** via the global
  `FilterLevel`/`Filter2Level` (a per-osc share cannot be represented in parallel
  routing). With a verified dump load (noise floor 0.2/0.6), **F2 cutoff** follows the
  Blofeld (cosine 0.88–0.96, strength 0.6), **F2 drive** at high values
  (0.97), and the **F2 envelope**: env amount 0.92–1.0,
  env velocity 0.75–0.81, keytrack 0.89 (partial).
- **Addendum A2 (2026-11-21, code):** in parallel routing the converter now sets
  `FilterLink = Independent` (the v8 template was on `Boost`, which ignores
  cutoff 2/resonance 2) and a separate `Filter2Type` (v14 has a separate
  `Filter2Type` besides `Filter12Type`). Filter drive runs as an insert with
  `DriveDryWet=1.0`; the resonance response maps raw 113 (Blofeld
  self-oscillation) to 1.0. The **F2 re-measurement** is still pending
  (`TODO_MEASURE.md`).
- **Limit:** despite the response-curve fix, the resonance shape remains an approximation;
  if the cosine stays poor, the filter models
  (`Filter1Model`/`Filter2Model`, B5) are the next lever.

### 2.5 Filter Drive and Filter FM

The Blofeld has drive **and** a drive curve per filter; the Iridium has no
filter drive. Drive is an FX (`DriveAmount`, `DriveGain`, `DriveType`).

- **Workaround:** `FX1/FX2 = Drive` and approximate the curve via the drive type.
- **Cost:** one FX slot; not available if FX slots are already in use.
- Filter FM has no Iridium counterpart; filter pan only works via the matrix.

### 2.6 Waveform Generator

The Blofeld offers ~70 shapes (VA, sync, fuzz, wavetable variants). The Iridium
separates **wavetable** (tables + position/brilliance/travel) and **waveform**
(saw/sine/tri/square/noise + warp/PW). Sync and fuzz shapes have no direct
equivalent; they are approximated via the bridge table.

- **Measurement:** osc 1/2/3 shape mostly OK (cos 0.93–0.99); individual
  wavetable tables (e.g. Osc 3 Shape 18/36) deviate.

### 2.7 Envelopes

Blofeld: 4 envelopes with mode (ADSR, ADS1DS2R, One Shot, Loop), attack level,
decay 2 / sustain 2. Iridium: envelopes with **curve shape** (RC/Exp/Lin), delay,
loop mode.

- **Workaround:** ADSR 1:1; reduce ADS1DS2R to ADSR (the second stage is
  lost); approximate attack level via the first envelope stage.
- **Measurement:** filter env amount, attack and sustain OK (cos 0.90–0.99); amp attack
  and sustain partial (Iridium 1.7–2.0× stronger); **filter env decay** only measurable at
  long times (with sustain 100, decay has no effect); **filter env release**
  could not be measured reliably (amp release shorter than filter release).

### 2.8 LFOs

The Iridium has **six** LFOs with delay, attack, decay and slew — the Blofeld has three
with fade and keytrack.

- **Workaround:** Blofeld fade → `LfoNAttack`/`LfoNDecay`; keytrack →
  matrix `Keytrack → LFO Speed`; clocked/sync → `LfoNSync` + `SyncRatio`.
- **Measurement (2026-11-22, `docs/LFO-2026-11-21.md`):**
  - **Free speed:** Blofeld raw 20/40/60/80 = 0.45/2.63/10.43/30.65 Hz;
    Iridium 0.11/1.09/5.66/16.32 Hz. The linear `norm(raw)` mapping is
    2–4× too slow at medium/high values → an Hz curve is needed.
  - **Fade:** the Blofeld value is a **rate** (larger magnitude = faster),
    positive = fade-in, negative = fade-out after `Delay`. With the converted
    `Lfo1Attack/Decay` values, the Iridium shows no measurable fade-in/out
    (even at 1.0 in all `Lfo1Global` modes). The linear `(raw−64)/63`
    time mapping is therefore wrong in direction.
- **Status:** the fade mapping exists in code (A7a), but is **not effective** on the
  device; free speed is uncalibrated.

### 2.9 Modulation Matrix and Modifier

Blofeld: 16 slots + 4 modifiers with arithmetic operators. Iridium: 40 matrix rows with
source + control.

- **Workaround:** products (LFO × ModWheel, LFO × Pressure) as `Src=LFO` +
  `MatrixControl=Wheel/Aftertouch`; sums with a constant as src + offset.
- **Not mappable:** AND/OR/XOR/MAX/min, modifier chains, control W–Z exactly.

### 2.10 Pan and Balance (Test E, 2026-11-21)

The L/R-separated test proves the difference in black and white:

- **Balance is not pan.** On the Blofeld, the stereo image remains practically unchanged
  at every balance setting (effect ≈ 0), because balance only distributes the
  F1/F2 share. The Iridium used to drift noticeably (effect 5–12)
  because the converter mapped balance to `OscNPan`. **Fixed (A11):** serial →
  `OscNDestination`, parallel → `FilterLevel`/`Filter2Level`; the re-measurement shows
  no drift anymore (noise balance n/a on both sides).
- **Filter pan amount was asymmetric** (100% cosine 1.0, 0% no
  Iridium effect). Cause: the matrix row was not created at amount 0
  (Blofeld 0 is "full left deflection", not "off"). Fixed: row from 0,
  amount bipolar `0.5 + (raw−64)/127`. Re-measured: 0% cosine 0.998,
  100% 0.997.
- **Amp velocity response:** at amount 0, the Iridium is clearly more
  velocity-sensitive than the Blofeld (I 6.1 vs. B 2.4, cosine 0.97) — the
  scaling of the velocity curve must be adjusted.

### 2.11 Arpeggiator

The Blofeld arp (pattern, 16 steps, glide/accent, timing) is a separate block.
The Iridium has arp/sequencer parameters (`ArpOn`, `ArpStepLength`, `ArpGate`,
`ArpSortOrder`, `ArpVeloMode`), but the converter does not use them.

- **Workaround:** the basic function (on/off, step length, octaves, sorting, gate)
  could be mapped; step patterns/accent/glide remain unmapped.

### 2.12 Glide: Mono/Modes vs. Onset/Legato

The Blofeld has **poly/mono**, four glide modes (Portamento, fingered P,
Glissando, fingered G) and a rate 0–127 (exponential, milliseconds to
several seconds). The Iridium has **no mono mode** (`VoiceAllocationMode`
only knows 8/16 voices), but `GlideOnOff`, `GlideRate` (0…1) and `GlideType`
(Onset = every new note glides, Legato = only when overlapping).

- **Mapped:** `GlideOnOff` and `GlideRate`. **Not mapped:** glide mode and
  mono allocation.
- **Measurement Block 5 (2026-11-21, C3→C5, dry):**
  - Portamento at rate 50: **OK** (Blofeld 155 ms / Iridium 144 ms).
  - Rate curve: Blofeld raw 50/64/70/85 = 155/592/1013/2117 ms. Iridium
    `GlideRate` 0.30/0.50/0.75/1.00 = 139/379/896/1600 ms. The converter maps
    raw 85 to 0.50 → 384 ms (0.18×); raw 70 to 0.419 → 315 ms (0.31×).
    Recommendation: raw 50 → ~0.32, 64 → ~0.59, 70 → ~0.79, from 85 → 1.0.
  - Glissando/fingered G: the Blofeld produces semitone steps (6 and 14
    plateaus respectively), the Iridium glides continuously (0) → mode missing.
  - Staccato + fingered: the Blofeld does not glide, the Iridium (Onset) does.
- **Limit:** no mono mode and a maximum glide of ~1.6 s on the Iridium. The
  Blofeld times from raw 85 (2.1 s … 5 s) cannot be reached 1:1.
- **Workaround:** derive `GlideType` from the mode (Portamento→Onset,
  fingered→Legato); Glissando has no Iridium counterpart (Legato as an approximation);
  calibrate the rate using the measured anchors and clamp high values to 1.0.

---

## 3. Mappable but Not Yet Used in the Converter (Mapping Gaps)

These points are **not** architectural limits — the Iridium parameters exist,
but are not being set:

| Blofeld | Existing Iridium parameter | Benefit |
|---|---|---|
| Mixer RingMod Balance / O1×O3 | `RingModOsc1ToOsc3` | ring mod on Osc 3 |
| Glide Mode | `GlideType` | Portamento/fingered→Onset/Legato; Glissando not mappable |
| Allocation/Unisono | `UnisonoPan`, `UnisonoDelay` | wider unison voices |
| LFO Fade | `LfoNAttack`, `LfoNDecay` | fade-in/out |
| LFO Keytrack | matrix `Keytrack → LFO Speed` | speed-dependent LFOs |
| Osc Bend Range / Keytrack | `OscNPitchBendRange`, `OscNKeytrack` | pitch-bend range, keyboard tracking |
| Arpeggiator (basic) | `ArpOn`, `ArpStepLength`, `ArpGate`, … | basic arp |
| Noise Colour (continuous) | filter cutoff/type or particle dirt | approximate the colour gradient |

