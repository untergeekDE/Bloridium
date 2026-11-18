# Phase-B eval 2026-11-14 (CLAP embedding + LLM verdict vs Phase A)

Spec: `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md`
Plan: `docs/superpowers/plans/2026-11-14-phaseb-sim-embed.md` (Task 10)

## Setup

- CLAP: `models/larger_clap_music_and_speech-q8_0.gguf` (gorse-io, Q8_0, Apache-2.0) via clap-cpp 0.1.1, 512-d embedding, `embed_score = 100*clip(cos,0,1)`.
- LLM: ollama `lfm3-omni:2b`, mode **audio** (base64 WAV accepted in the `audio` field), prompt ID `judge-v2-pegel`, contract `{"score":0-100,"summary","differences"}`.
- `combined = 0.5*score + 0.5*embed_score`; LLM score informative, not in combined.
- Offline eval: `python3 scripts/sim_eval_offline.py` -> `recordings/phaseb_eval_20261114_171001.json`.

## Table (eval 2026-11-14 17:10)

| Pair | Phase A score | embed_score | combined | verdict |
|---|---|---|---|---|
| ab_20261114_170201 (A001 live) | 92.3 | 32.24 | 62.27 | close |
| ab_A001_20261114_154306 | – | – | – | error (silence) |
| ab_A001_20261114_160154 | 94.2 | 41.73 | 67.97 | close |
| ab_A008_20261114_160856 | – | – | – | error (silence) |
| ab_A043_20261108_142609 | – | – | – | error (silence) |
| ab_A043_20261108_143856 | – | – | – | error (silence) |
| ab_A043_20261108_144314 | – | – | – | error (silence) |
| ab_A043_20261114_153000 | 93.08 | 56.61 | 74.84 | close |
| check_20261108_152813 (reference) | 98.5 | 88.23 | 93.37 | close |

Live measurement 2026-11-14 17:00:55 (A001 Blofeld vs Iridium Set6/PC108, note 72):
Phase A **91.19** (spec_cos 0.9116, env_dtw 0.0876, verdict close), embed **32.0**, combined **61.59**,
LLM **5** — reason per LLM: Iridium **-66.5 dBFS** vs Blofeld **-22.9 dBFS** (level, ~44 dB too quiet).
Log: `recordings/sim_log.jsonl` (ts 20261114_170055, prompt_id `judge-v2-pegel`).

## Findings

- Phase A is level-invariant (normalized) -> high scores despite the level error.
- CLAP embedding and LLM react to level -> embed/combined/LLM break down.
  **Check level normalization before Phase B** (or Scarlett gain Iridium In 5/6 / Iridium master).
- check pair (same device) embed 88.23 -> the embedding fundamentally discriminates.
- Filter cutoff scale (Blofeld raw -> Iridium norm) is wrong with direct norm()
  (A001 on the Iridium: Filter1 416 Hz, DF 199 Hz; Blofeld F1 raw 64 / F2 raw 52) ->
  cutoff calibration (Blofeld CC sweep + peak measurement -> Hz) pending (HANDOVER-2026-11-10 plan 4).
- Osc octave sign fixed 2026-11-14 (`qpat_map.py`: raw-64 instead of 64-raw,
  A001 Osc3 raw 52 -> CoarsePitch 12.0 instead of 36.0; test `test_osc_octave_sign_a001`).

## Rating by the user (post-hoc, 0-100 listening impression) — TODO

| Pair | Blofeld | Iridium | Phase A | embed | combined | LLM | User 0-100 | Comment |
|---|---|---|---|---|---|---|---|---|
| A001 live 170055 | A001 | Set6 PC108 | 91.19 | 32.0 | 61.59 | 5 | | Level -66 dBFS; Filter 416/199 Hz |
| ab_A001_20261114_160154 | A001 | ? | 94.2 | 41.73 | 67.97 | – | | |
| ab_A043_20261114_153000 | A043 | ? | 93.08 | 56.61 | 74.84 | – | | |
| check_20261108_152813 | – | – | 98.5 | 88.23 | 93.37 | – | | Reference |

Ratings as JSON `{"<pair>": 0-100}` -> `python3 scripts/sim_eval_offline.py --ratings ratings.json`
-> Spearman of score/embed/combined against the user rating.

**Caveat post-hoc:** the user rates with knowledge of the numeric scores (not blind).

## Live run 9 presets 2026-11-14 (Set 6 PC108-116, note 72, manual-panel mode)

Iridium PC switching broken (HANDOVER-2026-11-14) -> favorites turned on the panel,
only notes via MIDI; Blofeld PC (Bank A) from the script. Script: `scripts/sim_manual_compare.py`
(mode=`manual_panel`, log `recordings/sim_log.jsonl`, ts 20261114_175046-180616).
**Level normalization before Phase B active** (`norm_pegel=True` in `score_pair_embed`:
embed/LLM on peak-0.5-aligned copies, Phase A + raw peak_dbfs) — Iridium raw still
15-30 dB below Blofeld (serial patches A001/A008/A039/A073 strongest, down to -64.8 dBFS
peak; after norm the RMS distance is small, embed jumps 29 -> 75.6 on A001).
WAVs (level-aligned, peak 0.5) for listening in: `recordings/ab_<LOC>_20261114_*_n72_{blo,irr}.wav`.

| Preset | Iridium PC | ts | Phase A | embed | combined | LLM | Peak A/B dBFS | User 0-100 | Comment |
|---|---|---|---|---|---|---|---|---|---|
| A001 JMX jun | 108 | 175046 | 92.86 | 75.58 | 84.22 | 45 | -19.4 / -47.9 | 70 | Quieter, filter closed too far, LFO1 filter acts too strong |
| A008 Easy Piano | 109 | 175216 | 95.20 | 69.35 | 82.28 | 45 | -25.6 / -64.8 | 45 | Barely audible; presumably 1 octave lower, very strongly filtered |
| A010 Wurly Piano1 | 110 | 175258 | 97.00 | 78.22 | 87.61 | 45 | -44.2 / -42.8 | 80 | High registers different character (hollow square wave) |
| A019 Tines DocT | 111 | 175329 | 95.05 | 87.77 | 91.41 | 45 | -29.4 / -45.5 | 90 | Does not react to aftertouch |
| A022 ModWheelOrgDrive | 112 | 180424 | 94.74 | 83.62 | 89.18 | 45 | -15.5 / -29.2 | 95 | Iridium audibly different character, but very similar; mid harmonic louder on the Blofeld? |
| A039 A Elektro | 113 | 180454 | 96.07 | 77.22 | 86.64 | 45 | -37.9 / -55.3 | 90 | Much quieter; delay on the Blofeld |
| A043 SH Power | 114 | 180519 | 95.02 | 78.38 | 86.70 | 45 | -19.3 / -35.6 | 75 | Blofeld fuller (filter further closed); Iridium strong aftertouch bending; problem Channel->Poly aftertouch |
| A071 Windowed SYNC2FM | 115 | 180547 | 94.38 | 86.71 | 90.54 | 45 | -23.2 / -40.6 | 70 | No sync on the Iridium |
| A073 Chord Hose T | 116 | 180616 | 96.63 | 81.01 | 88.82 | 45 | -27.0 / -53.9 | 85 | Different effects, similar basic character, Blofeld more cutting |

User ratings: `recordings/phaseb_ratings_raw.json`.
Spearman user vs metric (n=9): Phase A **+0.27**, embed **+0.50**, combined **+0.52**
-> embed/combined correlate better with the listening impression than Phase A alone.

## LLM judge comparison 2026-11-15 (d1-omni vs lfm3-omni on the same 9 WAV pairs)

Spike: `scripts/spike_d1_omni_eval.py` -> `recordings/d1_omni_eval_20261115_083238.json`.
d1-omni:600m (Liquid AI, System One `/v1/systemone`, 850 MB) as **score** question
(10 levels) via spectrogram PNGs, two variants: two single images (spec2img) vs
one side-by-side image (spec1img). Baseline lfm3-omni:2b in audio mode.

| Preset | User | lfm3 audio | d1 spec2img | d1 spec1img |
|---|---|---|---|---|
| A001 | 70 | 85 | 95.9 | 87.9 |
| A008 | 45 | 85 | 92.0 | 88.1 |
| A010 | 80 | 85 | 91.7 | 86.1 |
| A019 | 90 | 85 | 95.3 | 88.3 |
| A022 | 95 | 85 | 93.2 | 88.1 |
| A039 | 90 | 85 | 92.7 | 86.1 |
| A043 | 75 | 85 | 92.7 | 88.5 |
| A071 | 70 | 85 | 93.3 | 87.0 |
| A073 | 85 | 85 | 96.0 | 89.4 |

Spearman vs user (n=9): lfm3-audio **+0.35** (degenerate: constant 85 on
level-aligned clips), d1-spec2img **+0.07**, d1-spec1img **+0.12**.

**Finding:** d1-omni is not suitable for synth timbre A/B — scores collapse at
88-96 (music spectrograms all look similar to the model; the audio encoder is
trained on English speech, not music). lfm3-omni in spec mode hallucinates
("screens", Spearman -0.39). **Conclusion: embed/combined (ρ 0.50/0.52) remain the
best automatic proxy scores; the LLM verdict stays informative-only.**
Fix from the spike: `_extract_json` in `sim_embed.py` now a more balanced brace scan
(prose/code fences after the JSON broke the greedy match; 2/9 spec calls failed),
tests in `tests/test_sim_embed.py` (236 passed).

### d1-omni as a difference profiler (noul questions, English) — 600m vs 2b

Spike: `scripts/spike_d1_profile_eval.py` -> `recordings/d1_profile_eval_20261115_084819.json`.
Per pair one `/v1/systemone` call with images=[specA, specB] + 8 questions: `similarity`
(score 10 levels) plus noul `same_pitch, octave_lower, brighter, darker, noisier,
punchier, same_overall`.

| Preset | User | 600m score | 2b score | 2b flags (p>=0.5) |
|---|---|---|---|---|
| A001 | 70 | 95.9 | 63.5 | darker |
| A008 | 45 | 92.0 | 59.3 | octave_lower, brighter, darker |
| A010 | 80 | 91.7 | 64.6 | brighter, darker |
| A019 | 90 | 95.3 | 67.3 | brighter, darker |
| A022 | 95 | 93.2 | 61.9 | darker, noisier |
| A039 | 90 | 92.7 | 65.9 | darker |
| A043 | 75 | 92.7 | 67.0 | brighter, darker |
| A071 | 70 | 93.3 | 67.3 | darker |
| A073 | 85 | 96.0 | 64.3 | octave_lower, brighter, darker |

Spearman vs user: score 600m +0.07 / 2b +0.13; `diff_count` 600m **-0.38**
(correct direction: more flags = lower user rating), `score-k*diff` 600m +0.32;
2b variants worse. Flag prevalence: `darker` 7/9 (600m) resp. 9/9 (2b) — matches
the user comments ("filter closed", "filtered", "Blofeld fuller");
`octave_lower` on 2b only A008 (p=0.50, borderline) + A073 — user suspicion A008
"1 octave lower" thus only weakly confirmed. 600m partly saturates on noul
(octave_lower 9/9, same_pitch 4/9).

**Finding:** d1-omni:2b as an absolute score is more critical (59-67 instead of 92-96), but as
a ranking still weaker than embed/combined (+0.13 vs +0.52, n=9 noisy).
Valuable is the **noul profile as an explanation layer** (flags match the user comments),
not as a score. **Integrated 2026-11-15:** `D1ProfileBackend` in `sim_embed.py`,
`profile` field in result/log, `--profile` in `sim_compare.py` / `sim_manual_compare.py`
/ `bloridium sim compare` (default `d1-omni:2b`). combined remains the Phase-B score.

## Re-measurement 2026-11-15 after P0-1/P0-2 (Set 6 re-imported, note 72, wheel 0/50/100 %)

P0-1 (MatrixDst v14: DF Amount 95, Filter2 Cutoff 104, Volume 115 + template-leak fix)
and P0-2 (AfterTouchDoPoly=0) built, 9 qpats newly onto the stick, re-imported.
Measurement: `sim_manual_compare.py --wheel 0,50,100 --profile` (llm/profile only at wheel 0).
Log: `recordings/sim_log.jsonl` (mode=manual_panel + wheel_pct), WAVs
`recordings/ab_<LOC>_20261115_*_n72_w<pct>_{blo,irr}.wav`.

| Preset | wheel | Phase A | embed | combined | Peak B dBFS (old→new) | Top-Band-DTW (Hz) | d1 flags |
|---|---|---|---|---|---|---|---|
| A001 | 0/50/100 | 93.4/90.3/90.0 | 77.7/74.4/77.3 | 85.6/82.4/83.6 | -47.9→**-37.6** | 2883-5223 | brighter, darker |
| A008 | 0/50/100 | 96.1/95.8/96.1 | 78.2/70.9/72.2 | 87.1/83.3/84.1 | -64.8→**-51.3** | 990-1592 | brighter, darker |
| A010 | 0/50/100 | 96.2/96.0/95.2 | 75.7/76.1/**37.9** | 85.9/86.0/**66.5** | -42.8→-38.0 | 238-302 | brighter, darker |
| A019 | 0/50/100 | 94.9/94.4/93.9 | 83.6/75.4/71.6 | 89.2/84.9/82.8 | -45.5→-40.4 | 990-2883 | brighter, darker |
| A022 | 0/50/100 | 96.7/96.9/98.3 | 79.1/78.0/79.2 | 87.9/87.4/88.8 | -29.2→**-21.0** | 990-2274 | brighter, darker |
| A039 | 0/50/100 | 97.1/98.1/98.3 | 75.5/59.0/**51.0** | 86.3/78.6/**74.7** | -55.3→-47.9 | 693-879 (0%), 1793-2019 (100%) | darker |
| A043 | 0/50/100 | 94.6/95.6/92.1 | 76.6/75.9/71.8 | 85.6/85.7/81.9 | -35.6→-26.7 | 211-302 | brighter, darker |
| A071 (deprio) | 0/50/100 | 93.2/96.9/94.6 | 60.1/68.7/64.0 | 76.6/82.8/79.3 | -40.6→-36.2 | 6624-12000 (highs/sync) | darker, noisier |
| A073 | 0/50/100 | 97.3/94.7/93.1 | 75.5/75.1/65.0 | 86.4/84.9/79.0 | -53.9→-48.9 | 546-615 (0%), 131-166 (50/100%) | brighter, darker, noisier |

**Findings:**
- **P0-1 works**: peak B on all serial presets 7-13 dB better (A022 best,
  -21 dBFS). Serial patches no longer "too dark/quiet" in level.
- **Wheel comparison localizes mod deficits**: strongest wheel divergence on A010
  (embed 75.7→37.9 at 100 %), A039 (→51.0), A073 (→65.0) — mod wheel destinations in the matrix
  mapping deviate; A022 stable (~79 at all levels).
- **band_dtw localizes**: A001/A008 mids/highs 990-5223 Hz; A010/A043 fundamental
  211-302 Hz ("Blofeld fuller"); A071 highs 6.6-12 kHz (missing sync sidebands);
  A073 at wheel>0 low bass 131-166 Hz.
- llm constant 45 (known non-discriminating), d1 profile flags stable.

Findings:
- Phase A 92.9-97.0 (all "close"), combined 82.3-91.4 — ranking: A019 > A071 > A073 >
  A022 > A010 > A039 ~ A043 > A001 > A008.
- LLM constant 45 with identical reasoning ("significantly quieter") despite level-aligned
  clips -> not discriminating in this run, only informative.
- Raw level of the Iridium stays clearly too low on serial patches (Filter>Former)
  (down to -64.8 dBFS peak) — Scarlett gain In 5/6 or patch (DigiFormer amount) clarification open.
- Earlier A001 runs without norm_pegel (ts 174650/174915): embed 44.6/29.0, LLM 15/5.
