# STATUS – Bloridium (Übergabe für neue Session; ersetzt HANDOVER.md)

Stand: 2026-11-08. Alles unten ist empirisch verifiziert am echten Setup (Mac + Scarlett 18i8 + Blofeld + Iridium Keyboard OS4/SOM2), außer explizit als "offen" markiert.

## 1. Ziel
Synth-Programme **Blofeld → Iridium** übertragen: Dumps lesen, Parameterstrukturen vergleichen, Mapping aufstellen, Sound übertragen, Klang per Audio messen (Scarlett In3/4 vs In5/6) und per Detailkorrektur angleichen.

## 2. Hardware & Verkabelung (verifiziert)
- **Blofeld** (FW 1.24, SL-Lizenz): USB → CoreMIDI-Port `Blofeld`, **Kanal 5**, **SINGLE MODE aktiv** (nur ch5 antwortet; Modus nur am Gerät via Shift+Sound/Multi änderbar). Audio → Scarlett **In 3/4** (c2/c3), Peak ~ -17 dBFS.
- **Iridium Keyboard** (OS 4, SOM2): USB → Endpunkte `Iridium Keyboard (MIDI 2.0) MIDI 2.0` (primär; MIDI-1.0-Bytes werden als UMP zugestellt) und `... Synth` (empfängt nichts). Parts 1-4 auf **Kanal 6-9**. Audio → Scarlett **In 5/6** (c4/c5), Peak ~ -27 dBFS. Aktuelles Preset nach Neustart: **0039 „Stepping Out" (Split!)** – ch6 note36 ≈ -26 dBFS, note60 ≈ stumm (Split um C4), ch7 note60 ≈ -36.
- **Scarlett 18i8**: 20 Eingänge @ 48 kHz via ffmpeg/AVFoundation (`bloridium/audio.py`).
- Launchpad Pro 3 nur Fallback (DIN-Kette, derzeit abgeschaltet).
- **Wichtig**: Vor Kanal-Scans All Notes Off (CC123) auf allen Kanälen + Release abwarten. Nie Hardware-Einstellungen am Gerät ohne Rückfrage ändern.

## 3. Geräte-Verhalten – Kernaussagen (alle belegt in docs/FINDINGS.md + docs/sources/)
- **Blofeld**: volle SysEx-Unterstützung über USB. `F0 3E 13 00 <cmd> …` — SNDR(0x00)→SNDD(0x10), SNDP(0x20) Parameter-Change per Index 0..382, GLBR(0x04)→GLBD. Offizielle Spec: `docs/manuals/Blofeld_sysex_v1_04.pdf`. SNDD = `F0 3E 13 DEV 10 BB NN <SDATA 383B> CHK F7`, CHK = sum(SDATA)&0x7F. Location BB NN: `00 00..` = A001.., `7F 00` = Edit-Puffer (enthält ggf. NICHT den gewählten Sound! z. B. Edit-Puffer = „JP Wannabe" während A043 „SH Power" gewählt war → immer mit Location anfragen, z. B. A043 = `00 2A`).
- **Iridium**: **KEINE SysEx-Schicht** (kein Reply auf gar nichts – bytestream/UMP sysex7+8, beide Endpunkte, Model/Device-Sweeps; belegt durch rolfw-Zitat 2019 + Foren + Changelogs, Dossier `docs/sources/rolfw_no_sysex_dossier.md`). Patch-Transfer nur **dateibasiert als .qpat** via USB-Stick/SD (Load>Actions>Import/Export). **Kein USB-Drive-Modus am Computer** (rolfw-Idee nie umgesetzt; Mac sieht nur MIDI-Endpunkte).
- **Iridium MIDI**: Kanal-MIDI (Note/CC/PC) geht. PC lädt nur Favorites. CC-Liste: 115 CCs (CC2-116), `docs/midi-maps/iridium_midi_guide.csv`. **CC7 = Output/Main Level (0 = stumm!)** – nicht in CSV gelistet. Eingehende NRPN werden ignoriert. F1-Cutoff hat keinen CC; Mod-Matrix/Filter-Typ/Coarse-Pitch ebenso nicht → qpat-Weg bevorzugen.
- **.qpat-Format** (vollständig entschlüsselt, verifiziert gegen offizielle Waldorf-Files + autosamplerT): 512-B-Header (magic `b4 ec 33 00` = u32 3402932, u32 version, name/creator/desc + 4×category je char[32], u16 param-count, 16× Resource-Header à 12 B, 2nd-Layer u16+u16+u32, u8 instrument, pad 0x200), dann **68-B-Records**: `float32 LE value (0..1 normiert) | char[32] name | char[32] display`, danach Sample-Maps (tab-getrennt). Parser+Writer: `bloridium/qpat.py` (Roundtrip-getestet). Enum-Tabellen (OscType, WF-Shape, Filter, FX …) + 2168 Key-Namen: `bloridium/qpat_map.py` + `docs/refs/qpat/`.

## 4. Werkzeuge

### Library `bloridium/`
- `midi.py` – `connect("blofeld"|"iridium")`, `Synth` (note_on/off, control_change, program_change, pitchwheel, send_sysex, device_inquiry, receive), Ports/Kanäle vorkonfiguriert (`DEFAULT_PORTS`), Fallbacks.
- `audio.py` – `record(duration, channels)` (channels=None → alle 20, Form (20,samples)), `record_wav`, `measure` (rms/peak dBFS), `play_and_measure`, `CHANNELS = {blofeld:(2,3), iridium:(4,5)}`, `SAMPLERATE=48000`.
- `waldorf.py` – SysEx-Primitive `build_sysex/parse_sysex/identity_reply_info` (Blofeld ID 0x13).
- `blofeld_dump.py` – **Blofeld SNDD/SNDP laut Spec**: SDATA-Tabelle 0..382 + Wertetabellen 4.1-4.18/FX 5.x, `checksum`, `parse_sndd` (→ name, params mit Labels), `build_sndd`, `build_sndp`, `build_sndr(bb,nn)`.
- `qpat.py` – **.qpat Parser+Writer**: `parse_qpat(data)/load(path)` → name/creator/categories/params{name:(value,display)}; `build_qpat(name, params, …)`.
- `qpat_map.py` – **Blofeld-SNDD → qpat-Keys**: `blofeld_to_qpat_params(parsed) -> (overrides, unmapped)`, Enum-Tabellen, `apply_to_template(template, overrides, name)`.
- `mapping.py` – CC-Weg: `blofeld_to_iridium(parsed) -> (msgs, unmapped)`, `load_iridium_cc()` (CSV → name→CC). Achtung CC7=Output Level.
- `midi2.py` – UMP-Helfer + `UMPOut` via `tools/ump_send` (CoreMIDI-Endpunktnamen OHNE Präfix: `MIDI 2.0`, `Synth`!).

### Scripts `scripts/`
- `step1_verify_connection.py` – Verbindung + Sound messen (Blofeld ch5, Iridium ch6).
- `check_blofeld_mode.py`, `scan_ports.py`, `scan_channels.py`, `monitor_live.py` – Diagnose.
- `step2_read_blofeld_dump.py [A043|edit]` – SNDD lesen → `dumps/blofeld_sndd_<loc>_<ts>.bin/.hex`.
- `step2_parse_blofeld_dump.py [file]` – Dump dekodieren (Parameterliste).
- `step2_probe_iridium_sysex*.py`, `step2_probe_iridium_devsweep.py`, `step2_probe_iridium_ump_min.py` – Iridium-SysEx-Probes (alle negativ; Doku warum in FINDINGS).
- `step3_transfer_qpat.py [A043]` – **Blofeld-SNDD → `transfer/<name>.qpat`** (Template `docs/refs/qpat/template_waveform.qpat` + Mapping).
- `step3_transfer_sound.py [A043] [--note 36]` – CC-Weg (approximativ; CC7-Falle beachten).
- `step4_measure_ab.py [--note 36] [--dur 3] [--label X]` – **A/B-Messung**: Note auf beiden Synths, alle 20 Kanäle aufnehmen, Blofeld In3/4 vs Iridium In5/6: peak/rms/centroid + 8 Log-Bänder (dB-Delta) + JSON-Report → `recordings/`.

### Tools
- `tools/ump_send(.m)` – rohe UMP-Pakete an CoreMIDI-Endpunkt (Endpunktnamen: `MIDI 2.0`, `Synth`).

## 5. Daten / Artefakte
- `dumps/` – Blofeld-SNDDs (u. a. `blofeld_sndd_A043_*.bin` = „SH Power").
- `transfer/SH Power_A043.qpat` – **fertiger Transfer** (80 qpat-Parameter gemappt) zum Import am Iridium.
- `recordings/` – A/B-Aufnahmen (.npy) + Reports (.json).
- `docs/FINDINGS.md` – **alle empirischen Funde** (verbindlich lesen!).
- `docs/MAPPING.md` – CC-Mapping-Entwurf Blofeld→Iridium.
- `docs/manuals/` – `Blofeld_sysex_v1_04.pdf` (+txt) offiziell; Handbücher lokal in `~/Nextcloud/AAA Musik/Manuals` (Blofeld.pdf, iridium_desk_kb_manual_os3.pdf, Iridium_os4_SOMv2_manual.pdf), extrahiert als Text in `docs/manual-text/`.
- `docs/midi-maps/` – CC-CSVs (midi.guide): blofeld, iridium.
- `docs/refs/` – offizielle Waldorf-Soundset-Zips (Quantum_Factories.zip 1.8 GB, additional_patches_IKB.zip 158 MB) + extrahierte `.qpat` (inkl. `template_waveform.qpat`).
- `docs/sources/` – rolfw-„no Sysex"-Dossier + Roh-Snippets (Gearspace-Zitate, Wayback-CDX).

## 6. Workflows (copy-paste)

```bash
cd /Users/jan/Code/Bloridium
# Blofeld-Dump lesen + parsen
python3 scripts/step2_read_blofeld_dump.py A043
python3 scripts/step2_parse_blofeld_dump.py dumps/blofeld_sndd_A043_*.bin

# Transfer-Datei fürs Iridium erzeugen
python3 scripts/step3_transfer_qpat.py A043     # -> transfer/SH Power_A043.qpat
# am Iridium: USB-Stick rein, Load>Actions>Import, Slot waehlen, laden

# A/B messen (Blofeld ch5 vs Iridium ch6, note 36 wegen Split)
python3 scripts/step4_measure_ab.py --note 36 --label shpower

# Iridium-Dump lesen: am Geraet Load>Actions>Export auf Stick -> .qpat
python3 bloridium/qpat.py /Volumes/STICK/export-xxx/iridium/....qpat
```

## 7. Plan für die neue Session (Implementation)
1. `transfer/SH Power_A043.qpat` am Iridium importieren (USB-Stick, Load>Actions>Import) → laden.
2. `step4_measure_ab.py --note 36 --label shpower` → Band-Deltas analysieren (aktuell bei Fremd-Patch: Iridium +7 dB in hohen Bändern, +8 dB 82-166 Hz).
3. Mapping-Lücken schließen in `bloridium/qpat_map.py` (unmapped-Liste von step3): Osc FM/PWM/Keytrack/BendRange, Mod-Matrix Source/Dest (Matrix*-Keys), Filter Drive/Pan/Routing, Wavetable Table/Position, Arp, LFO-Shapes. Enum-Werte aus `docs/refs/qpat/*.qpat` ableiten.
4. Detailkorrektur-Schleife: qpat-Keys feinjustieren (Werte 0..1) → neu schreiben → importieren → messen → wiederholen.
5. Iridium-Dump (Readback) verifizieren: Export am Gerät → `qpat.py` parsen → Keys mit Blofeld-SNDD vergleichen (Strukturvergleich 3 OSC / 2 Filter / Mod-Matrix).
6. Dann weitere Sounds (A-Bank) systematisch übertragen.

## 8. Offene Punkte
- Iridium-Split (Preset 0039) beachten: A/B mit note 36 auf ch6, oder am Gerät Single-Patch laden.
- CC-Weg nur als Näherung; qpat-Weg ist primär.
- Sample-basierte Patches (Particle/Resonator) brauchen Sample-Maps im qpat (Ressourcen 4-6) – noch nicht abgedeckt.
