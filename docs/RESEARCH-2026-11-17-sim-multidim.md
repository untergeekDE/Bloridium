# Research status 2026-11-17 – two-sound comparison: multiple dimensions + embedding distance

Reason: planned tool that compares two recorded sounds (Blofeld vs Iridium, one A/B pair)
across **multiple dimensions** and additionally delivers an **embedding distance**
value. This document is the state of the art (literature 2025-2026) plus the status
in our own repo – as the basis for the tool's design.

## 1. Status in the repo (what we already measure today)

- **Phase A** (`bloridium/sim.py`, numpy-only): `score = 100·(0.7·spec_cos + 0.3·(1−env_dtw))`
  plus diagnostic fields `band_dtw` (per frequency band DTW over time), `spec_dtw`,
  `frame_cos`, `band_delta_db`, `band_edges_hz`.
- **Phase B** (`bloridium/sim_embed.py`): CLAP GGUF (`larger_clap_music_and_speech-q8_0`,
  512-d, clap.cpp) → `embed_cos` / `embed_score = 100·clip(cos,0,1)`; `combined = 0.5·A + 0.5·embed`;
  ollama LLM judge (lfm3-omni:2b) and d1-omni:2b profile (noul flags) as explanation layer.
  `norm_pegel=True` (peak 0.5 before embed/LLM) is essential (otherwise embed collapses on
  quiet Iridium takes: A001 29 instead of 75.6).
- **Eval against user ratings** (n=9 presets, post-hoc 0-100, `docs/PHASEB-EVAL-2026-11-14.md`):
  Spearman ρ Phase A **+0.27**, embed **+0.50**, combined **+0.52**. LLM scores degenerate
  (lfm3 constant 85; d1-omni as score ρ +0.07/+0.13), d1 flags usable as profile
  (`darker` 9/9 matches the user comments).
- **Known weakness** (HANDOVER-2026-11-09, open point 5): Phase A delivers 93-97, although
  the listening impression is "often very different" → the need for additional dimensions is exactly
  what the planned tool should address.

## 2. State of the art: embedding models and distance metrics

### 2.1 Which embeddings for pairwise audio comparison?

- **CLAP family** (LAION / MS-CLAP): 512-d, L2-normalized, cosine = dot product.
  Variants: `630k-audioset` (general, <10 s), `music_audioset`, `music_speech`,
  `music_speech_audioset`. M2D-CLAP (IEEE 2025): on music tasks, general-purpose and
  music models are comparable; music models only ahead on pitch classification. For our
  **short monophonic synth notes**, `music_and_speech` (GGUF via clap.cpp, Apache-2.0)
  is a good default – we already use it.
- **MuQ / MuQ-MuLan** (music-only, 512/1024-d) and **MERT** (frame-level, 768/1024-d):
  MuQ-MuLan and CLAP without fine-tuning are comparable on ABX/instrument-sim benchmarks
  (arXiv 2601.19109). MERIT (arXiv 2605.27346) uses a MERT backbone + 3 projection heads.
- **clap.cpp** (gorse-io, status 2026-11) directly supports as GGUF **CLAP, CLaMP3,
  MERT v1/v2, MuQ, MuQ-MuLan** – all local, CPU, ROCm-portable. Model switching
  without code change is thus possible (subprocess/HTTP interface stays).
- **Important for us – caveat "Don't CLAP"** (Cheng & Lerch, arXiv 2609.30540, 2026):
  CLAP scores behave like a bag-of-words on fine attribute swaps (e.g. timbre swap in
  captions); LAION-CLAP swap accuracy ≈ 0.51 (chance). Meaning: the global CLAP cosine is good for
  **coarse** similarity, blind for fine synth timbre details
  (individual harmonic deltas). Therefore: embedding distance as one dimension among
  several, not as the sole truth.
- **Timbre-alignment eval** (Tian, Lattner, Saitis, ISMIR 2025, arXiv 2507.07764):
  on 21 psychoacoustic timbre datasets (2 614 pair ratings), **Huang-style
  embeddings from CLAP** (mean+variance over the feature dims of the first Swin blocks,
  concatenated) are the strongest representation, **MFCC stays competitive**, EnCodec-24k
  beats EnCodec-48k. Distance functions: **cosine distance (1−cos) and L2** on
  L2-normalized vectors; eval metrics: triplet agreement (with margin 0.1), Kendall,
  Spearman, NDCG against human ratings. → Recommendation: besides `embed_cos` also
  `embed_l2` and optionally **MFCC cosine** as a robust, cheap component.
- **Cross-cultural similarity** (TISMIR 2026, tismir.341): foundation models beat
  handcrafted features; **CLAP-Music&Speech** highest alignment with human
  similarity judgments; among the features **melody** is the most predictive single factor.

### 2.2 Multidimensional / disentangled similarity (the 2026 trend)

- **MERIT** (arXiv 2605.27346): a single monolithic score is the problem; MERT
  backbone (frozen, layers 3-6 + 23) + **three separate heads for melody, rhythm,
  timbre**, each 128-d on the unit sphere, retrieval per cosine per head → explicit
  per-factor scores. Human eval confirms the selectivity of the heads.
- **Post-hoc CSN disentanglement** (arXiv 2611.14415, Nov 2026): learned masks on
  frozen foundation embeddings (CLAP/MERT/MuQ) gate into attribute-specific
  subspaces; minimal adaptation suffices, improves attribute-specific disentanglement.
- **Instrument-weighted cosine** (arXiv 2601.19109): source separation → per-stem
  embeddings, weighted sum; on ABX with listening tests.
- **Timbre-trait predictor for synthesizers** (arXiv 2606.30369): instead of a global FAD a
  **20-dimensional timbre-trait profile** (Reymore & Huron: bright, percussive, woody …)
  predicted from the CLAP embedding + shallow head (RWC database) – directly transferable to
  "comparison across multiple dimensions" for synth sounds.
- **SynthCloner** (arXiv 2509.24286, 2026): synth sound = **timbre (time-invariant,
  spectral) + ADSR envelope** – exactly the two axes our A/B comparison
  should separate (spectrum vs envelope).

### 2.3 Interpretable timbre dimensions (psychoacoustic features)

Classical correlates (McAdams 2019; Kazazis 2021; Peeters 2011): **spectral centroid**
↔ brightness, **attack time**, **spectral flux**, spread/skewness/slope, odd-to-even
harmonic ratio, harmonic deviation.
DAGA 2025 (Czedik-Eysenberg & Reuter, "Evaluating Timbre-Related Audio Descriptors"):
- **Brightness**: sharpness (DIN 45692 / AudioCommons) r≈0.57-0.73, spectral centroid
  r≈0.55-0.63 – **but strongly pitch-dependent** (at the same note E4: F0 r=−0.16).
  → We measure at a fixed note (72), so centroid/sharpness are valid here.
- **Roughness**: Vassilakis roughness (log) r≈0.82-0.87, dissonance r≈0.67-0.74.
- **Percussiveness**: loudness difference percussive/harmonic after HPSS (librosa
  harmonic-percussive separation) best.
- Embedding similarity to verbal descriptors correlates only partly (r up to 0.65 for
  "bright") → classical features are more reliable for the *named* dimensions than
  CLAP cosine against text.

### 2.4 Distance metrics and comparison methodology (MIR standard)

- Distances in the music-similarity literature (CMMR 2021 survey): **Manhattan, Euclidean,
  cosine, KL, Earth Mover's Distance (EMD)**, sequence distances (Levenshtein/LCS).
  For embeddings: **cosine distance + L2** (standard); EMD rather for histogram features
  (chroma, MFCC histograms).
- Pairwise comparison of short clips: global vector (mean-pooled) → cosine/L2; for
  temporal structure: **DTW/soft-DTW on envelopes** (arXiv 2506.22628, sound matching:
  DTW envelope recommended for amplitude-modulated signals; spectrogram L1 without alignment
  sensitive to local time shifts). We already use DTW on env + bands.
- **Eval against humans**: triplet agreement / ABX with margin, Spearman/Kendall against
  ratings (we do this with ρ against post-hoc 0-100; document the post-hoc caveat).
- **Preprocessing is critical**: level normalization before embedding comparison (CLAP reacts
  to gain – our norm_pegel finding), fixed pitch, mono, 48 kHz; CLAP window 10 s with
  repeat-padding of short clips (clap.cpp behavior, verified).

### 2.5 LLM judges as score – negative finding (repo + literature)

- Own eval: lfm3-omni:2b constant 85 (ρ +0.35 degenerate), d1-omni:600m collapses
  88-96 (ρ +0.07), spec mode hallucinates (ρ −0.39). d1-omni:2b as noul profiler
  (darker/octave_lower/brighter…) matches the user comments → **explanation layer yes,
  score no**.
- Literature confirms: "Don't CLAP" (see above) and FIGMA (ACL 2026): CLAP & Co. are
  unreliable for fine musical attributes (key, chords, fine timbre bindings).
- **Finding confirmed 2026-11-17 (user recall vs `docs/PHASEB-EVAL-2026-11-14.md`):
  d1-omni:2b vs lfm3-omni:2b on the same 9 WAV pairs — as a score both weak
  (d1:600m collapses 88-96, ρ +0.07; d1:2b 59-67, ρ +0.13; lfm3 audio constant 85,
  ρ +0.35 degenerate without variance; lfm3 spec hallucinates, ρ −0.39). As
  **description-encoded dimensions** (noul profile via `/v1/systemone`) the
  decision model was somewhat better: flags match the user comments (`darker` 9/9,
  `octave_lower` A008 only p=0.50 borderline), diff_count ρ −0.38, score−k·diff +0.32 —
  overall though a smaller gain; the best proxy scores remain embed ρ +0.50 /
  combined ρ +0.52 (n=9). → the d1 profile stays an explanation layer (`profile` field), never a score.

## 3. Consequences for the planned tool (proposal)

Comparison result as JSON with two levels:

1. **Dimension comparison** (interpretable, per dimension 0-100 or delta):
   - *Spectrum/timbre*: `spec_cos` (global, existing), `band_dtw`/`band_delta_db` with
     `band_edges_hz` (localization: filter→low bands, harmonics→high — proven),
     plus psychoacoustic traits as deltas: `d_centroid` (brightness), `d_sharpness`,
     `d_roughness` (Vassilakis log), `d_percussive` (HPSS-Δloudness), `d_flatness`.
   - *Time/envelope*: `env_dtw` (existing), attack-time delta, `frame_cos` (LFO/mod
     divergence over time, existing).
   - *Pitch*: F0 delta in semitones (at the same note ≈0; localizes octave errors like
     the A008 suspicion better than the d1 flag p=0.50).
   - *Semantic*: d1 profile flags (existing, explanation layer).
2. **Embedding distance** (hard, numeric):
   - `embed_cos` + `embed_l2` on CLAP-512-d (existing `embed_cos`; L2 added),
     optionally `mfcc_cos` (robust, competitive per ISMIR 2025) as a cheap second layer,
     optionally Huang-style embedding distance from CLAP (best timbre alignment 2025) as
     `timbre_dist` – extraction: mean/var of the first Swin blocks (clap.cpp only delivers
     the final vector → HF reference or clap.cpp patch; spike needed).
   - Score mapping: linearly clipped (existing), calibration against user ratings via
     Spearman (eval as before).
3. **Preprocessing mandatory**: `norm_pegel` (peak 0.5), fixed note, mono, 48 kHz – otherwise
   embed/LLM are worthless (proven).
4. **Do not use the LLM score as a metric**; only profile/explanation.

Open design questions for the tool (next step):
- Huang-style embedding: patch clap.cpp vs HF reference (eval only) vs drop it.
- MFCC cosine as second embedding distance: yes (cheap, robust) – numpy implementation
  without librosa.
- Psychoacoustic traits: own numpy implementation (DIN sharpness, Vassilakis roughness,
  HPSS via median filtering) – no new dependency.

## 4. Addendum 2026-11-17: locally available models & instruments (inventory of this machine + status)

Two levels: **(a) runnable models** for embedding distance / verdict, **(b) classical
DSP/parameter instruments** for the interpretable dimensions.

### 4.1 Models – what runs locally here or is readily downloadable

| Instrument | Where | Local status | License | For our A/B comparison (short monophonic synth notes) |
|---|---|---|---|---|
| **CLAP `larger_clap_music_and_speech` Q8_0 GGUF** (512-d, 48 kHz) | `models/` + clap-cpp 0.1.1 (pip) | ✅ in use (`ClapBackend`) | Apache-2.0 | **primary embedding** (`embed_cos`/`embed_l2`) |
| **clap.cpp GGUF family** (gorse-io@HF): all CLAP variants, **CLaMP3** (768-d, 24 kHz), **MERT v1 95M/330M + v2**, **MuQ** (1024-d), **MuQ-MuLan** (512-d, text+audio) | `hf download gorse-io/...` → `models/`, CPU, ROCm-portable | ⬇️ downloadable, ~0.2-2 GB | CLAP Apache-2.0, CLaMP3 MIT, **MERT/MuQ CC-BY-NC-4.0** (research/non-commercial only – note for the Strix-Halo migration) | model switch per path, no code change. **MuQ-MuLan**: per arXiv 2510.14249 best Pearson/Spearman (0.535/0.530) on EQ/reverb timbre semantics – relevant for filter deltas; LAION-CLAP most consistent instrumental timbre |
| **Music2Latent** | HF via torch 2.2.2 + transformers 4.47.1 (installed) | ⬇️ downloadable (reference/eval) | research | per ISMIR 2025 (arXiv 2507.07764) aligned **better than CLAP** with human timbre ratings, high compression, music+speech |
| **ollama local**: `d1-omni:2b` (4.4 GB), `d1-omni:600m`, `lfm3-omni:2b` (2.4 GB) | `ollama list` | ✅ present | LFM Open License | d1-omni:2b as noul profiler (integrated), lfm3 audio judge (degenerate as score) — **explanation layer, not metric** |
| **ollama library**: `lfm3-audio:2b` (2.1 GB, pure audio LM, 16 kHz), `qwen2.5-omni-3b/7b`, `qwen3-omni` (GGUF) | pull | ✅ pulled + spike 2026-11-17 | LFM Open License | **lfm3-audio:2b tested (ollama 0.40.16):** `/api/chat` with `audio` field → 200 but audio doesn't arrive ("you haven't provided any audio"); `content` as part list → 400 (not supported); only `/v1/chat/completions` with `input_audio` delivers audio (200), but **unreliable on pure synth tones** (440 Hz → "low vocalization", 220 Hz → "440 Hz" wrong); `/api/embeddings` + `/api/embed` → "does not support embeddings" → **no embedding model** (generative audio LM). Conclusion: not as judge/metric; embeddings stay CLAP GGUF (+ MuQ-MuLan/MERT/MuQ GGUF, MFCC). Qwen-Omni: candidate for captioner; same degeneration risk as d1/lfm3 |
| **jina-embeddings-v2-base-de** (322 MB) | ollama ✅ | Text embeddings DE | Apache-2.0 | text side only (e.g. description comparison); the CLAP text encoder is RoBERTa (EN) → prompts in English |
| **CLAP text encoder** (in the GGUF) via `clap embedding --text` | clap.cpp ✅ | zero-shot: project the audio embedding against text prompts ("bright synth pad", "dull filtered bass"…) | Apache-2.0 | **per-attribute scores without a new model** (brightness/roughness as text probes) – DAGA 2025: embedding↔"bright" only r≈0.65, so complementary to DSP features |
| **timbremetrics** (Python package, Tian/Lattner/Saitis) | pip | ⬇️ | — | **eval instrument**: 21 timbre datasets (334 samples, 2 614 ratings), triplet agreement/Kendall/Spearman/NDCG — with this we evaluate our metrics against human ratings (instead of only our n=9) |
| **NSynth** (305 979 monophonic notes, 1 006 instruments, pitch/timbre/envelope labels) | HF ✅ | dataset | CC-BY | **calibration dataset**: exactly our setting (single sustained notes); e.g. self-similarity of CLAP/MFCC on NSynth electronic/synthetic as a reference scale |

### 4.2 Status: which representation beats which (for timbre/short notes)

- **timbremetrics benchmark** (arXiv 2507.07764; package `timbremetrics`): LAION-CLAP 70.8-71.8 % triplet agreement, **MFCC 68.7 %**, **PANNs (AudioSet) only 61.4 %**, EnCodec-24k > 48k, Music2Latent strong, **Huang-style embedding from CLAP internals best**. → deep models are only marginally better than MFCC for fine timbre; don't bother with PANNs/VGGish.
- **Effect-induced timbre changes** (arXiv 2510.14249): **MuQ-MuLan** strongest monotone/linear mapping (Pearson 0.535), LAION-CLAP most consistent across instruments; reverb is encoded better than EQ → for our filter deltas (EQ-like) CLAP/MuQ-MuLan are ok, but limited.
- **"Don't CLAP"** (arXiv 2609.30540): CLAP score ≈ bag-of-words on fine attribute swaps → global embedding distance is a **coarse** indicator, fine deltas need DSP features (section 2.3).
- **Synth-specific (parameter↔audio)**: **Synth-JEPA** (arXiv 2609.31024, Hayes/Tian/Lattner 2026; Surge XT, 85 % listening preference, renderer-free objective), **FM-SynAPSE/DX7-GNN** (arXiv 2608.18226; audio↔parameter joint space, DX7AllTheWeb 31k presets), DDSynth-RL (Dexed, arXiv 2608.03032), SynthRL (IJCAI 2025). → state of the art for the **parameter level**: we have both sides (Blofeld-SNDD ↔ qpat) – a direct parameter diff (already `qpat_map` overrides/unmapped) is the "instrument" without rendering; joint audio-parameter embeddings are future work (training needed – against our no-training rule).
- **Sound-matching losses** (arXiv 2506.22628): MSS, **wMFCC**, CLAP, P-loss, soft-DTW (envelope), JTFS — wMFCC and DTW envelope are the practically relevant ones for us (wMFCC = weighted MFCC distance, cheap in numpy/scipy).

### 4.3 DSP instruments (numpy/scipy only, no new dependency; scipy 1.11.4 is installed)

- Spectral: log-mel/log-STFT (numpy FFT), **MFCC/wMFCC** (DCT via scipy), centroid, spread, skewness, slope, rolloff, flatness, crest, odd-to-even harmonic ratio, harmonic deviation (Peeters/Kazazis).
- Psychoacoustic (DAGA 2025): **DIN 45692 sharpness** ↔ brightness (r≈0.57-0.73), **Vassilakis roughness (log)** ↔ roughness (r≈0.82-0.87), **HPSS-Δloudness** (median filter via scipy.ndimage) ↔ percussiveness.
- Temporal: env RMS + **DTW** (we have it), attack time, spectral flux, frame_cos (we have it).
- Pitch: F0 via autocorrelation (scipy) → octave deltas in semitones (better than the d1 flag for the A008 suspicion).
- Parameter level (we have it): SNDD/qpat diff, `unmapped` lists.

### 4.4 Spike 2026-11-17: CLAP vs MERT on our 9 pairs (own data)

`scripts/spike_mert_clap_eval.py` (result: `recordings/mert_clap_eval_20261117_213852.json`):
the 9 level-aligned WAV pairs `ab_<LOC>_20261115_*_n72_w0_{blo,irr}.wav` embedded with three
GGUFs via clap-cpp, cosine score vs user ratings (`phaseb_ratings_raw.json`):

| Model (GGUF, clap-cpp) | Scores (range) | Spearman ρ vs user (n=9) |
|---|---|---|
| `larger_clap_music_and_speech-q8_0` (previous production) | 60-84 | **+0.227** |
| `larger_clap_music-q8_0` (music-only) | 84-99 (compressed at the top) | **+0.462** |
| `MERT-v1-95M-q8_0` (24 kHz, resample) | 76-92 | **+0.454** |

Findings: on our data **CLAP music-only ≈ MERT**, both clearly ahead of the previous
`music_and_speech`; MERT has the better score spread (less saturation at the top), CLAP-music
the slightly higher rank correlation. Caveats: n=9 noisy; MERT here only mean-pooled
(768-d), MERIT-style layer concat (3-6+23) not possible via GGUF; MERT license CC-BY-NC-4.0.

### 4.5 Consequence for the tool (updated)

- **Embedding distance**: primary **CLAP music-only GGUF** (`larger_clap_music-q8_0`, spike 4.4: ρ +0.46 > music_and_speech +0.23 on our pairs; music-only also ahead on pitch per M2D-CLAP) with `embed_cos` + `embed_l2`; **second distance: wMFCC/MFCC cosine** (numpy, competitive per the benchmark); optional as third: **MERT-v1-95M GGUF** via the same clap.cpp path (ρ +0.45, better score spread; license CC-BY-NC) or MuQ-MuLan GGUF for EQ/reverb deltas; Music2Latent + Huang-style only as HF reference in the eval (torch present, transformers 4.47.1 has no MERT – the GGUF path is the right one).
- **Per-attribute scores without training**: CLAP text prompts (EN) for bright/dull/rough/percussive + DSP traits as hard deltas.
- **Eval against human ratings**: `timbremetrics` package + NSynth as reference scale, instead of only our own n=9 Spearman.
- **LLM verdicts** (lfm3-omni audio, d1-omni profile, optional qwen2.5-omni): explanation layer only — own finding + "Don't CLAP".

## 5. References

- Tian, Lattner, Saitis: "Assessing the Alignment of Audio Representations with Timbre
  Similarity Ratings", ISMIR 2025, arXiv:2507.07764 (Huang-style embeddings, MFCC
  competitive, cosine+L2, triplet agreement).
- Cheng & Lerch: "Don't CLAP: Are Music-Text Models Bag-of-Words?", arXiv:2609.30540 (2026).
- MERIT: "Learning Disentangled Music Representations for Audio Similarity",
  arXiv:2605.27346 (2026) – 3 heads melody/rhythm/timbre on MERT.
- arXiv:2611.14415 (Nov 2026): post-hoc CSN disentanglement of frozen foundation embeddings.
- arXiv:2601.19109 (Jan 2026): CLAP/MuQ-MuLan on ABX; instrument-weighted cosine via MSS.
- TISMIR 2026: "Cross-Cultural Music Similarity…", tismir.341 – CLAP-Music&Speech best alignment.
- arXiv:2606.30369 (2026): timbre-trait predictor (20 Reymore-Huron qualia) on CLAP for
  synthesizer eval instead of FAD.
- SynthCloner, arXiv:2509.24286 (2026): timbre-vs-ADSR disentanglement for synth sounds.
- arXiv:2506.22628 (2025): sound-matching losses – soft-DTW on envelope, JTFS, MSS, P-loss.
- Czedik-Eysenberg & Reuter, DAGA 2025: sharpness↔brightness, Vassilakis(log)↔roughness,
  HPSS-Δloudness↔percussiveness; pitch dependence of brightness.
- McAdams 2019 (timbre chapter); Kazazis 2021 (JASA, ordinal scaling spectral descriptors);
  Peeters 2011 (descriptor set); CMMR 2021 survey (distance metrics: Manhattan/Euclidean/
  cosine/KL/EMD/Levenshtein).
- M2D-CLAP, IEEE SPL 2025: general vs music CLAP on music tasks.
- clap.cpp (gorse-io, status 2026-11): GGUF support CLAP/CLaMP3/MERT/MuQ/MuQ-MuLan,
  10-s window with repeat-pad, 48 kHz.
- Repo-internal: `docs/PHASEB-EVAL-2026-11-14.md`, `docs/HANDOVER-2026-11-15.md`,
  `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md`, `bloridium/sim.py`,
  `bloridium/sim_embed.py`.
