# TODO_MEASURE — offene Verifikation der Konverter-Fixes

**Stand:** 2026-11-21 · **Geräte:** Blofeld + Iridium Keyboard, beide über USB
(kein Launchpad) · **Audio:** Scarlett 18i8, 48 kHz, Blofeld In 3/4, Iridium In 5/6.

Die Code-Fixes A1, A2, A3, A4 und A7a (LFO-Fade) sind umgesetzt und
unit-getestet; Details in `FIXES_HISTORY.md`. Diese Datei sammelt nur noch, was
am Gerät nachgemessen bzw. an der Messmethodik repariert werden muss.

**Runner:** `scripts/profile_todo_measure.py <group>` misst die offenen Gruppen
getrennt (`pulse_amt`, `fx1types`, `reverb`, `unison_detune`, `unison_count`).
`... report` schreibt die Zusammenfassung nach
`docs/research/TODO-MEASURE-2026-11-21.md`. Der Runner setzt für FX1-Messungen
`FX2Type = Off` und für Reverb `FX1Type = Off` — damit ist die alte
Reverb-Kontamination des FX-Sweeps beseitigt.

## 1. A1 — PWM-Zeile nur für pulsartige Shapes

**Status: negativer Fall und positiver Pulse-Fall gemessen (2026-11-21), bestanden.**
Zwei Konverter-Punkte bleiben offen (siehe unten).

`python3 scripts/profile_testb_sweep.py osc2` (Osc 2 = Saw, PWM Source = LFO 2):
PWM Source und PWM Amount sind jetzt auf **beiden** Seiten n/a:

| Parameter | Werte | Blofeld-Wirkung | Iridium-Wirkung | Status |
|---|---|---|---|---|
| Osc 2 PWM Source | 0, 8, 15, 30 | 0,13–0,51 | 0,14–0,43 | n/a |
| Osc 2 PWM Amount | 0, 32, 64, 127 | 0,13–0,27 | 0,14–0,27 | n/a |

Damit ist die alte Beobachtung „nur der Iridium reagiert“ weg. Die Zeile wird
für Saw/Triangle/Sine nicht mehr angelegt; der Hinweis steht als
`Ignored: Osc N PWM …` im `unmapped`-Report (Webapp zählt ihn nicht mehr als
„not in MIDI map“).

**Noch offen (optional):** positiver Pulse-Fall am Gerät. Unit-Test deckt ihn ab
(`test_pwm_row_only_for_pulse_shapes`), aber ein Sweep mit `Osc 2 Shape = Pulse`
und `PWM Source = LFO 1` wäre die saubere Hardware-Bestätigung.

**Positiver Pulse-Fall gemessen (2026-11-21):**
`python3 scripts/profile_todo_measure.py pulse_amt` — Osc 2 = Pulse,
PWM Source = LFO 1, LFO 1 Fade = 64 (kein Ausblenden), Filter offen, FX aus.
Wirkung = Effektvektor gegen die Neutralstellung (Amount 64); Modulation =
zeitliche Streuung des Log-Spektrums.

| PWM Amount | Blofeld (Wirkung / Mod.) | Iridium (Wirkung / Mod.) | Status |
|---:|---:|---:|---|
| 0 (−64) | 8,12 / 2,95 | 0,22 / 0,22 | defekt |
| 32 (−32) | 1,49 / 0,24 | 0,15 / 0,19 | n/a |
| 64 (neutral) | 0,21 / 0,22 | 0,30 / 0,20 | n/a |
| 127 (+63) | 6,58 / 2,80 | 0,14 / 0,22 | defekt |

**Ergebnis:** Die PWM-Zeile wird für Pulse angelegt (Ziel `WF2 Warp`), und der
Blofeld moduliert bei maximalem negativem/positivem Betrag deutlich. Der
Iridium-Warp reagiert nur schwach. Ein Teil davon ist die **ungekalibrierte
LFO-Speed-Kurve**: Blofeld raw 20 ≈ 0,36 Hz, der konvertierte Iridium-Wert
(`Lfo1Speed = 0,157`) läuft messbar deutlich langsamer (~0,2 Hz). Der Warp-Ziel
selbst reagiert (manueller Matrix-Test: Centroid 3168 → 3740 Hz über den Betrag).

**Neue Konverter-Punkte (für die Fix-Session, nicht hier geändert):**
- [ ] `qpat_map.py` PWM-Block prüft `amt != 0`. Der Blofeld-Betrag ist aber
      bipolar: **0 = maximale negative Modulation, 64 = neutral**. Amount 0 wird
      deshalb fälschlich als „aus“ behandelt und bekommt keine Matrixzeile.
      Erwartung: auf `amt != 64` prüfen (bzw. Betrag zentrieren).
- [ ] Amount 32 (−32) zeigt am Blofeld keine messbare Modulation, obwohl die
      statische Pulsbreite (SDATA 25) sauber reagiert. Die PWM-Betragskennlinie
      ist also nicht linear um 64; vor einer Verstärkung des Warp-Betrags klären.

## 2. A2 — Filter 2

**Status: Code-Fix fertig; Parallel- und Seriell-Messung durchgeführt (2026-11-22).**

Der Code setzt jetzt in Parallel-Schaltung `FilterLink = Independent` und einen
eigenen `Filter2Type`; außerdem Resonanz-Kennlinie (`raw 113 -> 1.0`) und
Filter-Drive als Insert (`DriveDryWet = 1.0`). Details in `FIXES_HISTORY.md`.

**Zu tun:**

- [x] `python3 scripts/profile_testb_sweep.py f2` erneut fahren.
- [x] Vor dem Lauf per Readback prüfen, dass im Edit-Buffer wirklich
      `FilterLink=Independent`, `Filter2Type=3` (A010 LP24) und
      `DriveDryWet=1.0` stehen.
- [x] F2-Type/Cutoff/Resonanz/Drive in Parallel- und Seriell-Schaltung prüfen.
- [ ] Bei weiterhin schlechtem Resonanz-Cosinus: Filter-1/2-Modelle
      (`Filter1Model`/`Filter2Model`, B5) als nächsten Hebel untersuchen.

**Readback (2026-11-22):** Parallel: `FilterLink=6` (Independent),
`Filter2Type=3` (24 dB LP), `Filter2State=0` (Active); bei F2 Drive > 0:
`FX1Type=8` (Drive), `DriveDryWet=1.0`. Seriell: `Filter2State=2` (Off),
`FilterFormerRouting=1` (Filter > Former), `DigiFormerType=7` (Nave LP24).

**Ergebnis parallel (`f2`):**

| Parameter | Ergebnis |
|---|---|
| Filter 2 Type | raw 3 **OK** (cos 0,83), 0 Mismatch, 6 teilweise |
| Filter 2 Cutoff | 32/64/127 **OK** (cos 0,95–0,98), 0 teilweise |
| Filter 2 Resonance | 127 Mismatch (cos 0,13) |
| Filter 2 Drive | 127 **OK** (cos 0,99), 64 defekt, 32 n/a |

**Ergebnis seriell (`f2ser`, DigiFormer):**

| Parameter | Ergebnis |
|---|---|
| Filter 2 Type | 0/6 **OK** (cos 0,99), 3 defekt (kein `DigiFormerType` für diesen Typ) |
| Filter 2 Cutoff | 0/32/127 **OK** (cos 0,81–0,99), 64 teilweise |
| Filter 2 Resonance | 127 defekt (`DigiFormerColor`) |
| Filter 2 Drive | 127 **OK** (cos 0,97), 64 teilweise, 32 defekt |

**Fazit:** Type/Cutoff/Drive sind in beiden Schaltungen weitgehend OK; die
**Resonanz** bleibt die offene Baustelle (parallel Mismatch, seriell defekt).

## 3. A3 — Reverb-Mix über `ReverbGain`

**Status: Code-Fix + Unit-Test fertig; getrennte Messung durchgeführt (2026-11-21).**

Der `fx`-Sweep läuft mit `FX1 = Chorus` **und** `FX2 = Reverb` gleichzeitig.
Dadurch wird jede Effect-1-Mix-/Chorus-Messung vom Reverb überlagert
(Baseline-Rauschen 2,04/1,02 → Schwelle 5,11; Effect 1 Mix durchgehend n/a).
Das ist ein **Fehler der Messanordnung**, nicht des Konverters: der Konverter
setzt mit dem neuen Fix `ReverbGain = norm(Effect 2 Mix)` (Handbuch: Gain ist
der Reverb-Dry/Wet-Regler), nicht mehr die alte Matrix-Zeile.

**Zu tun:**

- [x] Mit `scripts/profile_todo_measure.py fx1types` FX1 allein messen
      (`FX2Type = Off`).
- [x] Mit `scripts/profile_todo_measure.py reverb` FX2 allein messen
      (`FX1Type = Off`) und Effect 2 Mix 0/32/64/127 % auf monotone Hall-Zunahme
      prüfen (Status OK/teilweise, nicht defekt).
- [x] Danach `profile_testb_sweep.py fx` nicht mehr als Gesamtlauf verwenden.
- [x] Erst dann `FIXES_HISTORY.md` als „verifiziert“ markieren.

**Ergebnis (2026-11-21):**

- **FX1 allein:** Alle neun Effect-1-Typen erzeugen auf beiden Seiten eine
  deutliche Wirkung (Blofeld 1,2–10,5 / Iridium 2,2–6,4). Die adaptive Schwelle
  liegt wegen des Chorus-Phasenrauschens bei 8,8, deshalb stehen die Zeilen im
  Bericht als n/a — das heißt hier *nicht* „keine Wirkung“. Der spektrale
  Charakter der Engines unterscheidet sich (Cos 0,0–0,4), die Stärke passt.
- **Reverb allein:** Tail-Pegel ab 3,0 s (≈1 s nach Note-Off) relativ zum
  gehaltenen Ton:

| Effect 2 Mix | Blofeld | Iridium | Iridium `ReverbGain` |
|---:|---:|---:|---:|
| 0 | −58,5 dB | −58,9 dB | 0,0 |
| 32 | −27,9 dB | −34,0 dB | 0,252 |
| 64 | −19,5 dB | −23,4 dB | 0,504 |
| 127 | −14,9 dB | −15,7 dB | 1,0 |

  Beide Seiten steigen monoton über 43 dB. **A3 verifiziert.**

**FX-Typen (Zusatzbefund, 2026-11-21):**
- Effect 1 akzeptiert am Blofeld nur Bypass/Chorus/Flanger/Phaser/Overdrive/
  Triple FX. Delay/Clk.Delay/Reverb werden in Effect 1 auf Chorus normalisiert
  (Readback 6/7/8 → 1). Der `fx1types`-Sweep misst daher nur 0–5; alle sechs
  erzeugen auf beiden Seiten eine deutliche Wirkung, der Charakter unterscheidet
  sich (niedriger Cos — bei FX-Engines erwartbar, die Stärke ist die belastbare
  Aussage).
- Effect 2 akzeptiert Delay/Clk.Delay/Reverb. Der Reverb-Fall ist sauber
  (Tabelle oben). Die **Delay-Fälle weichen ab**: der Konverter setzt nur
  `DelayFeed`/`DelayHiCut` aus p5/p6, aber **keine Delay-Zeit**; der
  Blofeld-Delay braucht seine Zeit-/Feed-Parameter. Offener Punkt für die
  Fix-Session, nicht Teil der A3-Abnahme.
- Der alte Gesamtlauf `recordings/profile_testb_fx.jsonl` (FX1 + FX2 gleichzeitig)
  ist in `docs/research/PROFILING-INIT-2026-11-21.md` noch enthalten; für FX-Fragen gilt
  die getrennte Messung in diesem Dokument.

## 4. A4 — Unisono Count/Detune

**Status: Code-Fix fertig, Geräte-Readback bestätigt; Breiten-Metrik gemessen
(2026-11-21).**

`profile_testb_sweep.py unison` (kurzes Amp-Release 0, Count 0x40 = 5 Stimmen):

| Parameter | Werte | Klassifikator | Ursache |
|---|---|---|---|
| Allocation/Unisono | 0, 32, 64, 127 | n/a | Count allein erzeugt bei Detune 0 kaum Spektraländerung |
| Unisono Detune | 0, 32, 64, 127 | n/a | Baseline-Rauschen 2,21/1,06 → Schwelle 5,53 |

Der Klassifikator ist für Unisono ungeeignet, weil die Schwebung die
Hüllkurve/Phase stark streut. Eine **offline Spektralbreite um den Grundton**
(C4, ±30 Hz) zeigt dagegen die erwartete monotone Reaktion:

| Detune raw | Blofeld Bandbreite | Iridium Bandbreite |
|---|---|---|
| 0 | 1,21 Hz | 1,15 Hz |
| 32 | 3,12 Hz | 1,32 Hz |
| 64 | 6,14 Hz | 3,13 Hz |
| 127 | 11,39 Hz | 10,18 Hz |

Geräte-Readback nach dem Lauf: `UnisonoCount = 4` (5 Stimmen),
`UnisonoDetune = 1.0`, `UnisonoPan = 0.5`, `UnisonoDelay = 0.0` — der Fix kommt
also am Gerät an.

**Zu tun:**

- [x] Mit `scripts/profile_todo_measure.py unison_detune` die Spektralbreite
      (2 Takes, ≥ 3 s) messen.
- [x] Mit `scripts/profile_todo_measure.py unison_count` Count 0/2/4/8 Stimmen
      bei Detune 127 separat prüfen.
- [x] Ergebnis in `FIXES_HISTORY.md` als verifiziert eintragen.

**Ergebnis (2026-11-21, 5 Stimmen, C4, ±55 Hz):**

| Detune | Blofeld | Iridium | Δ Blofeld | Δ Iridium |
|---:|---:|---:|---:|---:|
| 0 | 1,50 Hz | 1,47 Hz | – | – |
| 32 | 3,67 Hz | 1,56 Hz | +2,17 | +0,09 |
| 64 | 6,95 Hz | 3,19 Hz | +5,45 | +1,72 |
| 127 | 13,89 Hz | 11,51 Hz | +12,39 | +10,04 |

Count (Detune 127) bei 0/2/4/8 Stimmen: Blofeld 1,42 → 9,48 / 10,77 / 11,94 Hz,
Iridium 1,41 → 10,52 / 11,63 / 11,19 Hz. **Unisono greift auf beiden Seiten und
die Breite passt bei maximalem Detune; die Iridium-Kennlinie ist bei kleinen
Detune-Werten deutlich komprimiert.** Die Breiten-Metrik kann 2/4/8 Stimmen
nicht trennen (die Gesamtspreizung ist bei festem Detune ähnlich) — für die
Stimmenzahl ist der Geräte-Readback (`UnisonoCount`) die belastbare Quelle.

## 5. A7 — LFO Free-Speed und Fade

**Status: Free-Speed und Fade gemessen (2026-11-22); beide Mappings weichen ab.**

`LfoNAttack`/`LfoNDecay` werden jetzt aus dem bipolaren Blofeld-Fade gesetzt
(Test `test_lfo_fade_maps_to_attack_decay`). Die Zeit-Skalierung ist linear
angenähert.

**Zu tun:**

- [x] Fade-Sweep am Gerät (positiv/negativ) und Zeitkonstanten vergleichen.
- [x] Free-Speed-Hz-Kurve mit 7 Stützstellen messen (langsame LFOs zuerst).
- [x] Speed-Sweep (7 Werte) fahren.
- [ ] `LfoNSpeed` anhand der gemessenen Kurve kalibrieren (Fix-Session).
- [ ] `LfoNAttack/Decay` neu aufsetzen (Fix-Session, siehe unten).

**Free-Speed (`scripts/profile_lfo_measure.py speed`):**

| raw | Blofeld | Iridium | Verhältnis |
|---:|---:|---:|---:|
| 20 | 0,45 Hz | 0,11 Hz | 0,24 |
| 30 | 1,11 Hz | 0,35 Hz | 0,32 |
| 40 | 2,63 Hz | 1,09 Hz | 0,42 |
| 50 | 5,48 Hz | 2,56 Hz | 0,47 |
| 60 | 10,43 Hz | 5,66 Hz | 0,54 |
| 70 | 17,06 Hz | 10,32 Hz | 0,60 |
| 80 | 30,65 Hz | 16,32 Hz | 0,53 |

(Frequenz aus der RMS-Hüllkurve; die langsamsten Werte sind wegen < 2 Perioden
unsicher.) Der Konverter mappt `LfoNSpeed = norm(raw)` linear → der Iridium ist
bei mittleren/hohen Speeds **2–4× zu langsam**. Es braucht eine Hz-Kalibrierung.

**Fade (`scripts/profile_lfo_measure.py fade`):** Der Blofeld-Fade ist eine
**Rate** (größerer Betrag = schneller), positiv = Fade-in, negativ = Fade-out
nach `Delay`. Gemessene Halbzeiten: +48 (raw 112) 1,4 s; −48 (raw 16) 1,0 s;
−24 (raw 40) 2,0 s; +16/+32 (raw 80/96) > 6,5 s. Der Iridium zeigt mit den
konvertierten `Lfo1Attack/Decay`-Werten **keine messbare Ein-/Ausblendung**
(Tiefe ab Note-On konstant) — auch bei `Lfo1Attack=1.0` in allen
`Lfo1Global`-Modi. Das lineare `(raw−64)/63`-Mapping ist damit nicht nur zu
grob, sondern in der Richtung falsch.

## 6. Block 5 — Glide/Legato

**Status: gemessen (2026-11-21), Details in `docs/research/GLIDE-2026-11-21.md`.**

Setup: Blofeld Allocation = Mono + Portamento, Iridium Onset, C3 → C5, trocken.

- **Glide on/off** funktioniert: aus = beide springen auf C5, ein = beide
  gleiten (Rate 64: Blofeld 592 ms / Iridium 256 ms).
- **Portamento @ Rate 50: OK** (155 / 144 ms).
- **Rate-Kurve weicht ab:** Blofeld raw 50/64/70/85 = 155/592/1013/2117 ms;
  Iridium `GlideRate` 0,30/0,50/0,75/1,00 = 139/379/896/1600 ms. Der Konverter
  mappt raw 70 auf 0,419 (315 ms, 0,31×) und raw 85 auf 0,50 (384 ms, 0,18×).
  Empfehlung: 50→0,32, 64→0,59, 70→0,79, ab 85→1,0.
- **Modi:** Glissando und fingered G erzeugen auf dem Blofeld Halbtonschritte
  (6 bzw. 14 Plateaus), der Iridium gleitet durchgehend (0). Staccato-fingered:
  Blofeld gleitet nicht, Iridium (Onset) gleitet. Ursache: Glide-Modus und
  Mono-Allocation werden nicht gemappt; der Iridium hat keinen Mono-Modus.
- **Grenze:** Iridium maximal ~1,6 s Glide; Blofeld bis ~5 s.

**Offen (Fix-Session):** Rate-Kurve und `GlideType`; siehe `TODO_FIX.md`.

## 7. Messhygiene / offene Punkte

- [x] Vor jedem Lauf `FX1Type = Off` bzw. `FX2Type = Off` explizit setzen, wenn
      der jeweilige FX nicht Gegenstand der Messung ist. Der neue Runner macht
      das pro Gruppe (FX1-Messung: nur FX2 aus; Reverb: nur FX1 aus).
- [ ] Baseline-Rauschen < 1,5 anstreben (C5); bei längeren Releases Takes
      entzerren oder Release verkürzen.
- [ ] Die alten Rohdaten liegen unter
      `recordings/profile/pre_fix_2026-11-21/`; die neuen A1-Läufe unter
      `recordings/profile_testb_osc2.jsonl`, die Unison-Läufe unter
      `recordings/profile_testb_unison.jsonl` (der verrauschte Zwischenlauf als
      `recordings/profile/unison_high_noise_2026-11-21.jsonl`).
- [x] `fx`-Lauf war abgebrochen; die getrennten Läufe ersetzen ihn:
      `recordings/todo_measure_fx1types.jsonl` und
      `recordings/todo_measure_reverb.jsonl`.

**Neu gelernt (2026-11-21):**

- Der Blofeld-LFO hat `Fade = 0` als **−64** (sofort ausblenden). Für
  PWM-/LFO-Messungen muss `Fade = 64` (Neutralstellung) gesetzt werden, sonst
  misst man einen stummen LFO und schreibt die Wirkung fälschlich nur dem
  Iridium zu.
- Der Iridium übernimmt FX-Änderungen gelegentlich verzögert; nach
  `init-patch` 0,6 s warten und den FX-Zustand per Readback bestätigen
  (`profile_todo_measure.py` macht das).
- Die ADC-Aufnahme ist je nach Länge ~0,3–0,6 s kürzer als angefordert; bei
  Tail-Messungen die Fenster entsprechend legen (Note-Off bei 2,7 s, Tail ab
  3,0 s).

## 8. RF100 v3 — Re-Conversion, SD, Messung, Retraining

**Status: Konvertierung fertig, Messung/Retraining vorbereitet (2026-11-21).**

- `transfer/rf100_v3/` enthält 100 qpats (A001–A100) mit aktuellem Mapping
  (141–220 gemappt, Mittel 170,3), SD-Ordner `rf300`, Slots 300–399;
  `MANIFEST.json`/`MANIFEST.md` liegen daneben.
- Runner: `scripts/measure_rf100.py` (dry-run ohne `--run`, `--verify-sd`
  read-only). Log-Ziel: `recordings/sim_log_v3.jsonl`.
- Trainingsvorbereitung: `scripts/reconvert_rf.py` + `prognose train`; siehe
  `docs/research/MEASURE-RF100-V3.md`.

**Zu tun:**

- [x] `transfer/rf100_v3` als `rf300/` auf die SD-Karte kopieren.
      (2026-11-22: `/Volumes/NO NAME/rf300`, 102 Dateien; Karte steckt im
      Iridium, Slots 200–299.)
- [x] `measure_rf100.py --verify-sd` → 100/100 (2026-11-22; prüft Name **und**
      Byte-Größe, weil v2/v3 dieselben Dateinamen haben).
      **Hinweis:** `ls` blockiert den Device-Readout für einige Zeit → Verify in
      eigener Sitzung, Messlauf mit `--skip-verify`.
- [x] `measure_rf100.py --run --skip-verify` (100 Locs × Notes 72/60) —
  **erster Lauf 2026-11-22 ungültig:** `load-patch <PFAD>` ist ein stiller
  No-op, der Iridium-Edit-Buffer blieb gleich (Readback-Beweis). Log verworfen
  (`recordings/sim_log_v3_invalid_loadpath.jsonl`), Modell auf v2 zurück.
- [x] **Neuer Lauf mit Slot-Load + Readback-Verifikation** (2026-11-22):
  200 Zeilen, 197 gescort, **mean 66,9** (v2 51,1 auf denselben Sounds),
  73/99 besser, Bestwert 96,3; 3 stumm (A050 ×2, A097 note72).
- [x] Entropy: H(y)=2,93 bits. Retrain: MAE 9,32, R² −0,013 / R²_cv 0,075 →
  **nicht geshippt**, `models/prognose_rf.pkl` bleibt v2.
- [x] A12 (DigiFormerAmount) mit Slot-Load gemessen (2026-11-22): globaler
      Skalar 0,65 bringt im Mittel +0,7 (11 besser / 10 schlechter) → keine
      pauschale Korrektur. Offen bleibt eine Hz-Kalibrierung pro Former-Modell
      (`TODO_FIX.md`).
- [x] Schwache Fälle: Ursache war der Template-Semitone-Leak (Osc 3 eine
      Oktave zu tief, Fix in 0.6.1). v4: A020 32->62, A023 44->52, A024 39->65.
- [x] v4-Lauf (Slots 200–299): 196/200 gescort, **mean 70,7** (v3 67,0,
      v2 51,1), +3,8 gegen v3 (53 besser / 28 schlechter). Retrain auf v4:
      R² −0,234 / R²_cv 0,070 → **nicht geshippt**, Modell bleibt v2.
- [ ] Hüllkurven-Zeiten kalibrieren (Decay/Attack); A014/A026/A052/A070/A072
      waren zeitweise stumm, weil das Messfenster den kurzen Iridium-Decay
      verpasst (Amp-Sustain 0, Pre-Roll 0,35 s). A072 zusätzlich Attack 0,72.
- [ ] Ausreißer v4 prüfen: A015 68→49, A003 88→70, A061 59→48.

**Hinweis:** `measure_rf100.py --verify-sd` prüft jetzt auch ohne `--run`
(read-only); vorher kehrte das Skript vor der Prüfung zurück.

### Hüllkurven (2026-11-22)
- [x] Attack/Decay-Zeiten kalibriert (`ENVELOPE_TIME_ANCHORS`, 0.6.2); A/B
      A003/A016 je +4,7.
- [ ] Release-Zeiten messen (Note-Off-Erkennung zu unzuverlässig).
- [ ] Messprotokoll für Sustain-0-Patches: Aufnahme ab Note-On, sonst bleiben
      A014/A026/A070 stumm.
- [ ] v5 auf SD `rf500`/Slots 300–399 laden und vollständig messen.

### v5-Lauf (2026-11-22, erledigt)
- [x] 100 Sounds, Onset-Protokoll, Slots 200–299 → 79,5 im Mittel.
- [ ] Protokoll-Bias quantifizieren: 10 v5-Sounds zusätzlich mit dem alten
      Pre-Roll-Fenster messen (gleiche Patches) → sauberer v4↔v5-Delta.
- [ ] Release-Zeiten messen (Note-Off-Erkennung).

### Don Solaris Bank E (2026-11-22)
- [x] Bank E live vom Blofeld gedumpt (128 Sounds, `dumps/banks/E`).
- [x] SD-Upload verifiziert: E001-E100 in 200-299.
- [ ] Bank E mit 0.6.3 neu konvertieren, hochladen, messen (Onset-Protokoll).
- [ ] Prognose-Modell mit Bank E zusammen neu trainieren (v2 vs. kombiniert).

### Bank E / Prognose (2026-11-22, erledigt)
- [x] Bank E gemessen (100 Sounds, 0.6.4): Mittel 68,2, keine stummen Sounds.
- [x] Modell-Gegenprobe über Bänke: kein Transfer (R² < 0).
- [ ] Entscheiden: Prognose in der Webapp als "experimentell" kennzeichnen oder
      ganz entfernen (aktuell sagt v2 auf neuen Daten 27 Punkte zu niedrig).
- [ ] Optional: Wiederholbarkeit messen (8 Sounds doppelt) als Obergrenze für R².

### Filter-Env-Amount (0.6.5)
- [ ] Sauberer Skalentest: Test-Patch, nur Cutoff + Filter1EnvAmount sweepen,
      Spektralverlauf je Wert messen (monoton?). Bestätigt/kippt 0.6.5.
- [ ] `FilterNVeloAmount` / `AmpVeloAmount` prüfen (gleiche Bipolar-Frage).
- [ ] Nach Bestätigung: Bank E neu konvertieren (0.6.5) und erneut messen;
      dabei 2-3 Wiederholungen pro Ausreißer einplanen.
