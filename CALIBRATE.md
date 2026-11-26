# CALIBRATE.md — Measurement-Based Calibration of Blofeld → Iridium Mappings

One-parameter-at-a-time hardware calibration: how we turn converter mappings
from assumptions into measured curves. Every table below lives (or should live)
as anchor points in `bloridium/qpat_map.py`; the raw measurement data and
analysis are documented in `docs/research/<TOPIC>-<date>.md`.

**Rule of thumb:** a mapping may ship only with (a) a measured calibration,
(b) a manual-documented identity (e.g. both sides linear in the same unit), or
(c) an explicit `TODO` comment naming the calibration task. `norm(raw)` on a
parameter whose device scale is logarithmic/exponential is a bug, not a
shortcut.

---

## 1. Method: INIT → isolate → sweep → measure → anchors

### 1.1 Isolate (both devices start from a known INIT state)

- **Blofeld**: the init sound is `dumps/banks/A/A066.bin` ("Init"). The test
  program is built **offline** as SDATA byte overrides
  (`profile_todo_measure.with_overrides`) — single sine oscillator, FX
  bypassed, *all* of the init sound's own modulation paths switched off
  (matrix rows, Osc Pitch Source, F1/F2 Mod, Amp Mod, PWM/FM sources). Only
  the parameter under test varies.
- **Iridium**: QUIR `init-patch` resets the edit buffer to factory init. The
  values under test are then applied as **exactly the shipped converter
  output** (`overrides_for(sdata)` = `qpat_map.blofeld_to_qpat_params`), never
  hand-picked values — the calibration must measure the converter, not an
  idealized setting.

### 1.2 Verified load (never trust a silent set)

- **Blofeld**: `M.load_sndd_actual()` (scripts/_measure.py) sends the SNDD to
  the edit buffer and reads it back; the *actual* (device-normalized) SDATA is
  used for the conversion, not the intended one.
- **Iridium**: after `init-patch`, wait ≥ 1 s, then apply the base values with
  **readback verification and retry**. Right after `init-patch` the QUIR shell
  answers get/set-param with memory garbage (measured 2026-11-26) — an
  unverified base apply silently kills any row that is never re-sent.
- Per condition: verify the parameter/row under test by readback before
  recording; verify FX bypass (`apply_fx({"kind": "dry"})`).

### 1.3 One capture, both devices

`M.capture()` plays the same note on both synths and records all Scarlett
channels at once (Blofeld in 3/4, Iridium in 5/6). Any difference in the two
audio tracks is attributable to the mapping under test. Preconditions:

- Iridium audio via DIN (USB plugged in only for the QUIR shell; ground loop).
- CC123=0 + CC7=127 on all channels before every take.
- Blofeld in **single** mode (Shift+Sound/Multi — a channel scan cannot detect
  multi mode; checked on the device, see `check_blofeld_mode.py`).
- Part 1 only (ch 6) on the Iridium.

### 1.4 Sweep and measure

Vary one raw value across the musically relevant range (include the neutral
value as a zero check and the extremes). Measure the **audio-domain quantity**
— Hz, seconds, dB, semitones — with an estimator suited to the signal:

| Quantity | Estimator | Where |
|---|---|---|
| Instantaneous pitch (sine) | complex heterodyne + unwrapped phase | `calib_lfo_pitch.inst_pitch_semi` |
| Fundamental (sanity check) | FFT peak / autocorrelation | `fft_peak_hz`, `diag_lfo.pitch_hz` |
| Tremolo depth/rate | RMS envelope + synchronous demodulation | `profile_lfo_measure.mod_freq/depth_profile` |
| Glide time | 10–90 % transition of the pitch glide | `profile_glide_sweep` |
| Attack/decay times | 10–90 % attack, −20 dB decay (Lin curve) | `calib_envelope*` |
| Filter cutoff | Hz at self-oscillation / spectrum peak | calib 200–205 |

Every capture gets a **fundamental sanity check** (FFT peak must sit at the
expected pitch — a wrong patch in a buffer shows up here immediately).

### 1.5 Anchors, not factors

Fit the result as an **anchor table** raw → device value and interpolate
logarithmically where the device is log-scaled (time, Hz). Implement in
`qpat_map.py` next to the mapping function, add/adjust a regression test that
freezes the anchors, document the measurement in
`docs/research/<TOPIC>-<date>.md`, bump the version, note it in
`FIXES_HISTORY.md`.

### 1.6 Expensive lessons (pitfalls)

- **Edit buffer must be INIT before layering diffs.** A run with the user's
  last selection ("Prophet Brass", slot 200) in the buffer produced ~8 semi of
  fake depth at ~400 Hz (2026-11-26).
- **QUIR shell flakiness:** memory-dump garbage right after `init-patch`;
  "No free DTD!" (USB transfer descriptors exhausted) after many commands →
  power-cycle, scripts resume from their logs.
- **Dead rows:** a swallowed set-param leaves a matrix row inert while the
  readback of *other* params looks fine — verify the row under test, not just
  anything.
- **Estimator windows:** the heterodyne lowpass must be far below the LFO
  period but long enough to crush the 2nd harmonic (24 ms window let 2×f₀
  ripple fake a "523 Hz rate"; 60 ms is correct for LFOs ≤ ~3 Hz). At extreme
  modulation depths (> ±15 semi) the heterodyne loses lock — keep sweeps in
  the musical range or use slower LFO rates.
- **Score vs ear:** `spec_mad_db` rewards spectral brightness; the 0.6.5
  env-amount (+8.0 score) sounded worse and was reverted in 0.6.7. Calibration
  is the honest third way: measure the physical quantity instead of trusting
  either.
- **Iridium scales are rarely linear** in time/frequency — never map with
  `norm()` where the device is log-scaled (cutoff, glide, envelope times,
  LFO speed were all wrong before calibration).

---

## 2. Calibrated parameters (shipped in `qpat_map.py`)

| Parameter | Calibration | Source / date |
|---|---|---|
| Osc detune → `OscNFinePitch` | ±203 cent per norm unit, divisor 127 | PROFILING-INIT, 2026-11-21 |
| Filter cutoff → `FilterNCutOff`/`DigiFormerAmount` | Hz bridge: Blofeld semitone steps, 440 Hz @ raw 64; Iridium log10 f = 0.9117 + 3.387·norm | calib 200–205, 2026-11-14 |
| Filter resonance → `FilterNReso` | self-oscillation threshold raw 113 → 1.0 | manual + verified |
| Glide rate → `GlideRate` | time anchors both sides (`GLIDE_BLO_ANCHORS`/`GLIDE_IRR_ANCHORS`) | GLIDE-2026-11-21.md |
| Envelope attack/decay times | `ENVELOPE_TIME_ANCHORS` (Lin curve, 10–90 % / −20 dB) | 2026-11-22 |
| Envelope curve enums | RC/Exp/Exp per curve type (factory qpat cross-check) | 0.6.3 |
| Matrix pitch amount → semi | `MATRIX_PITCH_CAL` (amount → semitones, Constant→Osc1Pitch) | 2026-11-21 |
| Bipolar matrix full scale | divisor 127 (`bipolar_amount_full`), pan measured at half with /254 | 2026-11-21 |
| `LfoNDecay` ≠ 0 | 0 kills the LFO output; 1.0 for every converted LFO | E090 measurement, 2026-11-22 |
| LFO → Pitch depth (small amounts) | `amt_bipolar` (divisor 254) **confirmed correct** for raw 64-80 (ratio 0.98-1.11, direct and matrix identical); above raw 88 the Iridium undershoots (0.52/0.25/0.19), affects 8/200 sounds | LFO-PITCH-CALIB-2026-11-26.md |

**Measured but not yet implemented** (curves exist, converter still linear):

| Parameter | Status | Source |
|---|---|---|
| `LfoNSpeed` | Blofeld raw→Hz and Iridium norm→Hz both measured (raw 40: 2.63 Hz BF vs 1.09 Hz IR); converter still `norm(raw)` | LFO-2026-11-21.md (A7) |
| LFO fade (→ `LfoNAttack`/`LfoNDecay`) | Blofeld fade is a *rate* (+/-, with delay), Iridium shows no measured fade with the current mapping — semantics unresolved | LFO-2026-11-21.md (A7) |

---

## 3. Calibration candidates (worth measuring, prioritized)

1. **`LfoNSpeed` implementation** — highest value: curves are already measured
   (A7); the "LFO too strong" ear verdict on A001 (2026-11-26) points at speed,
   not depth — A001's amounts sit in the range where depth was confirmed
   correct. Implement the Hz bridge.
2. **Clocked LFOs** (`LFO n Clocked = 1`, 16/100 bank E sounds) — currently
   mapped as free rate; needs a tempo-sync measurement (SyncRatio semantics,
   `LfoNSync`/`SyncRatio` enums from own exports).
3. **LFO fade semantics** — A7 data exists; needs a follow-up sweep
   (positive/negative fade × delay) with the depth-profile estimator.
4. **Filter 1/2 Env Amount** — the scale itself was never measured; 0.6.5
   (bipolar) was reverted by ear, 0.6.7 is back to `norm(raw)`. A clean
   init-patch sweep (env amount × cutoff trajectory) would settle it.
5. **Envelope release times** — attack/decay are anchored; release still maps
   linearly. Same 10–90 %/−60 dB method as `calib_envelope*`.
6. **Filter keytrack** (raw 72/96 in many sounds) — never measured on either
   device.
7. **PWM amount / Pulsewidth** — matrix rows use a different amount scale;
   no audio-domain measurement yet.
8. **AmpVelo (Velocity→Volume)** — `0.5+0.5·norm` was chosen from the bipolar
   trap, never verified by a velocity sweep.
9. **Unisono detune / unison count** — unconverted/unmeasured.
10. **LFO → Pitch depth, large-depth region** (raw > 88): Iridium measures
    flatter than Blofeld (measured 2026-11-26, ratios 0.52/0.25/0.19 at raw
    88/96/112); affects 8/200 bank sounds (A003, A037, A048, A051, A071,
    A072, A099, E042) — a correction curve for amounts > 0.59 would only
    matter for those.
11. **LFO → F1/F2 Cutoff depth** (A9) — measured 2026-11-26 on A001: IR
    brightness wobble 9.6 dB where the BF shows none (raw 103 → amount
    0.654). INIT-framework sweep over cutoff-mod amounts, centroid-mod
    depth BF vs IR. See docs/research/A001-LFO-2026-11-26.md.
12. **Drive / FM amounts** — unmeasured.
13. **FX parameter scales** (Effect 1/2 Parameter 1–14) — confirmed gap: only
    FX *types* are converted, no parameters (A001 chorus → IR defaults;
    2026-11-26). Start with chorus rate/depth/mix.

When a candidate is measured: move it to §2, implement anchors in
`qpat_map.py`, reference the research doc, update `TODO_MEASURE.md`.

---

## 4. Tooling quick reference

| Task | Script / helper |
|---|---|
| Blofeld SNDD → edit buffer + verified readback | `scripts/_measure.py: load_sndd_actual` |
| Simultaneous capture, CC hygiene | `scripts/_measure.py: capture` |
| SDATA byte overrides / converted overrides | `scripts/profile_todo_measure.py: with_overrides, overrides_for` |
| Iridium init + verified apply + FX dry | `IridiumState`, `apply_fx`, `base_values` (same file) |
| LFO speed/fade measurement (A7) | `scripts/profile_lfo_measure.py` |
| LFO→Pitch depth calibration (A8) | `scripts/calib_lfo_pitch.py` |
| Envelope time calibration | `scripts/calib_envelope*.py` |
| Glide calibration | `scripts/profile_glide_sweep.py` |
| Init profiling / single-param sweeps | `scripts/profile_init_sweep.py` |
| LFO diagnosis (is the LFO alive?) | `scripts/diag_lfo.py` |
| Full-bank A/B measurement | `scripts/measure_rf100.py` (see README.md) |
