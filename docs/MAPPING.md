# Mapping-Tabelle: Blofeld (SNDD/SNDP) → Iridium (CC) – Entwurf

Quellen:
- Blofeld: `docs/manuals/Blofeld_sysex_v1_04.pdf` (offizielle Spec, SDATA-Indizes 0..382,
  siehe `bloridium/blofeld_dump.py`) + CC-Liste im Blofeld-Handbuch Anhang S.121-124
  und `docs/midi-maps/blofeld_midi_guide.csv`
- Iridium: `docs/midi-maps/iridium_midi_guide.csv` (115 CCs, CC 2..116, Stand Sep 2024)
  + Iridium OS3/OS4-Handbuch

Legende Iridium-CC: Nummer aus dem CSV. „–“ = kein CC in der midi.guide-Tabelle
(z.B. Filter1 Cutoff) → evtl. per MIDI Learn zuweisbar oder nur per SysEx.

## Oszillatoren (Blofeld 3× OSC ↔ Iridium 3× OSC, je Wavetable/Waveform/Particle/Resonator/Kernels wählbar)

| Blofeld (SDATA-Index / CC) | Iridium | Iridium-CC | Bemerkung |
|---|---|---|---|
| Osc N Octave (1/17/33 / CC 27,35,42) | – (Coarse Pitch) | – | Iridium: kein CC; evtl. Keytrack/Patch |
| Osc N Semitone (2/18/34 / CC 28,36,43) | – | – | wie Octave |
| Osc N Detune (3/19/35 / CC 29,37,44) | OSC N Fine Pitch | 32/46/60 | -64..+63 ↔ 0..127 (Mitte 64) |
| Osc N Shape 0..72 (8/24/40 / CC 31,39,46) | WT: OSC N WT Table + WT Position + WT Spectrum; WF: OSC N WF Shape | 37/51/65, 35/49/63, 36/50/64, 39/53/67 | Blofeld-Shape ist Wavetable-Index; Iridium trennt Table/Position. VA-Shapes (Pulse/Saw/Tri/Sine) ≈ WF Shape |
| Osc N Pulsewidth (9/25/41 / CC 33,40,47) | OSC N WF PW | 42/56/70 | nur im Waveform-Modus |
| Osc N PWM Source/Amount (10/11, 26/27, 42/43) | Mod-Matrix | – | kein direktes PW-CC |
| Osc N FM Source/Amount (6/7, 22/23, 38/39 / CC 30,38,45) | Kernels / Mod-Matrix | – | Iridium: FM über Kernel, nicht per-OSC-CC |
| Osc N Keytrack (5/21/37) | – | – | – |
| Osc N Bend Range (4/20/36) | PB Range pro OSC | – | – |
| Osc N Brilliance (16/32/48) | WT Spectrum? | 36/50/64 | unklar, prüfen |
| Osc 2 Sync to O3 (49) | OSC N WF Sync | 43/57/71 | – |
| Osc Pitch Source/Amount (50/51 / CC 50) | Mod-Matrix Pitch | – | – |

## Mixer

| Blofeld (SDATA / CC) | Iridium | CC | Bemerkung |
|---|---|---|---|
| Mixer Osc N Level (61/63/65 / CC 52,56,58) | OSC N VOL | 33/47/61 | |
| Mixer Osc N Balance (62/64/66 / CC 53,57,59) | OSC N PAN (näherungsw.) | 34/48/62 | Blofeld Balance = F1/F2-Anteil, Iridium PAN = Stereo; Filter-Routing beachten |
| Mixer Noise Level (67 / CC 60) | – (Particle/Resonator) | – | – |
| Mixer Noise Colour (69 / CC 62) | – | – | – |
| Mixer RingMod Level/Bal (71/72 / CC 54,55) | Ringmod OSC1→OSC2 / OSC1→OSC3 | 74/75 | – |

## Filter (Blofeld F1/F2 ↔ Iridium Dual Filter F1/F2 + Digital Former)

| Blofeld (SDATA / CC) | Iridium | CC | Bemerkung |
|---|---|---|---|
| Filter N Type (77/97 / CC 68,79) | Filter-Modell (Nave/Largo/PPG/...) | – | kein CC; ggf. SysEx |
| Filter N Cutoff (78/98 / CC 69,80) | Filter N Cutoff | F1: –, F2: 9 | F1 Cutoff ohne CC in CSV! |
| Filter N Resonance (80/100 / CC 70,81) | Filter N Reso | 2/10 | |
| Filter N Drive (81/101 / CC 71,82) | Drive Amount/Gain | 102/104 | Drive sitzt im Former/FX |
| Filter N Keytrack (86/106 / CC 72,83) | – | – | – |
| Filter N Env Amount (87/107 / CC 73,84) | Filter N Amount | 7/15 | |
| Filter N Env Velocity (88/108 / CC 74,85) | Filter N Velo Amount | 8/16 | |
| Filter N FM Source/Amount (91/92, 111/112) | – | – | – |
| Filter N Pan (93/113 / CC 77,88) | Digi Former PAN | 78 | – |
| Filter Routing (117 / CC 67) | Filter-Routing | – | serial/parallel ↔ Iridium-Routing |

## Amplifier / Envelopes

| Blofeld (SDATA / CC) | Iridium | CC | Bemerkung |
|---|---|---|---|
| Amplifier Volume (121 / CC 90) | Master/Channel Volume | CC 7 | – |
| Amplifier Velocity (122 / CC 91) | AMP Velo Amount | 17 | -64..+63 ↔ 0..127 |
| Filter Env A/D/S/R (+A-Lvl, D2, S2) (199..205 / CC 95..100) | Filter1/2 Attack/Decay/Sustain/Release + Amount | 3-6, 7, 11-14, 15 | Iridium trennt F1/F2-Env |
| Amp Env A/D/S/R (211..217 / CC 101..106) | AMP Attack/Decay/Sustain/Release | 18-21 | |
| Env 3/4 A/D/S/R (223..229, 235..241 / CC 107..118) | Free ENV1 / Free ENV2 | 105-116 | |
| Env Mode (4.12) | – | – | – |

## LFO / Modulation

| Blofeld (SDATA / CC) | Iridium | CC | Bemerkung |
|---|---|---|---|
| LFO N Shape/Speed/Sync/Delay/Fade/Keytrack (160..194 / CC 15..26) | LFO N Speed + Amount; Komplex | 80-88 | Shape/Sync per CC nicht abgedeckt |
| Modulation 1..16 Source/Dest/Amount (261..308) | Mod-Matrix (40 Slots) | – | Iridium: keine CCs für Matrix; evtl. SysEx |
| Modifier 1..4 (245..260) | – | – | – |
| Glide (53/56/57 / CC 5,65,51) | Glide ON/OFF + Rate | 90/89 | |
| Allocation/Unisono (58/59) | Unisono Count/Detune | 91/92 | |

## Effekte

| Blofeld (SDATA / CC) | Iridium | CC | Bemerkung |
|---|---|---|---|
| FX1/FX2 Type + Mix + Params (128..159 / CC 92..94 + FX-CCs) | Chorus/Phaser/Flanger/Drive/Delay/Reverb | 22-31, 93-104 | Blofeld FX1: Chorus/Flanger/Phaser/Overdrive/Triple; FX2: + Delay/Reverb |

## Offene Punkte

- Iridium reagiert nicht auf eingehende NRPN (laut OS3-Handbuch) → Parameter ohne CC
  (z.B. Filter1 Cutoff, Filter-Typ, Mod-Matrix) brauchen SysEx oder MIDI Learn am Gerät.
- Iridium antwortet derzeit auf KEIN SysEx (auch kein Identity Reply) – siehe FINDINGS.md
  Runde 2; Verdacht: SysEx RX am Gerät ausgeschaltet (Global > MIDI).
- Ob das Iridium überhaupt Sound-Dumps senden kann (Dump Request), ist unklar;
  Import von .syx über Load>Actions>Import ist dokumentiert (FAQ).
