# Iridium OS 4.1.0b2 – Runtime enum lists (2026-11-18)

Values captured with private device-side tooling that is **not part of this project**.
Results only; the capture logs are not shipped. Device export patches are **qpat version 14**.

## Key finding (controlled load test 2026-11-18): qpat FILE enum == RUNTIME enum (identity)

A v14 qpat written by us with MatrixDst=109 was loaded on the device and read back as
runtime **109** (identity); device saves (v11) are identity too (17->17, 33->33).
=> On OS 4.1.0b2 the loader interprets qpat enum values with the CURRENT runtime layout.
The old displays in `dumps/export-001` (v14 files from an older OS build, e.g. 95='DF Amount',
16='After Touch') are STALE artifacts - do not use them. The converter therefore uses the
RUNTIME values below, and so does the private device-side path.

## Runtime enum lists (OS 4.1.0b2)

### MatrixSrc1 (pid 2478) — runtime
0 Off · 1 Amp Env · 2 Filter1 Env · 3 Filter2 Env · 4 Free Env1 · 5 Free Env2 · 6 Free Env3 ·
7 LFO 1 · 8 LFO 2 · 9 LFO 3 · 10 LFO 4 · 11 LFO 5 · 12 LFO 6 · 13 Komplex · 14 Wheel ·
15 Pitch Bend · **16 Per-Note Pitch Bend** · **17 After Touch** · 18 MPE Y Axis · 19 Pedal ·
20 Expression · 21 Breath Control · 22-31 CC 22-31 · 32 Keytrack · 33 Velocity ·
34 Release Velocity · 35 Voice Number · 36 Unisono Idx · 37 Poly Idx · 38 Rand Trig ·
39 Rand Trig Bipol · 40 Constant · 41 Mod Pad X · 42 Mod Pad Y · 43-50 SeqParam 1-8 ·
51-54 CV 1-4 · 55 CV Start · 56 CV Gate

### MatrixDst1 (pid 2480) — runtime
0 Off · 1 Pitch · 2 Osc1 Pitch · 3 Osc2 Pitch · 4 Osc3 Pitch · 5-7 Osc1-3 Mix · 8-10 Osc1-3 Pan ·
11 WT1 Position · 12 WT1 Travel · 13 WT1 Spectrum · 14 WT1 Noisy · 15 WT1 Brilliance · 16 WT1 FX ·
17 WT1 Table · 18 WF1 Warp · 19 WF1 Sync · 20 WF1 Detune · 21-28 PT1 ... · 29 Osc1 Samp Start ·
30-33 RS1 ... · 34-38 KN1 ... · 39-41 SD1 ... · 42-48 WT2 ... · 49 WF2 Warp · 50 WF2 Sync ·
51 WF2 Detune · ... 73 WT3 Position · 80 WF3 Warp · 81 WF3 Sync · 82 WF3 Detune · ...
**104 DF Amount · 105 DF Color · 106 DF Tilt · 107 DF Pan · 108 DF Level** ·
**109 Filter1 Cutoff · 110 Filter1 Reso · 111 Filter1 Pan · 112 Filter1 Level** ·
113 Filter2 Cutoff · 114 Filter2 Reso · 115 Filter2 Pan · 116 Filter2 Level · 117 VCA ·
118 AmpEnv Attack · 119 AmpEnv Decay · 120 AmpEnv Sustain · 121 AmpEnv Release ·
122 Filt1Env Attack · 123 Filt1Env Decay · 124 Filt1Env Sustain · 125 Filt1Env Release ·
126-129 Filt2Env A/D/S/R · 130-133 Free1Env · 134-137 Free2Env · 138-141 Free3Env ·
142 FX1 DryWet · 143 FX1 Control · 144 FX2 DryWet · 145 FX2 Control · 146 FX3 DryWet ·
147 FX3 Control · 148 FX4 DryWet · 149 FX4 Control · 150 FX5 DryWet · 151 FX5 Control ·
**152 Volume** · 153 Pan · **154-159 LFO1-6 Speed** · 160-165 LFO1-6 Gain · 166-170 Komplex ·
171 Glide Rate · 172 Tremolo Depth · 173 Tremolo Speed · 174 Chorus DryWet · 175 Chorus Depth ·
176 Chorus Speed · 177 Chorus Feedback · 178 Phaser DryWet · 179 Phaser Depth · 180 Phaser Speed ·
181 Phaser Feedback · 182 Phaser Spread · 183 Flanger DryWet · 184 Flanger Depth · 185 Flanger Speed ·
186 Flanger Feedback · 187 Reverb Gain · 188 Reverb Time · 189 Reverb Color · 190 Delay DryWet ·
191 Delay Feedback · 192 Delay Time L · 193 Delay Time R · 194 EQ DryWet · 195 EQ FreqShift ·
196 Drive DryWet · 197 Drive Amount · 198 Drive Gain · 199 Compress Ratio · 200 Compress Thresh ·
201-203 FX Lane 1-3 Level · 204 Arp/Seq RelGate · 205 Arp/Seq Swing · 206 Seq Length ·
207 Reverb Shimmer · 208 Reverb Pitch

### Other enums (runtime)
- `AfterTouchDoPoly` (2876): 0 Mono AT · 1 Poly AT (same in v14 files)
- `FX1Type`/`FX2Type` (2754/2756): 0 Off · 1 Tremolo · 2 Phaser · 3 Chorus · 4 Flanger ·
  5 Delay · 6 Reverb · 7 EQ · 8 Drive · 9 Compressor (v14 FILE enum lacks Tremolo: Phaser=1,
  Chorus=2, ... Drive=7, Compressor=8 — current `FX_TYPE` table, matches export-001)
- `Filter12Type` (2098): 0 12dB LP · 1 12dB sat LP · 2 12dB dirty LP · 3 24dB LP · 4 24dB sat LP ·
  5 24dB dirty LP · 6-8 12dB HP/sat/dirty · 9 24dB HP · 10-11 sat/dirty · 12-14 12dB BP ·
  15 24dB BP · 16-17 sat/dirty BP (identical in v14 files)
- `DigiFormerType` (2090): 0 Bypass · 1 Drive · 2 Gain · 3 Comb+ · 4 Comb- · 5 Bit Crusher ·
  6 Ring Mod · 7 Nave LP24 · 8 PPG LP24 · 9 Largo LP24 · 10 SVF LP24 · 11 Nave LP12 ·
  12 PPG LP12 · 13 Largo LP12 · 14 SVF LP12 · 15 Nave HP24 · 16 Largo HP24 · 17 SVF HP24 ·
  18 Nave HP12 · 19 Largo HP12 · 20 SVF HP12 · 21 Nave BP24 · ... · 27 Nave Notch24 · ...
  (identical in v14 files)
- `Filter2State` (2116): 0 Active · 1 Bypass · 2 Off (same in v14)
- `Osc1Type` (0): 0 Wavetable · 1 Waveform · 2 Particle · 3 Resonator · 4 Kernels · 5 Seeds ·
  6 Off (v14 FILE: Off=4! — `OSC_TYPE` table uses 4, correct for v14 files)

## Still open (live audio sweeps)
amt_bipolar divisor (MatrixAmount scale), FinePitch cent-per-norm, LFO free-speed Hz,
WT bridge by CLAP, MIDI-CI over MIDI-2.0-UMP with "CI Support" on — see
`docs/research/superpowers/plans/2026-11-18-converter-rebuild-polyat.md`.
