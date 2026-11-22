# Configuration & hardware discovery (`bloridium.yaml`)

All hardware-dependent settings live in one **user-editable YAML file**. This document is
the full reference; the short version is in `README.md` → "Configuration".

## 1. Where the config file is found

Precedence (first hit wins):

1. `--config PATH` CLI flag (global, put it **before** the subcommand: `bloridium --config my.yaml status`)
2. `$BLORIDIUM_CONFIG` environment variable
3. `./bloridium.yaml` (current working directory / project root)
4. built-in defaults — so everything works even without any YAML file

`bloridium status` prints which config file is in effect (`Config: <path>` or
`Config: built-in defaults`). Related env var: `$BLORIDIUM_DB` for the SQLite bank DB.

## 2. File format — annotated example

An annotated example (reference measurement rig via the Launchpad DIN chain). The shipped
`bloridium.yaml` currently uses the USB ports for both synths — switch the Iridium ports to
`Launchpad Pro MK3 LPProMK3 DIN` for low-noise A/B recordings. Every key is optional;
missing keys fall back to the built-in defaults.

```yaml
# bloridium.yaml -- Bloridium configuration (edit freely).
# `bloridium discover --write` only fills keys you left empty.
# MIDI channels are 0-based (Blofeld Global Channel 5 -> 4; Iridium Part 1 = ch 6 -> 5).
# Audio channels are 0-based input numbers on the audio interface.
midi:
  blofeld:
    out_port: Launchpad Pro MK3 LPProMK3 DIN   # port NAME (see `bloridium discover`);
                                               # matched exactly, else case-insensitive substring
    in_port: Launchpad Pro MK3 LPProMK3 DIN    # MIDI input for replies (SysEx dumps, identity);
                                               # null = send-only
    channel: 4                                 # 0-based MIDI channel (here: ch 5, Blofeld Global Channel)
  iridium:
    out_port: Launchpad Pro MK3 LPProMK3 DIN
    in_port: Launchpad Pro MK3 LPProMK3 DIN
    channel: 5                                 # 0-based (ch 6 = Part 1; Parts 1-4 = ch 6-9)
  fallback_out_ports:                          # candidate port names per synth (reference list;
                                               # `discover --write` prepends what it finds here).
                                               # NOTE: connecting uses only `out_port` (see below);
                                               # on a mismatch the CLI exits 2 and lists the ports.
    blofeld: [Launchpad Pro MK3 LPProMK3 DIN, Blofeld]   # e.g. USB port "Blofeld"
    iridium:
      - Launchpad Pro MK3 LPProMK3 DIN
      - Iridium Keyboard (MIDI 2.0) MIDI 2.0
      - Iridium Keyboard (MIDI 2.0) Synth
audio:
  device: Scarlett 18i8 USB                    # ffmpeg device name (AVFoundation on macOS,
                                               # ALSA card name on Linux) - see `bloridium discover`
  samplerate: 48000                            # recording samplerate
  raw_channels: 20                             # channel count of the raw device stream
  channels:                                    # which inputs each synth is wired to (0-based)
    blofeld: [2, 3]                            # inputs 3/4
    iridium: [4, 5]                            # inputs 5/6
```

Notes:

- **Port matching** (`midi.match_port`): exact name first, then case-insensitive substring.
  So `out_port: Blofeld` also matches the CoreMIDI port `Blofeld`. Only `out_port` is used when
  connecting; if nothing matches, the CLI exits with code **2** and prints the available ports —
  run `bloridium discover` to see them.
- **`fallback_out_ports`** is a candidate list per synth (kept for reference and updated by
  `discover --write`); it is not auto-tried at connect time — fix `out_port` instead.
- **Channels are 0-based everywhere** (MIDI channel 5 = `channel: 4`; audio input 3 = index 2).

## 3. Discovering your own hardware

```bash
bloridium discover                 # list MIDI ports, audio devices, effective config
bloridium discover --probe         # additionally send a Device Inquiry per MIDI out port
                                   # (identity reply: manufacturer 0x3E = Waldorf, model 0x13 = Blofeld)
bloridium --json discover          # machine-readable (--json also works after the subcommand)
bloridium discover --write         # merge discovered values into the YAML config file
```

Example (text mode):

```text
Config: /path/to/bloridium.yaml
MIDI ports:
  OUT: Blofeld
  OUT: Iridium Keyboard (MIDI 2.0) MIDI 2.0
  ...
Audio devices:
  [0] MacBook Air Microphone (avfoundation)
  [3] Scarlett 18i8 USB (avfoundation)
Effective config (precedence: user YAML > discovered > built-in defaults):
  ...
```

How the scan works:

- **MIDI**: all CoreMIDI/mido input+output ports (`mido.get_input_names()/get_output_names()`).
  With `--probe`, a Universal Device Inquiry (`F0 7E 7F 06 01 F7`) is sent to every output port
  and identity replies are shown.
- **Audio**: `ffmpeg -f avfoundation -list_devices true -i ""` on macOS,
  `ffmpeg -f alsa -list_devices true -i ""` on Linux; parsed into a device list.
  If several devices are found, the audio `device` is picked preferring a name containing
  "scarlett", else the first device. **Requires ffmpeg** (see Installation in README).

What `--write` fills (and what it does **not**):

- fills `midi.<synth>.out_port`/`in_port` (ports whose name contains "blofeld"/"iridium"),
  prepends them to `fallback_out_ports`, and sets `audio.device`
- **never overwrites existing values** — precedence is user YAML > discovered > defaults;
  only empty/missing keys are filled
- does **not** set `channel`, `samplerate`, `raw_channels` or `audio.channels` — those are
  physical cabling facts; set them by hand (see the example above)

After `--write`, open `bloridium.yaml`, adjust the audio channels to your cabling, and check
with `bloridium status` (add `--audio` to also play a note and measure the level).

## 4. Using the config from Python

```python
from bloridium import midi, audio, config

cfg = config.load_config()                 # or load_config("my.yaml"); $BLORIDIUM_CONFIG / ./bloridium.yaml
ports = midi.ports_from_config()           # {synth: {"out", "in", "channel"}}
with midi.connect("blofeld") as blo:      # reads the YAML automatically
    blo.note_on(60)

s = audio.settings()                       # {"device", "samplerate", "raw_channels", "channels"}
data = audio.record(duration=2.0, channels=s["channels"]["iridium"])  # device/samplerate from YAML
```

All library entry points accept `config_path=...` to override the lookup
(`midi.connect(name, config_path=...)`, `audio.record(..., config_path=...)`,
`workflow.check_connection/measure_ab/record_ab_pair(config_path=...)`).

## 5. Scope & limitations

- The **CLI and the Python library** honor `bloridium.yaml`. The standalone scripts in
  `scripts/` still use the built-in defaults (`midi.DEFAULT_PORTS`, `audio.CHANNELS`) —
  for those, either edit the constants' source (`bloridium/config.py` `DEFAULTS`) or use the
  CLI/library equivalents.
- Audio discovery needs **ffmpeg**; without it `discover` lists no audio devices and
  recording is unavailable.
- MIDI discovery needs **python-rtmidi** (installed with the package); on macOS this uses
  CoreMIDI, on Linux ALSA sequencer via rtmidi.
- The config file is plain YAML — edit it in any editor; `bloridium status` shows which file
  is active, so a typo in the path is easy to spot.

## 6. Troubleshooting

- `ERROR: MIDI port not found: '...' - available: [...]` (exit code 2): the configured
  `out_port` does not exist right now. Run `bloridium discover`, fix `out_port` /
  `fallback_out_ports` in `bloridium.yaml` (or pass `--config`), re-run.
- `status --audio` reports `NO SOUND`: wrong `audio.channels` for your cabling, or the synth
  plays on another MIDI channel (`midi.<synth>.channel`); on the Iridium also check the
  device's `Global > MIDI = on`. By default CC7 = 0 is silent (Output Level); a loaded
  `.mimap` may reassign CC7.
- `invalid YAML in bloridium.yaml: ...`: the file is malformed — the error names the file;
  `python3 -c "import yaml; yaml.safe_load(open('bloridium.yaml'))"` shows the exact line.
