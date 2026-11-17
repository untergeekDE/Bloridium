# Bloridium Web-App (Podman)

Kleine Web-App: **Blofeld-Midi-Dump hochladen → in Iridium-`.qpat` konvertieren →
ZIP herunterladen**, inkl. deterministischer Match-Schätzung (Score 0–100) pro Sound.
Läuft als Podman-Container (z. B. auf dem Debian-Server).

## Deployment auf dem Debian-Server (Podman)

Image bauen (Build-Kontext ist das Repo-Root):

```bash
cd /pfad/zum/Bloridium
podman build -f webapp/Containerfile -t localhost/bloridium-web:latest .
```

Dann eine der beiden Varianten:

**A) systemd-Quadlet (empfohlen auf dem Server, rootless):**

```bash
mkdir -p ~/.config/containers/systemd
cp webapp/bloridium-web.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user enable --now bloridium-web.container
# App: http://<server>:8000   Logs: journalctl --user -u bloridium-web.container
```

**B) podman compose:**

```bash
podman compose -f webapp/compose.yaml up -d --build    # bzw. podman-compose ...
```

**C) direkt:**

```bash
podman run -d --name bloridium-web -p 8000:8000 \
  -v "$HOME/bloridium-web-data:/data" localhost/bloridium-web:latest
```

App erreichbar unter `http://<server>:8000` (Healthcheck: `GET /health`;
bei Variante A uebernimmt das Quadlet den Healthcheck via `HealthCmd`,
`podman healthcheck bloridium-web`). Hinweis: Podman ignoriert das `HEALTHCHECK`
aus dem Image (OCI-Format) – wer es im Image haben moechte, baut mit
`podman build --format docker ...`.

## Benutzung

1. `http://<server>:8000` öffnen (Layout wie `webpage.pdf`, Hintergrund
   `bloridium-scaled.jpg` aus `webapp/static/`)
2. `.syx`-Bank-Backup hochladen (z. B. `bank-a-2019-06-17.syx` aus den Sysex
   Backups – 128 SNDD-Nachrichten; einzelner Sound geht auch als `.bin`/`.hex`)
3. Ergebnisseite zeigt pro Sound Location, Name, **Score** (Platzhalter),
   gemappte/unmapped Parameter
4. **ZIP-Download**: ein `<LOC>_<Name>.qpat` pro Sound + `MANIFEST.md` + `report.json`
   - Am Iridium: USB-Stick/SD → `Load > Actions > Import` (Favorites Bank 6,
     dann `CC0=6` + PC; mido-PC = MIDI-Nummer − 2)

## Versionierung

- **Conversion-Tool: v0.3** (`convert.CONVERSION_VERSION`) – UI-Titel
  „Bloridium Tool v0.3“, `conversion_version` in `report.json` und `MANIFEST.md`
- **Similarity-Tool: v0.2** (`matching.SIMILARITY_VERSION`) – `similarity_version`
  in `report.json`, Score-Hinweis auf der Ergebnisseite

## Matching-Schätzung

`webapp/matching.py` (`estimate_match`) ist ein **deterministischer Platzhalter v0.2**:
gleicher Dump → gleicher Score, gewichtet aus Osc/Filter/FX/Env-Mod/Arp mit
Abzügen für Näherungen (Wavetable ohne Bridge, BP/Notch/Comb, Triple FX, Arp).
Die echte Matching-Funktion konstruieren wir später aus den A/B-Vergleichen
(`recordings/sim_log.jsonl`) – deshalb landet pro Sound der Feature-Vektor
(geparste Parameter, unmapped, mapped) in `report.json` im ZIP.

## Lokal entwickeln (ohne Container)

```bash
pip install -r webapp/requirements.txt
python3 webapp/app.py        # http://localhost:8000
python3 -m pytest tests/test_webapp.py -q
```

## Dateien

- `Containerfile` – Image (python:3.12-slim-bookworm, gunicorn); `.containerignore`
  am Repo-Root hält Build-Kontext klein
- `compose.yaml` – `podman compose`
- `bloridium-web.container` – systemd-Quadlet (rootless)
- `app.py` / `convert.py` / `matching.py` – die App

## Env-Variablen

| Variable | Default | Bedeutung |
|---|---|---|
| `DATA_DIR` | `./data` bzw. `/data` im Container | Artefakte (ZIP/Report) je Upload-Token |
| `DATA_TTL_HOURS` | `24` | Aufbewahrung der Artefakte |
| `MAX_UPLOAD_MB` | `8` | Upload-Limit |
| `PORT` | `8000` | nur lokaler Dev-Server |
| `BLORIDIUM_CORE_DIR` | `/app/core` im Container | pure-python bloridium-Module |
| `BLORIDIUM_TEMPLATE` | `/app/template_waveform.qpat` | qpat-Template |
