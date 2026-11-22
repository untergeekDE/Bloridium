# Design: Bloridium CLI – Phase 1 (classic terminal tool + SQLite bank)

Date: 2026-11-08
Status: draft for approval

## Intent & Why

The user wants to turn the existing step scripts into a **production-ready
terminal tool**. "Production-ready" means concretely: today everything is only
superficially documented – you have to know the scripts individually and
assemble them yourself. The tool should be a single command `bloridium` that
drives the whole workflow: read Blofeld sounds (bank manager), convert to
Iridium (.qpat), test via A/B measurement, edit parameters
(Iridium editor). Phase 1 is **classic** (subcommands, no interactivity);
an interactive variant (menus/TUI) is **Phase 2** and out of scope here.

The user deliberately chose **approach B (CLI + SQLite bank database)**
so that searching across all sounds, conversion history and A/B history
are queryable.

## Goals

- One command `bloridium` (as `python3 -m bloridium` and as console script
  `bloridium` after `pip install -e .`), building on the existing library
  `bloridium/`.
- Subcommands: `status`, `bank read/list/show`, `convert`, `ab` (+ `list`/`diff`),
  `qpat info`, `edit`.
- SQLite DB as the bank-manager backbone (see schema below). Files remain
  the source of truth (`dumps/`, `transfer/`, `recordings/`); the DB indexes and
  caches parsed data.
- **Offline-first:** every hardware command accepts file input
  (`convert --dump …`), so the tool can be developed, tested and documented
  without connected synths.
- Docs in the tool: `--help` per subcommand with examples, JSON output via `--json`
  for scripting, warnings firmly anchored (All Notes Off before scans, CC7=0 →
  silent on the Iridium, import on the Iridium only via USB stick/SD via Load>Actions>Import).

## Non-Goals (Phase 1)

- No interactive TUI / no menus (Phase 2).
- No automatic copying onto the USB stick (the Iridium has no
  USB drive mode on the Mac); the tool prints the import instructions.
- No changes to device settings (never without asking, see Constraints).
- Closing mapping gaps (unmapped list from `qpat_map`) is a separate,
  ongoing workstream – the CLI should only make them visible, not solve them.
- Sample-based patches (Particle/Resonator with sample maps) stay open.

## Anti-Goals

- The existing `scripts/step*.py` must not break – they become
  thin wrappers around the refactored library functions.
- No new runtime dependencies except stdlib (`argparse`, `sqlite3`, `json`);
  existing deps stay `mido`, `python-rtmidi`, `numpy`.
- No binary data exclusively in the DB – .bin/.qpat/.npy stay in
  `dumps/`, `transfer/`, `recordings/`.

## Constraints (empirically verified, see docs/FINDINGS.md, docs/research/STATUS.md)

- **Blofeld** (FW 1.24): USB port `Blofeld`, MIDI channel 5 (1-based), SINGLE
  MODE. SysEx fully supported: SNDR `F0 3E 13 00 00 BB NN F7` → SNDD
  `… 10 BB NN <383 B SDATA> CHK F7`. Location: A001 = `00 00`, edit buffer =
  `7F 00`. SNDD parser/builder: `bloridium/blofeld_dump.py` (spec
  `docs/manuals/Blofeld_sysex_v1_04.pdf`, SDATA 0..382).
- **Iridium** (OS4/SOM2): **no SysEx layer** – patch transfer only as
  `.qpat` file via USB stick/SD (Load>Actions>Import/Export). MIDI: endpoint
  `Iridium Keyboard (MIDI 2.0) MIDI 2.0`, Parts 1-4 = channels 6-9. **CC7 = Output
  Level (0 = silent!)**. `.qpat` format: 512-B header (magic 3402932) +
  68-B records; parser/writer: `bloridium/qpat.py` (roundtrip-tested).
- **Scarlett 18i8:** 20 channels @ 48 kHz via ffmpeg/AVFoundation
  (`bloridium/audio.py`); Blofeld → In 3/4 (index 2/3), Iridium → In 5/6
  (index 4/5).
- Rules: before channel scans send All Notes Off (CC123) on all channels + wait for
  release; never change hardware settings on the device without asking.
- Environment: macOS (CoreMIDI/AVFoundation), Python ≥ 3.10.
- Reference data on disk: 41 Iridium presets (00000-00040) as `.qpat` in
  `dumps/export-001/` – usable as editor targets, enum reference and
  roundtrip test data.

## Approaches

- **A – argparse CLI, purely file-based:** subcommands, storage only as
  files + JSON index. Simple, no duplicate data holding, but no
  history/search features. *Not chosen.*
- **B – argparse CLI + SQLite bank database (CHOSEN):** like A, plus a DB for
  sounds, qpats, conversions, ab_runs. Enables searching across all 512 sounds
  (4 banks × 128), conversion history per sound and A/B history with diff.
  Tradeoff: the DB must be kept consistent with the files (upsert on
  every read/convert; the files remain authoritative). Chosen by the user on
  2026-11-08.
- **C – directly interactive TUI (textual/curses):** postponed by the user to Phase 2. *Not in Phase 1.*

## How (decided by the user or proposed)

### Layout

- `bloridium/cli.py` – argparse CLI with subcommands, global flags `--db PATH`
  (default: `BLORIDIUM_DB` env or `<repo>/bloridium.db`) and `--json`.
- `bloridium/__main__.py` – `python3 -m bloridium …`.
- `bloridium/db.py` – sqlite3 schema + helpers (init/migrate via `schema_version`).
- `bloridium/workflow.py` – the logic of today's step scripts as importable
  functions: `read_sound(location) -> parsed`, `read_bank(bank) -> …`,
  `convert_parsed(parsed, loc, out_dir, template) -> (path, mapped, unmapped)`,
  `measure_ab(note, dur, label) -> report`. `scripts/step*.py` become thin
  wrappers (backward compatible).
- `pyproject.toml` – `pip install -e .` provides the console script `bloridium`.

### DB schema (SQLite)

- `sounds(location TEXT PRIMARY KEY, bank TEXT, slot INTEGER, name TEXT,
  category TEXT, sndd_path TEXT, parsed_json TEXT, dumped_at TEXT, source TEXT)`
  – one row per Blofeld sound (e.g. `A043`), `parsed_json` = complete
  `parse_sndd` result.
- `qpats(id INTEGER PRIMARY KEY, path TEXT UNIQUE, name TEXT, source TEXT,
  params_json TEXT, registered_at TEXT)` – registered .qpat files
  (transfer outputs, export-001 presets, device readbacks).
- `conversions(id INTEGER PRIMARY KEY, sound_location TEXT, qpat_path TEXT,
  created_at TEXT, mapped INTEGER, unmapped_json TEXT)` – history: which
  Blofeld sound was converted to which .qpat when, incl. unmapped list.
- `ab_runs(id INTEGER PRIMARY KEY, label TEXT, sound_location TEXT NULL,
  note INTEGER, dur REAL, ts TEXT, report_path TEXT, blofeld_npy TEXT,
  iridium_npy TEXT, report_json TEXT)` – A/B measurements; `sound_location` links
  the run to a sound (user decision 2026-11-08).

### Subcommands (Phase 1, non-interactive)

```
bloridium status                                  # ports, identity, sound check (ex step1)
bloridium bank read A [--only A043,A044]          # SNDR all locations of the bank(s) → dumps/banks/A/*.bin + DB upsert
bloridium bank import <dir>                       # OFFLINE: parse existing SNDD .bin/.hex from dir → DB upsert
                                                   # + stable copies under dumps/banks/<Bank>/<LOC>.bin
bloridium bank list [BANK] [--grep PAT] [--json] # table from the DB: location, name, category
bloridium bank show A043                          # parsed parameters (like step2_parse)
bloridium convert A043 [--dump FILE.bin] [--out DIR] [--template FILE.qpat]
                                                   # SNDD (live or file) → transfer/<name>_<loc>.qpat
                                                   # + conversions row; printed unmapped report
bloridium ab --note 36 --dur 3 --label shpower [--sound A043]
                                                   # A/B measurement (ex step4) + ab_runs row + report
bloridium ab list [--sound A043] [--json]         # last runs, optionally filtered per sound
bloridium ab diff ID1 ID2                         # band deltas of two runs side by side
bloridium qpat info FILE.qpat [--register]        # parse, display, roundtrip check; optionally register in qpats
bloridium edit FILE.qpat --list [--grep PAT]      # parameter table (name, value, display)
bloridium edit FILE.qpat --show Key
bloridium edit FILE.qpat --set Key=0.5 [--display "…"] [--save OUT.qpat]
                                                   # without --save: in-place, creates FILE.qpat.bak before
bloridium edit FILE.qpat --diff OTHER.qpat        # parameter diff of two .qpat
```

- `edit` accepts any `.qpat` – also the 41 presets from
  `dumps/export-001/` as reference. Values: float 0..1 (qpat normalization) or
  `--set Key=display:value`; display strings survive the rebuild.
- `convert` reads live via SysEx (Blofeld must be connected) or offline via
  `--dump`; writes to `transfer/` (overridable with `--out`).
- `ab` sends All Notes Off on all channels of both synths before the measurement and
  prints the import instructions for the Iridium (USB stick, Load>Actions>Import).

### Output & errors

- Plain-text tables (no color dependency), `--json` for list/show/convert/
  ab list. Exit codes: 0 ok, 1 error, 2 hardware unreachable (clear message
  with available MIDI ports).

### Tests

- Offline unit tests without hardware: qpat roundtrip against all 41 files in
  `dumps/export-001/`, DB schema/CRUD, CLI smoke tests (argparse + monkeypatched
  `midi`/`audio`) for `bank list`, `convert --dump`, `edit --set/--save`,
  `qpat info`, `ab diff`. No live MIDI in tests.

## Builder check – decisions (2026-11-08)

Builder check by subagent; questions sorted. The following points are builder
calls, anchored in the document:

- **Error semantics `bank read`:** per sound timeout 4 s, 2 retries; on error
  continue reading and report collected at the end; **incremental upsert** per
  received SNDD (read is re-runnable, partial reads are not poison); mode
  (Single/Multi) is only **warned**, never changed (device rules). Exit 0
  if ≥1 sound read, else exit 2.
- **`edit --set` values:** Phase 1 only float (`--set Key=0.5`) plus optional
  `--display "text"` (display string, float stays). A `display:` evaluation
  against enum tables does **not** exist (enum tables in `qpat_map.py` are
  incomplete; their extension remains for the mapping workstream).
- **Wrapper compatibility:** `scripts/step*.py` keep argv, exit codes **and**
  stdout format (README/STATUS copy-paste workflows depend on them).
- **`status`:** default MIDI-only (ports + identity), `--audio` adds the
  complete step1 level measurement (ffmpeg/Scarlett); without ffmpeg graceful
  degradation. Exit 2 only if a requested synth is unreachable.
- **Bank/location range:** no artificial A-D limit; the CLI accepts
  what the parser can do (A-Z, see step2 parser). `bank read` gets explicit
  bank letters.

User decisions (2026-11-08) on the open builder-check questions:

- **Q1 offline ingest:** own command `bank import <dir>` (see subcommands);
  stable file storage per location under `dumps/banks/<Bank>/<LOC>.bin`
  (latest state overwrites the copy; the timestamped original dumps in
  `dumps/` remain untouched).
- **Q3 `edit --set` without `--save`:** in-place, automatically creates
  `FILE.qpat.bak` before. `--save OUT.qpat` writes to OUT instead.
- **Q6 ab ↔ sound:** `ab_runs.sound_location` (nullable) + `ab --sound A043` +
  `ab list --sound A043`.

## What's left to the builder

- Exact table formatting and JSON shapes.
- Order of the refactor steps (library functions first, wrappers after).
- Whether `pyproject.toml` is created new or existing packaging is used
  (the repo currently has none) – proposal: new, minimal, `pip install -e .`.
- Phase 2 (interactive TUI) is designed separately once Phase 1 stands.
