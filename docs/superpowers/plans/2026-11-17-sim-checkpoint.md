# sim_checkpoint.py (Checkpoint: 9 Presets × 4 Noten × Wheel 0/50/100 %) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Neues `scripts/sim_checkpoint.py`: ein Durchlauf misst alle 9 Presets aus `DEFAULT_MAP` im Manual-Panel-Modus, je Preset 4 Noten (Default 36,48,60,72 = C2–C5) × Wheel 0/50/100 % (12 Messungen, 108 gesamt), loggt Phase A + CLAP-embed (+ combined) pro Kombination nach `recordings/sim_log.jsonl`, WAVs pegel-angeglichen, llm/d1-Profil nur an Referenz-Kombination (Wheel 0 + Note 72), mit Panel-Prompt pro Preset, Wheel-Reset nach jedem Preset und Summary-Pivot am Ende.

**Architecture:** Dünner Checkpoint-Runner, der `measure()`/`set_wheel()` aus `scripts/sim_manual_compare.py` und `DEFAULT_MAP` aus `scripts/sim_sweep_pcs.py` importiert (kein Duplikat); Messung/Logging/WAV identisch zu `sim_manual_compare.main` via `sim_embed.score_pair_embed`. Keine Änderungen an bestehenden Skripten.

**Tech Stack:** Python 3.10, macOS; numpy-only Kern; mido/python-rtmidi (bestehend); pytest>=8; Tests offline via monkeypatch (kein Live-MIDI, keine Modelle).

**Spec:** `docs/superpowers/specs/2026-11-17-sim-checkpoint-design.md` (genehmigt 2026-11-17: Noten 36/48/60/72, Pfad A)

## Global Constraints

- Python 3.10, macOS; keine neuen Runtime-Dependencies; Kern bleibt numpy-only.
- Tests offline: `midi.connect`, `audio.record`, `time.sleep`, `builtins.input` und Backends werden gemockt (monkeypatch) — Muster siehe `test_sim_manual_compare_wheel_sweep` in `tests/test_scripts.py`. Kein Live-MIDI, kein Modell-Download.
- Degrade-Regel von `sim_embed.score_pair_embed` gilt unverändert (Backend fehlt → Felder `null` + `backend_error`, kein Crash).
- Eherne Mess-Regeln (aus `measure()`, wird nur importiert): nur Iridium ch6 (Part 1) monophon; vor jeder Messung CC123=0 auf allen 16 Kanaelen beider Synths, CC7=127 nur am Blofeld (am Iridium ist CC7 = Filter1 Amount!).
- WAV-Namen konsistent zu `sim_manual_compare.py`: `ab_<LOC>_<ts>_n<note>_w<pct:.0f>_{blo,irr}.wav` im `--wav-dir` (Default `recordings/`), pegel-angeglichen auf Peak 0.5 falls `norm_pegel` aktiv.
- Log: ein JSONL-Eintrag pro (Preset, Note, Wheel) in `--log` (Default `sim.DEFAULT_LOG`), `meta = {"mode": "checkpoint", "blofeld", "blofeld_pc", "irr_pc", "bank": 6, "note", "wheel_pct"}`.
- Doku/Commit-Messages auf Deutsch. Tests: `python3 -m pytest tests/ -q`.

## Review Focus

1. **Stumme Messung darf den Checkpoint nicht abbrechen** → score None wird geloggt (verdict „fehler"), Warnung, weiter; Exit 1 erst am Ende. (Task 1, Test c)
2. **Wheel-Reset nach jedem Preset** → CC1 auf Blofeld ch4 UND Iridium ch5 endet pro Preset mit 0: Sequenz [0, 64, 127, 0]. (Task 1, Test a)
3. **llm/profile nur an Referenz-Kombination** → `use_llm`/profile nur bei wheel_pct == erste Stufe UND note == ref_note (72 falls in --notes, sonst letzte Note); bei 9 Presets genau 9 volle Calls. (Task 1, Test b)
4. **Log-Schema stabil** → jede Zeile hat exakt die Meta-Keys {mode, blofeld, blofeld_pc, irr_pc, bank, note, wheel_pct}; 108 Zeilen bei vollem Lauf. (Task 1, Test b)
5. **Panel-Prompt im Test/Non-interactive überspringbar** → `input()` wird 9× gerufen, mit `--no-wait` 0×. (Task 1, Test d)

---

### Task 1: `scripts/sim_checkpoint.py` + Tests (TDD)

**Files:**
- Create: `scripts/sim_checkpoint.py`
- Create: `tests/test_sim_checkpoint.py`

**Interfaces:**
- Consumes: `sim_manual_compare.measure(blo, irr, note, dur) -> (bx, ix)`, `sim_manual_compare.set_wheel(blo, irr, pct) -> int`, `sim_sweep_pcs.DEFAULT_MAP: dict[str, int]`, `sim_embed.build_backends(models_dir, want_embed, want_llm) -> (clap, ollama)`, `sim_embed.build_profile_backend(want, model)`, `sim_embed.score_pair_embed(bx, ix, sr, meta, log_path, clap, ollama, use_llm, norm_pegel, profile_backend) -> dict`, `sim_embed.peak_dbfs/write_wav/print_result`, `sim.DEFAULT_LOG`, `audio.SAMPLERATE/CHANNELS`, `midi.connect`.
- Produces: `main(argv=None) -> int` (0 = alle Messungen ok, 1 = mind. ein score None); CLI-Flags: `--only LOC`, `--irr-pc` (nur mit `--only`, Default aus `DEFAULT_MAP[loc]`), `--notes` (Default `"36,48,60,72"`), `--wheel` (Default `"0,50,100"`), `--dur` (Default 2.0), `--log`, `--wav-dir`, `--no-embed`, `--no-llm`, `--no-norm-pegel`, `--profile`, `--d1-model`, `--models-dir`, `--full-all`, `--no-wait`.

- [ ] **Step 1: Tests schreiben** in `tests/test_sim_checkpoint.py` (FakeSynth/FakeRecord wie in `test_scripts.py`, `monkeypatch.setattr(time, "sleep", lambda s: None)`, `monkeypatch.setattr("builtins.input", lambda *a: "")`, `monkeypatch.setattr(midi, "connect", ...)`, `monkeypatch.setattr(audio, "record", fake_record)`; `sys.path.insert(0, str(repo / "scripts"))`):
  - a) `test_checkpoint_only_a001_defaults`: `main(["--only", "A001", "--irr-pc", "108", "--no-embed", "--no-llm", "--log", str(log), "--wav-dir", str(tmp_path)])` → rc 0; 12 Log-Zeilen; Meta-Key-Menge exakt `{"mode","blofeld","blofeld_pc","irr_pc","bank","note","wheel_pct"}` mit `mode=="checkpoint"`, `note` in {36,48,60,72}, `wheel_pct` in {0.0,50.0,100.0}; CC1-Werte auf ch4 und ch5 == `[0, 64, 127, 0]`; 24 WAVs in tmp_path mit Muster `ab_A001_*_n36_w0_blo.wav` … `n72_w100_irr.wav`; `capsys` enthaelt `"A001"` und `"n36"` (Summary).
  - b) `test_checkpoint_all_presets_llm_only_ref`: ohne `--only`, `sim_embed.build_backends` auf `(None, None)` patchen, `sim_embed.score_pair_embed` auf Fake patchen, der `(meta, use_llm)` sammelt und `{"score": 90.0, "embed_score": 80.0, "combined": 85.0, "verdict": "nahe", "peak_dbfs": None}` liefert → 108 Log-Zeilen (9 Presets × 12); `input` 9× gerufen; `use_llm==True` genau 9× und nur bei `wheel_pct==0.0 and note==72`; Meta `blofeld` deckt alle 9 Keys von `DEFAULT_MAP` ab.
  - c) `test_checkpoint_stumm_weiter_exit1`: Fake `score_pair_embed` liefert fuer `(A001, note 36, wheel 0)` `{"score": None, "verdict": "fehler", ...}`, sonst score 90 → rc 1; fehler-Zeile ist im Log; danachliegende Kombinationen trotzdem geloggt (Zeilen > 1).
  - d) `test_checkpoint_no_wait_and_overrides`: `main(["--only", "A008", "--notes", "60,72", "--wheel", "0", "--no-wait", ...])` mit input auf eine Funktion patchen, die Assertion feuert wenn gerufen → rc 0; 2 Log-Zeilen mit notes {60, 72}, wheel_pct {0.0}.
- [ ] **Step 2:** `python3 -m pytest tests/test_sim_checkpoint.py -q` → FAIL (Modul `sim_checkpoint` fehlt).
- [ ] **Step 3:** Implementiere `scripts/sim_checkpoint.py`: sys.path-Setup wie andere Skripte; Imports (`from sim_manual_compare import measure, set_wheel`, `from sim_sweep_pcs import DEFAULT_MAP`, `from bloridium import audio, midi, sim, sim_embed`); `main(argv=None) -> int` mit argparse-Flags oben; Backends einmal vor der Schleife; pro Preset: Blofeld CC0=0/CC32=0/PC=`int(loc[1:])-1`, `if not args.no_wait: input(f"== {loc}: bitte am Iridium Favorites Set 6 PC{irr_pc} einstellen, Enter bestaetigen ==")`, `wheel_pcts`/`notes` parsen, `ref_note = 72 if 72 in notes else notes[-1]`; `for pct in wheel_pcts: set_wheel(blo, irr, pct); for note in notes:` measure → WAVs (norm_pegel wie in sim_manual_compare, Namen `ab_{loc}_{ts}_n{note}_w{pct:.0f}_{blo,irr}.wav`) → `full = args.full_all or (pct == wheel_pcts[0] and note == ref_note)` → `score_pair_embed(..., meta={"mode":"checkpoint", ...}, use_llm=not args.no_llm and full, norm_pegel=not args.no_norm_pegel, profile_backend=d1 if full else None)` → `print_result` + peak-Zeile; `summary[(loc, note)][pct] = (score, embed_score, combined)`; Fehler zaehlen (`r["score"] is None`); nach jedem Preset `set_wheel(blo, irr, 0.0)`; am Ende Summary-Pivot printen (`f"{loc} n{note}: " + " ".join(f"w{int(p)}={c}" …)`); `finally: blo.close(); irr.close()`; return 1 falls Fehler sonst 0. Einziger ts pro Lauf (`datetime.now()` am Start).
- [ ] **Step 4:** `python3 -m pytest tests/test_sim_checkpoint.py -q` → PASS.
- [ ] **Step 5:** Commit: `git add scripts/sim_checkpoint.py tests/test_sim_checkpoint.py && git commit -m "feat: sim_checkpoint.py – Checkpoint 9 Presets × 4 Noten × Wheel 0/50/100 (TDD)"`.

### Task 2: Gesamt-Suite grün

**Files:**
- Modify: keine (nur Verifikation); ggf. kleine Fixes in `tests/test_sim_checkpoint.py`.

- [ ] **Step 1:** `python3 -m pytest tests/ -q` → alle Tests PASS (inkl. bestehender `test_sim_manual_compare_wheel_sweep` — darf durch den Import nicht brechen).
- [ ] **Step 2:** Falls Rot: minimalste Fixes, bis Suite gruen; keine Refactors.
- [ ] **Step 3:** Commit (nur falls geaendert): `git commit -am "test: sim_checkpoint – Suite grün"`.

### Task 3: Doku

**Files:**
- Modify: `docs/STATUS.md` (Abschnitt 4 Scripts: Eintrag für `sim_checkpoint.py` mit Aufruf-Beispiel)

- [ ] **Step 1:** `docs/STATUS.md` um einen Bullet ergaenzen: `sim_checkpoint.py [--only A001] [--notes 36,48,60,72] [--wheel 0,50,100] [--dur 2.0] [--full-all] [--no-wait]` – Checkpoint aller 9 Presets im Manual-Panel-Modus (Panel-Prompt pro Preset: Set 6 PC lt. DEFAULT_MAP), 12 Messungen/Preset, JSONL + WAVs wie `sim_manual_compare.py`, Summary-Pivot am Ende.
- [ ] **Step 2:** `python3 -m pytest tests/ -q` bleibt gruen (docs only, schnelle Rueckversicherung).
- [ ] **Step 3:** Commit: `git add docs/STATUS.md docs/superpowers/specs/2026-11-17-sim-checkpoint-design.md docs/superpowers/plans/2026-11-17-sim-checkpoint.md && git commit -m "docs: Spec+Plan sim_checkpoint + STATUS-Eintrag"`.
