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

## 2026-11-21 — A006 @ slot 205 (LFO2*MW via matrix Ctrl) + Envelope-Curves linear

- **Modifier-Produkte (LFOx*MW / LFOx*Press / Modifier M = LFOx * controller)** waren
  bisher unmapped oder fielen auf reines Wheel/AT zurueck (LFO-Anteil verloren). Jetzt
  `_resolve_mod_source()`: matrix row mit **Src=LFO x + MatrixControlN=Wheel/AfterTouch**
  (+ControlAmount 1.0) — die „LFO2 CTRL: ModWheel“-Struktur des Iridium. Betrifft u.a.
  A006 Mod 10–12 (Modifier 1 = LFO2*MW -> F1 Cutoff / F2 Cutoff / O1 Pitch, jetzt rows
  10–12 mit Ctrl Wheel) und A001/A008 „LFO1*MW“ -> Src LFO1 + Ctrl Wheel.
- **Envelope-Curves**: Blofeld-ADSRs sind linear, das Iridium-Template defaultet Attack
  auf RC (1.0) — massiver Unterschied (User-Finding 11-21). Alle Amp/Filter1/Filter2/
  FreeEnv1/FreeEnv2 Attack+Decay+Release-Curves werden jetzt auf **2.0 'Lin'** gesetzt
  (Enum aus Factory-qpats: 0=Exp, 1=RC/'Exp alt', 2=Lin). Betrifft ALLE Sounds.
- rf100_v2 re-konvertiert: A006 jetzt 191 mapped (war ~150), qpat enthaelt
  MatrixControl10=14 'Ctrl Wheel' + alle Curves Lin. 397 Tests gruen.

## 2026-11-21 — A007 @ slot 206 (Pulsantw0rt): PWM/FM -> Matrix-Slots >= 21; Detune offen

- **Fest verdrahtete Modulationen landen jetzt auf Matrix-Slots ab 21** (Iridium hat 40
  Rows; 1-16 = Blofeld Mod 1-16, 17-20 = Amp-Velo/Amp-Mod/Osc-Pitch/DF-Env):
  - Osc N PWM Source/Amount -> `WF{n} Warp` (Waveform-Osc) bzw. `WT{n} Position`
    (Wavetable-Osc). A007: Rows 22-24 = LFO1/2/3 -> WF1/2/3 Warp (war komplett unmapped).
  - Osc N FM -> Approximation via `Osc{n} Pitch` (kein FM-Dst am Iridium).
  - Filter N Mod/FM/Pan Source -> Filter Cutoff/Pan (serial: DF Amount/DF Pan).
  - A007 jetzt 169 mapped (vorher ~150), PWM nicht mehr in unmapped.
- **Detune**: Blofeld raw 64 = 0 cent -> Iridium FinePitch 0.5 (A007: Osc2 0.5, Osc3 0.492
  bei raw 62). Am Geraet werden da „hohe Werte" angezeigt -> die cent-per-norm-Skala des
  Iridium ist NICHT zentriert bei 0.5 (bekannter live-calibration TODO, divisor 254
  annimmt +/-127 cent). Offen: Live-Pitch-Sweep per QUIR (FinePitch 0/0.5/1 -> Grundton
  messen), dann fine_pitch_norm korrigieren.
- rf100_v2 re-konvertiert (A007-qpat verifiziert: MatrixSrc/Dst 22-24 = WF Warp). 399 Tests.

## 2026-11-21 — Oktavlagen: CoarsePitch-Clamp + Constant-Verschiebung (A008); SD-Kopie veraltet

- Live verifiziert (QUIR, 11-21): `set-pid` (nicht set-param!) setzt OscNCoarsePitch;
  Runtime-Enum = 0..48 = −24…+24 semi (param-info pid 1391; 48 = +24 semi = 2').
  **Matrix-Runtime hat nur 40 Rows** (MatrixSrc41 loest nicht auf) — "ab 41" gibt es nicht.
- A007 @ SD: Geraet las nach load-patch Osc3CoarsePitch=36 -> die SD-Kopie `2:rf200` ist
  VERALTET (altes +12-Mapping); lokales qpat hat korrekt 12.0 (−12 semi = 16'). set-pid
  1391 12 wird akzeptiert. => SD frisch aus transfer/rf100_v2 kopieren.
- A008 Easy Piano: Osc1 = 1' (+36 semi) + 4 semi = +40 semi -> CoarsePitch clamp auf 48,
  Rest (+16 semi) als Matrix-Row Constant -> Osc1 Pitch in den Slots >= 21 (Amount
  0.5 + excess/48 — Skala ±24 semi angenommen, live-calibration TODO). CoarsePitch-Label
  zeigt jetzt die GESAMT-Semitones (war nur Semitone-Anteil).
- Kein PC von meinen QUIR-Sonden (nur Shell-Kommandos; set-pid nur Edit-Puffer, nie
  save-patch). ChangeProgram las 0.000. SD war am Geraet nicht gemountet (ls 2: fails).
- rf100_v2 re-konvertiert (A008: 184 mapped). 401 Tests gruen.

## 2026-11-21 — Matrix-Pitch-Kalibrierung live gemessen (INIT, Constant -> Osc1 Pitch)

- Experiment `tools/quir_matrix_pitch_calib.py` (codesearch): `init-patch`, nur Osc1
  (Sine), Matrix Row 1 = Constant(40) -> Osc1 Pitch(2), MatrixAmount gesweept, note 60
  gespielt, Grundton per FFT (parabolisch interpoliert).
- Ergebnis: **amount 0.5 = 0 semi (neutral), 1.0 = +24.0 semi, 0.0 = −13.8 semi**;
  dazwischen nichtlinear (exponentiell). Kalibrierungstabelle MATRIX_PITCH_CAL in
  qpat_map.py; Oktav-Rest-Shift (A008 1′) nutzt die inverse Interpolation
  (`matrix_pitch_amount_for_semi`). Erster Messlauf hatte Shape=4 = Pink Noise gesetzt
  (Enum: 0 Saw, 1 Sine, …, 4 Pink Noise) -> Messung unbrauchbar; mit Sine wiederholt.
- init-patch loest sauberen Zustand im Edit-Puffer aus (verifiziert per get-param:
  Shape 0, Vol 1/0/0, Coarse 24, Fine 0.5, Matrix row1 leer). Nichts persistiert.
- 402 Tests gruen; rf100_v2 re-konvertiert (A008: CoarsePitch 48 + Constant-Row).

### Mapping-Stand 2026-11-21 (Checkliste: Befund -> Fix -> Test)

| Befund (live am Iridium) | Fix in qpat_map.py | Test |
|---|---|---|
| A005@204: F1 PPG LP kam als svf/12dB LP an | `PPG LP -> "24dB LP"` (Filter12Type 3.0); matching.py exact | test_ppg_lp_maps_to_24db_lp |
| A005@204: Filter-Drive fehlte | Drive -> FX1=Drive, DriveType aus Curve (Tube/Pickup/PNP), Amount/DryWet=norm(drive) | test_filter_drive_*_a005/a043/pickup/no_drive |
| A006@205: Modifier1 = LFO2*MW unmapped | `_resolve_mod_source`: Src=LFOx + MatrixControl=Wheel/AT (+Amount 1.0) | test_modifier_product_*/test_direct_lfox_mw/test_resolve_mod_source_unit |
| Env-Attack Blofeld linear vs Iridium RC | alle Amp/Filter/FreeEnv Attack/Decay/Release-Curves = 2.0 'Lin' | test_envelope_curves_are_linear |
| A007@206: Osc PWM/FM, Filter FM/Pan unmapped | Matrix-Slots >= 21: OscN PWM -> WF{n} Warp/WT Position, OscN FM -> Osc{n} Pitch (approx), Filter Mod/FM/Pan -> Cutoff/Pan (serial: DF) | test_a007_osc_pwm_*/test_a005_osc_fm_* |
| A008@207: Osc1 1' (+36 semi) > CoarsePitch-Max (+24) | Clamp auf 48 + Rest als Constant -> OscN Pitch, Amount per MATRIX_PITCH_CAL (live: 0.5=0 semi, 1.0=+24 semi) | test_a008_osc1_1ft_*/test_matrix_pitch_calibration_inverse |
| A007@206: Detune-Anzeige am Panel „hoch" | DOKUMENTIERT, offen: FinePitch-Kalibrierung live (FIXES_TODO), Mapping raw 64 -> 0.5 bleibt bis dahin | — (FIXES_TODO) |
| SD `2:rf200` war veraltet (A007 las CoarsePitch 36) | kein Code-Bug; frische Kopie aus transfer/rf100_v2 noetig (plain cp) | — |
| Matrix-Runtime nur 40 Rows (kein 41) | Doku; Hard-wired-Block nutzt 21..40 | — |

### P0-Fixes A1/A3/A4 (2026-11-21)

| Befund (Messung) | Fix in qpat_map.py | Test |
|---|---|---|
| PWM Amount nur auf dem Iridium hörbar (3,3–6,6×), weil `WFn Warp` auch Sägezahn/Triangle verändert | `has_pulse_width()`: Matrixzeile nur für pulsartige Shapes; Saw/Triangle/Sine -> `Ignored: …`-Hinweis, Wavetable weiter `WTn Position` | test_pwm_row_only_for_pulse_shapes, test_a007_osc_pwm_mapped_to_wf_warp_rows_ge_21 |
| Reverb-Mix über `Constant -> FX2 DryWet` konnte keinen statischen Zwischenwert erzeugen | `ReverbGain = norm(Effect N Mix)`; Matrixzeile entfernt. Handbuch OS3: Reverb Gain ist der Dry/Wet-Regler (0 % trocken, 100 % nur Hall) | test_reverb_fx2_mix_via_reverb_gain_and_params |
| Unisono Detune ohne monotone Reaktion, obwohl Count gesetzt wurde | `Allocation/Unisono = 0uuu000a` (Spec 4.10): Bits **4–6** statt 5–7 -> `unison_count()`; `UnisonoPan=0.5`, `UnisonoDelay=0.0` (Blofeld hat keinen Pan-Spread/Voice-Delay) | test_unison_count_uses_bits_4_to_6 |

- Geräte-Verifikation (QUIR, lesend): `param-info 3691` = UnisonoCount, Enum
  0 Off / 1 = 2 … 7 = 8; `param-info 2747` = FXTotalDryWet, `ReverbGain` existiert
  als eigener kontinuierlicher Parameter.
- Offen: Neumessung der drei Punkte (`profile_testb_sweep.py osc2|unison|fx`);
  die frühere Unison-Aufnahme zeigte bei Detune 127 eine Reaktion (Centroid
  3536 -> 3140 Hz), aber nicht monoton.

### A2-Fix Filter 2 (2026-11-21, ohne neue Hardware-Messung)

| Befund (bisherige Messung) | Fix in qpat_map.py | Test |
|---|---|---|
| F2-Type „defekt“: nur `Filter12Type` (F1) wurde geschrieben; v14/v15 haben ein separates `Filter2Type` | `Filter2Type` aus der Blofeld-F2-Type (gleiche v14-Enum-Tabelle) | test_parallel_routing_f2_stays_filter2_active |
| F2 in Parallel-Schaltung praktisch stumm: v8-Template `FilterLink=Boost` ignoriert Cutoff 2/Resonanz 2 | parallel mit aktiver F2: `FilterLink=Independent` (6.0); seriell bleibt `Single`, weil F2 im DigiFormer sitzt | test_parallel_routing_f2_stays_filter2_active |
| Resonanz bei 100 % Mismatch (cos 0,06–0,44), Iridium erreichte die Selbstoszillation erst bei raw 127 | `blofeld_reso_norm()`: raw 113 (Blofeld-Selbstoszillation) -> 1.0, darüber clamp | test_resonance_self_oscillation_calibration |
| F2-Drive bei raw 32/64 nur 0,20/0,30× so stark wie Blofeld (bei 127 OK) | Drive ist ein Insert: `DriveDryWet=1.0` statt `norm(drive)`; `DriveAmount=norm(drive)` | test_filter_drive_* |

- Die f2-Neumessung steht noch aus (`TODO_MEASURE.md`); insbesondere muss vor
  dem Lauf per Readback geprüft werden, dass `FilterLink`, `Filter2Type` und
  `DriveDryWet` wirklich im Edit-Buffer stehen (die frühere Messung nutzte
  teilweise Geräte-Init-Werte statt der qpat-Werte).

### A7a-Fix LFO-Fade (2026-11-21)

| Befund (Messung) | Fix in qpat_map.py | Test |
|---|---|---|
| LFO 1 Fade defekt (Blofeld 2,6–2,9; Iridium 0,1–0,3) | Blofeld Fade bipolar: raw>64 -> `LfoNAttack=(raw-64)/63`, raw<64 -> `LfoNDecay=(64-raw)/64`, 64 -> beide 0 | test_lfo_fade_maps_to_attack_decay |

- Free-Speed-Hz-Kurve bleibt offen (Hardware-Kalibrierung, `TODO_MEASURE.md`).

### RF100 v3 vorbereitet (2026-11-21)

- `scripts/reconvert_rf.py` konvertiert A001–A100 aus den SNDD-Dumps mit dem
  aktuellen Mapping nach `transfer/rf100_v3` (SD-Ordner `rf300`, Slots 300–399,
  `MANIFEST.json`/`MANIFEST.md`). Ergebnis: 100 qpats, gemappt 141–220
  (Mittel 170,3), alle roundtrip-parsebar und SD-sicher benannt.
- `scripts/measure_rf100.py` lädt die qpats per QUIR von `2:rf300/...`, misst
  Notes 72/60, scorst mit v2 und schreibt `recordings/sim_log_v3.jsonl`
  (dry-run ohne `--run`; `--verify-sd` read-only; Resume über `(loc, note)`).
- Trainingspipeline mit dem vorhandenen v2-Log als Smoke-Test geprüft:
  `prognose train --log recordings/sim_log_v2_rf.jsonl --dumps dumps
  --target score` → n=99, MAE 10.47, R² 0.064 / R²_cv 0.132 (unverändert).
  Nach dem neuen Lauf: `--log recordings/sim_log_v3.jsonl --model
  models/prognose_rf_v3.pkl`.
- Ablauf und Akzeptanz: `docs/MEASURE-RF100-V3.md`.

## 2026-11-22 — A005 am Gerät geprüft: Osc1 aus korrekt, DigiFormer-HP zu hoch

- User-Check Slot 204 (A005 HooverBass): Osc1 im Mix aus, F2/DigiFormer-HP
  nimmt den Bass. **Osc1 ist korrekt:** Blofeld Mixer Osc1 Level = 0
  (SDATA 61), das qpat schreibt `Osc1Vol=0`.
- **F2:** Blofeld `HP 12dB` raw 48, seriell → `DigiFormerType=Nave HP12`,
  `DigiFormerAmount=0.393`. Am Ohr zu weit offen; Messung (Notes 60/72):
  Amount 0,393 → 46/40, 0,25 → 52/55, 0,15 → 51/53, 0,08 → 58/50,
  **Bypass → 26/26**. Der HP wird gebraucht, ist aber zu hoch angesetzt.
  Ein zweiter Sweep über Former-Typ/Amount war nicht reproduzierbar (der
  Shell-Zustand ließ sich nicht bestätigen) → offener Fix **A12** in
  `TODO_FIX.md` (eigene Amount-Kalibrierung nötig).
- Zusätzlich: die fehlenden Bänder liegen bei A005 eine Oktave **unter** dem
  Grundton (30–50 dB) — der bekannte Oktav-/CoarsePitch-Fall, unabhängig vom
  Former.
- Messlauf v3: `measure_rf100.py --verify-sd` → 100/100 (Name + Byte-Größe);
  `ls` blockiert den QUIR-Readout, daher Verify in eigener Sitzung und
  `--run --skip-verify` für den Lauf.

## 2026-11-22 — RF100 v3: erster Messlauf ungültig (load-patch-Pfad ist ein No-op)

- **Befund:** `load-patch 2:<dir>/<file>.qpat` wird von der Firmware akzeptiert,
  ändert den Edit-Buffer aber **nicht** (Readback `Osc1FinePitch` blieb 0.500,
  während der Slot-Load 208 den qpat-Wert 0.988 lieferte). Nur
  `load-patch <slot>` lädt wirklich. Der erste v3-Lauf (200 Zeilen) hat daher
  über weite Strecken denselben Iridium-Sound gemessen.
- **Verworfen:** Log `recordings/sim_log_v3_invalid_loadpath.jsonl`, Modell
  `models/prognose_rf_v3.pkl` gelöscht, `models/prognose_rf.pkl` wieder v2.
  Die dort berichteten Zahlen (mean 56,6; R² 0,212) sind **nicht** gültig und
  die „Regressionen“ A009/A001/A095 waren ein Artefakt.
- **Korrekte Stichproben** (Slot-Load + Readback-Verifikation, 2026-11-22):
  A001 76,5/73,9 · A009 68,7/59,4 · A016 72,8/79,5. A009 ist damit **nicht**
  schlechter als v2 (alt 60,3/69,9), A016 deutlich besser.
- **Runner-Fix:** `measure_rf100.py` lädt per Slot aus dem Manifest und prüft
  nach jedem Load drei Parameter per `get-param` (`Osc1FinePitch`,
  `Filter1CutOff`, `Filter1EnvAmount`); Abweichung > 0,002 bricht ab. Neuer
  Lauf schreibt `recordings/sim_log_v3.jsonl`.
- **Offen:** neuer Lauf + Entropy/Retrain; A12 (DigiFormerAmount) muss neu
  gemessen werden, weil auch der frühere DF-Sweep den Pfad-Load nutzte.
