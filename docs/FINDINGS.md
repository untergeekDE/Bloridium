# Findings – Verbindungsaufbau & Messungen (dokumentiert)

Alle Angaben empirisch verifiziert am Mac (macOS, CoreMIDI + AVFoundation).

## Sichtbare MIDI-Ports (CoreMIDI/rtmidi)

```
OUT/IN: Launchpad Pro MK3 LPProMK3 MIDI
OUT/IN: Launchpad Pro MK3 LPProMK3 DIN
OUT/IN: Launchpad Pro MK3 LPProMK3 DAW
OUT/IN: Scarlett 18i8 USB
OUT/IN: Blofeld                              <- Blofeld per USB (neu)
OUT/IN: Iridium Keyboard (MIDI 2.0) Synth
OUT/IN: Iridium Keyboard (MIDI 2.0) MIDI 2.0
```

## MIDI-Mapping (verifiziert)

| Synth | Port | Kanal (1-basiert) | Richtung | Identity |
|---|---|---|---|---|
| Blofeld | `Blofeld` (USB) | **5** (Single Mode, Global Channel) | bidirektional | `F0 7E .. 06 02 3E 13 00 00 00 "1.24" F7` (Waldorf=3E, Blofeld=13, FW 1.24) |
| Blofeld (Fallback) | `Launchpad Pro MK3 LPProMK3 DIN` | 5 | Out only (In liefert nur Launchpad-eigenes Reply `00 20 29`) | – |
| Iridium | `Iridium Keyboard (MIDI 2.0) MIDI 2.0` | **6-9** (Parts 1-4) | Out (Keyboard sendet ch6) + In funktioniert | kein Identity-Reply bisher |
| Iridium | `Iridium Keyboard (MIDI 2.0) Synth` | – | empfängt nichts (Display zeigt keine MIDI-In-Reaktion) | – |

Wichtig: Am Iridium-Endpunkt `MIDI 2.0` werden MIDI-1.0-Bytes von CoreMIDI
automatisch als UMP (mt=2) zugestellt – plain mido-Messages funktionieren dort.
Nach Umschalten der SOM2-USB-Ports ("Computer"/"USB CTRL") bzw. Replug/Reboot
war der Empfang am `MIDI 2.0`-Endpunkt aktiv.

## Audio-Mapping (Scarlett 18i8, 20 Kanäle @ 48 kHz, AVFoundation)

| Synth | Scarlett-Eingänge | 0-basierte Kanäle im Stream |
|---|---|---|
| Blofeld | **3/4** | c2/c3 |
| Iridium | **5/6** | c4/c5 |

Verifiziert per Tastendruck am Iridium (Audio erschien auf In5/6, ca. -22 dBFS)
und per MIDI-Note (Blofeld->In3/4 ca. -17 dBFS, Iridium->In5/6 ca. -27 dBFS).

## Blofeld: Multi- vs Single Mode

- **Kanal-Scan ist KEIN zuverlässiger Mode-Indikator**: Im Multi Mode dürfen
  alle 16 Parts auf *beliebigen* Kanälen liegen (bei uns z. B. nur Kanal 5
  belegt – trotzdem war der Multi Mode an). Nur "alle 16 Kanäle antworten"
  wäre ein sicheres Multi-Kriterium; ein einzelner Kanal beweist nichts.
- Stand: Blofeld war im **MULTI MODE** (laut User) und wurde auf **SINGLE MODE**
  umgeschaltet (Shift+Sound/Multi). Verifiziert: danach antwortet nur noch
  Kanal 5. Für den Programm-Transfer Single Mode verwenden.
- Global Channel = Kanal 5 (im Single Mode antwortet nur dieser).
- Release-Reste täuschen beim Scan (scheinbar Kanäle 2/3/5): vorher CC123 +
  CC120 auf allen Kanälen und ~4 s warten, dann Baseline.
- `scripts/check_blofeld_mode.py` zeigt Kanaele/Identity/GLBD und den Hinweis.

## Blofeld-SysEx (über USB-Port `Blofeld`, funktioniert)

Format `F0 3E 13 <dev> <cmd> [data] F7` (Checksum bei Requests weglassen):

| Request | Cmd | Reply | Inhalt |
|---|---|---|---|
| `F0 3E 13 00 04 F7` (GLBR) | 0x04 | GLBD (0x14), ~74 Datenbytes | Global-Parameter-Dump |
| `F0 3E 13 00 00 F7` (SNDR) | 0x00 | SNDD (0x10), ~386 Bytes | aktueller Sound (Edit-Puffer) |
| `F0 3E 13 00 01 F7` (MULR) | 0x01 | MULD (0x11), ~419 Bytes | aktuelles Multi (enthält z.B. "String Ch5") |

Helfer: `bloridium/waldorf.py` (`build_sysex`, `parse_sysex`, `identity_reply_info`).

## Technische Stolperfallen (gelöst)

- ffmpeg `pan`-Filter kennt keine Layouts > 8 Kanäle -> bei >= 16 Kanälen
  roh aufnehmen und in numpy slicen (`bloridium/audio.py`).
- AVFoundation gibt das Scarlett manchmal nicht sofort frei -> Retry mit
  1 s Pause in `audio.record`.
- python-rtmidi `send_message` lehnt Pakete > 3 Bytes ab (nur SysEx) ->
  für echtes UMP das kompilierte Tool `tools/ump_send` nutzen
  (`clang -framework CoreMIDI -framework Foundation -o ump_send ump_send.m`).
- Direkter `MIDISend`-Aufruf via ctypes stellte keine Pakete zu ->
  `bloridium/midi2.py` nutzt daher `tools/ump_send`.
- Identity-Reply auf dem Launchpad-DIN-Port (`00 20 29`) kommt vom
  **Launchpad selbst**, nicht vom Blofeld.
- Störsignale auf In11/12 (ca. -5 dBFS) waren hängengebliebene Noten;
  per CC123 auf allen Kanälen beseitigt.

## Runde 2: SysEx-Mapping (Stand: in Arbeit)

### Blofeld-SysEx – vollständig dokumentiert & ausgelesen
- Offizielle Spec heruntergeladen: `docs/manuals/Blofeld_sysex_v1_04.pdf`
  (Nextcloud-Share `ybExJgT4TzqT8ir`, "Blofeld sysex 1.04" im Blofeld-FAQ-Bereich).
- SNDD-Format: `F0 3E 13 DEV 10 BB NN <SDATA 383 B> CHK F7`; CHK = Summe(SDATA) & 0x7F
  (Status/IDs zählen NICHT mit). SNDP (0x20) = einzelner Parameter per Index 0..382.
- SDATA-Kompletttabelle (Spec 3.1, Indizes 0..382) in `bloridium/blofeld_dump.py`
  umgesetzt (inkl. Wertetabellen 4.1–4.18, FX 5.x).
- `scripts/step2_read_blofeld_dump.py [A043|edit]` liest SNDD und speichert nach
  `dumps/blofeld_sndd_<loc>_<ts>.bin/.hex`. Verifiziert: 392 B gesamt, CHK ok.
  - Default (kein Arg) = Edit-Puffer (BB=7F): lieferte **„JP Wannabe"** – der Puffer
    hält den zuletzt *editierten* Sound, nicht den gewählten!
  - Location-basiert (SNDR mit BB NN, z.B. `A043` = `00 2A`): **„SH Power"**
    (A043 lt. User; Osc1=Saw, Osc2=Pulse, Osc3=off, F1=LP24dB Cutoff 52 Reso 51,
    Cat=Bass, Mod1: LFO2*Press→Pitch Amt 84).
- `scripts/step2_parse_blofeld_dump.py` dekodiert den Dump (290 benannte Parameter,
  z.B. Osc1/2 Shape=Saw, F1=LP12dB Cutoff 67 Reso 38, Mod1: LFO1*MW→Pitch Amt 82).

### Iridium – Stand SysEx
- **Kein SysEx-Reply auf beiden USB-Endpunkten** (`MIDI 2.0` und `Synth`):
  weder Universal Device Inquiry noch Waldorf-Style-Sweep `F0 3E <model 0x00..0x1F> 00 <cmd 0x00/0x01/0x04> F7`
  (siehe `scripts/step2_probe_iridium_sysex.py`) – 0 Antworten.
- Kanalstimme (Notes) und CC werden auf `MIDI 2.0` empfangen (verifiziert per Audio).
- CC-Empfang getestet: CC7=0 auf Kanälen 6–9 senkt Peak um ca. -4,6 dBFS;
  einzelne OSC-VOL-CCs (33/47/61) zeigen nur geringe Peak-Deltas (Layer-/Kanal-Zuordnung
  prüfen; CC7 wirkt kanalweit).
- Iridium-CC-Tabelle (115 CCs, CC 2..116): `docs/midi-maps/iridium_midi_guide.csv`
  (midi.guide / pencilresearch/midi GitHub). Achtung: Filter1 Cutoff hat dort KEINEN CC;
  eingehende NRPN werden laut OS3-Handbuch ignoriert.
- Erste Mapping-Tabelle (Blofeld SNDD → Iridium CC): `docs/MAPPING.md`.
- Iridium-Handbücher (lokal) enthalten KEINE SysEx-Byte-Doku (nur Glossar);
  OS4/SOMv2-Manual beschreibt nur neue Global-MIDI-Optionen (Layer-Kanäle pro Port).
  Offizielles „Iridium MIDI Implementation"-PDF liegt vermutlich im Login-Bereich
  (My Waldorf) bzw. als .qpat/.syx-Format – .syx-Import über Load>Actions>Import
  ist dokumentiert (Waldorf-FAQ).
- **Iridium antwortet auf KEIN SysEx** – getestet: bytestream + natives UMP
  (SysEx7 mt=3 UND SysEx8 mt=5), beide Endpunkte (`MIDI 2.0`, `Synth`),
  Model-Sweep 0x00–0x3F, Device-ID-Sweep 0x00–0x7E, cmds 0x00/0x01/0x04/0x30,
  mit/ohne Location – 0 Antworten. Aber: Kanal-MIDI TX/RX funktioniert
  (nach Program Change sendet der Iridium CC123-All-Notes-Off-Bursts auf ch6-8;
  CC7=0 auf ch6-9 senkt Peak um -4,6 dBFS). => Dump-Lese-Richtung vermutlich nur
  als Datei-Export (Load>Actions>Export -> SD/USB als .qpat) oder evtl. DIN.
- **.qpat-Format reverse-engineered** (offizielle Soundsets von waldorfmusic.com,
  `docs/refs/*.zip`: Quantum_Factories.zip 1186 qpat, additional_patches_IKB.zip
  453 qpat): magic `b4 ec 33 00`, uint32 Version, name/author/bank/category/attrs
  je char[32], dann Key-Value-Records ab ~0x200 (Typ-Byte `?@B>=<` + Key,
  Value-Feld ~34 B ab key+33; numerisch = float LE, sonst String). Parser:
  `bloridium/qpat.py`. Vollständiger Iridium-Parameter-Namensraum extrahiert
  (Osc1Type/Osc1Vol/Filter1CutOff/Filter1Reso/Filter12Type/AmpEnv*/Filter1Env*/
  FreeEnv1-3*/MatrixAmount1-40/FX1Type/... – 645 Params in einem Patch).
  Samples dazu: `docs/refs/qpat/*.qpat`.
- **Recherche-Ergebnis (Subagent, ses_e44a06781ffeZV5NgA6lrz4Uzc): Iridium/Quantum
  haben KEINE SysEx-Anwendungsschicht** – kein Dump-Request, keine SysEx-Antwort,
  auch nicht ueber DIN (OS 3.3+ UMP = reiner Transport, kein SysEx-Handler;
  Gearspace: „there is no sysex layer in quantum/iridium"). Patch-Transfer nur
  dateibasiert: `Load>Actions>Export/Import` -> SD/USB als **.qpat**. Waldorf-SysEx
  existiert nur fuer Legacy + M (Model-ID 0x30); Blofeld = 0x13.
  .qpat-Spec (verifiziert gegen offizielle Waldorf-Files + autosamplerT-Code):
  `b4 ec 33 00` magic, u32 version, name/author/desc + 4x category je char[32],
  param-count u16, 16 Resource-Header a 12 B (type/offset/len), pad auf 0x200,
  dann 68-B-Records: `float32 LE value | char[32] name (mit Typ-Praefix @/?/B...) |
  char[32] display`, danach Sample-Maps (tab-getrennt). Writer-Referenz:
  github.com/timandtheocean/autosamplerT `src/export/export_qpat.py`.
  => **Iridium-"Dump" = .qpat-Datei** (am Geraet Load>Actions>Export auf USB/SD,
  dann am Mac parsen mit bloridium/qpat.py). Umgekehrt koennen wir .qpat selbst
  schreiben (Blofeld-SNDD -> qpat-Keys) und am Geraet importieren.
  Artefakte des Subagenten: /private/var/folders/kg/zkn9b6n546vfmpb6qd3n4pdr0000gn/T/iridium-research/.
- **Iridium erscheint NICHT als USB-Drive am Mac** (geprueft 2026-11-08: diskutil/
  system_profiler zeigen kein zusaetzliches Laufwerk, nur MIDI-Endpunkte). rolfw's
  Idee von 2019 („sample storage appears as an external drive on your computer") kam
  fuer Quantum/Iridium nie (Paul_xyz 2023: nur filebasiert). Gearspace Iridium S.112:
  USB-Host erkennt „Only MIDI and storage devices". „Internal Flash als Drive" = nur
  im Geraete-eigenen Browser (Kopie Stick<->Flash am Geraet). => Datei-Austausch nur
  per USB-Stick/SD im Host-Port/Slot.
- **Vorfall geloest: Iridium verstummt bei CC7=0** – CC7 ist am Iridium der
  **Output/Main Level** (nicht in midi.guide-CSV gelistet); 0 = stumm. Nach CC7=0
  kein Ton auf In5/6 (ueberlebt Patch-Wechsel; MIDI-Eingang lebt: PC -> CC123).
  Fix: CC7 hochsetzen (User am Geraet bestaetigt). mapping.py mappt jetzt
  Blofeld "Amplifier Volume" -> CC7. Neustart nicht noetig, nur CC7>0.
- Nach Neustart (Preset 0039 "Stepping Out" = SPLIT): ch6 note36 = -26 dBFS,
  note60 = -59 (Split um C4); ch7 note60 = -36 dBFS. => Fuer A/B tiefere Note
  nutzen (36) oder alle Part-Kanaele 6-9 beschreiben.
