# TODO_FIX — Konverter- und Mess-Backlog aus dem Init-Profiling

**Stand:** 2026-11-21 · **Quellen:** `docs/PROFILING-INIT-2026-11-21.md`,
`docs/ARCHITEKTUR-DIFFERENZEN.md`, `docs/profiling_init_2026-11-21.csv`

Diese Liste ist der *messbasierte* Backlog (121 Parameter, 752 Einzelmessungen).
Die allgemeine Code-Review-Liste ist `FIXES_HISTORY.md`.

Legende: **P0** = belegter Fehler, hoher Klangimpact · **P1** = wichtig, aber
eingegrenzt · **P2** = Doku/Komfort · ✅ erledigt

Jeder Punkt nennt Beleg → Stelle → Fix → Akzeptanz. Wo „Neumessung“ steht, ist der
bestehende Sweep erneut zu fahren (`scripts/profile_testb_sweep.py <mode>`).

---

## 0. Aktueller Fokus: offene Messungen

Die Umsetzung/Reparatur des Konverters war an eine **andere Session** übergeben.
Die Punkte A1–A10 waren daher **zurückgestellt** (nicht vergessen); A8 und A11 wurden
noch vor dieser Umstellung umgesetzt.

**Nachtrag 2026-11-21 (Umsetzungs-Session):** A1, A2, A3 und A4 sind ebenfalls
umgesetzt (Code + Unit-Tests, Suite 407 passed). Alle umgesetzten Punkte (A1, A2,
A3, A4, A8, A11) stehen jetzt mit Beleg und Test in `FIXES_HISTORY.md` und sind aus
dieser Liste entfernt. Offen bleibt nur die jeweilige **Neumessung** am Gerät.

Nächste Messblöcke (Reihenfolge):

0. **Verifikation A1/A2/A3/A4** — PWM (`osc2`), Filter 2 (`f2`), Reverb-Mix (`fx`),
   Unisono (`unison`); Details und Akzeptanz in `FIXES_HISTORY.md`/`TODO_MEASURE.md`.
1. **5 · Glide/Legato** — Zwei-Noten-Recorder; Rate/Mode 0/1, 20/60/100.
2. **6 · Unisono** — Count 2/4/8, Detune, Pan (A4-Befund absichern).
3. **7 · Sync** — nur Osc 2+3, Intervall +7, Sync aus/ein.
4. **8 · FX pro Typ** — Chorus/Flanger/Phaser/Delay/Reverb, je 100 % wet.

Messhygiene: verifizierter Dump-Load (C1), 2 Takes je Wert, L/R bei Pan, Notenpaare
bei Keytrack, Anschlagspaare bei Velocity.

## A. Konverter-Fixes mit Messbeleg

### A5 · P1 · FX-Parameter-Indizes und Skalen
- **Beleg:** Chorus-Test (100 % wet): Parameter 5 bei 64/127 **Iridium 5–11×**
  zu stark, Parameter 1/2 nur teilweise (cos 0,53–0,67). Parameter 3/4 sind beim
  Blofeld-Chorus ohne Wirkung (n/a).
- **Stelle:** `FX_PARAM_MAP` (ca. Zeile 796–800), `FX_MIX_KEY`.
- **Fix:** pro FX-Typ die Parameter-Zuordnung und Skala prüfen (Speed/Depth/Feedback),
  insbesondere p5 nur bei Flanger/Phaser/Drive belegen; für Chorus keine p5-Zeile.
- **Akzeptanz:** Sweep `fx1` liefert für die belegten Parameter cos ≥ 0,8 und
  Stärke 0,5–2,0.

### A6 · P1 · Amp-Hüllkurve Attack/Sustain zu stark
- **Beleg:** „Amplifier Envelope Attack“ teilweise (1,67×), „Sustain“ teilweise
  (1,99×), Cosinus 0,66–0,80. Release dagegen OK (0,64×, cos 0,88).
- **Stelle:** `qpat_map.py`, Amp-Env-Block; Iridium-Kurven (`AmpEnvAttackCurve`,
  `AmpEnvDecayCurve` = Lin) vs. Blofeld-Zeitkonstanten.
- **Fix:** Zeit-/Pegel-Skalierung der Hüllkurven gegen die gemessenen Punkte
  nachziehen (Attack/Decay/Sustain getrennt), Kurvenform dokumentieren.
- **Akzeptanz:** Attack/Sustain cos ≥ 0,85 und Stärke 0,7–1,4.

### A7 · 🟡 Fade umgesetzt (2026-11-21), Free-Speed offen · LFO: Fade abbilden, Free-Speed kalibrieren
- **Beleg:** „LFO 1 Fade“ = **defekt** (Blofeld 2,6–2,9; Iridium 0,1–0,3).
  „LFO 1 Speed“: langsame Werte ohne Iridium-Wirkung, schnelle nur teilweise
  (cos 0,65). Der Iridium hat `LfoNAttack`/`LfoNDecay` — die werden nicht genutzt.
- **Stelle:** `qpat_map.py`, LFO-Block.
- **Fix:** Blofeld-Fade → `LfoNAttack` (Fade-in) bzw. `LfoNDecay` (Fade-out);
  Free-Speed-Hz-Kurve mit 6–8 Stützstellen kalibrieren (langsame LFOs zuerst).
- **Akzeptanz:** Fade-Sweep OK/teilweise; Speed-Sweep über 4 Werte cos ≥ 0,8.
- **Stand:** Fade-Mapping umgesetzt: raw>64 → `LfoNAttack=(raw−64)/63`,
  raw<64 → `LfoNDecay=(64−raw)/64`, 64 → beide 0. Keytrack bleibt unmapped.
  Test: `test_lfo_fade_maps_to_attack_decay`. Die Zeit-Skalierung ist linear
  angenähert; Free-Speed-Kalibrierung braucht weiterhin eine Messung.

### A9 · P1 · Noise: Kennlinie und Farbe
- **Beleg:** „Mixer Noise Level“ in der Tendenz richtig (cos 0,77–0,93), aber
  abweichende Kennlinie; „Noise Colour“ = **defekt** (nur Pink ≤ 64 / White > 64).
- **Stelle:** `qpat_map.py`, Noise→freier-Osc-Block (ca. 471–497).
- **Fix:** Level-Kennlinie gegen die Messpunkte prüfen (evtl. nichtlinear);
  Farbe bei Zwischenwerten über einen Tiefpass (Cutoff als Funktion von Colour)
  annähern oder im Report klar als 2-Stufen-Grenze ausweisen.
- **Akzeptanz:** Level-Sweep cos ≥ 0,85; Colour dokumentiert, bei ≤ 40 / ≥ 88
  eindeutig Pink/White.

### A10 · P2 · Amp/Hüllkurven: ADS1DS2R und Attack-Level
- **Beleg:** Blofeld-Modi ADS1DS2R/OneShot/Loop werden auf ADSR reduziert.
- **Stelle:** Envelope-Block.
- **Fix:** zweite Decay/Sustain-Stufe als dokumentierte Näherung behandeln
  (oder über eine zweite Iridium-Hüllkurve + Matrix abbilden); Attack-Level
  über die erste Stufe annähern.
- **Akzeptanz:** Entscheidung dokumentiert, Test-Sound mit ADS1DS2R konvertiert.

---

## B. Mapping-Lücken (Iridium-Parameter vorhanden, ungenutzt)

| # | Blofeld | Iridium-Parameter | Aufwand |
|---|---|---|---|
| B1 · P1 | Ringmod O1×O3 | `RingModOsc1ToOsc3` | klein |
| B2 · P1 | Glide Mode | `GlideType` | klein |
| B3 · P2 | Unisono Pan/Detune-Delay | `UnisonoPan`, `UnisonoDelay` | klein |
| B4 · P2 | Osc Bend Range / Keytrack | `OscNPitchBendRange`, `OscNKeytrack` | klein |
| B5 · P2 | Filter-Modelle | `Filter1Model`, `Filter2Model` (Svf/Ladder/…) | mittel |
| B6 · P2 | Arpeggiator-Basis | `ArpOn`, `ArpStepLength`, `ArpGate`, `ArpSortOrder` | groß |
| B7 · P2 | LFO Keytrack | Matrix `Keytrack → LFO Speed` | klein |
| B8 · P2 | Noise-Farbe stufenlos | Filter-Cutoff/Typ oder Particle-Dirt | mittel |

Jeweils: Mapping + Unit-Test + ein Sweep-Lauf; Akzeptanz = Status OK/teilweise im
Profiling-Report, kein `unmapped`-Eintrag mehr.

---

## Vorschlag Reihenfolge

1. **A2** + Neumessung `f2`.
2. **A6, A7, A9** — Kennlinien/Kalibrierung.
3. **A5, A10**.
4. **B1–B8** und **D/E** parallel.
5. Verifikation A1/A3/A4 gemäß `TODO_MEASURE.md` (Code ist fertig).

# Sonstige Fixes

Check whether these have been done already. 

## Webapp / container
   - ⬜ `load_core()` could now shrink to plain imports. It stays for now because it serves
     the flat `/app/core` container layout.

## Codebase

12. ⬜ **No CI and no lint/type config.** Add a GitHub Actions job (ubuntu, Python 3.12,
    `pip install -e .[dev]`, pytest) once item 11 makes the suite pass without private
    data. Add Ruff and, optionally, mypy.
    14. ⬜ **`scripts/` ignore `bloridium.yaml`.** Wire them to `config.load_config()`, or
    retire the scripts the CLI covers.
15. ⬜ **macOS-only MIDI 2.0 path.** `tools/ump_send` is CoreMIDI Objective-C, and the
    compiled Mach-O binary is tracked. Build it in a setup step instead, and document
    Linux/Windows limitations.
        - ⬜ Move the `scripts/spike_*` and `step2_probe_*` into `scripts/archive/`.

    18. ⬜ **`cli.py` is 1,000+ lines.** Split it into `cli/` per command group.
    19.     - ⬜ `_dtw` is still a pure-Python double loop; vectorise it or use a banded DTW.
16. - ⬜ **_MAD_SCALE (20 dB)** gegen User-Ratings kalibrieren (bestehender Punkt aus Item 1).