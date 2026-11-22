# Design: Prognosemodell – Random Forest aus Blofeld-SNDD-Parametern → erwartete Konvertiergüte

Datum: 2026-11-18 · Status: zur Umsetzung („bereite vor“, Benutzer 2026-11-18)

## Intent & Why

Vor/nach der Konvertierung eines Sounds soll ein **leichtgewichtiges Modell auf der CPU**
vorhersagen, wie gut der Blofeld-Sound auf dem Iridium landen wird (Score 0–100 aus
unseren sim-Messungen). Random Forest: robust bei wenigen Samples, liefert
Feature-Importances (welche Blofeld-Parameter treiben die Konvertiergüte – z. B.
Sync/FM/PWM, serielle Filter-Routing), kein GPU nötig. sklearn 1.5.1 + joblib sind
bereits installiert.

**Datenvertrag mit der datenliefernden Session:** Trainingsdaten sind die vorhandenen
Repo-Artefakte – `recordings/sim_log.jsonl` (pro Messung: `meta.blofeld` = Location,
`result.score` / `result.combined` / `result.embed_score`) + SNDD-Dumps in `dumps/`
(`blofeld_sndd_<LOC>_<ts>.bin`, Location steht auch im SysEx-Header bb/nn).
Sobald die andere Session ihre Vergleichsdaten in diesen Formaten (oder als JSONL mit
gleichem Schema) ablegt, kann `bloridium prognose train` direkt lernen.

## Goals / Non-goals

- Goals:
  - Neues Modul `bloridium/prognose.py`:
    - `feature_vector(parsed) -> np.ndarray` – SDATA-Bytes (Indizes 0–382 außer
      Namens-Bytes 363–378) / 127 → 367-d Vektor; `param_names()` dazu (aus
      `blofeld_dump.SDATA`).
    - `loc_from_header(data)`, `find_dump(dumps_dir, loc)` (neuester Dump pro Location).
    - `load_training_rows(log_path, dumps_dir, target="combined")` – liest JSONL,
      aggregiert pro Location (Mittel über `result[target]`, Fallback `score`),
      überspringt fehler/stille Messungen und fehlende Dumps → `(X, y, locs, skipped)`.
    - `train_model(X, y, seed, n_estimators)` – `RandomForestRegressor`, Holdout-Metriken
      (MAE/RMSE/R²) + 5-fold-CV-R² (falls n≥10) + Top-Feature-Importances → Bundle-dict.
    - `save_model`/`load_model` via joblib nach `models/prognose_rf.joblib` (gitignored).
    - `predict_loc(loc, dumps_dir, model_path)` – Prediction + Std über die Bäume
      (Unsicherheit).
  - CLI: `bloridium prognose train --log … --dumps … [--target combined] [--model …]`
    und `bloridium prognose predict A043 [--dumps …] [--model …]`.
- Non-goals:
  - Kein Training auf qpat/qpat_map-Zwischenrepräsentation – direkt SNDD→Score.
  - Kein Deep Learning, kein GPU, kein Online-Learning; Modell wird per CLI neu trainiert.
  - Kein Persistieren von Trainingsdaten im Repo (nur Modell-Bundle in `models/`, gitignored).
- Anti-goals:
  - Namens-Bytes (363–378) nicht als Features (Soundname würde leaken/overfitten).
  - Keine stillen Sample-Verluste: `skipped` wird geloggt/printet.

## Constraints

- **Ruling 2026-11-18 (bei Task 1):** sklearn ist in dieser Env NICHT nutzbar (sklearn→scipy
  und scipy ist defekt: `libgfortran.5.dylib` fehlt) und der Repo-Kern ist numpy-only.
  → kein sklearn/joblib; stattdessen kompakter eigener `RandomForestRegressor` in
  `prognose.py` (CART-Regression, Bootstrap, mtry=p//3, SSE-Gewinn, Feature-Importances)
  + Persistenz via stdlib `pickle`. Kosten falls falsch: eigener RF weniger kampferprobt
  als sklearn – mitigiert durch synthetische Signal-Recovery-Tests. Vorhersage: bei
  funktionierendem scipy auf der Zielmaschine kann sklearn spaeter drop-in ersetzt werden.
- CPU only, deterministisch (`random_state=seed`).
- Tests offline: echte Dump-Datei (`dumps/blofeld_sndd_A043_*.bin`) + synthetische
  Dumps via `blofeld_dump.build_sndd` + synthetisches JSONL. Kein Live-MIDI.
- Deutsch Doku/Commits; `python3 -m pytest tests/ -q`.

## Approaches

- **A (gewählt):** SNDD-Rohvektor (367 Features) → sklearn RandomForestRegressor,
  Label = gemitteltes sim-Target pro Location. Einfach, robust, importances direkt auf
  Blofeld-Parameternamen abbildbar.
- **B (abgelehnt):** Features aus dem qpat-Mapping (overrides) – näher am Iridium, aber
  Mapping-abhängig und lückenhaft (unmapped); SNDD ist die stabile Quelle.
- **C (abgelehnt):** Gradient Boosting / MLP – overkill bei erwartet <100 Samples,
  schlechter interpretierbar.

## Was die datenliefernde Session beachten muss (Datenvertrag)

- Messungen landen als JSONL wie `recordings/sim_log.jsonl`: `{"ts", "meta": {…,
  "blofeld": "A043", …}, "result": {"score", "combined", "embed_score", "verdict", …}}`.
- Dumps als `dumps/blofeld_sndd_<LOC>_<ts>.bin` (komplette SysEx inkl. F0/F7 oder mido-Bytes).
- Optional gleiches Schema als separate Datei: `prognose train --log <datei>`.
