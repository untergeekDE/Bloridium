# sim_checkpoint.py (checkpoint: 9 presets × 4 notes × wheel 0/50/100 %) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** New `scripts/sim_checkpoint.py`: one run measures all 9 presets from `DEFAULT_MAP` in manual-panel mode, per preset 4 notes (default 36,48,60,72 = C2-C5) × wheel 0/50/100 % (12 measurements, 108 total), logs Phase A + CLAP embed (+ combined) per combination to `recordings/sim_log.jsonl`, level-aligned WAVs, llm/d1 profile only on the reference combination (wheel 0 + note 72), with a panel prompt per preset, wheel reset after each preset and a summary pivot at the end.

**Architecture:** Thin checkpoint runner that imports `measure()`/`set_wheel()` from `scripts/sim_manual_compare.py` and `DEFAULT_MAP` from `scripts/sim_sweep_pcs.py` (no duplicate); measurement/logging/WAV identical to `sim_manual_compare.main` via `sim_embed.score_pair_embed`. No changes to existing scripts.

**Tech Stack:** Python 3.10, macOS; numpy-only core; mido/python-rtmidi (existing); pytest>=8; tests offline via monkeypatch (no live MIDI, no models).

**Spec:** `docs/research/superpowers/specs/2026-11-17-sim-checkpoint-design.md` (approved 2026-11-17: notes 36/48/60/72, path A)

## Global Constraints

- Python 3.10, macOS; no new runtime dependencies; the core stays numpy-only.
- Tests offline: `midi.connect`, `audio.record`, `time.sleep`, `builtins.input` and the backends are mocked (monkeypatch) — pattern see `test_sim_manual_compare_wheel_sweep` in `tests/test_scripts.py`. No live MIDI, no model download.
- The degrade rule of `sim_embed.score_pair_embed` applies unchanged (backend missing → fields `null` + `backend_error`, no crash).
- Standing measurement rules (from `measure()`, only imported): only Iridium ch6 (Part 1) monophonic; before each measurement CC123=0 on all 16 channels of both synths, CC7=127 only on the Blofeld (on the Iridium CC7 = Filter1 Amount!).
- WAV names consistent with `sim_manual_compare.py`: `ab_<LOC>_<ts>_n<note>_w<pct:.0f>_{blo,irr}.wav` in `--wav-dir` (default `recordings/`), level-aligned to peak 0.5 if `norm_pegel` is active.
- Log: one JSONL entry per (preset, note, wheel) in `--log` (default `sim.DEFAULT_LOG`), `meta = {"mode": "checkpoint", "blofeld", "blofeld_pc", "irr_pc", "bank": 6, "note", "wheel_pct"}`.
- Docs/commit messages in German. Tests: `python3 -m pytest tests/ -q`.

## Review Focus

1. **A silent measurement must not abort the checkpoint** → score None is logged (verdict "error"), warning, continue; exit 1 only at the end. (Task 1, test c)
2. **Wheel reset after each preset** → CC1 on Blofeld ch4 AND Iridium ch5 ends each preset with 0: sequence [0, 64, 127, 0]. (Task 1, test a)
3. **llm/profile only on the reference combination** → `use_llm`/profile only when wheel_pct == first level AND note == ref_note (72 if in --notes, else the last note); for 9 presets exactly 9 full calls. (Task 1, test b)
4. **Log schema stable** → every line has exactly the meta keys {mode, blofeld, blofeld_pc, irr_pc, bank, note, wheel_pct}; 108 lines on a full run. (Task 1, test b)
5. **Panel prompt skippable in tests/non-interactive** → `input()` is called 9×, with `--no-wait` 0×. (Task 1, test d)

---

### Task 1: `scripts/sim_checkpoint.py` + tests (TDD)

**Files:**
- Create: `scripts/sim_checkpoint.py`
- Create: `tests/test_sim_checkpoint.py`

**Interfaces:**
- Consumes: `sim_manual_compare.measure(blo, irr, note, dur) -> (bx, ix)`, `sim_manual_compare.set_wheel(blo, irr, pct) -> int`, `sim_sweep_pcs.DEFAULT_MAP: dict[str, int]`, `sim_embed.build_backends(models_dir, want_embed, want_llm) -> (clap, ollama)`, `sim_embed.build_profile_backend(want, model)`, `sim_embed.score_pair_embed(bx, ix, sr, meta, log_path, clap, ollama, use_llm, norm_pegel, profile_backend) -> dict`, `sim_embed.peak_dbfs/write_wav/print_result`, `sim.DEFAULT_LOG`, `audio.SAMPLERATE/CHANNELS`, `midi.connect`.
- Produces: `main(argv=None) -> int` (0 = all measurements ok, 1 = at least one score None); CLI flags: `--only LOC`, `--irr-pc` (only with `--only`, default from `DEFAULT_MAP[loc]`), `--notes` (default `"36,48,60,72"`), `--wheel` (default `"0,50,100"`), `--dur` (default 2.0), `--log`, `--wav-dir`, `--no-embed`, `--no-llm`, `--no-norm-pegel`, `--profile`, `--d1-model`, `--models-dir`, `--full-all`, `--no-wait`.

- [ ] **Step 1: Write the tests** in `tests/test_sim_checkpoint.py` (FakeSynth/FakeRecord like in `test_scripts.py`, `monkeypatch.setattr(time, "sleep", lambda s: None)`, `monkeypatch.setattr("builtins.input", lambda *a: "")`, `monkeypatch.setattr(midi, "connect", ...)`, `monkeypatch.setattr(audio, "record", fake_record)`; `sys.path.insert(0, str(repo / "scripts"))`):
  - a) `test_checkpoint_only_a001_defaults`: `main(["--only", "A001", "--irr-pc", "108", "--no-embed", "--no-llm", "--log", str(log), "--wav-dir", str(tmp_path)])` → rc 0; 12 log lines; meta key set exactly `{"mode","blofeld","blofeld_pc","irr_pc","bank","note","wheel_pct"}` with `mode=="checkpoint"`, `note` in {36,48,60,72}, `wheel_pct` in {0.0,50.0,100.0}; CC1 values on ch4 and ch5 == `[0, 64, 127, 0]`; 24 WAVs in tmp_path with the pattern `ab_A001_*_n36_w0_blo.wav` … `n72_w100_irr.wav`; `capsys` contains `"A001"` and `"n36"` (summary).
  - b) `test_checkpoint_all_presets_llm_only_ref`: without `--only`, patch `sim_embed.build_backends` to `(None, None)`, patch `sim_embed.score_pair_embed` with a fake that collects `(meta, use_llm)` and returns `{"score": 90.0, "embed_score": 80.0, "combined": 85.0, "verdict": "close", "peak_dbfs": None}` → 108 log lines (9 presets × 12); `input` called 9×; `use_llm==True` exactly 9× and only when `wheel_pct==0.0 and note==72`; meta `blofeld` covers all 9 keys of `DEFAULT_MAP`.
  - c) `test_checkpoint_stumm_weiter_exit1`: fake `score_pair_embed` returns `{"score": None, "verdict": "error", ...}` for (A001, note 36, wheel 0), else score 90 → rc 1; the error line is in the log; the following combinations are still logged (lines > 1).
  - d) `test_checkpoint_no_wait_and_overrides`: `main(["--only", "A008", "--notes", "60,72", "--wheel", "0", "--no-wait", ...])` with input patched to a function that fires an assertion when called → rc 0; 2 log lines with notes {60, 72}, wheel_pct {0.0}.
- [ ] **Step 2:** `python3 -m pytest tests/test_sim_checkpoint.py -q` → FAIL (module `sim_checkpoint` missing).
- [ ] **Step 3:** implement `scripts/sim_checkpoint.py`: sys.path setup like the other scripts; imports (`from sim_manual_compare import measure, set_wheel`, `from sim_sweep_pcs import DEFAULT_MAP`, `from bloridium import audio, midi, sim, sim_embed`); `main(argv=None) -> int` with the argparse flags above; build the backends once before the loop; per preset: Blofeld CC0=0/CC32=0/PC=`int(loc[1:])-1`, `if not args.no_wait: input(f"== {loc}: please set Favorites Set 6 PC{irr_pc} on the Iridium, confirm with Enter ==")`, parse `wheel_pcts`/`notes`, `ref_note = 72 if 72 in notes else notes[-1]`; `for pct in wheel_pcts: set_wheel(blo, irr, pct); for note in notes:` measure → WAVs (norm_pegel like in sim_manual_compare, names `ab_{loc}_{ts}_n{note}_w{pct:.0f}_{blo,irr}.wav`) → `full = args.full_all or (pct == wheel_pcts[0] and note == ref_note)` → `score_pair_embed(..., meta={"mode":"checkpoint", ...}, use_llm=not args.no_llm and full, norm_pegel=not args.no_norm_pegel, profile_backend=d1 if full else None)` → `print_result` + peak line; `summary[(loc, note)][pct] = (score, embed_score, combined)`; count errors (`r["score"] is None`); after each preset `set_wheel(blo, irr, 0.0)`; at the end print the summary pivot (`f"{loc} n{note}: " + " ".join(f"w{int(p)}={c}" …)`); `finally: blo.close(); irr.close()`; return 1 if errors else 0. A single ts per run (`datetime.now()` at the start).
- [ ] **Step 4:** `python3 -m pytest tests/test_sim_checkpoint.py -q` → PASS.
- [ ] **Step 5:** Commit: `git add scripts/sim_checkpoint.py tests/test_sim_checkpoint.py && git commit -m "feat: sim_checkpoint.py – checkpoint 9 presets × 4 notes × wheel 0/50/100 (TDD)"`.

### Task 2: Full suite green

**Files:**
- Modify: none (verification only); possibly minimal fixes in `tests/test_sim_checkpoint.py`.

- [ ] **Step 1:** `python3 -m pytest tests/ -q` → all tests PASS (incl. the existing `test_sim_manual_compare_wheel_sweep` — must not break from the import).
- [ ] **Step 2:** If red: minimal fixes until the suite is green; no refactors.
- [ ] **Step 3:** Commit (only if changed): `git commit -am "test: sim_checkpoint – suite green"`.

### Task 3: Docs

**Files:**
- Modify: `docs/research/STATUS.md` (section 4 Scripts: entry for `sim_checkpoint.py` with a call example)

- [ ] **Step 1:** extend `docs/research/STATUS.md` with a bullet: `sim_checkpoint.py [--only A001] [--notes 36,48,60,72] [--wheel 0,50,100] [--dur 2.0] [--full-all] [--no-wait]` – checkpoint of all 9 presets in manual-panel mode (panel prompt per preset: Set 6 PC per DEFAULT_MAP), 12 measurements/preset, JSONL + WAVs like `sim_manual_compare.py`, summary pivot at the end.
- [ ] **Step 2:** `python3 -m pytest tests/ -q` stays green (docs only, quick re-insurance).
- [ ] **Step 3:** Commit: `git add docs/research/STATUS.md docs/research/superpowers/specs/2026-11-17-sim-checkpoint-design.md docs/research/superpowers/plans/2026-11-17-sim-checkpoint.md && git commit -m "docs: spec+plan sim_checkpoint + STATUS entry"`.
