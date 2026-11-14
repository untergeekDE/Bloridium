# Phase B Sim-Embed (CLAP-GGUF + ollama-Urteil) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase B des Sound-Vergleichs: numerischer CLAP-Embedding-Score + optionales ollama-LLM-Urteil neben Phase A, auf allen Entrypoints (`sim compare`, `ab`, Skripte), geloggt in `sim_log.jsonl`/`report_json`, offline evaluierbar auf den 4 vorhandenen .npy-Paaren.

**Architecture:** Modelle laufen extern (clap.cpp GGUF via pip-Binding/subprocess; ollama per HTTP) — `bloridium/sim_embed.py` kapselt beide Backends hinter schmalen Klassen; `score_pair_embed` kombiniert `sim.features`/`sim.compare` (Phase A, ohne Doppel-Log) mit Embedding (+LLM) zu einem Ergebnisdict. Kein MLX (ROCm-Portabilität), kein DB-Schema-Wechsel (report_json ist JSON-Blob).

**Tech Stack:** Python 3.10.13, macOS; numpy-only im Kern; stdlib `wave` (kein soundfile); PIL 10.2 (Spektrogramm-PNG); requests/httpx für ollama-API; pytest>=8; Modelle: `gorse-io/larger_clap_music_and_speech-GGUF` Q8_0 (Apache-2.0) in `models/`, ollama `lfm3-omni:2b`.

**Spec:** `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md` (genehmigt 2026-11-14; Builder-Check ses_e25f5d23… ist eingearbeitet)

## Global Constraints

- Python 3.10, macOS; Kern bleibt numpy-only — keine neuen schweren Runtime-Dependencies (clap-cpp/ollama sind extern: subprocess/HTTP).
- Unit-Tests offline: kein Live-MIDI, kein Modell-Download, Backends werden gemockt (monkeypatch); echter GGUF nur in einem `slow`-markierten Integrationstest (skip wenn Modell fehlt).
- Degrade-Regel: Backend fehlt → Warnung auf stderr, Phase A läuft, Log-Felder `null` + `backend_error`, Exit 0; `--strict` → Exit 3. Bestehendes Exit-Verhalten (1 bei Phase-A-`fehler`) bleibt.
- CLAP-Input: ganze Aufnahme mono; Resample auf 48 kHz nur wenn nötig; Padding macht das Backend.
- LLM: deutscher `DEFAULT_JUDGE_PROMPT`, Anker 100 = nicht unterscheidbar; Antwort-Contract `{"score": 0-100, "summary": str, "differences": [str, ...]}`; `differences` = String-Array; Prompt-ID im Log.
- `combined = 0.5*score + 0.5*embed_score`; LLM-Score informativ, nicht in `combined`.
- `models/` in `.gitignore`; keine Modell-Dateien ins Repo.
- Doku/Prompts/Commit-Messages auf Deutsch, konsistent zum Repo. Tests laufen: `python3 -m pytest tests/ -q`.

## Review Focus

1. **Sweeps dürfen nie wegen fehlendem Backend crashen** → Degrade-Test: `score_pair_embed` mit `clap=None` + `strict=False` liefert `embed_*: null` + `backend_error`, Exit-Verhalten 0; mit `strict=True` wirft/exit 3. (Task 5, Task 7)
2. **LLM-Antwort-Parsing** muss Fließtext um das JSON herum verkraften → Test mit `"Hier das Urteil: {...} Hoffe das hilft."`. (Task 4)
3. **Paare unterschiedlicher Länge vergleichbar** → Embed-Test mit 126 080 vs 133 969 Samples und mit sr≠48000 (Resample-Pfad). (Task 3)
4. **Log-Schema stabil für Downstream-Training** → JSONL-Eintrag enthält Backend-Keys immer (als `null`), nie fehlend; ein Test pinnt die Key-Menge. (Task 5)
5. **`ab_runs.report_json` bleibt ohne Migration kompatibel** → Test: `db.log_ab_run` mit erweitertem report dict (sim/embed/llm keys) roundtrip; alte Rows ohne Keys lesbar. (Task 9)

---

### Task 1: Spike — Runtime-Fähigkeiten verifizieren (vor allem Code)

**Files:**
- Modify: `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md` (Abschnitt „Spike-Ergebnisse 2026-11-14“ anhängen)
- Create: `models/` (gitignored, lokal)

- [ ] **Step 1:** CLAP-GGUF laden: `python3 -m huggingface_hub.commands.hf_cli download gorse-io/larger_clap_music_and_speech-GGUF larger_clap_music_and_speech-q8_0.gguf --local-dir models/` (oder `hf download …`); erwartet: ~208 MB Datei in `models/`.
- [ ] **Step 2:** `pip install clap-cpp` testen; danach Smoke: kleines WAV (Sine 440 Hz, 1 s, 48 kHz) embedden → 512-d Vektor, Norm ≈ 1. Falls pip-Paket nicht tut: clap.cpp bauen (cmake) und Binary-Pfad als Fallback notieren — Entscheidung im Spec festhalten.
- [ ] **Step 3:** `ollama pull lfm3-omni:2b` (2 GB); `ollama serve` sicherstellen; dann API-Test: `POST /api/chat` mit `messages:[{role:user, content:"…", audio:[<base64 wav>]}]` gegen lfm3-omni:2b. Ergebnis notieren: akzeptiert 0.40.16 das `audio`-Feld (200 + valides JSON-Urteil) oder 4xx → dann Fallback-Modus = Spektrogramm-PNG via `images` an Vision-Modell (z. B. gleiches lfm3-omni, das ist vision-fähig). Modus im Spec vermerken.
- [ ] **Step 4:** Spec-Abschnitt „Spike-Ergebnisse“ committen (docs only): GGUF-Pfad, clap-cpp-Zugang (pip vs binary), ollama-Modus (audio vs spec-PNG), Modell-Versionen.

### Task 2: `bloridium/sim_embed.py` — reine Helfer (TDD)

**Files:**
- Create: `bloridium/sim_embed.py`
- Create: `tests/test_sim_embed.py`

**Interfaces (produziert):**
- `write_wav(x: np.ndarray, sr: int, path: Path) -> None` — float32 → int16 PCM mono via stdlib `wave`
- `render_spec_png(x: np.ndarray, sr: int, path: Path) -> None` — log_spec aus `sim.features` als Graustufen-PNG via PIL (log-dB auf 0–255 gemappt)
- `embed_compare(ea: np.ndarray, eb: np.ndarray) -> dict` — `{"embed_cos": float, "embed_score": float}`; Score = `100*clip(cos, 0, 1)`

- [ ] **Step 1:** Tests schreiben: `test_write_wav_roundtrip` (wave-Modul liest zurück, Länge/Pegel ok), `test_render_spec_png_valid` (PIL öffnet, Mode L, Größe>0), `test_embed_compare_edges` (cos=1→100, cos=0→0, cos<0→0, dict-Keys exakt `embed_cos`/`embed_score`).
- [ ] **Step 2:** `python3 -m pytest tests/test_sim_embed.py -q` → FAIL (Modul fehlt).
- [ ] **Step 3:** Implementierung in `bloridium/sim_embed.py` (nur diese drei Funktionen; `REPO`/`DEFAULT_LOG` analog zu `sim.py` importieren).
- [ ] **Step 4:** pytest → PASS. Commit: `feat(sim_embed): write_wav/render_spec_png/embed_compare + Tests`.

### Task 3: `ClapBackend` (TDD, gemockt)

**Files:**
- Modify: `bloridium/sim_embed.py`
- Modify: `tests/test_sim_embed.py`

**Interfaces:**
- `class ClapBackend:` `__init__(self, model_path: str | Path)`; `embed(self, x: np.ndarray, sr: int) -> np.ndarray` — mono-mitteln, sr≠48000 → linear resample (numpy), WAV via `write_wav` in tmp, dann: zuerst `clap_cpp`-Binding, Fallback subprocess `clap embedding --model M --audio WAV` → stdout JSON-Array parsen → float32-Vektor (512,), L2-normalisiert; Fehler → `RuntimeError` mit Backend-Message.

- [ ] **Step 1:** Tests mit monkeypatch: `test_embed_uses_binding_when_available` (fake `clap_cpp` Modul injizieren), `test_embed_subprocess_fallback_parses_json` (fake subprocess.run → stdout `[0.1, …]`), `test_embed_resamples_non_48k` (sr=44100 → WAV-Header tragen 48000), `test_embed_different_lengths_ok` (126 080 vs 133 969 Samples → jeweils (512,)), `test_embed_raises_on_backend_error`.
- [ ] **Step 2:** pytest → FAIL. **Step 3:** Implementierung. **Step 4:** pytest → PASS. Commit.

### Task 4: `OllamaBackend` + `DEFAULT_JUDGE_PROMPT` (TDD, gemockt)

**Files:**
- Modify: `bloridium/sim_embed.py`, `tests/test_sim_embed.py`

**Interfaces:**
- `DEFAULT_JUDGE_PROMPT: str` — deutsch, zwei Clips (A/B) + Anker 100 = nicht unterscheidbar, Contract `{"score":0-100,"summary":"…","differences":["…"]}`.
- `class OllamaBackend:` `__init__(self, model="lfm3-omni:2b", host="http://localhost:11434")`; `available(self) -> bool` (GET `/api/tags`); `judge(self, x_a, x_b, sr, prompt=DEFAULT_JUDGE_PROMPT) -> dict` — Request bauen; Spike-Modus `audio` (base64 WAV via `audio`-Feld) probieren, bei 4xx Fallback: `render_spec_png` beider Clips + `images`-Feld; Antwort-Content → erstes `{...}` extrahieren (regex), validieren (score int 0–100, differences list[str]); Rückgabe: `{"score", "summary", "differences", "mode": "audio"|"spec", "model"}`.

- [ ] **Step 1:** Tests (monkeypatch `requests.post`/`get`): `test_available_true_false`, `test_judge_audio_mode_ok`, `test_judge_falls_back_to_spec_on_400` (erstes post → 400, zweites mit `images` → 200), `test_judge_parses_json_inside_prose` (Content = `"Urteil: {\"score\": 87, ...} Ende."`), `test_judge_invalid_json_raises`.
- [ ] **Step 2:** FAIL. **Step 3:** Implementierung. **Step 4:** PASS. Commit.

### Task 5: `score_pair_embed` — Kombination + Log (TDD, echte .npy, Fake-Backends)

**Files:**
- Modify: `bloridium/sim_embed.py`, `tests/test_sim_embed.py`

**Interfaces:**
- `score_pair_embed(x_blo, x_irr, sr=48000, meta=None, log_path=DEFAULT_LOG | None, clap: ClapBackend | None = None, ollama: OllamaBackend | None = None, use_llm=False, strict=False) -> dict`
  - ruft `sim.features` + `sim.compare` direkt auf (kein `sim.score_pair` → kein Doppel-Log), Stille-Guard wie Phase A (`verdict:"fehler"` → return, loggen).
  - Ergebnis-Keys: Phase-A-Keys (`score`, `spec_cos`, `env_dtw`, `band_delta_db`, `verdict`) + `embed_cos`, `embed_score`, `combined` + `llm` (dict|None) + `backend_error` (str|None). Backend fehlt & nicht strict → Felder `null`, `backend_error` gesetzt, weiterrechnen; strict → `RuntimeError`.
  - `log_path` gesetzt → genau ein JSONL-Eintrag via `sim.log_run` mit Meta inkl. `backends: {clap: model|"none", ollama: model|"none", llm: bool, prompt_id}`; `log_path=None` → nicht loggen (für `measure_ab`).

- [ ] **Step 1:** Tests auf den echten Paaren `recordings/ab_A043_20261108_142609_{blofeld,iridium}.npy` mit Fake-Clap (gibt Einheitsvektor zurück) + tmp log: `test_score_pair_embed_full_schema` (Key-Menge exakt gepinnt, inkl. `null`-Felder bei fehlendem Backend), `test_combined_is_50_50`, `test_no_backend_degrades_not_raises` (clap=None → embed null, backend_error gesetzt, score ok), `test_strict_raises`, `test_silence_verdict_fehler` (Null-Signal → fehler, geloggt), `test_log_written_once` (JSONL wächst um genau 1 Zeile, `log_path=None` → keine Zeile).
- [ ] **Step 2:** FAIL. **Step 3:** Implementierung. **Step 4:** PASS. Commit.

### Task 6: `scripts/fetch_models.py` + `.gitignore` (TDD, gemockt)

**Files:**
- Create: `scripts/fetch_models.py`
- Modify: `.gitignore` (Zeile `models/`)
- Modify: `tests/test_scripts.py` (oder neues `tests/test_fetch_models.py`)

**Interfaces:**
- `main(argv=None) -> int` — lädt GGUF Q8_0 nach `models/` (hf download, idempotent: vorhanden → skip), `ollama pull lfm3-omni:2b` (subprocess, idempotent), optional `--pip-clap-cpp` → `pip install clap-cpp`. Exit 0 bei Erfolg, 1 bei Fehler mit klarer Meldung. Startet **keinen** ollama-Server.

- [ ] **Step 1:** Tests mit monkeypatch subprocess: `test_fetch_skips_existing_gguf`, `test_fetch_pulls_ollama_model`, `test_fetch_failure_exit_1`.
- [ ] **Step 2:** FAIL. **Step 3:** Implementierung + `.gitignore`. **Step 4:** PASS. Commit.

### Task 7: `scripts/sim_compare.py` um `--embed`/`--llm`/`--strict` erweitern (TDD)

**Files:**
- Modify: `scripts/sim_compare.py`, `tests/test_scripts.py`

**Interfaces:** `sim_compare.main` bekommt `--embed`, `--llm`, `--strict`, `--models-dir` (Default `models/`); baut Backends (ClapBackend(models_dir/GGUF falls Datei existiert, sonst None + Warnung; OllamaBackend wenn `available()`), ruft `sim_embed.score_pair_embed` statt `sim.score_pair` (beide Pfade `--npy` und `--live`). Exit: 1 bei Phase-A-fehler, 3 bei strict+Backend-Fehler, sonst 0.

- [ ] **Step 1:** Tests (monkeypatch midi/audio/sim_embed-Backends): `test_npy_embed_flag_adds_embed_score`, `test_embed_missing_model_degrades_exit_0`, `test_strict_missing_model_exit_3`, `test_live_path_uses_score_pair_embed`.
- [ ] **Step 2:** FAIL. **Step 3:** Implementierung. **Step 4:** PASS + `python3 -m pytest tests/ -q` gesamt grün. Commit.

### Task 8: `scripts/sim_eval_offline.py` — Offline-Eval auf den 4 Paaren (TDD)

**Files:**
- Create: `scripts/sim_eval_offline.py`, `tests/test_sim_embed.py` (oder eigenes Testfile)

**Interfaces:**
- `main(argv=None) -> int` — findet Paare `recordings/ab_*_blofeld.npy` ↔ `ab_*_iridium.npy` (und `check_*`) per Regex; für jedes Paar: Phase A + embed (ClapBackend aus `models/`, degrade falls fehlt) → Zeile (Paar, score, embed_score, combined); schreibt `recordings/phaseb_eval_<ts>.json` (Liste + Meta: Modelle, ts) und druckt Tabelle. `--ratings PATH` (JSON `{"<pair>": 0-100}`) → ergänzt Spearman-Rangkorrelation (eigene numpy-Implementierung mit Tie-Averaging, kein scipy) von score/embed_score/combined gegen Ratings in JSON + Tabelle.
- `spearman(a: list[float], b: list[float]) -> float` in sim_embed oder Skript (numpy).

- [ ] **Step 1:** Tests mit tmp recordings (2 synthetisierte Paare, Fake-Clap): `test_pairs_discovery` (blofeld/iridium gematcht), `test_eval_writes_json_and_table` (JSON-Struktur gepinnt), `test_spearman_perfect_and_inverse` (1.0 / −1.0, Ties ok), `test_ratings_optional`.
- [ ] **Step 2:** FAIL. **Step 3:** Implementierung. **Step 4:** PASS. Commit.

### Task 9: CLI + `ab`-Integration (TDD, alles gemockt)

**Files:**
- Modify: `bloridium/cli.py`, `bloridium/workflow.py`, `tests/test_cli.py`, `tests/test_scripts.py` (ggf. `tests/test_workflow.py` neu)

**Interfaces:**
- Neues Subcommand `bloridium sim compare --npy A B [--embed] [--llm] [--strict] [--models-dir D] [--log P]` und `--live [--note N] [--dur S] [--blofeld L] [--iridium-slot S] …` — dünner Wrapper um `sim_embed.score_pair_embed` (live: Aufnahme analog `sim_compare.run_live`, monophon Part 1 ch6, CC123/CC7-Regeln wie gehabt).
- `workflow.measure_ab(..., embed=False, llm=False, backends=None) -> dict` — report dict erhält zusätzlich Keys `"sim"` (Phase-A-Vergleich), `"embed"`, `"llm"` (oder `null` + `backend_error`); `log_path=None` (kein sim_log.jsonl-Doppel-Log; report.json + DB tragen es). **Keine Schema-Änderung**: `ab_runs.report_json` ist JSON-Blob.
- `cmd_ab` bekommt `--embed/--llm/--strict` und reicht an `measure_ab` durch.

- [ ] **Step 1:** Tests: `test_sim_compare_npy_cli` (monkeypatch backends, tmp npy), `test_ab_report_has_sim_embed_keys` (measure_ab mit gemocktem midi/audio + Fake-Clap → report["embed"]["embed_score"] gesetzt, report_json-Roundtrip via `db.log_ab_run` + `db.ab_runs`), `test_ab_legacy_report_without_keys_still_readable` (alte DB-Row ohne sim/embed Keys → `db` liest ok), `test_ab_embed_off_by_default` (ohne Flag keine embed-Keys → Rückwärtskompatibilität).
- [ ] **Step 2:** FAIL. **Step 3:** Implementierung. **Step 4:** `python3 -m pytest tests/ -q` gesamt grün. Commit.

### Task 10: Eval ausführen + Doku-Template (braucht Task 1–5, echte Modelle)

**Files:**
- Create: `docs/PHASEB-EVAL-2026-11-14.md`
- Create: `recordings/phaseb_eval_<ts>.json` (Output des Skripts)

- [ ] **Step 1:** `python3 scripts/fetch_models.py` (Modelle holen), dann `python3 scripts/sim_eval_offline.py` → Tabelle + JSON.
- [ ] **Step 2:** `docs/PHASEB-EVAL-2026-11-14.md` anlegen: Tabelle (Paar, Phase A, embed_score, combined), Spike-Modus (audio/spec), Modelle/Pfade, **leere Bewertungs-Tabelle** (Paar × 0–100 Höreindruck) für den Benutzer + Post-hoc-Caveat + Platz für Spearman (`--ratings`).
- [ ] **Step 3:** Commit (Doku + eval-JSON; keine Modelle).

---

## Self-Review (Checkliste gegen Spec)

1. **Spec-Coverage:** Embedding-Score (T3/T5), LLM-Urteil (T4/T5), combined 50/50 (T5), JSONL-Log (T5), degrade/strict (T5/T7), whole-clip CLAP-Input (T3), PNG-Fallback (T4, Modus aus T1), fetch_models (T6), sim_compare flags (T7), eval offline + post-hoc ratings (T8/T10), CLI `sim compare --npy/--live` (T9), `ab`/`measure_ab` mit report-Keys ohne Schema-Wechsel (T9), `models/` gitignored (T6), kein MLX, ROCm-Pfad via subprocess/HTTP (T1/T3/T4). ✅ alle Spec-Punkte haben einen Task.
2. **Step-Scan:** Jeder Step hat genau ein prüfbares Ergebnis (Testname+Assertions, pytest-Kommando, erwartetes FAIL/PASS, Commit). Keine "TBD".
3. **Typ-Konsistenz:** `ClapBackend.embed(x, sr) -> np.ndarray`, `OllamaBackend.judge(x_a, x_b, sr, prompt) -> dict`, `score_pair_embed(...) -> dict` in T3–T5 und T7–T9 identisch verwendet. `write_wav`/`render_spec_png` aus T2 werden in T3/T4 konsumiert. ✅
4. **Review Focus:** 5 Punkte oben, jeweils mit Test in Task 5/7/3/4/9 verankert. ✅
5. **Proportion:** Plan ~ so lang wie Spec; Code-Blöcke nur Test-Assertions/Skizzen, keine Transkripte. ✅
