# Design: sim_checkpoint.py – Checkpoint-Messrunde (9 Presets × 4 Noten × Wheel 0/50/100 %)

Datum: 2026-11-17 · Status: genehmigt durch Benutzer 2026-11-17 (Noten 36/48/60/72 bestätigt, Pfad A gewählt)

## Intent & Why

Der naechste Checkpoint soll nicht mehr nur Note 72 bei Wheel 0 messen, sondern das
Oktav- und Mod-Verhalten systematisch abdecken: **4 Noten ueber 4 Oktaven
(Default 36, 48, 60, 72 = C2–C5, eine pro Oktave) × Wheel 0/50/100 %** fuer alle 9
konvertierten Presets. Bekannte Befunde, die das motivieren: tiefe Noten zeigen
gerade die env_dtw-Abweichung (Skill-Regel), A008 hat Oktav-Verdacht (d1 octave_lower
nur p=0.50), Wheel-Divergenz lokalisiert Mod-Defizite (A010 embed 75.7→37.9 bei 100 %).
Iridium-PC-Umschaltung ist defekt (HANDOVER-2026-11-14) → Manual-Panel-Modus: der
Mensch dreht pro Preset am Iridium auf Set 6 PC lt. DEFAULT_MAP, das Skript spielt
nur Noten und setzt Wheel.

## Goals / Non-goals / Anti-goals

- Goals:
  - Neues `scripts/sim_checkpoint.py`: ein Durchlauf = alle 9 Presets aus
    `DEFAULT_MAP` (sim_sweep_pcs), je Preset 4 Noten × 3 Wheel-Stufen = 12 Messungen
    (108 gesamt), Defaults `--notes 36,48,60,72 --wheel 0,50,100 --dur 2.0`.
  - Pro Kombination: ein JSONL-Eintrag in `recordings/sim_log.jsonl` mit
    `meta = {"mode": "checkpoint", "blofeld": loc, "blofeld_pc", "irr_pc", "bank": 6,
    "note": note, "wheel_pct": pct}` + Ergebnis von `sim_embed.score_pair_embed`
    (Phase A + embed + combined; llm/profile nur an Referenz-Kombination, s. u.).
  - WAVs pegel-angeglichen (Peak 0.5) wie in `sim_manual_compare.py`:
    `recordings/ab_<LOC>_<ts>_n<note>_w<pct>_{blo,irr}.wav`.
  - CLAP-Embed bei **allen** 108 Kombinationen; llm + d1-Profil nur bei
    Wheel 0 + Note 72 (Referenz-Oktave; 72 falls in --notes, sonst letzte Note),
    `----full-all` schaltet llm/profile auf alle Kombinationen.
  - Pro Preset Panel-Prompt (`input(...)`): „Bitte Set 6 PC<irr_pc> einstellen";
    `--no-wait` spart den Prompt (Tests/Non-interactive).
  - Wheel-Reihenfolge außen→innen (nur 3 CC1-Wechsel pro Preset), Reset CC1=0
    nach **jedem** Preset auf beiden Synths.
  - Summary am Ende: Pivot pro Preset — `A001 n36: w0=<combined> w50=… w100=…`.
  - Exit 0 wenn alle Messungen ok; stumme Aufnahme (score None) loggen + warnen +
    weiter, am Ende Exit 1.
- Non-goals:
  - Kein Iridium-PC-Senden (defekt, Workaround Panel).
  - Keine neuen Multi-Dimensions-Felder (sim_dims aus
    `docs/RESEARCH-2026-11-17-sim-multidim.md` ist eigener nächster Schritt) — der
    Checkpoint bleibt mit frueheren Runs vergleichbar (Phase A + embed + combined).
  - Kein Aenderung an `sim_manual_compare.py`/`sim_sweep_pcs.py` (die werden nur
    importiert).
- Anti-goals:
  - Kein Duplikat von `measure()`/`set_wheel()` — Import aus `sim_manual_compare`.
  - Checkpoint darf wegen einzelner stummer Messung nicht abbrechen.

## Constraints

- Python 3.10, macOS; numpy-only Kern; keine neuen Dependencies.
- Tests offline: MIDI/Audio/Backends/Input via monkeypatch (Muster
  `test_sim_manual_compare_wheel_sweep` in `tests/test_scripts.py`), kein Live-MIDI,
  keine Modell-Downloads. `time.sleep` im Test auf no-op patchen.
- Degrade-Regel von `score_pair_embed` gilt unveraendert (Backend fehlt → Felder
  `null` + `backend_error`, kein Crash).
- Eherne Regeln (Skill): nur Part 1 (Iridium ch6) triggern, monophon; CC123=0 alle
  16 Kanaele + CC7=127 nur am Blofeld vor jeder Messung (uebernommen aus
  `measure()`); Iridium-USB bleibt ab.
- Doku/Commit-Messages auf Deutsch; Tests: `python3 -m pytest tests/ -q`.

## Approaches

- **A (gewaehlt):** eigenes `scripts/sim_checkpoint.py`, das `measure`/`set_wheel`
  aus `sim_manual_compare.py` und `DEFAULT_MAP` aus `sim_sweep_pcs.py` importiert und
  die Preset-Schleife + Panel-Prompt + Summary kapselt. Trade-off: ein weiteres
  Skript — gerechtfertigt, weil Manual-Panel-Wechsel pro Preset ohnehin manuell
  passiert und ein Durchlauf konsistente Timestamps/Meta/Summary will.
- **B (abgelehnt):** nur Doku „pro Preset sim_manual_compare.py aufrufen“ — 9 manuelle
  Aufrufe mit Panel-Dreh als Fehlerquelle, keine Summary, inkonsistente ts.

## Design

- `scripts/sim_checkpoint.py`, `main(argv=None) -> int` (wie uebrige Skripte).
- Ablauf: Backends einmal bauen (`sim_embed.build_backends`, `build_profile_backend`);
  `midi.connect` beider Synths; pro Preset: Blofeld Bank A (CC0=0, CC32=0) + PC
  `int(loc[1:])-1`, Prompt `input()` (ausser `--no-wait`), dann
  `for pct in wheel_pcts: set_wheel(blo, irr, pct); for note in notes: measure(...)`.
  `full = args.full_all or (pct == wheel_pcts[0] and note == ref_note)`;
  `ref_note = 72 if 72 in notes else notes[-1]`.
- Messung/WAV/Log identisch zu `sim_manual_compare.main` (gleiche WAV-Namen, gleiches
  `norm_pegel`-Verhalten, `sim_embed.print_result` pro Kombination).
- Nach jedem Preset: `set_wheel(blo, irr, 0.0)`.
- Summary: `summary[(loc, note)][pct] = (score, embed_score, combined)`; Ende:
  pro Preset eine Zeile pro Note: `A001 n36: w0=84.2 w50=82.4 w100=61.0`.
- Exit: 1 falls mind. ein Ergebnis `score is None` (verdict „fehler“), sonst 0.
- Tests: neues `tests/test_sim_checkpoint.py` (FakeSynth/FakeRecord-Muster aus
  `test_scripts.py`): (1) `--only A001` Default-Noten/Wheel → 12 Log-Zeilen, Meta-Key-Menge
  exakt, CC1 ch4/ch5 == [0,64,127,0], 24 WAVs mit Namensmuster, rc 0, Summary enthaelt
  „A001“/„n36“; (2) alle 9 Presets → 108 Zeilen, `input` 9× gerufen, gefakte
  `score_pair_embed` zeichnet `use_llm` — nur wheel 0 + note 72 True (9×); (3) stumme
  Messung (score None) → Zeile geloggt, rc 1, Rest laeuft weiter; (4) `--no-wait` ruft
  `input` nicht auf; `--notes 60,72 --wheel 0` → 2 Zeilen/Preset.

## Was der Builder noch klären muss

- Nichts offen — alle Calls vom Benutzer genehmigt (Noten 36/48/60/72, Pfad A,
  dur 2.0, embed ueberall, llm/profile nur Referenz-Kombination).
