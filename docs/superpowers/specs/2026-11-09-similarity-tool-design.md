# Design: similarity tool Blofeld ↔ Iridium (approach A: spectral + envelope)

Date: 2026-11-09 · Status: draft for approval

## Intent & Why
Toolset that transfers a first approximation of a Blofeld sound to the Iridium
(qpat conversion + live CCs). The similarity tool closes the loop:
sound doesn't sound like the original → measure how much → turn parameters → measure again.

Four goals (given by the human):
1. **Feedback to the human** — how much does the Iridium sound deviate from the Blofeld original?
2. **Improving the transfer scripts** — score as an objective metric instead of the ear.
3. **LLM-supported exploration** — systematically turn parameters until the score rises
   (needs a good CC map: `docs/midi-maps/iridium_pid_map.csv` + `iridium_rdb.mimap`).
4. **Training data for a later mapping model** — every measurement as a logged dataset.

## Goals / Non-goals / Anti-goals
- Goals: score 0-100 + interpretable deviations (per frequency band, envelope);
  offline on existing takes AND live (change CC → measure); JSONL log per run.
- Non-goals (Phase A): ML embeddings (researched in parallel, later Phase B);
  polyphonic sounds; sample-based oscillators.
- Anti-goals: no "ear replacement" claim, only a first approximation; no training in Phase A.

## Constraints
- macOS, Python 3.10, **numpy only in Phase A** (no new ML dependency).
- Recording: `bloridium.audio.record` (ffmpeg/avfoundation, Scarlett 18i8, 48 kHz,
  Blofeld In 3/4 = ch (2,3), Iridium In 5/6 = ch (4,5)).
- MIDI: Blofeld + Iridium on the Launchpad Pro 3 DIN out (`bloridium/midi.py`,
  Blofeld ch5/idx4, Iridium Parts ch6-9/idx5-8). USB is unplugged because of the ground loop.
- Iridium patches only via qpat import (stick); CCs controllable live.
- Existing artifacts: A/B .npy takes (`spike_ab_compare.py`), `recordings/*.json`,
  `docs/refs/qpat_params_v14/v15`, `docs/midi-maps/iridium_pid_map.csv`.

## Approaches
- **A (chosen): spectral + envelope, numpy-only.** Log-magnitude spectrogram
  (log bands ~40 Hz-12 kHz) + RMS envelope; distance = cosine on the mean
  sustain spectrogram + DTW on the envelope; score 0-100 weighted.
  Trade-off: less "semantic" than embeddings, but interpretable
  (per-band dB → direct parameter feedback) and without a model download.
- B: audio embedding — **research complete** (subagent, 2026-11-09). Top candidates
  (all ≤ 4 GB, CPU-capable):
  - **LAION CLAP2-xxs/xs** ([HF laion/clap2-xxs-audioxl-s1B](https://huggingface.co/laion/clap2-xxs-audioxl-s1B), 109-200 MB, Apache-2.0, 224/320-d, 32 kHz, no 10-s padding → ideal for 1-2-s clips) — recommendation for the embedding score.
  - **MERT-v1-95M** ([HF m-a-p/MERT-v1-95M](https://huggingface.co/m-a-p/MERT-v1-95M), 378 MB, 768-d @ 24 kHz, purely musical) — best timbre resolution, but **CC-BY-NC** (internal/experimental only).
  - **EnCodec 48 kHz** ([HF facebook/encodec_48khz](https://huggingface.co/facebook/encodec_48khz), 76 MB, MIT) — encoder latent/code histogram as timbre signature (FAD approach), full 48 kHz bandwidth.
  - 16 kHz models (VGGish, BEATs, wav2vec2, music2vec) only as a fast reference because of synth harmonics > 8 kHz.
  - **Combination principle (recommended):** neural embedding score (CLAP2) + classical
    features (log-mel/MFCC/chroma/centroid) = more robust score + interpretable deltas.
  Trade-off: model download, score harder to interpret than pure band deltas.
- C: pure qpat parameter comparison (no audio) — as a quick pre-check
  added (cf. `docs/DONSOLARIS-COMPARE.md`), not as a replacement.

## Design (Phase A)
New module `bloridium/sim.py`:
- `features(x, sr)` → `(log_spec [n_bands × n_frames], env_rms [n_frames], band_edges)`
  (FFT + Hann, log-spaced bands 40 Hz-12 kHz, ~50 ms hop).
- `compare(feat_a, feat_b)` → `{"score": 0-100, "spec_cos": .., "env_dtw": ..,
  "band_delta_db": [...], "verdict": "close/medium/far"}`.
- Sustain window 0.5-1.2 s after note-on (filter env distorts the attack — HANDOVER).
- `log_run(result, meta)` → `recordings/sim_log.jsonl` (features summary + score + meta:
  Blofeld loc, Iridium slot, CC states, timestamp) → training data for goal 4.

Scripts (consistent with `scripts/spike_*.py`):
- `scripts/sim_compare.py` — measures fresh (note on both synths, record, compare)
  OR evaluates existing .npy takes (`--npy dir`). Output: score + band deltas
  + JSONL log.
- `scripts/sim_live.py` — turn loop for goal 3: loads the CC map (`iridium_pid_map.csv`),
  takes a parameter name or CC, sets the value on the Iridium (ch6-9), measures, logs.
  `--auto` later: LLM proposes the next change.

CLI later: `bloridium sim compare ...` / `bloridium sim live ...` (Phase B).

CC map integration: `bloridium/ccmap.py` exists (CSV names → CC). Extend with the
pid column from `iridium_pid_map.csv`, so `sim_live` knows parameter names ↔ CC ↔ pid.

## Phase B (after Phase A, optional)
- `bloridium/sim_embed.py`: optional embedding score via CLAP2-xxs (HuggingFace, 109 MB,
  Apache-2.0) as a second score; combination with the Phase A score (weighted) in the JSONL log.
- Only if the license is ok: MERT-95M for finer timbre deltas (CC-BY-NC → internal only).
- Embeddings also land in `sim_log.jsonl` → features for goal 4 (mapping model).

## What the builder still has to clarify (proposals = my calls)
- DTW implementation: own small DP (numpy) instead of a scipy dependency → call: own DP.
- Band count: 48 log bands → call: 48.
- Score weighting: 70 % spectrogram cosine, 30 % envelope DTW → call: 70/30.
- JSONL path: `recordings/sim_log.jsonl` → call: there.

## Next step after approval
Plan via superpowers:writing-plans, then TDD implementation (test_sim.py first).
