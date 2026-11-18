# Design: specdiff – Interpretation des Spektral-Diffs (A | B | ΔdB)

Datum: 2026-11-18 · Status: Design zur Freigabe (Ansatz A "hybrid" + beide Verwendungen
("Feld im sim_log + eigene Score-Komponente") vom Benutzer bestätigt 2026-11-18)

## Intent & Why

Pro Messung existiert bereits das Diff-Bild (`render_spec_pair_png` in
`bloridium/sim_embed.py`: A | B | ΔdB, divergierend ±20 dB, landet in
`recordings/spec/`). Was fehlt: eine **strukturierte Interpretation** dieses Diffs –
mit einem multimodalen Decision Model (lokales Vision-Modell), mit deterministischem
DSP-Fallback. Output-Schema (vom Benutzer vorgegeben):

```json
{
  "severity": "light | medium | heavy",        // overall deviation
  "spread":   "even | punctual",               // räumlich: verteilt vs. punktuell
  "temporal": "even | periodical | single | multiple | increasing | decreasing",
  "bands":    ["low", "mid", "high"],          // betroffene Frequenzbereiche
  "summary":  "one sentence"
}
```

Verwendung (beides, bestätigt): (1) als Feld `result.specdiff` im `sim_log.jsonl` pro
Messung – um pro Preset/Location zu sehen, *wo* die Konvertierung hakt; (2) als eigene
Score-Komponente `result.specdiff_score` (0–100), **separat** von `combined` (bestehende
Score-Korrelationen bleiben vergleichbar).

## Spike-Ergebnisse 2026-11-18 (Basis der Model-Wahl)

- **d1-omni:2b via `/v1/systemone`** (bestehender Profile-Endpunkt): unterstützt
  `images` + typisierte Fragen. `choice`-Fragen brauchen `"criteria"` als **Dict**
  Option→Beschreibung (2–26 Kandidaten; `options` als Liste → 400). Antwort:
  `{"choice": "heavy", "probabilities": {...}, "confidence": 0.08}`; `noul` →
  `{"noul": p}`. **~3 s pro Aufruf** mit Bild auf CPU → Default-Model.
- `/api/chat` und `/api/generate` mit d1-omni → 400 "does not support chat/generate"
  (nur systemone).
- **gemma4:12b-it-qat via `/api/chat`**: hat `vision`, braucht **`"think": false`**
  (sonst leere Content bei `done_reason: length` – Thinking-Tokens verbraten
  num_predict). Liefert valides JSON, aber **~64 s/Aufruf** → schwere Option
  (`--model gemma4:12b-it-qat`), nicht Default.
- **Orientierung:** `sim.features` log_spec[0] = 40 Hz landet im PNG **oben**
  (Image.fromarray(img.T)). State-Text muss "LOW frequencies at TOP" sagen –
  gemma4 las sonst high/low vertauscht (Spike: high-band boost → gemma4 sagte
  low/mid, d1-omni mit Orientation-Hinweis sagte high korrekt).
- lfm3-audio:2b (früherer Spike): als Bild-Judge unbrauchbar – bleibt draußen.

## Goals / Non-goals

- Goals:
  - `bloridium/specdiff.py`:
    - `diff_matrix(x_a, x_b, sr)` → (ΔdB (n_bands, n_frames), band_edges) aus
      `sim.features`, längere Seite gepadded, Pad-Spalten = 0 (wie im PNG).
    - `dsp_features(delta, band_edges)` → numerische Merkmale: `severity_db`
      (Mittel |Δ| über aktive Bins; aktiv = max(sa,sb) > floor), `spread_frac`
      (Anteil aktiver Bins mit |Δ| > thr), `temporal` Serie e(t) = Mittel |Δ| pro
      Frame, Slope, Autokorrelation, Peaks; `bands` Mittel |Δ| pro Bereich
      (low < 250 Hz, mid 250–2000 Hz, high > 2000 Hz – aus band_edges).
    - `classify_dsp(...)` → Labels deterministisch (Schwellen s. u.).
    - `SystemOneBackend` (d1-omni via /v1/systemone, questions = Schema als
      choice/noul) und optional `OllamaChatBackend` (gemma4 via /api/chat,
      think:false, JSON-Prompt, robustes JSON-Extrakt aus erster `{`..letzter `}`).
    - `interpret_pair(x_a, x_b, sr, use_vision, model)` →
      `{labels, probs, confidence, dsp: {...}, vision: {...}|None, score, source}`.
      Labels kommen vom Vision-Model wenn verfügbar, sonst DSP (`source` merken).
      `score` immer numerisch-deterministisch aus `severity_db`.
    - CLI `bloridium specdiff`:
      - Einzel: `--wav A.wav B.wav [--png out.png] [--no-vision] [--model …]`
      - Batch: `--log recordings/sim_log.jsonl --recordings recordings/
        [--only A043] [--write] [--no-vision]` – WAVs über
        `ab_<LOC>_<ts>_n<note>[_w<pct>]_blo|irr.wav`; mit `--write` landet
        `specdiff` + `specdiff_score` in `result` der JSONL-Zeile.
  - Optionaler Flag `--specdiff` in `sim compare` / `sim_checkpoint.py`, der das
    Feld direkt bei der Messung schreibt (Vision nur an der Referenz-Kombo
    wheel 0 + note 72, sonst DSP – Muster wie `--profile`).
- Non-goals:
  - Kein eigenes Training/Gewichte; keine Änderung von `combined`.
  - Kein scipy (in der Env defekt), numpy-only Kern; `requests`/`urllib` + PIL wie
    bestehend. Ollama optional – bei Fehlen: WARNING + DSP-Fallback.
- Anti-goals:
  - Keine stillen Ausfälle: Vision-Fehler → `source: "dsp"` + WARNING, nie Absturz.
  - Pad-Spalten dürfen nicht als Fehler gewertet werden (grau/0 wie im PNG).

## Constraints

- numpy-only Core; PIL nur fürs PNG-Render; ollama lokal (`http://localhost:11434`).
- Determinismus wo möglich: DSP 100 %; Vision mit temperature 0 (d1: fix, gemma:
  options.temperature=0).
- Tests offline (TDD): synthetische Δ-Matrizen mit bekannten Mustern, monkeypatchte
  HTTP-Antworten für beide Vision-Backends, tmp-WAVs + tmp-Log fürs CLI-Batch.
  Kein Live-MIDI. `python3 -m pytest tests/ -q`.
- Deutsch Doku/Commits.

## Approaches

- **A (gewählt, bestätigt):** Hybrid – DSP-Features/-Labels (deterministisch, testbar,
  Fallback) + Vision-Decision-Model (d1-omni:2b default via systemone choice/noul,
  gemma4 optional via /api/chat) als Label-Quelle. Score immer aus DSP-Severity.
- **B (abgelehnt):** nur Vision-LLM – nicht testbar offline, ~64 s/Aufruf (gemma4),
  kein Fallback wenn ollama down; d1-omni allein reicht nicht als alleinige Quelle
  (Decision-Qualität auf Bildern ohne Kalibrierung unbekannt).
- **C (abgelehnt):** nur DSP – deterministisch, aber keine qualitative Interpretation
  ("wirkt wie Filter-Divergenz in den Höhen"); Benutzer wollte ausdrücklich das
  multimodale Model.

## Schwellen (Vorschlag, Konstanten im Modul, konfigurierbar)

- severity: **median** |Δ| aktiv < 5 dB → light, < 15 dB → medium, sonst heavy
  (Median statt Mittel + Schwellen kalibriert an Eval 2026-11-18 gegen
  `phaseb_ratings_raw.json`, n=9: User-Ratings 90er liegen bei median 6–11 dB,
  45–75er bei 12–37 dB; median erreicht Spearman ρ=+0.71 vs. User-Rating).
- bands im Endergebnis = **Union aus Vision- und DSP-Bändern** (das PNG oben/low wird
  vom Vision-Model leicht unterlesen; DSP traf 7/7 Text-Hits, Vision 6/7).
- aktiv = max(sa,sb) ≥ peak − 40 dB (nahe Rauschbins liefern riesige, irrelevante dB-Deltas).
- `specdiff_score` = clip(100 − 4 · severity_db, 0, 100).
- spread: aktiver Anteil |Δ|>3 dB ≥ 0.25 → even, sonst punctual.
- temporal: |Slope| der e(t)-Geraden > 0.5 dB über die Dauer → increasing/decreasing
  (Vorzeichen); sonst Autokorrelation lag 2..n/2, r > 0.5 → periodical; sonst
  Peak-Anzahl (prominenz > 3 dB): 1 → single, >1 → multiple, 0 → even.
- bands: Bereich betroffen wenn Mittel |Δ| im Bereich > 3 dB.
- Vision-`summary`: d1-omni hat keinen Freitext-Typ in systemone → summary kommt
  aus DSP-Template ("Δ≈X dB, even/punctual, temporal …, bands …") bzw. bei gemma4
  aus dem JSON.

## Was noch offen ist (Builder-Calls)

- `bands` als noul-Tripel (low/mid/high) statt einem choice mit 8 Kombinationen –
  einfacher, robustere Wahrscheinlichkeiten.
- Batch-Vision default: AN mit d1-omni:2b (~3 s × n, bei 108 Messungen ≈ 6 min),
  `--no-vision` für reines DSP.
