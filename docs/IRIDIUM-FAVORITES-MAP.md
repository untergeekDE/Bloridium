# Iridium Favorites mapping (PC control) — measured 2026-11-09

> Slot and Favorites contents change between sessions. The authoritative slot list for
> scripts is `DEFAULT_MAP` in `scripts/sim_sweep_pcs.py`; use this page for the PC-number
> convention and the traps.

## Principle

- **0200… are storage slots** (Load view). Via **MIDI PC you only select Favorites**
  (Favorites tab, OS4: 20 blocks per set, sets 1-12).
- The display shows e.g. **`0206 (MIDI 106)`** = slot 0206, Favorites MIDI number 106.
- **mido PC = display "MIDI" - 2** (empirical; e.g. SH Power "MIDI 113" = mido PC 111).
- Slot display = MIDI number + 100 (MIDI 106 -> slot 0206).

## Active Favorites set (bank/set 6) — content

| Display MIDI | mido PC | Slot | Content | Source |
|---|---|---|---|---|
| 100 | 98 | 0200 | cutoff 0.10 (1st test sound) | `transfer/upload/calib/200_cutoff_0.10.qpat` |
| 101 | 99 | 0201 | cutoff 0.25 | `calib/201_cutoff_0.25.qpat` |
| 102 | 100 | 0202 | cutoff 0.41 | `calib/202_cutoff_0.41.qpat` |
| 103 | 101 | 0203 | cutoff 0.60 | `calib/203_cutoff_0.60.qpat` |
| 104 | 102 | 0204 | cutoff 0.80 | `calib/204_cutoff_0.80.qpat` |
| 105 | 103 | 0205 | cutoff 1.00 (last test sound) | `calib/205_cutoff_1.00.qpat` |
| 106 | 104 | 0206 | **v15init_cutoff010** | `calib/206_v15init_cutoff010.qpat` |
| 107 | 105 | 0207 | A001 JMX jun. | `A001_JMX_jun.qpat` |
| 108 | 106 | 0208 | A008 Easy Piano HS | `A008_Easy_Piano_HS.qpat` |
| 109 | 107 | 0209 | A010 Wurly Piano1 HM | `A010_Wurly_Piano1_HM.qpat` |
| 110 | 108 | 0210 | A019 Tines DocT | `A019_Tines_DocT.qpat` |
| 111 | 109 | 0211 | A022 ModWheelOrgDrive | `A022_ModWheelOrgDrive.qpat` |
| 112 | 110 | 0212 | A039 A Elektro | `A039_A_Elektro.qpat` |
| 113 | 111 | 0213 | A043 SH Power | `A043_SH_Power.qpat` |
| 114 | 112 | 0214 | A071 Windowed SYNC2FM | `A071_Windowed_SYNC2FM.qpat` |
| 115 | 113 | 0215 | A073 Chord Hose T | `A073_Chord_Hose_T.qpat` |

Mirrored in code: `DEFAULT_MAP` + `CALIB_MAP` in `scripts/sim_sweep_pcs.py`
(sim_cc_sweep.py imports DEFAULT_MAP).

## Important traps

- **rdb .mimap loaded** (`docs/midi-maps/iridium_rdb.mimap`): CC0 = Filter1 Cutoff,
  CC7 = Filter1 Amount, CC32 = OSC1 Fine Pitch. **With this map loaded, set/bank is NO LONGER
  selectable via MIDI** (CC0/CC32 are parameters!) — switch the Favorites set only on the device.
  In that state CC7=0 no longer silences; never touch CC7 on the Iridium (except during the sweep).
  Without a custom map, CC7 is the main Output Level and CC7 = 0 is silent.
- On the **Blofeld**, CC0/CC32 remain bank select → the scripts send CC0=0 (Bank A) before
  every PC, otherwise the PC lands in the active bank (B008 trap).
- Slot 0206 = v15init (Cutoff 0.10 ≈ 18 Hz) — practically silent at higher notes;
  NEVER confuse it as a measurement reference with A008 (mido PC 106 = slot 0208!).

## Deleting test sounds (start the session from scratch)

On the device (OS4):
1. **Delete Favorites entries MIDI 100-106**: Favorites tab → Set 6 → block
   tap → hold → **Clear** (OS4 manual: "Clear the selected block").
2. **Delete storage slots 0200-0206**: Load view → select slot → Delete/Clear.
3. Optional full reset: delete all Favorites/slots and re-import `transfer/upload/`
   via stick (Load > Actions > Import → Favorites Set 6).

After that remains: Favorites MIDI 107-115 = the 9 converted sounds (mido 105-113).
