# Design: Phase B – modellbasierter Sound-Vergleich (Embedding-Score + LLM-Urteil)

Datum: 2026-11-14 · Status: Entwurf zur Genehmigung

## Intent & Why

Phase A (`bloridium/sim.py`, numpy-only: 70 % Spektrogramm-Cosine + 30 % Hüllkurven-DTW)
liefert eine mechanische Zahl, aber keinen Eindruck vom *Charakter* eines Sounds –
beobachtet: Blofeld↔Iridium-Scores 93–97, obwohl der Klang „oft sehr anders" ist
(HANDOVER-2026-11-09, Offen Punkt 5). Phase B ergänzt zwei modellbasierte Komponenten:

1. **Embedding-Score (numerisch, hart):** CLAP (musik-trainiert) als GGUF via clap.cpp
   (llama.cpp-Fork) → 512-d Audio-Embeddings, Cosine = Embedding-Score 0–100.
2. **LLM-Urteil (semantisch, erklärend):** Omni-Audio-Modell hinter ollama vergleicht
   beide Clips und antwortet mit JSON `{score, summary, differences[]}` – das „Warum".

Beide laufen **offline auf vorhandenen Takes** (Computer aktuell nicht an den Synths:
4 A/B-.npy-Paare in `recordings/` + `sim_log.jsonl`). Architekturvorgabe des Benutzers:
**ollama oder llama.cpp oder MLX**; Migration auf AMD Strix Halo mit ROCm ist geplant.

## Goals / Non-goals / Anti-goals

- Goals:
  - `embed_score` 0–100 pro A/B-Paar, geloggt in `recordings/sim_log.jsonl` neben Phase A.
  - Optionales LLM-Urteil (Text + geparster Score) im selben Log.
  - Kombinierter Score (gewichtetes Mittel aus Phase-A- und Embedding-Score).
  - Offline-Eval auf allen 4 vorhandenen .npy-Paaren: korreliert der Embedding-Score
    besser mit dem Höreindruck („Charakter anders") als Phase A allein?
  - Runtime-Abstraktion: Backend-Wechsel (CPU jetzt, ROCm später) ohne Code-Änderung.
- Non-goals:
  - Kein Training/Fine-Tuning, kein MLX-Port (MLX läuft nicht auf AMD → Sackgasse für
    Strix Halo; bewusst nicht gewählt).
  - Kein Whisper/ASR; HF/transformers (CLAP2-xxs) nur als *Referenz* in Tests, nicht
    als Produktiv-Backend.
  - `sim_live.py`/`sim_cc_sweep.py` ohne `--embed` in dieser Phase.
  - Keine DB-Schema-Migration: `ab_runs.report_json` ist ein JSON-Blob und nimmt die
    neuen Keys `sim`/`embed`/`llm` ohne Änderung auf.
- Anti-goals:
  - Kein „Ohr-Ersatz"-Anspruch; Phase B ist zweite Metrik, nicht Wahrheit.
  - Keine neuen schweren Runtime-Dependencies im Kern (numpy bleibt; Modelle laufen
    extern via subprocess/HTTP).

## Constraints

- macOS, Python 3.10.13; numpy-only im Kern. Bereits vorhanden: PIL 10.2, requests,
  httpx, matplotlib (kein soundfile → WAV via stdlib `wave`).
- ollama 0.40.16 installiert (`/usr/local/bin/ollama`), noch keine Modelle gepullt.
  clap.cpp nicht gebaut; `pip install clap-cpp` (Python-Bindings) als erste Wahl.
- Lizenz: CLAP `larger_clap_music_and_speech` = Apache-2.0 (ok). LLM: **lfm3-omni:2b**
  (LFM Open License, 2 GB) als Default; Qwen2.5-Omni-GGUF nur optional (qwen-research).
- Ungeklärt (wird im Spike aufgelöst, Plan-Schritt 1): akzeptiert ollama 0.40.16
  Audio direkt im Chat-API (`audio`-Feld)? Falls nein → Fallback: Spektrogramm-PNG
  (PIL) als `images`-Feld an ein Vision-Modell. Beides hinter derselben Backend-Schnittstelle.
- Modelle liegen lokal in `models/` (gitignored), nie im Repo.
- Portabilität Strix Halo/ROCm: clap.cpp ist ggml-basiert (HIP/ROCm-Build existiert),
  ollama hat offizielle ROCm-Builds. Zugriff nur via subprocess/HTTP → kein Code-Wechsel.

## Approaches

- **A (gewählt, numerisch): clap.cpp + `gorse-io/larger_clap_music_and_speech-GGUF`
  (Q8_0, 208 MB, 48 kHz, 512-d, Apache-2.0, musik-trainiert).** Embedding via
  `pip clap-cpp`-Bindings, Fallback: clap.cpp-Binary via subprocess.
  Cosine der Embeddings → `embed_score`. Trade-off: nur Zahl, kein „Warum"; dafür
  klein, schnell, ROCm-portabel.
- **B (gewählt, semantisch, optional per Flag): ollama + lfm3-omni:2b.** Prompt mit
  beiden Clips (Audio direkt oder Spektrogramm-PNG) → JSON-Urteil. Trade-off:
  größer/langsamer, Score subjektiver; liefert aber die textliche Begründung.
- C: MLX-Port (mlx-audio / CLAP→MLX) — **abgelehnt**: schnellstes auf Apple Silicon,
  aber nicht auf AMD/ROCm lauffähig → widerspricht der Migrationsvorgabe.
- D: HF transformers CLAP2-xxs als Produktiv-Backend — **abgelehnt** (Vorgabe: ollama/
  llama.cpp/MLX); bleibt als Test-Referenz (torch 2.2.2 + transformers 4.47.1 sind
  installiert).

## Design

### Neues Modul `bloridium/sim_embed.py` (rein, testbar; Modelle extern)

- `write_wav(x, sr, path)` — stdlib `wave`, float32 → int16 PCM mono (clap.cpp nimmt WAV).
- `render_spec_png(x, sr, path)` — Phase-A-log-Spektrogramm als PNG via PIL
  (für den ollama-Vision-Fallback).
- `class ClapBackend`: `__init__(model_path)`, `embed(x, sr) -> np.ndarray (512,)`.
  Intern: zuerst `clap-cpp`-Python-Binding, sonst `clap embedding --model M --audio WAV`
  als subprocess, Ergebnis-JSON parsen. Kein Download in der Klasse – Pfad kommt von außen.
  **Input-Konvention (Builder-Check Q3, mein Call):** ganze Aufnahme, mono gemittelt;
  Resampling auf 48 kHz nur falls nötig (numpy, linear); Padding auf das 10-s-Fenster
  übernimmt das Backend (clap.cpp repeat-padded kürzere Clips selbst). Konsistent zu
  Phase A, das ebenfalls die ganze Aufnahme featurisiert – Vergleiche über Paare
  verschiedener Länge (126 080 vs 133 969 Samples) bleiben dadurch vergleichbar.
- `DEFAULT_JUDGE_PROMPT` (Builder-Check Q4, mein Call): deutscher Prompt, Anker
  „100 = nicht unterscheidbar, 0 = völlig verschiedener Klang“, Contract
  `{"score": 0-100, "summary": "...", "differences": ["...", ...]}` – `differences` ist
  ein Array von Strings. Prompt ist überschreibbar, landet mit im Log (Versionierung
  der Urteile über Modell/Prompt-ID).
- `class OllamaBackend`: `__init__(model="lfm3-omni:2b", host="http://localhost:11434")`;
  `available()` (GET /api/tags); `judge(x_a, x_b, sr, prompt=DEFAULT_JUDGE_PROMPT) -> dict` –
  baut Chat-Request, probiert `audio`-Feld, fällt bei 4xx auf Spektrogramm-PNG + `images`
  zurück; Antwort-JSON aus dem Content extrahieren (erstes {...}-Objekt), robust parsen.
  **Lifecycle (Builder-Check Q6, mein Call):** `ollama serve` läuft vorausgesetzt
  (Menubar-App jetzt, systemd auf Strix Halo); `fetch_models.py` pullt nur Modelle,
  startet keinen Server. `available() == False` → siehe Degrade-Regel unten.
- `embed_compare(ea, eb) -> {"embed_cos", "embed_score"}` — Score = 100·clip(cos,0,1),
  linear (Mapping-Kurve im Eval validieren; sigmoid optional).
- `score_pair_embed(x_blo, x_irr, sr, meta, log_path, clap=None, ollama=None, use_llm=False)`:
  führt Phase A (`sim.score_pair` ohne Doppel-Log) + Embedding (+ LLM) aus, baut
  kombiniertes Ergebnis:
  ```json
  {"score": <PhaseA>, "embed_cos": .., "embed_score": .., "combined": ..,
   "llm": {"model": .., "score": .., "summary": .., "differences": [..], "mode": "audio|spec"},
   "verdict": ..}
  ```
  `combined = 0.5·score + 0.5·embed_score` (LLM-Score nur informativ, bis Eval validiert).
  Ein JSONL-Eintrag pro Run in `recordings/sim_log.jsonl`, Meta inkl. Backends/Modellnamen.

### Skripte / CLI (konsistent zum bestehenden Stil)

- `scripts/sim_compare.py`: neue Flags `--embed` (CLAP-Score) und `--llm` (ollama-Urteil),
  wirkt auf `--npy` und `--live`.
- `scripts/sim_eval_offline.py`: wertet alle vorhandenen .npy-Paare in `recordings/`
  (ab_*_blofeld.npy vs ab_*_iridium.npy) mit Phase A + Embedding aus, schreibt
  `recordings/phaseb_eval_<ts>.json` + druckt Tabelle (Paar, PhaseA, embed, combined).
- `scripts/fetch_models.py`: `python3 scripts/fetch_models.py` lädt CLAP-GGUF (Q8_0)
  via `hf download` nach `models/`, `ollama pull lfm3-omni:2b`, optional `pip install clap-cpp`.
- CLI: neues Subcommand `bloridium sim compare --npy A B [--embed] [--llm]`
  (lt. Spec 2026-11-09 war das für Phase B vorgesehen); Skripte bleiben dünne Wrapper.
- `.gitignore`: `models/` ergänzen.

### Tests (`tests/test_sim_embed.py`, offline, ohne Modell-Download)

- `write_wav` roundtrip (lesbar via `wave`, korrekte Länge/Pegel).
- `render_spec_png` erzeugt valides PNG (PIL öffnet, Größe > 0).
- `ClapBackend`/`OllamaBackend` mit gemockten subprocess/HTTP (monkeypatch): Payload-Form,
  JSON-Extraktion aus LLM-Text mit umgebendem Fließtext, Fallback audio→spec bei 400.
- `embed_compare`: cos=1 → 100, cos=0 → 0, negativ → 0.
- `score_pair_embed` mit Fake-Backends auf den echten `recordings/ab_*.npy`-Paaren:
  Log-Schema (ein JSONL-Eintrag, Felder vollständig), kombinierter Score im Bereich 0–100.
- Integration (marked slow, skipped ohne Modell): echtes CLAP-GGUF auf einem .npy-Paar.

### Degrade-Regel bei fehlendem Backend (Builder-Check Q5, mein Call)

`--embed` ohne CLAP-GGUF oder `--llm` ohne laufendes ollama → **kein Hard-Fail**: Warnung
auf stderr, Phase A läuft normal, JSONL-Eintrag enthält die Backend-Felder als `null`
plus `"backend_error": "..."` (Downstream-Training sieht also explizit, dass Daten fehlen).
Exit-Code: 0 wenn Phase A ok (bestehendes Verhalten: 1 nur bei Phase-A-`fehler`);
`--strict` schaltet auf Hard-Fail (Exit 3) für CI/Sweeps, die Embeddings brauchen.

### Eval (Nachweis, dass Phase B etwas bringt)

Ablauf (Q1 entschieden, post-hoc): `sim_eval_offline.py` wertet alle 4 .npy-Paare
(`ab_*_blofeld.npy` vs `ab_*_iridium.npy`, inkl. `check_*`) mit Phase A + Embedding
(+ combined) aus, schreibt `recordings/phaseb_eval_<ts>.json` und druckt die Tabelle.
Danach trägt der Benutzer in `docs/PHASEB-EVAL-2026-11-14.md` pro Paar eine
0–100-Bewertung des Höreindrucks ein („wie ähnlich klingt das Paar?“); das Skript
kann mit `--ratings` die Spearman-Rangkorrelation der drei Metriken gegen diese
Bewertungen nachrechnen (n=4 → Rangkorrelation; Post-hoc-Caveat wird dokumentiert).
Entscheidung „combined als neuer Default-Score“ fällt auf Basis dieser Auswertung.

## Builder-Check 2026-11-12→14 (Subagent ses_e25f5d23…): Auflösung

- **Q1 Ground Truth — ENTSCHIEDEN (Benutzer 2026-11-14): post-hoc.** Kein
  pre-registered JSON. Ablauf: `sim_eval_offline.py` rechnet Phase A + embed + combined
  für die 4 Paare und schreibt Tabelle + `recordings/phaseb_eval_<ts>.json`; der
  Benutzer bewertet danach jedes Paar **0–100** (Höreindruck „wie ähnlich?“) und trägt
  die Bewertungen in `docs/PHASEB-EVAL-2026-11-14.md` ein. Das Eval-Skript kann die
  Tabelle nachträglich um Spearman-Rangkorrelation gegen diese Bewertungen ergänzen
  (`--ratings` liest die Eval-Doku/JSON). Caveat post-hoc (Scores können das Urteil
  färben) wird in der Eval-Doku vermerkt.
- **Q2 Scope — ENTSCHIEDEN (Benutzer 2026-11-14): volle Integration auch in `ab`.**
  - `workflow.measure_ab(..., embed=False, llm=False)`: nach dem bestehenden Report
    zusätzlich `sim.compare` (Phase A) + Embedding (+ LLM) auf den aufgenommenen Signalen;
    Ergebnis landet als neue Keys `"sim"`, `"embed"`, `"llm"` im report dict →
    `report_json`-Blob in `ab_runs` trägt sie mit (**keine Schema-Migration nötig**,
    report_json ist JSON-Text; SCHEMA_VERSION bleibt). `cmd_ab` bekommt `--embed/--llm`
    und reicht durch.
  - Neues CLI `bloridium sim compare --npy A B [--embed] [--llm]` und
    `--live [--note N] [--dur S] [--blofeld LOC] [--iridium-slot S] [--embed] [--llm]`
    → loggt über `sim_embed.score_pair_embed` nach `recordings/sim_log.jsonl`
    (ein Eintrag, alle Metriken). Kein Doppel-Log: `measure_ab` ruft die Features
    direkt auf (`log_path=None`), nicht `sim.score_pair`.
  - `scripts/sim_compare.py` bekommt ebenfalls `--embed/--llm` (wirkt auf `--npy` und
    `--live`).
  - `sim_live.py` / `sim_cc_sweep.py` bleiben in dieser Phase ohne `--embed` (Non-Goal;
    adoptieren `sim_embed` später analog).
- **Q3 CLAP-Input:** mein Call — ganze Aufnahme mono, Backend padded (siehe Design).
- **Q4 Prompt/Anker:** mein Call — deutscher `DEFAULT_JUDGE_PROMPT`, 100 = nicht
  unterscheidbar, `differences` = String-Array (siehe Design).
- **Q5 Backend fehlt:** mein Call — degrade + warn + `null`-Felder im Log, Exit 0;
  `--strict` → Exit 3 (siehe Degrade-Regel).
- **Q6 ollama-Lifecycle:** mein Call — Server läuft vorausgesetzt; `fetch_models.py`
  pullt nur.

## Was der Builder noch klären muss (Vorschläge = meine Calls)

- Spike (Plan-Schritt 1): ollama 0.40.16 + lfm3-omni:2b – funktioniert Audio im Chat-API?
  Ergebnis entscheidet Default-Modus (audio vs. spec-PNG); beides ist implementiert.
- CLAP-Zugriff: `pip install clap-cpp` zuerst, sonst clap.cpp bauen (cmake).
  Call: pip zuerst.
- Cosine→Score: linear geclippt. Call: linear, Kurve im Eval prüfen.
- Combined-Gewichtung: 50/50 PhaseA/Embedding, LLM nur Text. Call: 50/50.
- `models/` in `.gitignore`. Call: ja.

## Nächster Schritt nach Genehmigung

Plan via superpowers:writing-plans (Spike zuerst: ollama-Audio-Fähigkeit + CLAP-GGUF-Download
verifizieren), dann TDD-Implementierung (test_sim_embed.py zuerst).

## Spike-Ergebnisse 2026-11-14 (nachimplementiert)

- **CLAP-GGUF**: `models/larger_clap_music_and_speech-q8_0.gguf` (208 MB) via
  `huggingface_hub.hf_hub_download` geladen (hf_cli-Modulpfad existiert in hub 0.27 nicht).
  `pip install clap-cpp` funktioniert; `clap_cpp.CLAP(path)` + `encode_audio(pcm, sample_rate=48000)`
  liefert 512-d, L2-normalisiert. Smoke: self-cos = 1.0, 440 vs 220 Hz = 0.938.
  → **Modus: pip-Binding**, subprocess-Fallback bleibt im Code.
- **ollama 0.40.16 + lfm3-omni:2b**: `ollama pull lfm3-omni:2b` ok (2,4 GB).
  `/api/chat` akzeptiert das **`audio`-Feld** (base64 WAV, 48 kHz und 16 kHz getestet) →
  HTTP 200 mit JSON-Antwort. → **Default-Modus: audio**; Spektrogramm-PNG-Fallback bei 4xx
  bleibt für andere Server/Versionen. Live-Smoke judge(440 Hz vs 233 Hz+1200 Hz) →
  `mode=audio, score=85`, deutsche summary + differences.
- **Aufnahme-Daten**: von den 4 .npy-Paaren ist nur `check_20261108_152813` brauchbar
  (Iridium env 4.6e-2); die 3 `ab_A043_*`-Iridium-Takes sind ~1e-5 = stumm
  (vgl. sim_log „stille Aufnahme“). Eval wertet daher primär das check-Paar aus;
  frische Paare können jetzt (Hardware wieder dran) per `sim compare --live` nachgelegt werden.
