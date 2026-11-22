# Bloridium

## Objective - what this is about

Transfer sound programs (patches) **from the Waldorf Blofeld to the Waldorf Iridium synthesizer**.

An exact transfer is impossible, although those two synths are related and have a similar basic architecture, they are very different beasts. The conversion is therefore an **approximation**. 

To close the gap, Bloridium provides tools to **measure and track the differences** between the original and the converted sound (A/B recordings over a Focusrite Scarlett 18i8, similarity score 0–100 from log-spectrogram + envelope comparison) and to **optimise parameters** until the Iridium patch matches the Blofeld as closely as possible.

### What you can do with it

- Read sounds from a Blofeld: single sounds or whole banks. The dumps are kept in a SQLite database.
- Convert a Blofeld sound to the Iridium format and create a `.qpat` file for transfer to SD card/USB stick
- Edit Iridium parameters in the `.qpat` file
- Edit Iridium parameters via MIDI CC, using a customised MIDI map for the Iridium
- A/B comparison: Both synth play the same notes with Modwheel variations, which are recorded for comparison
- Mathematical comparison of the spectra and the envelopes for a coarse similarity score
- AI-based comparison via embeddings, and via a local decision model running on ollama
- Prognostics: Based on the comparison, a very crude Random Forest model has been trained to predict how close a converted file is to the original
- Web app for conversion: find a demo on [bloridium.frankruft.de](https://bloridium.frankruft.de)
  
### Limitations

- **Limited Iridium control:** To read back sounds from the Iridium, you have to copy them from the transfer medium
- **No fully automatic tweaking - yet** - but all the tools are there for an AI agent to use, see below.
- **Many things cannot be converted 1:1 to the Iridium**: see the [table of architectural differences](docs/ARCHITECTURE-DIFFERENCES.md). 
    - Wavetables unique to the Blofeld
    - Osc FM and Sync
    - Balance, Brilliance, Noise mixer
    - LFO: Waveform, Delay, Fade, Keytrack
    - Filter Drive and Curve
    - Parts of the Modulation Matrix
    - Arpeggiator

**Basically, what you get is a first starting point for tweaking**. Keeps the fun in it, after all!

## Using bloridium

### Optimised for agentic use

The code has been produced, and optimised, with the [Opencode agent](https://opencode.ai) using [Mistral-Large-4 and Deepseek-V4.1-flash models via mistral.ai](https://docs.mistral.ai/inference/pricing) (which comes cheap at €18 a month.) It is meant to be used by AI: 

- Point your coding agent (Claude Code, Codex, Opencode, Hermes...) at this repository and tell it to install the `bloridium` skill from the `skills/` folder.
- Once loaded, the agent knows how to load and convert sounds, to tweak a sound in the Iridium, and how to measure the distance between the original and the recreation. 

### Hardware

The test hardware used: 

- Macbook Air
- both synths connected directly via USB (**MIGHT CAUSE DIGITAL NOISE BY GROUND LOOP**)
- Focusrite Scarlett 18i8 Audio interface
- Blofeld on inputs 3/4 (MIDI channel 5), Iridium on inputs 5/6 (MIDI channels 6–9, Parts 1–4).

Important note: 

- My Iridium features **OS4.1.0beta** as well as the **SOM2** extension board. The code should keep only to those features that are available on every version of the Iridium but there may be occasional incompatibilities. Update to the [most recent OS4 version](https://waldorfmusic.com/iridium-os-update/) of the firmware is strongly encouraged.

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

## Using the code

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
- Similarity score (`bloridium/sim.py`, `score_version` 2 since v0.4.0): 70 % spectral similarity (`1 − spec_mad_db/20 dB`, the mean level-aligned deviation of the log-spectrogram bands) + 30 % envelope DTW → score 0–100, plus per-band dB deltas. The v1 cosine score saturated (see `docs/FINDINGS.md`); log rows without `score_version` are v1 and are skipped by `prognose train`. Offline via `scripts/sim_compare.py --npy A.npy B.npy`, live via `--live` or `scripts/sim_live.py --param "Filter1 Cutoff" --value 90 --ref ref.npy`; every run is logged to `recordings/sim_log.jsonl`.

## License

Bloridium is free software, licensed under the [GNU General Public License v3.0](LICENSE) (GPL-3.0-only).
