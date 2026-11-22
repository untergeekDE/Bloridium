# Findings — current reference

Empirically verified on the reference rig. This file holds the facts still needed for
normal work; dated measurement journals and superseded notes are in `docs/research/`.

## Reference rig

| Device | MIDI | Audio (Scarlett 18i8, 48 kHz) |
|---|---|---|
| Blofeld (FW 1.24, Single Mode) | USB port `Blofeld`, channel **5** | inputs **3/4** (0-based c2/c3) |
| Iridium Keyboard (OS 4.1.0b2, SOM2) | Parts 1–4 = channels **6–9** | inputs **5/6** (0-based c4/c5) |
| Launchpad Pro MK3 | DIN fallback; carries Iridium MIDI during measurements | – |

- On the USB endpoint `Iridium Keyboard (MIDI 2.0) MIDI 2.0`, CoreMIDI delivers MIDI 1.0
  bytes as UMP; plain mido messages work. The `... Synth` endpoint receives nothing.
- Direct Iridium USB can create a ground-loop noise on inputs 5/6. For low-noise A/B
  recordings use the Launchpad DIN path and unplug the Iridium USB; the shipped
  `bloridium.yaml` uses USB for convenience (switch the ports for measurements).
- The Iridium keyboard sometimes boots with a split preset (e.g. 0039 “Stepping Out”);
  then only part of the range sounds. Check or load a single patch before measuring.
- Scarlett/AVFoundation sometimes does not release the device immediately; `audio.record`
  retries after a short pause. With ≥ 16 channels, record raw and slice in numpy
  (ffmpeg’s `pan` filter supports at most 8 channels).

## Blofeld SysEx (documented, works)

Format `F0 3E 13 <dev> <cmd> [data] F7`; requests carry no checksum.

| Request | Cmd | Reply | Content |
|---|---|---|---|
| `F0 3E 13 00 00 BB NN F7` (SNDR) | 0x00 | SNDD (0x10) | sound at location BB NN (383-byte SDATA + checksum) |
| `F0 3E 13 00 20 LL HH PP XX F7` (SNDP) | 0x20 | – | set parameter index 0..382 |
| `F0 3E 13 00 04 F7` (GLBR) | 0x04 | GLBD (0x14) | global parameters |
| `F0 7E 7F 06 01 F7` | – | identity | Waldorf `0x3E`, Blofeld model `0x13` |

- SNDD checksum = `sum(SDATA) & 0x7F`; status/IDs are not counted.
- **Location matters**: the edit buffer (BB NN = `7F 00`) contains the last *edited*
  sound, not the selected one. Always request by location (A043 = `00 2A`).
- Single Mode is required for transfer (`Shift+Sound/Multi`); in Multi Mode the channel
  scan is not a reliable mode indicator. Send CC123 (+ CC120) on all channels and wait
  ~4 s before scanning.
- Official spec: `docs/manuals/Blofeld_sysex_v1_04.pdf` / `.txt`; SDATA table in
  `bloridium/blofeld_dump.py`.

## Iridium interfaces

- **No documented SysEx application layer** and no USB-drive mode. Patches arrive as
  `.qpat` files on SD/USB (`Load > Actions > Import`) and are read back via
  `Export`. Incoming **NRPN is ignored**; the panel only sends NRPN.
- OS 4.1.0b2 also accepts private device-side tooling that is **not part of this project**.
  Some archived measurement runs were taken with it; it is firmware-specific and not part of
  the normal convert/transfer workflow.
- Computer control in this project: **MIDI CC** (the published list has 115 assignments,
  CC 2–116; direct control needs a `.mimap` or MIDI Learn), **program change** (only
  selects within the active Favorites set) and **notes**.
- **CC7 is main/Output Level by default (CC7 = 0 → silent).** A loaded `.mimap` can
  reassign CC7 (the `rdb` map maps it to Filter1 Amount); then it no longer silences.
  Check the loaded map before touching CC7. Likewise CC0/CC32 may change from bank
  select to parameters when a map is loaded — choose the Favorites set on the device.
- Measured Favorites/PC mapping: `docs/IRIDIUM-FAVORITES-MAP.md`; the authoritative
  slot list for scripts is `DEFAULT_MAP` in `scripts/sim_sweep_pcs.py`.

## `.qpat` format

- 512-byte header (magic `b4 ec 33 00`, version, name/creator/description, four
  categories, parameter count, resource headers), then 68-byte records:
  `float32 LE` normalized value, `char[32]` key, `char[32]` display string; sample maps
  follow as tab-separated data.
- OS 4 expects **version 14** files; the template ships as v8 and is rewritten on export.
- Runtime enums (OS 4.1.0b2) equal qpat enum values; old displayed strings in some
  exports are stale. See `docs/refs/runtime_enums_2026-11-18.md`.
- File names must be SD-safe (`bloridium.qpat.sd_filename`: no spaces, only
  `[A-Za-z0-9-_.]`), because device-side load paths have no quoting.

## Similarity score and prognosis

- **Score v2** (`score_version: 2`): `70 % · (1 − spec_mad_db/20 dB) + 30 % · (1 − env_dtw)`,
  0–100, plus per-band dB deltas. `spec_mad_db` is the mean level-aligned log-spectrum
  deviation; the old v1 dB cosine saturated (saw vs. white noise scored 99.3) and is kept
  only as the diagnostic `spec_cos`. Log rows without `score_version` are v1 and are
  skipped by `prognose train`.
- The 20 dB scale is heuristic. The score is a **relative** guide, not a perceptual
  verdict; note 72 (C5) is the best comparison octave.
- Prognosis is a rough random forest over Blofeld SNDD parameters. The shipped model is
  v2-trained (R² ≈ 0.06 holdout / 0.13 CV); v3 labels did not improve it. Do not present
  predictions as precise.

## Archived material

`docs/research/` contains dated measurements and design notes: profiling sweeps,
per-block calibration (glide/LFO), RF100 runs, Phase-B evaluation, the old CC mapping
draft, German originals, historical handovers and superpowers plans/specs. Treat them as
evidence, not as current instructions.

## 2026-11-22 — A12: DigiFormerAmount braucht keine globale Skalierung

- Gültiger A/B (Slot-Load + Readback) über **alle 30 seriellen F2-Sounds** mit
  `DigiFormerAmount = 0,65 × aktuell`: **mean Δ +0,7**, 11 besser / 10
  schlechter. Ausreißer: A044 +29,6, A001 +19,0, A049 +12,3, A018 +12,0 gegen
  A083 −21,1, A006 −17,2, A023 −10,8. Ein Skalar ist damit **nicht**
  gerechtfertigt.
- A005 (HP 12dB) mit tiefen Noten: aktuell 85/71/64 (36/48/60), k=0,65
  83/72/70, k=0,35 88/73/67 → der HP ist nicht die Ursache des fehlenden
  Basses. Der bleibt der Sub-Oktav-/CoarsePitch-Fall.
- Konsequenz: A12 bleibt offen, aber neu gefasst — Amount-Kennlinie pro
  Former-Modell gegen Hz kalibrieren, nicht die Filter-Cutoff-Norm skalieren.

## 2026-11-22 — Sub-Oktav-Ursache: Template-Semitone-Slots (Fix, +33 Punkte)

- **Ursache:** Das Template `template_waveform.qpat` liefert
  `Osc2WaveformSemitone2 = 0` und `Osc3WaveformSemitone1 = 0`; 0 bedeutet
  **−12 Halbtöne**. Der Konverter hat diese Slots nie überschrieben, also lief
  **Osc 3 in jedem konvertierten Sound eine Oktave zu tief** (und Osc 2 je nach
  aktivem Slot ebenfalls). Das CoarsePitch-Mapping war korrekt.
- **Beweis (live, Slot-Load + Readback):** A020 Osc3 (Coarse 24 = +0) klang
  262 Hz statt 523 Hz. `Osc3WaveformSemitone1 = 12` → 525 Hz. Nur Slot 1 ist
  aktiv; Slots 2–4 sind inert.
- **Wirkung am Gerät** (nur diese Slots auf 12 gesetzt, sonst identisch):
  A020 30,3 → **63,0**, A023 40,2 → **51,8**, A024 38,2 → **61,2**.
- **Fix:** `qpat_map.py` setzt für alle drei Oszillatoren alle vier
  `OscNWaveformSemitoneX` auf 12 (+0) — die Blofeld-Semitone steckt bereits in
  CoarsePitch. Test: `test_waveform_semitone_slots_neutral`.
- **Neu konvertiert:** `transfer/rf100_v4` (SD `rf400`, Slots 300–399);
  Diff gegen v3 = nur die zwei geleakten Slots. 88/100 Sounds haben Osc3 hörbar.
- **Nächster Schritt:** v4 auf SD kopieren, Slots 300–399 laden, neu messen;
  die v3-Scores (26–96) sind für Sounds mit hörbarem Osc3 zu niedrig.

## 2026-11-22 — RF100 v4 (Semitone-Fix): Messung, Entropy, Retrain

- **Messung** (`transfer/rf100_v4`, Slots 200–299, Slot-Load + Readback):
  200 Zeilen, **196 gescort**, 4 stumm (A050, A097 — beide Noten).
  **mean 70,7**, Median 72,0, Range 28,0–**97,8**.
- **Entwicklung:** v2 51,1 → v3 67,0 → **v4 70,7**. Gegen v3 auf 98 Sounds
  **+3,8**, 53 besser / 28 schlechter.
  - Größte Gewinne: A053 44,6→84,9, A025 57,1→90,1, A020 32,2→62,3,
    A024 39,1→65,0, A035 64,4→88,2.
  - Größte Verluste: A015 68,0→48,6, A003 87,8→69,6, A026 67,9→54,7,
    A061 59,2→47,5 (teils Messstreuung bei sehr leisen/percussiven Patches).
  - Die Semitone-Ziele: A020 +30, A024 +26, A023 +8.
- **Entropy** (n=98): H(y)=2,83 bits; `spec_mad_db` zirkulär (IG 1,74);
  partielle IG: `spec_dtw` 0,390, `env_dtw` 0,584.
- **Retrain** (`--target score`, v4-Labels): n=98, MAE 11,05, RMSE 13,26,
  **R² −0,234 / R²_cv 0,070** → **nicht geshippt**. `models/prognose_rf.pkl`
  bleibt v2 (MAE 10,47, R² 0,064/0,132). Die besseren Labels sind noch weniger
  aus den Blofeld-Parametern vorhersagbar; die Restfehler dominieren.
- **Stille-Fälle:** A014/A026/A052/A070/A072 waren im Lauf zeitweise stumm.
  Kein Fix-Regress: mit zurückgesetzten Slots genauso laut/leise. Ursache ist
  das Messfenster (0,35 s Pre-Roll) bei Patches mit Amp-Sustain 0 und
  zu kurzem Iridium-Decay; A072 zusätzlich mit Attack 0,72.
- **Offen:** Hüllkurven-Zeitabbildung kalibrieren (Decay/Attack), Messprotokoll
  für Sustain-0-Patches (ab Note-On aufnehmen), Ausreißer A015/A061 prüfen.

## 2026-11-22 — Hüllkurven: Form passt mit RC, Zeiten sind der größere Fehler

- **Kurvenform (synthetisch, sauberer Test-Patch, normierte Hüllkurve):**
  - Decay: Blofeld-Form ≈ **RC** (RMS-Diff 0,034 gegen 0,122 Lin / 0,209 Exp).
  - Attack: **RC** am nächsten (0,07 gegen 0,105 Lin, 0,63 Exp).
  - Release: bei gleichem Norm-Wert passte Lin formal besser (0,114), aber die
    Dauer war nicht angeglichen → nicht belastbar.
- **Echte Sounds (A/B Lin vs. RC, alle Amp/Filter-Kurven):**
  A003 +1,3 · A016 **−4,8** · A053 −0,4 · A057 +3,8 · A070 +1,4 → Mean **+0,3**,
  also score-neutral. Die Form allein reicht nicht; die **Zeitabbildung** ist
  der Hebel.
- **Zeiten:** Blofeld Attack raw 64 ≈ 0,19 s, raw 96 ≈ 1,4 s. Iridium Attack
  norm 0,5 ≈ 1,18 s (RC, -10-dB-Schwelle) — der aktuelle lineare Normwert ist
  damit rund **6× zu langsam**. Das erklärt die stummen percussiven Patches
  (A014/A026/A052/A070), deren Klang vor dem Messfenster tot ist.
- **Messhürde:** Der synthetische Sweep ist mit der lazy QUIR-Shell unzuverlässig
  (nicht-monotone Zeiten, Kommandos teils nicht rechtzeitig angewendet). Für eine
  belastbare Kalibrierung muss nach jedem `set-param` ein Readback verifiziert
  werden; Skripte: `scripts/calib_envelope.py`, `scripts/calib_envelope2.py`.

### Hüllkurven-Zeiten kalibriert (Attack/Decay, 0.6.2)

- Messung mit sauberem Test-Patch (Blofeld SNDP, Iridium init + Filter-Bypass,
  Lin-Kurven) und konsistenter Metrik (Attack 10–90 %, Decay bis −20 dB).
  Anker (raw → Iridium-Norm):
  - Attack: 0→0,0 · 32→0,02 · 64→0,22 · 96→0,52 · 127→0,55
  - Decay:  0→0,0 · 32→0,29 · 64→0,35 · 96→0,58 · 127→0,60
  Die alte lineare Abbildung (raw/127) war im Attack bis ~3× zu langsam.
- A/B auf echten Sounds (nur Amp/Filter1-Attack/Decay geändert):
  **A003 +4,7, A016 +4,7**; A014/A026/A070 bleiben stumm (Messfenster, s. u.).
- **Kurven bleiben Lin:** RC passt zwar analytisch besser zur Form, aber ein
  früherer Nutzerbefund und der Score-A/B (nur +0,3) sprechen dagegen — vorerst
  keine Änderung.
- **Release bleibt linear** (unzuverlässig gemessen; Note-Off-Erkennung).
- **Stumme Percussive-Patches** (Sustain 0, kurzer Decay) sind ein
  Messprotokoll-Problem: Aufnahme ab Note-On statt 0,35 s davor.
- Neu konvertiert: `transfer/rf100_v5` (SD `rf500`, Slots 300–399).
