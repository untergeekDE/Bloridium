# sim-specpng (Side-by-Side-Spektrogramm-PNG pro A/B-Paar) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jede A/B-Messung kann ein optisches Spektrogramm-Vergleichs-PNG (A | B | ΔdB) erzeugen, das im JSONL-Log verlinkt ist – zentral in `sim_embed.score_pair_embed` via `spec_png_dir`, verdrahtet in `sim_checkpoint.py` (default AN: `recordings/spec/`) und `sim_compare.py` (opt-in).

**Architecture:** `render_spec_pair_png` in `bloridium/sim_embed.py` (numpy+PIL, Basis `sim.features`), gemeinsames lo/hi für A/B, divergierende Δ-Skala ±20 dB; `score_pair_embed` rendert auf den pegel-normalisierten Signalen und setzt `result["spec_png"]`; Degrade-Regel wie andere Backends.

**Tech Stack:** Python 3.10; numpy + PIL (bereits Soft-Dep via `render_spec_png`); pytest>=8.

**Spec:** `docs/superpowers/specs/2026-11-18-sim-specpng-design.md`

## Global Constraints

- numpy + PIL only im Produktivpfad (kein matplotlib); keine neuen Dependencies.
- Tests offline, synthetische Signale, kein MIDI/Modell.
- Bestehendes Log-Schema bleibt: nur zusätzliches Feld `spec_png` im result (null wenn aus).
- Degrade: Render-Fehler → `spec_png=None` + `backend_error` um `spec_png: …`; `strict=True` → BackendError. Score/Log unverändert.
- Deutsche Doku/Commits. Tests: `python3 -m pytest tests/ -q`.

## Review Focus

1. **Δ-Panel darf keinen Pegel-Vergleich zeigen** → Rendern auf `xe_blo`/`xe_irr` (normiert), nicht Roh-Signal. (Task 1, Test: norm_pegel=True, unterschiedliche Gains → Δ ≈ 0)
2. **Unterschiedliche Längen** → pad auf max n_frames. (Task 1, Test mit 1.0 s vs 1.3 s)
3. **Gemeinsames lo/hi für A/B** → sonst täuscht Graustufen-Normierung. (Task 1, Test: A leiser als B, gleiche Form → A-Panel dunkler als B-Panel)
4. **Render-Fehler killt Messung nicht** → score ok, spec_png None, backend_error gesetzt. (Task 1)
5. **Dateiname kollisionsfrei** bei gleichem meta im selben Lauf. (Task 1, Test: zweimal gleicher meta → 2 Dateien)

---

### Task 1: `render_spec_pair_png` + `score_pair_embed(spec_png_dir=…)` (TDD)

**Files:**
- Modify: `bloridium/sim_embed.py`
- Modify: `tests/test_sim_embed.py`

**Interfaces:**
- Produces: `render_spec_pair_png(x_a, x_b, sr, path, db_span=20.0) -> Path`; `score_pair_embed(..., spec_png_dir=None)` setzt `result["spec_png"]: str | None` (auch im `_fehler_result`-Pfad als None – dort ohne Render).

- [ ] **Step 1:** Tests in `tests/test_sim_embed.py` schreiben:
  - `test_render_spec_pair_png_shape`: 1 s Sinus 220 vs 221 Hz @48 kHz, tmp path → PNG via PIL öffnen; Breite == 3·n_frames + 2·2 (Separator 2 px), Höhe == n_bands (48); Modus RGB.
  - `test_render_spec_pair_png_delta_varies_and_common_scale`: 220 Hz (0.3) vs 221 Hz (0.15) → Delta-Panel (rechte Drittel-Spalten) nicht konstant; A-Panel heller als B-Panel (gemeinsames lo/hi, A lauter). Gleiches Signal zweimal → Delta-Panel konstant (alle Pixel = 0-Mapping-Farbe).
  - `test_render_spec_pair_png_pads_lengths`: 1.0 s vs 1.3 s → kein Fehler, Breite auf max frames.
  - `test_score_pair_embed_spec_png_writes_and_logs`: zwei 1 s Sinus, `spec_png_dir=tmp`, `norm_pegel=False` → `result["spec_png"]` gesetzt, Datei existiert, JSONL-Zeile enthält `spec_png`; ohne `spec_png_dir` → `result["spec_png"] is None`, keine Datei.
  - `test_score_pair_embed_spec_png_uses_normed_signals`: A = 0.3·sin, B = 0.03·sin (10× leiser, gleiche Form), `norm_pegel=True`, spec_png_dir=tmp → Delta-Panel annähernd konstant (nach Norm ≈ gleich); Roh (norm_pegel=False) → Delta stark gefärbt. (Review-Focus 1)
  - `test_score_pair_embed_spec_png_degrade`: Signal < 0.2 s → features ValueError wird in score_pair_embed ohnehin gefangen (fehler-result); stattdessen: spec_png_dir gesetzt + normales Signal, aber `render_spec_pair_png` per monkeypatch auf raising patchen → `result["score"]` ok, `spec_png is None`, `backend_error` enthält "spec_png".
  - `test_spec_png_name_collision`: gleicher meta zweimal mit gleichem spec_png_dir → zwei verschiedene Dateien (`spec_pair.png`, `spec_pair_2.png` o. ä.).
- [ ] **Step 2:** `python3 -m pytest tests/test_sim_embed.py -q` → FAIL.
- [ ] **Step 3:** Implementieren in `bloridium/sim_embed.py`:
  - `render_spec_pair_png(x_a, x_b, sr, path, db_span=20.0) -> Path` (wie Spec: gemeinsames lo/hi, pad, LUT, Separator, `Image.fromarray(...transpose(1,0,2))`).
  - `_spec_png_name(meta, spec_png_dir) -> Path` (sanitize, Kollisions-Suffix).
  - `score_pair_embed(..., spec_png_dir=None)`: nach dem Phase-A-Teil (auch bei fehler-result: `spec_png=None` ins `_fehler_result` aufnehmen bzw. result.setdefault), mit try/except um `render_spec_pair_png(xe_blo, xe_irr, sr, path)`; Erfolg → `result["spec_png"]=str(path)`, Fehler → `result["spec_png"]=None` + `errors.append(f"spec_png: {e}")` (strict → BackendError). Rendern auf `xe_*`.
  - `print_result`: `if r.get("spec_png"): print(f"  spec_png: {r['spec_png']}")`.
- [ ] **Step 4:** `python3 -m pytest tests/test_sim_embed.py -q` → PASS.
- [ ] **Step 5:** Commit: `git add bloridium/sim_embed.py tests/test_sim_embed.py && git commit -m "feat(sim_embed): render_spec_pair_png (A|B|ΔdB) + score_pair_embed(spec_png_dir) – optischer Spektrogramm-Vergleich (TDD)"`.

### Task 2: CLI-Verdrahtung (TDD)

**Files:**
- Modify: `scripts/sim_checkpoint.py`, `scripts/sim_compare.py`
- Modify: `tests/test_sim_checkpoint.py`, `tests/test_sim_compare_embed.py`

- [ ] **Step 1:** Tests: `test_sim_checkpoint.py::test_checkpoint_spec_png_dir` – Lauf `--only A001 --no-embed --no-llm --no-wait --spec-png-dir tmp/spec` → rc 0, 12 PNGs in tmp/spec mit Namen `spec_A001_n*_w*.png`, jede Log-Zeile hat `result.spec_png` gesetzt. `test_sim_compare_embed.py`: sim_compare.main(["--npy", a, b, "--no-embed"... mit --spec-png-dir]) → PNG existiert + Log enthält spec_png; ohne Flag → spec_png None. (Pfade/Flags an bestehende Tests anpassen.)
- [ ] **Step 2:** pytest → FAIL.
- [ ] **Step 3:** Implementieren: `sim_checkpoint.py` um `--spec-png-dir` (Default `str(REPO/"recordings"/"spec")`) + `--no-spec-png` ergänzen, an `score_pair_embed(..., spec_png_dir=None if args.no_spec_png else args.spec_png_dir)` durchreichen; `sim_compare.py` um `--spec-png-dir` (Default None) ergänzen und in `_score_pair` durchreichen (`spec_png_dir=getattr(args, "spec_png_dir", None)`).
- [ ] **Step 4:** pytest beide Dateien → PASS.
- [ ] **Step 5:** Commit: `git commit -am "feat: --spec-png-dir in sim_checkpoint (default recordings/spec/) und sim_compare (opt-in)"`.

### Task 3: Suite + Doku

- [ ] **Step 1:** `python3 -m pytest tests/ -q` → alle PASS.
- [ ] **Step 2:** `docs/STATUS.md` ergänzen (sim_checkpoint: spec-PNGs in `recordings/spec/`, im Log verlinkt; sim_compare: `--spec-png-dir`).
- [ ] **Step 3:** Commit: `git add docs/STATUS.md docs/superpowers/specs/2026-11-18-sim-specpng-design.md docs/superpowers/plans/2026-11-18-sim-specpng.md && git commit -m "docs: Spec+Plan sim-specpng + STATUS-Eintrag"`.
