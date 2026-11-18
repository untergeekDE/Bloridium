# Interface Discovery + User YAML Config Plan

**Goal:** Make Bloridium hardware-agnostic: a `discover` routine that scans MIDI ports and audio devices, and a user-editable `bloridium.yaml` in the project root that stores the effective configuration.

**Architecture:** New modules `bloridium/config.py` (load/merge/save YAML over built-in defaults; search order `--config` > `$BLORIDIUM_CONFIG` > `./bloridium.yaml`) and `bloridium/discover.py` (MIDI port listing + optional identity probe, audio device listing via `ffmpeg -list_devices` with AVFoundation/ALSA parsers, merge that preserves user edits: precedence user YAML > discovered > built-in defaults). CLI gains `bloridium discover [--write] [--probe] [--json]` plus a global `--config`; `midi.connect()`, `audio.record()` and `status` read the YAML when present, else fall back to today's hardcoded defaults (backward compatible). New dependency: `pyyaml`.

**Tech Stack:** Python 3.10+, mido/python-rtmidi, PyYAML, ffmpeg (AVFoundation on macOS / ALSA on Linux), pytest.

**Spec:** User request 2026-11-18 ("routine for discovering MIDI and Audio interfaces + user-modifiable YAML in the project directory"); design approved in conversation (user YAML sketch).

## Tasks

### Task 1: config module (TDD)
**Files:** Create `tests/test_config.py`, `bloridium/config.py`; create `bloridium.yaml` in repo root; add `pyyaml>=6` to `requirements.txt` + `pyproject.toml`.
- [x] RED: tests fail (module missing) — `load_config` defaults, deep-merge of user YAML, `find_config_path` precedence (explicit > env > cwd), `save_config` round-trip, `midi_ports`/`audio_settings` accessors, invalid-YAML error.
- [x] GREEN: implemented `config.py`; `pytest tests/test_config.py -q` passes (22 tests incl. discover).

### Task 2: discover module (TDD)
**Files:** Create `tests/test_discover.py`, `bloridium/discover.py`.
- [x] RED: `parse_avfoundation_devices`/`parse_alsa_devices` on sample ffmpeg output, `discover_midi` with monkeypatched mido, `discover_audio(api=..., runner=fake)`, `parse_identity_reply`/`probe_port`, `build_config` precedence (user > discovered > defaults), `discover(write=True)` creates YAML.
- [x] GREEN: implemented `discover.py`; live smoke test on the dev Mac found Blofeld/Iridium ports + Scarlett 18i8.

### Task 3: wiring
**Files:** Modified `bloridium/midi.py` (`ports_from_config`/`fallback_out_ports`, `connect(config_path=...)`; `DEFAULT_PORTS` now derived from `config.DEFAULTS`), `bloridium/audio.py` (`settings(config_path=...)`; `record`/`record_wav` resolve device/samplerate/raw_channels from config when not given), `bloridium/workflow.py` (`_ckw` guard keeps old call signatures when no config given), `bloridium/cli.py` (`discover` subcommand, global `--config`, `status` shows config source, explore port from config), README/docs.
- [x] `bloridium discover --json` works live; `bloridium status` unchanged without YAML.
- [x] Full suite green: `python3 -m pytest tests -q` → 301 passed, 1 skipped (tests/test_wiring.py added, 7 tests).

## Review Focus
- Precedence rule (user YAML > discovered > defaults) must never silently drop a user edit.
- No YAML present → behavior identical to today (all existing tests pass unmodified).
- Forbidden: no mention of any agent skill for Iridium control in tracked files; vendor SysEx wording stays neutral.
