# Architektur-Differenzen Blofeld ↔ Iridium — und was daraus für die Konvertierung folgt

**Stand:** 2026-11-21 · **Grundlage:** Blofeld-Bedienhandbuch, Iridium-OS-4-Parameterdump
(`dumps/00000-.qpat`), Konverter (`bloridium/qpat_map.py`) und der Profiling-Sweep
(`docs/PROFILING-INIT-2026-11-21.md`, 752 Einzelmessungen).

Die beiden Synths sind keine Geschwister mit anderem Gehäuse. Der Blofeld ist ein
klassischer Subtractive-Synth mit zwei Multimode-Filtern und einem eigenen Noise-Mixer;
der Iridium ist ein Wavetable-/Kernel-Synth, bei dem viele Bausteine als *Oszillator-,
Filter- oder Matrix-Ziel* existieren, aber nicht als eigener Menüpunkt. Für jeden
Parameter gibt es daher drei Fälle:

1. **Direkt abbildbar** (gleiche Funktion, andere Skala) — z. B. Filter-Cutoff, Hüllkurven.
2. **Architektonisch anders, aber mit Workaround** — z. B. Noise als Wellenform,
   PWM über die Modulationsmatrix.
3. **Nicht abbildbar** — z. B. Filter-FM, Modifier-Rechenoperatoren, Arpeggiator-Pattern.

---

## 1. Kurzfassung

| Bereich | Blofeld | Iridium | Konsequenz | Workaround | Messung 2026-11-21 |
|---|---|---|---|---|---|
| **Rauschen** | eigener Noise-Generator im Mixer (Level, Balance, Colour 0–127) | **kein Noise-Mixer**; Noise ist eine Oszillator-Wellenform (White/Pink) oder Particle/Resonator-„Dirt“ | Noise braucht einen Oszillator-Slot | freien Osc als Noise: `OscNType=Waveform`, `WaveformShape=White/Pink`, Level→`OscNVol`, Balance→`OscNPan` | Level in der Tendenz richtig (cos 0,77–0,93), Kennlinie weicht ab; **Colour defekt** (nur 2 Stufen) |
| **PWM** | Oszillator-PWM mit Source + Amount, wirkt auf die **Pulsbreite** | statische PW (`OscNWaveformPW`); Modulation über Matrix-Ziel `WFn Warp` / `WTn Position` | Warp verändert die **ganze Wellenform**, nicht nur die Pulsbreite | Matrixzeile `Source → WFn Warp` nur bei pulsartigen Shapes, Wavetable → `WTn Position`; sonst bewusst ignorieren | **behoben (A1, 2026-11-21):** Saw/Triangle/Sine erzeugen keine Warp-Zeile mehr; Neumessung offen |
| **FM** | Osc-FM mit Source + Amount pro Oszillator | **kein FM-Eingang pro Osc**; FM lebt in den 6 Kernels (`V4OscNKernel*`) oder als Matrix→Pitch | nicht 1:1 | Kernels für echte FM-Klänge; Matrix→`OscN Pitch` nur für Vibrato-ähnliche Effekte | im Init nicht prüfbar (kein FM im Init) |
| **Sync** | ein Schalter „Osc 2 Sync to O3“ | `Osc2WaveformSync` (nur Waveform-Osc); Wavetable-Sync über `WavetableTravel(SyncRatio)` | Sync nur für Waveform-Osc direkt | `Osc2WaveformSync=1`; bei Wavetable-Osc WT-Travel/SyncRatio | Test D Sync nicht belastbar (zwei klingende Oscs → hohe Streuung) |
| **Filter-Topologie** | 2 Multimode-Filter; **Balance pro Klangquelle** (Osc/Ring/Noise) verteilt auf F1/F2; Routing parallel/seriell | 2 Filter mit `FilterLink` (Single/Boost/Independent/Linked) und `OscNDestination` (DF/F1/F2-Anteil) | Balance ist kein Pan, sondern eine Filter-Zuordnung | Balance → `OscNDestination`-Anteile, Routing → `FilterLink`, F2-Modell → DigiFormer | Direkttest: **Balance 0 = F1, 127 = F2; Routing 0 = parallel, 1 = seriell**. Konverter-Mapping für F2 noch nicht belastbar (Sweep-Variante inkonsistent) |
| **Filter-Drive** | Drive + 13 Drive-Kurven pro Filter | kein Filter-Drive; Drive ist ein FX (`DriveAmount`, `DriveGain`) | FX-Slot wird verbraucht | `FX1/FX2 = Drive`, Kurve über Drive-Typ annähern | Filter 1 Drive teilweise (cos 0,96; 0,81×) |
| **Filter-FM / Filter-Pan** | FM und Pan mit Source/Amount pro Filter | kein Filter-FM; Pan nur als Matrix-Ziel `FilterN Pan` | FM nicht abbildbar | Pan über Matrix; FM als „nicht unterstützt“ markieren | Filter 1 Pan Amount: bei 100 % OK (cos 1,0), bei 0 % **keine** Iridium-Wirkung → Betrag asymmetrisch |
| **Panorama vs. Balance** | Balance verteilt auf **F1/F2**, kein Stereo-Pan | `OscNPan` ist echtes Stereo-Pan | Balance ≠ Pan | Balance → `OscNDestination`, **nicht** → Pan | L/R-Test: Blofeld-Bild unverändert (B≈0), Iridium wandert (I 5–12) → Mismatch |
| **Ringmodulation** | O1×O2 **und** O1×O3, je mit Balance | `RingModOsc1ToOsc2` **und** `RingModOsc1ToOsc3` vorhanden | O1×O3 ist **abbildbar**, wird aber nicht genutzt | `RingModOsc1ToOsc3` zusätzlich setzen | im Init nicht hörbar (Osc 2/3 aus) |
| **Wellenformen** | ~70 Shapes inkl. Sync-, Fuzz- und Wavetable-Varianten | Wavetable (viele Tabellen) + Waveform (Saw/Sine/Tri/Square/Noise) + Particle/Resonator/Kernels/Seeds | nur ein Teil ist 1:1 | Bridge-Tabelle für Wavetables; VA-Shapes direkt | Osc 1/2/3 Shape überwiegend OK (cos 0,93–0,99); einzelne Tabellen Mismatch |
| **Unisono** | bis 8 Stimmen, Detune; kein Pan/Delay | `UnisonoCount`, `UnisonoDetune`, **`UnisonoPan`, `UnisonoDelay`** | Count/Detune reichen nicht | Count aus Bitfeld **4–6** (Spec 4.10), Detune norm; Pan 0.5 / Delay 0 neutral halten | **behoben (A4, 2026-11-21):** Bits 4–6 statt 5–7 (Stimmenzahl war halbiert); Neumessung offen |
| **Glide** | 4 Modi (Portamento/fingered P/Glissando/fingered G) | `GlideOnOff`, `GlideRate`, **`GlideType`** | Modi sind abbildbar, werden aber nicht gesetzt | `GlideType` aus dem Blofeld-Modus; Rate zeitkalibriert (÷ 127) | im Init nicht messbar (kein Legato) |
| **Hüllkurven** | 4 Hüllkurven, Modi ADSR/ADS1DS2R/OneShot/Loop, Attack-Level, Decay2/Sustain2 | Hüllkurven mit Kurven (RC/Exp/Lin), Loop-Modi, Delay | zweite Decay/Sustain-Stufe fehlt | ADSR 1:1; ADS1DS2R auf ADSR annähern (Stufe 2 geht verloren) | FE Env Amount/Attack/Sustain OK (cos 0,90–0,99); Amp Attack/Sustain teilweise; FE Decay nur bei langen Zeiten |
| **LFOs** | 3 LFOs: Shape, Speed, Sync, Clocked, Phase, Delay, **Fade**, Keytrack | 6 LFOs: Shape, Speed, Sync, Phase, **Delay, Attack, Decay**, Slew, Warp | Fade/Keytrack haben kein direktes Pendant | Fade → `LfoNAttack`/`LfoNDecay`; Keytrack → Matrix `Keytrack → LFO Speed` | Fade-Mapping umgesetzt (A7a); LFO Speed bei langsamen Werten defekt (Free-Speed-Hz offen) |
| **Modifier** | 4 Rechen-Modifier (+ − × AND OR XOR MAX min) | Matrix-Control (Src + Ctrl), keine freien Rechenoperatoren | nur ×-Produkte und + mit Konstante annäherbar | `LFO × ModWheel` als Src+Ctrl; übrige Operatoren „nicht unterstützt“ | — |
| **Arpeggiator** | Arp mit 16-Step-Pattern, Glide/Accent, Timing | Arp/Sequencer (`ArpOn`, `ArpStepLength`, `ArpGate`, …) | eigener Block, vollständig unmapped | Arp-Grundfunktion könnte gemappt werden (Step-Länge, Oktaven, Sortierung) | nicht getestet |
| **FX** | 2 Slots, feste Typen, Dry/Wet je Typ | 2 FX-Slots + Mod-FX, mehr Typen | Typ-Mapping nötig; Parameter-Indizes weichen ab | DryWet-Key je Typ; Parameter 1:1 nach Index | FX Mix teilweise; Parameter 1/2 teilweise; **Parameter 5 bei 64/127 stark übersteuert** |
| **Stimmen** | 16 Parts, multitimbral | 4 Parts/Layer | für Sound-Konvertierung irrelevant | ein Part (Part 1, Kanal 6) | — |

---

## 2. Die wichtigsten Unterschiede im Detail

### 2.1 Rauschen: Mixer-Kanal vs. Oszillator-Wellenform

Der Blofeld hat einen eigenen Rauschgenerator, dessen Pegel, Filter-Balance und
**Farbe** (Colour, stufenlos) im Mixer liegen. Der Iridium kennt kein „Noise“-Modul;
Rauschen entsteht als **Wellenform eines Oszillators** (`OscNType=Waveform`,
`WaveformShape` = Pink/White Noise) oder als Dirt-Anteil in Particle/Resonator.

- **Workaround (im Konverter umgesetzt):** einen freien Oszillator als Noise-Quelle
  verwenden (bevorzugt Osc 3), Pegel → `OscNVol`, Balance → `OscNPan`,
  Ziel → `DF 0 Fil 100`.
- **Grenzen:** (a) es muss ein Oszillator frei sein, sonst ist der Noise-Anteil nicht
  abbildbar; (b) die stufenlose Farbe wird auf **zwei Stufen** (Pink ≤ 64, White > 64)
  reduziert. Für Zwischenwerte hilft nur ein Filter (Cutoff/Typ) oder Particle-Dirt.
- **Messung:** Noise Level folgt in der Tendenz (Cosinus 0,77–0,93, aber abweichende
  Kennlinie), **Noise Colour ist defekt** — der Iridium springt nur zwischen Pink und
  White, der Blofeld fährt stufenlos.

### 2.2 PWM: Pulsbreite vs. Wellenform-Warp

Beim Blofeld moduliert PWM die **Pulsbreite** — und nur bei pulsartigen Wellenformen.
Der Iridium hat eine statische PW (`OscNWaveformPW`) und als Modulationsziel
`WFn Warp` (Waveform-Osc) bzw. `WTn Position` (Wavetable-Osc).

- **Workaround (im Konverter umgesetzt):** Matrixzeile `PWM Source → WFn Warp`
  mit bipolarem Betrag, aber **nur bei pulsartigen Shapes**; bei Wavetable-Osc
  stattdessen `WTn Position`. Bei Saw/Triangle/Sine wird die Zeile bewusst nicht
  angelegt und als „ignored“ im `unmapped`-Report vermerkt (A1, 2026-11-21).
- **Grenze:** Warp verändert die gesamte Wellenform. Bei einer Sägezahn-Vorlage hat
  Blofeld-PWM **keine Wirkung**, der Iridium-Warp aber schon. Genau das zeigte die
  Messung: **PWM Amount war bei Osc 1/2/3 „nur Iridium reagiert“**.
- **Stand:** Fix + Unit-Tests vorhanden (`has_pulse_width`, A066/A007); die
  Neumessung mit dem gefilterten Mapping steht noch aus.

### 2.3 FM: Oszillator-Eingang vs. Kernel-Engine

Blofeld-FM ist ein echter Oszillator-Eingang (Source + Amount pro Osc). Der Iridium
hat keinen FM-Eingang am Oszillator; FM entsteht in den **6 Kernels** pro Oszillator
(`V4OscNKernel1..6`: Ratio, Level, Feedback, Mod-Source, Hüllkurven) oder als
Matrix-Ziel `OscN Pitch`.

- **Workaround:** für FM-Klänge die Kernel-Engine nachbauen (Kernel 1 = Träger,
  Kernel 2 = Modulator, Ratio/Level aus dem Blofeld-FM-Amount); für Vibrato-artige
  Effekte reicht Matrix→Pitch.
- **Nicht 1:1:** die Klangcharakteristik (Rückkopplung, Wellenform des Modulators)
  ist anders. Im Init-Sound nicht prüfbar, weil dort kein FM aktiv ist.

### 2.4 Filter: Balance-Topologie vs. FilterLink

Das ist der am häufigsten unterschätzte Unterschied. Der Blofeld verteilt **jede
Klangquelle** über einen eigenen Balance-Regler auf Filter 1 und Filter 2
(Direkttest: 0 = F1, 127 = F2; die Handbuch-Anzeige „F1 64 … F2 63“ ist irreführend).
Der Iridium verteilt über `OscNDestination` („DF 0 Fil 100“ … „DF 100 Fil 0“) und
verbindet die Filter über `FilterLink`.

- **Workaround:** Balance → `OscNDestination`-Anteile; Routing → `FilterLink`;
  Filter-2-Modell → DigiFormer (`Nave/PPG/Largo/SVF/Comb`) hinter Filter 1
  (`FilterFormerRouting = Filter > Former`), weil der Blofeld-F2 oft ein
  Charakterfilter ist.
- **Messbeleg (Direkttest, 12 Aufnahmen):** Bei Routing 0 (parallel) ist Filter 2
  nur hörbar, wenn die Balance auf F2 steht (balance 127: F2-Cutoff ändert den
  Klang stark, Centroid 1663 → 3511 Hz); bei Balance 0 (F1) bleibt F2 wirkungslos.
  Bei Routing 1 (seriell) liegt Filter 2 immer im Signalweg, unabhängig von der
  Balance (Centroid 1795 → 3550 Hz). Das bestätigt die Handbuch-Beschreibung:
  **Balance 0 = F1, 127 = F2; Routing 0 = parallel, 1 = seriell.**
- **Stand nach der Routing-Korrektur (2026-11-21):** Der Konverter bildet die
  Balance jetzt routingabhängig ab — **seriell** über `OscNDestination`
  (2 = F1 … 22 = Former/F2), **parallel** über die globalen
  `FilterLevel`/`Filter2Level` (per-Osc-Anteil ist in Parallel-Schaltung nicht
  darstellbar). Mit verifiziertem Dump-Load (Rauschboden 0,2/0,6) folgt der
  **F2-Cutoff** dem Blofeld (Cosinus 0,88–0,96, Stärke 0,6), **F2-Drive** bei
  hohen Werten (0,97) und die **F2-Hüllkurve**: Env Amount 0,92–1,0,
  Env Velocity 0,75–0,81, Keytrack 0,89 (teilweise).
- **Nachtrag A2 (2026-11-21, Code):** In Parallel-Schaltung setzt der Konverter
  jetzt `FilterLink = Independent` (das v8-Template stand auf `Boost`, das
  Cutoff 2/Resonanz 2 ignoriert) und einen eigenen `Filter2Type` (v14 hat neben
  `Filter12Type` ein separates `Filter2Type`). Filter-Drive läuft als Insert mit
  `DriveDryWet=1.0`; die Resonanz-Kennlinie mappt raw 113 (Blofeld-
  Selbstoszillation) auf 1.0. Die **F2-Neumessung** steht noch aus
  (`TODO_MEASURE.md`).
- **Grenze:** Die Resonanzform bleibt trotz Kennlinien-Fix eine Näherung; bei
  weiterhin schlechtem Cosinus sind die Filter-Modelle
  (`Filter1Model`/`Filter2Model`, B5) der nächste Hebel.

### 2.5 Filter-Drive und Filter-FM

Der Blofeld hat pro Filter Drive **und** eine Drive-Kurve; der Iridium hat keinen
Filter-Drive. Drive ist ein FX (`DriveAmount`, `DriveGain`, `DriveType`).

- **Workaround:** `FX1/FX2 = Drive` und die Kurve über den Drive-Typ annähern.
- **Kosten:** ein FX-Slot; bei bereits belegten FX-Slots nicht verfügbar.
- Filter-FM hat kein Iridium-Pendant; Filter-Pan geht nur über die Matrix.

### 2.6 Wellenform-Generator

Der Blofeld bietet ~70 Shapes (VA, Sync-, Fuzz-, Wavetable-Varianten). Der Iridium
trennt **Wavetable** (Tabellen + Position/Brilliance/Travel) und **Waveform**
(Saw/Sine/Tri/Square/Noise + Warp/PW). Sync- und Fuzz-Shapes haben keine direkte
Entsprechung; sie werden über die Bridge-Tabelle angenähert.

- **Messung:** Osc 1/2/3 Shape überwiegend OK (cos 0,93–0,99); einzelne
  Wavetable-Tabellen (z. B. Osc 3 Shape 18/36) weichen ab.

### 2.7 Hüllkurven

Blofeld: 4 Hüllkurven mit Modus (ADSR, ADS1DS2R, One Shot, Loop), Attack-Level,
Decay 2 / Sustain 2. Iridium: Hüllkurven mit **Kurvenform** (RC/Exp/Lin), Delay,
Loop-Modus.

- **Workaround:** ADSR 1:1; ADS1DS2R auf ADSR reduzieren (die zweite Stufe geht
  verloren); Attack-Level über die erste Hüllkurvenstufe annähern.
- **Messung:** Filter-Env Amount, Attack und Sustain OK (cos 0,90–0,99); Amp-Attack
  und -Sustain teilweise (Iridium 1,7–2,0× stärker); **Filter-Env Decay** nur bei
  langen Zeiten messbar (bei Sustain 100 wirkt Decay nicht); **Filter-Env Release**
  blieb nicht belastbar messbar (Amp-Release kürzer als Filter-Release).

### 2.8 LFOs

Der Iridium hat **sechs** LFOs mit Delay, Attack, Decay und Slew — der Blofeld drei
mit Fade und Keytrack.

- **Workaround:** Blofeld-Fade → `LfoNAttack`/`LfoNDecay`; Keytrack →
  Matrix `Keytrack → LFO Speed`; Clocked/Sync → `LfoNSync` + `SyncRatio`.
- **Stand:** Fade-Mapping ist umgesetzt (bipolar: positiv → Attack, negativ →
  Decay, A7a, Test `test_lfo_fade_maps_to_attack_decay`). **LFO Speed** bleibt
  offen: langsame Werte ohne Iridium-Wirkung, schnelle nur teilweise
  (Free-Speed-Hz-Skala noch nicht kalibriert).

### 2.9 Modulationsmatrix und Modifier

Blofeld: 16 Slots + 4 Modifier mit Rechenoperatoren. Iridium: 40 Matrixzeilen mit
Source + Control.

- **Workaround:** Produkte (LFO × ModWheel, LFO × Pressure) als `Src=LFO` +
  `MatrixControl=Wheel/Aftertouch`; Summen mit Konstante als Src + Offset.
- **Nicht abbildbar:** AND/OR/XOR/MAX/min, Modifier-Ketten, Control W–Z exakt.

### 2.10 Panorama und Balance (Test E, 2026-11-21)

Der L/R-getrennte Test belegt den Unterschied schwarz auf weiß:

- **Balance ist kein Pan.** Beim Blofeld bleibt das Stereo-Bild bei jeder
  Balance-Stellung praktisch unverändert (Wirkung ≈ 0), weil Balance nur den
  F1/F2-Anteil verteilt. Der Iridium wanderte früher deutlich (Wirkung 5–12),
  weil der Konverter Balance auf `OscNPan` legte. **Behoben (A11):** seriell →
  `OscNDestination`, parallel → `FilterLevel`/`Filter2Level`; Nachmessung zeigt
  kein Wandern mehr (Noise-Balance beidseitig n/a).
- **Filter-Pan-Amout war asymmetrisch** (100 % Cosinus 1,0, 0 % keine
  Iridium-Wirkung). Ursache: die Matrixzeile wurde bei Amount 0 nicht angelegt
  (Blofeld-0 ist „voller Links-Ausschlag“, nicht „aus“). Behoben: Zeile ab 0,
  Betrag bipolar `0,5 + (raw−64)/127`. Nachgemessen: 0 % Cosinus 0,998,
  100 % 0,997.
- **Amp-Velocity-Kennlinie:** Bei Amount 0 ist der Iridium deutlich
  anschlagempfindlicher als der Blofeld (I 6,1 vs. B 2,4, Cosinus 0,97) — die
  Skalierung der Velocity-Kurve muss nachgezogen werden.

### 2.11 Arpeggiator

Der Blofeld-Arp (Pattern, 16 Steps, Glide/Accent, Timing) ist ein eigener Block.
Der Iridium hat Arp/Sequencer-Parameter (`ArpOn`, `ArpStepLength`, `ArpGate`,
`ArpSortOrder`, `ArpVeloMode`), aber der Konverter nutzt sie nicht.

- **Workaround:** Grundfunktion (On/Off, Step-Länge, Oktaven, Sortierung, Gate)
  könnte gemappt werden; Step-Pattern/Accent/Glide bleiben unmapped.

---

## 3. Abbildbar, aber im Konverter noch nicht genutzt (Mapping-Lücken)

Diese Punkte sind **keine** Architekturgrenzen — die Iridium-Parameter existieren,
werden aber nicht gesetzt:

| Blofeld | vorhandener Iridium-Parameter | Nutzen |
|---|---|---|
| Mixer RingMod Balance / O1×O3 | `RingModOsc1ToOsc3` | Ringmod auf Osc 3 |
| Glide Mode | `GlideType` | Portamento/Glissando/fingered |
| Allocation/Unisono | `UnisonoPan`, `UnisonoDelay` | breitere Unisono-Stimmen |
| LFO Fade | `LfoNAttack`, `LfoNDecay` | Ein-/Ausblenden |
| LFO Keytrack | Matrix `Keytrack → LFO Speed` | geschwindigkeitsabhängige LFOs |
| Osc Bend Range / Keytrack | `OscNPitchBendRange`, `OscNKeytrack` | Pitch-Bend-Bereich, Tastatur-Tracking |
| Arpeggiator (Basis) | `ArpOn`, `ArpStepLength`, `ArpGate`, … | Grund-Arp |
| Noise Colour (stufenlos) | Filter-Cutoff/-Typ oder Particle-Dirt | Farbverlauf annähern |

---

## 4. Empfohlene nächste Schritte

1. ✅ **PWM-Zeile nur für pulsartige Blofeld-Wellenformen** — umgesetzt (A1,
   2026-11-21), Neumessung offen.
2. ✅ **Filter-2-/Balance-Mapping** — Balance → `OscNDestination`/`FilterLevel`,
   parallel `FilterLink=Independent` + `Filter2Type`, Filter-Drive als Insert,
   Resonanz-Kennlinie (A2, 2026-11-21); Neumessung `f2` offen.
3. ✅ **Unisono Detune** — Bitfeld-Korrektur (Bits 4–6) + neutrale Pan/Delay-Werte
   (A4, 2026-11-21), Neumessung offen.
4. **LFO Fade** auf `LfoNAttack`/`LfoNDecay` legen und **Free-Speed** in Hz
   kalibrieren (langsame LFOs weichen).
5. **FX-Parameter-Indizes** prüfen: Parameter 5 ist bei 64/127 stark übersteuert
   (Iridium 5–11×), Parameter 1/2 nur teilweise.
6. **Noise-Farbe** dokumentieren: nur Pink/White; für Zwischenwerte Filter-Cutoff
   mitführen.
7. **Pan/Balance** in einer L/R-getrennten Messung prüfen; die aktuelle
   Monosumme kann sie prinzipbedingt nicht bewerten.

---

## 5. Testaufbau (reproduzierbar)

Alle Zahlen stammen aus `docs/PROFILING-INIT-2026-11-21.md` und
`docs/profiling_init_2026-11-21.csv`. Die Varianten sind in
`scripts/profile_testb_sweep.py` (`MODES`) definiert:

| Variante | Ziel | Aktivierung |
|---|---|---|
| `clean` | Osc 2/3 | beide Saw, Pegel 100, Balance Mitte |
| `f2` | Filter 2 | F2 LP24, Balance auf F2 (127), Routing parallel (0) – Lauf war inkonsistent, siehe §2.4 |
| `fe`, `fe_decay`, `fe_rel` | Filter-Hüllkurve | Cutoff 64, Env-Amount 100, Sustain 80/100 |
| `osc2`, `osc3` | Osc 2/3 solo | Osc 1 aus, Balance auf F1 |
| `noise` | Noise-Mixer | alle Oscs aus, Noise-Pegel 100 |
| `lfo1` | LFO 1 | Mod 1: LFO1 → O1 Pitch, Betrag 90 |
| `unison` | Unisono | 2 Stimmen, Detune-Sweep |
| `fx1` | FX 1 | Chorus, 100 % wet |
| `sync` | Sync | Osc 2+3 an, Osc 2 Sync |

Grenzen der Aussagekraft: Test-D-Varianten mit mehreren klingenden Oszillatoren haben
eine höhere Streuung (Schwebung/Phase); Pan/Balance sind mit der Monosumme nicht
messbar; Release-Parameter brauchen den separaten Durchgang mit Note-off während der
Aufnahme.
