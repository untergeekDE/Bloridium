# Converter rebuild + Poly-AT + clarification plan (2026-11-18)

> Status: converter rebuild IMPLEMENTED inline 2026-11-18 (user directive: AT->Poly AT first,
> then clarifications, then fix converter; A001-A100 export/conversion only AFTER this).
> Tests: `python3 -m pytest tests/ -q` -> 323 passed, 1 skipped.

**Goal:** Blofeld->Iridium converter reflects the live-verified Iridium behavior (Poly AT,
v14 enums from the 4096-pid device-side sweep), remaining unknowns are clarified by automated
tools, and afterwards the batch run A001-A100 (dump -> convert -> remote apply -> A/B sweep
-> sim_log.jsonl -> `bloridium prognose train` RF) can start from a clean baseline.

**Architecture:** conversion stays qpat-based (SNDD -> overrides in `bloridium/qpat_map.py`
-> v14 .qpat via `workflow.convert_parsed`). Device-side truth comes from the private device-side layer
(sister repo `an external private repository`: pid sweep, `device_tweak`/`device_apply_qpat`/`device_ab_sweep`);
this repo keeps only results (no sysex artifacts here).

**Tech Stack:** Python 3.10, numpy, mido; pytest; private device-side tools in `an external private repository/tools/`.

**Spec/references:** `docs/research/ANALYSIS-2026-11-15-conversion-fixes.md` (P0/P1/P2),
`docs/refs/qpat_enum_scan.md` (enum histograms per qpat version, 1813 files, from
`scripts/extract_qpat_enums.py`), `docs/MAPPING-MASTER.md`, skill `the private Iridium-control skill`,
`an external private repository/HANDOFF-2026-11-17.md` + `TODO_FIX.md`.

---

## Done 2026-11-18 (converter, offline, tested)

- [x] **Poly AT** (user, live): `AfterTouchDoPoly=1.0 'Poly AT'` (`qpat_map.py`); matrix src
      "After Touch" stays **16.0 in the v14 FILE enum** (runtime 17 — loader translates,
      live-verified 2026-11-18 via param-info 2478 + load-patch/get-param; see
      `docs/refs/runtime_enums_2026-11-18.md`). Tests assert 16.0/1.0.
- [x] New v14 MATRIX_DST from enum scan: AmpEnv Attack=109, LFO1/2/3 Speed=145/146/147, DF Level=99.
- [x] P1-1 sync: `Osc 2 Sync to O3` -> `Osc2WaveformSync=1.0` (A071/A008).
- [x] P1-2 serial F2 mods -> DF Amount (95) / DF Color (96); parallel keeps 104/105.
- [x] P1-3 FX: mix key by mapped TYPE (Chorus/Flanger/Phaser/Delay/Drive DryWet) + per-type
      params per Blofeld SysEx spec 5.2-5.9; Clk.Delay -> DelaySync=1 + Sync indices from Length.
- [x] Detune centered: `fine_pitch_norm = 0.5+(raw-64)/254` (was norm(), A008 126 -> 0.992).
- [x] Amp Mod Source/Amount -> matrix slot -> Volume; Osc Pitch Source/Amount -> slot -> Pitch.
- [x] New tool `scripts/extract_qpat_enums.py` -> `docs/refs/qpat_enum_scan.{json,md}`.
- [x] Tests updated/added in `tests/test_qpat_map.py`; MAPPING-MASTER.md updated.

## Clarifications — status 2026-11-18 (live, device via private device-side tooling on Launchpad-DIN, dev 0x00)

1. [x] **Enum truth from the device**: `param-info 2478/2480/2876/2754/2756/2098/2090/2116/0/19/
   2121/26/2120/2117/2106/3691/2726` captured -> `docs/refs/runtime_enums_2026-11-18.md`.
   Controlled load test (own v14 file -> load-patch -> get-param): **file enum == runtime enum
   (identity)** on OS 4.1.0b2; old export-001 displays are stale. => converter now uses RUNTIME
   values everywhere (AT src=17, Velocity=33, DF Amount=104, Volume=152, FX Chorus=3 ...), incl.
   full wavetable bridge (68/68 Blofeld shapes) and new mod dsts (FE/AE Release, F1/F2 Pan,
   E3/E4 envs). 352 tests green.
2. [x] **qpat version on device**: export-patches preserves each patch's version (v11/v13/v14/v15
   mixed observed); our v14 files load fine -> `PRESET_VERSION=14` stays.
3. [ ] **MatrixAmount scale** (P2-1): sweep one slot amount via `device_tweak.py --pid <MatrixAmountN>`
   (0 / 0.5 / 0.75 / 1.0) + record note 72 (`sim_live.py`), measure effect (cutoff opening /
   pitch swing in Hz/cent via FFT) -> fit divisor for `amt_bipolar` (currently 254).
4. **FinePitch cent scale**: sweep `Osc1FinePitch` 0..1, measure pitch offset per step (FFT) ->
   cent per norm -> adjust `fine_pitch_norm` divisor.
5. **LFO free speed Hz**: sweep `Lfo1Speed` with Sync off, measure tremolo rate from envelope ->
   Hz-per-norm anchor like the glide/cutoff anchors.
6. **WT bridge by ear/CLAP** (P2-4): for Blofeld WTs without a table entry, set top-N Iridium
   tables via set-pid + `device_ab_sweep`-style embed_score vs the Blofeld original -> best table.
7. **Readback verification per sound**: after remote apply, `device_apply_qpat.py --check <slot>`
   (3-way diff dump <-> qpat <-> live get-param); enum-display mismatches expected until (1).
8. Optional: MIDI-CI live retest over MIDI-2.0 UMP with "CI Support" on (`device_mci.py`,
   subID2 0x70/0x34 fixed) for ProgramList slot<->name.

Standing rules (unchanged): U-poll >= 0.1 s, drain ring before first command, W-interval >= 0.25-0.5 s
for set-pid bulk + resend mismatches, `ps aux | grep device_` before sessions, never red commands,
Part 1 = ch6 only, CC123=0 + CC7=127 before each measurement, note 72 reference, Scarlett In3/4 vs In5/6.

## Then: batch run A001-A100 (user runs export/conversion after this is done)

1. `bloridium bank read A --only A001..A100` -> `dumps/banks/A/*.bin`
2. `bloridium convert <loc> --dump ... --out transfer/a100` per sound (or loop)
3. qpats auf SD (`2:`), remote persist: `load-patch 2:<file>.qpat` + `save-patch <slot 200+>`
   (`an external private repository/tools/device_shell.py run --allow-write ...`)
4. Sweep config (slots <-> LOCs) -> `device_ab_sweep.py --config ... --notes 72,60 --embed --llm
   --norm-pegel --allow-write` -> `recordings/sim_log.jsonl` (+ phaseb ratings)
5. `bloridium prognose train --log recordings/sim_log.jsonl --dumps dumps/ --target combined`
   -> RF feature importances = critical Blofeld parameters for conversion quality.

## Review focus

- v14-vs-v15 enum shifts (scan shows both; device decides via param-info/export) — wrong enum =
  silently wrong destination (the P0-1 class of bug).
- Slot numbering gaps: unmapped mod slots still consume a slot number (pre-existing); neutralized
  via MatrixDst=0/MatrixOnOff=0 in `apply_to_template`.
- Serial vs parallel F2 remap must not fire when F2 is Bypass (f2_bypass) — tested (A001 vs A010).
- FX: when both slots map to the same Iridium type, slot 2 wins on shared keys (tested, A008).
