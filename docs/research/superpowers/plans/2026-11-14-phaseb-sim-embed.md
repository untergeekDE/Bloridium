# Phase B sim-embed (CLAP GGUF + ollama verdict) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase B of the sound comparison: numeric CLAP embedding score + optional ollama LLM verdict next to Phase A, on all entrypoints (`sim compare`, `ab`, scripts), logged in `sim_log.jsonl`/`report_json`, offline evaluable on the 4 existing .npy pairs.

**Architecture:** models run externally (clap.cpp GGUF via pip binding/subprocess; ollama via HTTP) — `bloridium/sim_embed.py` encapsulates both backends behind narrow classes; `score_pair_embed` combines `sim.features`/`sim.compare` (Phase A, without double logging) with embedding (+LLM) into one result dict. No MLX (ROCm portability), no DB schema change (report_json is a JSON blob).

**Tech Stack:** Python 3.10.13, macOS; numpy-only in the core; stdlib `wave` (no soundfile); PIL 10.2 (spectrogram PNG); requests/httpx for the ollama API; pytest>=8; models: `gorse-io/larger_clap_music_and_speech-GGUF` Q8_0 (Apache-2.0) in `models/`, ollama `lfm3-omni:2b`.

**Spec:** `docs/research/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md` (approved 2026-11-14; builder-check ses_e25f5d23… is incorporated)

## Global Constraints

- Python 3.10, macOS; the core stays numpy-only — no new heavy runtime dependencies (clap-cpp/ollama are external: subprocess/HTTP).
- Unit tests offline: no live MIDI, no model download, backends mocked (monkeypatch); the real GGUF only in a `slow`-marked integration test (skip if the model is missing).
- Degrade rule: backend missing → warning on stderr, Phase A runs, log fields `null` + `backend_error`, exit 0; `--strict` → exit 3. The existing exit behavior (1 on a Phase-A `error`) stays.
- CLAP input: the whole recording mono; resample to 48 kHz only if needed; padding is done by the backend.
- LLM: German `DEFAULT_JUDGE_PROMPT`, anchor 100 = indistinguishable; answer contract `{"score": 0-100, "summary": str, "differences": [str, ...]}`; `differences` = string array; prompt ID in the log.
- `combined = 0.5*score + 0.5*embed_score`; the LLM score is informative, not in `combined`.
- `models/` in `.gitignore`; no model files in the repo.
- Docs/prompts/commit messages in German, consistent with the repo. Tests run: `python3 -m pytest tests/ -q`.

## Review Focus

1. **Sweeps must never crash because of a missing backend** → degrade test: `score_pair_embed` with `clap=None` + `strict=False` delivers `embed_*: null` + `backend_error`, exit behavior 0; with `strict=True` raises/exit 3. (Task 5, Task 7)
2. **LLM answer parsing** must tolerate prose around the JSON → test with `"Here is the verdict: {...} Hope that helps."`. (Task 4)
3. **Pairs of different lengths comparable** → embedding test with 126 080 vs 133 969 samples and with sr≠48000 (resample path). (Task 3)
4. **Log schema stable for downstream training** → the JSONL entry always contains the backend keys (as `null`), never missing; one test pins the key set. (Task 5)
5. **`ab_runs.report_json` stays compatible without migration** → test: `db.log_ab_run` with an extended report dict (sim/embed/llm keys) roundtrip; old rows without the keys still readable. (Task 9)

---

### Task 1: Spike — verify runtime capabilities (before any code)

**Files:**
- Modify: `docs/research/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md` (append the section "Spike results 2026-11-14")
- Create: `models/` (gitignored, local)

- [ ] **Step 1:** download the CLAP GGUF: `python3 -m huggingface_hub.commands.hf_cli download gorse-io/larger_clap_music_and_speech-GGUF larger_clap_music_and_speech-q8_0.gguf --local-dir models/` (or `hf download …`); expected: ~208 MB file in `models/`.
- [ ] **Step 2:** test `pip install clap-cpp`; then smoke: a small WAV (sine 440 Hz, 1 s, 48 kHz) embedded → 512-d vector, norm ≈ 1. If the pip package doesn't work: build clap.cpp (cmake) and note the binary path as a fallback — decision anchored in the spec.
- [ ] **Step 3:** `ollama pull lfm3-omni:2b` (2 GB); make sure `ollama serve` runs; then an API test: `POST /api/chat` with `messages:[{role:user, content:"…", audio:[<base64 wav>]}]` against lfm3-omni:2b. Note the result: does 0.40.16 accept the `audio` field (200 + valid JSON verdict) or 4xx → then the fallback mode = spectrogram PNG via `images` to a vision model (e.g. the same lfm3-omni, which is vision-capable). Note the mode in the spec.
- [ ] **Step 4:** commit the spec section "Spike results" (docs only): GGUF path, clap-cpp access (pip vs binary), ollama mode (audio vs spec PNG), model versions.

### Task 2: `bloridium/sim_embed.py` — pure helpers (TDD)

**Files:**
- Create: `bloridium/sim_embed.py`
- Create: `tests/test_sim_embed.py`

**Interfaces (produced):**
- `write_wav(x: np.ndarray, sr: int, path: Path) -> None` — float32 → int16 PCM mono via stdlib `wave`
- `render_spec_png(x: np.ndarray, sr: int, path: Path) -> None` — log_spec from `sim.features` as a grayscale PNG via PIL (log dB mapped to 0-255)
- `embed_compare(ea: np.ndarray, eb: np.ndarray) -> dict` — `{"embed_cos": float, "embed_score": float}`; score = `100*clip(cos, 0, 1)`

- [ ] **Step 1:** write the tests: `test_write_wav_roundtrip` (the wave module reads it back, length/level ok), `test_render_spec_png_valid` (PIL opens, mode L, size>0), `test_embed_compare_edges` (cos=1→100, cos=0→0, cos<0→0, dict keys exactly `embed_cos`/`embed_score`).
- [ ] **Step 2:** `python3 -m pytest tests/test_sim_embed.py -q` → FAIL (module missing).
- [ ] **Step 3:** implement in `bloridium/sim_embed.py` (only these three functions; import `REPO`/`DEFAULT_LOG` analogously to `sim.py`).
- [ ] **Step 4:** pytest → PASS. Commit: `feat(sim_embed): write_wav/render_spec_png/embed_compare + tests`.

### Task 3: `ClapBackend` (TDD, mocked)

**Files:**
- Modify: `bloridium/sim_embed.py`
- Modify: `tests/test_sim_embed.py`

**Interfaces:**
- `class ClapBackend:` `__init__(self, model_path: str | Path)`; `embed(self, x: np.ndarray, sr: int) -> np.ndarray` — mono-average, sr≠48000 → linear resample (numpy), WAV via `write_wav` in tmp, then: first the `clap_cpp` binding, fallback subprocess `clap embedding --model M --audio WAV` → parse the stdout JSON array → float32 vector (512,), L2-normalized; error → `RuntimeError` with the backend message.

- [ ] **Step 1:** tests with monkeypatch: `test_embed_uses_binding_when_available` (inject a fake `clap_cpp` module), `test_embed_subprocess_fallback_parses_json` (fake subprocess.run → stdout `[0.1, …]`), `test_embed_resamples_non_48k` (sr=44100 → the WAV header carries 48000), `test_embed_different_lengths_ok` (126 080 vs 133 969 samples → (512,) each), `test_embed_raises_on_backend_error`.
- [ ] **Step 2:** pytest → FAIL. **Step 3:** implement. **Step 4:** pytest → PASS. Commit.

### Task 4: `OllamaBackend` + `DEFAULT_JUDGE_PROMPT` (TDD, mocked)

**Files:**
- Modify: `bloridium/sim_embed.py`, `tests/test_sim_embed.py`

**Interfaces:**
- `DEFAULT_JUDGE_PROMPT: str` — German, two clips (A/B) + anchor 100 = indistinguishable, contract `{"score":0-100,"summary":"…","differences":["…"]}`.
- `class OllamaBackend:` `__init__(self, model="lfm3-omni:2b", host="http://localhost:11434")`; `available(self) -> bool` (GET `/api/tags`); `judge(self, x_a, x_b, sr, prompt=DEFAULT_JUDGE_PROMPT) -> dict` — build the request; try the spike mode `audio` (base64 WAV via the `audio` field), on 4xx fall back to `render_spec_png` of both clips + `images` field; extract the answer content → first `{...}`, validate (score int 0-100, differences list[str]); return: `{"score", "summary", "differences", "mode": "audio"|"spec", "model"}`.

- [ ] **Step 1:** tests (monkeypatch `requests.post`/`get`): `test_available_true_false`, `test_judge_audio_mode_ok`, `test_judge_falls_back_to_spec_on_400` (first post → 400, second with `images` → 200), `test_judge_parses_json_inside_prose` (content = `"Urteil: {\"score\": 87, ...} Ende."`), `test_judge_invalid_json_raises`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. Commit.

### Task 5: `score_pair_embed` — combination + log (TDD, real .npy, fake backends)

**Files:**
- Modify: `bloridium/sim_embed.py`, `tests/test_sim_embed.py`

**Interfaces:**
- `score_pair_embed(x_blo, x_irr, sr=48000, meta=None, log_path=DEFAULT_LOG | None, clap: ClapBackend | None = None, ollama: OllamaBackend | None = None, use_llm=False, strict=False) -> dict`
  - calls `sim.features` + `sim.compare` directly (no `sim.score_pair` → no double log), silence guard like Phase A (`verdict:"error"` → return, log).
  - result keys: the Phase-A keys (`score`, `spec_cos`, `env_dtw`, `band_delta_db`, `verdict`) + `embed_cos`, `embed_score`, `combined` + `llm` (dict|None) + `backend_error` (str|None). Backend missing & not strict → fields `null`, `backend_error` set, continue; strict → `RuntimeError`.
  - `log_path` set → exactly one JSONL entry via `sim.log_run` with meta incl. `backends: {clap: model|"none", ollama: model|"none", llm: bool, prompt_id}`; `log_path=None` → don't log (for `measure_ab`).

- [ ] **Step 1:** tests on the real pairs `recordings/ab_A043_20261108_142609_{blofeld,iridium}.npy` with a fake Clap (returns a unit vector) + tmp log: `test_score_pair_embed_full_schema` (key set pinned exactly, incl. `null` fields on a missing backend), `test_combined_is_50_50`, `test_no_backend_degrades_not_raises` (clap=None → embed null, backend_error set, score ok), `test_strict_raises`, `test_silence_verdict_error` (null signal → error, logged), `test_log_written_once` (the JSONL grows by exactly 1 line, `log_path=None` → no line).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. Commit.

### Task 6: `scripts/fetch_models.py` + `.gitignore` (TDD, mocked)

**Files:**
- Create: `scripts/fetch_models.py`
- Modify: `.gitignore` (line `models/`)
- Modify: `tests/test_scripts.py` (or a new `tests/test_fetch_models.py`)

**Interfaces:**
- `main(argv=None) -> int` — downloads the GGUF Q8_0 to `models/` (hf download, idempotent: present → skip), `ollama pull lfm3-omni:2b` (subprocess, idempotent), optional `--pip-clap-cpp` → `pip install clap-cpp`. Exit 0 on success, 1 on error with a clear message. Starts **no** ollama server.

- [ ] **Step 1:** tests with monkeypatched subprocess: `test_fetch_skips_existing_gguf`, `test_fetch_pulls_ollama_model`, `test_fetch_failure_exit_1`.
- [ ] **Step 2:** FAIL. **Step 3:** implement + `.gitignore`. **Step 4:** PASS. Commit.

### Task 7: extend `scripts/sim_compare.py` with `--embed`/`--llm`/`--strict` (TDD)

**Files:**
- Modify: `scripts/sim_compare.py`, `tests/test_scripts.py`

**Interfaces:** `sim_compare.main` gets `--embed`, `--llm`, `--strict`, `--models-dir` (default `models/`); builds the backends (ClapBackend(models_dir/GGUF if the file exists, else None + warning; OllamaBackend if `available()`), calls `sim_embed.score_pair_embed` instead of `sim.score_pair` (both paths `--npy` and `--live`). Exit: 1 on a Phase-A error, 3 on strict+backend error, else 0.

- [ ] **Step 1:** tests (monkeypatch midi/audio/sim_embed backends): `test_npy_embed_flag_adds_embed_score`, `test_embed_missing_model_degrades_exit_0`, `test_strict_missing_model_exit_3`, `test_live_path_uses_score_pair_embed`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS + `python3 -m pytest tests/ -q` fully green. Commit.

### Task 8: `scripts/sim_eval_offline.py` — offline eval on the 4 pairs (TDD)

**Files:**
- Create: `scripts/sim_eval_offline.py`, `tests/test_sim_embed.py` (or its own test file)

**Interfaces:**
- `main(argv=None) -> int` — finds pairs `recordings/ab_*_blofeld.npy` ↔ `ab_*_iridium.npy` (and `check_*`) via regex; per pair: Phase A + embed (ClapBackend from `models/`, degrade if missing) → line (pair, score, embed_score, combined); writes `recordings/phaseb_eval_<ts>.json` (list + meta: models, ts) and prints the table. `--ratings PATH` (JSON `{"<pair>": 0-100}`) → adds the Spearman rank correlation (own numpy implementation with tie averaging, no scipy) of score/embed_score/combined against the ratings in the JSON + table.
- `spearman(a: list[float], b: list[float]) -> float` in sim_embed or the script (numpy).

- [ ] **Step 1:** tests with a tmp recordings dir (2 synthesized pairs, fake Clap): `test_pairs_discovery` (blofeld/iridium matched), `test_eval_writes_json_and_table` (JSON structure pinned), `test_spearman_perfect_and_inverse` (1.0 / −1.0, ties ok), `test_ratings_optional`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. Commit.

### Task 9: CLI + `ab` integration (TDD, all mocked)

**Files:**
- Modify: `bloridium/cli.py`, `bloridium/workflow.py`, `tests/test_cli.py`, `tests/test_scripts.py` (possibly a new `tests/test_workflow.py`)

**Interfaces:**
- New subcommand `bloridium sim compare --npy A B [--embed] [--llm] [--strict] [--models-dir D] [--log P]` and `--live [--note N] [--dur S] [--blofeld L] [--iridium-slot S] …` — a thin wrapper around `sim_embed.score_pair_embed` (live: recording analogous to `sim_compare.run_live`, monophonic Part 1 ch6, CC123/CC7 rules as before).
- `workflow.measure_ab(..., embed=False, llm=False, backends=None) -> dict` — the report dict additionally gets the keys `"sim"` (Phase-A comparison), `"embed"`, `"llm"` (or `null` + `backend_error`); `log_path=None` (no sim_log.jsonl double log; report.json + the DB carry it). **No schema change**: `ab_runs.report_json` is a JSON blob.
- `cmd_ab` gets `--embed/--llm/--strict` and passes them to `measure_ab`.

- [ ] **Step 1:** tests: `test_sim_compare_npy_cli` (monkeypatch backends, tmp npy), `test_ab_report_has_sim_embed_keys` (measure_ab with mocked midi/audio + fake Clap → report["embed"]["embed_score"] set, report_json roundtrip via `db.log_ab_run` + `db.ab_runs`), `test_ab_legacy_report_without_keys_still_readable` (old DB row without sim/embed keys → `db` reads ok), `test_ab_embed_off_by_default` (without a flag no embed keys → backward compatibility).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `python3 -m pytest tests/ -q` fully green. Commit.

### Task 10: Run the eval + doc template (needs Tasks 1-5, real models)

**Files:**
- Create: `docs/research/PHASEB-EVAL-2026-11-14.md`
- Create: `recordings/phaseb_eval_<ts>.json` (output of the script)

- [ ] **Step 1:** `python3 scripts/fetch_models.py` (get the models), then `python3 scripts/sim_eval_offline.py` → table + JSON.
- [ ] **Step 2:** create `docs/research/PHASEB-EVAL-2026-11-14.md`: table (pair, Phase A, embed_score, combined), spike mode (audio/spec), models/paths, **empty rating table** (pair × 0-100 listening impression) for the user + post-hoc caveat + room for Spearman (`--ratings`).
- [ ] **Step 3:** commit (docs + eval JSON; no models).

---

## Self-Review (checklist against the spec)

1. **Spec coverage:** embedding score (T3/T5), LLM verdict (T4/T5), combined 50/50 (T5), JSONL log (T5), degrade/strict (T5/T7), whole-clip CLAP input (T3), PNG fallback (T4, mode from T1), fetch_models (T6), sim_compare flags (T7), offline eval + post-hoc ratings (T8/T10), CLI `sim compare --npy/--live` (T9), `ab`/`measure_ab` with report keys without a schema change (T9), `models/` gitignored (T6), no MLX, ROCm path via subprocess/HTTP (T1/T3/T4). ✅ all spec points have a task.
2. **Step scan:** every step has exactly one verifiable result (test name + assertions, pytest command, expected FAIL/PASS, commit). No "TBD".
3. **Type consistency:** `ClapBackend.embed(x, sr) -> np.ndarray`, `OllamaBackend.judge(x_a, x_b, sr, prompt) -> dict`, `score_pair_embed(...) -> dict` used identically in T3-T5 and T7-T9. `write_wav`/`render_spec_png` from T2 are consumed in T3/T4. ✅
4. **Review focus:** the 5 points above, each with a test anchored in Task 5/7/3/4/9. ✅
5. **Proportion:** the plan is about as long as the spec; code blocks only test assertions/sketches, no transcripts. ✅
