# sim-specpng (side-by-side spectrogram PNG per A/B pair) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every A/B measurement can produce an optical spectrogram comparison PNG (A | B | ΔdB) that is linked in the JSONL log – centrally in `sim_embed.score_pair_embed` via `spec_png_dir`, wired into `sim_checkpoint.py` (default ON: `recordings/spec/`) and `sim_compare.py` (opt-in).

**Architecture:** `render_spec_pair_png` in `bloridium/sim_embed.py` (numpy+PIL, basis `sim.features`), shared lo/hi for A/B, diverging Δ scale ±20 dB; `score_pair_embed` renders on the level-normalized signals and sets `result["spec_png"]`; the degrade rule is like the other backends.

**Tech Stack:** Python 3.10; numpy + PIL (already a soft dep via `render_spec_png`); pytest>=8.

**Spec:** `docs/research/superpowers/specs/2026-11-18-sim-specpng-design.md`

## Global Constraints

- numpy + PIL only in the production path (no matplotlib); no new dependencies.
- Tests offline, synthetic signals, no MIDI/model.
- The existing log schema stays: only the additional field `spec_png` in the result (null when off).
- Degrade: render error → `spec_png=None` + `backend_error` extended by `spec_png: …`; `strict=True` → BackendError. Score/log unchanged.
- German docs/commits. Tests: `python3 -m pytest tests/ -q`.

## Review Focus

1. **The Δ panel must not show a level comparison** → render on `xe_blo`/`xe_irr` (normalized), not the raw signal. (Task 1, test: norm_pegel=True, different gains → Δ ≈ 0)
2. **Different lengths** → pad to max n_frames. (Task 1, test with 1.0 s vs 1.3 s)
3. **Shared lo/hi for A/B** → otherwise the grayscale normalization deceives. (Task 1, test: A quieter than B, same shape → the A panel darker than the B panel)
4. **A render error must not kill the measurement** → score ok, spec_png None, backend_error set. (Task 1)
5. **File name collision-free** with the same meta in the same run. (Task 1, test: same meta twice → 2 files)

---

### Task 1: `render_spec_pair_png` + `score_pair_embed(spec_png_dir=…)` (TDD)

**Files:**
- Modify: `bloridium/sim_embed.py`
- Modify: `tests/test_sim_embed.py`

**Interfaces:**
- Produces: `render_spec_pair_png(x_a, x_b, sr, path, db_span=20.0) -> Path`; `score_pair_embed(..., spec_png_dir=None)` sets `result["spec_png"]: str | None` (also in the `_fehler_result` path as None – there without rendering).

- [ ] **Step 1:** write the tests in `tests/test_sim_embed.py`:
  - `test_render_spec_pair_png_shape`: 1 s sine 220 vs 221 Hz @48 kHz, tmp path → open the PNG via PIL; width == 3·n_frames + 2·2 (separator 2 px), height == n_bands (48); mode RGB.
  - `test_render_spec_pair_png_delta_varies_and_common_scale`: 220 Hz (0.3) vs 221 Hz (0.15) → the delta panel (right third of the columns) not constant; the A panel brighter than the B panel (shared lo/hi, A louder). The same signal twice → the delta panel constant (all pixels = the 0-mapping color).
  - `test_render_spec_pair_png_pads_lengths`: 1.0 s vs 1.3 s → no error, width to max frames.
  - `test_score_pair_embed_spec_png_writes_and_logs`: two 1 s sines, `spec_png_dir=tmp`, `norm_pegel=False` → `result["spec_png"]` set, the file exists, the JSONL line contains `spec_png`; without `spec_png_dir` → `result["spec_png"] is None`, no file.
  - `test_score_pair_embed_spec_png_uses_normed_signals`: A = 0.3·sin, B = 0.03·sin (10× quieter, same shape), `norm_pegel=True`, spec_png_dir=tmp → the delta panel nearly constant (after norm ≈ equal); raw (norm_pegel=False) → the delta strongly colored. (Review focus 1)
  - `test_score_pair_embed_spec_png_degrade`: signal < 0.2 s → the features ValueError is caught by score_pair_embed anyway (error result); instead: spec_png_dir set + a normal signal, but monkeypatch `render_spec_pair_png` to raise → `result["score"]` ok, `spec_png is None`, `backend_error` contains "spec_png".
  - `test_spec_png_name_collision`: the same meta twice with the same spec_png_dir → two different files (`spec_pair.png`, `spec_pair_2.png` or similar).
- [ ] **Step 2:** `python3 -m pytest tests/test_sim_embed.py -q` → FAIL.
- [ ] **Step 3:** implement in `bloridium/sim_embed.py`:
  - `render_spec_pair_png(x_a, x_b, sr, path, db_span=20.0) -> Path` (like the spec: shared lo/hi, pad, LUT, separator, `Image.fromarray(...transpose(1,0,2))`).
  - `_spec_png_name(meta, spec_png_dir) -> Path` (sanitize, collision suffix).
  - `score_pair_embed(..., spec_png_dir=None)`: after the Phase-A part (also on the error result: include `spec_png=None` in the `_fehler_result` or result.setdefault), with try/except around `render_spec_pair_png(xe_blo, xe_irr, sr, path)`; success → `result["spec_png"]=str(path)`, error → `result["spec_png"]=None` + `errors.append(f"spec_png: {e}")` (strict → BackendError). Render on `xe_*`.
  - `print_result`: `if r.get("spec_png"): print(f"  spec_png: {r['spec_png']}")`.
- [ ] **Step 4:** `python3 -m pytest tests/test_sim_embed.py -q` → PASS.
- [ ] **Step 5:** Commit: `git add bloridium/sim_embed.py tests/test_sim_embed.py && git commit -m "feat(sim_embed): render_spec_pair_png (A|B|ΔdB) + score_pair_embed(spec_png_dir) – optical spectrogram comparison (TDD)"`.

### Task 2: CLI wiring (TDD)

**Files:**
- Modify: `scripts/sim_checkpoint.py`, `scripts/sim_compare.py`
- Modify: `tests/test_sim_checkpoint.py`, `tests/test_sim_compare_embed.py`

- [ ] **Step 1:** tests: `test_sim_checkpoint.py::test_checkpoint_spec_png_dir` – run `--only A001 --no-embed --no-llm --no-wait --spec-png-dir tmp/spec` → rc 0, 12 PNGs in tmp/spec with names `spec_A001_n*_w*.png`, every log line has `result.spec_png` set. `test_sim_compare_embed.py`: sim_compare.main(["--npy", a, b, "--no-embed"... with --spec-png-dir]) → the PNG exists + the log contains spec_png; without the flag → spec_png None. (Adjust paths/flags to the existing tests.)
- [ ] **Step 2:** pytest → FAIL.
- [ ] **Step 3:** implement: extend `sim_checkpoint.py` with `--spec-png-dir` (default `str(REPO/"recordings"/"spec")`) + `--no-spec-png`, pass through to `score_pair_embed(..., spec_png_dir=None if args.no_spec_png else args.spec_png_dir)`; extend `sim_compare.py` with `--spec-png-dir` (default None) and pass through in `_score_pair` (`spec_png_dir=getattr(args, "spec_png_dir", None)`).
- [ ] **Step 4:** both test files → PASS.
- [ ] **Step 5:** Commit: `git commit -am "feat: --spec-png-dir in sim_checkpoint (default recordings/spec/) and sim_compare (opt-in)"`.

### Task 3: Suite + docs

- [ ] **Step 1:** `python3 -m pytest tests/ -q` → all PASS.
- [ ] **Step 2:** extend `docs/research/STATUS.md` (sim_checkpoint: spec PNGs in `recordings/spec/`, linked in the log; sim_compare: `--spec-png-dir`).
- [ ] **Step 3:** Commit: `git add docs/research/STATUS.md docs/research/superpowers/specs/2026-11-18-sim-specpng-design.md docs/research/superpowers/plans/2026-11-18-sim-specpng.md && git commit -m "docs: spec+plan sim-specpng + STATUS entry"`.
