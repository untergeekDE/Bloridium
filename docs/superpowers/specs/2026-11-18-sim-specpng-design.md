# Design: optischer Spektrogramm-Vergleich (Side-by-Side-PNG) pro A/B-Paar

Datum: 2026-11-18 · Status: zur Umsetzung freigegeben („bau das ein“, Benutzer 2026-11-18)

## Intent & Why

`sim_embed.render_spec_png` rendert das Log-Spektrogramm schon als PNG – bisher nur als
`images`-Fallback für ollama. Der **optische Vergleich** der Spektrogramme von A und B
(Blofeld vs Iridium) fehlt: nach einem Checkpoint-Lauf (108 Paare) will der Mensch die
Spektrogramme nebeneinander sehen (A | B | Δ in dB), nicht nur Scores. Befunde aus
PHASEB-EVAL (band_dtw lokalisiert 211–302 Hz etc.) zeigen: das Auge sieht Frequenzbänder,
die der Score mittelt.

## Goals / Non-goals

- Goals:
  - `sim_embed.render_spec_pair_png(x_a, x_b, sr, path, db_span=20.0) -> Path`: ein PNG,
    horizontal **A | B | Δ** (2 px Separator), A/B als Graustufen mit **gemeinsamem**
    lo/hi (sonst täuscht die Normierung), Δ = spec_b − spec_a in dB als divergierende
    Farbskala (blau = B leiser … rot = B lauter, ±`db_span` dB geclippt, 0 = mittelgrau).
    Basis: `sim.features(...)["log_spec"]` (n_bands × n_frames, dB), x = Zeit, y = Band.
  - `score_pair_embed(..., spec_png_dir=None)`: rendert das Paar-PNG auf den
    **pegel-normalisierten** Signalen (`xe_blo`/`xe_irr` – sonst ist Δ nur Gain!),
    Dateiname aus meta (`spec_<blofeld>_n<note>_w<wheel>.png`, Fallback `spec_pair.png`),
    `result["spec_png"] = str(path)` → landet automatisch im JSONL-Log.
    Render-Fehler killt die Messung nicht (Degrade: `spec_png=None` + `backend_error`
    um "spec_png: …" ergänzt; `strict=True` → raise).
  - CLI: `scripts/sim_checkpoint.py` bekommt `--spec-png-dir` (Default
    `recordings/spec/` – AN, das ist der Wunsch) und `--no-spec-png`;
    `scripts/sim_compare.py` bekommt `--spec-png-dir` (Default None = opt-in, beide
    Modi `--npy`/`--live`). `print_result` druckt den PNG-Pfad, wenn gesetzt.
- Non-goals: kein Video/Overlay im PNG, keine Achsenbeschriftung (PIL-only, kompakt),
  kein Upload an ein Modell (das bleibt der bestehende spec-Fallback), kein eigenes
  Delta-"Score".
- Anti-goals: Kern bleibt numpy+PIL (kein matplotlib im Produktivpfad); PNG-Render
  darf bestehende Log-/Score-Pfade nicht verändern (nur zusätzliches Feld `spec_png`).

## Constraints

- Python 3.10, numpy + PIL (wie `render_spec_png`); kein neues Dependency.
- Unterschiedliche Aufnahmelängen: kürzeres log_spec wird rechts mit seinem eigenen
  min-Wert gepadet (max n_frames) – analog zu `sim.compare`.
- Tests offline (keine Modelle, kein MIDI): synthetische Sinus-Signale.
- Deutsche Doku/Commits; Tests: `python3 -m pytest tests/ -q`.

## Approaches

- **A (gewählt):** Rendern im zentralen `score_pair_embed` (einzige Stelle, die alle
  Entrypoints – `sim compare`, `sim_checkpoint`, `ab` – speist) mit opt-in
  `spec_png_dir`; Dateiname aus meta. Vorteil: ein JSONL-Eintrag trägt Score + PNG-Pfad.
- **B (abgelehnt):** nur in den Skripten rendern – dann fehlt der Pfad im Log und
  `bloridium sim compare`/`ab` bekämen es nicht.

## Design-Details

- `render_spec_pair_png`: `fa = sim.features(x_a, sr)`, `fb = sim.features(x_b, sr)`;
  pad auf `n = max(frames)`; grau = `(spec - lo)/(hi - lo)*255` mit `lo/hi` über beide;
  delta_db = clip(spec_b − spec_a, −db_span, +db_span)/db_span in [−1,1]; LUT: negativ →
  blau (0,0,255)→grau(128), positiv → grau→rot(255,0,0), 0 → (128,128,128);
  `np.stack([...], axis=-1)` uint8; concat horizontal mit 2 px weiß (255) Separator;
  `Image.fromarray(img.transpose(1,0,2))` (Breite = Zeit wie `render_spec_png`).
- Dateiname: aus meta `blofeld`/`note`/`wheel_pct`/`mode` sanitized
  (`spec_{blofeld}_n{note}_w{wheel}.png`), sonst `spec_pair.png`; Kollision bei
  gleichem meta im selben Lauf → Suffix `_2`, `_3`, …
- `score_pair_embed`: Parameter `spec_png_dir=None` (keyword-only); rendert mit
  `xe_blo`/`xe_irr`; try/except wie andere Backends.

## Tests (TDD)

- `tests/test_sim_embed.py`: `test_render_spec_pair_png` (valides PNG, Breite =
  3·n_frames + 2·2, Höhe = n_bands; 220 vs 221 Hz → Delta-Panel variiert; gleiches
  Signal → Delta-Panel konstant); `test_score_pair_embed_spec_png` (mit dir: Datei da,
  `result["spec_png"]` gesetzt, Log-Eintrag enthält es; ohne dir: `None`, keine Datei;
  zu kurzes Signal → ValueError von features wird gefangen, `spec_png=None`,
  `backend_error` enthält "spec_png", score ok).
- `tests/test_sim_checkpoint.py`: Checkpoint mit `--spec-png-dir tmp` → 12 PNGs +
  Log-Zeilen enthalten `spec_png`.
