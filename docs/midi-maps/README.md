# Iridium MIDI Maps & Pid table

## Files

| File | Content |
|---|---|
| `midimap0.mimap` | Factory MIDI map (2017, exported from the device): only CC3-CC8 assigned, pids 2102/2103/3699/3700/2112/2113 |
| `iridium_rdb.mimap` | Ready-made .mimap from @rdb (squarp.community/t/waldorf-iridium/9276, 2023-03-24): CC0, CC2-CC116 -> pid, "most useful" selection (max. 119 entries) |
| `iridium_hapax_L1.def.txt` | Matching Squarp Hapax instrument definition (layer 1, ch1); `[CC]` section resolves CC -> parameter name. Layer 2 = TRACKNAME "Iridium L2", OUTCHAN 2 |
| `iridium_pid_map.csv` | Combined: `cc, pid_rdb_2023, parameter_name, pid_werks_2017_midimap0, cc_midi_guide_csv` (116 rows) |
| `iridium_midi_guide.csv` | Official CC list (116 CCs, nrpn columns empty) |

## Findings

- **CC -> name from the rdb map matches `iridium_midi_guide.csv` 1:1.**
- **CC0 -> pid 966 = Filter1 Cutoff** (rdb map): F1 Cutoff has no CC in the
  factory map/CSV, but can be assigned to CC0 via .mimap -> solves the HANDOVER point
  "F1 Cutoff has no CC".
- **CC7 discrepancy:** factory map 2017: CC7->2112 (behaves as Output/Main Level,
  CC7=0 = silent). rdb map 2023: CC7->969 = Filter1 Amount. -> **Pid numbers are
  firmware-dependent** (2017 vs 2023).
- Thread warning (2024/2025): since FW 3.2 the .mimap format may have changed;
  on OS4 (our device) **untested**. Verify before use on the device
  (e.g. send CC0 -> does Filter1 Cutoff change on the display?).

## Loading on the Iridium

Copy the .mimap to an SD/USB stick -> on the device `Global > MIDI > Mappings > Load`.

## NRPN

Incoming NRPN are **ignored** by the Iridium (OS3 manual: "Iridium doesn't react
on incoming NRPN MIDI data") — NRPN only outgoing (panel -> automation). Control paths:
CC (via .mimap/MIDI Learn), PC (only Favorites), qpat import (stick).
