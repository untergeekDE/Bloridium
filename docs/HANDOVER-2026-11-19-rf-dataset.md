# Handover 2026-11-19 — RF-Datensatz + Prognose: alles, was die Prognose-Session wissen muss

**Eine Datei, self-contained.** Erzeugt von der datenliefernden Session (Repo
`../bloridium-codesearch`) am 2026-11-19. Alles Zahlen/Befehle hier verifiziert.

## 1. Was bereits da ist (alles in DIESEM Repo, gitignored: `dumps/`, `recordings/`, `models/`)

| Artefakt | Pfad | Inhalt |
|---|---|---|
| Mess-Log (Vertrag) | `recordings/sim_log.jsonl` | 381 Zeilen gesamt; davon **202 `mode=="rf-dataset"`** (100 Blofeld-Sounds A001–A100 × Note 72+60, gemessen 2026-11-19 voll remote), 197 mit `result.score`, 99/100 locs (A050 siehe §5) |
| SNDD-Dumps (Vertrag) | `dumps/blofeld_sndd_<LOC>_<ts>.bin` | **100/100** für A001–A100 (392 B komplettes SysEx inkl. F0/F7) + 3 ältere (11-08), byte-identisch zur Bank (sha256-geprüft) |
| Fertiges Modell | `models/prognose_rf.pkl` | trainiert 2026-11-19, `target=score`, n=99, **MAE 1.29 / RMSE 1.60** (holdout), R² −0.19 (negativ wg. kleiner Label-Varianz 86.8–98; MAE absolut gut). Vergleichsmodell `models/prognose_rf_combined.pkl` (MAE 2.32 — schlechter, nicht verwenden) |
| Eigenes Mess-Log | `../bloridium-codesearch/recordings/quir_rf_dataset.jsonl` | 202 Zeilen mit slot/label/qpat-Pfad pro Messung |
| Sweep-Config | `../bloridium-codesearch/recordings/quir_rf_dataset_config.json` | 100 Einträge `{slot 200–299, blofeld, qpat: "2:rf100/…", label}` |

## 2. Datenvertrag (exakt)

**sim_log.jsonl** — eine Zeile pro Messung:
```json
{"ts": "…", "meta": {"mode": "rf-dataset", "blofeld": "A043", "note": 72,
                     "iridium_slot": "242", "label": "SH Power", "load": "2:rf100/…",
                     "backends": {…}},
 "result": {"score": 89.01, "combined": 89.01, "embed_score": null, "verdict": "close",
            "spec_cos": …, "env_dtw": …, "error": null, …}}
```
- `meta.blofeld` = Location `^[A-Z]\d{3}$` (Vorsicht: eine Alt-Zeile hat `blofeld:"live"` → Regex filtern!)
- Label = `result.score` (Phase A, 0–100). **`result.combined == score` bei rf-dataset-Zeilen** (ohne `--embed` gemessen; `embed_score` ist dort `null`).
- Alte Zeilen ( Modi `live`, `pc_sweep`, `manual_panel`, `live-remote`, 11-14 bis 11-18) haben ebenfalls `result.score`, aber ihr `combined` ist durch den CLAP-Embed depressiv (z. B. A043: 75.04) → **immer `--target score` verwenden** (siehe §4).
- Fehler/stille Messungen: `result.score = null`, `result.error = "silent recording …"` → werden von `load_training_rows` übersprungen.

**Dumps** `dumps/blofeld_sndd_<LOC>_<ts>.bin`: komplettes SNDD-SysEx `F0 3E 13 00 10 bb nn <383 B SDATA> chk F7`; Bank A = `bb 0x10`, `nn` 0-basiert (A043 → nn 42). Parse: `blofeld_dump.parse_sndd(bytes)` → `{"bb","nn","sdata","chk","chk_ok","name","params"}`. Features: `prognose.feature_vector(parsed)` = SDATA-Bytes 0–382 **außer Namens-Bytes 363–378** / 127 → 367-d Vektor; Namen via `prognose.param_names()`. `find_dump(dumps_dir, loc)` nimmt pro LOC den neuesten Dump.

## 3. API + CLI (Modul `bloridium/prognose.py`, bereits im Repo)

```python
from bloridium import prognose
X, y, locs, skipped = prognose.load_training_rows(log_path, dumps_dir, target="score")  # aggregiert Mittel pro LOC, Fallback combined→score, skippt fehler/stumm/fehlende Dumps
bundle = prognose.train_model(X, y, seed=42, n_estimators=200, test_size=0.25, target="score")  # eigener RF (CART, Bootstrap, mtry=p//3, SSE) — sklearn/scipy ist in dieser Env DEFEKT (libgfortran.5.dylib fehlt), deshalb eigener RF + stdlib-pickle
prognose.save_model(bundle, "models/prognose_rf.pkl");  b = prognose.load_model("models/prognose_rf.pkl")
r = prognose.predict_loc("A043", dumps_dir, model_path)   # -> {"predicted", "std", "loc", "dump", …}
```
CLI:
```
python3 -m bloridium prognose train --target score            # Defaults: --log recordings/sim_log.jsonl --dumps dumps --model models/prognose_rf.pkl
python3 -m bloridium prognose predict A091                    # -> predicted 90.4 ± 3.0 (Ist-Mittel 87.8)
```
Defaults (verifiziert): `sim.DEFAULT_LOG = recordings/sim_log.jsonl`, `prognose.DEFAULT_DUMPS = dumps`, `prognose.DEFAULT_MODEL = models/prognose_rf.pkl`.

## 4. Bereits trainiert + Ergebnis (2026-11-19)

`prognose train --target score` → **n=99 locs** (A001–A100 ohne A050), MAE 1.29, RMSE 1.60, R²_holdout −0.187, R²_cv −0.062. Top-10 Feature-Importances (Treiber der Konvertier-Abweichung):

1. Modulation 5 Amount 0.033 · 2. Unisono Detune 0.029 · 3. Filter 1 Drive 0.028 ·
4. Osc 3 Bend Range 0.028 · 5. Filter Envelope Release 0.028 · 6. Filter 2 Resonance 0.028 ·
7. Osc 3 Octave 0.026 · 8. Modulation 2 Source 0.024 · 9. Modulation 3 Source 0.021 · 10. LFO 3 Speed 0.019

→ Drive / Resonanz / Detune / Modulation / Env-Release sind die kritischen Parameter.
Predict-Spotchecks: A091 → 90.4±3.0 (Ist 87.8), A024 → 95.2 (Ist 98.0), A019 → 94.2 (Ist 97.6).

## 5. Gotchas / Fallen

- **sklearn geht nicht** (scipy → `libgfortran.5.dylib` fehlt in conda-env `native`) → eigener RF in `prognose.py`, Persistenz via `pickle` (nicht joblib). Auf einer Maschine mit funktionierendem scipy kann sklearn drop-in ersetzt werden (Spec: `docs/superpowers/specs/2026-11-18-prognose-rf-design.md`).
- **A050 „Wakey Wakey" ist auf dem Blofeld selbst silent** (solo gemessen: −76,5 dBFS @ Note 72) → kein Konvertierungsfehler, hat keinen Score; `load_training_rows` skippt es automatisch.
- **A097** nur bei Note 72 silent (Blofeld-Seite), Note 60 = 87.94 → hat Score.
- `embed_score` ist in allen rf-dataset-Zeilen `null` (ohne `--embed` gemessen). Wer Embed als Label will, muss neu messen mit `--embed` (siehe §6).
- Frischer Clone: `dumps/`, `recordings/` und die GGUF-Downloads in `models/` sind gitignored → von diesem Mac kopieren (oder neu erzeugen, §6). **Die RF-Modelle `models/prognose_rf*.pkl` (~0,9 MB) sind dagegen git-tracked** (`.gitignore`: `models/*` + `!models/prognose_rf*.pkl`) und kommen mit dem Clone mit.
- `load_training_rows` liest ALLE Zeilen mit `meta.blofeld`. **Achtung seit 2026-11-19 12:00:** das Log enthält jetzt auch `mode=="optimize"`-Zeilen (Tweak-Loop, Phasen before/trial*/after — teils Duplikate, teils verrauscht). Für den sauberen Datensatz **auf `meta.mode == "rf-dataset"` filtern** (202 Zeilen, 197 scored, 99 locs). Alte Modi (`live`, `pc_sweep`, …) nur mit `--target score` mischen (deren `combined` ist embed-depressiv).
- 9 locs (A001, A008, A010, A019, A022, A039, A043, A071, A073) haben Vertrag-Dumps von 11-08 — sha256-identisch zur heutigen Bank (geprüft 11-19), also keine Stale-Features.

## 6. Workflow: neue Daten → re-train

Neue Messungen kommen aus dem codesearch-Repo (QUIR, voll remote; SD-qpats liegen auf `2:rf100/`, Slots 200–299 sind per `save-patch` persistiert):
```
cd ../bloridium-codesearch
python3 tools/quir_rf_dataset.py verify-sd                       # SD checken (100/100)
python3 tools/quir_rf_dataset.py measure --config recordings/quir_rf_dataset_config.json --allow-write --resume [--notes 72,60] [--embed]
# landet in recordings/sim_log.jsonl (dieses Repo) + codesearch/recordings/quir_rf_dataset.jsonl
cd ../Bloridium && python3 -m bloridium prognose train --target score   # re-train
```
Tweak-Loop: Ausreißer (loc-mean) **A091 87.78, A097 87.94, A043 89.55, A044 89.59, A025 90.47** — Parameter per `tools/quir_tweak.py` (codesearch) auf den Slots 200–299 ändern (Top-Importances aus §4 zuerst), dann Re-Sweep einzelner Sounds (`tools/quir_ab_sweep.py --config … --notes 72,60 --allow-write`) und re-train.

## 6b. Tweak-Loop-Ergebnis 2026-11-19 12:00 (codesearch)

- `quir_optimize.py` (CLI, voll remote): lädt `2:rf100/<sd_name>.qpat`, Bulk-Readback,
  Hill-Climbing in Geräte-Skala. **Negativ-Ergebnis:** hartes Setzen auf qpat-Readback-Werte
  (`--mode fix`, deprecated) schadet — qpat-Loader und QUIR-Readback rechnen in
  unterschiedlichen Skalen (A091/A097 stumm, A043 90.8→80.3). Hill-Climbing bei delta 0.05
  liegt unter dem Messrauschen (±1–3); "Gewinne" waren Artefakte (pid 3779 LastNotePlayed).
  → Zuverlässiges Tweaken braucht Mehrfachmessung pro Trial oder `--embed` als Ziel.
  Phase-B-Diagnose der Ausreißer (A091 A043 A044 A025 A097): `recordings/quir_ab_sweep_rf_outliers_phaseb.jsonl` + PNGs in `../bloridium-codesearch/recordings/spec_rf/`.

## 6c. Migration auf Score v2 (2026-11-20) — Modelle sind jetzt v2-trainiert

- `sim.py` rechnet seit 2026-11-20 mit **SCORE_VERSION 2** (`70 % spec_mad + 30 % env_dtw`);
  jede neue Zeile trägt `result.score_version: 2`. v1-Zeilen (gesättigt ~94–97) sind im
  `sim_log.jsonl` weiterhin vorhanden, werden aber von `prognose train` per Default
  übersprungen (`--min-score-version 2`; `0` = alle, nie mischen!).
- v2-Datensatz: 200 Messungen A001–A100 (notes 72,60, neue Konversion rf200 auf SD),
  188 gescored, **mean 50.5, range 22.4–81.3** — `recordings/sim_log_v2_rf.jsonl`
  (gefiltert: v2 + mode=rf-dataset; das Roh-Log `sim_log.jsonl` enthält v1+v2 gemischt).
- Retrain: `bloridium prognose train --log recordings/sim_log_v2_rf.jsonl --target score`
  → n=99, MAE 10.47, **R²=+0.064 / R²_cv=+0.132** (v1-Modell: R²<0). Alte Modelle:
  `models/prognose_rf_v1.pkl`, `prognose_rf_combined_v1.pkl`.
- Entropy-Check (`bloridium prognose entropy --log recordings/sim_log_v2_rf.jsonl`):
  H(y)=3.14 bits; **embed_score partielle IG 0.63 bits gegeben spec_mad_db** (d1-profile
  0.60, llm konstant). embed/d1 sind post-hoc (Leakage als Input-Feature) → nur als
  Label/diagnostisch, nicht für die Dump→Score-Vorhersage.
- Conversion 2026-11-20: LFO Shape/Phase/Delay + Mixer-Noise (freier/stummer Osc als
  White/Pink Noise) + Sync (bereits gedeckt) gemappt; qpat-Dateinamen sind per Konversion
  SD-sicher (`qpat.sd_filename`) — plain cp auf die SD reicht.

## 7. Stand 2026-11-19 (finaler Tweak-Loop-Abschluss 12:20)

Phase-B-Diagnose der Ausreißer (A091 A043 A044 A025 A097, `--embed --llm --norm-pegel
--spec-png-dir`): LLM meldet überall „very similar, dezenter Higher-Frequency-Edge auf der
Iridium-Seite" → **systematische Timbre-Differenz** (Oszillator/Wavetable), kein
Per-Sound-Param-Problem. Gerichteter EqHighGain-Test (A091, pid 2836: 0.5→0.3) ergab
+1.1 Score — unter dem Messrauschen (±1–3). Hill-Climbing bei delta 0.05 ebenfalls unter
Rauschen; hartes Setzen auf qpat-Readback-Werte schadet (Skalen-Diff). Fazit: mean 93.9
(99 locs) ist nahe am Machbaren; RF-Modell MAE 1.29 bleibt gültig (Training nur auf
`mode=="rf-dataset"` filtern!). Details: `../bloridium-codesearch/TODO_FIX.md` 11-19 11:05–12:20.

Datensatz komplett (100 Dumps, 202 rf-Messungen, 197 scored, 99 locs), Modell trainiert
(MAE 1.29). Nächster Schritt: Prognose-Funktion um das Modell herum bauen
(`predict_loc` + CLI `prognose predict`), dann Tweak-Loop auf den Ausreißern mit den
Top-Importances-Parametern und Re-Train — Ziel: MAE weiter drücken und die
critical params sicher identifizieren.
