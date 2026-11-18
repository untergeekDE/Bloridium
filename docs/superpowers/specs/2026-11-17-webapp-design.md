# Spec: Bloridium web app (upload -> convert -> ZIP + match estimate)

Date: 2026-11-17

## Intent
Small web app that runs in a Podman container on a Debian server
(update 2026-11-17: Podman instead of Docker – `Containerfile`, `compose.yaml`, Quadlet):
upload a Blofeld MIDI dump (`.syx` bank backup like `bank-a-2019-06-17.syx`, alternatively
a single SNDD as `.bin`/`.hex`), convert offline to Iridium `.qpat`, offer it as a ZIP for
download (stick-friendly names `<LOC>_<Name>.qpat`) and give a per-sound estimate of how well
it matches (score 0-100).

## Why
The conversion (`bloridium` offline path) should be usable from the server without a Mac/MIDI
hardware. The match estimate is a **deterministic placeholder (v0)** – we will construct the
real matching function later from the results of the A/B comparisons (`recordings/sim_log.jsonl`).
That's why the app stores a feature vector (parsed parameters + conversion
stats) per sound in `report.json` – that is the later training datum.

## Goals
- Upload `.syx` (128 chained SNDD messages, F0..F7), `.bin`, `.hex`
- Conversion identical to `workflow.convert_parsed` (qpat v14, template
  `docs/refs/qpat/template_waveform.qpat`, Filter2State=Off etc. via qpat_map)
- ZIP download: one `.qpat` per sound + `MANIFEST.md` + `report.json`
- Results page: table location/name/score/unmapped + download links
- Deterministic score estimate 0-100, reproducible, explainable

## Non-Goals
- No live MIDI, no audio, no DB in the container (no mido/numpy/rtmidi dependencies)
- No learning/ML in v0; the matching function is a placeholder
- No multi-user/auth (personal server behind its own reverse proxy)

## Constraints
- Versioning (2026-11-17): conversion tool **v0.3** (`convert.CONVERSION_VERSION`,
  UI title like webpage.pdf, `conversion_version` in report.json/MANIFEST),
  similarity tool **v0.2** (`matching.SIMILARITY_VERSION`)
- UI like `webpage.pdf` (repo root): English copy, title/upload form/NOTE box/
  footer, background image `bloridium-scaled.jpg` (webapp/static/)
- Container image based on `python:3.12-slim-bookworm` (Debian), build context = repo root (`podman build -f webapp/Containerfile .`)
- Only the pure-python modules from `bloridium/` are copied into the container
  (`blofeld_dump.py`, `qpat.py`, `qpat_map.py`, `waldorf.py`) – `bloridium/__init__.py`
  imports audio/midi (numpy/mido) and is therefore bypassed (loading via file path)
- Upload limit 8 MB (largest known dump ~456 KB); artifacts under `DATA_DIR/<token>/`
  with TTL (default 24 h)

## Approaches
1. **Flask + gunicorn, single service** (chosen): minimal deps, fits
   "small web app", simple Dockerfile. Alternative FastAPI/uvicorn would be
   equivalent, but heavier; pure stdlib HTTP would be less comfortable (upload,
   ZIP download, templates).
2. **Whole `bloridium/` package + numpy/mido in the image** (rejected):
   python-rtmidi needs ALSA dev headers in the Debian build, the image gets big,
   although the web app needs no hardware.
3. **Matching: learned model right away** (rejected, per request):
   deterministic placeholder now, learning later from the comparisons.

## Design (short)
- `webapp/app.py` – Flask app: `GET /` (form), `POST /upload`,
  `GET /download/<token>` (ZIP), `GET /report/<token>` (JSON), `GET /health`
- `webapp/convert.py` – parse the upload (SysEx split F0..F7, SNDD via
  `blofeld_dump.parse_sndd`, location from BB/NN), convert per sound
  (qpat_map + qpat.build_qpat, v14), build the ZIP + report.json
- `webapp/matching.py` – `estimate_match(parsed, unmapped, qpat_map)`:
  weighted sub-scores (Osc 30 %, Filter 25 %, FX 15 %, Env/Mod 20 %,
  Arp 10 %) minus deductions for approximations; purely deterministic
- `webapp/Containerfile`, `webapp/compose.yaml` (podman compose),
  `webapp/bloridium-web.container` (systemd Quadlet), `webapp/requirements.txt`,
  `webapp/README.md`, `.containerignore`
- Tests: `tests/test_webapp.py` (pipeline against real dumps, Flask test client,
  determinism of the scores)

## Open points (builder calls)
- The score weighting is a placeholder heuristic, replaced later by a learned function
- ZIP name: `<LOC>_<Name>.qpat` (stick-friendly per the bloridium skill)
