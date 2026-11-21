# Fixes & TODO (review 2026-11-20)

Outcome of a code review of `64c73e3`. Fixes live on branch `fix/review-notes`.
Legend: ✅ done · 🟡 partly done · ⬜ open · 🖥 to do on the measurement machine (Mac + synths)

Test baseline on Linux without private data: 200 passed / 46 failed / 17 errors.
All remaining failures come from the missing `dumps/` and `recordings/` data. The full
suite is run on the measurement machine (item 11).

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
   - ⬜ If not: get more and more varied data, use fewer features, or drop the RF in favour
     of the placeholder.
3. ⬜ **Own random forest instead of sklearn**, kept only because scipy was broken locally.
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
   - ⬜ `load_core()` could now shrink to plain imports. It stays for now because it serves
     the flat `/app/core` container layout.

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
    - ⬜ Change to `GPL-3.0-or-later` if "or any later version" is intended.
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
    - ⬜ Still German: `docs/HANDOVER-2026-11-18.md`, `docs/HANDOVER-2026-11-19-rf-dataset.md`,
      some comments in `tests/` and `scripts/spike_*`.
17. 🟡 **Stale docs.**
    - ✅ `docs/STATUS.md` has a "partly outdated" banner, and the absolute path is removed.
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
      below and nothing else; guard: `git grep -E "QUIR|quir_|midi-sysex|codesearch|
      load-patch|set-pid|dump-params|find-pid" skills/` must stay empty.
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
    `docs/superpowers/plans/2026-11-18-english-comments-and-docs.md` set the rule that no
    tracked file may name it, but references remain in HEAD and in the git history:
    - skill name: `docs/superpowers/plans/2026-11-18-converter-rebuild-polyat.md` and the
      rule plan itself
    - tool names, layer name and sister-repo paths:
      - `docs/HANDOVER-2026-11-17.md`, `docs/HANDOVER-2026-11-18.md`,
        `docs/HANDOVER-2026-11-19-rf-dataset.md`
      - `docs/MAPPING-MASTER.md`
      - the runtime-enum reference file of 2026-11-18 in `docs/refs/` (also its file name)
      - `bloridium/qpat_map.py` (comments)
      - `docs/superpowers/plans/2026-11-18-converter-rebuild-polyat.md`
    - ✅ The `.gitignore` comment that named the sister repo is neutralised.
    - ⬜ Decide how far to clean up. Options:
      1. Neutralise the wording in HEAD, e.g. "device-side verification (private tooling)",
         and rename the enum reference file.
      2. Additionally rewrite the history (`git filter-repo`) and force-push. The GitHub
         repo is already public, so existing clones and forks keep the old state.
    - ⬜ Add a guard to the planned CI (item 12): `git grep` on the forbidden names fails
      the build.
