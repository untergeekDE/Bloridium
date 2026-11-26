# Fixes History (review 2026-11-20)

Outcome of a code review of `64c73e3`. Fixes live on branch `fix/review-notes`.
Legend: ✅ done · 🟡 partly done · ⬜ open · 🖥 to do on the measurement machine (Mac + synths)

Test baseline on Linux without private data: 200 passed / 46 failed / 17 errors.
All remaining failures come from the missing `dumps/` and `recordings/` data. The full
suite is run on the measurement machine (item 11).

## Release 0.6.7 (2026-11-26)

- **Filter envelope amount reverted to `norm(raw)`** (undoes 0.6.5's
  `0.5 + 0.5*norm(raw)`). The A/B *score* preferred bipolar by +8.0, but by ear
  the filter envelope then opens far too much - the user judged the 0.6.4/0.6.5
  sound clearly better. The score rewards spectral brightness, not taste.
- **LFO decay fix stays** (0.6.6): live LFOs are an enrichment, even if the
  modulation is sometimes too strong (open point: LFO amount/speed scaling).
- Both packages re-converted: `transfer/don_solaris_v1` (E, 200-299) and
  `transfer/rf100_v6` (A, 300-399).

## Release 0.6.6 (2026-11-23)

- **All converted LFOs were silent:** the fade mapping wrote `LfoNAttack = 0`
  and `LfoNDecay = 0` for a neutral Blofeld LFO Fade. Measured on E090
  ("Soft Pulses", slot 289) with a clean `LFO2 -> Pitch` row at 1.81 Hz:
  `Lfo2Decay 0.0` -> flat pitch (spectral flux 0.37), `1.0` -> real vibrato
  (flux 1.01). Every factory/template qpat has `LfoNDecay = 1.0`.
  Fix: neutral/positive fade -> Decay 1.0 (no fade-out); a negative Blofeld
  fade (fade-out) is no longer modelled and is reported as unmapped instead of
  writing 0.0 (which silenced the LFO).
- `scripts/diag_lfo.py`: pitch-trajectory A/B for an LFO -> Pitch row.

## Release 0.6.5 (2026-11-22)

- **Filter envelope amount is bipolar:** `Filter1EnvAmount`/`Filter2EnvAmount`
  are mapped as `0.5 + 0.5*norm(raw)` instead of `norm(raw)`. The Iridium
  value 0.5 is neutral (factory qpats); the old mapping gave raw 86 only
  +0.18 of the range instead of +0.68, so the filter envelope barely moved
  (bank E outliers E072/E001/E015 too dark, E077/E078 too thin).
- **Validated by A/B (2026-11-23):** +8.0 mean over 5 sounds, all better
  (E015 +10.6, E089 +10.6, E072 +9.4, E077 +5.4, E001 +4.0).
- Still open (TODO_MEASURE): the same suspicion for `FilterNVeloAmount` /
  `AmpVeloAmount`.

## Release 0.6.4 (2026-11-22)

- **Poly/Mono allocation mapped:** Blofeld `Allocation/Unisono` bit 0 (1 = Mono)
  -> Iridium `PolyMonoMode` (0 Poly / 1 Mono, verified live via param-info 2870).
  The older note that the Iridium has no mono mode is wrong. 40 of the first
  100 AnalogVoltage sounds are mono; 14 of bank A.

## Release 0.6.3 (2026-11-22)

- **Envelope curves: Attack = RC, Decay/Release = Exp** (was all Lin). The Lin
  setting made releases audibly too long (Don Solaris user finding); it dated
  from before the time calibration.
- **Sync sounds:** a pitch modulation on a hard-synced oscillator now targets
  `WF2 Sync` instead of `Osc2 Pitch`. `Osc2WaveformSync` gets a moderate base
  amount `SYNC_AMOUNT = 0.25` (Iridium sync is continuous, 0..36 semitones),
  not 1.0. Ear-matched on Don Solaris E016 vs Iridium slot 215.
- **Filter drive:** a Blofeld `Filter 1 Drive > 0` on a 24 dB LP now selects
  `24dB sat. LP` instead of `24dB LP`; the separate FX1 Drive simulation is
  skipped for F1 (no double distortion). F2 drive still uses FX1 Drive.
- `MATRIX_DST` gains the runtime destinations `WF1/2/3 Sync` (19/50/81,
  verified with `param-info 2480`).

## Release 0.6.2 (2026-11-22)

- **Envelope attack/decay times calibrated:** `ENVELOPE_TIME_ANCHORS` +
  `envelope_time_norm()` in `qpat_map.py` replace the linear raw/127 mapping
  (attack was up to ~3x too slow). Applies to amp, filter and free envelopes.
- A/B on real sounds: A003 +4.7, A016 +4.7 (only attack/decay changed).
- Curves stay Lin (RC fits the shape better but the earlier user finding and
  the score A/B are not in its favour); release stays linear (not measured
  reliably).
- Re-converted to `transfer/rf100_v5` (SD `rf500`, slots 300-399).

## Release 0.6.1 (2026-11-22)

- **Fix:** the waveform template shipped `Osc2WaveformSemitone2 = 0` and
  `Osc3WaveformSemitone1 = 0` (= -12 semitones) and the converter never
  overrode them, so Osc 3 ran an octave low in every converted sound
  (CoarsePitch itself was correct). All four semitone slots of every
  oscillator are now neutral (12 = +0); test
  `test_waveform_semitone_slots_neutral`.
- **Measured effect** (only those slots changed): A020 30.3 -> 63.0,
  A023 40.2 -> 51.8, A024 38.2 -> 61.2.
- Re-converted to `transfer/rf100_v4` (slots 200-299).
  88/100 sounds have an audible Osc 3, so the v3 scores are too low for them.
- **Full v4 run:** 196/200 rows scored, mean **70.7** (v3 67.0, v2 51.1),
  +3.8 vs v3 with 53/98 better. Prognosis retrain on the v4 labels did not
  beat the mean (R² -0.234 / R²_cv 0.070) -> model stays v2.

## Release 0.6.0 (2026-11-22)

- **RF100 v3:** A001–A100 re-converted with the A1/A2/A3/A4/A7a and Glide fixes
  (`transfer/rf100_v3`, SD folder `rf300`, slots 200–299) and measured against
  the Blofeld from the stored slots: 200 rows, 197 scored, **mean 66.9**
  (v2: 51.1 on the same sounds), 73 of 99 sounds better.
- Version bump only — the converter output is unchanged since 0.5.3.
- **Prognosis model stays v2:** retrained on the v3 labels (n=99, MAE 9.32,
  R² −0.013 / R²_cv 0.075) it did not beat v2 (MAE 10.47, R² 0.064 / 0.132),
  so `models/prognose_rf.pkl` is unchanged.
- **Load trap found and fixed:** `load-patch 2:<dir>/<file>.qpat` is accepted
  but silently does nothing; only `load-patch <slot>` loads. The first v3 run
  was invalid and was discarded (`recordings/sim_log_v3_invalid_loadpath.jsonl`);
  the runner now verifies three edit-buffer parameters after every load.
- Open: A12 (`DigiFormerAmount`), weak cases A057/A020/A051, silent Blofeld
  channel on A050/A097.

## Scoring & prognosis

1. 🟡 **Similarity score saturated** (`bloridium/sim.py`). The v1 cosine on raw dB spectra
   rated saw vs. white noise at 99.3 and sine 220 Hz vs. 3000 Hz at 91.4, both "close".
   Details: `docs/FINDINGS.md` → "Similarity score saturation".
   - ✅ **Decision: the new formula replaces the old one** (`SCORE_VERSION = 2`):
     `score = 70 % · (1 − spec_mad_db/20 dB) + 30 % · (1 − env_dtw)`. With it, saw vs.
     noise scores 64 and the two sines score 30.
   - ✅ Every result carries `score_version: 2`. The v1 cosine is kept as the diagnostic
     `spec_cos`. Tests are in `tests/test_sim.py`, and the error schema in `sim_embed` is
     in sync.
   - ✅ `prognose train` skips log rows scored with v1 by default
     (`--min-score-version 2`, `0` = all). Old and new scores can no longer be mixed silently.
   - ✅ `docs/CLI.md` and `docs/FINDINGS.md` are updated.
   - ✅ `README.md` describes the v2 score.
   - 🖥 Re-score the existing recordings with v2. `sim compare --npy` works on the
     stored `.npy`/`.wav` pairs, so no re-recording should be needed.
   - 🖥 Calibrate the 20 dB scale (`_MAD_SCALE`) against user ratings, as was done for
     specdiff.
2. 🟡 **RF prognosis is not predictive.** R² is −0.19 on held-out data and −0.06 in CV.
   - ✅ `bloridium prognose train` warns on stderr when R² < 0.
   - ✅ The webapp score note and the module docstring state the caveat.
   - ✅ **Done 2026-11-20:** retrained on v2 (`--target score`, `recordings/sim_log_v2_rf.jsonl`):
     n=99, MAE 10.47, **R²=+0.064 holdout / R²_cv=+0.132 — positive** (v1 model: R²<0).
     Shipped `models/prognose_rf.pkl` is now v2-trained (old kept as `prognose_rf_v1.pkl`).
     `--target combined` stays noisy (R² −0.19 holdout) — ship `score`. Note MAE is larger
     in absolute terms only because v2 labels spread over 22–84 instead of saturated 87–98.
   - ✅ Entropy check before training (`bloridium prognose entropy`): H(y)=3.14 bits on
     n=99 v2 labels; embed_score adds partial IG 0.63 bits beyond spec_mad_db (d1 profile
     0.60 on n=23, llm constant → none). embed/d1 are only available AFTER measuring →
     leakage as RF input features; usable as label/diagnostic only (docs/FINDINGS.md).
3. ✅ **Own random forest instead of sklearn**, kept only because scipy was broken locally.
   Option: an optional `sklearn` extra with the numpy RF as fallback. Not changed,
   because the pickled model depends on `bloridium.prognose` classes.

## Webapp / container

4. ✅ **Cleanup race → HTTP 500.** `cleanup()` ran on every request in both gunicorn
   workers without a lock. It is now race-tolerant (`shutil.rmtree(ignore_errors=True)`)
   and runs at most every `CLEANUP_INTERVAL_S` (default 300 s) per worker. Tests:
   `test_cleanup_*`.
5. 🟡 **Containerfile out of date.**
   - ✅ The header comment is fixed.
   - ✅ `models/prognose_rf.pkl` and `bloridium/version.py` are baked in;
     `.containerignore` re-includes the model.
   - ✅ Comments in `compose.yaml` and the webapp README are adjusted.
   - 🖥 Verify with an actual `podman build`.
6. 🟡 **`convert.load_core()` builds a synthetic package** to avoid importing mido.
   - ✅ `bloridium/__init__.py` imports `audio`/`midi` lazily, so `import bloridium` no
     longer pulls in mido/rtmidi.


## Packaging, versions, license

7. ✅ **`requests` undeclared but required.** `cli.py` → `sim_embed` imports it at module
   level, so a fresh install crashed on start. It is now a core dependency and in
   `requirements.txt`.
8. ✅ **Test dependencies undeclared.** `dev` now includes `pillow` and `flask`.
   New extras: `embed` (pillow) and `web` (flask, gunicorn).
9. ✅ **Versions unified.** There is now one version, `__version__` in
   `bloridium/version.py`, set to **0.4.0** because the score formula changed. It is used
   by:
   - `pyproject.toml` (dynamic version)
   - `bloridium --version`
   - the webapp UI title, footer, `report.json` and `MANIFEST.md`
   - the matcher labels (`rf-prognose-v0.4.0`, `deterministic-placeholder-v0.4.0`).
   `matching.SIMILARITY_VERSION` and `PLACEHOLDER_VERSION` remain as aliases for the
   `report.json` field names. Test: `test_versions_are_unified`.
10. ✅ **License: GPL-3.0.** `LICENSE` contains the unmodified GPL-3.0 text from
    gnu.org, and `pyproject.toml` declares `GPL-3.0-only` plus the classifier.
    The webapp footer shows "GPL-3.0".
    - ✅ The README has a License section.

## Tests & CI

11. 🖥 **Run the full suite on the measurement machine.** About 60 tests read gitignored
    `dumps/…`, `dumps/export-001/` and `recordings/check_*.npy`.
    - ⬜ For CI: either commit a few small fixture dumps under `tests/fixtures/`, or mark
      these tests `needs_data` and skip them when the file is missing.
12. ⬜ **No CI and no lint/type config.** Add a GitHub Actions job (ubuntu, Python 3.12,
    `pip install -e .[dev]`, pytest) once item 11 makes the suite pass without private
    data. Add Ruff and, optionally, mypy.

## Portability & configuration

13. ✅ **Hard-coded path in `scripts/build_cp70_iridium.py`.** The sample pack is now taken
    from a CLI argument, then `$BLORIDIUM_CP70_ZIP`, then `./CP70-Exs24-v1.2.zip`.
14. ⬜ **`scripts/` ignore `bloridium.yaml`.** Wire them to `config.load_config()`, or
    retire the scripts the CLI covers.
15. ⬜ **macOS-only MIDI 2.0 path.** `tools/ump_send` is CoreMIDI Objective-C, and the
    compiled Mach-O binary is tracked. Build it in a setup step instead, and document
    Linux/Windows limitations.

## Docs & code hygiene

16. 🟡 **"English-only" not quite true.**
    - ✅ Translated the German docstrings, comments, CLI help and messages in `cli.py`,
      `prognose.py`, `specdiff.py`, `sim_embed.py` and `sim.py`, plus the `.gitignore`
      comments.

17. 🟡 **Stale docs.**
    - ✅ `docs/research/STATUS.md` has a "partly outdated" banner, and the absolute path is removed.
    - ⬜ Consolidate the HANDOVER files, STATUS, MAPPING and MAPPING-MASTER.
    - ⬜ Move the `scripts/spike_*` and `step2_probe_*` into `scripts/archive/`.
18. ⬜ **`cli.py` is 1,000+ lines.** Split it into `cli/` per command group.
19. 🟡 **Performance in `sim`.**
    - ✅ `features()` computes the band masks once, not per frame.
    - ⬜ `_dtw` is still a pure-Python double loop; vectorise it or use a banded DTW.

## Agent skill & private tooling

20. ✅ **Public agent skill for all MIDI-based functions.** Today the `bloridium` skill
    exists only outside the repo, so clones never get it, yet `CLAUDE.md` asks to keep it
    updated.
    - ✅ **Done 2026-11-21:** shipped in the repo as `skills/bloridium/SKILL.md`
      (+ `skills/README.md` with per-runtime install instructions; `README.md` already
      points to the `skills/` folder). Covers exactly the documented interfaces listed
      below and nothing else; guard: no private protocol, tool or command names in `skills/`.
    - **Goal:** ship a skill in the repo (`.claude/skills/bloridium/SKILL.md`, optionally
      mirrored for other agent runtimes) that exposes every function based on documented
      MIDI control.
    - **Blofeld (SysEx, official spec v1.04):**
      - device identity and status (`status`, `discover --probe`)
      - read sounds and banks (`bank read`, SNDR → SNDD) and import, list and show dumps
      - set single parameters (SNDP)
      - convert to `.qpat` (`convert`)
    - **Iridium (MIDI CC, plus note/PC):**
      - send CCs by name (`cc`, midi.guide CSV) and explore which CC drives which
        parameter (`explore`)
      - program change into the Favorites bank (CC0 + PC)
      - edit `.qpat` files (`edit`, `qpat info`)
      - safety rules: CC7 = 0 is silent; send All Notes Off before measuring; never change
        device settings without asking.
    - **Measurement:**
      - A/B recording (`ab`, `sim compare --live`)
      - similarity score v2 (`sim compare`)
      - interpreting the difference (`specdiff`)
      - prognosis (`prognose`, flagged as a rough indication).
    - **Skill updates from this review:**
      - `score` is now v2 (`score_version: 2`) and `spec_cos` is only a diagnostic.
      - RF predictions are rough indications only.
      - Install with `pip install -e ".[dev]"`; `requests` is a core dependency.
      - `bloridium --version` exists.
      - `build_cp70_iridium.py` takes the zip path as an argument or via `$BLORIDIUM_CP70_ZIP`.
    - **Hard boundary:** the skill covers only documented interfaces (Blofeld SysEx spec,
      Iridium MIDI CC/PC/notes, `.qpat` files). The separate tooling for remote control of
      the Iridium over undocumented SysEx **stays private**: no code, no skill, no
      commands, no names in tracked files.
21. ⬜ **Private tooling is already referenced in public tracked files.** The plan
    `docs/research/superpowers/plans/2026-11-18-english-comments-and-docs.md` set the rule that no
    tracked file may name it, but references remain in HEAD and in the git history:
    - skill name: `docs/research/superpowers/plans/2026-11-18-converter-rebuild-polyat.md` and the
      rule plan itself
    - tool names, layer name and sister-repo paths:
      - `docs/HANDOVER-2026-11-17.md`, `docs/HANDOVER-2026-11-18.md`,
        `docs/HANDOVER-2026-11-19-rf-dataset.md`
      - `docs/MAPPING-MASTER.md`
      - the runtime-enum reference file of 2026-11-18 in `docs/refs/` (also its file name)
      - `bloridium/qpat_map.py` (comments)
      - `docs/research/superpowers/plans/2026-11-18-converter-rebuild-polyat.md`
    - ✅ The `.gitignore` comment that named the sister repo is neutralised.
    - ⬜ Decide how far to clean up. Options:
      1. Neutralise the wording in HEAD, e.g. "device-side verification (private tooling)",
         and rename the enum reference file.
      2. Additionally rewrite the history (`git filter-repo`) and force-push. The GitHub
         repo is already public, so existing clones and forks keep the old state.
    - ⬜ Add a guard to the planned CI (item 12): `git grep` on the forbidden names fails
      the build.

## A. Konverter-Fixes mit Messbeleg

### A1 · ✅ umgesetzt (2026-11-21) · PWM-Zeile nur für pulsartige Wellenformen
- **Beleg:** „Osc 1/2/3 PWM Amount“ war im Test **nur auf dem Iridium hörbar**
  (Iridium 3,3–6,6× stärker, Blofeld 0,2–0,5). Ursache: Blofeld-PWM moduliert nur
  die Pulsbreite; die Iridium-Matrixzeile ging auf `WFn Warp`, das auch
  Sägezahn/Triangle verändert.
- **Stelle:** `bloridium/qpat_map.py`, Block „Osc N PWM Source/Amount“.
- **Umsetzung:** `has_pulse_width()` / `PULSE_LIKE_SHAPES`; Waveform-Oszis mit
  Saw/Triangle/Sine bekommen keine `WFn Warp`-Zeile mehr, sondern den Hinweis
  `Ignored: Osc N PWM (shape … has no pulse width)`. Wavetable-Oszis behalten
  `WTn Position`; Pulse/Square/PulSync/True PWM bleiben gemappt.
- **Verifiziert (Gerät, 2026-11-21):** `profile_testb_sweep.py osc2` (Osc 2 Saw,
  PWM Source LFO 2): PWM Source 0/8/15/30 und PWM Amount 0/32/64/127 sind jetzt
  auf **beiden** Seiten n/a (B 0,13–0,51 / I 0,14–0,43). A007: nur noch Osc 2/3
  (Pulse) erzeugen Warp-Zeilen, Osc 1 (Saw) nicht.
- **Positiver Pulse-Fall verifiziert (Gerät, 2026-11-21):**
  `profile_todo_measure.py pulse_amt` (Osc 2 = Pulse, PWM Source = LFO 1,
  LFO-Fade = 64, Filter offen). Die PWM-Zeile wird angelegt (`WF2 Warp`); der
  Blofeld moduliert bei Amount 0/127 deutlich (Wirkung 8,1/6,6; zeitliche
  Spektralstreuung 2,95/2,80). Der Iridium-Warp reagiert nur schwach
  (0,2; 0,22). Ursache ist u. a. die unkalibrierte LFO-Speed-Kurve (Blofeld
  raw 20 ≈ 0,36 Hz, Iridium `Lfo1Speed = 0,157` ≈ 0,2 Hz).
- **Tests:** `test_pwm_row_only_for_pulse_shapes`,
  `test_a007_osc_pwm_mapped_to_wf_warp_rows_ge_21`.
- **Neue offene Punkte (Fix-Session):**
  - `qpat_map.py` prüft `PWM Amount != 0`, aber 0 ist die **maximale negative**
    Modulation (64 = neutral). Amount 0 bekommt daher fälschlich keine Zeile.
  - Amount 32 (−32) zeigt am Blofeld keine messbare Modulation; die
    PWM-Betragskennlinie ist nicht linear um 64.

### A2 · ✅ umgesetzt (2026-11-21), Neumessung offen · Filter 2
- **Beleg (Profiling/Test D, verifizierter Load):** F2 **Cutoff** cos 0,89,
  Stärke 0,61 (teilweise); **Drive** bei raw 32/64 nur 0,20/0,30× so stark wie
  Blofeld, bei 127 OK (cos 0,97); **Type** defekt, weil nur `Filter12Type` (F1)
  geschrieben wurde; **Resonanz** Mismatch (cos 0,06–0,44). Die frühere
  Routing-Korrektur (A11) hatte den konstanten Offset beseitigt.
- **Stelle:** `qpat_map.py`, Filter-/Routing-Block und Filter-Drive-Block.
- **Umsetzung:**
  1. **`FilterLink`:** parallel mit aktiver F2 jetzt `Independent` (6.0). Das
     v8-Template stand auf `Boost` (1.0), das Cutoff 2/Resonanz 2 ignoriert —
     F2 wäre im qpat praktisch stumm gewesen. Seriell bleibt `Single`, weil F2
     dort im DigiFormer sitzt (nicht `Linked`; das alte TODO war hier falsch).
  2. **`Filter2Type`:** eigener F2-Typ aus der Blofeld-F2-Type (gleiche
     v14-Enum-Tabelle wie `Filter12Type`). Bisher fiel F2 auf den Geräte-Default
     12dB LP zurück; A010 bekommt jetzt 24dB LP.
  3. **Resonanz-Kennlinie:** `blofeld_reso_norm()` mappt raw 113 (Beginn der
     Blofeld-Selbstoszillation laut Handbuch) auf 1.0 statt auf 0.89; raw > 113
     wird geklemmt. Damit erreichen beide Filter die Selbstoszillation im
     gleichen Bereich, niedrige Werte bleiben proportional.
  4. **Filter-Drive:** Blofeld-Drive ist ein Insert, kein Send. `DriveDryWet`
     steht jetzt auf 1.0 (vorher `norm(drive)`, dadurch bei raw 32/64 nur
     0,20/0,30× Wirkung); `DriveAmount = norm(drive)` steuert weiter die
     Sättigung, `DriveGain` bleibt neutral.
- **Tests:** `test_parallel_routing_f2_stays_filter2_active`,
  `test_resonance_self_oscillation_calibration`,
  `test_filter_drive_simulated_as_fx1_drive_tube_a005`,
  `test_filter_drive_clipping_maps_to_pnp_and_keeps_inaudible_fx1_a043`.
- **Verifikation offen:** `f2`-Sweep mit den neuen qpat-Werten wiederholen
  (Cutoff/Reso/Drive/Type in Parallel- und Seriell-Schaltung); Details in
  `TODO_MEASURE.md`.

### A3 · ✅ umgesetzt (2026-11-21) · Reverb-Mix über `ReverbGain`
- **Beleg:** „Effect 2 Mix“ war **defekt** (Blofeld 3,3; Iridium 1,8). Es gibt
  keinen `ReverbDryWet`-qpat-Parameter; der alte Workaround (Matrix
  `Constant → FX2 DryWet`) konnte wegen des bipolaren Betrags keinen statischen
  Zwischenwert erzeugen.
- **Stelle:** `qpat_map.py`, FX-Mix-Block.
- **Umsetzung:** `ReverbGain = norm(Effect N Mix)`; Matrixzeile entfernt. Das
  Iridium-Handbuch (OS3, „Reverb / Gain“) beschreibt Gain als Dry/Wet-Regler
  (0 % = nur trocken, 100 % = nur Hall), also als echten stufenlosen Mix.
- **Test:** `test_reverb_fx2_mix_via_reverb_gain_and_params`.
- **Verifiziert (Gerät, 2026-11-21):** getrennte Messung mit
  `profile_todo_measure.py`: FX1 = Off, nur FX2 = Reverb, Effect 2 Mix
  0/32/64/127. Tail-Pegel ab 3,0 s relativ zum Halten: Blofeld
  −58,5/−27,9/−19,5/−14,9 dB, Iridium −58,9/−34,0/−23,4/−15,7 dB;
  `ReverbGain`-Readback 0,0/0,252/0,504/1,0. Beide Seiten steigen monoton über
  43 dB — **A3 verifiziert**.

### A4 · ✅ umgesetzt (2026-11-21) · Unisono Count/Detune
- **Beleg:** „Unisono Detune“ war **defekt** (Iridium-Stärke 0,69, keine Reaktion),
  obwohl `UnisonoCount` gesetzt wurde.
- **Stelle:** `qpat_map.py`, Glide/Unisono-Block.
- **Umsetzung:** Blofeld `Allocation/Unisono = 0uuu000a` (SysEx-Spec 4.10):
  Unisono-Index steht in **Bits 4–6**, nicht 5–7. Der alte `>>5` halbierte die
  Stimmenzahl (0x40 = 5 Stimmen wurde zu 3). Neuer `unison_count()` liest
  `(raw >> 4) & 7`; `UnisonoPan = 0.5` und `UnisonoDelay = 0.0` werden gesetzt,
  weil der Blofeld weder Pan-Spread noch Voice-Delay hat (Template-Default 0.25
  verzögerte die Iridium-Stimmen).
- **Verifiziert (Gerät, 2026-11-21):** `param-info 3691` = Enum 0 Off / 1 = 2 …
  7 = 8; Readback: Count 4 (5 Stimmen), Detune 1.0, Pan 0.5, Delay 0.0.
  Breiten-Metrik (5 Stimmen, C4, ±55 Hz, 2 Takes): Detune 0/32/64/127 →
  Blofeld 1,50/3,67/6,95/13,89 Hz, Iridium 1,47/1,56/3,19/11,51 Hz. Count
  0/2/4/8 (Detune 127): Blofeld 1,42 → 9,5–11,9 Hz, Iridium 1,41 → 10,5–11,6 Hz.
  Unisono greift beidseitig; die Iridium-Kennlinie ist bei kleinen Detune-Werten
  komprimiert. Die Breite trennt 2/4/8 Stimmen nicht — dafür gilt der
  `UnisonoCount`-Readback.
- **Test:** `test_unison_count_uses_bits_4_to_6`.

### A7a · ✅ umgesetzt (2026-11-21) · LFO-Fade -> Attack/Decay
- **Beleg:** „LFO 1 Fade“ war defekt (Blofeld 2,6–2,9; Iridium 0,1–0,3), obwohl
  der Iridium `LfoNAttack`/`LfoNDecay` hat.
- **Umsetzung:** Blofeld Fade ist bipolar (-64…+63, raw 64 = 0):
  raw > 64 → `LfoNAttack=(raw−64)/63` (Fade-in), raw < 64 →
  `LfoNDecay=(64−raw)/64` (Fade-out), raw 64 → beide 0.
- **Test:** `test_lfo_fade_maps_to_attack_decay`.
- **Nachmessung (2026-11-22, `docs/research/LFO-2026-11-21.md`):** Free-Speed ist
  unkalibriert — Iridium 2–4× zu langsam (raw 40: 2,63/1,09 Hz; raw 80:
  30,65/16,32 Hz). Der Blofeld-Fade ist eine **Rate** (größer = schneller),
  keine Zeit; die lineare `(raw−64)/63`-Abbildung ist in der Richtung falsch.
  Der Iridium-`Lfo1Attack/Decay` zeigt bei den konvertierten Werten (und bei
  1.0 in allen `Lfo1Global`-Modi) keine messbare Ein-/Ausblendung.
- **Offen (A7):** Free-Speed-Hz-Kurve kalibrieren; Fade-Mapping neu aufsetzen
  (Richtung invertieren, Zeitbereich prüfen).

### B2 / Block 5 · ✅ umgesetzt (2026-11-21) · Glide Mode + Rate-Kalibrierung
- **Beleg (Messung, `docs/research/GLIDE-2026-11-21.md`):** Glide on/off OK; Portamento
  Rate 50 OK (155/144 ms); ab raw 70 war der konvertierte Iridium-Glide zu kurz
  (raw 70: 1013/315 ms, raw 85: 2117/384 ms). Glide Mode wurde nicht übertragen;
  Glissando/fingered G erzeugen auf dem Blofeld Halbtonschritte, der Iridium
  glitt durchgehend.
- **Umsetzung:**
  1. **Rate:** `blofeld_glide_seconds()`/`iridium_glide_seconds()` nutzen jetzt
     die gemessenen Stützstellen (Blofeld 50/64/70/85 = 155/592/1013/2117 ms;
     Iridium 0.30/0.50/0.75/1.00 = 139/379/896/1600 ms). `glide_rate_norm()`
     invertiert die Iridium-Kurve per Gleichzeit; raw 50/64/70 -> 0.32/0.59/0.79,
     ab 85 -> 1.0. Iridium-Maximum ~1.6 s, Blofeld bis ~5 s -> hohe Raten klemmen.
  2. **Mode:** `Glide Mode` -> `GlideType`: Portamento -> Onset (0),
     fingered P -> Legato (1). Glissando/fingered G -> Onset/Legato als
     kontinuierliche Näherung; Hinweis im `unmapped`-Report.
- **Tests:** `test_glide_rate_matches_measured_curve`,
  `test_glide_mode_maps_to_glide_type`.
- **Grenze:** Iridium hat keinen Mono-/fingered-Allocation-Modus; staccato
  fingered gleitet dort trotzdem. Glissando-Schritte sind nicht abbildbar.

### A8 · ✅ umgesetzt (2026-11-21) · Filter-Pan-Ziele (Betrag bipolar)
- **Beleg (Test E, L/R, vor der Korrektur):** „Filter 1 Pan Amount“ war bei
  **100 % OK** (Cosinus 1,0), bei **0 % ohne Iridium-Wirkung** (Blofeld-Wirkung 4,6).
- **Stelle:** `qpat_map.py`, Pan-Source/Amount-Blöcke.
- **Umsetzung:** Matrixzeile wird jetzt auch bei Amount 0 angelegt (Blofeld-
  0 = voller Links-Ausschlag, nicht „aus“); `bipolar_amount_full()` = 0,5 +
  (raw−64)/127.
- **Verifiziert:** Test E Pan: 0 % OK (cos 0,998), 100 % OK (cos 0,997);
  32 % noch ohne Blofeld-Wirkung (n/a) → bei Gelegenheit feiner nachmessen.

### A11 · ✅ umgesetzt (2026-11-21) · Balance nicht auf Pan mappen
- **Beleg (Test E, L/R):** Blofeld-Balance lässt das Stereo-Bild unverändert
  (Wirkung ≈ 0), der Iridium wandert deutlich (5–12), weil der Konverter
  `Mixer Osc/Noise Balance → OscNPan` legt. Balance ist aber der F1/F2-Anteil.
- **Stelle:** `qpat_map.py`, Balance→Pan-Zuweisungen (Osc 1–3, Noise, Ringmod).
- **Umsetzung:** seriell → `OscNDestination` (2…22, F1→Former/F2); parallel →
  globale `FilterLevel`/`Filter2Level` aus dem Balance-Anteil, `OscNPan` bleibt
  center. Noise-Balance analog (kein Pan mehr).
- **Verifiziert:** L/R-Test `pan_noise` → Noise-Balance jetzt beidseitig n/a
  (kein Wandern mehr); Filter-Pan bei 0 % **OK** (cos 0,998).
- **Offen (andere Session):** per-Osc-Balance in Parallel-Schaltung ist nur global
  abbildbar (Grenze, im `unmapped`-Log vermerkt).

  
## C. Messmethodik (Voraussetzung für belastbare Fixes)

### C1 · ✅ erledigt (2026-11-21) · Dump-Load verifizieren (Readback)

- **Beleg:** Der Test-D-Lauf „f2“ war inkonsistent (konstanter Iridium-Offset);
  Verdacht: SNDD-Dump wurde vom Blofeld nicht (vollständig) übernommen.
- **Umsetzung:** `scripts/_measure.load_sndd_verified()` liest den Edit-Buffer per
  `SNDR` zurück und vergleicht die 383 SDATA-Bytes; **Wartezeit ≥ 0,35 s** nach dem
  Dump, sonst ignoriert der Blofeld die Anfrage. Alle Sweeps (Init, B/C/D, Modal)
  laden jetzt verifiziert und brechen bei Abweichung ab.
- **Offen:** den `f2`-Lauf mit verifiziertem Load **wiederholen** (Teil von A2).


### C2 · ✅ erledigt (2026-11-21) · L/R-getrennte Auswertung für Pan/Balance
- **Umsetzung:** `scripts/_measure.pan_desc()` (statisches L/R-Verhältnis,
  zeitliche Pan-Bewegung, L/R-Zentroide) + Modus `pan`/`pan_noise` in
  `profile_modal_sweep.py`.
- **Ergebnis:** Filter-Pan und alle Balance-Parameter haben jetzt ein echtes Urteil
  (Details: A8, A11). Unisono-Pan bleibt offen, weil es im Blofeld kein
  entsprechendes Bedienelement gibt (Mapping-Lücke B3).

### C3 · 🟡 teilweise erledigt (2026-11-21) · Keytrack/Velocity mit zwei Anregungen
- **Umsetzung:** Modi `keytrack` (Noten 48/72) und `velocity` (Anschläge 40/120)
  in `profile_modal_sweep.py`.
- **Ergebnis:** Filter 1 Keytrack cos 0,86 (teilweise); Filter-Env-Velocity cos 0,36
  (teilweise); Amp-Velocity bei Amount 0: Iridium 2,5× empfindlicher.
- **Offen:** (a) Velocity-Variante mit **FE-Sustain < 100** wiederholen (Sustain 100
  maskiert die Kennlinie); (b) Filter 2 Keytrack/Env-Velocity erst nach A2.

### C4 · P1 · Release in die Hauptpipeline
- **Beleg:** FE-Release blieb n/a (Amp-Release kürzer als Filter-Release);
  Amp-Release ist mit dem separaten Recorder OK.
- **Fix:** `profile_release_sweep.py` in den Hauptlauf integrieren; für FE-Release
  Amp-Release 127 + FE-Sustain > 0 + geschlossener Filter (Cutoff ≈ 70).
- **Akzeptanz:** FE-Release OK/teilweise, nicht n/a.

### C5 · P2 · Streuung der Test-B/D-Varianten senken
- **Beleg:** Mehrere klingende Oszillatoren → Baseline-Rauschen bis 3,2
  (Init: 0,3–0,8). Dadurch viele n/a und „nur Iridium“-Fehlalarme.
- **Fix:** 2 Aufnahmen je Wert mitteln, Aufnahme auf 3–4 s verlängern,
  Varianten mit einem Solooszillator bevorzugen.
- **Akzeptanz:** Rauschboden < 1,5 in allen Varianten.

---

## D. Doku und Daten

- **D1 · P1:** Profiling-Status in `docs/MAPPING-MASTER.md` übernehmen
  (✅/🟡/⚠️/❌ je Parameter, mit Verweis auf den Report). Aktuell steht dort nur
  der Detune-Fix.
- **D2 · P1:** `docs/research/ARCHITEKTUR-DIFFERENZEN.md` in `README.md`/`docs/research/STATUS.md`
  verlinken.
- **D3 · P2:** Reproduzierbaren Gesamtlauf dokumentieren
  (`profile_init_sweep.py` → Test B/C/D → `profile_analyze.py`) inkl. Reihenfolge
  und Laufzeit.
- **D4 · P2:** CSV-Spalten dokumentieren (Wirkungsmaß, Cosinus, `iridium_keys`)
  und die Rohaufnahmen (`recordings/profile/`) archivieren.

---

## E. Tests

- **E1 · P0:** `test_pwm_row_only_for_pulse_shapes` — A066/Saw erzeugt keine
  Warp-Zeile, Pulse schon.
- **E2 · P0:** Balance-/Routing-Test: `OscNDestination` 0/64/127 und
  `FilterLink` parallel/seriell.
- **E3 · P1:** Reverb-Mix-Test: `FXTotalDryWet` statt Matrix-Zeile.
- **E4 · P1:** Analyzer-Smoke-Test mit kleinem Fixture (2 Parameter, 8 npy-Dateien):
  Status, CSV-Zeilen, Kurven-JSON.
- **E5 · P2:** `fine_pitch_norm`-Test um die Grenzwerte 0/64/127 ergänzen
  (✅ Basis-Test existiert seit 2026-11-21).

---

## Erledigt (2026-11-21)

- ✅ **Detune/Fein-Stimmung kalibriert:** `0,5 + (raw − 64)/127` (vorher /254);
  Blofeld ±101 Cent, Iridium 203 Cent/Norm; nachgemessen cos 0,97–0,98.
  `qpat_map.fine_pitch_norm`, Test angepasst, `MAPPING-MASTER` aktualisiert.
- ✅ **Profiling-Sweep** über 121 Parameter / 752 Messungen inkl. Test B/C/D.
- ✅ **Architektur-Dokument** mit Differenzen und Workarounds.
- ✅ **Release-Messung** (`scripts/profile_release_sweep.py`) mit Note-off im Take.
- ✅ **MIDI auf USB-only** umgestellt (Launchpad aus); Ports verifiziert.
- ✅ **Block 4 wiederholt (2026-11-21):** F1-Resonanz bei Cutoff 65 und 85 →
  Iridium reagiert stark (5,6–5,8), aber andere Form (cos 0,06–0,20) → **Mismatch**
  statt „defekt“. F2-Resonanz (Cutoff 65) → Mismatch (cos 0,16). FE-Decay bei
  100 % OK (cos 0,90), kurze Zeiten weichen ab; FE-Attack/Sustain/Release OK.
  Release-Wiederholung mit Sustain 0 war zu verrauscht (Rauschboden 6,4) →
  frühere Messung (OK bei 100 %, cos 0,85) bleibt gültig.
- ✅ **Block 3b gemessen (2026-11-21):** F2 Keytrack mit Noten 48/72, Env Velocity
  mit 40/120, Env Amount bei Cutoff 60/FE-Sustain 60; alle drei jetzt mit Urteil.
- ✅ **Block 0/1/2 gemessen:** SNDD-Readback (`_measure.py`), Keytrack (2 Noten),
  Velocity (2 Anschläge), Pan/Balance (L/R). Neue Befunde: Balance→Pan ist
  semantisch falsch (A11), Filter-Pan-Betrag asymmetrisch (A8),
  Amp-Velocity-Kennlinie zu steil (A6-Umfeld).

---
