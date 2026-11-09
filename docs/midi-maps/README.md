# Iridium MIDI-Maps & Pid-Tabelle

## Dateien

| Datei | Inhalt |
|---|---|
| `midimap0.mimap` | Werks-Midi-Map (2017, vom Geraet exportiert): nur CC3–CC8 belegt, Pids 2102/2103/3699/3700/2112/2113 |
| `iridium_rdb.mimap` | Fertige .mimap von @rdb (squarp.community/t/waldorf-iridium/9276, 2023-03-24): CC0, CC2–CC116 → Pid, "most useful" Auswahl (max. 119 Eintraege) |
| `iridium_hapax_L1.def.txt` | Passende Squarp-Hapax-Instrument-Definition (Layer 1, ch1); `[CC]`-Sektion loest CC → Parametername auf. Layer 2 = TRACKNAME "Iridium L2", OUTCHAN 2 |
| `iridium_pid_map.csv` | Kombiniert: `cc, pid_rdb_2023, parameter_name, pid_werks_2017_midimap0, cc_midi_guide_csv` (116 Zeilen) |
| `iridium_midi_guide.csv` | Offizielle CC-Liste (116 CCs, nrpn-Spalten leer) |

## Erkenntnisse

- **CC → Name aus rdb-Map stimmt 1:1 mit `iridium_midi_guide.csv` ueberein.**
- **CC0 → Pid 966 = Filter1 Cutoff** (rdb-Map): F1 Cutoff hat zwar keinen CC in der
  Werks-Map/CSV, ist aber per .mimap auf CC0 legbar → loest HANDOVER-Punkt "F1 Cutoff
  hat keinen CC".
- **CC7-Diskrepanz:** Werks-Map 2017: CC7→2112 (verhält sich als Output/Main Level,
  CC7=0 = stumm). rdb-Map 2023: CC7→969 = Filter1 Amount. → **Pid-Nummern sind
  firmware-abhaengig** (2017 vs 2023).
- Thread-Warnung (2024/2025): seit FW 3.2 hat sich das .mimap-Format evtl. geaendert;
  auf OS4 (unser Geraet) **ungetestet**. Vor Einsatz am Geraet verifizieren
  (z. B. CC0 senden → aendert sich Filter1 Cutoff am Display?).

## Laden am Iridium

.mimap auf SD/USB-Stick kopieren → am Geraet `Global > MIDI > Mappings > Load`.

## NRPN

Eingehende NRPN werden vom Iridium **ignoriert** (OS3-Handbuch: "Iridium doesn't react
on incoming NRPN MIDI data") — NRPN nur outgoing (Panel → Automation). Steuerwege:
CC (per .mimap/MIDI Learn), PC (nur Favorites), qpat-Import (Stick).
