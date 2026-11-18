# Analysis 2026-11-15: what still has to be fixed in the qpat sound conversion?

Subagent analysis (read-only/offline only: dumps, qpats, logs, references; no MIDI, no code change).
Method: systematic-debugging (Phase 1 root cause + Phase 2 pattern) — every statement below is backed by
raw dump (`bloridium bank show <LOC>` / `dumps/blofeld_sndd_<LOC>_*.bin`), generated qpat
(`qpat info transfer/upload/*.qpat` + direct comparison override vs. qpat value), `qpat_map.py`,
own OS4 exports (`dumps/export-001`, v14) and the Iridium manual (`docs/manual-text/iridium_os3.txt`).
All 9 generated qpats are **qpat v14** (`workflow.py:138`: "target device OS4 expects v14").

## Evidence base (live A/B 2026-11-14, Set 6 PC108-116, note 72, mode=manual_panel)

| Preset | User 0-100 | User comment (core) | Phase A | combined | Peak A/B dBFS | Routing |
|---|---|---|---|---|---|---|
| A001 JMX jun | 70 | Quieter, filter closed too far, LFO1 filter too strong | 92.86 | 84.22 | -19.4 / **-47.9** | serial |
| A008 Easy Piano | **45** | Barely audible, presumably 1 octave lower, heavily filtered | 95.20 | 82.28 | -25.6 / **-64.8** | serial |
| A010 Wurly | 80 | High registers different character (hollow square wave) | 97.00 | 87.61 | -44.2 / -42.8 | parallel |
| A019 Tines | 90 | Does not react to aftertouch | 95.05 | 91.41 | -29.4 / -45.5 | parallel |
| A022 ModWheelOrg | 95 | Mid harmonic louder on the Blofeld | 94.74 | 89.18 | -15.5 / -29.2 | serial |
| A039 A Elektro | 90 | Much quieter; delay on the Blofeld | 96.07 | 86.64 | -37.9 / -55.3 | serial |
| A043 SH Power | 75 | Blofeld fuller; Iridium strong AT bending (Channel->Poly AT) | 95.02 | 86.70 | -19.3 / -35.6 | parallel |
| A071 Windowed SYNC2FM | 70 | **No sync on the Iridium** | 94.38 | 90.54 | -23.2 / -40.6 | serial |
| A073 Chord Hose | 85 | Different effects, Blofeld more cutting | 96.63 | 88.82 | -27.0 / -53.9 | serial |

Sources: `recordings/phaseb_ratings_raw.json`, `recordings/sim_log.jsonl` (ts 20261114_175046-180616,
`norm_pegel=true`), `docs/PHASEB-EVAL-2026-11-14.md`, `transfer/upload/MANIFEST.md`.
Additional evidence: d1-omni:2b profile `darker` 9/9 (2b) resp. 7/9 (600m), `octave_lower` only A008 borderline
(p=0.50) — matches "filter closed / filtered" on all, octave suspicion A008 only weak.

**Pattern (Phase 2):** all 6 serial patches (A001 A008 A022 A039 A071 A073) have Iridium peaks
15-40 dB below the Blofeld (down to -64.8 dBFS) and all serial user texts complain about
"too/much quieter/filtered" — that's no coincidence, but a systematic defect in the serial path
(see P0-1). The parallel patches (A010 A019 A043) have normal levels and their complaints
concern matrix/FX detail (sync, AT, FM, drive) — see P0-2/P1.

---

## P0 — serial patches too dark/too quiet (all 6 serial presets)

### P0-1 MatrixDst enum values are v8 values in v14 files: "DF Amount"=71 instead of **95**, "Filter2 Cutoff"=103 instead of **104**
- **Affected:** A001, A008, A022, A039, A071, A073 (serial) — the extra slot `Filter1 Env -> DF Amount`
  (qpat_map.py:461-466) lands with `MatrixDst = 71.0` (qpat_map.py:89, comment "v14 value from qpat_params_v8.md")
  on a **v14-wrong destination**; likewise "Filter2 Cutoff"=103 (qpat_map.py:85).
- **Evidence:** own OS4 exports (v14, `dumps/export-001`): per slot evaluation shows in v14 consistently
  `DF Amount = 95.0` (slots 2/4/5/9), `Filter1 Cutoff = 100`, `Filter1 Reso = 101`, `Filter2 Cutoff = 104`,
  `Filter2 Reso = 105`; 71/103 do NOT occur in v14 at all (in v8 factories: 71=DF Amount n=234,
  103=Filter2 Cutoff). The built qpats are v14 (`qpat info`: version 14) — on the device dst 71/103 is
  a different destination (WT/RS-/filter-pan range). So the slot that is supposed to open the DigiFormer via the filter env
  (HANDOVER-2026-11-14: "otherwise the Former stays statically closed ... -66 dBFS"), **does nothing** →
  the serial chain stays F1-cutoff + static, possibly very closed Former → exactly the observed
  -40 to -64.8 dBFS peaks and "filter closed too far" (A001), "barely audible" (A008),
  "much quieter" (A039), d1 `darker` 9/9.
- **Root cause:** `bloridium/qpat_map.py:89` (`"DF Amount": 71.0`) and `:85` (`"Filter2 Cutoff": 103.0`) —
  v8 enum in v14 output (mix-up: Filter12Type was corrected to v14 on 2026-11-14, MATRIX_DST was not).
- **Fix:** MATRIX_DST for v14: `"DF Amount": 95.0`, `"DF Color": 96.0` (v14: 96='DF Color'), `"Filter2 Cutoff": 104.0`,
  `"Filter2 Reso": 105.0` (rest 100/101/113/114/123/144/1-11/18/39/46/67/74/76 already v14-conform).
  The change affects all 9 qpats (serial slot + F2 mod slots).
- **Test:** `tests/test_qpat_map.py` — new test: for A001 `MatrixDst{df_slot} == 95.0`; regression:
  assert all dst values present in v14 exports against a hardcoded v14 table; existing test
  `test_mod_matrix_slots_mapped` (asserted 100/101/103/105...) must be adjusted to 104.
  Device check: load one serial patch (A001), is the matrix slot with dst 95 shown as "DF Amount" on the panel?

### P0-2 Aftertouch: global `AfterTouchDoPoly` stays on template default 1.0 (Poly AT) → Channel AT doesn't work / works wrong
- **Affected:** A019 ("does not react to aftertouch", user=90), A043 ("strong aftertouch bending; problem
  Channel AT (Blofeld) -> Poly AT (Iridium)", user=75).
- **Evidence:** qpat_map.py never sets `AfterTouchDoPoly`. Template **and all own v14 exports** have
  `AfterTouchDoPoly = 1.0 'Poly AT'`. Iridium manual (os3.txt:5387): globally selectable Mono AT / Poly AT;
  appendix (os3.txt:7660): matrix source "After Touch" = **"Polyphonic Keyboard Pressure Data"**.
  Blofeld "Pressure" is Channel Aftertouch → with DoPoly=1 the matrix does not react to Channel AT.
  A043 additionally has 2 AT slots (M1 LFO2*Press→Pitch amt 84, M2 Pressure→O2 Pitch amt 43 →
  MatrixSrc 16.0, qpat_map.py:80), which bend per note under Poly AT ("strong bending").
- **Root cause:** `qpat_map.py` — missing completely (no `setp("AfterTouchDoPoly", ...)`); `MATRIX_SRC`
  "After Touch": 16.0 (line 80) — in v14 exports 16 **and** 17 appear with display 'After Touch'
  (16=channel?, 17=poly? — clarify on the device).
- **Fix:** in `blofeld_to_qpat_params` for all patches `setp("AfterTouchDoPoly", 0.0, "Mono AT")`
  (Blofeld sends Channel AT), leave MatrixSrc AT at 16.0 for now; on the device test Channel AT against 17.
- **Test:** new test: `ov["AfterTouchDoPoly"][0] == 0.0` for all 9 dumps; device check: load A043,
  send Channel AT → pitch bends only via M2 (amt 43→0.417), not doubled.

---

## P1 — concrete feature gaps with user evidence

### P1-1 Hard sync is not translated: "Osc 2 Sync to O3" lands in `unmapped`
> **Deprioritized 2026-11-15 (user):** windowed-sync sounds (A071, sound 215) use an
> experimental, Blofeld-specific technique -> low priority, after P2.
- **Affected:** A071 Windowed SYNC2FM (user=70: **"No sync on the Iridium"**), A008 (raw `Osc 2 Sync to O3 = 1`).
- **Evidence:** dump A071/A008: `Osc 2 Sync to O3 = 1`. qpat_map.py:285: `unmapped += ["Osc 2 Sync to O3", ...]`;
  in the qpats `Osc2WaveformSync = 0.0` (template default). Manual os3.txt:1680: osc sync =
  "typical oscillator synchronization"; qpat param exists: `Osc2WaveformSync` (v15 doc line 977;
  v8 factories use values 0.02-0.70, i.e. 0..1 scale, 0=off). Additionally matrix dst "WF2 Sync" exists
  (v8: 37; check the v14 value on the device).
- **Root cause:** qpat_map.py:285 (deliberately unmapped) — nowhere sets `OscNWaveformSync`.
- **Fix:** `if p.get("Osc 2 Sync to O3"): setp("Osc2WaveformSync", 1.0, "Sync on")` (value 1.0 = full sync;
  exact amount scale on the device, possibly 0.5 default). Affects A071 (Osc2 is wavetable 'Resonant2' —
  check whether WaveformSync works on WT oscs, else matrix slot src LFO? -> device check).
- **Test:** `test_osc2_sync_mapped_a071`: dump A071 → `ov["Osc2WaveformSync"][0] == 1.0`; A001 (Sync=0) → not set/0.0.

### P1-2 Serial F2 modulations target the switched-off filter-2 stage (and wrong enum)
- **Affected:** A001 (Filter 2 Mod Source=Velocity amt 107 → slot `Velocity -> Filter2 Cutoff` dst 103),
  A071 (M7 LFO3→F2 Cutoff amt 13 → dst 103; M9 MW→F2 Reson. amt 100 → dst 105), A022 (M11 Modifier1→F2 Cutoff,
  M15 MW→F2 Cutoff).
- **Evidence:** qpat_map.py:435-447 (`d_disp = "Filter2 Cutoff"` line 440) and BLOFELD_MOD_DST:109. In serial
  mode `Filter2State = Off` (qpat_map.py:328) — the filter-2 stage is off; the audible F2 is the
  DigiFormer. Modulations to "Filter2 Cutoff/Reso" go nowhere (or, due to P0-1, to the wrong destination).
  Consequence e.g. A001: velocity opens BOTH filters on the Blofeld, on the Iridium only F1.
- **Root cause:** qpat_map.py:435-447 + :109 — no serial-aware remapping F2→DigiFormer.
- **Fix:** in the serial case (`seriell and not f2_bypass`): Blofeld destinations "F2 Cutoff" → MatrixDst "DF Amount"
  (v14: 95.0), "F2 Reson." → "DF Color" (v14: 96.0); in the parallel case they stay 104/105. Same for the
  direct block `Filter 2 Mod Source/Amount` (lines 436-447, n=2 → dst "DF Amount").
- **Test:** A001: no MatrixDst values with display "Filter2 Cutoff" may occur in the serial qpat;
  instead a slot with dst 95.0 and src Velocity. A010 (parallel) keeps 104.0.

### P1-3 FX block: mix key by slot instead of by type + all 14 effect parameters unmapped (delay/reverb/drive chars)
- **Affected:** A039 (user=90: "delay on the Blofeld" — FX2=Clk.Delay mix 14, but the Blofeld delay
  parameters 1-14 are not translated → the Iridium delay runs on template default
  DelayDelayL/R=0.30/0.35, DelaySync=Off, DelayFeed=0.75), A073 ("different effects": FX2=Delay mix 11
  + FX1=Chorus mix 58), A001 (FX2=Clk.Delay), A008 (FX2=**Chorus** mix 24 → lands in `DelayDryWet`=0.189,
  `ChorusDryWet` stays 0.0 from FX1 — visible in the qpat), A022 (FX2=Overdrive mix 11 → `DelayDryWet` 0.087).
- **Evidence:** qpat_map.py:468-475: `mixkey = {1: "ChorusDryWet", 2: "DelayDryWet"}.get(n)` (line 473) — the key
  depends on the FX slot, not on the mapped type. `unmapped` contains all "Effect N Parameter 1-14"
  (MAPPING-MASTER.md:130-159 ❌). Blofeld Clk.Delay parameters per the manual (blofeld.txt:2442+): Length
  (1/96..10 bars, note-value synced), Feedback 0..127, Cutoff (feedback HF damping), Polarity, Spread.
  Iridium equivalents (v15 doc): `DelaySync` (0/1), `DelayLeftSync/RightSync` (note values), `DelayDelayL/R`,
  `DelayFeed`, `DelayHiCut`, `DelayDryWet`, `DelayXPan`.
- **Root cause:** qpat_map.py:473 (wrong mix key) + FX parameters completely unmapped (lines 468-475).
- **Fix:** (a) choose the mix key from the mapped type: Chorus→`ChorusDryWet`, Delay→`DelayDryWet`, Phaser→
  `PhaserDryWet`, Flanger→`FlangerDryWet`, Reverb→`ReverbDryWet`(if present), Drive→`DriveDryWet`;
  (b) for Blofeld "Delay"/"Clk.Delay" on FX2: `DelayDryWet=norm(Mix)`, `DelayFeed=norm(Feedback param)`,
  `DelayHiCut≈norm(Cutoff)`, for Clk.Delay additionally `DelaySync=1.0` + `DelayLeftSync/RightSync` from
  Length (Blofeld note value → Iridium SyncRatio index, analogous to `iridium_sync_ratio_index`); (c) Chorus:
  `ChorusSpeed/Depth` from the Blofeld chorus parameters.
- **Test:** A008: `DelayDryWet` must not be set when FX2=Chorus, `ChorusDryWet==norm(24)`;
  A039: `ov["DelaySync"][0]==1.0` and `DelayFeed` set; A001 FX2 Clk.Delay analogous.

### P1-4 Missing Blofeld mod destinations in BLOFELD_MOD_DST → slots get dropped (incl. A019's only AT slot)
- **Affected:** A019 (M4 **Pressure→F1 Drive** amt 113 → unmapped → "does not react to aftertouch";
  additionally M3 Keytrack→AE Release unmapped), A001 (M9 Mod Wheel→F1 Drive amt 116 unmapped),
  A008 (M1 Env3→RMod Level, M2 Env3→F1 Drive, M3 Env3→NoiseLevel, M6/M7/M16 Keytrack→O2/O3 FM,
  M10 Keytrack→FE Release, M11 Vel→M1 Amount, M14 MW→LFO1Speed — all unmapped), A010 (M1/M2 Env3→O1/O3 FM,
  M11 Vel→M1 Amount, M12/M13 MW→M3/M4 Amount, M15 Vel→F2 Pan), A022 (M2/M3 Control W→O2/O3 Level —
  "Control W" is also missing in BLOFELD_MOD_SRC!, M4 Pressure→LFO2Speed, M7-9 MW→LFO1/2Speed, M10-12 Modifier1→...,
  M13 LFO2→F2 Pan), A071 (M5 Pressure→O1 FM, M6 Unisono V.→F2 Pan, M8 MW→F1 Drive), A073 (M1 MW→O2 FM).
- **Evidence:** `unmapped` list of the mapping output per preset (85 entries on A008); BLOFELD_MOD_DST
  (qpat_map.py:105-112) only covers Pitch/Osc-Pitch/Osc-Level/F1-F2 Cutoff+Reso/FE A+D+S/Volume.
  Blofeld destination enums (blofeld_dump.py:47-48): F1/F2 Drive, F1/F2 FM, F1/F2 Pan, LFO1-3Speed, Volume, ...
  The Iridium side has destinations for those (manual appendix os3.txt:7700+): "DF Color", "DF Pan", "DF Level",
  "Filter 1/2 Pan/Level", "LFO1-6 Speed", "AmpEnv Attack/Decay/Release", "FXn DryWet/Control", "Drive Amount"...
- **Root cause:** qpat_map.py:105-112 (incomplete dst table) + :94-103 (src table without "Control W",
  "Modifier 1-4", "Unisono V.").
- **Fix (at least):** "AE Attack/Decay/Release" → AmpEnv dst (v14: Attack=109, Decay/Sustain/Release per
  exports 110/111/112-region — verify on the device), "LFO1Speed..3" → "LFO1..3 Speed" dst (v14: 145/…),
  "F1 Drive"/"F2 Drive" → serial: "DF Color" (96.0), parallel: nearest drive — or FX Drive Amount;
  "F2 Pan" → "DF Pan"; "O1/O2/O3 FM" and "RMod Level"/"NoiseLevel"/"M1-4 Amount" document as unmapped
  (no 1:1 source). "Control W" → "Wheel" (Control W = second wheel on the Blofeld? verify).
- **Test:** A019: Pressure slot present (src 16.0, dst not Off); number of unmapped mod slots decreases;
  assert no active Blofeld slot with a known dst lands in unmapped.

---

## P2 — calibration / approximations (measure after P0/P1)

### P2-1 `amt_bipolar()` scales bipolar amounts half (or double) — calibrate against the device
- **Evidence:** qpat_map.py:183-187: `0.5 + (raw-64)/254` — the docstring claims "127 -> 1.0", the code delivers 0.748.
  Test `test_mod_matrix_slots_mapped` codifies /254. User evidence contradicts "too weak": A001
  "LFO1 filter acts **too strong**" (LFO1→F1 Cutoff amt raw 103 → 0.6535), A043 "strong AT bending"
  (AT→Pitch raw 84 → 0.5787). I.e. the Iridium MatrixAmount 0..1 is apparently **not** ±100% around 0.5,
  but larger (direction ±200%: 0.6535 ≈ +131% instead of Blofeld +61%). In contrast Vel→Volume
  (line 455) uses `0.5+0.5*norm` (full scale) — inconsistent.
- **Fix:** read out a slot amount scale on the device (panel shows %); then set the divisor: Blofeld
  (raw-64)/64 = ±100% → Iridium value such that the panel shows ±100% (presumably `0.5 + (raw-64)/64*0.25`,
  i.e. /256, if 1.0=+200%). Uniform for amt_bipolar AND Vel→Volume.
- **Test:** parameterized divisor; test against the documented anchor (panel % at raw 64/127/0).

### P2-2 "LFOx*Press" sources become flat "After Touch" (LFO multiplier is lost)
- **Affected:** A043 M1 (LFO2*Press→Pitch amt 84 → slot AT→Pitch 0.579 constant bending share —
  user: "strong aftertouch bending").
- **Root cause:** qpat_map.py:96-97 (`"LFO1*Press": "After Touch"` etc.) — Blofeld semantics is
  LFO signal × pressure, not pure pressure.
- **Fix:** either drop the slot entirely (no constant AT share) or as AT with reduced amount;
  best a device check whether Iridium src "After Touch" × LFO via 2 slots (AT→LFO gain) is possible.
- **Test:** A043: dst Pitch with src AT only from the real Pressure slot (M2), not from M1.

### P2-3 FM (Osc N FM Source/Amount) not mapped → "different character in high registers"
- **Affected:** A010 Wurly (user=80: "hollow square wave in high registers"; Osc1 FM←Osc2 amt **80**,
  Osc3 FM←Osc2 amt 80), A008 (Osc2 FM←Osc3 amt 35), A073 (M1 MW→O2 FM).
- **Root cause:** qpat_map.py:280-282 (FM Source/Amount in unmapped). The Iridium has no matrix osc source;
  FM runs via kernel mode (`OscNWaveformDesity` = kernel count, qpat_map.py:270 sets 0.0 = 1 kernel).
- **Fix:** approximation via kernel: osc with FM source → `OscNWaveformDesity` > 0 with a kernel FM template
  (manual os3.txt:2606+ "FM bells" kernel), amount → FM index; or document as unmapped.
  Check A010 on the device first whether missing FM really explains the high-register character.
- **Test:** A010: if FM Amount>0 → `Osc1WaveformDesity` > 0 set.

### P2-4 Wavetable bridge gaps: Blofeld WTs without an Iridium equivalent stay on template "Resonant" (0.0)
- **Affected:** A022 Osc1 "Fat Organ" (user=95: "mid harmonic louder on the Blofeld"), A071 Osc1 "Alt 1",
  Osc2 "Resonant2" (user=70, next to sync the 2nd reason for the different SYNC2FM character).
- **Root cause:** qpat_map.py:44-51 (`BLOFELD_WAVETABLE_TO_IRIDIUM`) + :249-253 (unmapped → table stays 0).
- **Fix:** extend the bridge table with the frequent Blofeld WTs (choose the next Iridium WT by ear/CLAP,
  e.g. "Organ Syn"=14 for Fat Organ); leave the rest as unmapped.
- **Test:** A022: `Osc1WavetableTable != 0.0` after the extension.

### P2-5 Further known deviations (doc level, no acute user finding)
- LFO free speed: `norm(raw)` (qpat_map.py:392) uncalibrated against the Iridium Hz scale (can reinforce
  "LFO1 acts too strong", A001) — anchor-based Hz calibration like for glide/cutoff to follow.
- Mixer Balance → `OscNPan` (qpat_map.py:279) is semantically wrong (MAPPING-MASTER ⚠️): in parallel
  balance sets the F1/F2 share, not stereo pan; better `OscNDestination` DF/Fil share. Mono measurement
  masks it (peaks ok), in the stereo image wrong (A010/A019/A043 Balance=0 → Pan 0.0 hard left).
- `OscNFinePitch = norm(Detune)` (qpat_map.py:277): Blofeld detune bipolar ±64 cent around raw 64 —
  norm() scales to the full Iridium range (A008 Osc1 Detune raw 126 → 0.992 ≈ +98 instead of +62 cent).
- "Osc Pitch Source/Amount" (global pitch mod, on A008 = LFO1*MW amt 74, A019/A043/A071 amt 64)
  unmapped (qpat_map.py:285).
- Amp `Mod Source/Amount` (A008: AmpEnv, A019/A043/A010/A022/A039/A071/A073: LFO3 amt 64) unmapped —
  Iridium equivalent would be a matrix slot → Volume.

## What is NOT in the qpat mapping (out of scope, hardware/protocol)
- Iridium PC switching broken (no NRPN pid 3113) → manual-panel workaround (HANDOVER-2026-11-14).
- Raw level of the Iridium generally low (Scarlett gain In 5/6 / Iridium master) — `norm_pegel` compensates
  on the measurement side; does NOT explain the serial outliers (after norm they are only ~1 dB apart in RMS,
  but the crest factor/DF defect remains audible).
- A008 "presumably 1 octave lower": CoarsePitch values in the qpat are consistent with the raw values
  (Osc2/3 = 24.0, Osc1 = 64.0 but Vol=0); d1 `octave_lower` only p=0.50. Hypothesis: psychoacoustic due to
  the closed filter (F1 raw 22 ≈ 39 Hz + DF) — re-test after P0-1/P1-2 before touching the osc mapping.

## Suggested order
1. P0-1 (MatrixDst v14: 95/104/96) + P0-2 (AfterTouchDoPoly=0) — one rebuild of all 9 qpats, then 9-preset
   re-measurement (sim_manual_compare) + user rating; expected: serial peaks rise, `darker` flag disappears.
2. P1-1 sync (A071/A008), P1-2 serial F2 mods, P1-3 FX, P1-4 mod destination gaps.
3. P2 calibrations (amt_bipolar, LFO speed, WT bridge) — each with a device anchor.

All tests in `tests/test_qpat_map.py` must be adjusted along (they partly codify the v8 values,
e.g. `test_mod_matrix_slots_mapped` with dst 103/105 and amt /254).
