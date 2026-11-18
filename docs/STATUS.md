# STATUS – Bloridium (handoff for the new session; supersedes the earlier handover notes, see docs/HANDOVER-2026-11-*.md)

As of: 2026-11-08. Everything below was empirically verified on the real setup (Mac + Scarlett 18i8 + Blofeld + Iridium Keyboard OS4/SOM2), unless explicitly marked as "open".

## 1. Goal

Transfer synth programs **Blofeld -> Iridium**: read dumps, compare parameter structures, build the mapping, transfer the sound, measure the sound via audio (Scarlett In3/4 vs In5/6) and align it via detailed corrections.

## 2. Hardware & cabling (verified)
- **Blofeld** (FW 1.24, SL license): USB -> CoreMIDI port `Blofeld`, **channel 5**, **SINGLE MODE active** (only ch5 responds; mode only changeable on the device via Shift+Sound/Multi). Audio -> Scarlett **In 3/4** (c2/c3), peak ~ -17 dBFS.
- **Iridium Keyboard** (OS 4, SOM2): USB -> endpoints `Iridium Keyboard (MIDI 2.0) MIDI 2.0` (primary; MIDI 1.0 bytes are delivered as UMP) and `... Synth` (receives nothing). Parts 1-4 on **channels 6-9**. Audio -> Scarlett **In 5/6** (c4/c5), peak ~ -27 dBFS. Current preset after reboot: **0039 "Stepping Out" (Split!)** – ch6 note36 ≈ -26 dBFS, note60 ≈ silent (split at C4), ch7 note60 ≈ -36.
- **Scarlett 18i8**: 20 inputs @ 48 kHz via ffmpeg/AVFoundation (`bloridium/audio.py`).
- Launchpad Pro 3 only as fallback (DIN chain, currently switched off).
- **Important**: before channel scans send All Notes Off (CC123) on all channels + wait for release. Never change hardware settings on the device without asking.

## 3. Device behavior – key findings (all documented in docs/FINDINGS.md + docs/sources/)
- **Blofeld**: full SysEx support over USB. `F0 3E 13 00 <cmd> …` — SNDR(0x00)->SNDD(0x10), SNDP(0x20) parameter change per index 0..382, GLBR(0x04)->GLBD. Official spec: `docs/manuals/Blofeld_sysex_v1_04.pdf`. SNDD = `F0 3E 13 DEV 10 BB NN <SDATA 383B> CHK F7`, CHK = sum(SDATA)&0x7F. Location BB NN: `00 00..` = A001.., `7F 00` = edit buffer (may NOT contain the selected sound! e.g. edit buffer = "JP Wannabe" while A043 "SH Power" was selected -> always request with location, e.g. A043 = `00 2A`).
- **Iridium**: **NO SysEx layer** (no reply to anything – bytestream/UMP sysex7+8, both endpoints, model/device sweeps; documented by the rolfw quote 2019 + forums + changelogs, dossier `docs/sources/rolfw_no_sysex_dossier.md`). Patch transfer only **file-based as .qpat** via USB stick/SD (Load>Actions>Import/Export). **No USB drive mode on the computer** (rolfw's idea never implemented; the Mac only sees MIDI endpoints).
- **Iridium MIDI**: channel MIDI (note/CC/PC) works. PC loads only Favorites. CC list: 115 CCs (CC2-116), `docs/midi-maps/iridium_midi_guide.csv`. **CC7 = Output/Main Level (0 = silent!)** – not listed in the CSV. Incoming NRPN are ignored. F1 cutoff has no CC; mod matrix/filter type/coarse pitch likewise -> prefer the qpat path.
- **.qpat format** (fully reverse-engineered, verified against official Waldorf files + autosamplerT): 512-B header (magic `b4 ec 33 00` = u32 3402932, u32 version, name/creator/desc + 4x category each char[32], u16 param count, 16x resource header a 12 B, 2nd layer u16+u16+u32, u8 instrument, pad 0x200), then **68-B records**: `float32 LE value (0..1 normalized) | char[32] name | char[32] display`, then sample maps (tab-separated). Parser+writer: `bloridium/qpat.py` (roundtrip-tested). Enum tables (OscType, WF shape, filter, FX …) + 2168 key names: `bloridium/qpat_map.py` + `docs/refs/qpat/`.

## 4. Tools

### Library `bloridium/`
- `config.py` – **user-editable YAML config** (`bloridium.yaml`, precedence: `--config` > `$BLORIDIUM_CONFIG` > `./bloridium.yaml` > `DEFAULTS`): `load_config`/`load_raw_config`/`save_config`/`find_config_path`, `midi_ports`, `fallback_out_ports`, `audio_settings`, `merge`.
- `discover.py` – **interface discovery**: `discover_midi` (mido ports), `probe_port`/`parse_identity_reply` (Universal Device Inquiry), `discover_audio` + `parse_avfoundation_devices`/`parse_alsa_devices` (ffmpeg `-list_devices`), `build_config` (user YAML > discovered > defaults), `discover(write=...)`; CLI: `bloridium discover [--write] [--probe] [--json]`.
- `midi.py` – `connect("blofeld"|"iridium", config_path=...)`, `Synth` (note_on/off, control_change, program_change, pitchwheel, send_sysex, device_inquiry, receive), `ports_from_config`/`fallback_out_ports` (YAML over `DEFAULT_PORTS`), `list_ports`/`match_port`.
- `audio.py` – `record(duration, channels)` (channels=None -> all raw channels, shape (raw,samples)), `record_wav`, `measure` (rms/peak dBFS), `play_and_measure`, `settings(config_path=...)` (YAML over built-in `DEVICE`/`SAMPLERATE`/`CHANNELS = {blofeld:(2,3), iridium:(4,5)}`).
- `waldorf.py` – SysEx primitives `build_sysex/parse_sysex/identity_reply_info` (Blofeld ID 0x13).
- `blofeld_dump.py` – **Blofeld SNDD/SNDP per spec**: SDATA table 0..382 + value tables 4.1-4.18/FX 5.x, `checksum`, `parse_sndd` (-> name, params with labels), `build_sndd`, `build_sndp`, `build_sndr(bb,nn)`.
- `qpat.py` – **.qpat parser+writer**: `parse_qpat(data)/load(path)` -> name/creator/categories/params{name:(value,display)}; `build_qpat(name, params, …)`.
- `qpat_map.py` – **Blofeld-SNDD -> qpat keys**: `blofeld_to_qpat_params(parsed) -> (overrides, unmapped)`, enum tables, `apply_to_template(template, overrides, name)`.
- `mapping.py` – CC path: `blofeld_to_iridium(parsed) -> (msgs, unmapped)`, `load_iridium_cc()` (CSV -> name->CC). Beware CC7=Output Level.
- `midi2.py` – UMP helpers + `UMPOut` via `tools/ump_send` (CoreMIDI endpoint names WITHOUT prefix: `MIDI 2.0`, `Synth`!).

### Scripts `scripts/`
- `step1_verify_connection.py` – connection + measure sound (Blofeld ch5, Iridium ch6).
- `check_blofeld_mode.py`, `scan_ports.py`, `scan_channels.py`, `monitor_live.py` – diagnostics.
- `step2_read_blofeld_dump.py [A043|edit]` – read SNDD -> `dumps/blofeld_sndd_<loc>_<ts>.bin/.hex`.
- `step2_parse_blofeld_dump.py [file]` – decode dump (parameter list).
- `step2_probe_iridium_sysex*.py`, `step2_probe_iridium_devsweep.py`, `step2_probe_iridium_ump_min.py` – Iridium SysEx probes (all negative; documentation why in FINDINGS).
- `step3_transfer_qpat.py [A043]` – **Blofeld-SNDD -> `transfer/<name>.qpat`** (template `docs/refs/qpat/template_waveform.qpat` + mapping).
- `step3_transfer_sound.py [A043] [--note 36]` – CC path (approximate; watch the CC7 trap).
- `step4_measure_ab.py [--note 36] [--dur 3] [--label X]` – **A/B measurement**: note on both synths, record all 20 channels, Blofeld In3/4 vs Iridium In5/6: peak/rms/centroid + 8 log bands (dB delta) + JSON report -> `recordings/`.
- `sim_checkpoint.py [--only A001] [--notes 36,48,60,72] [--wheel 0,50,100] [--dur 2.0] [--full-all] [--no-wait]` – **checkpoint measurement round** (2026-11-17): all 9 presets from `DEFAULT_MAP` in manual-panel mode (panel prompt per preset: set 6 PC per `sim_sweep_pcs.DEFAULT_MAP`), per preset 4 notes (C2-C5) x 3 wheel levels = 12 measurements; one JSONL entry per combination in `sim_log.jsonl` (`meta` mode="checkpoint" + note/wheel_pct), WAVs level-aligned `ab_<LOC>_<ts>_n<note>_w<pct>_{blo,irr}.wav`, embed for all combinations, llm/profile only on the reference (wheel 0 + note 72), wheel reset after each preset, summary pivot at the end; exit 1 on a silent measurement. Spec/plan: `docs/superpowers/specs/2026-11-17-sim-checkpoint-design.md`, `docs/superpowers/plans/2026-11-17-sim-checkpoint.md`; research status multi-dim/embeddings: `docs/RESEARCH-2026-11-17-sim-multidim.md`.

### Tools
- `tools/ump_send(.m)` – raw UMP packets to a CoreMIDI endpoint (endpoint names: `MIDI 2.0`, `Synth`).

## 5. Data / artifacts
- `dumps/` – Blofeld SNDDs (incl. `blofeld_sndd_A043_*.bin` = "SH Power").
- `transfer/SH Power_A043.qpat` – **finished transfer** (80 qpat parameters mapped) for import on the Iridium.
- `recordings/` – A/B recordings (.npy) + reports (.json).
- `docs/FINDINGS.md` – **all empirical findings** (must-read!).
- `docs/MAPPING.md` – CC mapping draft Blofeld->Iridium.
- `docs/manuals/` – `Blofeld_sysex_v1_04.pdf` (+txt) official; manuals local in `~/Nextcloud/AAA Musik/Manuals` (Blofeld.pdf, iridium_desk_kb_manual_os3.pdf, Iridium_os4_SOMv2_manual.pdf), extracted as text in `docs/manual-text/`.
- `docs/midi-maps/` – CC CSVs (midi.guide): blofeld, iridium.
- `docs/refs/` – official Waldorf soundset zips (Quantum_Factories.zip 1.8 GB, additional_patches_IKB.zip 158 MB) + extracted `.qpat` (incl. `template_waveform.qpat`).
- `docs/sources/` – rolfw "no SysEx" dossier + raw snippets (Gearspace quotes, Wayback CDX).

## 6. Workflows (copy-paste)

```bash
cd /Users/jan/Code/Bloridium
# read + parse Blofeld dump
python3 scripts/step2_read_blofeld_dump.py A043
python3 scripts/step2_parse_blofeld_dump.py dumps/blofeld_sndd_A043_*.bin

# create the transfer file for the Iridium
python3 scripts/step3_transfer_qpat.py A043     # -> transfer/SH Power_A043.qpat
# on the Iridium: insert USB stick, Load>Actions>Import, choose slot, load

# A/B measure (Blofeld ch5 vs Iridium ch6, note 36 because of the split)
python3 scripts/step4_measure_ab.py --note 36 --label shpower

# read an Iridium dump: on the device Load>Actions>Export to stick -> .qpat
python3 bloridium/qpat.py /Volumes/STICK/export-xxx/iridium/....qpat
```

## 7. Plan for the new session (implementation)
1. Import `transfer/SH Power_A043.qpat` on the Iridium (USB stick, Load>Actions>Import) -> load.
2. `step4_measure_ab.py --note 36 --label shpower` -> analyze band deltas (currently with a foreign patch: Iridium +7 dB in high bands, +8 dB 82-166 Hz).
3. Close mapping gaps in `bloridium/qpat_map.py` (unmapped list from step3): osc FM/PWM/keytrack/bend range, mod matrix source/dest (Matrix* keys), filter drive/pan/routing, wavetable table/position, arp, LFO shapes. Derive enum values from `docs/refs/qpat/*.qpat`.
4. Detailed-correction loop: fine-tune qpat keys (values 0..1) -> rewrite -> import -> measure -> repeat.
5. Verify Iridium dump (readback): export on the device -> parse with `qpat.py` -> compare keys with Blofeld SNDD (structure comparison 3 OSC / 2 filter / mod matrix).
6. Then transfer further sounds (bank A) systematically.

## 8. Open points
- Watch the Iridium split (preset 0039): A/B with note 36 on ch6, or load a single patch on the device.
- CC path only as an approximation; the qpat path is primary.
- Sample-based patches (Particle/Resonator) need sample maps in the qpat (resources 4-6) – not covered yet.
