# prognose-rf (Random Forest: Blofeld-SNDD → erwartete Konvertiergüte) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `bloridium/prognose.py` + CLI `bloridium prognose train|predict`: Random Forest (sklearn, CPU, seed-fixiert) lernt aus SNDD-Parametervektor (367 Features) → gemitteltes sim-Target pro Location aus `sim_log.jsonl`; Modell-Bundle via joblib in `models/`; Prediction mit Unsicherheit (Std über Bäume). Trainingsdaten (reale Vergleiche) kommen von einer anderen Session – Code + Tests laufen jetzt schon offline mit synthetischen Daten.

**Architecture:** `prognose.py` kapselt Features/IO/Train/Predict; `cli.py` bekommt `prognose` mit Subkommandos `train`/`predict` (Muster wie `sim compare`). Datenvertrag: `sim_log.jsonl` (meta.blofeld + result[target]) + `dumps/blofeld_sndd_<LOC>_<ts>.bin`.

**Tech Stack:** Python 3.10; numpy; scikit-learn 1.5.1 + joblib 1.3.2 (installiert, nicht in pyproject-Kerndeps); pytest>=8.

**Spec:** `docs/research/superpowers/specs/2026-11-18-prognose-rf-design.md`

## Global Constraints

- sklearn/joblib bleiben optionale Env-Dependencies (nicht in `pyproject.dependencies`); Import von sklearn erst innerhalb der Prognose-Funktionen, damit Kern ohne sklearn läuft (Degrade: klarer Fehlerhinweis).
- Features: SDATA-Indizes 0–382 ohne Namens-Bytes 363–378 → 367 Features, /127 normalisiert. Namen via `blofeld_dump.SDATA`.
- Deterministisch: `random_state=seed` überall (RF + train_test_split).
- Tests offline: echtes A043-Dump aus `dumps/` + synthetische Dumps via `build_sndd` + synthetisches JSONL in tmp. Kein MIDI.
- Deutsch Doku/Commits. Tests: `python3 -m pytest tests/ -q`.

## Review Focus

1. **Namens-Bytes dürfen nicht in die Features** (363–378 ausgeschlossen). (Task 1, Test: Länge 367, Namen enthalten keinen Namen-Char-Eintrag)
2. **Aggregation pro Location** (Mittel über Target), keine Duplikate; fehler/stille/fehlende Dumps landen in `skipped`, nie still. (Task 1, Tests)
3. **Kleine n abfangen** (n<5: kein Holdout, nur Train-Metriken; CV nur bei n≥10). (Task 1, Test mit n=3)
4. **Modell-Persistenz** rundtrip (joblib) + `predict` nutzt gespeichertes Modell, nicht neu trainiertes. (Task 2, Test)
5. **CLI ohne Daten → klarer Fehler (Exit 2), nicht Crash.** (Task 2, Test)

---

### Task 1: `bloridium/prognose.py` – Kern (TDD)

**Files:**
- Create: `bloridium/prognose.py`
- Create: `tests/test_prognose.py`

**Interfaces (produziert):**
- `FEATURE_IDX: list[int]` (367), `param_names() -> list[str]` (parallel zu FEATURE_IDX)
- `feature_vector(parsed: dict) -> np.ndarray (367,)`
- `loc_from_header(data: bytes) -> str` ("A043"-Format aus bb/nn)
- `find_dump(dumps_dir, loc) -> Path` (neuester *.bin mit passendem Header)
- `load_training_rows(log_path, dumps_dir, target="combined") -> (X, y, locs, skipped)`
- `train_model(X, y, seed=42, n_estimators=200, test_size=0.25) -> dict` (Bundle: model, metrics{mae,rmse,r2,r2_cv}, importances top20, feature_names, target, n, seed)
- `save_model(bundle, path)`, `load_model(path) -> dict`
- `predict_loc(loc, dumps_dir, model_path) -> dict` (loc, predicted, std, model_name)

- [ ] **Step 1:** Tests in `tests/test_prognose.py`:
  - `test_feature_vector_real_dump`: `parse_sndd` auf `dumps/blofeld_sndd_A043_20261108_135516.bin` (skip wenn Datei fehlt) → Vector-Länge 367, Werte in [0,1]; `param_names()` Länge 367, enthält z. B. "Osc1 Pitch"-ähnlichen Eintrag; keine Namen-Indices (363–378) in FEATURE_IDX.
  - `test_loc_from_header_and_find_dump`: Header des A043-Dumps → "A043"; `find_dump(REPO/"dumps", "A043")` findet Datei; unbekannt "ZZZ9" → FileNotFoundError.
  - `test_load_training_rows_aggregates_and_skips`: synthetisches JSONL in tmp (2 Einträge A043 mit combined 80/90 + 1 mit score 70 als Fallback, 1 fehler-Eintrag, 1 Eintrag loc ohne Dump) → X (1,367), y ≈ Mittel(80,90,70), skipped enthält fehler + fehlender Dump.
  - `test_train_model_synthetic_recovers_signal`: 80 synthetische Samples (zufällige sdata via build_sndd, tmp dumps dir mit 80 Dumps A001..; oder direkt X,y ohne Dumps – train_model nimmt X,y) mit y = 100*(0.6*x[:,i_cutoff]+0.4*x[:,i_osc]) + N(0,2); `train_model` → metrics["r2"] > 0.8; importances[0] == param_names()[i_cutoff] (oder i_osc in top2).
  - `test_train_model_tiny_n`: n=3 → keine CV (r2_cv None), r2 auf Train, kein Crash.
  - `test_save_load_roundtrip`: Bundle speichern/laden (tmp joblib), predict identisch.
- [ ] **Step 2:** `python3 -m pytest tests/test_prognose.py -q` → FAIL (Modul fehlt).
- [ ] **Step 3:** Implementiere `bloridium/prognose.py` (sklearn-Import lazy in train/predict; RF `RandomForestRegressor(n_estimators, random_state=seed, n_jobs=-1)`; Holdout via `train_test_split` wenn n≥5 und test_size*n≥2; CV `cross_val_score` r2 bei n≥10; importances als [(name, imp)] sortiert; Bundle via joblib.dump).
- [ ] **Step 4:** pytest → PASS.
- [ ] **Step 5:** Commit: `git add bloridium/prognose.py tests/test_prognose.py && git commit -m "feat(prognose): RF-Modell SNDD→Score – Features/IO/Train/Predict (TDD)"`.

### Task 2: CLI `bloridium prognose train|predict` (TDD)

**Files:**
- Modify: `bloridium/cli.py`
- Modify: `tests/test_cli.py` (oder tests/test_prognose.py mit cli.main – Pattern aus test_cli.py: `cli.main(["--db", db, ...])`)

- [ ] **Step 1:** Tests: synthetische Dumps (20 Locs via `build_sndd`, sdata variiert; y aus einem Parameter) + synthetisches JSONL in tmp; `cli.main(["prognose","train","--log",log,"--dumps",dd,"--model",tmp/"m.joblib","--target","combined"])` → rc 0, Modell-Datei existiert, stdout enthält "r2"/"importance"; dann `cli.main(["prognose","predict","A001","--dumps",dd,"--model",…])` → rc 0, stdout enthält "predicted". `test_prognose_train_no_data_exit2`: leeres log → rc 2 + stderr-Meldung.
- [ ] **Step 2:** pytest → FAIL.
- [ ] **Step 3:** Implementiere in `cli.py`: `pg = sub.add_parser("prognose", …)` + `psub` mit `train` (--log default `sim.DEFAULT_LOG`, --dumps default `REPO/"dumps"`, --target "combined", --model default `models/prognose_rf.joblib`, --seed 42, --n-estimators 200) und `predict` (loc positional, --dumps, --model); `cmd_prognose_train`/`cmd_prognose_predict` rufen prognose.* auf, drucken Metriken + Top-10-Importances (mit Blofeld-Paramnamen) bzw. Prediction; keine Daten → print stderr + return 2. Dispatch in main via args.func (bestehendes Muster).
- [ ] **Step 4:** pytest → PASS.
- [ ] **Step 5:** Commit: `git commit -am "feat(cli): bloridium prognose train|predict"`.

### Task 3: Suite + Doku + Push

- [ ] **Step 1:** `python3 -m pytest tests/ -q` → alle PASS.
- [ ] **Step 2:** Doku: `docs/research/STATUS.md` (prognose-Modul + CLI + Datenvertrag für die datenliefernde Session: sim_log.jsonl-Schema + dumps/); Spec/Plan committen.
- [ ] **Step 3:** Commit + `git push origin main`.
