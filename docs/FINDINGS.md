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
