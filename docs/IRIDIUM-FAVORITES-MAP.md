# Iridium Favorites-Mapping (PC-Steuerung) — definitiv, gemessen 2026-11-09

## Grundsatz

- **0200… sind Speicher-Slots** (Load-Ansicht). Per **MIDI PC wählt man nur Favorites**
  (Favorites-Tab, OS4: 20 Blöcke pro Set, Sets 1–12).
- Display zeigt z. B. **`0206 (MIDI 106)`** = Slot 0206, Favorites-MIDI-Nummer 106.
- **mido-PC = Display-"MIDI" − 2** (empirisch; z. B. SH Power „MIDI 113“ = mido PC 111).
- Slot-Anzeige = MIDI-Nummer + 100 (MIDI 106 → Slot 0206).

## Aktives Favorites-Set (Bank/Set 6) — Inhalt

| Display MIDI | mido PC | Slot | Inhalt | Quelle |
|---|---|---|---|---|
| 100 | 98 | 0200 | cutoff 0.10 (1. Testsound) | `transfer/upload/calib/200_cutoff_0.10.qpat` |
| 101 | 99 | 0201 | cutoff 0.25 | `calib/201_cutoff_0.25.qpat` |
| 102 | 100 | 0202 | cutoff 0.41 | `calib/202_cutoff_0.41.qpat` |
| 103 | 101 | 0203 | cutoff 0.60 | `calib/203_cutoff_0.60.qpat` |
| 104 | 102 | 0204 | cutoff 0.80 | `calib/204_cutoff_0.80.qpat` |
| 105 | 103 | 0205 | cutoff 1.00 (letzter Testsound) | `calib/205_cutoff_1.00.qpat` |
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

In Code gespiegelt: `DEFAULT_MAP` + `CALIB_MAP` in `scripts/sim_sweep_pcs.py`
(sim_cc_sweep.py importiert DEFAULT_MAP).

## Wichtige Fallen

- **rdb-.mimap geladen** (`docs/midi-maps/iridium_rdb.mimap`): CC0 = Filter1 Cutoff,
  CC7 = Filter1 Amount, CC32 = OSC1 Fine Pitch. **Set/Bank ist per MIDI NICHT mehr
  wählbar** (CC0/CC32 sind Parameter!) — Favorites-Set nur am Gerät wechseln.
  CC7=0 stummt damit NICHT mehr; CC7 am Iridium nie anfassen (außer beim Sweep).
- Am **Blofeld** bleibt CC0/CC32 = Bank select → Skripte senden CC0=0 (Bank A) vor
  jedem PC, sonst landet der PC in der aktive Bank (B008-Falle).
- Slot 0206 = v15init (Cutoff 0.10 ≈ 18 Hz) — bei höheren Noten praktisch stumm;
  NIEMALS als Mess-Referenz verwechseln mit A008 (mido PC 106 = Slot 0208!).

## Test-Sounds löschen (Session von vorn)

Am Gerät (OS4):
1. **Favorites-Einträge MIDI 100–106 löschen**: Favorites-Tab → Set 6 → Block
   antippen → lange halten → **Clear** (OS4-Handbuch: „Clear the selected block“).
2. **Speicher-Slots 0200–0206 löschen**: Load-Ansicht → Slot wählen → Delete/Clear.
3. Optional komplett frisch: alle Favorites/Slots löschen und `transfer/upload/`
   per Stick neu importieren (Load > Actions > Import → Favorites Set 6).

Danach bleibt: Favorites MIDI 107–115 = die 9 konvertierten Sounds (mido 105–113).
