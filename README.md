# Bloridium

## Objective - what this is about

Transfer sound programs (patches) **from the Waldorf Blofeld to the Waldorf Iridium synthesizer**.

An exact transfer is impossible, although those two synths are related and have a similar basic architecture, they are very different beasts. The conversion is therefore an **approximation**. 

To close the gap, Bloridium provides tools to **measure and track the differences** between the original and the converted sound (A/B recordings over a Focusrite Scarlett 18i8, similarity score 0–100 from log-spectrogram + envelope comparison) and to **optimise parameters** until the Iridium patch matches the Blofeld as closely as possible.

### Hardware

The test hardware used: 

- Macbook Air
- both synths connected directly via USB (**MIGHT CAUSE DIGITAL NOISE BY GROUND LOOP**)
- Focusrite Scarlett 18i8 Audio interface
- Blofeld on inputs 3/4 (MIDI channel 5), Iridium on inputs 5/6 (MIDI channels 6–9, Parts 1–4).

### Configuration: `bloridium.yaml`

All hardware-dependent settings live in the **user-editable `bloridium.yaml` in the project
directory**: MIDI port names + channels per synth, fallback port candidates, and the audio
device name, samplerate, raw channel count and per-synth input channels. Precedence:
`--config PATH` flag → `$BLORIDIUM_CONFIG` env var → `./bloridium.yaml` → built-in defaults
(so everything works without the file, too).
**Full reference with an annotated example: [`docs/CONFIG.md`](docs/CONFIG.md).**

To adapt to your own setup, run the discovery routine once:

```bash
bloridium discover              # list MIDI ports + audio devices + effective config (--probe: identity replies)
bloridium --json discover       # machine-readable output (--json also works after the subcommand)
bloridium discover --write      # merge discovered values into bloridium.yaml (your edits are kept; only empty keys are filled)
```

`discover` scans MIDI ports via CoreMIDI/mido (optionally sending a Universal Device Inquiry
per output port) and audio capture devices via `ffmpeg -list_devices` (AVFoundation on macOS,
ALSA on Linux). Then edit `bloridium.yaml` by hand — especially the `audio.channels` cabling —
and check with `bloridium status [--audio]`, which also shows which config file is active.

### Sound control on the Iridium

As infuriating as it may be: **right now, there is no official way to take full remote control of a sound on the Iridium.** The Iridium has no documented SysEx layer, so patches can only arrive as `.qpat` files (USB stick / SD card). It sends NRPN but does not interpret incoming NRPN.

**The only way to control Iridium parameters from a computer is via MIDI CC.** This limits computer/MIDI control to the 116 MIDI CC commands that are free. To use them, you must upload a MIDI map to the Iridium, defining the controls and the parameters they speak to.  

## Installation

```bash
pip install -e ".[dev]"   # installs the `bloridium` command (mido, python-rtmidi, numpy, pyyaml)
brew install ffmpeg        # audio recording via AVFoundation
cd tools && clang -framework CoreMIDI -framework Foundation -o ump_send ump_send.m
```

Optionally, without the package: `pip install -r requirements.txt` + the ffmpeg/ump_send steps above, then use the scripts in `scripts/`.

## Usage

Python library:

```python
from bloridium import midi, audio

with midi.connect("blofeld") as blofeld, midi.connect("iridium") as iridium:
    blofeld.note_on(note=60, velocity=100)   # Blofeld: channel 5
    iridium.note_on(note=60, velocity=100)   # Iridium: channel 6 (Part 1)
    data = audio.record(duration=2.0, channels=audio.CHANNELS["iridium"])  # inputs 5/6
    print(audio.measure(data)["peak_dbfs"])
    blofeld.note_off(60)
    iridium.note_off(60)
```

CLI (the full workflow):

```bash
bloridium status                 # MIDI ports + identity (--audio: level measurement)
bloridium bank read A            # read Bank A live via SysEx -> dumps/banks/A/ + DB
bloridium bank import dumps      # OFFLINE: import existing dumps into the bank
bloridium bank list              # list sounds (--grep, --json)
bloridium bank show A043         # parameters of a sound
bloridium convert A043           # A043 -> transfer/<name>_A043.qpat (+ DB entry)
# on the Iridium: USB stick/SD -> Load > Actions > Import -> load
bloridium ab --sound A043 --label shpower --note 36   # A/B measurement + DB run
bloridium ab --list --sound A043                      # runs per sound
bloridium ab --diff 1 2                               # compare two runs
bloridium qpat info transfer/SH\ Power_A043.qpat --register
bloridium edit transfer/SH\ Power_A043.qpat --list --grep osc1
bloridium edit transfer/SH\ Power_A043.qpat --set Osc1Type=1.0   # in-place, keeps .bak
```

Parameters & safety:

- The tool **never changes device settings**; All Notes Off (CC123) is sent on all channels before measurements.
- **Warning: CC7 = 0 is silent on the Iridium** (Output Level).
- Global DB option: `--db PATH` or `$BLORIDIUM_DB` (default `<repo>/bloridium.db`). Exit codes: 0 ok, 1 error, 2 hardware unreachable (with port list).
- Similarity score (`bloridium/sim.py`): log-spectrogram cosine (70 %) + envelope DTW (30 %) → score 0–100, plus per-band dB deltas. Offline via `scripts/sim_compare.py --npy A.npy B.npy`, live via `--live` or `scripts/sim_live.py --param "Filter1 Cutoff" --value 90 --ref ref.npy`; every run is logged to `recordings/sim_log.jsonl`.

## History & Todo

- 2026-11-08: CLI design + Phase 1 implementation (`docs/superpowers/specs/2026-11-08-bloridium-cli-design.md`).
- 2026-11-09: similarity tool (sim score, A/B measurement) designed and built (`docs/superpowers/specs/2026-11-09-similarity-tool-design.md`).
- 2026-11-18: hardware discovery (`bloridium discover`) + user-editable `bloridium.yaml` (`docs/CONFIG.md`, plan `docs/superpowers/plans/2026-11-18-discover-config.md`); codebase translated to English-only.
- Todo: Iridium answers no SysEx at all (suspected `SysEx RX` off on the device — hardware change, ask first).
- Todo: Iridium parameters without CC (e.g. Filter1 Cutoff, mod matrix) reachable only via MIDI Learn on the device.
- Todo: mapping model trained from `recordings/sim_log.jsonl`.
- Full findings: `docs/FINDINGS.md`; inventory + next-session plan: `docs/STATUS.md`.
