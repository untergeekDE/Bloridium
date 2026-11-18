# Bloridium CLI (Phase 1) – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A production-ready terminal tool `bloridium` (Phase 1: classic subcommands + SQLite bank DB) that reads Blofeld sounds, converts to Iridium (.qpat), measures via A/B and edits qpat parameters – exactly per the approved design.

**Architecture:** Thin argparse CLI (`bloridium/cli.py`) over three new library modules: `db.py` (SQLite schema/CRUD), `workflow.py` (logic from the step scripts as importable functions), `editor.py` (qpat list/set/save/diff). `scripts/step*.py` become thin wrappers (argv/exit/stdout compatible). Files remain the source of truth, the DB indexes/caches.

**Tech Stack:** Python ≥ 3.10, macOS (CoreMIDI/AVFoundation), mido + python-rtmidi + numpy, stdlib (argparse, sqlite3, json) – **no new runtime deps**; pytest as dev extra. CLI texts in German (like the repo docs at the time).

**Spec:** `docs/superpowers/specs/2026-11-08-bloridium-cli-design.md` (approved 2026-11-08; contains all builder-check decisions and user decisions).

## Global Constraints

- Never change device settings; before scans/measurements All Notes Off (CC123) on all channels of both synths; warning "CC7=0 → silent on the Iridium" anchored in the tool.
- Iridium transfer only via .qpat file (no SysEx on the device); the import instructions (USB stick, Load>Actions>Import) are printed.
- `scripts/step*.py` keep argv, exit codes AND stdout format (README copy-paste workflows).
- Exit codes: 0 ok, 1 error, 2 hardware unreachable (message with available MIDI ports).
- DB default: `BLORIDIUM_DB` env, else `<repo>/bloridium.db`; global flag `--db PATH`; `--json` for list/show/convert/ab list.
- Offline-first: `convert --dump FILE`, `bank import <dir>` need no hardware.
- Tests run without hardware (monkeypatched midi/audio); qpat roundtrip against all 41 files in `dumps/export-001/`.

## Review Focus

1. **qpat rebuild distorts parameters** (float precision/display loss) → test: roundtrip parse→build→parse over all 41 export-001 files, params identical (Task 4).
2. **`edit --set` overwrites reference presets without backup** → test: after `save`, `FILE.qpat.bak` exists with the old content (Task 4).
3. **DB/file desync** (row in DB, file deleted) → `bank list` marks the missing file, `bank show` reports clearly (Task 5).
4. **Wrong location parsing** (`a043`, `A043`, `edit`, `A1`) → tests for `parse_location` incl. error cases (Task 3).
5. **Hardware not connected** → exit 2 with port list, no traceback; `ab` sends CC123 on all channels before the measurement (monkeypatched synth records calls) (Task 5).

---

### Task 1: Packaging + CLI skeleton + test scaffolding

**Files:**
- Create: `pyproject.toml`, `bloridium/__main__.py`, `bloridium/cli.py` (parser skeleton, no subcommands yet), `tests/conftest.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Produces: `bloridium.cli:main(argv: list[str] | None = None) -> int`; `python3 -m bloridium` and console script `bloridium` after `pip install -e .`; `tests/conftest.py` provides fixtures `repo` (path to the repo root) and `db_path` (tmp_path/"test.db").

- [ ] **Step 1: Write the failing test** – `tests/test_scaffold.py`: `main(["--help"])` raises SystemExit with code 0 and prints "usage"; `import bloridium.__main__` ok.
- [ ] **Step 2: Run test, verify it fails** – `python3 -m pytest tests/test_scaffold.py -v` → FAIL (cli.main does not exist).
- [ ] **Step 3: Implement** – `pyproject.toml` (setuptools, name bloridium, deps from requirements.txt, `[project.scripts] bloridium = "bloridium.cli:main"`, dev extra with pytest); `bloridium/cli.py` with `build_parser()` (argparse, prog="bloridium", global `--db`, `--json`) and `main(argv=None)->int`; `bloridium/__main__.py` calls `cli.main()`.
- [ ] **Step 4: Verify** – `pip install -e ".[dev]"`, `python3 -m pytest tests/test_scaffold.py -v` PASS, `bloridium --help` exit 0.
- [ ] **Step 5: Commit** – `git add pyproject.toml bloridium/cli.py bloridium/__main__.py tests/ && git commit -m "chore: packaging + cli skeleton + pytest scaffolding"`

### Task 2: SQLite bank – `bloridium/db.py`

**Files:**
- Create: `bloridium/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces (consumed by Task 5): `SCHEMA_VERSION = 1`; `connect(path) -> sqlite3.Connection` (creates the DB, migrates via schema_version, foreign keys on); `upsert_sound(conn, row: dict) -> None` (PK location); `get_sound(conn, loc) -> dict | None`; `list_sounds(conn, bank: str | None = None, grep: str | None = None) -> list[dict]` (grep case-insensitive on name/location); `register_qpat(conn, path, parsed) -> int`; `list_qpats(conn) -> list[dict]`; `insert_conversion(conn, sound_location, qpat_path, mapped, unmapped: list) -> int`; `list_conversions(conn, sound=None) -> list[dict]`; `insert_ab_run(conn, label, sound_location, note, dur, report_path, blo_npy, irr_npy, report_json) -> int`; `list_ab_runs(conn, sound=None) -> list[dict]`; `get_ab_run(conn, run_id) -> dict`.
- Schema exactly like the spec: tables `sounds`, `qpats`, `conversions`, `ab_runs` (incl. `ab_runs.sound_location TEXT NULL`), plus `meta(key,value)` with schema_version.

- [ ] **Step 1: Write the failing test** – `tests/test_db.py` with tmp DB: init creates all tables; upsert+get sound; list filter bank/grep; insert/list conversions; insert/list ab_runs with sound_location filter; get_ab_run.
- [ ] **Step 2: Run, verify FAIL** – `python3 -m pytest tests/test_db.py -v` → ImportError.
- [ ] **Step 3: Implement** `bloridium/db.py` – pure sqlite3 helpers, dict row factory, `INSERT ... ON CONFLICT(location) DO UPDATE` for upsert; JSON columns via `json.dumps`.
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_db.py -v`.
- [ ] **Step 5: Commit** – `git commit -am "feat: sqlite bank db layer (db.py)"`

### Task 3: Workflow library – `bloridium/workflow.py` (refactor from step2/3/4)

**Files:**
- Create: `bloridium/workflow.py`
- Modify: none (wrappers come in Task 6)
- Test: `tests/test_workflow.py`

**Interfaces:**
- Produces: `parse_location(loc: str) -> tuple[int, int]` (bb, nn; "A001"→(0,0), "A043"→(0,42), "edit"→(0x7F,0); ValueError on invalid); `location_str(bb, nn) -> str`; `load_sndd_file(path) -> bytes` (reads .bin; decodes .hex); `read_sound(synth, loc, timeout=4.0, retries=2) -> dict` (SNDR→SNDD→`blofeld_dump.parse_sndd`, retry on timeout/checksum error); `read_bank(synth, banks: list[str], progress=None) -> dict[str, dict]` (all locations, errors collected, never aborts except 0 successes); `convert_parsed(parsed, loc, out_dir, template_path) -> tuple[Path, int, list[str]]` (qpat_map.blofeld_to_qpat_params + apply_to_template + qpat.build_qpat; writes `<name>_<loc>.qpat`); `spectral_centroid(x, sr)`, `band_energies(x, sr, n_bands=8)` (taken from step4); `measure_ab(note, dur, label, rec_dir, sound_location=None) -> dict` (All Notes Off beforehand on all channels, note on both synths, record all 20 channels, report dict + save .npy/.json; calls midi.connect itself).

- [ ] **Step 1: Write failing tests** – `tests/test_workflow.py`: parse_location cases incl. errors; `load_sndd_file` on `dumps/blofeld_sndd_A043_20261108_135516.bin` → parse_sndd yields name "SH Power"; `convert_parsed` offline (tmp out_dir, template `docs/refs/qpat/template_waveform.qpat`) → file exists, mapped>0, unmapped is a list, qpat.load of the new file contains the mapped keys (e.g. `Osc1Type`); `read_sound` with a fake synth (monkeypatch; delivers SNDD bytes) incl. retry after timeout.
- [ ] **Step 2: Run, verify FAIL.**
- [ ] **Step 3: Implement** – move the logic from `scripts/step2_read_blofeld_dump.py`, `step3_transfer_qpat.py`, `step4_measure_ab.py` (importable, no prints in core functions; progress callback instead of print).
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_workflow.py -v`.
- [ ] **Step 5: Commit** – `git commit -am "feat: workflow library (read/convert/measure) refactored from step scripts"`

### Task 4: qpat editor – `bloridium/editor.py` + roundtrip tests

**Files:**
- Create: `bloridium/editor.py`
- Test: `tests/test_editor.py`

**Interfaces:**
- Produces: `list_params(parsed: dict, grep: str | None = None) -> list[tuple[str, float, str]]` (name, value, display; grep case-insensitive); `show_param(parsed, key) -> tuple[float, str]` (KeyError→clear error); `set_param(parsed, key, value: float, display: str | None = None) -> None` (value clamp 0..1; display only if given); `save(parsed, path, backup=True) -> Path` (backup: overwrite `path.bak` with the old content, then write `qpat.build_qpat`); `diff_params(a: dict, b: dict) -> list[tuple[str, float, float, str, str]]` (only differing keys; only on one side = value None).

- [ ] **Step 1: Write failing tests** – `tests/test_editor.py`: (a) **roundtrip over all 41 files** `dumps/export-001/*.qpat`: parse→build→parse, `params` dict identical; (b) set+save on a copy of `docs/refs/qpat/template_waveform.qpat` in tmp_path: reload shows the new value, `.bak` exists and contains the old value; (c) diff_params finds the set key, unchanged keys not; (d) list_params grep filter.
- [ ] **Step 2: Run, verify FAIL.**
- [ ] **Step 3: Implement** `bloridium/editor.py` on top of `qpat.parse_qpat/build_qpat` (build_qpat gets params as {name:(value,display)}; take over sample_maps from parsed).
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_editor.py -v`.
- [ ] **Step 5: Commit** – `git commit -am "feat: qpat editor (list/set/save-with-bak/diff) + roundtrip tests over export-001"`

### Task 5: CLI – all subcommands in `bloridium/cli.py`

**Files:**
- Modify: `bloridium/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `db.*`, `workflow.*`, `editor.*`, `midi`, `audio` (exact signatures from Tasks 2-4).
- Produces: `main(argv)->int` with subcommands exactly like the spec: `status [--audio]`, `bank read BANK… [--only L1,L2]`, `bank import DIR`, `bank list [BANK] [--grep P] [--json]`, `bank show LOC`, `convert LOC [--dump F] [--out DIR] [--template F]`, `ab [--note N] [--dur S] [--label L] [--sound LOC]` (measurement) / `ab --list [--sound LOC] [--json]` / `ab --diff ID1 ID2`, `qpat info FILE [--register]`, `edit FILE (--list [--grep P] | --show K | --set K=V [--display D] [--save OUT] | --diff OTHER)`.
- Behavior: `bank read`/`import` upsert sounds + write stable copies `dumps/banks/<Bank>/<LOC>.bin`; `convert` without `--dump` reads live (exit 2 if the Blofeld is unreachable, print the port list); without `--save` on `edit` → in-place with `.bak`; `bank list` marks rows whose `sndd_path` is missing (Review Focus 3); `status` default MIDI-only, `--audio` does the step1 measurement; all hardware commands print the CC7/import hints.

- [ ] **Step 1: Write failing tests** – `tests/test_cli.py` (monkeypatch `midi.connect`/`audio.record`, tmp `--db`): `bank import dumps` fills sounds (A043 present, name "SH Power"); `bank list --json` parseable JSON output; `bank list` shows the missing-file marker (delete the row's file); `convert A043 --dump dumps/blofeld_sndd_A043_20261108_135516.bin --out tmp` writes the qpat + conversions row (mapped>0, unmapped in the DB); `qpat info dumps/export-001/00000-NotSoGrand.qpat --register` registers in qpats; `edit` set in-place with .bak (on a tmp copy); `ab --list` empty→exit 0; `ab --diff` with two runs created via db.insert_ab_run shows the band deltas; `status` without ports (monkeypatch midi.list_ports empty + connect raises) → exit 2, port list on stderr; `ab` measurement with fake synths: assert CC123 was sent on all 16 channels of both synths before note-on (Review Focus 5).
- [ ] **Step 2: Run, verify FAIL.**
- [ ] **Step 3: Implement** – one subparser per command, `--json` via a helper `emit(data, as_json)`; text tables (fixed column widths); German messages.
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_cli.py -v`; manually `bloridium --help` and `bloridium bank --help`.
- [ ] **Step 5: Commit** – `git commit -am "feat: bloridium cli subcommands (status/bank/convert/ab/qpat/edit)"`

### Task 6: step scripts as thin wrappers

**Files:**
- Modify: `scripts/step1_verify_connection.py`, `scripts/step2_read_blofeld_dump.py`, `scripts/step2_parse_blofeld_dump.py`, `scripts/step3_transfer_qpat.py`, `scripts/step4_measure_ab.py`
- Test: `tests/test_scripts.py`

**Interfaces:**
- Consumes: `workflow.*` (Task 3). Produces: identical argv/exit/stdout as before (review focus: wrapper compatibility).

- [ ] **Step 1: Write failing test** – `tests/test_scripts.py`: subprocess `python3 scripts/step2_parse_blofeld_dump.py dumps/blofeld_sndd_A043_20261108_135516.bin` → exit 0, stdout contains "SH Power"; `step3_transfer_qpat.py --help` path/argv stays (only import check of the wrapper modules, since live hardware is not in the test).
- [ ] **Step 2: Run, verify FAIL** (old scripts run, but the test checks the wrapper structure – initially FAIL because the scripts are still old).
- [ ] **Step 3: Implement** – each wrapper: sys.path bootstrap stays, then calls the workflow function with the same argv parsing and the same output (old print statements as a format layer in the wrapper, not in workflow).
- [ ] **Step 4: Verify** – `python3 -m pytest tests/test_scripts.py -v` PASS; diff of the stdout of `step2_parse` old vs. new (before/after) is empty.
- [ ] **Step 5: Commit** – `git commit -am "refactor: step scripts become thin wrappers over bloridium.workflow"`

### Task 7: Docs "production-ready" ("anwendungsreif")

**Files:**
- Modify: `README.md`
- Create: `docs/CLI.md`

- [ ] **Step 1:** extend `README.md` with a section "Bloridium CLI (Phase 1)": installation (`pip install -e ".[dev]"`), the complete workflow as copy-paste (`status` → `bank read A` → `convert A043` → import on the Iridium → `ab --sound A043` → `ab list/diff` → `edit`), safety notes (CC7, All Notes Off, never change device settings); `docs/CLI.md` = reference of all subcommands with examples and exit codes.
- [ ] **Step 2: Verify** – `bloridium <each subcommand> --help` runs without error (exit 0); check the links in README.
- [ ] **Step 3: Commit** – `git commit -am "docs: CLI workflow + reference (production-ready)"`

---

## Self-Review (checked while writing)

1. **Spec coverage:** status/bank read+import/list/show/convert/ab(+list/diff)/qpat info/edit = all subcommands of the spec; schema incl. sound_location; .bak behavior; offline-first; wrapper compat; tests offline – all covered in Tasks 1-7.
2. **Step scan:** every step names test/signature/command + expected result; no "TBD" gaps.
3. **Type consistency:** `parse_location`→(bb,nn) the same everywhere; `convert_parsed`→(Path,int,list); `save(parsed,path,backup)`; db helpers return dicts.
4. **Review focus:** all 5 points have pinned tests (Task 4: 1+2; Task 5: 3+5; Task 3: 4).
5. **Proportion:** the plan describes decisions (signatures, tests, commands), no transcripts.
