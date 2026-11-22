# Bloridium CLI – reference

Command: `bloridium` (after `pip install -e .`) or `python3 -m bloridium`.
Global flags: `--db PATH` (default: `$BLORIDIUM_DB` or `<repo>/bloridium.db`),
`--json` (JSON output where supported),
`--config PATH` (YAML config; default: `$BLORIDIUM_CONFIG` or `./bloridium.yaml`),
`--version`.

Exit codes: **0** ok · **1** error (e.g. location not in bank) · **2** hardware
unreachable (message with available MIDI ports on stderr).

## discover
```
bloridium [--json] [--config PATH] discover [--write] [--probe] [--json]
```
Scans the MIDI ports (mido/CoreMIDI) and the audio capture devices (`ffmpeg -list_devices`;
AVFoundation on macOS, ALSA on Linux) and shows the effective config.
`--probe` additionally sends a Universal Device Inquiry to every MIDI output port and shows
the identity replies (manufacturer `0x3E` = Waldorf, model `0x13` = Blofeld).
`--write` merges the discovered values into the YAML config
(`--config PATH` / `$BLORIDIUM_CONFIG` / `./bloridium.yaml`) — existing user edits are kept,
only empty keys are filled (ports + audio device; channels/samplerate stay manual).
Precedence at runtime: user YAML > discovered > built-in defaults.
See [`CONFIG.md`](CONFIG.md) for the full annotated `bloridium.yaml` reference,
a step-by-step discovery example and troubleshooting.

## status
```
bloridium status [--audio]
```
Lists MIDI ports; per synth (Blofeld, Iridium): connection, channel, identity reply.
`--audio` additionally: plays C4 and measures the level on the Scarlett (ex step1).

## bank – Blofeld bank manager
```
bloridium bank read A [B ...] [--only A043,A044] [--banks-dir DIR]
bloridium bank import DIR [--banks-dir DIR]      # offline from blofeld_sndd_*.bin/.hex
bloridium bank list [BANK] [--grep PAT] [--json]
bloridium bank show A043 [--json]
```
- `read`: reads all 128 locations of the bank(s) via SysEx (SNDR/SNDD); per sound
  a stable copy under `dumps/banks/<Bank>/<LOC>.bin` + upsert in the DB.
  Individual errors don't abort (timeout 4 s, 2 retries, collective report at the end).
- `import`: parses existing dump files offline into the DB.
- `list`: marks sounds whose `.bin` file is missing with `MISSING`.
- `show`: parsed parameters (name, category, all SDATA parameters).

## convert – Blofeld -> Iridium (.qpat)
```
bloridium convert A043 [--dump FILE.bin] [--out DIR] [--template FILE.qpat]
```
Reads the sound live (Blofeld must be connected, Single Mode, channel 5) or offline via
`--dump`; writes `<LOC>_<Name>.qpat` (default: `transfer/`, SD-safe name, e.g.
`A043_SH_Power.qpat`) and records the conversion incl. `unmapped` list in the DB.
Afterwards prints the import instructions for the Iridium (USB stick/SD ->
Load>Actions>Import).

## ab – A/B sound measurement (Scarlett In3/4 vs In5/6)
```
bloridium ab [--note 36] [--dur 3.0] [--label L] [--sound A043] [--rec-dir DIR]
bloridium ab --list [--sound A043] [--json]
bloridium ab --diff ID1 ID2
```
Measurement: All Notes Off (CC123) on all 16 channels of both synths, then a note on
both, record all 20 channels; saves `.npy` + `_report.json` under
`recordings/` and the run in the DB (with `sound_location`). `--diff` shows the
8 log bands of both runs side by side.

## qpat – .qpat files
```
bloridium qpat info FILE.qpat [--register]
```
Parses the file, shows name/creator/categories/version/parameters, does a
roundtrip check (parse->build->parse, parameters must be identical) and with
`--register` adds the file to the `qpats` table (source = directory name,
e.g. `export-001` for the 41 presets in `dumps/export-001/`).

## edit – Iridium editor (.qpat)
```
bloridium edit FILE.qpat --list [--grep PAT] [--json]
bloridium edit FILE.qpat --show KEY
bloridium edit FILE.qpat --set KEY=0.5 [--display "Text"] [--save OUT.qpat]
bloridium edit FILE.qpat --diff OTHER.qpat
```
- Values are qpat-normalized **0..1** (clamped); `--display` sets the
  display string. Without `--save`, **in-place** is written; beforehand
  `FILE.qpat.bak` is created automatically. `--save OUT` writes to OUT instead.
- Works with any `.qpat` – also the reference presets in
  `dumps/export-001/`.
- `--diff` lists only the differing parameters of both files.

## cc – live CC on the loaded patch (re-tuning without re-import)
```
bloridium cc --list [--grep PAT]              # CC table (from docs/midi-maps/*.csv)
bloridium cc "Filter1 Reso" 100 [--part 2]    # resolve name -> CC, send (default Part 1 = MIDI ch6)
bloridium cc --raw 9 64                       # raw CC number
bloridium cc ... --synth blofeld              # Blofeld (Single Mode, MIDI ch5)
```
- Names case-insensitive; a unique substring is enough, ambiguous -> list + exit 1.
- **NRPN-only parameters** (e.g. Iridium `Filter1 Cutoff`) have **no CC** – NRPN is
  ignored on the Iridium -> use qpat re-import or MIDI Learn on the device for those.
- ⚠️ **CC7 = Output Level by default (0 = silent!)** – `cc --raw 7 0` is refused without
  `--force`. A loaded `.mimap` may reassign CC7 (the `rdb` map maps it to Filter1 Amount).

## explore – OS4 pid exploration on the Iridium (NRPN capture)
```
bloridium explore [--essential] [--grep PAT] [--only-cc 0,2,7]
bloridium explore --list [--json]
bloridium explore [--csv PATH] [--log PATH] [--port NAME] [--channel N] [--listen S]
```
- Interactive session: shows the next open parameter from
  `docs/midi-maps/iridium_os4_cc_list.csv` (essential first, then usage %),
  you turn the panel, Enter -> decode NRPN (pid = CC99/98, value = CC6/38, 14-bit)
  and book: CSV (`os4_verified=ja`, `pid_os4`, min/max/last; one-time `.bak`) +
  `recordings/explore_log.jsonl`. Deviation from the rdb pid -> **DEVIATION**.
  `s` = skip without booking, `q` = quit (resumable – the CSV is the state).
- **Read-only** – sends no MIDI. On the Iridium: Global > MIDI = on, Send NRPN = on,
  Part 1 active (default `--channel 5` = ch6).
- Iridium panel NRPN has so far only been seen via the **USB endpoints** (ch6);
  Launchpad DIN delivers no panel NRPN (check 2026-11-12, see
  `docs/research/STATUS.md`) -> on an empty capture plug in the Iridium USB briefly and
  set `--port "Iridium Keyboard (MIDI 2.0) MIDI 2.0"`.
- `--list` shows the verification status of all 115 CCs (needs no MIDI).

## sim – similarity score Blofeld<->Iridium

```
bloridium sim compare --npy A.npy B.npy
bloridium sim compare --live [--note 72] [--blofeld A043] [--iridium-slot 113]
                       [--embed] [--llm] [--profile] [--specdiff off|dsp|vision]
```
- Offline from `.npy` recordings, or live measurement; `scripts/sim_compare.py` and
  `scripts/sim_live.py` wrap the same logic.
- Score 0–100 (`score_version` 2): 70 % level-aligned band deviation
  (`1 − spec_mad_db/20 dB`) + 30 % envelope DTW, plus band deltas. The v1 cosine is kept
  as `spec_cos`. Log: `recordings/sim_log.jsonl`.
- `--iridium-slot` is metadata only — select the patch beforehand via PC.
- CC/pid resolution: `bloridium/ccmap.py` (`docs/midi-maps/iridium_pid_map.csv`).

## prognose – predicted conversion quality

```
bloridium prognose train --log recordings/sim_log.jsonl --dumps dumps [--target score]
bloridium prognose predict A043
bloridium prognose entropy --log recordings/sim_log.jsonl --dumps dumps
```
Random forest over Blofeld SNDD parameters. Training skips v1 log rows by default
(`--min-score-version 2`). The prediction is a **rough** indication, not a guarantee
(see `docs/FINDINGS.md`).

## specdiff – interpret the spectral difference

```
bloridium specdiff --wav A.wav B.wav [--png out.png] [--no-vision]
bloridium specdiff --log recordings/sim_log.jsonl --recordings recordings/ [--only A043] [--write]
```
DSP features (numpy-only) plus an optional local vision model; labels severity, spread,
temporal pattern and affected bands.

## Tests
```bash
pip install -e ".[dev]"
python3 -m pytest            # offline suite; no MIDI/audio hardware required
```
