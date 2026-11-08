# Design: Bloridium CLI – Phase 1 (klassisches Terminal-Tool + SQLite-Bank)

Datum: 2026-11-08
Status: Entwurf zur Genehmigung

## Intent & Why

Der Benutzer möchte aus den bestehenden Step-Skripten ein **anwendungsreifes
Terminal-Tool** machen. „Anwendungsreif" heißt konkret: heute ist alles nur
oberflächlich dokumentiert – man muss die Skripte einzeln kennen und
zusammensetzen. Das Tool soll ein einziges Kommando `bloridium` sein, das den
gesamten Workflow führt: Blofeld-Sounds auslesen (Bank-Manager), nach Iridium
konvertieren (.qpat), per A/B-Messung testen, Parameter editieren
(Iridium-Editor). Phase 1 ist **klassisch** (Subcommands, keine Interaktivität),
eine interaktive Variante (Menüs/TUI) ist **Phase 2** und hier nicht im Scope.

Der Benutzer hat sich bewusst für **Ansatz B (CLI + SQLite-Bankdatenbank)**
entschieden, damit Suchen über alle Sounds, Konvertierungshistorie und A/B-Verlauf
abfragbar sind.

## Goals

- Ein Kommando `bloridium` (als `python3 -m bloridium` und als console script
  `bloridium` nach `pip install -e .`), aufbauend auf der bestehenden Library
  `bloridium/`.
- Subcommands: `status`, `bank read/list/show`, `convert`, `ab` (+ `list`/`diff`),
  `qpat info`, `edit`.
- SQLite-DB als Bank-Manager-Backbone (siehe Schema unten). Dateien bleiben
  Source of Truth (`dumps/`, `transfer/`, `recordings/`); die DB indexiert und
  cached geparste Daten.
- **Offline-first:** Jedes Hardware-Kommando akzeptiert Datei-Input
  (`convert --dump …`), damit das Tool ohne angeschlossene Synths entwickel-,
  test- und dokumentierbar ist.
- Doku im Tool: `--help` pro Subcommand mit Beispielen, JSON-Ausgabe per `--json`
  für Scripting, Warnhinweise fest verankert (All Notes Off vor Scans, CC7=0 →
  stumm am Iridium, Import am Iridium nur per USB-Stick/SD via Load>Actions>Import).

## Non-Goals (Phase 1)

- Keine interaktive TUI / keine Menüs (Phase 2).
- Kein automatisches Kopieren auf den USB-Stick (der Iridium hat keinen
  USB-Drive-Modus am Mac); das Tool gibt die Import-Anleitung aus.
- Keine Änderungen von Geräte-Einstellungen (nie ohne Rückfrage, siehe Constraints).
- Mapping-Lücken schließen (unmapped-Liste aus `qpat_map`) ist ein eigener,
  laufender Arbeitsstrang – die CLI soll sie nur sichtbar machen, nicht lösen.
- Sample-basierte Patches (Particle/Resonator mit Sample-Maps) bleiben offen.

## Anti-Goals

- Die bestehenden `scripts/step*.py` dürfen nicht kaputt gehen – sie werden zu
  dünnen Wrappern um die refactorten Library-Funktionen.
- Keine neuen Runtime-Dependencies außer stdlib (`argparse`, `sqlite3`, `json`);
  bestehende Deps bleiben `mido`, `python-rtmidi`, `numpy`.
- Keine Binärdaten ausschließlich in der DB – .bin/.qpat/.npy bleiben in
  `dumps/`, `transfer/`, `recordings/`.

## Constraints (empirisch verifiziert, siehe docs/FINDINGS.md, docs/STATUS.md)

- **Blofeld** (FW 1.24): USB-Port `Blofeld`, MIDI-Kanal 5 (1-basiert), SINGLE
  MODE. SysEx voll unterstützt: SNDR `F0 3E 13 00 00 BB NN F7` → SNDD
  `… 10 BB NN <383 B SDATA> CHK F7`. Location: A001 = `00 00`, Edit-Puffer =
  `7F 00`. SNDD-Parser/Builder: `bloridium/blofeld_dump.py` (Spec
  `docs/manuals/Blofeld_sysex_v1_04.pdf`, SDATA 0..382).
- **Iridium** (OS4/SOM2): **keine SysEx-Schicht** – Patch-Transfer nur als
  `.qpat`-Datei per USB-Stick/SD (Load>Actions>Import/Export). MIDI: Endpunkt
  `Iridium Keyboard (MIDI 2.0) MIDI 2.0`, Parts 1–4 = Kanal 6–9. **CC7 = Output
  Level (0 = stumm!)**. `.qpat`-Format: 512-B-Header (magic 3402932) +
  68-B-Records; Parser/Writer: `bloridium/qpat.py` (roundtrip-getestet).
- **Scarlett 18i8:** 20 Kanäle @ 48 kHz via ffmpeg/AVFoundation
  (`bloridium/audio.py`); Blofeld → In 3/4 (Index 2/3), Iridium → In 5/6
  (Index 4/5).
- Regeln: vor Kanal-Scans All Notes Off (CC123) auf allen Kanälen + Release
  abwarten; nie Hardware-Einstellungen am Gerät ändern ohne Rückfrage.
- Umgebung: macOS (CoreMIDI/AVFoundation), Python ≥ 3.10.
- Referenzdaten auf Platte: 41 Iridium-Presets (00000–00040) als `.qpat` in
  `dumps/export-001/` – nutzbar als Editor-Ziele, Enum-Referenz und
  Roundtrip-Testdaten.

## Approaches

- **A – argparse-CLI, rein dateibasiert:** Subcommands, Speicherung nur als
  Dateien + JSON-Index. Einfach, keine doppelte Datenhaltung, aber keine
  Verlaufs-/Such-Features. *Nicht gewählt.*
- **B – argparse-CLI + SQLite-Bankdatenbank (GEWÄHLT):** wie A, plus DB für
  Sounds, qpats, conversions, ab_runs. Ermöglicht Suchen über alle 512 Sounds
  (4 Bänke × 128), Konvertierungshistorie pro Sound und A/B-Verlauf mit Diff.
  Tradeoff: DB muss mit den Dateien konsistent gehalten werden ( Upsert bei
  jedem Read/Convert; Dateien bleiben maßgeblich). Gewählt vom Benutzer am
  2026-11-08.
- **C – direkt interaktives TUI (textual/curses):** vom Benutzer auf Phase 2
  verschoben. *Nicht in Phase 1.*

## How (vom Benutzer entschieden bzw. propuesto)

### Layout

- `bloridium/cli.py` – argparse-CLI mit Subcommands, globale Flags `--db PATH`
  (Default: `BLORIDIUM_DB` env oder `<repo>/bloridium.db`) und `--json`.
- `bloridium/__main__.py` – `python3 -m bloridium …`.
- `bloridium/db.py` – sqlite3-Schema + Helper (init/migrate via `schema_version`).
- `bloridium/workflow.py` – die Logik der heutigen Step-Skripte als importierbare
  Funktionen: `read_sound(location) -> parsed`, `read_bank(bank) -> …`,
  `convert_parsed(parsed, loc, out_dir, template) -> (path, mapped, unmapped)`,
  `measure_ab(note, dur, label) -> report`. `scripts/step*.py` werden dünne
  Wrapper (abwärtskompatibel).
- `pyproject.toml` – `pip install -e .` liefert console script `bloridium`.

### DB-Schema (SQLite)

- `sounds(location TEXT PRIMARY KEY, bank TEXT, slot INTEGER, name TEXT,
  category TEXT, sndd_path TEXT, parsed_json TEXT, dumped_at TEXT, source TEXT)`
  – ein Row pro Blofeld-Sound (z. B. `A043`), `parsed_json` = komplettes
  `parse_sndd`-Ergebnis.
- `qpats(id INTEGER PRIMARY KEY, path TEXT UNIQUE, name TEXT, source TEXT,
  params_json TEXT, registered_at TEXT)` – registrierte .qpat-Dateien
  (transfer-Ausgaben, export-001-Presets, Device-Readbacks).
- `conversions(id INTEGER PRIMARY KEY, sound_location TEXT, qpat_path TEXT,
  created_at TEXT, mapped INTEGER, unmapped_json TEXT)` – Historie: welcher
  Blofeld-Sound wurde wann in welche .qpat konvertiert, inkl. unmapped-Liste.
- `ab_runs(id INTEGER PRIMARY KEY, label TEXT, sound_location TEXT NULL,
  note INTEGER, dur REAL, ts TEXT, report_path TEXT, blofeld_npy TEXT,
  iridium_npy TEXT, report_json TEXT)` – A/B-Messungen; `sound_location` verknüpft
  den Run mit einem Sound (Entscheidung Benutzer 2026-11-08).

### Subcommands (Phase 1, nicht-interaktiv)

```
bloridium status                                  # Ports, Identity, Sound-Check (ex step1)
bloridium bank read A [--only A043,A044]          # SNDR aller Locations der Bank(en) → dumps/banks/A/*.bin + DB-Upsert
bloridium bank import <dir>                       # OFFLINE: vorhandene SNDD-.bin/.hex aus dir parsen → DB-Upsert
                                                  # + stabile Kopien unter dumps/banks/<Bank>/<LOC>.bin
bloridium bank list [BANK] [--grep PAT] [--json] # Tabelle aus DB: Location, Name, Kategorie
bloridium bank show A043                          # geparste Parameter (wie step2_parse)
bloridium convert A043 [--dump FILE.bin] [--out DIR] [--template FILE.qpat]
                                                  # SNDD (live oder Datei) → transfer/<name>_<loc>.qpat
                                                  # + conversions-Row; printed unmapped-Report
bloridium ab --note 36 --dur 3 --label shpower [--sound A043]
                                                  # A/B-Messung (ex step4) + ab_runs-Row + Report
bloridium ab list [--sound A043] [--json]         # letzte Runs, optional pro Sound gefiltert
bloridium ab diff ID1 ID2                         # Band-Deltas zweier Runs nebeneinander
bloridium qpat info FILE.qpat [--register]        # parsen, anzeigen, Roundtrip-Check; optional in qpats registrieren
bloridium edit FILE.qpat --list [--grep PAT]      # Parameter-Tabelle (Name, value, display)
bloridium edit FILE.qpat --show Key
bloridium edit FILE.qpat --set Key=0.5 [--display "…"] [--save OUT.qpat]
                                                  # ohne --save: in-place, legt vorher FILE.qpat.bak an
bloridium edit FILE.qpat --diff OTHER.qpat        # Parameter-Diff zweier .qpat
```

- `edit` akzeptiert beliebige `.qpat` – auch die 41 Presets aus
  `dumps/export-001/` als Referenz. Werte: float 0..1 (qpat-Normierung) oder
  `--set Key=display:Wert`; Display-Strings bleiben beim Rebuild erhalten.
- `convert` liest live per SysEx (Blofeld muss hängen) oder offline per
  `--dump`; schreibt nach `transfer/` (überschreibbar mit `--out`).
- `ab` macht vor der Messung All Notes Off auf allen Kanälen beider Synths und
  gibt die Import-Anleitung fürs Iridium aus (USB-Stick, Load>Actions>Import).

### Ausgabe & Fehler

- Plain-Text-Tabellen (keine Farb-Abhängigkeit), `--json` für list/show/convert/
  ab list. Exit-Codes: 0 ok, 1 Fehler, 2 Hardware nicht erreichbar (klare Meldung
  mit verfügbaren MIDI-Ports).

### Tests

- Offline-Unit-Tests ohne Hardware: qpat-Roundtrip gegen alle 41 Dateien in
  `dumps/export-001/`, DB-Schema/CRUD, CLI-Smoke-Tests (argparse + monkeypatchte
  `midi`/`audio`) für `bank list`, `convert --dump`, `edit --set/--save`,
  `qpat info`, `ab diff`. Kein Live-MIDI in Tests.

## Builder-Check – Festlegungen (2026-11-08)

Builder-Check per Subagent; Fragen sortiert. Folgende Punkte sind eigene
Festlegungen (vom Builder entscheidbar), im Dokument verankert:

- **Fehlersemantik `bank read`:** pro Sound Timeout 4 s, 2 Retries; bei Fehler
  weiterlesen und am Ende gesammelt melden; **inkrementelles Upsert** pro
  empfangener SNDD (Read ist re-runnable, partial reads sind kein Gift); Modus
  (Single/Multi) wird nur **gewarnt**, nie geändert (Geräteregeln). Exit 0,
  wenn ≥1 Sound gelesen, sonst Exit 2.
- **`edit --set` Werte:** Phase 1 nur float (`--set Key=0.5`) plus optionales
  `--display "text"` (Display-String, Float bleibt). Eine `display:`-Auswertung
  gegen Enum-Tabellen gibt es **nicht** (Enum-Tabellen in `qpat_map.py` sind
  unvollständig; deren Ausbau bleibt dem Mapping-Arbeitsstrang vorbehalten).
- **Wrapper-Kompatibilität:** `scripts/step*.py` behalten argv, Exit-Codes **und**
  stdout-Format bei (README/STATUS-Copy-paste-Workflows hängen daran).
- **`status`:** Default MIDI-only (Ports + Identity), `--audio` schaltet die
  komplette step1-Pegelmessung (ffmpeg/Scarlett) dazu; ohne ffmpeg graceful
  Degradierung. Exit 2 nur, wenn ein angefragter Synth nicht erreichbar.
- **Bank-/Location-Bereich:** keine künstliche A–D-Grenze; die CLI akzeptiert,
  was der Parser kann (A–Z, siehe step2-Parser). `bank read` bekommt explizite
  Bank-Buchstaben.

Entscheidungen des Benutzers (2026-11-08) zu den offenen Builder-Check-Fragen:

- **Q1 Offline-Ingest:** eigenes Kommando `bank import <dir>` (siehe Subcommands);
  stabile Dateiablage pro Location unter `dumps/banks/<Bank>/<LOC>.bin`
  (neuester Stand überschreibt die Kopie; die timestamped Original-Dumps in
  `dumps/` bleiben unangetastet).
- **Q3 `edit --set` ohne `--save`:** in-place, legt vorher automatisch
  `FILE.qpat.bak` an. `--save OUT.qpat` schreibt stattdessen nach OUT.
- **Q6 ab ↔ Sound:** `ab_runs.sound_location` (nullable) + `ab --sound A043` +
  `ab list --sound A043`.

## What's left to the builder

- Exakte Tabellenformatierung und JSON-Shapes.
- Reihenfolge der Refactor-Schritte (Library-Funktionen zuerst, Wrapper danach).
- Ob `pyproject.toml` neu angelegt wird oder bestehendes Packaging genutzt wird
  (Repo hat aktuell keins) – Vorschlag: neu, minimal, `pip install -e .`.
- Phase 2 (interaktives TUI) wird separat designed, sobald Phase 1 steht.
