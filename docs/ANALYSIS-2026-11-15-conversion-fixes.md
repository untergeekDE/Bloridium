# Analyse 2026-11-15: Was muss an der qpat-Sound-Umwandlung noch gefixt werden?

Subagent-Analyse (nur read-only/offline: Dumps, qpats, Logs, Referenzen; kein MIDI, keine Code-Aenderung).
Methode: systematic-debugging (Phase 1 Root Cause + Phase 2 Pattern) — jede Aussage unten ist gegen
Roh-Dump (`bloridium bank show <LOC>` / `dumps/blofeld_sndd_<LOC>_*.bin`), generiertes qpat
(`qpat info transfer/upload/*.qpat` + direkter Vergleich override vs. qpat-Wert), `qpat_map.py`,
eigene OS4-Exporte (`dumps/export-001`, v14) und Iridium-Handbuch (`docs/manual-text/iridium_os3.txt`)
abgesichert. Alle 9 generierten qpats sind **qpat v14** (`workflow.py:138`: "Zielgeraet OS4 erwartet v14").

## Evidenz-Basis (Live-A/B 2026-11-14, Set 6 PC108-116, Note 72, mode=manual_panel)

| Preset | User 0-100 | User-Bemerkung (Kern) | Phase A | combined | Peak A/B dBFS | Routing |
|---|---|---|---|---|---|---|
| A001 JMX jun | 70 | Leiser, Filter zu weit geschlossen, LFO1-Filter zu stark | 92.86 | 84.22 | -19.4 / **-47.9** | seriell |
| A008 Easy Piano | **45** | Kaum hörbar, vermutl. 1 Oktave tiefer, stark abgefiltert | 95.20 | 82.28 | -25.6 / **-64.8** | seriell |
| A010 Wurly | 80 | Hohe Lagen anderer Charakter (hohle square wave) | 97.00 | 87.61 | -44.2 / -42.8 | parallel |
| A019 Tines | 90 | Reagiert nicht auf Aftertouch | 95.05 | 91.41 | -29.4 / -45.5 | parallel |
| A022 ModWheelOrg | 95 | Mittl. Oberton am Blofeld lauter | 94.74 | 89.18 | -15.5 / -29.2 | seriell |
| A039 A Elektro | 90 | Viel leiser; Delay beim Blofeld | 96.07 | 86.64 | -37.9 / -55.3 | seriell |
| A043 SH Power | 75 | Blofeld voller; Iridium stark AT-Bending (Channel->Poly AT) | 95.02 | 86.70 | -19.3 / -35.6 | parallel |
| A071 Windowed SYNC2FM | 70 | **Kein Sync beim Iridium** | 94.38 | 90.54 | -23.2 / -40.6 | seriell |
| A073 Chord Hose | 85 | Unterschiedliche Effekte, Blofeld schneidender | 96.63 | 88.82 | -27.0 / -53.9 | seriell |

Quellen: `recordings/phaseb_ratings_raw.json`, `recordings/sim_log.jsonl` (ts 20261114_175046-180616,
`norm_pegel=true`), `docs/PHASEB-EVAL-2026-11-14.md`, `transfer/upload/MANIFEST.md`.
Zusatz-Evidenz: d1-omni:2b-Profil `darker` 9/9 (2b) bzw. 7/9 (600m), `octave_lower` nur A008 grenzwertig
(p=0.50) — deckt sich mit "Filter zu / abgefiltert" bei allen, Octave-Verdacht A008 nur schwach.

**Muster (Phase 2):** Alle 6 seriellen Patches (A001 A008 A022 A039 A071 A073) haben Iridium-Peaks
15-40 dB unter dem Blofeld (bis -64.8 dBFS) und alle seriellen User-Texte beschweren sich ueber
"zu/leiser/abgefiltert" — das ist kein Zufall, sondern ein systematischer Defekt im seriellen Pfad
(siehe P0-1). Die parallelen Patches (A010 A019 A043) haben normale Pegel und ihre Beschwerden
betreffen Matrix/FX-Detail (Sync, AT, FM, Drive) — siehe P0-2/P1.

---

## P0 — serielle Patches zu dunkel/zu leise (alle 6 seriellen Presets)

### P0-1 MatrixDst-Enum-Werte sind v8-Werte in v14-Dateien: "DF Amount"=71 statt **95**, "Filter2 Cutoff"=103 statt **104**
- **Betroffen:** A001, A008, A022, A039, A071, A073 (seriell) — der extra Slot `Filter1 Env -> DF Amount`
  (qpat_map.py:461-466) landet mit `MatrixDst = 71.0` (qpat_map.py:89, Kommentar "v14-Wert aus qpat_params_v8.md")
  auf einem **v14-falschen Ziel**; ebenso "Filter2 Cutoff"=103 (qpat_map.py:85).
- **Evidenz:** Eigene OS4-Exporte (v14, `dumps/export-001`): pro Slot auswertung zeigt in v14 konsistent
  `DF Amount = 95.0` (Slots 2/4/5/9), `Filter1 Cutoff = 100`, `Filter1 Reso = 101`, `Filter2 Cutoff = 104`,
  `Filter2 Reso = 105`; 71/103 kommen in v14 **gar nicht vor** (in v8-Factories dagegen: 71=DF Amount n=234,
  103=Filter2 Cutoff). Die gebauten qpats sind v14 (`qpat info`: Version 14) — im Geraet ist dst 71/103 ein
  anderes Ziel (WT/RS-/Filter-Pan-Bereich). Damit macht der Slot, der den DigiFormer per Filter-Env oeffnen
  soll (HANDOVER-2026-11-14: "sonst bleibt der Former statisch zu ... -66 dBFS"), **gar nichts** →
  serielle Kette bleibt F1-cutoff + statischer, evtl. sehr geschlossener Former → genau die beobachteten
  -40 bis -64.8 dBFS Peaks und "Filter zu weit geschlossen" (A001), "kaum zu hoehren" (A008),
  "viel leiser" (A039), d1 `darker` 9/9.
- **Root Cause:** `bloridium/qpat_map.py:89` (`"DF Amount": 71.0`) und `:85` (`"Filter2 Cutoff": 103.0`) —
  v8-Enum in v14-Output (Mischung: Filter12Type wurde 2026-11-14 auf v14 korrigiert, MATRIX_DST nicht).
- **Fix:** MATRIX_DST fuer v14: `"DF Amount": 95.0`, `"DF Color": 96.0` (v14: 96='DF Color'), `"Filter2 Cutoff": 104.0`,
  `"Filter2 Reso": 105.0` (Rest 100/101/113/114/123/144/1-11/18/39/46/67/74/76 bereits v14-konform).
  Aenderung betrifft alle 9 qpats (Seriell-Slot + F2-Mod-Slots).
- **Test:** `tests/test_qpat_map.py` — neuer Test: fuer A001 `MatrixDst{df_slot} == 95.0`; Regression:
  assert alle in v14-Exporten belegten dst-Werte gegen eine hartkodierte v14-Tabelle; bestehender Test
  `test_mod_matrix_slots_mapped` (asserted 100/101/103/105...) muss auf 104 angepasst werden.
  Device-Check: ein serieller Patch (A001) laden, Matrix-Slot mit dst 95 am Panel als "DF Amount" angezeigt?

### P0-2 Aftertouch: globales `AfterTouchDoPoly` bleibt auf Template-Default 1.0 (Poly AT) → Channel AT wirkt nicht / falsch
- **Betroffen:** A019 ("reagiert nicht auf Aftertouch", user=90), A043 ("stark Aftertouch-Bending; Problem
  Channel AT (Blofeld) -> Poly AT (Iridium)", user=75).
- **Evidenz:** qpat_map.py setzt `AfterTouchDoPoly` nie. Template **und alle eigenen v14-Exporte** haben
  `AfterTouchDoPoly = 1.0 'Poly AT'`. Iridium-Handbuch (os3.txt:5387): global waehlbar Mono AT / Poly AT;
  Appendix (os3.txt:7660): Matrix-Source "After Touch" = **"Polyphonic Keyboard Pressure Data"**.
  Blofeld "Pressure" ist Channel Aftertouch → mit DoPoly=1 reagiert die Matrix nicht auf Channel AT.
  A043 hat zusaetzlich 2 AT-Slots (M1 LFO2*Press→Pitch amt 84, M2 Pressure→O2 Pitch amt 43 →
  MatrixSrc 16.0, qpat_map.py:80), die bei Poly AT pro Note biegen ("starkes Bending").
- **Root Cause:** `qpat_map.py` — fehlt komplett (kein `setp("AfterTouchDoPoly", ...)`); `MATRIX_SRC`
  "After Touch": 16.0 (Zeile 80) — in v14-Exporten tauchen 16 **und** 17 mit Display 'After Touch' auf
  (16=channel?, 17=poly? — am Geraet klaeren).
- **Fix:** in `blofeld_to_qpat_params` fuer alle Patches `setp("AfterTouchDoPoly", 0.0, "Mono AT")`
  (Blofeld sendet Channel AT), MatrixSrc AT vorerst 16.0 lassen; am Geraet mit Channel AT gegen 17 testen.
- **Test:** neuer Test: `ov["AfterTouchDoPoly"][0] == 0.0` fuer alle 9 Dumps; Device-Check: A043 laden,
  Channel AT senden → Pitch biegt nur ueber M2 (amt 43→0.417), nicht doppelt.

---

## P1 — konkrete Feature-Luecken mit User-Evidenz

### P1-1 Hard Sync wird nicht uebersetzt: "Osc 2 Sync to O3" landet in `unmapped`
> **Deprioritized 2026-11-15 (User):** Windowed-Sync-Sounds (A071, Sound 215) nutzen eine
> experimentelle, Blofeld-spezifische Technik -> niedrige Prioritaet, nach P2.
- **Betroffen:** A071 Windowed SYNC2FM (user=70: **"Kein Sync beim Iridium"**), A008 (raw `Osc 2 Sync to O3 = 1`).
- **Evidenz:** Dump A071/A008: `Osc 2 Sync to O3 = 1`. qpat_map.py:285: `unmapped += ["Osc 2 Sync to O3", ...]`;
  in den qpats ist `Osc2WaveformSync = 0.0` (template default). Handbuch os3.txt:1680: Osc-Sync =
  "typische Oszillator-Synchronisation"; qpat-Param existiert: `Osc2WaveformSync` (v15 doc line 977;
  v8-Factories nutzen Werte 0.02-0.70, d.h. 0..1-Skala, 0=off). Zusaetzlich Matrix-Dst "WF2 Sync" existiert
  (v8: 37; v14-Wert am Geraet pruefen).
- **Root Cause:** qpat_map.py:285 (bewusst unmapped) — keine Stelle setzt `OscNWaveformSync`.
- **Fix:** `if p.get("Osc 2 Sync to O3"): setp("Osc2WaveformSync", 1.0, "Sync on")` (Wert 1.0 = voller Sync;
  genaue Amount-Skala am Geraet, evtl. 0.5 default). Betrifft A071 (Osc2 ist Wavetable 'Resonant2' —
  pruefen ob WaveformSync bei WT-Osc greift, sonst Matrix-Slot src LFO? -> Device-Check).
- **Test:** `test_osc2_sync_mapped_a071`: Dump A071 → `ov["Osc2WaveformSync"][0] == 1.0`; A001 (Sync=0) → nicht gesetzt/0.0.

### P1-2 Serielle F2-Modulationen zielen auf die abgeschaltete Filter-2-Stufe (und falsches Enum)
- **Betroffen:** A001 (Filter 2 Mod Source=Velocity amt 107 → Slot `Velocity -> Filter2 Cutoff` dst 103),
  A071 (M7 LFO3→F2 Cutoff amt 13 → dst 103; M9 MW→F2 Reson. amt 100 → dst 105), A022 (M11 Modifier1→F2 Cutoff,
  M15 MW→F2 Cutoff).
- **Evidenz:** qpat_map.py:435-447 (`d_disp = "Filter2 Cutoff"` Zeile 440) und BLOFELD_MOD_DST:109. Im seriellen
  Modus ist `Filter2State = Off` (qpat_map.py:328) — die Filter-2-Stufe ist aus; der hörbare F2 ist der
  DigiFormer. Modulationen auf "Filter2 Cutoff/Reso" gehen ins Leere (bzw. wg. P0-1 auf falsches Ziel).
  Konsequenz z.B. A001: Velocity oeffnet am Blofeld BEIDE Filter, am Iridium nur F1.
- **Root Cause:** qpat_map.py:435-447 + :109 — kein seriell-aware Remapping F2→DigiFormer.
- **Fix:** im seriellen Fall (`seriell and not f2_bypass`): Blofeld-Ziele "F2 Cutoff" → MatrixDst "DF Amount"
  (v14: 95.0), "F2 Reson." → "DF Color" (v14: 96.0); im parallelen Fall bleiben 104/105. Gleiches fuer den
  direkten Block `Filter 2 Mod Source/Amount` (Zeile 436-447, n=2 → dst "DF Amount").
- **Test:** A001: alle MatrixDst-Werte mit Display "Filter2 Cutoff" duerfen im seriellen qpat nicht vorkommen;
  stattdessen ein Slot mit dst 95.0 und src Velocity. A010 (parallel) behaelt 104.0.

### P1-3 FX-Block: Mix-Key nach Slot statt nach Typ + alle 14 Effekt-Parameter unmapped (Delay/Reverb/Drive-Chars)
- **Betroffen:** A039 (user=90: "Delay beim Blofeld" — FX2=Clk.Delay mix 14, aber DelayTime/Feedback/Cutoff
  der Blofeld-Parameter 1-14 werden nicht uebersetzt → Iridium-Delay laeuft auf Template-Default
  DelayDelayL/R=0.30/0.35, DelaySync=Off, DelayFeed=0.75), A073 ("unterschiedliche Effekte": FX2=Delay mix 11
  + FX1=Chorus mix 58), A001 (FX2=Clk.Delay), A008 (FX2=**Chorus** mix 24 → landet in `DelayDryWet`=0.189,
  `ChorusDryWet` bleibt 0.0 von FX1 — sichtbar im qpat), A022 (FX2=Overdrive mix 11 → `DelayDryWet` 0.087).
- **Evidenz:** qpat_map.py:468-475: `mixkey = {1: "ChorusDryWet", 2: "DelayDryWet"}.get(n)` (Zeile 473) — key
  haengt vom FX-Slot ab, nicht vom gemappten Typ. `unmapped` enthaelt alle "Effect N Parameter 1-14"
  (MAPPING-MASTER.md:130-159 ❌). Blofeld Clk.Delay-Parameter laut Handbuch (blofeld.txt:2442+): Length
  (1/96..10 bars, notenwert-synced), Feedback 0..127, Cutoff (Feedback-HF-Daempfung), Polarity, Spread.
  Iridium-Aequivalente (v15 doc): `DelaySync` (0/1), `DelayLeftSync/RightSync` (Notenwerte), `DelayDelayL/R`,
  `DelayFeed`, `DelayHiCut`, `DelayDryWet`, `DelayXPan`.
- **Root Cause:** qpat_map.py:473 (falsches Mix-Key) + FX-Parameter komplett unmapped (Zeilen 468-475).
- **Fix:** (a) Mix-Key aus dem gemappten Typ waehlen: Chorus→`ChorusDryWet`, Delay→`DelayDryWet`, Phaser→
  `PhaserDryWet`, Flanger→`FlangerDryWet`, Reverb→`ReverbDryWet`(falls vorhanden), Drive→`DriveDryWet`;
  (b) fuer Blofeld "Delay"/"Clk.Delay" auf FX2: `DelayDryWet=norm(Mix)`, `DelayFeed=norm(Feedback-Param)`,
  `DelayHiCut≈norm(Cutoff)`, bei Clk.Delay zusaetzlich `DelaySync=1.0` + `DelayLeftSync/RightSync` aus
  Length (Blofeld-Notenwert → Iridium-SyncRatio-Index, analog `iridium_sync_ratio_index`); (c) Chorus:
  `ChorusSpeed/Depth` aus Blofeld-Chorus-Parametern.
- **Test:** A008: `DelayDryWet` darf nicht gesetzt sein wenn FX2=Chorus, `ChorusDryWet==norm(24)`;
  A039: `ov["DelaySync"][0]==1.0` und `DelayFeed` gesetzt; A001 FX2 Clk.Delay analog.

### P1-4 Fehlende Blofeld-Mod-Ziele in BLOFELD_MOD_DST → Slots werden fallengelassen (u.a. A019s einziger AT-Slot)
- **Betroffen:** A019 (M4 **Pressure→F1 Drive** amt 113 → unmapped → "reagiert nicht auf Aftertouch";
  zusaetzlich M3 Keytrack→AE Release unmapped), A001 (M9 Mod Wheel→F1 Drive amt 116 unmapped),
  A008 (M1 Env3→RMod Level, M2 Env3→F1 Drive, M3 Env3→NoiseLevel, M6/M7/M16 Keytrack→O2/O3 FM,
  M10 Keytrack→FE Release, M11 Vel→M1 Amount, M14 MW→LFO1Speed — alle unmapped), A010 (M1/M2 Env3→O1/O3 FM,
  M11 Vel→M1 Amount, M12/M13 MW→M3/M4 Amount, M15 Vel→F2 Pan), A022 (M2/M3 Control W→O2/O3 Level —
  "Control W" fehlt auch in BLOFELD_MOD_SRC!, M4 Pressure→LFO2Speed, M7-9 MW→LFO1/2Speed, M10-12 Modifier1→...,
  M13 LFO2→F2 Pan), A071 (M5 Pressure→O1 FM, M6 Unisono V.→F2 Pan, M8 MW→F1 Drive), A073 (M1 MW→O2 FM).
- **Evidenz:** `unmapped`-Liste der Mapping-Ausgabe pro Preset (85 Eintraege bei A008); BLOFELD_MOD_DST
  (qpat_map.py:105-112) deckt nur Pitch/Osc-Pitch/Osc-Level/F1-F2 Cutoff+Reso/FE A+D+S/Volume ab.
  Blofeld-Ziel-Enums (blofeld_dump.py:47-48): F1/F2 Drive, F1/F2 FM, F1/F2 Pan, LFO1-3Speed, Volume, ...
  Iridium-Seite hat dafuer Destinations (Handbuch Appendix os3.txt:7700+): "DF Color", "DF Pan", "DF Level",
  "Filter 1/2 Pan/Level", "LFO1-6 Speed", "AmpEnv Attack/Decay/Release", "FXn DryWet/Control", "Drive Amount"...
- **Root Cause:** qpat_map.py:105-112 (unvollstaendige Dst-Tabelle) + :94-103 (Src-Tabelle ohne "Control W",
  "Modifier 1-4", "Unisono V.").
- **Fix (mindestens):** "AE Attack/Decay/Release" → AmpEnv-Dst (v14: Attack=109, Decay/Sustain/Release lt.
  Exporten 110/111/112-Region — am Geraet verifizieren), "LFO1Speed..3" → "LFO1..3 Speed"-Dst (v14: 145/…),
  "F1 Drive"/"F2 Drive" → seriell: "DF Color" (96.0), parallel: naechstes Drive — oder FX Drive Amount;
  "F2 Pan" → "DF Pan"; "O1/O2/O3 FM" und "RMod Level"/"NoiseLevel"/"M1-4 Amount" als unmapped dokumentieren
  (keine 1:1-Quelle). "Control W" → "Wheel" (Control W = zweites Wheel am Blofeld? verifizieren).
- **Test:** A019: Pressure-Slot vorhanden (src 16.0, dst nicht Off); Anzahl unmapped-Mod-Slots sinkt;
  assert kein aktiver Blofeld-Slot mit bekanntem Dst landet in unmapped.

---

## P2 — Kalibrierung / Approximationen (nach P0/P1 messen)

### P2-1 `amt_bipolar()` skaliert bipolar Amounts halb (oder doppelt) — gegen Geraet kalibrieren
- **Evidenz:** qpat_map.py:183-187: `0.5 + (raw-64)/254` — Docstring behauptet "127 -> 1.0", Code liefert 0.748.
  Test `test_mod_matrix_slots_mapped` kodifiziert /254. User-Evidenz widerspricht "zu schwach": A001
  "LFO1 Filter wirkt **zu stark**" (LFO1→F1 Cutoff amt raw 103 → 0.6535), A043 "stark AT-Bending"
  (AT→Pitch raw 84 → 0.5787). D.h. Iridium MatrixAmount 0..1 ist offenbar **nicht** ±100% um 0.5,
  sondern groesser (Richtung ±200%: 0.6535 ≈ +131% statt Blofeld +61%). Im Gegensatz dazu Vel→Volume
  (Zeile 455) nutzt `0.5+0.5*norm` (volle Skala) — inkonsistent.
- **Fix:** am Geraet eine Slot-Amount-Skala auslesen (Panel zeigt %); dann Divisor setzen: Blofeld
  (raw-64)/64 = ±100% → Iridium-Wert so, dass Panel ±100% zeigt (vermutlich `0.5 + (raw-64)/64*0.25`,
  also /256, falls 1.0=+200%). Einheitlich fuer amt_bipolar UND Vel→Volume.
- **Test:** parametrisierter Divisor; Test gegen dokumentierten Anker (Panel-% bei raw 64/127/0).

### P2-2 "LFOx*Press"-Quellen werden zu flachem "After Touch" (LFO-Multiplikator faellt weg)
- **Betroffen:** A043 M1 (LFO2*Press→Pitch amt 84 → Slot AT→Pitch 0.579 konstanter Bending-Anteil —
  user: "stark Aftertouch-Bending").
- **Root Cause:** qpat_map.py:96-97 (`"LFO1*Press": "After Touch"` etc.) — Blofeld-Semantik ist
  LFO-Signal × Pressure, nicht reines Pressure.
- **Fix:** entweder Slot ganz weglassen (kein konstanter AT-Anteil) oder als AT mit reduziertem Amount;
  am besten Device-Check, ob IridiumSrc "After Touch" × LFO ueber 2 Slots (AT→LFO-Gain) moeglich.
- **Test:** A043: dst Pitch mit src AT nur aus echtem Pressure-Slot (M2), nicht aus M1.

### P2-3 FM (Osc N FM Source/Amount) nicht gemappt → "anderer Charakter in hohen Lagen"
- **Betroffen:** A010 Wurly (user=80: "hohle square wave in hohen Lagen"; Osc1 FM←Osc2 amt **80**,
  Osc3 FM←Osc2 amt 80), A008 (Osc2 FM←Osc3 amt 35), A073 (M1 MW→O2 FM).
- **Root Cause:** qpat_map.py:280-282 (FM Source/Amount in unmapped). Iridium hat keine Matrix-Osc-Quelle;
  FM laeuft ueber Kernel-Modus (`OscNWaveformDesity` = Kernel-Count, qpat_map.py:270 setzt 0.0 = 1 Kernel).
- **Fix:** Approximation ueber Kernel: Osc mit FM-Source → `OscNWaveformDesity` > 0 mit Kernel-FM-Template
  (Handbuch os3.txt:2606+ "FM bells"-Kernel), Amount → FM-Index; oder als unmapped dokumentieren.
  A010 zuerst am Geraet pruefen, ob fehlendes FM wirklich den Hochton-Charakter erklaert.
- **Test:** A010: wenn FM Amount>0 → `Osc1WaveformDesity` > 0 gesetzt.

### P2-4 Wavetable-Bridge-Luecken: Blofeld-WTs ohne Iridium-Aequivalent bleiben auf Template "Resonant" (0.0)
- **Betroffen:** A022 Osc1 "Fat Organ" (user=95: "mittl. Oberton am Blofeld lauter"), A071 Osc1 "Alt 1",
  Osc2 "Resonant2" (user=70, neben Sync der 2. Grund fuer anderen SYNC2FM-Charakter).
- **Root Cause:** qpat_map.py:44-51 (`BLOFELD_WAVETABLE_TO_IRIDIUM`) + :249-253 (unmapped → Table bleibt 0).
- **Fix:** Bridge-Tabelle um die haeufigen Blofeld-WTs erweitern (naechstes Iridium-WT per Ohr/CLAP waehlen,
  z.B. "Organ Syn"=14 fuer Fat Organ); Rest als unmapped lassen.
- **Test:** A022: `Osc1WavetableTable != 0.0` nach Erweiterung.

### P2-5 Weitere bekannte Abweichungen (Doku-Level, kein akuter User-Befund)
- LFO free Speed: `norm(raw)` (qpat_map.py:392) unkalibriert gegen Iridium-Hz-Skala (kann "LFO1 wirkt zu
  stark" verstaerken, A001) — Hz-Kalib ankerbasiert wie bei Glide/Cutoff nachziehen.
- Mixer Balance → `OscNPan` (qpat_map.py:279) ist semantisch falsch (MAPPING-MASTER ⚠️): in parallel
  haengt Balance den F1/F2-Anteil, nicht Stereo-Pan; besser `OscNDestination` DF/Fil-Anteil. Mono-Messung
  kaschiert es (Peaks ok), im Stereobild falsch (A010/A019/A043 Balance=0 → Pan 0.0 hart links).
- `OscNFinePitch = norm(Detune)` (qpat_map.py:277): Blofeld Detune bipolar ±64 cent um raw 64 —
  norm() skaliert auf volle Iridium-Range (A008 Osc1 Detune raw 126 → 0.992 ≈ +98 statt +62 cent).
- "Osc Pitch Source/Amount" (globaler Pitch-Mod, bei A008 = LFO1*MW amt 74, A019/A043/A071 amt 64)
  unmapped (qpat_map.py:285).
- Amp `Mod Source/Amount` (A008: AmpEnv, A019/A043/A010/A022/A039/A071/A073: LFO3 amt 64) unmapped —
  Iridium-Aequivalent waere Matrix-Slot → Volume.

## Was NICHT im qpat-Mapping liegt (Out of Scope, Hardware/Protokoll)
- Iridium-PC-Umschaltung defekt (kein NRPN Pid 3113) → Manual-Panel-Workaround (HANDOVER-2026-11-14).
- Roh-Pegel des Iridium generell niedrig (Scarlett-Gain In 5/6 / Iridium-Master) — `norm_pegel` kompensiert
  messseitig; erklaert NICHT die seriellen Ausreisser (die bleiben nach Norm im RMS nur ~1 dB auseinander,
  aber der Crest-Faktor/DF-Defekt bleibt hörbar).
- A008 "vermutl 1 Oktave tiefer": CoarsePitch-Werte im qpat sind konsistent mit den Rohwerten
  (Osc2/3 = 24.0, Osc1 = 64.0 aber Vol=0); d1 `octave_lower` nur p=0.50. Hypothese: psychoakustisch durch
  den zugeschnuerten Filter (F1-Rohwert 22 ≈ 39 Hz + DF) — nach P0-1/P1-2 re-testen, bevor Osc-Mapping
  angefasst wird.

## Vorgeschlagene Reihenfolge
1. P0-1 (MatrixDst v14: 95/104/96) + P0-2 (AfterTouchDoPoly=0) — ein Rebuild aller 9 qpats, dann 9-Presets-
   Re-Messung (sim_manual_compare) + User-Rating; erwartet: serielle Peaks steigen, `darker`-Flag verschwindet.
2. P1-1 Sync (A071/A008), P1-2 serielle F2-Mods, P1-3 FX, P1-4 Mod-Dst-Luecken.
3. P2-Kalibrierungen (amt_bipolar, LFO-Speed, WT-Bridge) — jeweils mit Device-Anker.

Alle Tests in `tests/test_qpat_map.py` muessen mitgeaendert werden (sie kodifizieren tlw. die v8-Werte,
z.B. `test_mod_matrix_slots_mapped` mit dst 103/105 und amt /254).
