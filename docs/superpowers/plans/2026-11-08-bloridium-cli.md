# Bloridium CLI (Phase 1) – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein anwendungsreifes Terminal-Tool `bloridium` (Phase 1: klassische Subcommands + SQLite-Bank-DB), das Blofeld-Sounds ausliest, nach Iridium (.qpat) konvertiert, per A/B misst und qpat-Parameter editiert – exakt nach genehmigtem Design.

**Architecture:** Dünne argparse-CLI (`bloridium/cli.py`) über drei neuen Library-Modulen: `db.py` (SQLite-Schema/CRUD), `workflow.py` (Logik aus den step-Skripten als importierbare Funktionen), `editor.py` (qpat list/set/save/diff). `scripts/step*.py` werden zu dünnen Wrappern (argv/Exit/Stdout kompatibel). Dateien bleiben Source of Truth, die DB indexiert/cached.

**Tech Stack:** Python ≥ 3.10, macOS (CoreMIDI/AVFoundation), mido + python-rtmidi + numpy, stdlib (argparse, sqlite3, json) – **keine neuen Runtime-Deps**; pytest als dev-extra. CLI-Texte auf Deutsch (wie Repo-Doku).

**Spec:** `docs/superpowers/specs/2026-11-08-bloridium-cli-design.md` (genehmigt 2026-11-08; enthält alle Builder-Check-Festlegungen und Benutzer-Entscheidungen).

## Global Constraints

- Nie Geräte-Einstellungen ändern; vor Scans/Messungen All Notes Off (CC123) auf allen Kanälen beider Synths; Warnung „CC7=0 → stumm am Iridium" im Tool verankert.
- Iridium-Transfer nur per .qpat-Datei (kein SysEx am Gerät); Import-Anleitung (USB-Stick, Load>Actions>Import) wird ausgegeben.
- `scripts/step*.py` behalten argv, Exit-Codes UND stdout-Format (README-Copy-paste-Workflows).
- Exit-Codes: 0 ok, 1 Fehler, 2 Hardware nicht erreichbar (Meldung mit verfügbaren MIDI-Ports).
- DB-Default: `BLORIDIUM_DB` env, sonst `<repo>/bloridium.db`; globaler Flag `--db PATH`; `--json` für list/show/convert/ab list.
- Offline-first: `convert --dump FILE`, `bank import <dir>` brauchen keine Hardware.
- Tests laufen ohne Hardware (monkeypatchte midi/audio); qpat-Roundtrip gegen alle 41 Dateien in `dumps/export-001/`.

## Review Focus

1. **qpat-Rebuild verfälscht Parameter** (Float-Präzision/Display-Verlust) → Test: Roundtrip parse→build→parse über alle 41 export-001-Dateien, params identisch (Task 4).
2. **`edit --set` überschreibt Referenz-Presets ohne Backup** → Test: nach `save` existiert `FILE.qpat.bak` mit altem Inhalt (Task 4).
3. **DB/Datei-Desync** (Zeile in DB, Datei gelöscht) → `bank list` markiert fehlende Datei, `bank show` meldet klar (Task 5).
4. **Falsches Location-Parsing** (`a043`, `A043`, `edit`, `A1`) → Tests für `parse_location` inkl. Fehlerfällen (Task 3).
5. **Hardware nicht angeschlossen** → Exit 2 mit Port-Liste, kein Traceback; `ab` sendet vor Messung CC123 auf allen Kanälen (monkeypatchter Synth zeichnet Aufrufe) (Task 5).

---

### Task 1: Packaging + CLI-Skelett + Test-Scaffolding

**Files:**
- Create: `pyproject.toml`, `bloridium/__main__.py`, `bloridium/cli.py` (Parser-Skelett, noch keine Subcommands), `tests/conftest.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Produces: `bloridium.cli:main(argv: list[str] | None = None) -> int`; `python3 -m bloridium` und console script `bloridium` nach `pip install -e .`; `tests/conftest.py` stellt Fixtures `repo` (Path zum Repo-Root) und `db_path` (tmp_path/"test.db") bereit.

- [ ] **Step 1: Write the failing test** – `tests/test_scaffold.py`: `main(["--help"])` wirft SystemExit mit code 0 und printed „usage“; `import bloridium.__main__` ok.
- [ ] **Step 2: Run test, verify it fails** – `python3 -m pytest tests/test_scaffold.py -v` → FAIL (cli.main existiert nicht).
- [ ] **Step 3: Implement** – `pyproject.toml` (setuptools, name bloridium, deps aus requirements.txt, `[project.scripts] bloridium = "bloridium.cli:main"`, dev-extra mit pytest); `bloridium/cli.py` mit `build_parser()` (argparse, prog="bloridium", global `--db`, `--json`) und `main(argv=None)->int`; `bloridium/__main__.py` ruft `cli.main()`.
- [ ] **Step 4: Verify** – `pip install -e ".[dev]"`, `python3 -m pytest tests/test_scaffold.py -v` PASS, `bloridium --help` exit 0.
- [ ] **Step 5: Commit** – `git add pyproject.toml bloridium/cli.py bloridium/__main__.py tests/ && git commit -m "chore: packaging + cli skeleton + pytest scaffolding"`

### Task 2: SQLite-Bank – `bloridium/db.py`

**Files:**
- Create: `bloridium/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces (von Task 5 konsumiert): `SCHEMA_VERSION = 1`; `connect(path) -> sqlite3.Connection` (legt DB an, migriert via schema_version, foreign keys an); `upsert_sound(conn, row: dict) -> None` (PK location); `get_sound(conn, loc) -> dict | None`; `list_sounds(conn, bank: str | None = None, grep: str | None = None) -> list[dict]` (grep case-insensitive auf name/location); `register_qpat(conn, path, parsed) -> int`; `list_qpats(conn) -> list[dict]`; `insert_conversion(conn, sound_location, qpat_path, mapped, unmapped: list) -> int`; `list_conversions(conn, sound=None) -> list[dict]`; `insert_ab_run(conn, label, sound_location, note, dur, report_path, blo_npy, irr_npy, report_json) -> int`; `list_ab_runs(conn, sound=None) -> list[dict]`; `get_ab_run(conn, run_id) -> dict`.
- Schema exakt wie Spec: Tabellen `sounds`, `qpats`, `conversions`, `ab_runs` (inkl. `ab_runs.sound_location TEXT NULL`), plus `meta(key,value)` mit schema_version.

- [ ] **Step 1: Write the failing test** – `tests/test_db.py` mit tmp-DB: init legt alle Tabellen an; upsert+get sound; list filter bank/grep; insert/list conversions; insert/list ab_runs mit sound_location-Filter; get_ab_run.
- [ ] **Step 2: Run, verify FAIL** – `python3 -m pytest tests/test_db.py -v` → ImportError.
- [ ] **Step 3: Implement** `bloridium/db.py` – reine sqlite3-Helfer, Row-Factory dict, `INSERT ... ON CONFLICT(location) DO UPDATE` für upsert; JSON-Spalten via `json.dumps`.
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_db.py -v`.
- [ ] **Step 5: Commit** – `git commit -am "feat: sqlite bank db layer (db.py)"`

### Task 3: Workflow-Library – `bloridium/workflow.py` (Refactor aus step2/3/4)

**Files:**
- Create: `bloridium/workflow.py`
- Modify: keine (Wrapper kommen in Task 6)
- Test: `tests/test_workflow.py`

**Interfaces:**
- Produces: `parse_location(loc: str) -> tuple[int, int]` (bb, nn; „A001“→(0,0), „A043"→(0,42), „edit“→(0x7F,0); ValueError bei ungültig); `location_str(bb, nn) -> str`; `load_sndd_file(path) -> bytes` (liest .bin; .hex dekodiert); `read_sound(synth, loc, timeout=4.0, retries=2) -> dict` (SNDR→SNDD→`blofeld_dump.parse_sndd`, Retry bei Timeout/Checksum-Fehler); `read_bank(synth, banks: list[str], progress=None) -> dict[str, dict]` (alle Locations, Fehler gesammelt, nie abgebrochen außer 0 Erfolge); `convert_parsed(parsed, loc, out_dir, template_path) -> tuple[Path, int, list[str]]` (qpat_map.blofeld_to_qpat_params + apply_to_template + qpat.build_qpat; schreibt `<name>_<loc>.qpat`); `spectral_centroid(x, sr)`, `band_energies(x, sr, n_bands=8)` (aus step4 übernommen); `measure_ab(note, dur, label, rec_dir, sound_location=None) -> dict` (All Notes Off vorab auf allen Kanälen, Note auf beiden Synths, Aufnahme aller 20 Kanäle, Report dict + .npy/.json speichern; ruft midi.connect selbst).

- [ ] **Step 1: Write failing tests** – `tests/test_workflow.py`: parse_location Fälle inkl. Fehler; `load_sndd_file` auf `dumps/blofeld_sndd_A043_20261108_135516.bin` → parse_sndd liefert name „SH Power"; `convert_parsed` offline (tmp out_dir, Template `docs/refs/qpat/template_waveform.qpat`) → Datei existiert, mapped>0, unmapped ist Liste, qpat.load der neuen Datei enthält gemappte Keys (z. B. `Osc1Type`); `read_sound` mit Fake-Synth (monkeypatch; liefert SNDD-Bytes) inkl. Retry nach Timeout.
- [ ] **Step 2: Run, verify FAIL.**
- [ ] **Step 3: Implement** – Logik aus `scripts/step2_read_blofeld_dump.py`, `step3_transfer_qpat.py`, `step4_measure_ab.py` verschieben (importierbar, keine prints in Kernfunktionen; progress-Callback statt print).
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_workflow.py -v`.
- [ ] **Step 5: Commit** – `git commit -am "feat: workflow library (read/convert/measure) refactored from step scripts"`

### Task 4: qpat-Editor – `bloridium/editor.py` + Roundtrip-Tests

**Files:**
- Create: `bloridium/editor.py`
- Test: `tests/test_editor.py`

**Interfaces:**
- Produces: `list_params(parsed: dict, grep: str | None = None) -> list[tuple[str, float, str]]` (name, value, display; grep case-insensitive); `show_param(parsed, key) -> tuple[float, str]` (KeyError→klarer Fehler); `set_param(parsed, key, value: float, display: str | None = None) -> None` (value clamp 0..1; display nur wenn angegeben); `save(parsed, path, backup=True) -> Path` (backup: `path.bak` mit altem Inhalt überschreiben, dann `qpat.build_qpat` schreiben); `diff_params(a: dict, b: dict) -> list[tuple[str, float, float, str, str]]` (nur differing keys; nur in einer Seite = value None).

- [ ] **Step 1: Write failing tests** – `tests/test_editor.py`: (a) **Roundtrip über alle 41 Dateien** `dumps/export-001/*.qpat`: parse→build→parse, `params` dict identisch; (b) set+save auf Kopie von `docs/refs/qpat/template_waveform.qpat` in tmp_path: reload zeigt neuen Wert, `.bak` existiert und enthält alten Wert; (c) diff_params findet gesetzten Key, unveränderte Keys nicht; (d) list_params grep filtert.
- [ ] **Step 2: Run, verify FAIL.**
- [ ] **Step 3: Implement** `bloridium/editor.py` auf Basis `qpat.parse_qpat/build_qpat` (build_qpat bekommt params als {name:(value,display)}; sample_maps aus parsed übernehmen).
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_editor.py -v`.
- [ ] **Step 5: Commit** – `git commit -am "feat: qpat editor (list/set/save-with-bak/diff) + roundtrip tests over export-001"`

### Task 5: CLI – alle Subcommands in `bloridium/cli.py`

**Files:**
- Modify: `bloridium/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `db.*`, `workflow.*`, `editor.*`, `midi`, `audio` (exakte Signaturen aus Task 2–4).
- Produces: `main(argv)->int` mit Subcommands exakt wie Spec: `status [--audio]`, `bank read BANK… [--only L1,L2]`, `bank import DIR`, `bank list [BANK] [--grep P] [--json]`, `bank show LOC`, `convert LOC [--dump F] [--out DIR] [--template F]`, `ab [--note N] [--dur S] [--label L] [--sound LOC]` (Messung) / `ab --list [--sound LOC] [--json]` / `ab --diff ID1 ID2`, `qpat info FILE [--register]`, `edit FILE (--list [--grep P] | --show K | --set K=V [--display D] [--save OUT] | --diff OTHER)`.
- Verhalten: `bank read`/`import` upserten sounds + schreiben stabile Kopien `dumps/banks/<Bank>/<LOC>.bin`; `convert` ohne `--dump` liest live (Exit 2 wenn Blofeld nicht erreichbar, Port-Liste ausgeben); ohne `--save` bei `edit` → in-place mit `.bak`; `bank list` markiert Zeilen deren `sndd_path` fehlt (Review Focus 3); `status` default MIDI-only, `--audio` macht step1-Messung; alle Hardware-Kommandos geben CC7-/Import-Hinweise aus.

- [ ] **Step 1: Write failing tests** – `tests/test_cli.py` (monkeypatch `midi.connect`/`audio.record`, tmp `--db`): `bank import dumps` befüllt sounds (A043 vorhanden, name „SH Power“); `bank list --json` parsebarer JSON-Output; `bank list` zeigt fehlende-Datei-Markierung (Zeile löschen, Datei weg); `convert A043 --dump dumps/blofeld_sndd_A043_20261108_135516.bin --out tmp` schreibt qpat + conversions-Row (mapped>0, unmapped in DB); `qpat info dumps/export-001/00000-NotSoGrand.qpat --register` trägt in qpats ein; `edit` set in-place mit .bak (auf tmp-Kopie); `ab --list` leer→exit 0; `ab --diff` mit zwei per db.insert_ab_run angelegten Runs zeigt Band-Deltas; `status` ohne Ports (monkeypatch midi.list_ports leer + connect wirft) → exit 2, Port-Liste in stderr; `ab`-Messung mit Fake-Synths: assert CC123 wurde vor NoteOn auf allen 16 Kanälen beider Synths gesendet (Review Focus 5).
- [ ] **Step 2: Run, verify FAIL.**
- [ ] **Step 3: Implement** – Subparser je Kommando, `--json` via helper `emit(data, as_json)`; Text-Tabellen (feste Spaltenbreiten); deutsche Meldungen.
- [ ] **Step 4: Verify PASS** – `python3 -m pytest tests/test_cli.py -v`; manuell `bloridium --help` und `bloridium bank --help`.
- [ ] **Step 5: Commit** – `git commit -am "feat: bloridium cli subcommands (status/bank/convert/ab/qpat/edit)"`

### Task 6: step-Skripte als dünne Wrapper

**Files:**
- Modify: `scripts/step1_verify_connection.py`, `scripts/step2_read_blofeld_dump.py`, `scripts/step2_parse_blofeld_dump.py`, `scripts/step3_transfer_qpat.py`, `scripts/step4_measure_ab.py`
- Test: `tests/test_scripts.py`

**Interfaces:**
- Consumes: `workflow.*` (Task 3). Produces: identisches argv/Exit/Stdout wie bisher (Review-Fokus: Wrapper-Kompatibilität).

- [ ] **Step 1: Write failing test** – `tests/test_scripts.py`: subprocess `python3 scripts/step2_parse_blofeld_dump.py dumps/blofeld_sndd_A043_20261108_135516.bin` → exit 0, stdout enthält „SH Power“; `step3_transfer_qpat.py --help`-Pfad/argv bleibt (nur Import-Check der Wrapper-Module, da Live-Hardware nicht im Test).
- [ ] **Step 2: Run, verify FAIL** (alte Skripte laufen zwar, aber Test prüft Wrapper-Struktur – initial FAIL weil Skripte noch alt).
- [ ] **Step 3: Implement** – jeder Wrapper: sys.path-Bootstrap bleibt, dann Aufruf der workflow-Funktion mit gleichem argv-Parsing und gleicher Ausgabe (alte print-Statements als Format-Layer im Wrapper, nicht in workflow).
- [ ] **Step 4: Verify** – `python3 -m pytest tests/test_scripts.py -v` PASS; Diff der stdout von `step2_parse` alt vs. neu (vor/nach) ist leer.
- [ ] **Step 5: Commit** – `git commit -am "refactor: step scripts become thin wrappers over bloridium.workflow"`

### Task 7: Doku „anwendungsreif“

**Files:**
- Modify: `README.md`
- Create: `docs/CLI.md`

- [ ] **Step 1:** `README.md` um Abschnitt „Bloridium CLI (Phase 1)“ ergänzen: Installation (`pip install -e ".[dev]"`), kompletter Workflow als copy-paste (`status` → `bank read A` → `convert A043` → Import am Iridium → `ab --sound A043` → `ab list/diff` → `edit`), Safety-Hinweise (CC7, All Notes Off, nie Geräteeinstellungen ändern); `docs/CLI.md` = Referenz aller Subcommands mit Beispielen und Exit-Codes.
- [ ] **Step 2: Verify** – `bloridium <jeder Subcommand> --help` läuft fehlerfrei (exit 0); Links in README prüfen.
- [ ] **Step 3: Commit** – `git commit -am "docs: CLI workflow + reference (anwendungsreif)"`

---

## Self-Review (beim Schreiben geprüft)

1. **Spec-Coverage:** status/bank read+import/list/show/convert/ab(+list/diff)/qpat info/edit = alle Subcommands des Specs; Schema inkl. sound_location; .bak-Verhalten; offline-first; Wrapper-Kompat; Tests offline – alles in Tasks 1–7 abgebildet.
2. **Step-Scan:** Jeder Step nennt Test/Signatur/Command + erwartetes Ergebnis; keine „TBD“-Lücken.
3. **Typ-Konsistenz:** `parse_location`→(bb,nn) überall gleich; `convert_parsed`→(Path,int,list); `save(parsed,path,backup)`; db-Helfer liefern dicts.
4. **Review Focus:** alle 5 Punkte haben gepinnte Tests (Task 4: 1+2; Task 5: 3+5; Task 3: 4).
5. **Proportion:** Plan beschreibt Entscheidungen (Signaturen, Tests, Commands), keine Transkripte.
