# Bloridium Web-App (Podman)

Small web app: **upload Blofeld MIDI dump -> convert to Iridium `.qpat` ->
download ZIP**, including a deterministic match estimate (score 0-100) per sound.
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
`webapp/deploy/bloridium.conf` (a2ensite + `certbot --apache`).

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
  -v "$HOME/bloridium-web-data:/data" localhost/bloridium-web:latest
```

App reachable at `http://<server>:8000` (healthcheck: `GET /health`;
with variant A the unit passes `--health-cmd`, the Quadlet uses `HealthCmd`,
`podman healthcheck bloridium-web`). Note: Podman ignores the `HEALTHCHECK`
from the image (OCI format) – if you want it in the image, build with
`podman build --format docker ...`.

## Usage

1. Open `http://<server>:8000` (layout like `webpage.pdf`, background
   `bloridium-scaled.jpg` from `webapp/static/`)
2. Upload a `.syx` bank backup (e.g. `bank-a-2019-06-17.syx` from the SysEx
   backups – 128 SNDD messages; a single sound also works as `.bin`/`.hex`)
3. The results page shows per sound: location, name, **score** (placeholder),
   mapped/unmapped parameters
4. **ZIP download**: one `<LOC>_<Name>.qpat` per sound + `MANIFEST.md` + `report.json`
   - On the Iridium: USB stick/SD -> `Load > Actions > Import` (Favorites Bank 6,
     then `CC0=6` + PC; mido PC = MIDI number - 2)

## Versioning

- **Conversion tool: v0.3** (`convert.CONVERSION_VERSION`) – UI title
  "Bloridium Tool v0.3", `conversion_version` in `report.json` and `MANIFEST.md`
- **Similarity tool: v0.2** (`matching.SIMILARITY_VERSION`) – `similarity_version`
  in `report.json`, score note on the results page

## Match estimate

`webapp/matching.py` (`estimate_match`) is a **deterministic placeholder v0.2**:
same dump -> same score, weighted from osc/filter/FX/env-mod/arp with
deductions for approximations (wavetable without bridge, BP/Notch/Comb, triple FX, arp).
We will construct the real matching function later from the A/B comparisons
(`recordings/sim_log.jsonl`) – that's why the feature vector
(parsed parameters, unmapped, mapped) lands in `report.json` in the ZIP per sound.

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
| `DATA_TTL_HOURS` | `24` | Retention of the artifacts |
| `MAX_UPLOAD_MB` | `8` | Upload limit |
| `PORT` | `8000` | local dev server only |
| `BLORIDIUM_CORE_DIR` | `/app/core` in the container | pure-python bloridium modules |
| `BLORIDIUM_TEMPLATE` | `/app/template_waveform.qpat` | qpat template |
