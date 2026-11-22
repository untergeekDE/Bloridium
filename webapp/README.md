# Bloridium Web-App (Podman)

Small web app: **upload Blofeld MIDI dump -> convert to Iridium `.qpat` ->
download ZIP**, including a predicted match score (0-100) per sound
(RF prognosis when a model is available, deterministic placeholder otherwise).
Runs as a Podman container (e.g. on the Debian server).

## Deployment on the Debian server (Podman)

Build the image (build context is the repo root):

```bash
cd /path/to/Bloridium
podman build -f webapp/Containerfile -t localhost/bloridium-web:latest .
```

Then one of the two variants:

**A) systemd user unit (what runs on frankruft.de, rootless):**

Podman < 4.4 (e.g. Debian 12 ships 4.3.1) has no Quadlet support, so the
server uses a classic user unit that binds the container to `127.0.0.1:8000`
only; Apache publishes it as `https://bloridium.frankruft.de`.

```bash
cp webapp/bloridium-web.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now bloridium-web.service
# Update after a rebuild: systemctl --user restart bloridium-web.service
# Logs: journalctl --user -u bloridium-web.service
```

Reverse proxy (needs sudo, DNS A record first): see the header of
`webapp/deploy/bloridium.conf` (`a2enmod rewrite`, a2ensite +
`certbot --apache`). `mod_rewrite` is required for the truncated IP addresses
in the access/error logs.

**A') systemd Quadlet (Podman >= 4.4):** `webapp/bloridium-web.container`
into `~/.config/containers/systemd/`, then
`systemctl --user enable --now bloridium-web.service`.

**B) podman compose:**

```bash
podman compose -f webapp/compose.yaml up -d --build    # or podman-compose ...
```

**C) directly:**

```bash
podman run -d --name bloridium-web -p 8000:8000 \
  -v "$HOME/bloridium-web-data:/data" \
  -v "$PWD/models/prognose_rf.pkl:/app/models/prognose_rf.pkl:ro" \
  -e BLORIDIUM_MODEL=/app/models/prognose_rf.pkl \
  localhost/bloridium-web:latest
```

The RF model (`models/prognose_rf.pkl`) is git-tracked and **baked into** the image
at `/app/models/`. The mount above (and the `models` volume in compose.yaml / Quadlet)
is only needed to override it with a newer model. Without any model the app falls back
to the deterministic placeholder.

App reachable at `http://<server>:8000` (healthcheck: `GET /health`;
with variant A the unit passes `--health-cmd`, the Quadlet uses `HealthCmd`,
`podman healthcheck bloridium-web`). Note: Podman ignores the `HEALTHCHECK`
from the image (OCI format) – if you want it in the image, build with
`podman build --format docker ...`.

## Usage

1. Open `http://<server>:8000` (layout like `webpage.pdf`, background
   `bloridium-scaled.jpg` from `webapp/static/`)
2. Upload a `.syx` bank backup (e.g. `bank-a-2019-06-17.syx` from the SysEx
   backups – 128 SNDD messages; a single sound also works as `.bin`/`.hex`;
   a `.mid` MIDI file works too – its SysEx events are extracted from the
   track data, notes/meta are skipped, e.g. `Voltage-Bank-C.mid`)
3. The results page shows per sound: location, name, **predicted score** (RF
   prognosis ± std, or placeholder), count of parameters **not in the MIDI map**
   (hover the number for the list; the old separate "mapped" column was removed
   2026-11-21 — the count alone was confusing)
4. **One-time ZIP download**: one `<LOC>_<Name>.qpat` per sound + `MANIFEST.md`
   + `report.json` (inside the ZIP). The files are deleted from the server after
   the download, at the latest after one hour.
   - On the Iridium: USB stick/SD -> `Load > Actions > Import` (Favorites Bank 6,
     then `CC0=6` + PC; mido PC = MIDI number - 2)

## Versioning

One version for the whole project: `__version__` in `bloridium/version.py`
(currently 0.6.0). It is used for the package (`pyproject.toml`, `bloridium --version`),
the UI title "Bloridium Tool v…", and `conversion_version` / `similarity_version` in
`report.json` and `MANIFEST.md`. Which matcher produced the score is in `matcher`
(`rf-prognose-v…` or `deterministic-placeholder-v…`) and `model`.

## Score / conversion-quality prognosis

`webapp/matching.py` has two matchers:

- **rf-prognose** (active as soon as a model is found): the numpy-only random
  forest from `bloridium/prognose.py`, trained on the A/B measurements in
  `recordings/sim_log.jsonl` (target=score – see
  `docs/HANDOVER-2026-11-19-rf-dataset.md`; the shipped model has R² < 0 and was
  trained on the saturating v1 score, so treat it as a rough indication, see `FIXES_TODO.md`). Feature vector = the 367 SNDD bytes
  (without the name bytes) / 127 – computed directly from the upload, no dump file
  needed. Returns score 0-100 **plus the std over the trees** (± uncertainty).
- **deterministic-placeholder** (fallback without model): purely
  deterministic, weighted from osc/filter/FX/env-mod/arp with deductions for
  approximations (wavetable without bridge, BP/Notch/Comb, triple FX, arp).

Model path: `BLORIDIUM_MODEL` (default: auto-detect – `models/prognose_rf.pkl` in
the repo, `/app/models/prognose_rf.pkl` in the container – baked in, overridable by a mount).

Uploads are **not stored and not used for training**. The RF model was trained
on the operator's own A/B measurements, not on user uploads. `report.json`
contains only the per-sound result data needed for the download.

## Privacy, retention, logging

The public instance serves `/privacy`. The short version:

- The uploaded file is processed in memory and never written to disk.
- The generated ZIP/`report.json` is kept only for the one-time download and
  deleted immediately afterwards; if it is never downloaded, the background
  cleanup deletes it after `DATA_TTL_HOURS=1`.
- Uploads are not used for training.
- There are no cookies, analytics, or third-party assets.

The Apache vhost (`deploy/bloridium.conf`) truncates the client address in
**both** the access and error logs (`192.0.2.xxx`, `2001:db8::xxxx`) using
`mod_rewrite`; `sudo a2enmod rewrite` is required. Log retention is controlled
by Apache logrotate and journald, not by the app. The Flask app itself logs no
request data.

## Local development (without container)

```bash
pip install -r webapp/requirements.txt
python3 webapp/app.py        # http://localhost:8000
python3 -m pytest tests/test_webapp.py -q
```

## Files

- `Containerfile` – image (python:3.12-slim-bookworm, gunicorn); `.containerignore`
  at the repo root keeps the build context small
- `compose.yaml` – `podman compose`
- `bloridium-web.service` – systemd user unit (rootless, Podman < 4.4)
- `bloridium-web.container` – systemd Quadlet (rootless, Podman >= 4.4)
- `deploy/bloridium.conf` – Apache reverse-proxy vhost for bloridium.frankruft.de
- `app.py` / `convert.py` / `matching.py` – the app

## Env variables

| Variable | Default | Meaning |
|---|---|---|
| `DATA_DIR` | `./data` or `/data` in the container | Artifacts (ZIP/report) per upload token |
| `DATA_TTL_HOURS` | `1` | Maximum retention if a download never happens |
| `CLEANUP_INTERVAL_S` | `30` | Cleanup sweep interval (background thread + request throttle) |
| `BLORIDIUM_CLEANUP_THREAD` | `1` | Set to `0` to disable the background cleanup thread (tests) |
| `MAX_UPLOAD_MB` | `8` | Upload limit |
| `PORT` | `8000` | local dev server only |
| `BLORIDIUM_CORE_DIR` | `/app/core` in the container | pure-python bloridium modules (incl. `prognose.py`) |
| `BLORIDIUM_TEMPLATE` | `/app/template_waveform.qpat` | qpat template |
| `BLORIDIUM_MODEL` | `/app/models/prognose_rf.pkl` (baked in) | RF model for the prognosis; if missing -> placeholder |
