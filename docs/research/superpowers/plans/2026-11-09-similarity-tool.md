# Similarity tool Blofeld↔Iridium (Phase A) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A numpy-only tool that translates two synth recordings (Blofeld vs Iridium) into a similarity score 0-100 + interpretable band deltas and logs every run as JSONL (feedback for the human, metric for transfer tuning, data for the later mapping model).

**Architecture:** `bloridium/sim.py` (pure, numpy: `features()` → log-mel-like spectrogram + RMS envelope; `compare()` → score; `log_run()` → JSONL) + `scripts/sim_compare.py` (offline on .npy takes or live measurement) + `scripts/sim_live.py` (CC turn loop with CC/pid map). No new dependencies.

**Tech Stack:** Python 3.10, numpy, pytest; MIDI/audio only in the scripts (monkeypatched in tests); mido/rtmidi as existing.

**Spec:** `docs/superpowers/specs/2026-11-09-similarity-tool-design.md` (approved 2026-11-09)

## Global Constraints
- Phase A: **numpy only**, no ML models/new deps (embeddings are Phase B per the spec).
- Recording 48 kHz, Scarlett; Blofeld In 3/4 = ch (2,3), Iridium In 5/6 = ch (4,5) (`bloridium.audio.CHANNELS`).
- MIDI ports: DEFAULT_PORTS in `bloridium/midi.py` (Launchpad DIN; Iridium Parts = ch6-9, idx 5-8; Blofeld ch5, idx 4).
- Sustain window 0.5-1.2 s after note-on (attack distorted, HANDOVER); highpass 80 Hz before feature extraction (DC/hum).
- Log: `recordings/sim_log.jsonl` (one JSON line per run).
- Tests must not need hardware/MIDI/audio (monkeypatch).

## Review Focus
1. Empty/too short recording (ffmpeg delivers < window) → `features()` must not crash, but deliver a clear error/score None. → Task 1 test.
2. DC offset/mains hum in the low bands distorts the cosine → HP 80 Hz **before** features. → Task 1 test (DC-heavy signal).
3. Different lengths of the two recordings → cosine on the mean spec (length-independent), DTW on the envelopes. → Task 2 test.
4. JSONL log: disk full / broken entry must not kill the comparison → `log_run` catches OSError. → Task 3 test.
5. CC map without pid column (old CSV) → `ccmap` falls back to name-only, no crash. → Task 5 test.

---

### Task 1: `bloridium/sim.py` — `features()`

**Files:**
- Create: `bloridium/sim.py`
- Test: `tests/test_sim.py`

**Interfaces:**
- Produces: `features(x: np.ndarray, sr: int = 48000, n_bands: int = 48, f_lo: float = 40.0, f_hi: float = 12000.0, hop_s: float = 0.05, hp_hz: float = 80.0) -> dict` with keys `"log_spec"` (n_bands × n_frames, dB), `"env_rms"` (n_frames,), `"band_edges"` (n_bands+1,), `"sr"`, `"n_samples"`. Raises on `len(x) < int(0.2*sr)`: `ValueError("too short")`.

- [ ] **Step 1: Write the failing test** — `tests/test_sim.py::test_features_sine_peak_im_richtigen_band`: 1 s sine 440 Hz @ 48 kHz → `log_spec` argmax band ≈ band of 440 Hz (±1); `test_features_dc_wird_durch_hp_entfernt`: DC + small sine → lowest band not dominant; `test_features_zu_kurz_wirft`: 0.1 s → pytest.raises(ValueError).
- [ ] **Step 2: Run, expect FAIL** — `python3 -m pytest tests/test_sim.py -v`
- [ ] **Step 3: Implement `features()`** in `bloridium/sim.py`: FFT with Hann per frame (hop_s), power → dB; log-spaced bands via `band_edges = geomspace(f_lo, f_hi, n_bands+1)`; beforehand FFT highpass `hp_hz` (X[f<hp]=0) on the whole signal; `env_rms` = sqrt(mean(frame²)) per frame.
- [ ] **Step 4: Run, expect PASS**
- [ ] **Step 5: Commit** — `git add bloridium/sim.py tests/test_sim.py && git commit -m "feat: sim.features (log-spec + env)"`

### Task 2: `bloridium/sim.py` — `compare()`

**Files:**
- Modify: `bloridium/sim.py`
- Test: `tests/test_sim.py`

**Interfaces:**
- Consumes: `features()` from Task 1.
- Produces: `compare(fa: dict, fb: dict) -> dict` with keys `"score"` (0-100 float), `"spec_cos"` (0-1), `"env_dtw"` (normalized 0-1, 0 = identical), `"band_delta_db"` (list n_bands: fb − fa in dB, averaged over frames), `"verdict"` ("close" ≥ 85, "medium" ≥ 60, else "far").

- [ ] **Step 1: failing tests**: `test_compare_identisch_score_100`: same feature dict twice → score ≈ 100, verdict "close"; `test_compare_anderes_spektrum_score_sinkt`: fa = 440 Hz, fb = 2 kHz → spec_cos < 0.9, score < 100; `test_compare_unterschiedliche_laenge_ok`: fa 1.0 s, fb 0.7 s → no crash, finite score; `test_band_delta_vorzeichen`: fb brighter → band_delta_db in high bands > 0.
- [ ] **Step 2: Run, expect FAIL**
- [ ] **Step 3: Implement `compare()`**: spec_cos = cosine on the frame-averaged log_spec (flattened); env: own DTW DP (numpy) on env_rms, normalized by path length → env_dtw = dtw / (len_a+len_b); score = 100 * (0.7*spec_cos + 0.3*(1-env_dtw)), clamped 0-100; band_delta_db = mean(fb.log_spec, axis=1) − mean(fa.log_spec, axis=1).
- [ ] **Step 4: Run, expect PASS**
- [ ] **Step 5: Commit** — `git commit -m "feat: sim.compare (cosine + DTW + score)"`

### Task 3: `bloridium/sim.py` — `log_run()` + `score_pair()`

**Files:**
- Modify: `bloridium/sim.py`
- Test: `tests/test_sim.py`

**Interfaces:**
- Produces: `log_run(result: dict, meta: dict, path=REPO/"recordings/sim_log.jsonl") -> bool` (append JSON line `{"ts":..., "meta":..., "result":...}`, OSError → False, never raise); `score_pair(x_blo: np.ndarray, x_irr: np.ndarray, sr: int, meta: dict) -> dict` (features + compare + log_run, returns result; on ValueError from features → result with score None, verdict "error").

- [ ] **Step 1: failing tests**: `test_log_run_schreibt_jsonl` (tmp_path): one line, json.loads ok, keys ts/meta/result; `test_log_run_kaputter_pfad_gibt_false`: path in a non-existent, non-creatable dir (monkeypatch mkdir fail or read-only) → False, no raise; `test_score_pair_zu_kurz_gibt_fehler`: 0.05 s signals → verdict "error", score None.
- [ ] **Step 2/3/4: TDD as above**
- [ ] **Step 5: Commit** — `git commit -m "feat: sim.log_run + score_pair"`

### Task 4: `scripts/sim_compare.py`

**Files:**
- Create: `scripts/sim_compare.py`
- Test: `tests/test_scripts.py` (existing — adopt the pattern there)

**Interfaces:**
- Consumes: `bloridium.sim.score_pair`, `bloridium.audio`, `bloridium.midi`.
- CLI: `python3 scripts/sim_compare.py --npy A.npy B.npy [--meta k=v ...]` (offline: .npy with shape (2, N) or (N,), mono-averaged) OR `--live [--note 60] [--dur 1.6] [--blofeld A043] [--iridium-slot 207]`: All Notes Off + CC7=127 on all 16 ch, note-on Blofeld ch4 + Iridium ch5-8, record all 20 ch, slice CHANNELS, score_pair, print score + top-5 band deltas + verdict, log_run.

- [ ] **Step 1: failing test** in `tests/test_scripts.py`: `test_sim_compare_npy_offline`: two synthetic .npy (sine 440 vs 440 / vs 2000 Hz) in tmp_path → call sim_compare.main() with argv monkeypatched, exit 0, sim_log.jsonl (monkeypatch REPO log via env or tmp) contains an entry with score. (No MIDI/audio in the test: only the --npy path.)
- [ ] **Step 2/3/4: TDD** — live part only after the offline part is green, structure `midi.connect`/`audio.record` monkeypatchable (functions `run_live(note, dur)` individually testable with fakes).
- [ ] **Step 5: Commit** — `git commit -m "feat: scripts/sim_compare.py (npy + live)"`

### Task 5: CC/pid map + `scripts/sim_live.py`

**Files:**
- Modify: `bloridium/ccmap.py` (load the pid column from `docs/midi-maps/iridium_pid_map.csv`; fallback to name-only if the column is missing)
- Create: `scripts/sim_live.py`
- Test: `tests/test_cc.py` (existing) + `tests/test_scripts.py`

**Interfaces:**
- Produces: `ccmap.load_pid_map(path=REPO/"docs/midi-maps/iridium_pid_map.csv") -> dict` {name_lower: (cc, pid)}; `ccmap.cc_for(name) -> int | None`.
- `scripts/sim_live.py --param "Filter1 Cutoff" --value 90 [--ref REF.npy] [--note 60]`: send CC to the Iridium (ch5-8), play a note, record, score against the Blofeld reference (--ref .npy, else Blofeld plays live), print + log_run. Exit 0.

- [ ] **Step 1: failing tests**: `test_ccmap_pid_map_laden`: load the real CSV → "filter1 cutoff" → (0, 966); `test_ccmap_fallback_ohne_pid_spalte`: tmp CSV only cc,name → cc_for works, pid None; `test_sim_live_mit_fakes`: midi.connect/audio.record monkeypatched → main exit 0, log contains an entry.
- [ ] **Step 2/3/4: TDD**
- [ ] **Step 5: Commit** — `git commit -m "feat: ccmap pid map + scripts/sim_live.py"`

### Task 6: Docs & full suite

**Files:**
- Modify: `docs/CLI.md` (short section sim_compare/sim_live), `README.md` (1 paragraph)
- Test: `python3 -m pytest tests/ -q` full

- [ ] **Step 1: Write the doc sections** (call examples, log path, verdict thresholds).
- [ ] **Step 2:** `python3 -m pytest tests/ -q` → all green (currently 139 + new).
- [ ] **Step 3: Commit** — `git commit -m "docs: sim tool"`

---

## Self-Review (done inline while writing)
- Spec coverage: features/compare/log (Tasks 1-3), offline+live compare (Task 4), CC map + live loop (Task 5), docs (Task 6). Phase-B embeddings deliberately left out (spec: Phase B).
- Signatures consistent: `features`, `compare`, `log_run`, `score_pair`, `ccmap.load_pid_map/cc_for` — written identically in all tasks.
- Review-focus points 1-5 each have a test in Task 1/2/3/5.
- No new deps; HW only in scripts, tests monkeypatched.
