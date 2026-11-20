# RF v2 Retrain + Conversion-Erweiterung (Sync/Noise/LFO) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: executing-plans (nativ in dieser Session).
> Steps use checkbox (`- [ ]`) syntax.

**Goal:** Vorhandene Recordings mit Score v2 re-scoren, Embed/d1-Features berechnen und
per Entropie-Check prüfen, ob sie als RF-Feature taugen; Conversion um Sync/Noise/LFO
erweitern; A001–A100 neu konvertieren + auf SD; komplettes Neu-Recording (v2 + Embed + d1);
dann RF auf v2-Scores retrainieren und shippen.

**Architecture:** Offline-Rescore via `sim_embed.score_pair_embed` (liefert v2 automatisch,
`SCORE_VERSION=2`); Feature-Check als eigenes CLI (`prognose entropy`); Mapping-Änderungen
in `bloridium/qpat_map.py` (TDD); Re-Convert über `workflow.convert_parsed` in neues
`transfer/rf100_v2/` (SD-Ordner `rf200`); Live-Neu-Recording über `quir_rf_dataset.py measure`
(codesearch, lädt `2:rf200/...`, Slots 200–299 bleiben); Retrain via `prognose train`
(default `--min-score-version 2` pickt nur v2-Zeilen).

**Tech Stack:** Python 3.10, numpy only (kein sklearn — scipy broken), pickle-Models,
CLAP-GGUF + ollama (lfm3-omni/d1-omni) lokal, QUIR-Sysex für Iridium (codesearch-Repo).

**Spec:** User-Roadmap 2026-11-20 + `FIXES_TODO.md` Items 1–2 (🖥 Mac-Tasks) +
`docs/HANDOVER-2026-11-19-rf-dataset.md`.

## Global Constraints

- Nie v1- und v2-Scores mischen: `prognose train` default `--min-score-version 2`.
- rf-dataset-Audio von 11-19 wurde NICHT gespeichert → die 202 v1-Zeilen sind offline nicht
  re-scorbar; nur die 18 `ab_*`-Paare (9 Locs) haben Audio. Rest muss live neu gemessen werden.
- GELB (load-patch/save-patch) nur mit `--allow-write`; immer von `2:<sd>/...` laden, nie
  `load-patch <slot>` (1-MB-Sample-Slots sind stumm). SD-Namen ohne Spaces (MANIFEST sd_name).
- Messregeln (bloridium-Skill): nur Part 1 (ch6), CC123=0 + Blofeld CC7=127 vor jeder Messung
  (handled in quir_ab_sweep); Mess-Noise ±1–3 Punkte.
- Repo-Grenze: Sysex/QUIR nur in `bloridium-codesearch`; hier nur Ergebnisse/Code.
- dumps/, recordings/, transfer/, GGUFs gitignored; `models/prognose_rf*.pkl` getrackt.

## Review Focus

1. v2-Rescore darf alte v1-Zeilen nicht überschreiben → eigenes Log `sim_log_v2.jsonl`,
   alte `sim_log.jsonl` bleibt append-only.
2. Noise-Mapping darf einen belegten Osc NICHT überschreiben (nur freien Slot nutzen).
3. LFO-Shape-Enum-Mapping muss gegen echte OS4-Enum-Werte gecheckt werden (param-info),
   nicht erraten.
4. Neue qpats müssen MANIFEST-sichere Namen haben und per `verify-sd` prüfbar sein, BEVOR
   das Live-Recording startet.
5. Retrain-Vergleich alt vs. neu muss ehrlich sein (n, MAE, RMSE, R², R²_cv) und R²<0-Warnung
   ernst genommen werden (FIXES_TODO Item 2).

---

### Task 1: Offline v2-Rescore der vorhandenen ab_*-Paare + Embed/d1

**Files:**
- Create: `scripts/rescore_v2.py`
- Create: `tests/test_rescore_v2.py`
- Output: `recordings/sim_log_v2.jsonl`

**Interfaces:**
- `discover_pairs(rec_dir) -> list[(loc, note|None, path_a, path_b)]` — parst `ab_<LOC>_<ts>[_nXX][_wNN]_(blofeld|iridium).npy` und `_blo/_irr.wav`
- `main()`: pro Paar `np.load` → mono → `sim_embed.score_pair_embed(..., clap=..., ollama=...,
  use_llm=True, profile_backend=d1, norm_pegel=True, log_path=recordings/sim_log_v2.jsonl,
  meta={"mode": "npy-v2", "blofeld": loc, "note": note, "src": basename})`
- CLI: `--rec-dir`, `--log`, `--no-embed`, `--no-llm`, `--no-d1`, `--models-dir`, `--limit`

- [x] Step 1: Test für `discover_pairs` (tmp dir mit synthetischen Dateinamen, npy/wav-Mix, unvollständige Paare werden ignoriert, loc/note geparst)
- [x] Step 2: Test läuft rot
- [x] Step 3: `scripts/rescore_v2.py` implementieren (Backends einmal bauen, dann alle Paare)
- [x] Step 4: Tests grün; echter Lauf: 45 Paare → `recordings/sim_log_v2.jsonl`, jede Zeile mit `score_version: 2`, `embed_score`, `llm`, `profile`
- [x] Step 5: Commit `94930b3`

### Task 2: Entropie-/Feature-Check (`prognose entropy`)

**Files:**
- Modify: `bloridium/prognose.py` (neue Funktion `entropy_report(log_path, target="score", min_score_version=2) -> dict`)
- Modify: `bloridium/cli.py` (`prognose entropy` Subcommand)
- Modify: `tests/test_prognose.py`

**Interfaces:**
- `entropy_report(...)`: pro Loc Label = Mittel über `result[target]`; Kandidaten-Features
  pro Zeile: `embed_score`, `llm.score`, `profile.score` (falls vorhanden), `spec_mad_db`,
  `env_dtw`. Ausgabe: H(y) (bits, 10 Bins), pro Feature Information Gain IG = H(y) − H(y|f)
  (gleiche Bins) + Pearson/Spearman r. JSON-Report + Print.
- CLI: `bloridium prognose entropy --log recordings/sim_log_v2.jsonl [--target score] [--bins 10]`

- [x] Step 1: Tests: synthetisches Log (+ partielle IG) mit 2 Locs, perfekter Prädiktor-Feature (IG = H(y)) und nutzlosem Feature (IG ≈ 0)
- [x] Step 2: rot
- [x] Step 3: implementieren (inkl. partieller IG gegen spec_mad_db)
- [x] Step 4: grün + Lauf auf sim_log_v2.jsonl auf `sim_log_v2.jsonl` (9 Locs) → Report in `docs/FINDINGS.md` anhängen
- [x] Step 5: Commit

### Task 3: qpat_map — Sync / Noise / LFO ergänzen (TDD)

**Files:**
- Modify: `bloridium/qpat_map.py`
- Modify: `tests/test_qpat_map.py` (bestehend? prüfen)

**Interfaces:** `blofeld_to_qpat_params(parsed) -> (overrides, unmapped)` — Signatur bleibt.

- [x] Step 1: Enum aus 1186 Factory-qpats: Sine0 Tri1 Sqr2 SawDown3 SawUp4 SH5: Blofeld LFO-Shapes aus allen 102 Dumps sammeln; Iridium
  `LfoNShape`-Enum aus codesearch `recordings/quir_param_info_enums2.txt` / OS4-Export
- [x] Step 2: Tests: synthetisches SNDD (via `blofeld_dump.build_sndd`) mit Noise Level>0 +
  Osc3=Off → erwartet `Osc3Type`=Waveform, `Osc3WaveformShape`=White/Pink (Colour), `Osc3Vol`,
  `Osc3Pan` bipolar; Noise mit allen 3 Oscs belegt → bleibt unmapped, kein Override eines
  belegten Osc; LFO Shape=Saw → `Lfo1Shape` enum; LFO Start Phase → `Lfo1Phase`; LFO Delay →
  `Lfo1Delay`; Sync-Shapes (SawSync…) landen in `BLOFELD_WAVETABLE_TO_IRIDIUM` falls fehlend
- [x] Step 3: rot
- [x] Step 4: implementieren (Noise nur auf freiem Osc-Slot, bevorzugt Osc3 dann Osc2 dann
  Osc1; Colour raw<64→Pink, ≥64→White; Balance (raw−64)/64→Pan 0..1; Level→OscNVol)
- [x] Step 5: grün (49 Tests) + 102-Dump-Scan: LFO Shape/Phase/Delay + Noise (A065) gemappt, Rest dokumentiert unmapped: unmapped-Anteil für sync/noise/lfo-Kategorien
  auf 0 (abgesehen von dokumentiert unmapped: LFO Fade/Keytrack, Noise bei vollem Mixer)
- [x] Step 6: Commit `4919c18`

### Task 4: A001–A100 neu konvertieren → transfer/rf100_v2 + MANIFEST (SD `rf200`)

**Files:**
- Create: `scripts/reconvert_rf.py` (oder `quir_rf_dataset.py prepare` mit neuem Out-Dir —
  CLI checken, bevorzugt wiederverwenden)
- Output: `transfer/rf100_v2/<LOC>_<Name>.qpat` + `MANIFEST.json` (sd_dirname `rf200`)

- [x] Step 1: 100 qpats in transfer/rf100_v2, alle roundtrip-parsebar, sd_names ok aus den 100 rf-Dumps mit neuem Mapping; jeder qpat roundtrip-parsebar,
  Namen ohne Spaces, MANIFEST-Einträge mit `sd_name`
- [x] Step 2: Diff = nur neue LFO/Noise-Keys: Diff-Statistik (welche Keys kamen neu dazu) in Log
- [x] Step 3: Commit `5012b9a`/`9d1e634` + push; SD-Kopie erledigt (plain cp, Namen per Konversion SD-sicher) `transfer/rf100_v2/*` auf SD-Karte als `rf200/` kopieren

### Task 5: verify-sd + Live-Neu-Recording (v2 + embed + d1) — Hintergrund

**Files:** codesearch `tools/quir_rf_dataset.py` (verify-sd/measure), neue Config
`recordings/quir_rf_dataset_config_v2.json` (remote `2:rf200/...`, slots 200–299)

- [x] Step 1: `verify-sd` 100/100 auf `2:rf200` (nach Iridium-Reboot — QUIR war nach SD-Wechsel tot, Reboot hat geholfen) (nach SD-Kopie) grün — sonst STOP vor Recording
- [~] Step 2: `measure` läuft (Hintergrund rf_v2_measure.log): alle 100 × notes 72,60, v2 + --embed --norm-pegel; danach 24-Loc-Subset mit --llm --profile (d1) (notes 72,60) mit `--allow-write`, Scoring v2
  (automatisch), `--embed` für alle, `--llm --profile` (d1) auf Subset (5 Outlier + ~25
  Zufall) wegen Laufzeit; Zeilen in `recordings/sim_log.jsonl` mit `score_version: 2`
- [ ] Step 3: Nach Lauf: quick entropy-report auf den neuen v2-Zeilen

### Task 6: Retrain + Ship

**Files:**
- Modify: `bloridium/prognose.py` + `cli.py` — optional `--extra-features embed_score,...`
  (nur wenn Task 2/5 zeigt, dass Embed die Entropie senkt; Features aus Log pro Loc mitteln,
  an SNDD-Features anhängen)
- Modify: `FIXES_TODO.md` (Items 1–2 abhaken), `docs/HANDOVER-2026-11-19-rf-dataset.md` (Update)
- Output: `models/prognose_rf.pkl` (v2, ersetzt v1 nach Vergleich; alt als `prognose_rf_v1.pkl`
  behalten — Pattern `prognose_rf*.pkl` ist getrackt)

- [ ] Step 1: `prognose train --log recordings/sim_log.jsonl --target score` (v2-Default) →
  neue Metriken vs. alt (n=99 MAE 1.29 R²<0) loggen
- [ ] Step 2: Entscheidung Extra-Features anhand entropy-report; ggf. retrain mit
  `--extra-features`
- [ ] Step 3: Modell speichern, `predict_loc` Smoke-Test auf A091/A043
- [ ] Step 4: Doku aktualisieren, Tests gesamt grün, commit + push (Bloridium + codesearch)
