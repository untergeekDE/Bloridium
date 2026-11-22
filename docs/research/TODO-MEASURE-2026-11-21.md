# TODO_MEASURE — Messergebnisse 2026-11-21

Automatisch erzeugt von `scripts/profile_todo_measure.py report`.

## A1 — PWM bei Pulse-Wellenform (positiver Fall)

Osc 2 = Pulse, PWM Source = LFO 1; LFO 1 mit Fade = 64 (kein Ausblenden), Filter offen, FX aus. Amount 64 ist die Neutralstellung (0 Modulation), 0 = maximale negative, 127 = maximale positive Modulation.

**Osc 2 PWM Amount** (Schwelle 2.0)

| raw | Blofeld | Iridium | Cos | Modulation BF / IR | Status |
|---:|---:|---:|---:|---:|---|
| 0 | 8.12 | 0.22 | - | 2.949 / 0.224 | defekt |
| 32 | 1.49 | 0.15 | - | 0.241 / 0.189 | n/a |
| 64 | 0.21 | 0.30 | - | 0.216 / 0.200 | n/a |
| 127 | 6.58 | 0.14 | - | 2.804 / 0.219 | defekt |

## A3 — FX2-Typen (FX1 = Off, Effect 2 Mix 127)

Blofeld erlaubt in Effect 2 nur Delay/Clk.Delay/Reverb; Effect 1 nur Chorus/Flanger/Phaser/Overdrive/Triple FX. Delay/Reverb in Effect 1 normalisiert das Gerät auf Chorus (Readback geprüft). Delay-Tails weichen ab: der Blofeld-Delay braucht seine Zeit-/Feed-Parameter, der Konverter setzt nur Feed/HiCut (p5/p6), keine Delay-Zeit.

| Effect 2 Type | Blofeld Tail | Iridium Tail | Iridium FX2 |
|---:|---:|---:|---:|
| 0 | -58.2 dB | -58.8 dB | 0.0 |
| 6 | -57.0 dB | -26.9 dB | 5.0 |
| 7 | -10.4 dB | -50.0 dB | 5.0 |
| 8 | -16.6 dB | -15.2 dB | 6.0 |

## A3 — FX getrennt: FX1 allein (FX2 = Off)

Schwelle 4.9. Die Baseline ist Phaser (100 % wet); die Typen 0–5 sind die gültigen Effect-1-Typen. Delay/Clk.Delay/Reverb normalisiert der Blofeld in Effect 1 auf Chorus (Readback: 6/7/8 → 1). Beide Seiten reagieren auf alle gültigen Typen mit vergleichbarer Stärke; der spektrale Charakter der Engines unterscheidet sich (niedriger Cos).

| Parameter | raw | Blofeld | Iridium | Cos | Status |
|---|---:|---:|---:|---:|---|
| Effect 1 Type | 0 | 5.83 | 5.71 | 0.40 | Mismatch |
| Effect 1 Type | 1 | 4.68 | 5.11 | - | Mismatch |
| Effect 1 Type | 2 | 5.01 | 4.65 | - | defekt |
| Effect 1 Type | 3 | 2.18 | 1.90 | - | n/a |
| Effect 1 Type | 4 | 6.05 | 6.23 | 0.35 | Mismatch |
| Effect 1 Type | 5 | 9.09 | 5.59 | -0.61 | Mismatch |
| Effect 1 Mix | 0 | 5.88 | 5.82 | 0.41 | Mismatch |
| Effect 1 Mix | 32 | 2.69 | 1.97 | - | n/a |
| Effect 1 Mix | 64 | 1.72 | 2.74 | - | n/a |
| Effect 1 Mix | 127 | 1.84 | 3.32 | - | n/a |

## A3 — FX getrennt: FX2 = Reverb (FX1 = Off)

Metrik: Pegel des Hall-Schweifs ab 3,0 s (≈1 s nach Note-Off) bis Aufnahmeende, relativ zum gehaltenen Ton.

| Mix | Blofeld Tail | Iridium Tail | Iridium ReverbGain |
|---:|---:|---:|---:|
| 0 | -58.5 dB | -58.9 dB | 0.0 |
| 32 | -27.9 dB | -34.0 dB | 0.252 |
| 64 | -19.5 dB | -23.4 dB | 0.504 |
| 127 | -14.9 dB | -15.7 dB | 1.0 |

**Hub Blofeld 43.6 dB, Iridium 43.2 dB → OK.**

## A4 — Unisono Detune (5 Stimmen)

Metrik: leistungsgewichtete Spektralbreite um C4 (±55 Hz), Mittel aus 2 Takes.

| raw | Blofeld | Iridium | Δ Blofeld | Δ Iridium | Status |
|---:|---:|---:|---:|---:|---|
| 0 | 1.50 Hz | 1.47 Hz | +0.00 | +0.00 | n/a |
| 32 | 3.67 Hz | 1.56 Hz | +2.17 | +0.09 | defekt |
| 64 | 6.95 Hz | 3.19 Hz | +5.45 | +1.72 | Mismatch |
| 127 | 13.89 Hz | 11.51 Hz | +12.39 | +10.04 | OK |

## A4 — Unisono Count (Detune 127)

Metrik: leistungsgewichtete Spektralbreite um C4 (±55 Hz), Mittel aus 2 Takes.

| raw | Blofeld | Iridium | Δ Blofeld | Δ Iridium | Status |
|---:|---:|---:|---:|---:|---|
| 0 | 1.42 Hz | 1.41 Hz | +0.00 | +0.00 | n/a |
| 16 | 9.48 Hz | 10.52 Hz | +8.06 | +9.11 | OK |
| 32 | 8.05 Hz | 11.91 Hz | +6.63 | +10.50 | OK |
| 48 | 10.77 Hz | 11.63 Hz | +9.35 | +10.22 | OK |
| 64 | 12.79 Hz | 11.42 Hz | +11.37 | +10.01 | OK |
| 80 | 12.51 Hz | 10.72 Hz | +11.09 | +9.31 | OK |
| 96 | 11.66 Hz | 11.10 Hz | +10.24 | +9.69 | OK |
| 112 | 11.94 Hz | 11.19 Hz | +10.52 | +9.78 | OK |

