---
name: bloridium
description: >-
  Use when working with the Bloridium workflow in this repo: reading sounds from a
  Waldorf Blofeld over documented SysEx (SNDR/SNDD/SNDP, official spec v1.04),
  converting them to Waldorf Iridium .qpat files, transferring them via USB stick/SD
  card, selecting sounds with MIDI program change (Favorites bank), tweaking
  parameters live over MIDI CC, and measuring Blofeld-vs-Iridium similarity (A/B
  recordings over an audio interface, sim score 0-100, specdiff, prognosis).
  Triggers: "Blofeld sound auf Iridium", "konvertieren", "convert A043", "A/B messen",
  "sim score", "PC sweep", "Upload-Paket", "qpat edit", "sim compare".
  Covers only documented interfaces: Blofeld SysEx spec, Iridium MIDI CC/PC/notes and
  .qpat files - the Iridium has no documented SysEx.
---

# Bloridium — Blofeld → Iridium conversion & measurement

Convert sound programs from a **Waldorf Blofeld** to a **Waldorf Iridium** (`.qpat`),
transfer them via USB stick/SD card, and measure how close the result sounds to the
original (A/B recording through an audio interface + similarity score 0–100).
Run all commands from the repo root.

## Install & version

- `pip install -e ".[dev]"` (`requests` is a core dependency); `bloridium --version`
- macOS: `brew install ffmpeg` (audio capture) and build the MIDI 2.0 helper:
  `cd tools && clang -framework CoreMIDI -framework Foundation -o ump_send ump_send.m`
- Without the package: `pip install -r requirements.txt` + the two steps above, then
  `python3 -m bloridium ...` or the scripts in `scripts/`.
- Exit codes: **0** ok · **1** error · **2** hardware unreachable (lists the available
  MIDI ports on stderr).
- Global flags: `--db PATH` (default `$BLORIDIUM_DB` or `./bloridium.db`), `--json`,
  `--config PATH`.

## Configuration & hardware check

- All hardware-dependent settings live in `bloridium.yaml` (full reference:
  `docs/CONFIG.md`). Precedence: `--config PATH` > `$BLORIDIUM_CONFIG` >
  `./bloridium.yaml` > built-in defaults. MIDI channels are 0-based (Blofeld Global
  Channel 5 → 4; Iridium Part 1 = ch 6 → 5). Audio channels are 0-based input numbers
  of the audio interface.
- Discover once: `bloridium discover [--probe] [--write]` — scans MIDI ports and audio
  capture devices; `--probe` sends a Universal Device Inquiry to every output port
  (Waldorf = manufacturer `0x3E`, Blofeld = model `0x13`); `--write` merges the
  findings into the YAML (your own edits are kept, only empty keys are filled).
- Check the wiring: `bloridium status [--audio]` (with `--audio`: plays C4 and
  measures the level on the configured inputs).
- Reference rig: Blofeld on audio inputs 3/4 (MIDI ch 5), Iridium on inputs 5/6
  (Parts 1–4 = MIDI ch 6–9), 48 kHz, audio interface e.g. Focusrite Scarlett 18i8.

## Interfaces and limits

- **Blofeld — SysEx per the official spec** (`docs/manuals/Blofeld_sysex_v1_04.txt`):
  `SNDR` sound request → `SNDD` dump (`F0 3E 13 DEV 10 BB NN <383 B SDATA> CHK F7`),
  `SNDP` single parameter change (`F0 3E 13 DEV 20 LL HH PP XX F7`, parameter index
  0..382), plus the Universal Device Inquiry.
- **Iridium — no documented SysEx application layer.** Patches reach the device only as
  **`.qpat` files** on a USB stick / SD card (on the device: `Load > Actions >
  Import`). Control from a computer is possible via **MIDI CC** (requires a MIDI
  map uploaded to the device — e.g. `docs/midi-maps/iridium_rdb.mimap` via
  `Global > MIDI > Mappings > Load`, or MIDI Learn on the panel), **program change**
  (selects within the Favorites bank only) and **notes**. Incoming NRPN is *ignored*
  by the Iridium; the panel only *sends* NRPN (see `docs/midi-maps/README.md`).
- **OS 4.1.0b2 accepts private device-side tooling that is not part of this project.**
  Some archived measurements were taken with it; it is not a public interface and not part
  of the normal workflow. Never change device settings (Global menu, MIDI configuration, …)
  on either unit without asking first.

## Workflow: convert → upload → select → measure → tweak

1. **Read Blofeld sounds** (live, SysEx): `bloridium bank read A [B ...] [--only
   A043,A044]` → stable copies in `dumps/banks/<Bank>/` + upsert in the SQLite DB.
   Offline from existing dump files: `bloridium bank import DIR`.
   Inspect: `bloridium bank list [BANK] [--grep PAT] [--json]`,
   `bloridium bank show A043 [--json]`.
   Set a single Blofeld parameter (SNDP, spec v1.04) via the Python API:
   ```python
   from bloridium import midi
   from bloridium.blofeld_dump import build_sndp  # F0 3E 13 DEV 20 LL HH PP XX F7
   with midi.connect("blofeld") as blo:
       blo.send_sysex(build_sndp(param_index=105, value=64))  # index 0..382, spec 3.1
   ```
2. **Convert** to the Iridium format: `bloridium convert A043 [--dump FILE.bin]
   [--out DIR] [--template FILE.qpat]` → `transfer/<LOC>_<Name>.qpat` (e.g.
   `A043_SH_Power.qpat`) + DB entry;
   prints the import instructions for the device. `--dump` works fully offline.
   Converted file names are SD-safe by construction (`bloridium.qpat.sd_filename`:
   no spaces, only `[A-Za-z0-9-_.]`) — copy them to the stick **unchanged**
   (`cp transfer/*.qpat /Volumes/<STICK>/`), never rename them to names with spaces.
3. **Upload**: FAT32 USB stick / SD card → on the Iridium `Load > Actions > Import`
   → into a Favorites set (current assignment: `docs/IRIDIUM-FAVORITES-MAP.md`).
4. **Select** the sound for playback/measurement via program change into the active
   Favorites set: the display shows `MIDI n`, mido PC = n − 2 (e.g. A043 "MIDI 113" →
   PC 111). On the **Blofeld** send CC0 = 0 (Bank A) before each PC, PC = location − 1
   (A043 → PC 42). Single selection from the computer via the Python API:
   ```python
   from bloridium import midi
   with midi.connect("blofeld") as blo, midi.connect("iridium") as irr:
       blo.control_change(0, 0)      # CC0 = 0: Bank A on the Blofeld
       blo.program_change(42)        # A043 = location - 1
       irr.program_change(111)       # Favorites: mido PC = display "MIDI n" - 2
   ```
   Batch sweep over all converted sounds: `scripts/sim_sweep_pcs.py`
   (mapping in `DEFAULT_MAP` inside the script). Never send CC0/CC32 to the
   **Iridium** when a `.mimap` with parameter assignments is loaded — there they are
   parameters, not bank select; choose the Favorites set on the device.
5. **Tweak live over CC** (on the loaded patch):
   `bloridium cc --list [--grep PAT]`, `bloridium cc "Filter1 Reso" 100 [--part 2]`,
   `bloridium cc --raw 9 64`, `--synth blofeld`. Names come from the midi-guide CSVs in
   `docs/midi-maps/` (`iridium_midi_guide.csv`, `blofeld_midi_guide.csv`),
   case-insensitive unique substring. NRPN-only parameters (e.g. `Filter1 Cutoff`
   without a matching `.mimap`) have **no CC** → edit the `.qpat` and re-import, or
   use MIDI Learn on the device. To find out which CC drives which parameter:
   `bloridium explore` (read-only — it captures the panel's outgoing NRPN and books it
   into `docs/midi-maps/iridium_os4_cc_list.csv`; `--list` shows the status of all
   115 CCs without MIDI).
6. **Edit `.qpat` files offline**: `bloridium qpat info FILE.qpat [--register]`,
   `bloridium edit FILE.qpat --list [--grep osc1]`, `--show KEY`,
   `--set KEY=0.5 [--display "..."] [--save OUT.qpat]`, `--diff OTHER.qpat`.
   Values are qpat-normalized 0..1; without `--save` the file is edited in place and a
   `.bak` backup is kept automatically.

## Measurement: A/B recording + similarity score

- A/B run (both synths play the same note, all channels recorded):
  `bloridium ab --sound A043 --label run1 --note 36 [--dur 3.0] [--embed] [--llm]`
  → `.npy` + `_report.json` in `recordings/`, run in the DB; afterwards
  `bloridium ab --list [--sound A043] [--json]`, `bloridium ab --diff ID1 ID2`.
- Similarity score: `bloridium sim compare --npy A.npy B.npy` (offline) or
  `bloridium sim compare --live --note 72 --blofeld A043 --iridium-slot 113`
  (the slot is log metadata — select the sound beforehand via PC, see step 4;
  scripts: `scripts/sim_compare.py`, `scripts/sim_live.py --param "Filter1 Reso"
  --value 90`, `scripts/sim_sweep_pcs.py --notes 60,72`). Every run is appended to
  `recordings/sim_log.jsonl`.
- **The score is v2** (`score_version: 2` since v0.4.0): 70 % spectral similarity
  (`1 − spec_mad_db / 20 dB`, level-aligned log-spectrogram bands) + 30 % envelope DTW
  → 0–100, plus per-band dB deltas. The old cosine (`spec_cos`) is kept as a
  diagnostic only. Log rows without `score_version` are v1 and are skipped by
  `prognose train` by default (`--min-score-version 2`).
- Interpret the remaining difference: `bloridium specdiff --wav A.wav B.wav`, or batch
  over the log: `bloridium specdiff --log recordings/sim_log.jsonl --only A043
  [--write] [--no-vision]`.
- Prognosis (how good will the conversion be?): `bloridium prognose predict A043`,
  retrain with `bloridium prognose train [--target score]`. **Rough indication only** —
  random forest with low R² on held-out data (see `docs/FINDINGS.md`).

## Safety rules (hard-earned)

- **Ask before changing any setting on either device.**
- Before every measurement: All Notes Off (CC123 = 0) on all 16 channels of both
  synths (the measurement commands do this themselves).
- **CC7 = Output Level on the Iridium by default (0 = silent!)** — `bloridium cc --raw
  7 0` is refused without `--force`. A loaded `.mimap` can reassign CC7; check the map.
- Trigger only **Part 1** of the Iridium (ch 6), monophonic like the Blofeld; never
  sound several parts at once (several notes at once distort the score).
- Note 72 (C5) is the best comparison octave (scores ~95+); low notes show envelope
  deviation.
- Bipolar parameters (e.g. matrix amounts) are centered at 0.5 in `.qpat` files;
  velocity→volume is mapped as `0.5 + 0.5·norm`.
- The Blofeld must be in **Single Mode** with the configured Global Channel.

## References

- `README.md` (install + workflow), `docs/CLI.md` (full command reference),
  `docs/CONFIG.md` (`bloridium.yaml`), `docs/IRIDIUM-FAVORITES-MAP.md` (PC/Favorites),
  `docs/MAPPING-MASTER.md` (mapping status),
  `docs/midi-maps/README.md` (CC lists, `.mimap` loading, NRPN), `docs/FINDINGS.md`.
  Dated measurements and historical plans are archived in `docs/research/`.
- Manuals: `docs/manuals/Blofeld_sysex_v1_04.txt` (Blofeld SysEx spec),
  `docs/manual-text/iridium_os4_som2.txt` (Iridium OS4 manual text)
- Sample-pack conversion: `scripts/build_cp70_iridium.py <zip>` (path also via
  `$BLORIDIUM_CP70_ZIP`; default `./CP70-Exs24-v1.2.zip`)
