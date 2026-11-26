# A8 — LFO->Pitch depth: Blofeld vs Iridium (2026-11-26)

Init A066, Osc1 Sine, FX off, LFO1 Sine, speed raw 40
(Blofeld ~2.6 Hz, converted Iridium ~1.1 Hz), note 60.
depth = peak-to-peak/2 of the fundamental, in semitones.

## direct

| raw | BF semi | IR semi | ratio | BF Hz | IR Hz |
|---:|---:|---:|---:|---:|---:|
| 64 | 0.333 | 0.333 | 1.0 | 523.27 | 523.27 |
| 66 | 0.341 | 0.336 | 0.98 | 523.46 | 523.46 |
| 70 | 0.365 | 0.370 | 1.02 | 523.46 | 523.46 |
| 74 | 0.400 | 0.441 | 1.1 | 523.46 | 523.64 |
| 80 | 0.501 | 0.555 | 1.11 | 523.46 | 275.82 |
| 88 | 2.961 | 1.532 | 0.52 | 299.64 | 175.64 |
| 96 | 15.754 | 3.936 | 0.25 | 330.36 | 252.18 |
| 112 | 43.020 | 8.335 | 0.19 | 1195.64 | 277.64 |
| 127 | 25.235 | 28.537 | 1.13 | 0.00 | 268.64 |

## matrix

| raw | BF semi | IR semi | ratio | BF Hz | IR Hz |
|---:|---:|---:|---:|---:|---:|
| 64 | 0.333 | 0.334 | 1.0 | 523.27 | 523.27 |
| 66 | 0.341 | 0.335 | 0.98 | 523.46 | 523.27 |
| 70 | 0.365 | 0.369 | 1.01 | 523.46 | 523.27 |
| 74 | 0.400 | 0.438 | 1.09 | 523.27 | 523.27 |
| 80 | 0.502 | 0.554 | 1.1 | 523.64 | 275.09 |
| 88 | 2.960 | 1.533 | 0.52 | 298.91 | 172.18 |
| 96 | 15.731 | 3.956 | 0.25 | 330.00 | 252.00 |
| 112 | 43.138 | 8.300 | 0.19 | 1194.18 | 274.73 |
| 127 | 25.292 | 28.479 | 1.13 | 0.00 | 267.09 |


## Analysis

- **direct == matrix**: with a verified base application the two Blofeld paths
  (Osc Pitch Source/Amount vs Mod row LFO1→Pitch) convert to identical Iridium
  rows and measure identically. Round 1's dead "matrix" rows were an
  application artifact: the base `set_many` right after `init-patch` was
  swallowed by the QUIR shell (memory-dump garbage); the direct variant
  re-sent its full row per condition, the matrix variant only the amount.
  Fixed with readback verification + retry (`calib_lfo_pitch.py`).
- **Noise floor ~0.33 semi** (raw 64, both devices): heterodyne drift, common
  to all rows. Net depths below are ~0.03–0.17 semi in the raw 70–80 range.
- **Raw 64–80 (Iridium amount 0.5–0.563): mapping confirmed.** Ratios
  0.98–1.11, identical in both variants. `amt_bipolar` (divisor 254) is
  correct in the musically relevant small-depth range. **No global dosing.**
- **Raw ≥ 88 (amount ≥ 0.595): the Iridium undershoots** (ratios 0.52 / 0.25
  / 0.19 at raw 88/96/112). Deep vibrato converts too shallow. Direction is
  consistent with the asymmetric `MATRIX_PITCH_CAL` (bottom flattens at
  −13.8 semi while the top reaches +24). Caveat: at these depths the
  60 ms heterodyne window smears the 2.6 Hz sweep, so both sides are
  underestimated — but the BF/IR divergence is far larger than the smearing
  and appears in both variants identically.
- **Raw 127: both trackers saturate** (BF heterodyne loses lock, FFT peak
  103 Hz; IR at its +24 semi ceiling). Values there are meaningless.
- **Affected sounds**: 8/200 (A003, A037, A048, A051, A071, A072, A099, E042)
  use LFO→Pitch amounts beyond ±24 raw steps. A correction curve for
  amounts > 0.59 would only matter for those — candidate for a follow-up.
- **Consequence for the "LFO too strong" ear verdict (A001, 2026-11-26):**
  A001's amounts (70/58) sit in the confirmed-correct range — the perceived
  over-modulation cannot come from the depth mapping. Prime suspect is
  **LfoNSpeed** (A001: `Lfo1Speed = 0.457` ≈ 5 Hz on the Iridium vs the
  Blofeld's actual rate; see LFO-2026-11-21.md). Next step: an A001-specific
  A/B rate measurement, then implement the measured Hz bridge for LfoNSpeed.
