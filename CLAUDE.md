# Objective

A suite of utilities and skills to convert and transfer sound programs between two synthesizers:
- Waldorf Blofeld (older)
- Waldorf Iridium

## Sub-tasks

- Control: Get sound from synthesizer, manipulate sound on synthesizer, read or set single parameters
- Listen: Trigger sound and record a sample for comparison
- Analyse: Break down sampled synth sound for comparison
- Compare: Calculate similarity between two sound samples
- Categorize: Assess quality of conversion from the sound specifics
- Tweak: Trial-and-error editing of the Iridium sound to get closer to the Blofeld original
- Web app: Offer a simple conversion service to run as a container on a server

## Description

The Iridium synthesizer is a descendant of the Blofeld. 

Similarities:
- 3 Oscillators
- Synthesis: Wavetable, VA waveforms, sampling waveforms
- Modulation matrix
- 2 filters
  
Differences:
- Iridium has additional synthesis models (FM, Resonance, Particles, Seeds) we should not try to use - keep to Wavetable and Waveforms models
- Different filter architecture:
    - Blofeld filters can be routed parallel or serial; filters can be routed via a mixing parameter to F1 or F2
    - Iridium filters are fixed to parallel (with different link modes), but there is an additional "Digital Former" filter that can be used before or after filters;  filters can be routed via a mixing parameter to filters or Digital Former
- Iridium has no oscillator FM, as it uses a dedicated synthesis model for FM synthesis - ignore in conversion
- Iridium has more FX
  
## Manuals

Synth descriptions in the docs: 
- `docs/manuals/blofeld_sysex_v1_04.txt`
- `docs/manual-text/blofeld.txt`
- `docs/manual-text/iridium_os3.txt`
- `docs/manual-text/iridium_os4_som2.txt`

## Hardware & Setup

- Mac (macOS, CoreMIDI/AVFoundation); Focusrite Scarlett 18i8 audio interface. Blofeld via USB; Iridium via USB or Launchpad DIN (direct Iridium USB can cause ground-loop noise, so use DIN for A/B recordings; see `README.md`)
- Blofeld on Scarlett inputs 3/4 (MIDI channel 5), Iridium on inputs 5/6 (MIDI channels 6-9, Parts 1-4)
- Install: `pip install -e ".[dev]"`, `brew install ffmpeg`, build `tools/ump_send` (details in `README.md`)
- Workflow (convert -> upload -> A/B measure -> tweak): see `README.md`; mapping status: `docs/MAPPING-MASTER.md`; empirical facts: `docs/FINDINGS.md`; backlog: `FIXES_HISTORY.md`, `TODO_FIX.md`, `TODO_MEASURE.md`
- Parameter calibration (method + inventory of measured anchors + open candidates): `CALIBRATE.md` — a mapping may ship only with a measured calibration, a manual-documented identity, or an explicit TODO naming the calibration task

## Skills

- bloridium

# Rules

- Ask before changing settings on either unit
- Try to be hardware-agnostic, using generic MIDI and Audio interfaces
- Repository language is English
- When improving the code, always document your findings
- When improving the code, always correct the bloridium skill accordingly

