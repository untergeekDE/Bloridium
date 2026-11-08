# Bloridium CLI – Referenz (Phase 1)

Kommando: `bloridium` (nach `pip install -e .`) bzw. `python3 -m bloridium`.
Globale Flags: `--db PATH` (Default: `$BLORIDIUM_DB` oder `<repo>/bloridium.db`),
`--json` (JSON-Ausgabe, wo unterstützt).

Exit-Codes: **0** ok · **1** Fehler (z. B. Location nicht in Bank) · **2** Hardware
nicht erreichbar (Meldung mit verfügbaren MIDI-Ports auf stderr).

## status
```
bloridium status [--audio]
```
Listet MIDI-Ports; pro Synth (Blofeld, Iridium): Verbindung, Kanal, Identity-Reply.
`--audio` zusätzlich: spielt C4 und misst den Pegel am Scarlett (ex step1).

## bank – Blofeld-Bank-Manager
```
bloridium bank read A [B ...] [--only A043,A044] [--banks-dir DIR]
bloridium bank import DIR [--banks-dir DIR]      # offline aus blofeld_sndd_*.bin/.hex
bloridium bank list [BANK] [--grep PAT] [--json]
bloridium bank show A043 [--json]
```
- `read`: liest per SysEx (SNDR/SNDD) alle 128 Locations der Bank(en); pro Sound
  stabile Kopie unter `dumps/banks/<Bank>/<LOC>.bin` + Upsert in der DB.
  Einzelfehler brechen nicht ab (Timeout 4 s, 2 Retries, Sammel-Report am Ende).
- `import`: parst vorhandene Dump-Dateien offline in die DB.
- `list`: markiert Sounds, deren `.bin`-Datei fehlt, mit `FEHLT`.
- `show`: geparste Parameter (Name, Kategorie, alle SDATA-Parameter).

## convert – Blofeld → Iridium (.qpat)
```
bloridium convert A043 [--dump FILE.bin] [--out DIR] [--template FILE.qpat]
```
Liest den Sound live (Blofeld muss hängen, Single Mode, Kanal 5) oder offline per
`--dump`; schreibt `<name>_<LOC>.qpat` (Default: `transfer/`) und trägt die
Konvertierung inkl. `unmapped`-Liste in der DB ein. Gibt danach die Import-Anleitung
fürs Iridium aus (USB-Stick/SD → Load>Actions>Import).

## ab – A/B-Klangmessung (Scarlett In3/4 vs In5/6)
```
bloridium ab [--note 36] [--dur 3.0] [--label L] [--sound A043] [--rec-dir DIR]
bloridium ab --list [--sound A043] [--json]
bloridium ab --diff ID1 ID2
```
Messung: All Notes Off (CC123) auf allen 16 Kanälen beider Synths, dann Note auf
beiden, Aufnahme aller 20 Kanäle; speichert `.npy` + `_report.json` unter
`recordings/` und den Run in der DB (mit `sound_location`). `--diff` zeigt die
8 Log-Bänder beider Runs nebeneinander.

## qpat – .qpat-Dateien
```
bloridium qpat info FILE.qpat [--register]
```
Parst die Datei, zeigt Name/Creator/Kategorien/Version/Parameter, macht einen
Roundtrip-Check (parse→build→parse, Parameter müssen identisch sein) und trägt
mit `--register` die Datei in die `qpats`-Tabelle ein (Source = Verzeichnisname,
z. B. `export-001` für die 41 Presets in `dumps/export-001/`).

## edit – Iridium-Editor (.qpat)
```
bloridium edit FILE.qpat --list [--grep PAT] [--json]
bloridium edit FILE.qpat --show KEY
bloridium edit FILE.qpat --set KEY=0.5 [--display "Text"] [--save OUT.qpat]
bloridium edit FILE.qpat --diff OTHER.qpat
```
- Werte sind qpat-normiert **0..1** (werden geclampt); `--display` setzt den
  Display-String. Ohne `--save` wird **in-place** geschrieben, vorher liegt
  automatisch `FILE.qpat.bak` an. `--save OUT` schreibt stattdessen nach OUT.
- Funktioniert mit beliebigen `.qpat` – auch den Referenz-Presets in
  `dumps/export-001/`.
- `--diff` listet nur die unterschiedlichen Parameter beider Dateien.

## Tests
```bash
pip install -e ".[dev]"
python3 -m pytest            # 75 Tests, alle offline (kein MIDI/Audio noetig)
```
