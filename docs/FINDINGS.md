# Findings – connection setup & measurements (documented)

All statements empirically verified on the Mac (macOS, CoreMIDI + AVFoundation).

## Visible MIDI ports (CoreMIDI/rtmidi)

```
OUT/IN: Launchpad Pro MK3 LPProMK3 MIDI
OUT/IN: Launchpad Pro MK3 LPProMK3 DIN
OUT/IN: Launchpad Pro MK3 LPProMK3 DAW
OUT/IN: Scarlett 18i8 USB
OUT/IN: Blofeld                              <- Blofeld via USB (new)
OUT/IN: Iridium Keyboard (MIDI 2.0) Synth
OUT/IN: Iridium Keyboard (MIDI 2.0) MIDI 2.0
```

## MIDI mapping (verified)

| Synth | Port | Channel (1-based) | Direction | Identity |
|---|---|---|---|---|
| Blofeld | `Blofeld` (USB) | **5** (Single Mode, Global Channel) | bidirectional | `F0 7E .. 06 02 3E 13 00 00 00 "1.24" F7` (Waldorf=3E, Blofeld=13, FW 1.24) |
| Blofeld (fallback) | `Launchpad Pro MK3 LPProMK3 DIN` | 5 | Out only (In only delivers the Launchpad's own reply `00 20 29`) | – |
| Iridium | `Iridium Keyboard (MIDI 2.0) MIDI 2.0` | **6-9** (Parts 1-4) | Out (keyboard sends ch6) + In works | no identity reply so far |
| Iridium | `Iridium Keyboard (MIDI 2.0) Synth` | – | receives nothing (display shows no MIDI-in reaction) | – |

Important: on the Iridium endpoint `MIDI 2.0`, MIDI 1.0 bytes are automatically
delivered as UMP (mt=2) by CoreMIDI – plain mido messages work there.
After switching the SOM2 USB ports ("Computer"/"USB CTRL") or replug/reboot,
reception on the `MIDI 2.0` endpoint was active.

## Audio mapping (Scarlett 18i8, 20 channels @ 48 kHz, AVFoundation)

| Synth | Scarlett inputs | 0-based channels in the stream |
|---|---|---|
| Blofeld | **3/4** | c2/c3 |
| Iridium | **5/6** | c4/c5 |

Verified by key press on the Iridium (audio appeared on In5/6, ca. -22 dBFS)
and via MIDI note (Blofeld->In3/4 ca. -17 dBFS, Iridium->In5/6 ca. -27 dBFS).

## Blofeld: Multi vs Single Mode

- **Channel scan is NOT a reliable mode indicator**: in Multi Mode all 16 parts may
  sit on *arbitrary* channels (for us e.g. only channel 5 was occupied – yet Multi Mode
  was on). Only "all 16 channels respond" would be a safe Multi criterion; a single
  channel proves nothing.
- Status: the Blofeld was in **MULTI MODE** (per user) and was switched to **SINGLE MODE**
  (Shift+Sound/Multi). Verified: afterwards only channel 5 responds. Use Single Mode for
  program transfer.
- Global Channel = channel 5 (in Single Mode only this one responds).
- Release leftovers fool the scan (apparently channels 2/3/5): send CC123 +
  CC120 on all channels beforehand and wait ~4 s, then baseline.
- `scripts/check_blofeld_mode.py` shows channels/identity/GLBD and the hint.

## Blofeld SysEx (via USB port `Blofeld`, works)

Format `F0 3E 13 <dev> <cmd> [data] F7` (omit checksum on requests):

| Request | Cmd | Reply | Content |
|---|---|---|---|
| `F0 3E 13 00 04 F7` (GLBR) | 0x04 | GLBD (0x14), ~74 data bytes | global parameter dump |
| `F0 3E 13 00 00 F7` (SNDR) | 0x00 | SNDD (0x10), ~386 bytes | current sound (edit buffer) |
| `F0 3E 13 00 01 F7` (MULR) | 0x01 | MULD (0x11), ~419 bytes | current multi (contains e.g. "String Ch5") |

Helpers: `bloridium/waldorf.py` (`build_sysex`, `parse_sysex`, `identity_reply_info`).

## Technical pitfalls (solved)

- ffmpeg `pan` filter doesn't know layouts > 8 channels -> with >= 16 channels
  record raw and slice in numpy (`bloridium/audio.py`).
- AVFoundation sometimes doesn't release the Scarlett immediately -> retry with
  1 s pause in `audio.record`.
- python-rtmidi `send_message` rejects packets > 3 bytes (SysEx only) ->
  for real UMP use the compiled tool `tools/ump_send`
  (`clang -framework CoreMIDI -framework Foundation -o ump_send ump_send.m`).
- Direct `MIDISend` via ctypes didn't deliver any packets ->
  `bloridium/midi2.py` therefore uses `tools/ump_send`.
- Identity reply on the Launchpad DIN port (`00 20 29`) comes from the
  **Launchpad itself**, not from the Blofeld.
- Noise on In11/12 (ca. -5 dBFS) was stuck notes;
  eliminated with CC123 on all channels.

## Round 2: SysEx mapping (status: in progress)

### Blofeld SysEx – fully documented & read out
- Official spec downloaded: `docs/manuals/Blofeld_sysex_v1_04.pdf`
  (Nextcloud share `ybExJgT4TzqT8ir`, "Blofeld sysex 1.04" in the Blofeld FAQ area).
- SNDD format: `F0 3E 13 DEV 10 BB NN <SDATA 383 B> CHK F7`; CHK = sum(SDATA) & 0x7F
  (status/IDs do NOT count). SNDP (0x20) = single parameter per index 0..382.
- Complete SDATA table (spec 3.1, indices 0..382) in `bloridium/blofeld_dump.py`
  implemented (incl. value tables 4.1-4.18, FX 5.x).
- `scripts/step2_read_blofeld_dump.py [A043|edit]` reads SNDD and saves to
  `dumps/blofeld_sndd_<loc>_<ts>.bin/.hex`. Verified: 392 B total, CHK ok.
  - Default (no arg) = edit buffer (BB=7F): delivered **"JP Wannabe"** – the buffer
    holds the last *edited* sound, not the selected one!
  - Location-based (SNDR with BB NN, e.g. `A043` = `00 2A`): **"SH Power"**
    (A043 per user; Osc1=Saw, Osc2=Pulse, Osc3=off, F1=LP24dB Cutoff 52 Reso 51,
    Cat=Bass, Mod1: LFO2*Press->Pitch Amt 84).
- `scripts/step2_parse_blofeld_dump.py` decodes the dump (290 named parameters,
  e.g. Osc1/2 Shape=Saw, F1=LP12dB Cutoff 67 Reso 38, Mod1: LFO1*MW->Pitch Amt 82).

### Iridium – SysEx status
- **No SysEx reply on either USB endpoint** (`MIDI 2.0` and `Synth`):
  neither Universal Device Inquiry nor Waldorf-style sweep `F0 3E <model 0x00..0x1F> 00 <cmd 0x00/0x01/0x04> F7`
  (see `scripts/step2_probe_iridium_sysex.py`) – 0 replies.
- Channel voice (notes) and CC are received on `MIDI 2.0` (verified via audio).
- CC reception tested: CC7=0 on channels 6-9 lowers the peak by ca. -4.6 dBFS;
  individual OSC-VOL CCs (33/47/61) show only small peak deltas (check layer/channel
  assignment; CC7 acts channel-wide).
- Iridium CC table (115 CCs, CC 2..116): `docs/midi-maps/iridium_midi_guide.csv`
  (midi.guide / pencilresearch/midi GitHub). Beware: Filter1 Cutoff has NO CC there;
  incoming NRPN are ignored per the OS3 manual.
- First mapping table (Blofeld SNDD -> Iridium CC): `docs/MAPPING.md`.
- Iridium manuals (local) contain NO SysEx byte documentation (only glossary);
  the OS4/SOMv2 manual only describes new global MIDI options (layer channels per port).
  The official "Iridium MIDI Implementation" PDF is presumably in the login area
  (My Waldorf) or as .qpat/.syx format – .syx import via Load>Actions>Import
  is documented (Waldorf FAQ).
- **Iridium answers NO SysEx at all** – tested: bytestream + native UMP
  (SysEx7 mt=3 AND SysEx8 mt=5), both endpoints (`MIDI 2.0`, `Synth`),
  model sweep 0x00-0x3F, device-ID sweep 0x00-0x7E, cmds 0x00/0x01/0x04/0x30,
  with/without location – 0 replies. But channel MIDI TX/RX works
  (after program change the Iridium sends CC123 all-notes-off bursts on ch6-8;
  CC7=0 on ch6-9 lowers the peak by -4.6 dBFS). => Dump read direction probably only
  as file export (Load>Actions>Export -> SD/USB as .qpat) or possibly DIN.
- **.qpat format reverse-engineered** (official soundsets from waldorfmusic.com,
  `docs/refs/*.zip`: Quantum_Factories.zip 1186 qpat, additional_patches_IKB.zip
  453 qpat): magic `b4 ec 33 00`, uint32 version, name/author/bank/category/attrs
  each char[32], then key-value records from ~0x200 (type byte `?@B>=<` + key,
  value field ~34 B from key+33; numeric = float LE, else string). Parser:
  `bloridium/qpat.py`. Complete Iridium parameter namespace extracted
  (Osc1Type/Osc1Vol/Filter1CutOff/Filter1Reso/Filter12Type/AmpEnv*/Filter1Env*/
  FreeEnv1-3*/MatrixAmount1-40/FX1Type/... – 645 params in one patch).
  Samples: `docs/refs/qpat/*.qpat`.
- **Research result (subagent, ses_e44a06781ffeZV5NgA6lrz4Uzc): Iridium/Quantum
  have NO SysEx application layer** – no dump request, no SysEx reply,
  also not via DIN (OS 3.3+ UMP = pure transport, no SysEx handler;
  Gearspace: "there is no sysex layer in quantum/iridium"). Patch transfer only
  file-based: `Load>Actions>Export/Import` -> SD/USB as **.qpat**. Waldorf SysEx
  exists only for legacy + M (model ID 0x30); Blofeld = 0x13.
  .qpat spec (verified against official Waldorf files + autosamplerT code):
  `b4 ec 33 00` magic, u32 version, name/author/desc + 4x category each char[32],
  param-count u16, 16 resource headers a 12 B (type/offset/len), pad to 0x200,
  then 68-B records: `float32 LE value | char[32] name (with type prefix @/?/B...) |
  char[32] display`, then sample maps (tab-separated). Writer reference:
  github.com/timandtheocean/autosamplerT `src/export/export_qpat.py`.
  => **Iridium "dump" = .qpat file** (on the device Load>Actions>Export to USB/SD,
  then parse on the Mac with bloridium/qpat.py). Conversely we can write .qpat
  ourselves (Blofeld-SNDD -> qpat keys) and import on the device.
  Artifacts of the subagent: /private/var/folders/kg/zkn9b6n546vfmpb6qd3n4pdr0000gn/T/iridium-research/.
- **Iridium does NOT appear as USB drive on the Mac** (checked 2026-11-08: diskutil/
  system_profiler show no additional drive, only MIDI endpoints). rolfw's
  2019 idea ("sample storage appears as an external drive on your computer") never
  came for Quantum/Iridium (Paul_xyz 2023: file-based only). Gearspace Iridium p.112:
  USB host recognizes "Only MIDI and storage devices". "Internal flash as drive" = only
  in the device's own browser (copy stick<->flash on the device). => File exchange only
  via USB stick/SD in the host port/slot.
- **Incident solved: Iridium goes silent at CC7=0** – CC7 is the
  **Output/Main Level** on the Iridium (not listed in the midi.guide CSV); 0 = silent. After CC7=0
  no sound on In5/6 (survives patch change; MIDI input alive: PC -> CC123).
  Fix: set CC7 high (confirmed by user on the device). mapping.py now maps
  Blofeld "Amplifier Volume" -> CC7. No restart needed, just CC7>0.
- After reboot (preset 0039 "Stepping Out" = SPLIT): ch6 note36 = -26 dBFS,
  note60 = -59 (split at C4); ch7 note60 = -36 dBFS. => For A/B use a lower note
  (36) or address all part channels 6-9.

## Similarity score saturation (2026-11-20)

- **The v1 `sim.compare()["score"]` could not tell timbres apart.** Its spectral part (70 %) was the
  cosine of two frame-averaged log spectra in raw dB. Those vectors are almost entirely
  negative (-40..-120 dB, empty bands at the -240 dB floor), so the cosine stays near 1.0
  for unrelated sounds. Synthetic check (same envelope, 2 s @ 48 kHz):

  | A | B | score v1 | score v2 | spec_mad_db |
  |---|---|---|---|---|
  | saw 110 Hz | saw 110 Hz | 100.0 | 100.0 | 0.0 |
  | saw 110 Hz | square 110 Hz | 99.3 | 77.5 | 6.4 |
  | saw 110 Hz | white noise | 99.3 | 64.1 | 10.2 |
  | sine 220 Hz | sine 3000 Hz | 91.4 | 30.0 | 20.6 |
  | sine 3000 Hz | percussive saw 110 Hz | 89.8 | 55.3 | 11.1 |

  Consequence: the measured scores in `sim_log.jsonl` (86.8–98, mean 93.9) mostly reflect
  envelope differences, and the RF prognosis trained on them inherits that.
- **Fix (score_version 2, replaces v1):** `score = 70 % · (1 − spec_mad_db/20) + 30 % · (1 − env_dtw)`.
  `spec_mad_db` = mean |ΔdB| over bands active in either signal (clamped to 60 dB below
  each peak, level offset removed via the median). The v1 cosine is still returned as the
  diagnostic `spec_cos`. Every result carries `score_version: 2`; log rows without it are
  v1. `prognose train` skips them by default (`--min-score-version 2`). The 20 dB scale is
  a heuristic and still needs calibration against user ratings (like specdiff).

## 2026-11-20 — v2-Rescore der vorhandenen Aufnahmen + Entropy-Check (vor Retrain)

- `scripts/rescore_v2.py`: alle 45 vorhandenen `ab_*`-Paare (9 Locs: A001 A008 A010 A019
  A022 A039 A043 A071 A073) offline mit Score v2 + embed + llm + d1 re-gescored →
  `recordings/sim_log_v2.jsonl` (40/45 mit Score; v1-Log bleibt unberührt).
- v2-Scores streuen deutlich (mean 57.9, min 35.9, max 82.9) vs. v1-gesättigt ~94–97
  → v2 ist als RF-Label deutlich signalhaltiger.
- `bloridium prognose entropy` (H(y) + IG + partielle IG gegeben spec_mad_db):
  spec_mad_db erklärt das v2-Label quasi allein (pearson −0.998, zirkulär: 70 %
  Label-Gewicht); **embed_score / profile_score / spec_dtw / env_dtw haben partielle
  IG = 0.000** (n=9) — auf diesem Mini-Set senkt nichts die Entropie weiter.
  llm_score konstant 85 → IG 0. Caveat: embed/d1 sind erst NACH der Messung verfügbar
  und können keine Features für die Vorhersage aus dem SNDD-Dump allein sein (Leakage);
  sie taugen als Label-Komponente/diagnostisches Feature, nicht als Input-Feature.
- Finale Entropy-Auswertung folgt nach dem Neu-Recording der 100 Sounds mit v2.

## 2026-11-20 — v2 full pipeline: re-record A001–A100, entropy check, RF retrain

- Neu-Recording aller 100 Sounds mit erweiterter Konversion (LFO Shape/Phase/Delay,
  Mixer-Noise auf freien/stummen Osc; rf100_v2 auf SD `2:rf200`, verify-sd 100/100):
  200 Messungen (notes 72,60), alle `score_version: 2`, 188 gescored, **v2 mean 50.5,
  range 22.4–81.3** (v1 war gesättigt ~94–97). Subset (24 Locs) zusätzlich mit
  `--llm --profile` (d1): 83 llm + 83 d1-profile.
- `prognose entropy` auf n=99 v2-Labels: H(y)=3.14 bits. spec_mad_db erklärt das Label
  selbst (pearson −0.985, zirkulär). **Partielle IG gegeben spec_mad_db: embed_score
  0.627 bits, profile_score (d1) 0.603 (n=23), env_dtw 0.596, spec_dtw 0.427; llm_score
  konstant → 0.** => embed/d1 senken die Entropie WEITER, sind aber erst nach der Messung
  verfügbar (Leakage als RF-Input) — als Label/diagnostisches Feature tauglich.
- Retrain v2 (`--target score`): n=99, MAE 10.47, RMSE 12.51, **R²=+0.064 / R²_cv=+0.132**
  (v1: R²<0). Top-Features: Filter 1 Cutoff, Osc 1/3 Octave, Filter 1 Resonance,
  Filter 1 Env Amount. `combined` bleibt rauschig (R² −0.19) → `score` shippen.
  Alte Modelle als `models/prognose_rf*_v1.pkl` behalten.
- Bugfix: `audio.record` ffmpeg ohne Timeout hing 60 min (Fix: timeout=duration+20 s,
  4 Versuche); qpat-Dateinamen per Konversion SD-sicher (`qpat.sd_filename`).

## 2026-11-21 — v2-Messung verifiziert + Detail-Analyse A001–A005 (scripts/detail_compare.py)

- Slot-Belegung während des v2-Laufs (2026-11-20): pro Loc `load-patch 2:rf200/<sd_name>.qpat`
  + `save-patch <slot>` — quir_rf_dataset_v2.jsonl: 200 Zeilen, 100 Slots (200–299), **100
  verschiedene load-Pfade** (1:1 zu den Locs). Log `storeTimbreToSlot`-Zeilen mit lesbarem
  Namen matchen die Labels (200=JMX jun. … 204=HooverBass … 215=ArangedHeaven CT), kein Slot
  mit zwei verschiedenen Namen. Leere Namen im Log sind Interleaving zweier Jobs (alt +
  --resume) im selben Logfile. Messung ist nicht entwertet. (Gegencheck am Gerät steht aus —
  Iridium war 11-21 kurz nicht am MIDI-Bus; Readback der Slot-Namen + CoarsePitch folgt.)
  Beachte: *gespeicherte* Slots laden bekanntermaßen als Sample-Slots still (−70 dBFS,
  TODO_FIX) — am Panel klingen deshalb alle Slots gleich (leise), die Namen sind aber
  verschieden. Gemessen wurde immer vom SD-Pfad, nie vom Slot.
- Detail A001–A005 (v2, live): A001 79–80 (bestes), A002 59–62, A003 34–39, A004 54–59,
  A005 27–28. RF-Prognose aus dem Dump allein trifft das gut (A001 70±12 vs 80, A002 62 vs 60,
  A005 50±12 vs 27 — hier zu optimistisch).
- Auffälliges Muster A002–A005: schlechteste Bänder liegen im Grundtonbereich
  (band_delta_db = Iridium − Blofeld, z.B. A005@72: 211–302 Hz −75…−90 dB; A005@60:
  117–148 Hz −63…−73 dB). A001 (beide Osz. Octave 64) hat das nicht. Hypothese: **Osc-Octave
  < 64 (CoarsePitch < 24, z.B. 12 bei raw 52, 0 bei raw 40) landet am Iridium nicht korrekt**
  → Grundton fehlt eine Oktave daneben. A003 zusätzlich: Osc2 Sync-to-Osc3, FM Osc3→Osc1/2/
  Filter, PWM — alles unmapped. A004: Osc2 „PWM Pulse“ PW 9 (sehr schmal) + PWM via Env3.
  Verifikation am Gerät (get-param CoarsePitch + Spektral-Test note 72) folgt, sobald das
  Iridium am Bus ist.

## 2026-11-21 — Live-Findings A005 @ Iridium Slot 204 -> Mapping-Fixes

Befunde am Geraet (User, Slot 204 = A005 HooverBass) und Fixes in qpat_map.py:

- **Filter 1 PPG LP**: war als `12dB LP` (Filter12Type 0.0) konvertiert, am Geraet
  FilterModel=svf + FilterType=12dB LP. PPG LP ist ein 24dB-Ladder -> jetzt
  `BLOFELD_FILTER_TO_IRIDIUM["PPG LP"] = "24dB LP"` (Filter12Type 3.0; 24dB-Typen
  sind in Factory-qpats ohne Filter1Model-Aenderung gueltig). matching.py
  FILTER1_EXACT["PPG LP"] jetzt 1.0.
- **Filter-Drive -> FX1 Drive**: Blofeld `Filter 1/2 Drive` hat kein Iridium-Pendant
  (auch kein Matrix-Dst) -> wird jetzt als **Effect 1 = Drive** simuliert, DriveType aus
  der Blofeld-Curve (Tube->1.0, Pickup 1/2->2.0, Clipping etc.->0.0 PNP), DriveAmount/
  DriveDryWet = norm(drive). War Blofeld-FX1 hörbar (mix>0), landet ein
  "replaced by filter-drive"-Eintrag in unmapped. A005: F2 Drive 8 Tube -> FX1 Drive
  Tube 0.063. Betrifft u.a. A043 (F1 Drive 16 Clipping -> FX1 Drive PNP; FX1 Chorus mix 0
  war eh stumm).
- **Osc1 Mix 0 bei A005 ist korrekt**: Blofeld Mixer Osc 1 Level = 0 -> Osc1Vol 0.0
  (das Panel zeigt OscNVol als „OscN Mix“). Kein Bug.
- Re-Convert A001–A100 -> transfer/rf100_v2 (MANIFEST/config unveraendert, sd_dir rf200,
  Slots 200–299). Naechster Schritt: SD-Kopie (plain cp) + frischer Messlauf.
