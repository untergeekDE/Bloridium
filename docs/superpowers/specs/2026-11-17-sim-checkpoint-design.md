# Design: sim_checkpoint.py – checkpoint measurement round (9 presets × 4 notes × wheel 0/50/100 %)

Date: 2026-11-17 · Status: approved by the user 2026-11-17 (notes 36/48/60/72 confirmed, path A chosen)

## Intent & Why

The next checkpoint should no longer measure only note 72 at wheel 0, but systematically cover
the octave and mod behavior: **4 notes over 4 octaves
(default 36, 48, 60, 72 = C2-C5, one per octave) × wheel 0/50/100 %** for all 9
converted presets. Known findings that motivate this: low notes show
especially the env_dtw deviation (skill rule), A008 has an octave suspicion (d1 octave_lower
only p=0.50), the wheel divergence localizes mod deficits (A010 embed 75.7→37.9 at 100 %).
Iridium PC switching is broken (HANDOVER-2026-11-14) → manual-panel mode: the
human turns to Set 6 PC per `DEFAULT_MAP` on the Iridium per preset, the script only
plays notes and sets the wheel.

## Goals / Non-goals / Anti-goals

- Goals:
  - New `scripts/sim_checkpoint.py`: one run = all 9 presets from
    `DEFAULT_MAP` (sim_sweep_pcs), per preset 4 notes × 3 wheel levels = 12 measurements
    (108 total), defaults `--notes 36,48,60,72 --wheel 0,50,100 --dur 2.0`.
  - Per combination: one JSONL entry in `recordings/sim_log.jsonl` with
    `meta = {"mode": "checkpoint", "blofeld": loc, "blofeld_pc", "irr_pc", "bank": 6,
    "note": note, "wheel_pct": pct}` + the result of `sim_embed.score_pair_embed`
    (Phase A + embed + combined; llm/profile only on the reference combination, see below).
  - WAVs level-aligned (peak 0.5) like in `sim_manual_compare.py`:
    `recordings/ab_<LOC>_<ts>_n<note>_w<pct>_{blo,irr}.wav`.
  - CLAP embed on **all** 108 combinations; llm + d1 profile only at
    wheel 0 + note 72 (reference octave; 72 if in --notes, else the last note),
    `--full-all` switches llm/profile to all combinations.
  - Per preset a panel prompt (`input(...)`): "please set Set 6 PC<irr_pc>";
    `--no-wait` skips the prompt (tests/non-interactive).
  - Wheel order outer→inner (only 3 CC1 changes per preset), reset CC1=0
    after **each** preset on both synths.
  - Summary at the end: pivot per preset — `A001 n36: w0=<combined> w50=… w100=…`.
  - Exit 0 if all measurements are ok; a silent recording (score None) is logged + warned +
    continue, exit 1 at the end.
- Non-goals:
  - No Iridium PC sending (broken, workaround panel).
  - No new multi-dimension fields (sim_dims from
    `docs/RESEARCH-2026-11-17-sim-multidim.md` is its own next step) — the
    checkpoint stays comparable with earlier runs (Phase A + embed + combined).
  - No change to `sim_manual_compare.py`/`sim_sweep_pcs.py` (they are only imported).
- Anti-goals:
  - No duplicate of `measure()`/`set_wheel()` — import from `sim_manual_compare`.
  - The checkpoint must not abort because of a single silent measurement.

## Constraints

- Python 3.10, macOS; numpy-only core; no new dependencies.
- Tests offline: MIDI/audio/backends/input via monkeypatch (pattern
  `test_sim_manual_compare_wheel_sweep` in `tests/test_scripts.py`), no live MIDI,
  no model downloads. Patch `time.sleep` to a no-op in the test.
- The degrade rule of `score_pair_embed` applies unchanged (backend missing → fields
  `null` + `backend_error`, no crash).
- Standing rules (skill): only trigger Part 1 (Iridium ch6), monophonic; CC123=0 on all
  16 channels + CC7=127 only on the Blofeld before each measurement (taken over from
  `measure()`); the Iridium USB stays unplugged.
- Docs/commit messages in German; tests: `python3 -m pytest tests/ -q`.

## Approaches

- **A (chosen):** own `scripts/sim_checkpoint.py` that imports `measure`/`set_wheel`
  from `sim_manual_compare.py` and `DEFAULT_MAP` from `sim_sweep_pcs.py` and encapsulates
  the preset loop + panel prompt + summary. Trade-off: one more script — justified because
  the manual panel change per preset happens manually anyway and one run wants consistent
  timestamps/meta/summary.
- **B (rejected):** only docs "call sim_manual_compare.py per preset" — 9 manual
  calls with the panel turn as an error source, no summary, inconsistent ts.

## Design

- `scripts/sim_checkpoint.py`, `main(argv=None) -> int` (like the other scripts).
- Flow: build the backends once (`sim_embed.build_backends`, `build_profile_backend`);
  `midi.connect` both synths; per preset: Blofeld Bank A (CC0=0, CC32=0) + PC
  `int(loc[1:])-1`, prompt `input()` (except `--no-wait`), then
  `for pct in wheel_pcts: set_wheel(blo, irr, pct); for note in notes: measure(...)`.
  `full = args.full_all or (pct == wheel_pcts[0] and note == ref_note)`;
  `ref_note = 72 if 72 in notes else notes[-1]`.
- Measurement/WAV/log identical to `sim_manual_compare.main` (same WAV names, same
  `norm_pegel` behavior, `sim_embed.print_result` per combination).
- After each preset: `set_wheel(blo, irr, 0.0)`.
- Summary: `summary[(loc, note)][pct] = (score, embed_score, combined)`; at the end:
  one line per preset and note: `A001 n36: w0=84.2 w50=82.4 w100=61.0`.
- Exit: 1 if at least one result has `score is None` (verdict "error"), else 0.
- Tests: new `tests/test_sim_checkpoint.py` (FakeSynth/FakeRecord pattern from
  `test_scripts.py`): (1) `--only A001` default notes/wheel → 12 log lines, meta key set
  exactly, CC1 ch4/ch5 == [0,64,127,0], 24 WAVs with the name pattern, rc 0, summary contains
  "A001"/"n36"; (2) all 9 presets → 108 lines, `input` called 9×, faked
  `score_pair_embed` records `use_llm` — only wheel 0 + note 72 True (9×); (3) a silent
  measurement (score None) → line logged, rc 1, the run continues; (4) `--no-wait` does not
  call `input`; `--notes 60,72 --wheel 0` → 2 lines/preset.

## What the builder still has to clarify

- Nothing open — all calls approved by the user (notes 36/48/60/72, path A,
  dur 2.0, embed everywhere, llm/profile only on the reference combination).
