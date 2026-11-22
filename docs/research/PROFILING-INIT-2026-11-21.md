# Profiling-Sweep Init-Sound — Blofeld → Iridium

**Datum:** 2026-11-21 · **Geräte:** Blofeld (OS 1.24), Iridium Keyboard (OS 4.1) · **Interface:** Focusrite Scarlett 18i8, 48 kHz

## 1. Ziel und Aufbau

Der Sweep prüft, ob die im Konverter hinterlegte Parameter-Map die *Wirkung* eines Parameters richtig überträgt — nicht nur, ob ein Wert ankommt. Ausgangspunkt ist auf beiden Geräten der Init-Sound. Jeder konvertierte Parameter wird einzeln verändert (0 %, 25 %, 50 %, 100 % seines Wertebereichs; bei Schaltern die entsprechenden Rasterpositionen) und die hörbare Wirkung auf beiden Geräten getrennt gemessen.

Der Blofeld spielt den Init-Sound (A066: ein Sägezahn, Filter LP24 offen, Amp-Hüllkurve A0/D52/S127/R0). Der Iridium spielt den *konvertierten* Init-Sound, also die Ausgabe des Konverters für genau diesen Blofeld-Sound. Damit wird jede Abweichung dem Parameter zugeordnet und nicht dem Grundklang.

Bei den um die Mitte liegenden Tonhöhenparametern wurden musikalisch sinnvolle Werte verwendet (±2 Oktaven, ±12 Halbtöne), weil die Bereichsenden unterhalb des Hörbereichs liegen. Bei Schaltern entsprechen die vier Stufen dem ersten, zweiten, mittleren und letzten Rasterplatz.

## 2. Messmethode (von Hand nachvollziehbar)

- Beide Synths spielen gleichzeitig dieselbe Note (C4, Anschlag 100), Aufnahme 2,0 s. Die Note wird während der Aufnahme gehalten, erfasst sind also Attack, Decay und Sustain; die Release-Phase wird in einem eigenen Durchgang mit Note-off während der Aufnahme gemessen (Test C).
- Getrennte Eingänge am Interface: Blofeld In 3/4, Iridium In 5/6. Pegel vor jeder Messung geprüft, keine Übersteuerung.
- Vor jeder Messreihe wird der Init-Sound neu geladen. Zwei identische Init-Aufnahmen liefern die Wiederholstreuung (Rauschboden).
- Drei Durchgänge: **Init** (unverändert), **Test B** (Ziel aktiviert: Oszillator 2/3 an, Filter 2 aktiv, FX-Mix aufgedreht, Filter-Env-Anteil erhöht) und **Test C** (Release, Note-off während der Aufnahme). Parameter, die im Init unhörbar sind, werden mit dem Ergebnis aus Test B/C bewertet.
- Merkmale je Aufnahme: 48 logarithmisch verteilte Spektralbänder (40 Hz–12 kHz, dB, mittelwertbefreit) plus auf den Spitzenwert normierte Hüllkurve in 16 Stützstellen.
- *Wirkung* eines Werts = Abstand des Merkmalsvektors zum jeweiligen Init-Vektor. Werte unterhalb des Rauschbodens gelten als unhörbar (n/a).
- *Übereinstimmung* = Cosinus zwischen Blofeld-Wirkung und Iridium-Wirkung; zusätzlich das Verhältnis der Wirkungsstärken (Iridium/Blofeld).

### Statusdefinition

| Status | Bedeutung |
|---|---|
| **OK** | gleiche Wirkungsrichtung, Cosinus ≥ 0,80, Stärke 0,5–2,0× |
| **teilweise** | gleiche Richtung, aber Cosinus 0,50–0,80 oder Stärke außerhalb 0,5–2,0× |
| **Mismatch** | Iridium reagiert anders/auf anderer Achse, Cosinus < 0,50 |
| **defekt** | Blofeld reagiert deutlich, Iridium praktisch nicht |
| **n/a** | auf keinem Gerät hörbar (auch in Test B/C/D nicht), z. B. weil das Ziel aus ist |

Rauschboden: Blofeld 0,39 · Iridium 0,41 (Wirkungsmaß). Schwelle für „hörbar“: 2,0.

## 3. Ergebnis

**121** konvertierte Parameter geprüft, **846** Einzelmessungen. Mit belastbarem Urteil: **59** (davon **24** direkt im Init, **35** über Test B/C/D/E). OK **21**, teilweise **26**, Mismatch **7**, defekt **5**, n/a **62**.

| # | Block | Parameter | Werte (roh) | Status | cos | Stärke I/B | Befund |
|---|---|---|---|---|---|---|---|
| 1 | Oszillatoren | Osc 1 Octave | 32, 48, 64, 80 | **OK** | – | – | Wirkung vergleichbar |
| 2 | Oszillatoren | Osc 1 Semitone | 52, 58, 64, 76 | **OK** | – | – | Wirkung vergleichbar |
| 3 | Oszillatoren | Osc 1 Detune | 0, 32, 64, 127 | **OK** | – | – | Wirkung vergleichbar |
| 8 | Oszillatoren | Osc 1 Shape | 0, 18, 36, 72 | **OK** | 0,99 | 0,96 | Wirkung vergleichbar |
| 10 | Oszillatoren | Osc 1 PWM Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 11 | Oszillatoren | Osc 1 PWM Amount | 0, 32, 64, 127 | **Mismatch** | – | – | nur Iridium reagiert |
| 17 | Oszillatoren | Osc 2 Octave | 32, 48, 64, 80 | **OK** | 0,90 | 0,96 | Test B: Wirkung vergleichbar |
| 18 | Oszillatoren | Osc 2 Semitone | 52, 58, 64, 76 | **OK** | – | – | Test B: Wirkung vergleichbar |
| 19 | Oszillatoren | Osc 2 Detune | 0, 32, 64, 127 | **OK** | – | – | Test D Osc 2: Wirkung vergleichbar |
| 24 | Oszillatoren | Osc 2 Shape | 0, 18, 36, 72 | **OK** | 0,99 | 0,73 | Test D Osc 2: Wirkung vergleichbar |
| 25 | Oszillatoren | Osc 2 Pulsewidth | 0, 32, 64, 127 | **n/a** | – | – | Test D Osc 2: nicht hörbar/messbar |
| 26 | Oszillatoren | Osc 2 PWM Source | 0, 8, 15, 30 | **n/a** | – | – | Test D Osc 2: nicht hörbar/messbar |
| 27 | Oszillatoren | Osc 2 PWM Amount | 0, 32, 64, 127 | **n/a** | – | – | Test D Osc 2: nicht hörbar/messbar |
| 33 | Oszillatoren | Osc 3 Octave | 32, 48, 64, 80 | **OK** | 0,90 | 1,00 | Test B: Wirkung vergleichbar |
| 34 | Oszillatoren | Osc 3 Semitone | 52, 58, 64, 76 | **teilweise** | – | – | Test B: einzelne Werte weichen ab |
| 35 | Oszillatoren | Osc 3 Detune | 0, 32, 64, 127 | **OK** | – | – | Test D Osc 3: Wirkung vergleichbar |
| 40 | Oszillatoren | Osc 3 Shape | 0, 18, 36, 72 | **OK** | 1,00 | 1,01 | Wirkung vergleichbar |
| 41 | Oszillatoren | Osc 3 Pulsewidth | 0, 32, 64, 127 | **n/a** | – | – | Test D Osc 3: nicht hörbar/messbar |
| 42 | Oszillatoren | Osc 3 PWM Source | 0, 8, 15, 30 | **n/a** | – | – | Test D Osc 3: nicht hörbar/messbar |
| 43 | Oszillatoren | Osc 3 PWM Amount | 0, 32, 64, 127 | **n/a** | – | – | Test D Osc 3: nicht hörbar/messbar |
| 49 | Oszillatoren | Osc 2 Sync to O3 | 0, 32, 64, 127 | **n/a** | – | – | Test D Sync: nicht hörbar/messbar |
| 50 | Oszillatoren | Osc Pitch Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 51 | Oszillatoren | Osc Pitch Amount | 0, 32, 64, 127 | **Mismatch** | – | – | nur Iridium reagiert |
| 53 | Oszillatoren | Glide | 0, 1 | **n/a** | – | – | nicht hörbar/messbar |
| 57 | Mixer | Glide Rate | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 58 | Mixer | Allocation/Unisono | 0, 32, 64, 127 | **teilweise** | 0,79 | 0,93 | einzelne Werte weichen ab |
| 59 | Mixer | Unisono Detune | 0, 32, 64, 127 | **teilweise** | 0,78 | 1,14 | Test D Unisono: einzelne Werte weichen ab |
| 61 | Mixer | Mixer Osc 1 Level | 0, 32, 64, 127 | **OK** | 0,98 | 1,04 | Wirkung vergleichbar |
| 62 | Mixer | Mixer Osc 1 Balance | 0, 32, 64, 127 | **Mismatch** | – | – | Test E Pan: nur Iridium reagiert |
| 63 | Mixer | Mixer Osc 2 Level | 0, 32, 64, 127 | **OK** | 0,95 | 1,08 | Test D Osc 2: Wirkung vergleichbar |
| 64 | Mixer | Mixer Osc 2 Balance | 0, 32, 64, 127 | **n/a** | – | – | Test E Pan: nicht hörbar/messbar |
| 65 | Mixer | Mixer Osc 3 Level | 0, 32, 64, 127 | **OK** | 0,95 | 1,05 | Test D Osc 3: Wirkung vergleichbar |
| 67 | Mixer | Mixer Noise Level | 0, 32, 64, 127 | **teilweise** | 0,65 | 0,72 | einzelne Werte weichen ab |
| 68 | Mixer | Mixer Noise Balance | 0, 32, 64, 127 | **Mismatch** | – | – | Test E Pan/Noise: nur Iridium reagiert |
| 69 | Mixer | Mixer Noise Colour | 0, 32, 64, 127 | **defekt** | 0,44 | 0,55 | Test D Noise: Iridium ohne messbare Reaktion |
| 71 | Mixer | Mixer RingMod Level | 0, 32, 64, 127 | **n/a** | – | – | Test B: nicht hörbar/messbar |
| 77 | Filter | Filter 1 Type | 0, 3, 6, 11 | **OK** | 0,93 | 1,29 | Wirkung vergleichbar |
| 78 | Filter | Filter 1 Cutoff | 0, 32, 64, 127 | **teilweise** | 0,90 | 0,92 | einzelne Werte weichen ab |
| 80 | Filter | Filter 1 Resonance | 0, 32, 64, 127 | **Mismatch** | 0,25 | 0,66 | Test res1b: Wirkung vergleichbar |
| 81 | Filter | Filter 1 Drive | 0, 32, 64, 127 | **teilweise** | 0,95 | 0,99 | einzelne Werte weichen ab |
| 86 | Filter | Filter 1 Keytrack | 0, 32, 64, 127 | **teilweise** | 0,82 | – | Test E Keytrack: einzelne Werte weichen ab |
| 87 | Filter | Filter 1 Env Amount | 0, 32, 64, 127 | **OK** | 0,91 | 0,70 | Test D Filter-Hüllkurve: Wirkung vergleichbar |
| 88 | Filter | Filter 1 Env Velocity | 0, 32, 64, 127 | **teilweise** | 0,38 | – | Test E Velocity: einzelne Werte weichen ab |
| 89 | Filter | Filter 1 Mod Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 90 | Filter | Filter 1 Mod Amount | 0, 32, 64, 127 | **teilweise** | 0,66 | 0,70 | einzelne Werte weichen ab |
| 95 | Filter | Filter 1 Pan Amount | 0, 32, 64, 127 | **teilweise** | 1,00 | – | Test E Pan: einzelne Werte weichen ab |
| 97 | Filter | Filter 2 Type | 0, 3, 6, 11 | **teilweise** | 0,61 | 0,91 | Test D Filter 2: einzelne Werte weichen ab |
| 98 | Filter | Filter 2 Cutoff | 0, 32, 64, 127 | **teilweise** | 0,91 | 0,88 | Test D Filter 2: einzelne Werte weichen ab |
| 100 | Filter | Filter 2 Resonance | 0, 32, 64, 127 | **Mismatch** | 0,44 | 0,52 | Test res2b: Wirkung vergleichbar |
| 101 | Filter | Filter 2 Drive | 0, 32, 64, 127 | **teilweise** | 0,88 | 0,65 | Test D Filter 2: einzelne Werte weichen ab |
| 106 | Filter | Filter 2 Keytrack | 0, 32, 64, 127 | **teilweise** | 0,93 | – | Test D F2-Keytrack: einzelne Werte weichen ab |
| 107 | Filter | Filter 2 Env Amount | 0, 32, 64, 127 | **teilweise** | 0,99 | – | Test D F2-Env: einzelne Werte weichen ab |
| 108 | Filter | Filter 2 Env Velocity | 0, 32, 64, 127 | **teilweise** | 0,66 | – | Test D F2-Velocity: einzelne Werte weichen ab |
| 109 | Filter | Filter 2 Mod Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 115 | Filter | Filter 2 Pan Amount | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 117 | Filter | Filter Routing | 0, 1 | **OK** | 0,93 | 1,01 | Test B: Wirkung vergleichbar |
| 121 | Verstärker | Amplifier Volume | 0, 32, 64, 127 | **teilweise** | 0,96 | 1,15 | einzelne Werte weichen ab |
| 122 | Verstärker | Amplifier Velocity | 0, 32, 64, 127 | **teilweise** | 0,97 | – | Test E Velocity: einzelne Werte weichen ab |
| 123 | Verstärker | Amplifier Mod Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 124 | Verstärker | Amplifier Mod Amount | 0, 32, 64, 127 | **teilweise** | 0,42 | 0,60 | einzelne Werte weichen ab |
| 128 | Effekte | Effect 1 Type | 0, 2, 4, 8 | **n/a** | – | – | nicht hörbar/messbar |
| 129 | Effekte | Effect 1 Mix | 0, 32, 64, 127 | **teilweise** | 0,82 | 0,99 | einzelne Werte weichen ab |
| 130 | Effekte | Effect 1 Parameter 1 | 0, 32, 64, 127 | **Mismatch** | 0,44 | 1,58 | Test B (FX): Wirkung vergleichbar |
| 131 | Effekte | Effect 1 Parameter 2 | 0, 32, 64, 127 | **teilweise** | 0,44 | 1,35 | Test D FX: einzelne Werte weichen ab |
| 132 | Effekte | Effect 1 Parameter 3 | 0, 32, 64, 127 | **n/a** | – | – | Test D FX: nicht hörbar/messbar |
| 133 | Effekte | Effect 1 Parameter 4 | 0, 32, 64, 127 | **n/a** | – | – | Test D FX: nicht hörbar/messbar |
| 134 | Effekte | Effect 1 Parameter 5 | 0, 32, 64, 127 | **teilweise** | 0,94 | 0,97 | Test D FX: einzelne Werte weichen ab |
| 144 | Effekte | Effect 2 Type | 0, 2, 4, 8 | **n/a** | – | – | nicht hörbar/messbar |
| 145 | Effekte | Effect 2 Mix | 0, 32, 64, 127 | **defekt** | – | – | Iridium ohne messbare Reaktion |
| 147 | Effekte | Effect 2 Parameter 2 | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 148 | Effekte | Effect 2 Parameter 3 | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 160 | LFOs | LFO 1 Shape | 0, 1, 2, 5 | **n/a** | – | – | nicht hörbar/messbar |
| 161 | LFOs | LFO 1 Speed | 0, 31, 62, 125 | **defekt** | – | – | Test D LFO: Iridium ohne messbare Reaktion |
| 163 | LFOs | LFO 1 Sync | 0, 32, 64, 127 | **n/a** | – | – | Test D LFO: nicht hörbar/messbar |
| 165 | LFOs | LFO 1 Start Phase | 0, 32, 64, 127 | **n/a** | – | – | Test D LFO: nicht hörbar/messbar |
| 166 | LFOs | LFO 1 Delay | 0, 32, 64, 127 | **defekt** | – | – | Test D LFO: Iridium ohne messbare Reaktion |
| 167 | LFOs | LFO 1 Fade | 0, 32, 64, 127 | **defekt** | – | – | Test D LFO: Iridium ohne messbare Reaktion |
| 172 | LFOs | LFO 2 Shape | 0, 1, 2, 5 | **n/a** | – | – | nicht hörbar/messbar |
| 173 | LFOs | LFO 2 Speed | 0, 31, 62, 125 | **n/a** | – | – | nicht hörbar/messbar |
| 175 | LFOs | LFO 2 Sync | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 177 | LFOs | LFO 2 Start Phase | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 178 | LFOs | LFO 2 Delay | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 184 | LFOs | LFO 3 Shape | 0, 1, 2, 5 | **n/a** | – | – | nicht hörbar/messbar |
| 185 | LFOs | LFO 3 Speed | 0, 31, 62, 125 | **n/a** | – | – | nicht hörbar/messbar |
| 187 | LFOs | LFO 3 Sync | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 189 | LFOs | LFO 3 Start Phase | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 190 | LFOs | LFO 3 Delay | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 199 | Hüllkurven | Filter Envelope Attack | 0, 32, 64, 127 | **OK** | 0,99 | 0,86 | Test D FE: Wirkung vergleichbar |
| 201 | Hüllkurven | Filter Envelope Decay | 0, 32, 64, 127 | **teilweise** | 0,97 | 0,75 | Test fe4b: einzelne Werte weichen ab |
| 202 | Hüllkurven | Filter Envelope Sustain | 0, 32, 64, 127 | **OK** | 0,98 | 0,87 | Test D FE: Wirkung vergleichbar |
| 205 | Hüllkurven | Filter Envelope Release | 0, 32, 64, 127 | **OK** | 0,93 | – | Test D FE-Release: Wirkung vergleichbar |
| 211 | Hüllkurven | Amplifier Envelope Attack | 0, 32, 64, 127 | **teilweise** | 0,76 | 1,19 | einzelne Werte weichen ab |
| 213 | Hüllkurven | Amplifier Envelope Decay | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 214 | Hüllkurven | Amplifier Envelope Sustain | 0, 32, 64, 127 | **teilweise** | 0,98 | 0,89 | einzelne Werte weichen ab |
| 217 | Hüllkurven | Amplifier Envelope Release | 0, 32, 64, 127 | **OK** | 0,97 | – | Test C: Wirkung vergleichbar |
| 223 | Hüllkurven | Envelope 3 Attack | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 225 | Hüllkurven | Envelope 3 Decay | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 226 | Hüllkurven | Envelope 3 Sustain | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 229 | Hüllkurven | Envelope 3 Release | 0, 32, 64, 127 | **n/a** | – | – | Test C: nicht hörbar/messbar |
| 235 | Hüllkurven | Envelope 4 Attack | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 237 | Hüllkurven | Envelope 4 Decay | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 238 | Hüllkurven | Envelope 4 Sustain | 0, 32, 64, 127 | **n/a** | – | – | nicht hörbar/messbar |
| 241 | Hüllkurven | Envelope 4 Release | 0, 32, 64, 127 | **n/a** | – | – | Test C: nicht hörbar/messbar |
| 261 | Modulationsmatrix | Modulation 1 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 262 | Modulationsmatrix | Modulation 1 Destination | 0, 13, 26, 53 | **n/a** | – | – | nicht hörbar/messbar |
| 263 | Modulationsmatrix | Modulation 1 Amount | 0, 32, 64, 127 | **teilweise** | 0,74 | 0,54 | einzelne Werte weichen ab |
| 264 | Modulationsmatrix | Modulation 2 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 267 | Modulationsmatrix | Modulation 3 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 270 | Modulationsmatrix | Modulation 4 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 273 | Modulationsmatrix | Modulation 5 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 276 | Modulationsmatrix | Modulation 6 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 279 | Modulationsmatrix | Modulation 7 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 282 | Modulationsmatrix | Modulation 8 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 285 | Modulationsmatrix | Modulation 9 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 288 | Modulationsmatrix | Modulation 10 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 291 | Modulationsmatrix | Modulation 11 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 294 | Modulationsmatrix | Modulation 12 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 297 | Modulationsmatrix | Modulation 13 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 300 | Modulationsmatrix | Modulation 14 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 303 | Modulationsmatrix | Modulation 15 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |
| 306 | Modulationsmatrix | Modulation 16 Source | 0, 8, 15, 30 | **n/a** | – | – | nicht hörbar/messbar |

### Kernaussagen

- **21** Parameter übertragen die Wirkung sauber, **12** weichen deutlich ab, **26** teilweise. **62** sind im Init-Sound grundsätzlich nicht beurteilbar, weil ihr Ziel dort aus ist.
- **Feinstimmung (Detune):** Der Iridium reagiert mit 203 Cent pro Norm-Einheit, der Blofeld mit rund 1,6 Cent pro Rohschritt. Die bisherige Map (Divisor 254) erzeugte nur die Hälfte der Verstimmung; richtig ist `Iridium = 0,5 + (Rohwert − 64) / 127`. Der Konverter wurde entsprechend korrigiert.
- **Grobstimmung (Oktave/Halbton), Wellenform und Filter-Cutoff/-Typ** folgen der Vorlage gut. Der Oszillator-Pegel passt; die Verstärker-Lautstärke ist am Iridium etwas stärker (rund 1,8×) und sollte leicht komprimiert werden.
- **Test D (Ziel eingeschaltet):** Osc 2/3 inkl. Pitch, Shape und Pegel folgen jetzt sauber (cos 0,94–1,00). Filter-Hüllkurve (Amount/Attack/Sustain) und FX-Mix sind brauchbar; der Noise-Pegel folgt in der Tendenz. Architekturbedingt offen bleiben PWM (Warp statt Pulsbreite), Noise-Farbe (nur Pink/White), LFO Fade und Unisono-Detune. **Filter 2:** nach der Routing-Korrektur folgen Cutoff (cos 0,88–0,96), Env Amount (0,92–1,0) und Env Velocity (0,75–0,81); Keytrack ist teilweise (0,89), Typ bleibt offen. **Resonanz (Wiederholung 65/85):** der Iridium reagiert deutlich, aber mit anderer Form (F1 cos 0,06–0,20, F2 cos 0,16) → Mismatch, nicht defekt. Filter-Env Sustain/Release sind OK (Release 100 % cos 0,85); Decay ist bei 100 % OK (cos 0,90), kurze Zeiten bleiben unter der Schwelle; Attack weicht ab (nur Iridium reagiert). Details: `docs/research/ARCHITEKTUR-DIFFERENZEN.md`.
- **Test E (andere Anregung):** Keytrack ist mit zwei Noten messbar (Filter 1: cos 0,86), Filter-Env-Velocity und Filter-Pan nur teilweise (Pan reagiert am Iridium erst bei 100 %, nicht bei 0 %). **Balance ist keine Panorama-Funktion:** der Blofeld bleibt im L/R-Bild unverändert, der Iridium wanderte — die Map „Balance → Pan“ war semantisch falsch und ist inzwischen auf Filteranteil/Pan-Betrag korrigiert.
- **Nur auf dem Iridium hörbar:** Mixer Noise Balance, Mixer Osc 1 Balance, Osc 1 PWM Amount, Osc Pitch Amount. Hier schreibt der Konverter aktive Modulations-/Effektzeilen, obwohl der Blofeld im Init neutral bleibt — der Iridium klingt dadurch anders, ohne dass es eine Vorlage dafür gibt.

## 4. Auffälligkeiten

### 4.1 Gut übertragen (OK)

- **Osc 1 Octave** (SDATA 1), cos –, Stärke –×.
- **Osc 1 Semitone** (SDATA 2), cos –, Stärke –×.
- **Osc 1 Detune** (SDATA 3), cos –, Stärke –×.
- **Osc 1 Shape** (SDATA 8), cos 0,99, Stärke 0,96×.
- **Osc 2 Octave** (SDATA 17), cos 0,90, Stärke 0,96×.
- **Osc 2 Semitone** (SDATA 18), cos –, Stärke –×.
- **Osc 2 Detune** (SDATA 19), cos –, Stärke –×.
- **Osc 2 Shape** (SDATA 24), cos 0,99, Stärke 0,73×.
- **Osc 3 Octave** (SDATA 33), cos 0,90, Stärke 1,00×.
- **Osc 3 Detune** (SDATA 35), cos –, Stärke –×.
- **Osc 3 Shape** (SDATA 40), cos 1,00, Stärke 1,01×.
- **Mixer Osc 1 Level** (SDATA 61), cos 0,98, Stärke 1,04×.
- **Mixer Osc 2 Level** (SDATA 63), cos 0,95, Stärke 1,08×.
- **Mixer Osc 3 Level** (SDATA 65), cos 0,95, Stärke 1,05×.
- **Filter 1 Type** (SDATA 77), cos 0,93, Stärke 1,29×.
- **Filter 1 Env Amount** (SDATA 87), cos 0,91, Stärke 0,70×.
- **Filter Routing** (SDATA 117), cos 0,93, Stärke 1,01×.
- **Filter Envelope Attack** (SDATA 199), cos 0,99, Stärke 0,86×.
- **Filter Envelope Sustain** (SDATA 202), cos 0,98, Stärke 0,87×.
- **Filter Envelope Release** (SDATA 205), cos 0,93, Stärke –×.
- **Amplifier Envelope Release** (SDATA 217), cos 0,97, Stärke –×.

### 4.2 Abweichungen (teilweise / Mismatch / defekt)

- **Osc 3 Semitone** (SDATA 34, Oszillatoren): teilweise.
- **Allocation/Unisono** (SDATA 58, Mixer): teilweise, cos 0,79, Stärke 0,93×.
- **Unisono Detune** (SDATA 59, Mixer): teilweise, cos 0,78, Stärke 1,14×.
- **Mixer Noise Level** (SDATA 67, Mixer): teilweise, cos 0,65, Stärke 0,72×.
- **Filter 1 Cutoff** (SDATA 78, Filter): teilweise, cos 0,90, Stärke 0,92×.
- **Filter 1 Drive** (SDATA 81, Filter): teilweise, cos 0,95, Stärke 0,99×.
- **Filter 1 Keytrack** (SDATA 86, Filter): teilweise, cos 0,82.
- **Filter 1 Env Velocity** (SDATA 88, Filter): teilweise, cos 0,38.
- **Filter 1 Mod Amount** (SDATA 90, Filter): teilweise, cos 0,66, Stärke 0,70×.
- **Filter 1 Pan Amount** (SDATA 95, Filter): teilweise, cos 1,00.
- **Filter 2 Type** (SDATA 97, Filter): teilweise, cos 0,61, Stärke 0,91×.
- **Filter 2 Cutoff** (SDATA 98, Filter): teilweise, cos 0,91, Stärke 0,88×.
- **Filter 2 Drive** (SDATA 101, Filter): teilweise, cos 0,88, Stärke 0,65×.
- **Filter 2 Keytrack** (SDATA 106, Filter): teilweise, cos 0,93.
- **Filter 2 Env Amount** (SDATA 107, Filter): teilweise, cos 0,99.
- **Filter 2 Env Velocity** (SDATA 108, Filter): teilweise, cos 0,66.
- **Amplifier Volume** (SDATA 121, Verstärker): teilweise, cos 0,96, Stärke 1,15×.
- **Amplifier Velocity** (SDATA 122, Verstärker): teilweise, cos 0,97.
- **Amplifier Mod Amount** (SDATA 124, Verstärker): teilweise, cos 0,42, Stärke 0,60×.
- **Effect 1 Mix** (SDATA 129, Effekte): teilweise, cos 0,82, Stärke 0,99×.
- **Osc 1 PWM Amount** (SDATA 11, Oszillatoren): Mismatch.
- **Osc Pitch Amount** (SDATA 51, Oszillatoren): Mismatch.
- **Mixer Osc 1 Balance** (SDATA 62, Mixer): Mismatch.
- **Mixer Noise Balance** (SDATA 68, Mixer): Mismatch.
- **Filter 1 Resonance** (SDATA 80, Filter): Mismatch, cos 0,25, Stärke 0,66×.
- **Filter 2 Resonance** (SDATA 100, Filter): Mismatch, cos 0,44, Stärke 0,52×.
- **Effect 1 Parameter 1** (SDATA 130, Effekte): Mismatch, cos 0,44, Stärke 1,58×.
- **Mixer Noise Colour** (SDATA 69, Mixer): defekt, cos 0,44, Stärke 0,55×.
- **Effect 2 Mix** (SDATA 145, Effekte): defekt.
- **LFO 1 Speed** (SDATA 161, LFOs): defekt.
- **LFO 1 Delay** (SDATA 166, LFOs): defekt.
- **LFO 1 Fade** (SDATA 167, LFOs): defekt.

### 4.3 Im Init nicht prüfbar (n/a)

Diese Parameter haben im Init-Sound auf keinem Gerät eine hörbare Wirkung, weil ihr Ziel im Init nicht aktiv ist oder der Init-Wert die Wirkung aufhebt: Oszillator 2/3 aus, Filter 2 aus, Effekt-Mix 0, Filter bei 100 % offen (Hüllkurve und Resonanz können nichts mehr bewegen), Amp-Decay bei Sustain 100 %. Pan- und Balance-Parameter werden von der Monosumme der Messung nicht erfasst (dafür ist eine L/R-getrennte Auswertung nötig) und sind deshalb hier ebenfalls n/a. Für die übrige Gruppe ist eine Messung mit aktiviertem Ziel nötig (Test B/C/D, soweit durchgeführt):

Osc 1 PWM Source, Osc 2 Pulsewidth, Osc 2 PWM Source, Osc 2 PWM Amount, Osc 3 Pulsewidth, Osc 3 PWM Source, Osc 3 PWM Amount, Osc 2 Sync to O3, Osc Pitch Source, Glide, Glide Rate, Mixer Osc 2 Balance, Mixer RingMod Level, Filter 1 Mod Source, Filter 2 Mod Source, Filter 2 Pan Amount, Amplifier Mod Source, Effect 1 Type, Effect 1 Parameter 3, Effect 1 Parameter 4, Effect 2 Type, Effect 2 Parameter 2, Effect 2 Parameter 3, LFO 1 Shape, LFO 1 Sync, LFO 1 Start Phase, LFO 2 Shape, LFO 2 Speed, LFO 2 Sync, LFO 2 Start Phase, LFO 2 Delay, LFO 3 Shape, LFO 3 Speed, LFO 3 Sync, LFO 3 Start Phase, LFO 3 Delay, Amplifier Envelope Decay, Envelope 3 Attack, Envelope 3 Decay, Envelope 3 Sustain, Envelope 3 Release, Envelope 4 Attack, Envelope 4 Decay, Envelope 4 Sustain, Envelope 4 Release, Modulation 1 Source, Modulation 1 Destination, Modulation 2 Source, Modulation 3 Source, Modulation 4 Source, Modulation 5 Source, Modulation 6 Source, Modulation 7 Source, Modulation 8 Source, Modulation 9 Source, Modulation 10 Source, Modulation 11 Source, Modulation 12 Source, Modulation 13 Source, Modulation 14 Source.


## 5. Anpassungskurven

### 5.1 Feinstimmung (Detune) — korrigiert und verifiziert

Der Blofeld verstimmt über den vollen Rohbereich 0–127 um **−101 … +100 Cent** (1,6 Cent je Rohschritt). Der Iridium reagiert auf `OscNFinePitch` mit **203 Cent pro Norm-Einheit**. Die bisherige Umrechnung teilte durch 254 und erzeugte damit nur die halbe Verstimmung; richtig ist:

```
Iridium-Wert = 0,5 + (Blofeld-Rohwert − 64) / 127
```

| Blofeld roh | Cent | Iridium alt (÷254) | Cent alt | Iridium neu (÷127) | Cent neu |
|---|---|---|---|---|---|
| 0 | −101 | 0,248 | −51 | 0,000 | −101 |
| 32 | −50 | 0,374 | −25 | 0,248 | −51 |
| 64 | 0 | 0,500 | 0 | 0,500 | 0 |
| 127 | +100 | 0,748 | +50 | 0,996 | +101 |

Nach der Korrektur stimmen Richtung und Stärke (Cosinus 0,97–0,98, Stärkeverhältnis 1,0). Der Konverter wurde entsprechend angepasst (`qpat_map.fine_pitch_norm`, Test angepasst).

### 5.2 Kandidaten für weitere Kurven

Für die übrigen Parameter reichen vier Stützstellen nicht für eine belastbare Kurve. Die folgende Liste nennt die Richtung aus dem gemessenen Stärkeverhältnis; für eine echte Kurve sind 8–12 Stützstellen nötig.

| Parameter | Status | Stärke I/B | Empfehlung |
|---|---|---|---|
| Allocation/Unisono | teilweise | 0,93 | Wirkung passt, Abweichung liegt in der Form |
| Unisono Detune | teilweise | 1,14 | Wirkung passt, Abweichung liegt in der Form |
| Mixer Noise Level | teilweise | 0,72 | Iridium nur 0,7× so stark → Wert spreizen |
| Mixer Noise Colour | defekt | 0,55 | Iridium ohne ausreichende Wirkung → Ziel prüfen |
| Filter 1 Cutoff | teilweise | 0,92 | Wirkung passt, Abweichung liegt in der Form |
| Filter 1 Resonance | Mismatch | 0,66 | Iridium nur 0,7× so stark → Wert spreizen |
| Filter 1 Drive | teilweise | 0,99 | Wirkung passt, Abweichung liegt in der Form |
| Filter 1 Mod Amount | teilweise | 0,70 | Iridium nur 0,7× so stark → Wert spreizen |
| Filter 2 Type | teilweise | 0,91 | Wirkung passt, Abweichung liegt in der Form |
| Filter 2 Cutoff | teilweise | 0,88 | Wirkung passt, Abweichung liegt in der Form |
| Filter 2 Resonance | Mismatch | 0,52 | Iridium nur 0,5× so stark → Wert spreizen |
| Filter 2 Drive | teilweise | 0,65 | Iridium nur 0,7× so stark → Wert spreizen |
| Amplifier Volume | teilweise | 1,15 | Wirkung passt, Abweichung liegt in der Form |
| Amplifier Mod Amount | teilweise | 0,60 | Iridium nur 0,6× so stark → Wert spreizen |
| Effect 1 Mix | teilweise | 0,99 | Wirkung passt, Abweichung liegt in der Form |
| Effect 1 Parameter 1 | Mismatch | 1,58 | Iridium 1,6× zu stark → Wert komprimieren |
| Effect 1 Parameter 2 | teilweise | 1,35 | Iridium 1,4× zu stark → Wert komprimieren |
| Effect 1 Parameter 5 | teilweise | 0,97 | Wirkung passt, Abweichung liegt in der Form |
| Filter Envelope Decay | teilweise | 0,75 | Iridium nur 0,8× so stark → Wert spreizen |
| Amplifier Envelope Attack | teilweise | 1,19 | Wirkung passt, Abweichung liegt in der Form |
| Amplifier Envelope Sustain | teilweise | 0,89 | Wirkung passt, Abweichung liegt in der Form |
| Modulation 1 Amount | teilweise | 0,54 | Iridium nur 0,5× so stark → Wert spreizen |

Die maschinenlesbare Fassung der Messwerte steht in `docs/research/profiling_init_2026-11-21.csv` (eine Zeile je Parameter und Wert).

## 6. Empfehlungen

1. **Feinstimmung** ist kalibriert (Divisor 127) und muss nur noch in einer Testkonvertierung gegengeprüft werden. **Modulationsbeträge** (Osc Pitch Amount, PWM Amount, Amp Velocity) als Nächstes prüfen: dort reagiert nur der Iridium.
2. **PWM-/Modulationszeilen** prüfen: im Init erzeugen Osc 1 PWM Amount und Osc Pitch Amount am Iridium eine hörbare Wirkung, obwohl der Blofeld unbeeinflusst bleibt. Das deutet auf aktive Matrix-Zeilen mit einem Betrag hin, der am Iridium nicht neutral ist.
3. **Filter 2 / Effekte / Oszillator 2+3** in einer zweiten Runde mit aktivem Ziel messen; im Init sind sie prinzipbedingt nicht beurteilbar. Die Test-B-Ergebnisse haben wegen der drei gleichzeitig klingenden Oszillatoren eine höhere Streuung und sind gröber als die Init-Werte.
4. **Filter-Hüllkurve** braucht einen Test mit *geschlossenem* Filter (Cutoff ≈ 70); bei ganz offenem Filter kann die Hüllkurve nichts mehr öffnen und ist nicht messbar.
5. Parameter mit Status „defekt“ (keine Iridium-Reaktion) vor dem nächsten Konverter-Update gezielt nachziehen.

## 7. Anhang

- Einzelmessungen: `docs/research/profiling_init_2026-11-21.csv` (846 Zeilen, alle Werte und Iridium-Zielparameter).
- Aufnahmen: `recordings/profile/` (je Parameter/Wert/Gerät eine `.npy`).
- Messprotokoll: `recordings/profile_sweep.jsonl` (Init), `recordings/profile_testb_clean.jsonl` / `_fx.jsonl` (Test B), `recordings/profile_testb_release.jsonl` (Test C).
- Kurven/Kandidaten (maschinenlesbar): `docs/research/profiling_curves_2026-11-21.json`.
- Architektur-Differenzen und Workarounds: `docs/research/ARCHITEKTUR-DIFFERENZEN.md`.
