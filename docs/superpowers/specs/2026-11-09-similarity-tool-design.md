# Design: Ähnlichkeits-Tool Blofeld ↔ Iridium (Ansatz A: Spektral + Hüllkurve)

Datum: 2026-11-09 · Status: Entwurf zur Genehmigung

## Intent & Why
Toolset, das eine erste Approximation eines Blofeld-Sounds auf den Iridium überträgt
(qpat-Konvertierung + Live-CCs). Das Ähnlichkeits-Tool schließt den Regelkreis:
Sound klingt nicht wie das Vorbild → messen wie sehr → Parameter drehen → erneut messen.

Vier Ziele (vom Human vorgegeben):
1. **Feedback an den Human** — wie sehr weicht der Iridium-Sound vom Blofeld-Vorbild ab?
2. **Verbesserung der Transfer-Skripte** — Score als objektive Metrik statt Ohr.
3. **LLM-gestützte Exploration** — systematisch an Parametern drehen, bis der Score steigt
   (braucht eine gute CC-Map: `docs/midi-maps/iridium_pid_map.csv` + `iridium_rdb.mimap`).
4. **Trainingsdaten für ein späteres Mapping-Modell** — jedes Messung als geloggter Datensatz.

## Goals / Non-goals / Anti-goals
- Goals: Score 0–100 + interpretierbare Abweichungen (pro Frequenzband, Hüllkurve);
  offline auf vorhandenen Takes UND live (CC ändern → messen); JSONL-Log pro Run.
- Non-goals (Phase A): ML-Embeddings (recherchiert parallel, spätere Phase B);
  mehrstimmige Sounds; Sample-basierte Oszillatoren.
- Anti-goals: kein "Ohr-Ersatz"-Anspruch, nur erste Approximation; kein Training in Phase A.

## Constraints
- macOS, Python 3.10, **numpy only in Phase A** (kein neues ML-Dependency).
- Aufnahme: `bloridium.audio.record` (ffmpeg/avfoundation, Scarlett 18i8, 48 kHz,
  Blofeld In 3/4 = ch (2,3), Iridium In 5/6 = ch (4,5)).
- MIDI: Blofeld + Iridium hängen am Launchpad Pro 3 DIN-Out (`bloridium/midi.py`,
  Blofeld ch5/idx4, Iridium Parts ch6-9/idx5-8). USB ist wegen Masseschleife abgehängt.
- Iridium-Patches nur per qpat-Import (Stick); CCs live steuerbar.
- Bestehende Artefakte: A/B-.npy-Takes (`spike_ab_compare.py`), `recordings/*.json`,
  `docs/refs/qpat_params_v14/v15`, `docs/midi-maps/iridium_pid_map.csv`.

## Approaches
- **A (gewählt): Spektral + Hüllkurve, numpy-only.** Log-magnitude-Spektrogramm
  (log-Bänder ~40 Hz–12 kHz) + RMS-Hüllkurve; Distanz = Cosine auf mittlerem
  Sustain-Spektrogramm + DTW auf der Hüllkurve; Score 0–100 gewichtet.
  Trade-off: weniger "semantisch" als Embeddings, dafür interpretierbar
  (pro-Band-dB → direktes Parameter-Feedback) und ohne Modell-Download.
- B: Audio-Embedding — **Recherche abgeschlossen** (Subagent, 2026-11-09). Top-Kandidaten
  (alle ≤ 4 GB, CPU-tauglich):
  - **LAION CLAP2-xxs/xs** ([HF laion/clap2-xxs-audioxl-s1B](https://huggingface.co/laion/clap2-xxs-audioxl-s1B), 109–200 MB, Apache-2.0, 224/320-d, 32 kHz, keine 10-s-Paddung → ideal für 1–2-s-Clips) — Empfehlung für Embedding-Score.
  - **MERT-v1-95M** ([HF m-a-p/MERT-v1-95M](https://huggingface.co/m-a-p/MERT-v1-95M), 378 MB, 768-d @ 24 kHz, rein musikalisch) — beste Timbre-Auflösung, aber **CC-BY-NC** (nur intern/experimentell).
  - **EnCodec 48 kHz** ([HF facebook/encodec_48khz](https://huggingface.co/facebook/encodec_48khz), 76 MB, MIT) — Encoder-Latent/Code-Histogramm als Timbre-Signatur (FAD-Ansatz), volle 48-kHz-Bandbreite.
  - 16-kHz-Modelle (VGGish, BEATs, wav2vec2, music2vec) wegen Synth-Oberwellen > 8 kHz nur als schnelle Referenz.
  - **Kombinationsprinzip (empfohlen):** neuronaler Embedding-Score (CLAP2) + klassische
    Features (log-mel/MFCC/Chroma/Centroid) = robuster Score + interpretierbare Deltas.
  Trade-off: Modell-Download, Score schwerer interpretierbar als reine Band-Deltas.
- C: reiner qpat-Parameter-Vergleich (kein Audio) — als schnelle Vorab-Prüfung
  ergänzt (cf. `docs/DONSOLARIS-COMPARE.md`), nicht als Ersatz.

## Design (Phase A)
Neues Modul `bloridium/sim.py`:
- `features(x, sr)` → `(log_spec [n_bands × n_frames], env_rms [n_frames], band_edges)`
  (FFT + Hann, log-spaced Bänder 40 Hz–12 kHz, ~50 ms Hop).
- `compare(feat_a, feat_b)` → `{"score": 0-100, "spec_cos": .., "env_dtw": ..,
  "band_delta_db": [...], "verdict": "nahe/mittel/weit"}`.
- Sustain-Fenster 0.5–1.2 s nach Note-On (Filter-Env verfälscht Attack — HANDOVER).
- `log_run(result, meta)` → `recordings/sim_log.jsonl` (features summary + score + meta:
  blofeld loc, iridium slot, CC-Zustände, timestamp) → Trainingsdaten für Ziel 4.

Skripte (konsistent zu `scripts/spike_*.py`):
- `scripts/sim_compare.py` — misst frisch (Note auf beiden Synths, Aufnahme, Vergleich)
  ODER wertet vorhandene .npy-Takes aus (`--npy dir`). Output: Score + Band-Deltas
  + JSONL-Log.
- `scripts/sim_live.py` — Dreh-Loop für Ziel 3: lädt CC-Map (`iridium_pid_map.csv`),
  nimmt Parameter-Name oder CC, setzt Wert am Iridium (ch6-9), misst, loggt.
  `--auto` später: LLM schlägt nächste Änderung vor.

CLI später: `bloridium sim compare ...` / `bloridium sim live ...` (Phase B).

CC-Map-Integration: `bloridium/ccmap.py` existiert (CSV-Namen → CC). Erweitern um
Pid-Spalte aus `iridium_pid_map.csv`, damit `sim_live` Parameternamen ↔ CC ↔ Pid kennt.

## Phase B (nach Phase A, optional)
- `bloridium/sim_embed.py`: optionaler Embedding-Score via CLAP2-xxs (HuggingFace, 109 MB,
  Apache-2.0) als zweiter Score; Kombination mit Phase-A-Score (gewichtet) im JSONL-Log.
- Nur wenn Lizenz ok: MERT-95M für feinere Timbre-Deltas (CC-BY-NC → nur intern).
- Embeddings landen ebenfalls im `sim_log.jsonl` → Features für Ziel 4 (Mapping-Modell).

## Was der Builder noch klären muss (Vorschläge = meine Calls)
- DTW-Implementierung: eigene kleine DP (numpy) statt scipy-Dependency → Call: eigene DP.
- Band-Anzahl: 48 log-Bänder → Call: 48.
- Score-Gewichtung: 70 % Spektrogramm-Cosine, 30 % Hüllkurve-DTW → Call: 70/30.
- JSONL-Pfad: `recordings/sim_log.jsonl` → Call: dort.

## Nächster Schritt nach Genehmigung
Plan via superpowers:writing-plans, dann TDD-Implementierung (test-sim.py zuerst).
