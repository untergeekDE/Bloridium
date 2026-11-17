# Spec: Bloridium Web-App (Upload -> Konvertieren -> ZIP + Match-Schaetzung)

Datum: 2026-11-17

## Intent
Kleine Web-App, die im Podman-Container auf einem Debian-Server laeuft
(Update 2026-11-17: Podman statt Docker – `Containerfile`, `compose.yaml`, Quadlet):
Blofeld-Midi-Dump (`.syx`-Bank-Backup wie `bank-a-2019-06-17.syx`, alternativ
einzelner SNDD als `.bin`/`.hex`) hochladen, offline in Iridium-`.qpat`
konvertieren, als ZIP zum Download anbieten (stick-freundliche Namen
`<LOC>_<Name>.qpat`) und pro Sound eine Schaetzung, wie gut er matcht
(Score 0-100).

## Why
Die Konvertierung (`bloridium`-Offline-Pfad) soll ohne Mac/MIDI-Hardware vom
Server aus nutzbar sein. Die Match-Schaetzung ist ein **deterministischer
Platzhalter (v0)** – die echte Matching-Funktion konstruieren wir spaeter
aus den Ergebnissen der A/B-Vergleiche (`recordings/sim_log.jsonl`). Deshalb
legt die App pro Sound einen Feature-Vektor (geparste Parameter + Conversion-
Stats) in `report.json` ab – das ist das spaetere Trainingsdatum.

## Goals
- Upload `.syx` (128 verkettete SNDD-Nachrichten, F0..F7), `.bin`, `.hex`
- Konvertierung identisch zu `workflow.convert_parsed` (qpat v14, Template
  `docs/refs/qpat/template_waveform.qpat`, Filter2State=Off etc. via qpat_map)
- ZIP-Download: ein `.qpat` pro Sound + `MANIFEST.md` + `report.json`
- Ergebnisseite: Tabelle Location/Name/Score/Unmapped + Download-Links
- Deterministische Score-Schaetzung 0-100, reproduzierbar, erklaerbar

## Non-Goals
- Kein Live-MIDI, kein Audio, keine DB im Container (keine mido/numpy/rtmidi-Abhaengigkeiten)
- Kein Lernen/ML in v0; Matching-Funktion ist Platzhalter
- Kein Multi-User/Auth (persoenlicher Server hinter eigenem Reverse Proxy)

## Constraints
- Versionierung (2026-11-17): Conversion-Tool **v0.3** (`convert.CONVERSION_VERSION`,
  UI-Titel wie webpage.pdf, `conversion_version` in report.json/MANIFEST),
  Similarity-Tool **v0.2** (`matching.SIMILARITY_VERSION`)
- UI wie `webpage.pdf` (Repo-Root): englische Copy, Titel/Upload-Formular/NOTE-Box/
  Footer, Hintergrundbild `bloridium-scaled.jpg` (webapp/static/)
- Container-Image basiert auf `python:3.12-slim-bookworm` (Debian), Build-Kontext = Repo-Root (`podman build -f webapp/Containerfile .`)
- Nur pure-python-Module aus `bloridium/` werden in den Container kopiert
  (`blofeld_dump.py`, `qpat.py`, `qpat_map.py`, `waldorf.py`) – `bloridium/__init__.py`
  importiert audio/midi (numpy/mido) und wird deshalb umgangen (Laden per Dateipfad)
- Upload-Limit 8 MB (groesster bekannter Dump ~456 KB); Artefakte unter `DATA_DIR/<token>/`
  mit TTL (Default 24 h)

## Approaches
1. **Flask + gunicorn, single-service** (gewaehlt): minimale Deps, passt zu
   "kleine Web-App", einfaches Dockerfile. Alternative FastAPI/uvicorn waere
   gleichwertig, aber schwerer; reine stdlib-HTTP waere unkomfortabler (Upload,
   ZIP-Download, Templates).
2. **Ganzen `bloridium/`-Package + numpy/mido ins Image** (verworfen):
   python-rtmidi braucht ALSA-Dev-Header im Debian-Build, Image wird gross,
   obwohl die Web-App keine Hardware braucht.
3. **Matching: gelerntes Modell sofort** (verworfen, per Request):
   deterministischer Platzhalter jetzt, Lernen spaeter aus Vergleichen.

## Design (kurz)
- `webapp/app.py` – Flask-App: `GET /` (Formular), `POST /upload`,
  `GET /download/<token>` (ZIP), `GET /report/<token>` (JSON), `GET /health`
- `webapp/convert.py` – Upload parsen (SysEx-Split F0..F7, SNDD via
  `blofeld_dump.parse_sndd`, Location aus BB/NN), pro Sound konvertieren
  (qpat_map + qpat.build_qpat, v14), ZIP + report.json bauen
- `webapp/matching.py` – `estimate_match(parsed, unmapped, qpat_map)`:
  gewichtete Sub-Scores (Osc 30 %, Filter 25 %, FX 15 %, Env/Mod 20 %,
  Arp 10 %) ab obtenue Approximations-Abzuege; rein deterministisch
- `webapp/Containerfile`, `webapp/compose.yaml` (podman compose),
  `webapp/bloridium-web.container` (systemd-Quadlet), `webapp/requirements.txt`,
  `webapp/README.md`, `.containerignore`
- Tests: `tests/test_webapp.py` (Pipeline gegen echte Dumps, Flask-Testclient,
  Determinismus der Scores)

## Offene Punkte (Builder-Calls)
- Score-Gewichtung ist Placeholder-Heuristik, spaeter durch gelernte Funktion ersetzt
- ZIP-Name: `<LOC>_<Name>.qpat` (stick-freundlich lt. bloridium-Skill)
