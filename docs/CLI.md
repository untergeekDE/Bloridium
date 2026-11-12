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

## cc – Live-CC am geladenen Patch (Nachstellen ohne Re-Import)
```
bloridium cc --list [--grep PAT]              # CC-Tabelle (aus docs/midi-maps/*.csv)
bloridium cc "Filter1 Reso" 100 [--part 2]    # Name -> CC aufloesen, senden (Default Part 1 = MIDI ch6)
bloridium cc --raw 9 64                       # rohe CC-Nummer
bloridium cc ... --synth blofeld              # Blofeld (Single Mode, MIDI ch5)
```
- Namen case-insensitive; eindeutiger Substring reicht, mehrdeutig → Liste + Exit 1.
- **NRPN-only-Parameter** (z. B. Iridium `Filter1 Cutoff`) haben **keinen CC** – NRPN wird
  am Iridium ignoriert → dafür qpat-Re-Import oder MIDI Learn am Gerät.
- ⚠️ **CC7 = Output Level (0 = stumm!)** – `cc --raw 7 0` wird ohne `--force` verweigert.

## explore – OS4-Pid-Exploration am Iridium (NRPN-Mitschnitt)
```
bloridium explore [--essential] [--grep PAT] [--only-cc 0,2,7]
bloridium explore --list [--json]
bloridium explore [--csv PATH] [--log PATH] [--port NAME] [--channel N] [--listen S]
```
- Interaktive Session: zeigt den nächsten offenen Parameter aus
  `docs/midi-maps/iridium_os4_cc_list.csv` (essential zuerst, dann Nutzung %),
  du drehst am Panel, Enter → NRPN dekodieren (Pid = CC99/98, Wert = CC6/38, 14-bit)
  und buchen: CSV (`os4_verified=ja`, `pid_os4`, min/max/last; einmalig `.bak`) +
  `recordings/explore_log.jsonl`. Abweichung zum rdb-Pid → **ABWEICHUNG**.
  `s` = weiter ohne Buchung, `q` = Ende (fortsetzbar – die CSV ist der State).
- **Rein lesend** – sendet kein MIDI. Am Iridium: Global > MIDI = an, Send NRPN = on,
  Part 1 aktiv (Default `--channel 5` = ch6).
- Iridium-Panel-NRPN wurde bisher nur über die **USB-Endpunkte** gesehen (ch6);
  Launchpad-DIN liefert kein Panel-NRPN (Check 2026-11-12, siehe HANDOVER) →
  bei leerem Fang Iridium-USB kurz anstecken und
  `--port "Iridium Keyboard (MIDI 2.0) MIDI 2.0"` setzen.
- `--list` zeigt den Verifikations-Status aller 116 CCs (braucht kein MIDI).

## sim – Ähnlichkeits-Score Blofeld↔Iridium (Skripte, siehe README)

- `scripts/sim_compare.py --npy A.npy B.npy` – offline aus .npy-Takes
- `scripts/sim_compare.py --live [--note 60] [--blofeld A043] [--iridium-slot 207]` – live messen
- `scripts/sim_live.py --param "Filter1 Cutoff" --value 90 [--ref ref.npy]` – CC drehen + messen
- Score 0–100 (70 % Spektrogramm-Cosine + 30 % Hüllkurven-DTW) + Band-Deltas; Log: `recordings/sim_log.jsonl`
- CC/Pid-Auflösung: `bloridium/ccmap.py` (`docs/midi-maps/iridium_pid_map.csv`)

## Tests
```bash
pip install -e ".[dev]"
python3 -m pytest            # 75 Tests, alle offline (kein MIDI/Audio noetig)
```
