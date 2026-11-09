# Similarity-Tool Blofeld↔Iridium (Phase A) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein numpy-only Tool, das zwei Synth-Aufnahmen (Blofeld vs Iridium) in einen Ähnlichkeits-Score 0–100 + interpretierbare Band-Deltas übersetzt und jeden Run als JSONL loggt (Feedback für Human, Metrik fürs Transfer-Tuning, Daten fürs spätere Mapping-Modell).

**Architecture:** `bloridium/sim.py` (rein, numpy: `features()` → log-mel-ähnliches Spektrogramm + RMS-Hülle; `compare()` → Score; `log_run()` → JSONL) + `scripts/sim_compare.py` (offline auf .npy-Takes oder live Messung) + `scripts/sim_live.py` (CC-Dreh-Loop mit CC/Pid-Map). Keine neuen Dependencies.

**Tech Stack:** Python 3.10, numpy, pytest; MIDI/Audio nur in Skripten (in Tests monkeypatched); mido/rtmidi wie bestehend.

**Spec:** `docs/superpowers/specs/2026-11-09-similarity-tool-design.md` (genehmigt 2026-11-09)

## Global Constraints
- Phase A: **nur numpy**, keine ML-Modelle/neuen Deps (Embeddings sind Phase B laut Spec).
- Aufnahme 48 kHz, Scarlett; Blofeld In 3/4 = ch (2,3), Iridium In 5/6 = ch (4,5) (`bloridium.audio.CHANNELS`).
- MIDI-Ports: DEFAULT_PORTS in `bloridium/midi.py` (Launchpad-DIN; Iridium Parts = ch6–9, idx 5–8; Blofeld ch5, idx 4).
- Sustain-Fenster 0.5–1.2 s nach Note-On (Attack verfälscht, HANDOVER); Hochpass 80 Hz vor Feature-Extraktion (DC/Brumm).
- Log: `recordings/sim_log.jsonl` (eine JSON-Zeile pro Run).
- Tests dürfen keine Hardware/MIDI/Audio brauchen (monkeypatch).

## Review Focus
1. Leere/zu kurze Aufnahme (ffmpeg liefert < Fenster) → `features()` darf nicht crashen, sondern klaren Fehler/Score None liefern. → Task 1 Test.
2. DC-Offset/Netzbrumm in niederen Bändern verfälscht Cosine → HP 80 Hz **vor** Features. → Task 1 Test (DC-lastiges Signal).
3. Unterschiedliche Länge der beiden Aufnahmen → Cosine auf gemitteltem Spec (längenunabhängig), DTW auf Hüllen. → Task 2 Test.
4. JSONL-Log: Platte voll / kaputter Eintrag darf Vergleich nicht killen → `log_run` fängt OSError. → Task 3 Test.
5. CC-Map ohne Pid-Spalte (alte CSV) → `ccmap` fällt auf Name-Only zurück, kein Crash. → Task 5 Test.

---

### Task 1: `bloridium/sim.py` — `features()`

**Files:**
- Create: `bloridium/sim.py`
- Test: `tests/test_sim.py`

**Interfaces:**
- Produces: `features(x: np.ndarray, sr: int = 48000, n_bands: int = 48, f_lo: float = 40.0, f_hi: float = 12000.0, hop_s: float = 0.05, hp_hz: float = 80.0) -> dict` mit Keys `"log_spec"` (n_bands × n_frames, dB), `"env_rms"` (n_frames,), `"band_edges"` (n_bands+1,), `"sr"`, `"n_samples"`. Werfer bei `len(x) < int(0.2*sr)`: `ValueError("zu kurz")`.

- [ ] **Step 1: Write the failing test** — `tests/test_sim.py::test_features_sine_peak_im_richtigen_band`: 1 s Sinus 440 Hz @ 48 kHz → `log_spec` argmax-Band ≈ Band von 440 Hz (±1); `test_features_dc_wird_durch_hp_entfernt`: DC + kleiner Sinus → niederstes Band nicht dominant; `test_features_zu_kurz_wirft`: 0.1 s → pytest.raises(ValueError).
- [ ] **Step 2: Run, expect FAIL** — `python3 -m pytest tests/test_sim.py -v`
- [ ] **Step 3: Implement `features()`** in `bloridium/sim.py`: FFT mit Hann pro Frame (hop_s), Leistung → dB; log-spaced Bänder via `band_edges = geomspace(f_lo, f_hi, n_bands+1)`; vorab FFT-Hochpass `hp_hz` (X[f<hp]=0) auf ganzem Signal; `env_rms` = sqrt(mean(frame²)) pro Frame.
- [ ] **Step 4: Run, expect PASS**
- [ ] **Step 5: Commit** — `git add bloridium/sim.py tests/test_sim.py && git commit -m "feat: sim.features (log-spec + env)"`

### Task 2: `bloridium/sim.py` — `compare()`

**Files:**
- Modify: `bloridium/sim.py`
- Test: `tests/test_sim.py`

**Interfaces:**
- Consumes: `features()` aus Task 1.
- Produces: `compare(fa: dict, fb: dict) -> dict` mit Keys `"score"` (0–100 float), `"spec_cos"` (0–1), `"env_dtw"` (normiert 0–1, 0 = identisch), `"band_delta_db"` (Liste n_bands: fb − fa in dB, gemittelt über Frames), `"verdict"` ("nahe" ≥ 85, "mittel" ≥ 60, sonst "weit").

- [ ] **Step 1: failing tests**: `test_compare_identisch_score_100`: gleiches Feature-Dict zweimal → score ≈ 100, verdict "nahe"; `test_compare_anderes_spektrum_score_sinkt`: fa = 440 Hz, fb = 2 kHz → spec_cos < 0.9, score < 100; `test_compare_unterschiedliche_laenge_ok`: fa 1.0 s, fb 0.7 s → kein Crash, score endlich; `test_band_delta_vorzeichen`: fb heller → band_delta_db in hohen Bändern > 0.
- [ ] **Step 2: Run, expect FAIL**
- [ ] **Step 3: Implement `compare()`**: spec_cos = Cosine auf frame-gemitteltem log_spec (flatten); env: eigene DTW-DP (numpy) auf env_rms, normiert durch Pfadlänge → env_dtw = dtw / (len_a+len_b); score = 100 * (0.7*spec_cos + 0.3*(1-env_dtw)), geclampt 0–100; band_delta_db = mean(fb.log_spec, axis=1) − mean(fa.log_spec, axis=1).
- [ ] **Step 4: Run, expect PASS**
- [ ] **Step 5: Commit** — `git commit -m "feat: sim.compare (cosine + DTW + score)"`

### Task 3: `bloridium/sim.py` — `log_run()` + `score_pair()`

**Files:**
- Modify: `bloridium/sim.py`
- Test: `tests/test_sim.py`

**Interfaces:**
- Produces: `log_run(result: dict, meta: dict, path=REPO/"recordings/sim_log.jsonl") -> bool` (append JSON-Zeile `{"ts":..., "meta":..., "result":...}`, OSError → False, nie werfen); `score_pair(x_blo: np.ndarray, x_irr: np.ndarray, sr: int, meta: dict) -> dict` (features + compare + log_run, gibt result zurück; bei ValueError aus features → result mit score None, verdict "fehler").

- [ ] **Step 1: failing tests**: `test_log_run_schreibt_jsonl` (tmp_path): eine Zeile, json.loads ok, Keys ts/meta/result; `test_log_run_kaputter_pfad_gibt_false`: path in nicht existierendem, nicht anlegbarem Dir (monkeypatch mkdir fail oder read-only) → False, kein Raise; `test_score_pair_zu_kurz_gibt_fehler`: 0.05 s Signale → verdict "fehler", score None.
- [ ] **Step 2/3/4: TDD wie oben**
- [ ] **Step 5: Commit** — `git commit -m "feat: sim.log_run + score_pair"`

### Task 4: `scripts/sim_compare.py`

**Files:**
- Create: `scripts/sim_compare.py`
- Test: `tests/test_scripts.py` (bestehend — dortiges Pattern übernehmen)

**Interfaces:**
- Consumes: `bloridium.sim.score_pair`, `bloridium.audio`, `bloridium.midi`.
- CLI: `python3 scripts/sim_compare.py --npy A.npy B.npy [--meta k=v ...]` (offline: .npy mit shape (2, N) oder (N,), mono mitteln) ODER `--live [--note 60] [--dur 1.6] [--blofeld A043] [--iridium-slot 207]`: All Notes Off + CC7=127 alle 16 ch, Note-On Blofeld ch4 + Iridium ch5–8, record alle 20 ch, slice CHANNELS, score_pair, print Score + Top-5-Band-Deltas + verdict, log_run.

- [ ] **Step 1: failing test** in `tests/test_scripts.py`: `test_sim_compare_npy_offline`: zwei synthetische .npy (Sine 440 vs 440 / vs 2000 Hz) in tmp_path → ruft sim_compare.main() mit argv monkeypatched auf, exit 0, sim_log.jsonl (monkeypatch REPO-Log via env oder tmp) enthält Eintrag mit score. (Kein MIDI/Audio im Test: nur --npy-Pfad.)
- [ ] **Step 2/3/4: TDD** — Live-Teil erst nach offline-Teil grün, gegen `midi.connect`/`audio.record` monkeypatchbar strukturieren (Funktionen `run_live(note, dur)` einzeln testbar mit Fakes).
- [ ] **Step 5: Commit** — `git commit -m "feat: scripts/sim_compare.py (npy + live)"`

### Task 5: CC/Pid-Map + `scripts/sim_live.py`

**Files:**
- Modify: `bloridium/ccmap.py` (Pid-Spalte aus `docs/midi-maps/iridium_pid_map.csv` laden; Fallback name-only wenn Spalte fehlt)
- Create: `scripts/sim_live.py`
- Test: `tests/test_cc.py` (bestehend) + `tests/test_scripts.py`

**Interfaces:**
- Produces: `ccmap.load_pid_map(path=REPO/"docs/midi-maps/iridium_pid_map.csv") -> dict` {name_lower: (cc, pid)}; `ccmap.cc_for(name) -> int | None`.
- `scripts/sim_live.py --param "Filter1 Cutoff" --value 90 [--ref REF.npy] [--note 60]`: CC ans Iridium (ch5–8) senden, Note spielen, aufnehmen, gegen Blofeld-Referenz (--ref .npy, sonst live Blofeld mitspielen) score, print + log_run. Exit 0.

- [ ] **Step 1: failing tests**: `test_ccmap_pid_map_laden`: echte CSV laden → "filter1 cutoff" → (0, 966); `test_ccmap_fallback_ohne_pid_spalte`: tmp-CSV nur cc,name → cc_for funktioniert, pid None; `test_sim_live_mit_fakes`: midi.connect/audio.record monkeypatched → main exit 0, log enthält Eintrag.
- [ ] **Step 2/3/4: TDD**
- [ ] **Step 5: Commit** — `git commit -m "feat: ccmap pid-map + scripts/sim_live.py"`

### Task 6: Doku & Vollsuite

**Files:**
- Modify: `docs/CLI.md` (kurzer Abschnitt sim_compare/sim_live), `README.md` (1 Absatz)
- Test: `python3 -m pytest tests/ -q` voll

- [ ] **Step 1:** Doku-Abschnitte schreiben (Aufruf-Beispiele, Log-Pfad, Verdict-Schwellen).
- [ ] **Step 2:** `python3 -m pytest tests/ -q` → alle grün (aktuell 139 + neue).
- [ ] **Step 3: Commit** — `git commit -m "docs: sim-Tool"`

---

## Self-Review (done inline while writing)
- Spec-Coverage: features/compare/log (Tasks 1–3), offline+live compare (Task 4), CC-Map + live loop (Task 5), Doku (Task 6). Phase-B-Embeddings bewusst ausgespart (Spec: Phase B).
- Signaturen konsistent: `features`, `compare`, `log_run`, `score_pair`, `ccmap.load_pid_map/cc_for` — in allen Tasks gleich geschrieben.
- Review-Focus-Punkte 1–5 haben jeweils einen Test in Task 1/2/3/5.
- Keine neuen Deps; HW nur in Skripten, Tests monkeypatched.
