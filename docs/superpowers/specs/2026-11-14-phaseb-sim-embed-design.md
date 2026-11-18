# Design: Phase B – model-based sound comparison (embedding score + LLM verdict)

Date: 2026-11-14 · Status: draft for approval

## Intent & Why
Phase A (`bloridium/sim.py`, numpy-only: 70 % spectrogram cosine + 30 % envelope DTW)
delivers a mechanical number, but no impression of the *character* of a sound –
observed: Blofeld↔Iridium scores 93-97, although the sound is "often very different"
(HANDOVER-2026-11-09, open point 5). Phase B adds two model-based components:

1. **Embedding score (numeric, hard):** CLAP (music-trained) as GGUF via clap.cpp
   (llama.cpp fork) → 512-d audio embeddings, cosine = embedding score 0-100.
2. **LLM verdict (semantic, explanatory):** an omni-audio model behind ollama compares
   both clips and answers with JSON `{score, summary, differences[]}` – the "why".

Both run **offline on existing takes** (the computer is currently not connected to the synths:
4 A/B .npy pairs in `recordings/` + `sim_log.jsonl`). Architecture requirement from the user:
**ollama or llama.cpp or MLX**; migration to AMD Strix Halo with ROCm is planned.

## Goals / Non-goals / Anti-goals

- Goals:
  - `embed_score` 0-100 per A/B pair, logged in `recordings/sim_log.jsonl` next to Phase A.
  - Optional LLM verdict (text + parsed score) in the same log.
  - Combined score (weighted mean of the Phase A and embedding score).
  - Offline eval on all 4 existing .npy pairs: does the embedding score correlate
    better with the listening impression ("character different") than Phase A alone?
  - Runtime abstraction: backend switch (CPU now, ROCm later) without code change.
- Non-goals:
  - No training/fine-tuning, no MLX port (MLX doesn't run on AMD → dead end for
    Strix Halo; deliberately not chosen).
  - No Whisper/ASR; HF/transformers (CLAP2-xxs) only as a *reference* in tests, not
    as a production backend.
  - `sim_live.py`/`sim_cc_sweep.py` without `--embed` in this phase.
  - No DB schema migration: `ab_runs.report_json` is a JSON blob and takes the
    new keys `sim`/`embed`/`llm` without a change.
- Anti-goals:
  - No "ear replacement" claim; Phase B is a second metric, not the truth.
  - No new heavy runtime dependencies in the core (numpy stays; models run
    externally via subprocess/HTTP).

## Constraints

- macOS, Python 3.10.13; numpy-only in the core. Already present: PIL 10.2, requests,
  httpx, matplotlib (no soundfile → WAV via stdlib `wave`).
- ollama 0.40.16 installed (`/usr/local/bin/ollama`), no models pulled yet.
- clap.cpp not built; `pip install clap-cpp` (Python bindings) as the first choice.
- License: CLAP `larger_clap_music_and_speech` = Apache-2.0 (ok). LLM: **lfm3-omni:2b**
  (LFM Open License, 2 GB) as default; Qwen2.5-Omni-GGUF only optional (qwen-research).
- Unresolved (resolved in the spike, plan step 1): does ollama 0.40.16 accept
  audio directly in the chat API (`audio` field)? If not → fallback: spectrogram PNG
  (PIL) as the `images` field to a vision model. Both behind the same backend interface.
- Models live locally in `models/` (gitignored), never in the repo.
- Portability Strix Halo/ROCm: clap.cpp is ggml-based (HIP/ROCm build exists),
  ollama has official ROCm builds. Access only via subprocess/HTTP → no code change.

## Approaches

- **A (chosen, numeric): clap.cpp + `gorse-io/larger_clap_music_and_speech-GGUF`
  (Q8_0, 208 MB, 48 kHz, 512-d, Apache-2.0, music-trained).** Embedding via
  `pip clap-cpp` bindings, fallback: clap.cpp binary via subprocess.
  Cosine of the embeddings → `embed_score`. Trade-off: only a number, no "why"; but
  small, fast, ROCm-portable.
- **B (chosen, semantic, optional per flag): ollama + lfm3-omni:2b.** Prompt with
  both clips (audio directly or spectrogram PNG) → JSON verdict. Trade-off:
  bigger/slower, more subjective score; but delivers the textual reasoning.
- C: MLX port (mlx-audio / CLAP→MLX) — **rejected**: fastest on Apple Silicon,
  but not runnable on AMD/ROCm → contradicts the migration requirement.
- D: HF transformers CLAP2-xxs as production backend — **rejected** (requirement: ollama/
  llama.cpp/MLX); stays as a test reference (torch 2.2.2 + transformers 4.47.1 are
  installed).

## Design

### New module `bloridium/sim_embed.py` (pure, testable; models external)

- `write_wav(x, sr, path)` — stdlib `wave`, float32 → int16 PCM mono (clap.cpp takes WAV).
- `render_spec_png(x, sr, path)` — Phase-A log spectrogram as PNG via PIL
  (for the ollama vision fallback).
- `class ClapBackend`: `__init__(model_path)`, `embed(x, sr) -> np.ndarray (512,)`.
  Internally: first the `clap-cpp` Python binding, else `clap embedding --model M --audio WAV`
  as subprocess, parse the result JSON. No download in the class – the path comes from outside.
  **Input convention (builder-check Q3, my call):** the whole recording, mono-averaged;
  resampling to 48 kHz only if needed (numpy, linear); padding to the 10-s window
  is done by the backend (clap.cpp repeat-pads shorter clips itself). Consistent with
  Phase A, which also featurizes the whole recording – comparisons across pairs
  of different lengths (126 080 vs 133 969 samples) stay comparable.
- `DEFAULT_JUDGE_PROMPT` (builder-check Q4, my call): German prompt, anchor
  "100 = indistinguishable, 0 = completely different sound", contract
  `{"score": 0-100, "summary": "...", "differences": ["...", ...]}` – `differences` is
  an array of strings. The prompt is overridable and lands in the log (versioning
  of the verdicts via model/prompt ID).
- `class OllamaBackend`: `__init__(model="lfm3-omni:2b", host="http://localhost:11434")`;
  `available()` (GET /api/tags); `judge(x_a, x_b, sr, prompt=DEFAULT_JUDGE_PROMPT) -> dict` –
  build the chat request, try the `audio` field, on 4xx fall back to spectrogram PNG + `images`;
  extract the answer JSON from the content (first {...} object), parse robustly.
  **Lifecycle (builder-check Q6, my call):** `ollama serve` is assumed to be running
  (menubar app now, systemd on Strix Halo); `fetch_models.py` only pulls models,
  starts no server. `available() == False` → see the degrade rule below.
- `embed_compare(ea, eb) -> {"embed_cos", "embed_score"}` — score = 100·clip(cos,0,1),
  linear (validate the mapping curve in the eval; sigmoid optional).
- `score_pair_embed(x_blo, x_irr, sr, meta, log_path, clap=None, ollama=None, use_llm=False)`:
  runs Phase A (`sim.score_pair` without double logging) + embedding (+ LLM) and builds
  the combined result:
  ```json
  {"score": <PhaseA>, "embed_cos": .., "embed_score": .., "combined": ..,
   "llm": {"model": .., "score": .., "summary": .., "differences": [..], "mode": "audio|spec"},
   "verdict": ..}
  ```
  `combined = 0.5·score + 0.5·embed_score` (LLM score only informative until the eval validates it).
  One JSONL entry per run in `recordings/sim_log.jsonl`, meta incl. backends/model names.

### Scripts / CLI (consistent with the existing style)

- `scripts/sim_compare.py`: new flags `--embed` (CLAP score) and `--llm` (ollama verdict),
  effective on `--npy` and `--live`.
- `scripts/sim_eval_offline.py`: evaluates all existing .npy pairs in `recordings/`
  (ab_*_blofeld.npy vs ab_*_iridium.npy) with Phase A + embedding, writes
  `recordings/phaseb_eval_<ts>.json` + prints the table (pair, PhaseA, embed, combined).
- `scripts/fetch_models.py`: `python3 scripts/fetch_models.py` downloads the CLAP GGUF (Q8_0)
  via `hf download` to `models/`, `ollama pull lfm3-omni:2b`, optionally `pip install clap-cpp`.
- CLI: new subcommand `bloridium sim compare --npy A B [--embed] [--llm]`
  (per the spec 2026-11-09 that was planned for Phase B); the scripts stay thin wrappers.
- `.gitignore`: add `models/`.

### Tests (`tests/test_sim_embed.py`, offline, no model download)

- `write_wav` roundtrip (readable via `wave`, correct length/level).
- `render_spec_png` produces a valid PNG (PIL opens, size > 0).
- `ClapBackend`/`OllamaBackend` with mocked subprocess/HTTP (monkeypatch): payload form,
  JSON extraction from LLM text with surrounding prose, fallback audio→spec on 400.
- `embed_compare`: cos=1 → 100, cos=0 → 0, negative → 0.
- `score_pair_embed` with fake backends on the real `recordings/ab_*.npy` pairs:
  log schema (one JSONL entry, fields complete), combined score in the 0-100 range.
- Integration (marked slow, skipped without a model): real CLAP GGUF on one .npy pair.

### Degrade rule on a missing backend (builder-check Q5, my call)

`--embed` without a CLAP GGUF or `--llm` without a running ollama → **no hard fail**: warning
on stderr, Phase A runs normally, the JSONL entry contains the backend fields as `null`
plus `"backend_error": "..."` (downstream training thus explicitly sees that data is missing).
Exit code: 0 if Phase A is ok (existing behavior: 1 only on a Phase-A `error`);
`--strict` switches to a hard fail (exit 3) for CI/sweeps that need embeddings.

### Eval (proof that Phase B helps)

Procedure (Q1 decided, post-hoc): `sim_eval_offline.py` evaluates all 4 .npy pairs
(`ab_*_blofeld.npy` vs `ab_*_iridium.npy`, incl. `check_*`) with Phase A + embedding
(+ combined), writes `recordings/phaseb_eval_<ts>.json` and prints the table.
After that the user enters a 0-100 rating of the listening impression ("how similar does the pair sound?")
per pair in `docs/PHASEB-EVAL-2026-11-14.md`; the script can
recompute the Spearman rank correlation of the three metrics against these
ratings with `--ratings` (n=4 → rank correlation; the post-hoc caveat is documented).
The decision "combined as the new default score" is made on the basis of this evaluation.

## Builder-Check 2026-11-12→14 (subagent ses_e25f5d23…): resolutions

- **Q1 ground truth — DECIDED (user 2026-11-14): post-hoc.** No
  pre-registered JSON. Procedure: `sim_eval_offline.py` computes Phase A + embed + combined
  for the 4 pairs and writes the table + `recordings/phaseb_eval_<ts>.json`; the
  user then rates each pair **0-100** (listening impression "how similar?") and enters
  the ratings in `docs/PHASEB-EVAL-2026-11-14.md`. The eval script can add the Spearman rank correlation
  against these ratings afterwards (`--ratings` reads the eval doc/JSON). The post-hoc caveat (scores can
  color the judgment) is noted in the eval doc.
- **Q2 scope — DECIDED (user 2026-11-14): full integration also in `ab`.**
  - `workflow.measure_ab(..., embed=False, llm=False)`: after the existing report,
    additionally `sim.compare` (Phase A) + embedding (+ LLM) on the recorded signals;
    the result lands as new keys `"sim"`, `"embed"`, `"llm"` in the report dict →
    the `report_json` blob in `ab_runs` carries them (**no schema migration needed**,
    report_json is JSON text; SCHEMA_VERSION stays). `cmd_ab` gets `--embed/--llm`
    and passes them through.
  - New CLI `bloridium sim compare --npy A B [--embed] [--llm]` and
    `--live [--note N] [--dur S] [--blofeld LOC] [--iridium-slot S] [--embed] [--llm]`
    → logs via `sim_embed.score_pair_embed` to `recordings/sim_log.jsonl`
    (one entry, all metrics). No double logging: `measure_ab` calls the features
    directly (`log_path=None`), not `sim.score_pair`.
  - `scripts/sim_compare.py` also gets `--embed/--llm` (effective on `--npy` and `--live`).
  - `sim_live.py` / `sim_cc_sweep.py` stay without `--embed` in this phase (non-goal;
    adopt `sim_embed` later analogously).
- **Q3 CLAP input:** my call — whole recording mono, backend pads (see Design).
- **Q4 prompt/anchor:** my call — German `DEFAULT_JUDGE_PROMPT`, 100 = indistinguishable,
  `differences` = string array (see Design).
- **Q5 backend missing:** my call — degrade + warn + `null` fields in the log, exit 0;
  `--strict` → exit 3 (see the degrade rule).
- **Q6 ollama lifecycle:** my call — the server is assumed to run; `fetch_models.py`
  only pulls.

## What the builder still has to clarify (proposals = my calls)

- Spike (plan step 1): ollama 0.40.16 + lfm3-omni:2b – does audio work in the chat API?
  The result decides the default mode (audio vs. spec PNG); both are implemented.
- CLAP access: `pip install clap-cpp` first, else build clap.cpp (cmake).
  Call: pip first.
- Cosine→score: linearly clipped. Call: linear, check the curve in the eval.
- Combined weighting: 50/50 PhaseA/embedding, LLM only text. Call: 50/50.
- `models/` in `.gitignore`. Call: yes.

## Next step after approval

Plan via superpowers:writing-plans (spike first: verify ollama audio capability + CLAP GGUF download),
then TDD implementation (test_sim_embed.py first).

## Spike results 2026-11-14 (backfilled)

- **CLAP GGUF**: `models/larger_clap_music_and_speech-q8_0.gguf` (208 MB) via
  `huggingface_hub.hf_hub_download` (the hf_cli module path does not exist in hub 0.27).
  `pip install clap-cpp` works; `clap_cpp.CLAP(path)` + `encode_audio(pcm, sample_rate=48000)`
  delivers 512-d, L2-normalized. Smoke: self-cos = 1.0, 440 vs 220 Hz = 0.938.
  → **mode: pip binding**, the subprocess fallback stays in the code.
- **ollama 0.40.16 + lfm3-omni:2b**: `ollama pull lfm3-omni:2b` ok (2.4 GB).
  `/api/chat` accepts the **`audio` field** (base64 WAV, 48 kHz and 16 kHz tested) →
  HTTP 200 with a JSON answer. → **default mode: audio**; the spectrogram PNG fallback on 4xx
  stays for other servers/versions. Live smoke judge(440 Hz vs 233 Hz+1200 Hz) →
  `mode=audio, score=85`, German summary + differences.
- **Recording data**: of the 4 .npy pairs only `check_20261108_152813` is usable
  (Iridium env 4.6e-2); the 3 `ab_A043_*` Iridium takes are ~1e-5 = silent
  (cf. sim_log "silent recording"). Fresh live pair added 2026-11-14
  (`ab_A043_20261114_153000`, A043 vs PC114 @ C5): Phase A 93.08 / embed 56.61 / llm 85
  ("rough, grainy") — see `docs/PHASEB-EVAL-2026-11-14.md`.
- **saina-helm-3-0.8b (decision model) not usable** via ollama 0.40.16: chat/generate →
  400; `/v1/systemone` → llama-server "wrong number of tensors; expected 326, got 320".
  The LLM verdict stays lfm3-omni:2b (chat + audio). `/v1/systemone` + spectrogram PNGs noted
  as an option for future compatible decision models.
