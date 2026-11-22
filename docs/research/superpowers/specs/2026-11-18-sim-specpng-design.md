# Design: optical spectrogram comparison (side-by-side PNG) per A/B pair

Date: 2026-11-18 · Status: approved for implementation ("build it in", user 2026-11-18)

## Intent & Why

`sim_embed.render_spec_png` already renders the log spectrogram as a PNG – so far only as
an `images` fallback for ollama. The **optical comparison** of the spectrograms of A and B
(Blofeld vs Iridium) is missing: after a checkpoint run (108 pairs) the human wants to see the
spectrograms side by side (A | B | Δ in dB), not only scores. Findings from
PHASEB-EVAL (band_dtw localizes 211-302 Hz etc.) show: the eye sees frequency bands
that the score averages away.

## Goals / Non-goals

- Goals:
  - `sim_embed.render_spec_pair_png(x_a, x_b, sr, path, db_span=20.0) -> Path`: one PNG,
    horizontal **A | B | Δ** (2 px separator), A/B as grayscale with a **shared**
    lo/hi (otherwise the normalization deceives), Δ = spec_b − spec_a in dB as a diverging
    color scale (blue = B quieter … red = B louder, ±`db_span` dB clipped, 0 = mid gray).
    Basis: `sim.features(...)["log_spec"]` (n_bands × n_frames, dB), x = time, y = band.
  - `score_pair_embed(..., spec_png_dir=None)`: renders the pair PNG on the
    **level-normalized** signals (`xe_blo`/`xe_irr` – otherwise Δ is only gain!),
    file name from meta (`spec_<blofeld>_n<note>_w<wheel>.png`, fallback `spec_pair.png`),
    `result["spec_png"] = str(path)` → lands automatically in the JSONL log.
    A render error does not kill the measurement (degrade: `spec_png=None` + `backend_error`
    extended by "spec_png: …"; `strict=True` → raise).
  - CLI: `scripts/sim_checkpoint.py` gets `--spec-png-dir` (default
    `recordings/spec/` – ON, that's the wish) and `--no-spec-png`;
    `scripts/sim_compare.py` gets `--spec-png-dir` (default None = opt-in, both
    modes `--npy`/`--live`). `print_result` prints the PNG path when set.
- Non-goals: no video/overlay in the PNG, no axis labels (PIL-only, compact),
  no upload to a model (that stays the existing spec fallback), no own delta "score".
- Anti-goals: the core stays numpy+PIL (no matplotlib in the production path); the PNG render
  must not change the existing log/score paths (only the additional field `spec_png`).

## Constraints

- Python 3.10, numpy + PIL (like `render_spec_png`); no new dependency.
- Different recording lengths: the shorter log_spec is padded on the right with its own
  min value (max n_frames) – analogous to `sim.compare`.
- Tests offline (no models, no MIDI): synthetic sine signals.
- German docs/commits; tests: `python3 -m pytest tests/ -q`.

## Approaches

- **A (chosen):** render in the central `score_pair_embed` (the only place that feeds all
  entrypoints – `sim compare`, `sim_checkpoint`, `ab`) with opt-in
  `spec_png_dir`; file name from meta. Advantage: one JSONL entry carries score + PNG path.
- **B (rejected):** render only in the scripts – then the path would be missing in the log and
  `bloridium sim compare`/`ab` would not get it.

## Design details

- `render_spec_pair_png`: `fa = sim.features(x_a, sr)`, `fb = sim.features(x_b, sr)`;
  pad to `n = max(frames)`; gray = `(spec - lo)/(hi - lo)*255` with lo/hi over both;
  delta_db = clip(spec_b − spec_a, −db_span, +db_span)/db_span in [−1,1]; LUT: negative →
  blue (0,0,255)→gray(128), positive → gray→red(255,0,0), 0 → (128,128,128);
  `np.stack([...], axis=-1)` uint8; concat horizontally with a 2 px white (255) separator;
  `Image.fromarray(img.transpose(1,0,2))` (width = time like `render_spec_png`).
- File name: from meta `blofeld`/`note`/`wheel_pct`/`mode` sanitized
  (`spec_{blofeld}_n{note}_w{wheel}.png`), else `spec_pair.png`; a collision with
  the same meta in the same run → suffix `_2`, `_3`, …
- `score_pair_embed`: parameter `spec_png_dir=None` (keyword-only); renders with
  `xe_blo`/`xe_irr`; try/except like the other backends.

## Tests (TDD)

- `tests/test_sim_embed.py`: `test_render_spec_pair_png` (valid PNG, width =
  3·n_frames + 2·2, height = n_bands; 220 vs 221 Hz → the delta panel varies; the same
  signal → the delta panel constant); `test_score_pair_embed_spec_png` (with dir: the file is there,
  `result["spec_png"]` set, the log entry contains it; without dir: `None`, no file;
  too short a signal → the ValueError from features is caught, `spec_png=None`,
  `backend_error` contains "spec_png", score ok).
- `tests/test_sim_checkpoint.py`: checkpoint with `--spec-png-dir tmp` → 12 PNGs +
  the log lines contain `spec_png`.
