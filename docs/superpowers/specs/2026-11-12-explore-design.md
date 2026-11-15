# Design: `bloridium explore` – OS4-Pid-Exploration am Iridium (NRPN-Mitschnitt)

Datum: 2026-11-12
Status: Entwurf zur Genehmigung

## Intent & Why

Der Benutzer will wissen, welche **OS4-Pids** der Iridium wirklich sendet, wenn man
am Panel dreht – die rdb-2023-Pids in `docs/midi-maps/iridium_os4_cc_list.csv` sind
auf OS4 **unverifiziert** (beobachtete Abweichungen: 1024/1027/1045/1046/1055,
3113 bei Sound-Wechsel; siehe HANDOVER-2026-11-09/10, Plan-Punkt 2 und Offene
Punkte). Dafür soll ein Programm sagen, **an welchem Parameter als Nächstes zu
drehen ist**, und dann **Pid + Wert per NRPN aufnehmen** und dem Parameter zuordnen.

Das ist die Datenbasis für den übernächsten Schritt: einen funktionierenden
OS4-`.mimap` und damit **den Iridium als Editor für den Blofeld**
(Blofeld-CC → Iridium-Pid, siehe `zugehoeriger_blofeld_param` in der CSV).

Entscheidung des Benutzers (2026-11-12): **Ansatz B – eine interaktive Session,
State direkt in der CSV** (siehe Approaches).

## Goals

- Neues Subcommand `bloridium explore` (interaktiv, Phase-1-CLI-Stil bleibt argparse;
  die Interaktivität ist hier bewusst und gewollt – Loop aus Prompt + Aufnahme).
- Liste der zu erkundenden Parameter: `docs/midi-maps/iridium_os4_cc_list.csv`,
  gefiltert auf `os4_verified == "nein"`, sortiert: `essential=yes` zuerst, dann
  `nutzung_pct` absteigend, dann `cc` aufsteigend. Filter: `--essential`,
  `--grep PAT`, `--only-cc 0,2,7`.
- Pro Parameter: Prompt „dreh jetzt am Panel, dann Enter“; danach NRPN-Mitschnitt
  dekodieren (Pid + 14-bit-Wert), in die CSV buchen und an
  `recordings/explore_log.jsonl` anhängen. Sofortiges Speichern nach jeder Buchung
  (crash-safe, resume-fähig: erneuter Lauf macht mit den noch offenen weiter).
- `--list` zeigt den Verifikations-Status aller 116 CCs (auch `--json`).
- Rein lesend: das Tool **sendet kein MIDI** (Iridium ignoriert eingehende NRPN
  sowieso; CC7=0-Stumm-Gefahr entfällt damit komplett).

## Non-Goals

- **Kein .mimap-Emit** in diesem Schritt (war Ansatz C, nicht gewählt): CSV + JSONL
  sind die Datenbasis; `.mimap`/Editor-Mapping wird später daraus generiert.
- Kein Senden von MIDI (kein CC-Test, kein PC), kein Audio, keine Noten.
- Keine Änderung anderer Subcommands; `scripts/monitor_live.py` bleibt unverändert
  (manueller Mitschnitt weiterhin möglich).
- Keine SQLite-DB für den Explore-State – Dateien bleiben Source of Truth
  (konsistent mit CLI-Design 2026-11-08).

## Anti-Goals

- Die bestehenden 8 CSV-Spalten (`cc,pid,iridium_param,zugehoeriger_blofeld_param,
  nutzung_pct,essential,pid_quelle,os4_verified`) bleiben **unverändert und in
  dieser Reihenfolge**; neue Spalten werden nur **anhängt** (nichts liest die CSV
  heute programmatisch, nur Menschen – geprüft 2026-11-12).
- Keine neuen Runtime-Dependencies (stdlib + mido, wie gehabt).
- Kein Live-MIDI in Tests.

## Constraints (empirisch verifiziert)

- **NRPN-Format** (Mitschnitt `recordings/midi_monitor_20261109_090256.log`,
  Iridium-USB-Ports, Kanal B5 = ch6 = Part 1): Panel-Dreh sendet
  `CC99 (0x63) = Pid-MSB`, `CC98 (0x62) = Pid-LSB`, `CC6 = Wert-MSB`,
  `CC38 (0x26) = Wert-LSB`. Beispiel `63 18 / 62 29 / 06 7F / 26 7F`
  → Pid `(0x18<<7)|0x29 = 3113`, Wert `(0x7F<<7)|0x7F = 16383` (Sound-Wechsel).
  → Dekodierung: `pid = (cc99<<7)|cc98`, `value = (cc6<<7)|cc38` (14-bit).
  `CC99/CC98 = 127` = NRPN aus (Reset); `CC121` (Reset All Controllers) resetet
  den NRPN-State; `CC101/100` (RPN) werden ignoriert.
- **Port/Kanal heute:** Iridium hängt am Launchpad-DIN
  (`midi.DEFAULT_PORTS["iridium"]["in"]` = "Launchpad Pro MK3 LPProMK3 DIN"),
  Iridium-USB ist wegen Masseschleife **ab**. NRPN kommt auf Part-1-Kanal
  ch6 (0-basiert 5). Default `--channel 5`.
- Am Iridium muss **Global > MIDI = an** sein und **Send NRPN = on**
  (OS-Handbuch: „Iridium doesn't react on incoming NRPN" – Exploration ist
  ausschließlich outgoing-lesend).
- Ein Dreh am Panel erzeugt **mehrere NRPN** (Wert-Sweep) → min/max/last buchen,
  alle Werte ins Log. Pid 3113 (Sound-Wechsel) kann auftauchen – wird ganz normal
  mitgebucht (häufigster Pid gewinnt, alle im Log).
- Umgebung: macOS (CoreMIDI), Python ≥ 3.10, mido.

## Approaches

- **A – zwei Kommandos (`explore next` / `explore capture`), State in JSON:**
  flexibler zwischen den Schritten, aber mehr Tipparbeit, State-Drift.
  *Nicht gewählt (2026-11-12).*
- **B – eine interaktive Session, State direkt in der CSV (GEWÄHLT 2026-11-12):**
  `bloridium explore` arbeitet die offenen Parameter in einem Loop ab
  (Prompt → Panel-Dreh → Enter → NRPN aufnehmen → buchen → nächster).
  CSV ist einziger State → resume-fähig, crash-safe (save nach jeder Buchung),
  menschenlesbar. *Gewählt.*
- **C – Session wie B plus direktes .mimap-Emit:** größter End-Nutzen, aber zwei
  Jobs in einem Tool. *Nicht gewählt;* Emit kommt als eigenes Kommando, sobald
  die CSV-Datenbasis steht.

## How

### Layout

- `bloridium/explore.py` – reine, hardwarefreie Logik (testbar):
  - `NrpnDecoder.feed(msg) -> NrpnEvent | None` (State-Machine über mido-Messages,
    siehe Constraints); `NrpnEvent = (pid, value14)`.
  - `NEW_COLUMNS = ["pid_os4", "nrpn_min", "nrpn_max", "nrpn_last", "explore_ts", "explore_msgs"]`
  - `load_cc_list(path) -> (fieldnames, rows)` – fehlende neue Spalten = `""`.
  - `save_cc_list(path, fieldnames, rows, backup=False)` – hängt neue Spalten an;
    `backup=True` legt einmalig pro Session `iridium_os4_cc_list.csv.bak` an.
  - `pending_rows(rows, essential, grep, only_cc) -> rows` (Filter + Sortierung).
  - `book_row(row, events, ts) -> dict` – setzt `pid_os4` (häufigster Pid =
    Gewinner), `nrpn_min/max/last` **über die Events des Gewinner-Pids**,
    `explore_msgs` = **Anzahl NRPN-Events des Gewinner-Pids** (int),
    `explore_ts`, `os4_verified="ja"`;
    `abweichung = (pid_os4 != pid)` fürs Log.
  - `append_log(log_path, entry)` – eine JSON-Zeile pro Aufnahme.
- `bloridium/cli.py` – `cmd_explore(args)`:
  - Flags: `--csv PATH` (Default `docs/midi-maps/iridium_os4_cc_list.csv`),
    `--log PATH` (Default `recordings/explore_log.jsonl`),
    `--essential`, `--grep PAT`, `--only-cc 0,2,7`, `--list`, `--json`,
    `--port NAME` (Default `midi.DEFAULT_PORTS["iridium"]["in"]`),
    `--channel N` (Default 5), `--listen S` (Default 1.5 s Stille = Fang-Ende).
  - `--list`: Tabelle `cc | iridium_param | pid(rdb) | os4_verified | pid_os4 |
    nrpn_last` (+ `--json`); kein MIDI nötig.
  - Session: MIDI-In öffnen (Exit 2 + Port-Liste, wenn nicht erreichbar) →
    pending berechnen → Loop:
    1. Fortschritt `[verifiziert X/116]` + nächster Parameter ausgeben:
       `CC{cc}  {iridium_param}` / `erwartet rdb-Pid {pid}` /
       `Blofeld-Pendant: {zugehoeriger_blofeld_param} ({nutzung_pct}%, essential={essential})`.
    2. Input-Buffer leeren, Prompt: `Dreh jetzt am Panel, dann Enter  [s=weiter ohne Buchung, q=quit]`.
       `q`/EOF/Ctrl+C → sauber beenden (State ist bereits gebucht), Exit 0.
       `s` → nächster Parameter, ohne State-Änderung.
    3. Enter → Fang: `Synth.receive()`-Schleife, bis `--listen` s keine neue
       Nachricht; Decoder füttern, CCs werden mitgezählt/geloggt (falls .mimap
       geladen und Panel zusätzlich CC sendet).
    4. Events leer → **bleibt beim selben Parameter** (nochmal Enter = nochmal
       aufnehmen; `s`/`q` wie gehabt), aber mit differenzierter Diagnose:
       - gar keine MIDI-Nachricht auf dem Port empfangen → Hint: „Global > MIDI
         = an? Send NRPN = on? Iridium-USB kurz anstecken und `--port` setzen
         (DIN liefert evtl. kein Panel-NRPN – siehe Builder-Check Q1)?“
       - Nachrichten empfangen, aber kein NRPN darunter → Hint: „Send NRPN = on?
         richtiger Part/Kanal (default ch6 = Part 1)?“
       - NRPN nur auf **anderem Kanal** gesehen → Hint mit dem beobachteten
         Kanal („NRPN kam auf ch{N} – `--channel {N-1}`?“).
       Nachrichten auf anderen Kanälen werden weder dekodiert noch gebucht
       (der DIN-Port trägt sonst auch den Blofeld auf ch5).
    5. Events vorhanden → `book_row`, `append_log` (ts, cc, iridium_param,
       pid_rdb, pid_os4, abweichung, nrpn_min/max/last, n_msgs, werte, cc_gesehen,
       port, channel), CSV speichern (mit einmaligem `.bak` zu Sessionbeginn),
       Ergebnis drucken: `Pid {pid_os4}` + **`ABWEICHUNG zu rdb-Pid {pid}`**
       bei Abweichung + `Werte {min}..{max} (last {last}), {n} NRPNs`.
    6. nächster Parameter; Liste leer → „alle erfassten Parameter verifiziert“, Exit 0.
  - Exit-Codes konsistent mit CLI-Design: 0 ok, 1 Fehler, 2 Hardware nicht erreichbar.

### Beispiel-Session (Ausgabe-Skizze)

```
bloridium explore --essential
[0/116 verifiziert]  nächster: CC0  Filter1 Cutoff
  erwartet rdb-Pid 966  |  Blofeld-Pendant: Filter 1 Cutoff (93.8%, essential)
Dreh jetzt am Panel, dann Enter  [s=weiter, q=quit]
> <Enter>
  NRPN: Pid 1024  *** ABWEICHUNG zu rdb-Pid 966 ***  Werte 0..16383 (last 8712), 14 NRPNs
  gebucht: iridium_os4_cc_list.csv (os4_verified=ja, pid_os4=1024) + recordings/explore_log.jsonl
[1/116 verifiziert]  nächster: CC2  Filter1 Reso ...
```

### Tests (`tests/test_explore.py`, offline, kein Live-MIDI)

- NRPN-Decoder gegen Mitschnitt aus `recordings/midi_monitor_20261109_090256.log`
  (`63 18/62 29/06 7F/26 7F` → Pid 3113, Wert 16383), Mehrfach-Werte, Reset-Fälle
  (CC99/98=127, CC121), RPN-CCs ignoriert.
- CSV load/save roundtrip auf `tmp_path`: Spalten-Append, `.bak`,
  `pending_rows` (Filter essential/grep/only-cc, Sortierung nutzung_pct).
- `book_row` + `append_log` (JSONL eine Zeile, abweichung-Flag).
- CLI-Smoke mit monkeypatchtem `midi.connect` (Fake-Synth mit `receive()`-Queue)
  und monkeypatchtem `input` (`["", "q"]`): Session bucht in tmp-CSV, hängt Log an,
  druckt ABWEICHUNG; `--list` (Text + `--json`); kein In-Port → Exit 2.

## Builder-Check (Subagent 2026-11-12)

Fragen des Builders, sortiert:

- **Q1 (an den Benutzer – Hardware-Tatsache):** Liefert das **Launchpad-DIN**
  wirklich Panel-NRPN, oder kam der NRPN-Mitschnitt nur über die Iridium-**USB**-Ports
  (USB war am 2026-11-09 kurz an; aktuell ist es wegen Masseschleife ab)?
  Default bleibt DIN mit `--port`-Override; leerer erster Fang bekommt einen
  gezielten USB-Hinweis (siehe How, Schritt 4). Antwort des Benutzers folgt vor
  Genehmigung.
- **Q2 (Festlegung, Builder entscheidbar):** Kanal strikt filtern (default ch6 /
  0-basiert 5 = Part 1, `--channel` override); Prompt-Hinweis „Part 1 am Iridium
  aktiv?“. Verankert in How.
- **Q3 (Festlegung):** `explore_msgs` = Anzahl NRPN-Events des Gewinner-Pids (int).
  Verankert in How.
- **Q4 (Festlegung):** leere Fänge dreistufig diagnostizieren (nichts empfangen /
  nur CC / NRPN auf anderem Kanal) mit gezielten Hints. Verankert in How, Schritt 4.
- **Q5 (Festlegung):** `nrpn_min/max/last` nur über Gewinner-Pid-Events; alle Events
  (alle Pids) ins JSONL-Log. Verankert in How.

## What's left to the builder

- Exakte Prompt-/Tabellen-Texte (Plain Text, keine Farben – konsistent mit CLI).
- Fang-Loop: `Synth.receive(timeout=...)` aus `midi.py` wiederverwenden.
- Mehrere unterschiedliche Pids in einem Fang: häufigster gewinnt, alle ins Log.
- Ob `--listen` auch als „max. Gesamtdauer des Fangs“ dienen soll (Vorschlag: nur
  Stille-Ende, Gesamtdauer = unbegrenzt bis Enter-Stille).
