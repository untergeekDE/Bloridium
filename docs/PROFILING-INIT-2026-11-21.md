# Profiling-Sweep Init-Sound — Blofeld → Iridium

**Datum:** 2026-11-21 · **Geräte:** Blofeld (OS 1.24), Iridium Keyboard (OS 4.1) · **Interface:** Focusrite Scarlett 18i8, 48 kHz

## 1. Ziel und Aufbau

Der Sweep prüft, ob die im Konverter hinterlegte Parameter-Map die *Wirkung* eines Parameters richtig überträgt — nicht nur, ob ein Wert ankommt. Ausgangspunkt ist auf beiden Geräten der Init-Sound. Jeder konvertierte Parameter wird einzeln verändert (0 %, 25 %, 50 %, 100 % seines Wertebereichs; bei Schaltern die entsprechenden Rasterpositionen) und die hörbare Wirkung auf beiden Geräten getrennt gemessen.

Der Blofeld spielt den Init-Sound (A066: ein Sägezahn, Filter LP24 offen, Amp-Hüllkurve A0/D52/S127/R0). Der Iridium spielt den *konvertierten* Init-Sound, also die Ausgabe des Konverters für genau diesen Blofeld-Sound. Damit wird jede Abweichung dem Parameter zugeordnet und nicht dem Grundklang.

## 2. Messmethode (von Hand nachvollziehbar)

- Beide Synths spielen gleichzeitig dieselbe Note (C4, Anschlag 100), Aufnahme 2,0 s; Note-off nach 1,2 s, damit auch die Release-Phase erfasst wird.
- Getrennte Eingänge am Interface: Blofeld In 3/4, Iridium In 5/6. Pegel vor jeder Messung geprüft, keine Übersteuerung.
- Vor jeder Messreihe wird der Init-Sound neu geladen. Zwei identische Init-Aufnahmen liefern die Wiederholstreuung (Rauschboden).
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
| **n/a** | im Init-Sound auf keinem Gerät hörbar (z. B. Oszillator aus) |

Rauschboden: Blofeld 0,76 · Iridium 0,74 (Wirkungsmaß). Schwelle für „hörbar“: 2,0.

## 3. Ergebnis

**35** konvertierte Parameter geprüft, **139** Einzelmessungen. Davon im Init hörbar: **12**. OK **8**, teilweise **2**, Mismatch **2**, defekt **0**, n/a **23**.

| # | Block | Parameter | Werte (roh) | Status | cos | Stärke I/B | Befund |
|---|---|---|---|---|---|---|---|
| 1 | Oszillatoren | Osc 1 Octave | 32, 48, 64, 80 | **OK** | 0,98 | 1,01 | Wirkung vergleichbar |
| 2 | Oszillatoren | Osc 1 Semitone | 52, 58, 64, 76 | **OK** | 0,99 | 1,01 | Wirkung vergleichbar |
| 3 | Oszillatoren | Osc 1 Detune | 0, 32, 64, 127 | **teilweise** | 0,71 | 0,81 | Wirkung vergleichbar |
| 8 | Oszillatoren | Osc 1 Shape | 0, 18, 36, 72 | **OK** | 0,94 | 0,93 | Wirkung vergleichbar |
| 10 | Oszillatoren | Osc 1 PWM Source | 0, 8, 15, 30 | **n/a** | – | – | im Init nicht hörbar |
| 11 | Oszillatoren | Osc 1 PWM Amount | 0, 32, 64, 127 | **Mismatch** | – | – | nur Iridium reagiert |
| 17 | Oszillatoren | Osc 2 Octave | 32, 48, 64, 80 | **n/a** | – | – | im Init nicht hörbar |
| 18 | Oszillatoren | Osc 2 Semitone | 52, 58, 64, 76 | **n/a** | – | – | im Init nicht hörbar |
| 19 | Oszillatoren | Osc 2 Detune | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 24 | Oszillatoren | Osc 2 Shape | 0, 18, 36, 72 | **n/a** | – | – | im Init nicht hörbar |
| 26 | Oszillatoren | Osc 2 PWM Source | 0, 8, 15, 30 | **n/a** | – | – | im Init nicht hörbar |
| 27 | Oszillatoren | Osc 2 PWM Amount | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 33 | Oszillatoren | Osc 3 Octave | 32, 48, 64, 80 | **n/a** | – | – | im Init nicht hörbar |
| 34 | Oszillatoren | Osc 3 Semitone | 52, 58, 64, 76 | **n/a** | – | – | im Init nicht hörbar |
| 35 | Oszillatoren | Osc 3 Detune | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 40 | Oszillatoren | Osc 3 Shape | 0, 18, 36, 72 | **OK** | 0,93 | 0,89 | Wirkung vergleichbar |
| 42 | Oszillatoren | Osc 3 PWM Source | 0, 8, 15, 30 | **n/a** | – | – | im Init nicht hörbar |
| 43 | Oszillatoren | Osc 3 PWM Amount | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 49 | Oszillatoren | Osc 2 Sync to O3 | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 50 | Oszillatoren | Osc Pitch Source | 0, 8, 15, 30 | **n/a** | – | – | im Init nicht hörbar |
| 51 | Oszillatoren | Osc Pitch Amount | 0, 32, 64, 127 | **Mismatch** | – | – | nur Iridium reagiert |
| 53 | Oszillatoren | Glide | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 57 | Mixer | Glide Rate | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 58 | Mixer | Allocation/Unisono | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 59 | Mixer | Unisono Detune | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 61 | Mixer | Mixer Osc 1 Level | 0, 32, 64, 127 | **OK** | 0,93 | 0,94 | Wirkung vergleichbar |
| 63 | Mixer | Mixer Osc 2 Level | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 65 | Mixer | Mixer Osc 3 Level | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 67 | Mixer | Mixer Noise Level | 0, 32, 64, 127 | **teilweise** | 0,66 | 0,77 | Wirkung vergleichbar |
| 71 | Mixer | Mixer RingMod Level | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 77 | Filter | Filter 1 Type | 0, 3, 6, 11 | **OK** | 0,81 | 0,93 | Wirkung vergleichbar |
| 78 | Filter | Filter 1 Cutoff | 0, 32, 64, 127 | **OK** | 0,94 | 0,78 | Wirkung vergleichbar |
| 80 | Filter | Filter 1 Resonance | 0, 32, 64, 127 | **n/a** | – | – | im Init nicht hörbar |
| 81 | Filter | Filter 1 Drive | 0, 32, 64, 127 | **OK** | 0,97 | 1,03 | Wirkung vergleichbar |
| 86 | Filter | Filter 1 Keytrack | 0, 32, 64 | **n/a** | – | – | im Init nicht hörbar |

## 4. Auffälligkeiten

### 4.1 Gut übertragen (OK)

- **Osc 1 Octave** (SDATA 1), cos 0,98, Stärke 1,01×.
- **Osc 1 Semitone** (SDATA 2), cos 0,99, Stärke 1,01×.
- **Osc 1 Shape** (SDATA 8), cos 0,94, Stärke 0,93×.
- **Osc 3 Shape** (SDATA 40), cos 0,93, Stärke 0,89×.
- **Mixer Osc 1 Level** (SDATA 61), cos 0,93, Stärke 0,94×.
- **Filter 1 Type** (SDATA 77), cos 0,81, Stärke 0,93×.
- **Filter 1 Cutoff** (SDATA 78), cos 0,94, Stärke 0,78×.
- **Filter 1 Drive** (SDATA 81), cos 0,97, Stärke 1,03×.

### 4.2 Abweichungen (teilweise / Mismatch / defekt)

- **Osc 1 Detune** (SDATA 3, Oszillatoren): teilweise, cos 0,71, Stärke 0,81×.
- **Mixer Noise Level** (SDATA 67, Mixer): teilweise, cos 0,66, Stärke 0,77×.
- **Osc 1 PWM Amount** (SDATA 11, Oszillatoren): Mismatch.
- **Osc Pitch Amount** (SDATA 51, Oszillatoren): Mismatch.

### 4.3 Im Init nicht prüfbar (n/a)

Diese Parameter haben im Init-Sound auf keinem Gerät eine hörbare Wirkung, weil ihr Ziel im Init nicht aktiv ist (Oszillator 2/3 aus, Filter 2 aus, Effekt-Mix 0, Filter-Hüllkurvenanteil 0 usw.):

Osc 1 PWM Source, Osc 2 Octave, Osc 2 Semitone, Osc 2 Detune, Osc 2 Shape, Osc 2 PWM Source, Osc 2 PWM Amount, Osc 3 Octave, Osc 3 Semitone, Osc 3 Detune, Osc 3 PWM Source, Osc 3 PWM Amount, Osc 2 Sync to O3, Osc Pitch Source, Glide, Glide Rate, Allocation/Unisono, Unisono Detune, Mixer Osc 2 Level, Mixer Osc 3 Level, Mixer RingMod Level, Filter 1 Resonance, Filter 1 Keytrack.

Für diese Gruppe ist eine zweite Messreihe mit aktiviertem Ziel nötig (Test-Sound B: Oszillator 2/3 auf Sine/Saw mit Pegel 90, Filter 2 parallel, FX-Mix 50 %, Filter-Env-Anteil 60 %).

## 5. Anpassungskurven

Fuer jeden Parameter mit hörbarer Wirkung wurde geprüft, welche *Iridium*-Stellung die gleiche Wirkung erzeugt wie eine gegebene *Blofeld*-Stellung. Angegeben sind die Stützstellen (Blofeld-Wert → aktuell konvertierter Iridium-Wert → empfohlener Iridium-Wert). Wo beide Spalten gleich sind, stimmt die Map; wo sie abweichen, ist die Kurve die Korrektur.

| Parameter | Blofeld | konvertiert | empfohlen | cos |
|---|---|---|---|---|
| Osc 1 Detune | 0 | 0,248 | 0,004 | +203 Cent/Norm |
| Osc 1 Detune | 32 | 0,374 | 0,254 | +203 Cent/Norm |
| Osc 1 Detune | 64 | 0,500 | 0,506 | +203 Cent/Norm |
| Osc 1 Detune | 127 | 0,748 | 0,991 | +203 Cent/Norm |
| Filter 1 Cutoff | 0 | 0,037 | 0,511 | 0,111 |
| Filter 1 Cutoff | 32 | 0,274 | 0,037 | 0,674 |
| Filter 1 Cutoff | 64 | 0,511 | 0,511 | 0,987 |
| Filter 1 Cutoff | 127 | 0,978 | 0,978 | 0,691 |
| Filter 1 Drive | 0 | 3,000 | 3,000 | 0,778 |
| Filter 1 Drive | 32 | 0,252 | 0,504 | 0,881 |
| Filter 1 Drive | 64 | 0,504 | 0,504 | 0,654 |
| Filter 1 Drive | 127 | 1,000 | 1,000 | 0,906 |

## 6. Empfehlungen

1. **Detune/Fein-Stimmung** und **Oszillator-Pitch** zuerst kalibrieren: dort ist die Wirkung am Iridium systematisch zu stark (siehe Tabelle), was bei zwei verstimmten Oszillatoren doppelt auffällt.
2. **PWM-/Modulationszeilen** prüfen: mehrere PWM-Parameter erzeugen am Iridium eine hörbare Wirkung, obwohl der Blofeld im Init unbeeinflusst bleibt. Das deutet auf aktive Matrix-Zeilen mit neutralem Betrag am Iridium hin.
3. **Filter 2 / Effekte / Oszillator 2+3** in einer zweiten Runde mit aktivem Ziel messen; im Init sind sie prinzipbedingt nicht beurteilbar.
4. Parameter mit Status „defekt“ (keine Iridium-Reaktion) vor dem nächsten Konverter-Update gezielt nachziehen.

## 7. Anhang

- Einzelmessungen: `docs/profiling_init_2026-11-21.csv` (139 Zeilen, alle Werte und Iridium-Zielparameter).
- Aufnahmen: `recordings/profile/` (je Parameter/Wert/Gerät eine `.npy`).
- Messprotokoll: `recordings/profile_sweep.jsonl`.
