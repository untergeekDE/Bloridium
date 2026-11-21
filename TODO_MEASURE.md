# TODO_MEASURE — offene Verifikation der Konverter-Fixes

**Stand:** 2026-11-21 · **Geräte:** Blofeld + Iridium Keyboard, beide über USB
(kein Launchpad) · **Audio:** Scarlett 18i8, 48 kHz, Blofeld In 3/4, Iridium In 5/6.

Die Code-Fixes A1, A3 und A4 sind umgesetzt und unit-getestet; Details in
`FIXES_HISTORY.md`. Diese Datei sammelt nur noch, was am Gerät nachgemessen bzw.
an der Messmethodik repariert werden muss.

**Runner:** `scripts/profile_todo_measure.py <group>` misst die offenen Gruppen
getrennt (`pulse_amt`, `pulse_src`, `fx1types`, `reverb`, `unison_detune`,
`unison_count`). `... report` schreibt die Zusammenfassung nach
`docs/TODO-MEASURE-2026-11-21.md`. Der Runner setzt für FX1-Messungen
`FX2Type = Off` und für Reverb `FX1Type = Off` — damit ist die alte
Reverb-Kontamination des FX-Sweeps beseitigt.

## 1. A1 — PWM-Zeile nur für pulsartige Shapes

**Status: negativer Fall gemessen (2026-11-21), bestanden.**

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

## 2. A3 — Reverb-Mix über `ReverbGain`

**Status: Code-Fix + Unit-Test fertig; Messung abgebrochen/kontaminiert.**

Der `fx`-Sweep läuft mit `FX1 = Chorus` **und** `FX2 = Reverb` gleichzeitig.
Dadurch wird jede Effect-1-Mix-/Chorus-Messung vom Reverb überlagert
(Baseline-Rauschen 2,04/1,02 → Schwelle 5,11; Effect 1 Mix durchgehend n/a).
Das ist ein **Fehler der Messanordnung**, nicht des Konverters: der Konverter
setzt mit dem neuen Fix `ReverbGain = norm(Effect 2 Mix)` (Handbuch: Gain ist
der Reverb-Dry/Wet-Regler), nicht mehr die alte Matrix-Zeile.

**Zu tun:**

- [ ] Mit `scripts/profile_todo_measure.py fx1types` FX1 allein messen
      (`FX2Type = Off`).
- [ ] Mit `scripts/profile_todo_measure.py reverb` FX2 allein messen
      (`FX1Type = Off`) und Effect 2 Mix 0/32/64/127 % auf monotone Hall-Zunahme
      prüfen (Status OK/teilweise, nicht defekt).
- [ ] Danach `profile_testb_sweep.py fx` nicht mehr als Gesamtlauf verwenden.
- [ ] Erst dann `FIXES_HISTORY.md` als „verifiziert“ markieren.

## 3. A4 — Unisono Count/Detune

**Status: Code-Fix fertig, Geräte-Readback bestätigt, Klassifikator noch zu grob.**

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

- [ ] Mit `scripts/profile_todo_measure.py unison_detune` die Spektralbreite
      (2 Takes, ≥ 3 s) messen.
- [ ] Mit `scripts/profile_todo_measure.py unison_count` Count 0/2/4/8 Stimmen
      bei Detune 127 separat prüfen.
- [ ] Ergebnis in `FIXES_HISTORY.md` als verifiziert eintragen.

## 4. Messhygiene / offene Punkte

- [ ] Vor jedem Lauf `FX1Type = Off` bzw. `FX2Type = Off` explizit setzen, wenn
      der jeweilige FX nicht Gegenstand der Messung ist.
- [ ] Baseline-Rauschen < 1,5 anstreben (C5); bei längeren Releases Takes
      entzerren oder Release verkürzen.
- [ ] Die alten Rohdaten liegen unter
      `recordings/profile/pre_fix_2026-11-21/`; die neuen A1-Läufe unter
      `recordings/profile_testb_osc2.jsonl`, die Unison-Läufe unter
      `recordings/profile_testb_unison.jsonl` (der verrauschte Zwischenlauf als
      `recordings/profile/unison_high_noise_2026-11-21.jsonl`).
- [ ] `fx`-Lauf war abgebrochen; `recordings/profile_testb_fx.jsonl` enthält nur
      die ersten Zeilen und muss nach der Aufteilung neu erzeugt werden.
