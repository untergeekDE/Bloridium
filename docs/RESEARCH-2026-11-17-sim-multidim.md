# Forschungsstand 2026-11-17 – Zwei-Sound-Vergleich: mehrere Dimensionen + Embedding-Distanz

Anlass: geplantes Tool, das zwei aufgenommene Sounds (Blofeld vs Iridium, ein A/B-Paar)
über **mehrere Dimensionen** vergleicht und zusätzlich einen **Distanzwert der Embeddings**
liefert. Dieses Dokument ist der Stand der Technik (Literatur 2025–2026) plus der Stand
im eigenen Repo – als Grundlage für das Design des Tools.

## 1. Stand im Repo (was heute schon messen wir)

- **Phase A** (`bloridium/sim.py`, numpy-only): `score = 100·(0.7·spec_cos + 0.3·(1−env_dtw))`
  plus diagnostische Felder `band_dtw` (pro Frequenzband DTW über die Zeit), `spec_dtw`,
  `frame_cos`, `band_delta_db`, `band_edges_hz`.
- **Phase B** (`bloridium/sim_embed.py`): CLAP-GGUF (`larger_clap_music_and_speech-q8_0`,
  512-d, clap.cpp) → `embed_cos` / `embed_score = 100·clip(cos,0,1)`; `combined = 0.5·A + 0.5·embed`;
  ollama-LLM-Judge (lfm3-omni:2b) und d1-omni:2b-Profil (noul-Flags) als Erklär-Schicht.
  `norm_pegel=True` (Peak 0.5 vor embed/LLM) ist essentiell (sonst kollabiert embed bei
  leisen Iridium-Takes: A001 29 statt 75.6).
- **Eval gegen Benutzer-Ratings** (n=9 Presets, post-hoc 0–100, `docs/PHASEB-EVAL-2026-11-14.md`):
  Spearman ρ Phase A **+0.27**, embed **+0.50**, combined **+0.52**. LLM-Scores degeneriert
  (lfm3 konstant 85; d1-omni als Score ρ +0.07/+0.13), d1-Flags als Profil brauchbar
  (`darker` 9/9 matcht Benutzer-Bemerkungen).
- **Bekannte Schwäche** (HANDOVER-2026-11-09, Offen Punkt 5): Phase A liefert 93–97, obwohl
  der Höreindruck „oft sehr anders" ist → der Bedarf an zusätzlichen Dimensionen ist genau
  das, was das geplante Tool adressieren soll.

## 2. Forschungsstand: Embedding-Modelle und Distanzmetriken

### 2.1 Welche Embeddings für paarweisen Audio-Vergleich?

- **CLAP-Familie** (LAION / MS-CLAP): 512-d, L2-normalisiert, cosine = dot product.
  Varianten: `630k-audioset` (general, <10 s), `music_audioset`, `music_speech`,
  `music_speech_audioset`. M2D-CLAP (IEEE 2025): auf Musik-Tasks sind general-purpose- und
  Musik-Modelle vergleichbar; Musik-Modelle nur bei Pitch-Classification vorne. Für unsere
  **kurzen monophonen Synth-Noten** ist `music_and_speech` (GGUF via clap.cpp, Apache-2.0)
  ein guter Default – wir nutzen ihn bereits.
- **MuQ / MuQ-MuLan** (music-only, 512/1024-d) und **MERT** (frame-level, 768/1024-d):
  MuQ-MuLan und CLAP ohne Fine-Tuning auf ABX/Inst-Sim benchmarks vergleichbar
  (arXiv 2601.19109). MERIT (arXiv 2605.27346) nutzt MERT-Backbone + 3 Projektions-Heads.
- **clap.cpp** (gorse-io, Stand 2026-11) unterstützt als GGUF direkt **CLAP, CLaMP3,
  MERT v1/v2, MuQ, MuQ-MuLan** – alle lokal, CPU, ROCm-portabel. Damit sind Modell-Wechsel
  ohne Code-Änderung möglich (subprocess/HTTP-Schnittstelle bleibt).
- **Wichtig für uns – Caveat „Don't CLAP"** (Cheng & Lerch, arXiv 2609.30540, 2026):
  CLAP-Scores verhalten sich bei feinen Attribut-Vertauschungen (z. B. Timbre-Swap in
  Captions) wie ein Bag-of-Words; LAION-CLAP swap-accuracy ≈ 0.51 (Chance). Heißt: der
  globale CLAP-cosine ist für **grobe** Ähnlichkeit gut, für feine Synth-Timbre-Details
  (einzelne Oberton-Deltas) blind. Deshalb: Embedding-Distanz als eine Dimension unter
  mehreren, nicht als alleinige Wahrheit.
- **Timbre-Alignment-Eval** (Tian, Lattner, Saitis, ISMIR 2025, arXiv 2507.07764):
  auf 21 psychoakustischen Timbre-Datensätzen (2 614 Paar-Ratings) sind **Huang-Style-
  Embeddings aus CLAP** (Mittelwert+Varianz über die Feature-Dims der ersten Swin-Blöcke,
  konkateniert) die stärkste Repräsentation, **MFCC bleibt kompetitiv**, EnCodec-24k
  schlägt EnCodec-48k. Distanzfunktionen: **cosine distance (1−cos) und L2** auf
  L2-normalisierten Vektoren; Eval-Metriken: triplet agreement (mit Margin 0.1), Kendall,
  Spearman, NDCG gegen menschliche Ratings. → Empfehlung: neben `embed_cos` auch
  `embed_l2` und optional **MFCC-cosine** als robuste, cheap Komponente.
- **Cross-cultural Similarity** (TISMIR 2026, tismir.341): Foundation Models schlagen
  handgefertigte Features; **CLAP-Music&Speech** höchste Alignment mit menschlicher
  Ähnlichkeitsbeurteilung; bei den Features ist **Melodie** prädiktivster Einzelfaktor.

### 2.2 Mehrdimensionale / entkoppelte Similarity (der Trend 2026)

- **MERIT** (arXiv 2605.27346): einzelner monolithischer Score ist das Problem; MERT-
  Backbone (frozen, Layer 3–6 + 23) + **drei getrennte Heads für Melodie, Rhythmus,
  Timbre**, je 128-d auf der Einheitssphäre, Retrieval per cosine pro Head → explizite
  per-Faktor-Scores. Human Eval bestätigt Selektivität der Heads.
- **Post-hoc CSN-Disentanglement** (arXiv 2611.14415, Nov 2026): gelernte Masken auf
  gefrorenen Foundation-Embeddings (CLAP/MERT/MuQ) gating in attributspezifische
  Subräume; minimale Adaptation reicht, verbessert attributspezifische Disentanglement.
- **Instrumenten-gewichtetes Cosine** (arXiv 2601.19109): Source Separation → pro-Stem-
  Embeddings, gewichtete Summe; auf ABX mit listening tests.
- **Timbre-Trait-Predictor für Synthesizer** (arXiv 2606.30369): statt globalem FAD ein
  **20-dimensionales Timbre-Trait-Profil** (Reymore & Huron: bright, percussive, woody …)
  prädiziert aus CLAP-Embedding + shallow head (RWC-Datenbank) – direkt übertragbar auf
  „Vergleich über mehrere Dimensionen" für Synth-Sounds.
- **SynthCloner** (arXiv 2509.24286, 2026): Synth-Sound = **Timbre (zeitinvariant,
  spektral) + ADSR-Envelope** – genau die zwei Achsen, die unser A/B-Vergleich trennen
  sollte (Spektrum vs Hüllkurve).

### 2.3 Interpretierbare Timbre-Dimensionen (psychoakustische Features)

Klassische Korrelate (McAdams 2019; Kazazis 2021; Peeters 2011): **spectral centroid**
↔ Brightness, **attack time**, **spectral flux**, spread/skewness/slope, odd-to-even
Harmonic-Ratio, harmonic deviation.
DAGA 2025 (Czedik-Eysenberg & Reuter, „Evaluating Timbre-Related Audio Descriptors"):
- **Brightness**: Sharpness (DIN 45692 / AudioCommons) r≈0.57–0.73, spectral centroid
  r≈0.55–0.63 – **aber stark pitch-abhängig** (bei gleicher Note E4: F0 r=−0.16).
  → Wir messen bei fester Note (72), daher ist centroid/sharpness hier valide.
- **Roughness**: Vassilakis-Roughness (log) r≈0.82–0.87, Dissonance r≈0.67–0.74.
- **Percussiveness**: Loudness-Differenz perkussiv/harmonisch nach HPSS (librosa
  harmonic-percussive separation) am besten.
- Embedding-Similarity zu verbalen Descriptors korreliert nur partiell (r bis 0.65 für
  „bright") → klassische Features sind für die *benannten* Dimensionen zuverlässiger als
  CLAP-Cosine gegen Text.

### 2.4 Distanzmetriken und Vergleichsmethodik (MIR-Standard)

- Distanzen in der Musikähnlichkeits-Literatur (CMMR 2021 Survey): **Manhattan, Euclidean,
  Cosine, KL, Earth Mover's Distance (EMD)**, Sequenz-Distanzen (Levenshtein/LCS).
  Für Embeddings: **cosine distance + L2** (Standard); EMD eher für Histogram-Features
  (chroma, MFCC-Histogramme).
- Paarweise Vergleiche kurzer Clips: globaler Vektor (mean-pooled) → cosine/L2; für
  zeitliche Struktur: **DTW/soft-DTW auf Hüllkurven** (arXiv 2506.22628, sound-matching:
  DTW-Envelope empfohlen für amplitudenmodulierte Signale; spectrogram-L1 ohne Alignment
  empfindlich gegen lokale Zeitverschiebungen). Wir nutzen bereits DTW auf env + bands.
- **Eval gegen Menschen**: triplet agreement / ABX mit Margin, Spearman/Kendall gegen
  Ratings (das machen wir mit ρ gegen post-hoc 0–100; Caveat post-hoc dokumentieren).
- **Preprocessing ist kritisch**: Pegel-Normierung vor Embedding-Vergleich (CLAP reagiert
  auf Gain – unser norm_pegel-Befund), feste Tonhöhe, mono, 48 kHz; CLAP-Fenster 10 s mit
  repeat-padding kurzer Clips (clap.cpp-Verhalten, verifiziert).

### 2.5 LLM-Judges als Score – negativer Befund (Repo + Literatur)

- Eigenes Eval: lfm3-omni:2b konstant 85 (ρ +0.35 degeneriert), d1-omni:600m kollabiert
  88–96 (ρ +0.07), spec-Modus halluziniert (ρ −0.39). d1-omni:2b als noul-Profiler
  (darker/octave_lower/brighter…) matcht Benutzer-Bemerkungen → **Erklär-Schicht ja,
  Score nein**.
- Literatur bestätigt: „Don't CLAP" (s. o.) und FIGMA (ACL 2026): CLAP & Co. sind für
  feine musikalische Attribute (key, chords, feine Timbre-Bindungen) unzuverlässig.
- **Befund bestätigt 2026-11-17 (Benutzer-Recall vs `docs/PHASEB-EVAL-2026-11-14.md`):
  d1-omni:2b vs lfm3-omni:2b auf denselben 9 WAV-Paaren — als Score beide schwach
  (d1:600m kollabiert 88–96, ρ +0.07; d1:2b 59–67, ρ +0.13; lfm3 audio konstant 85,
  ρ +0.35 degeneriert ohne Varianz; lfm3 spec halluziniert, ρ −0.39). Als
  **beschreibungs-kodierte Dimensionen** (noul-Profil via `/v1/systemone`) war das
  Decision-Modell etwas besser: Flags matchen Benutzer-Bemerkungen (`darker` 9/9,
  `octave_lower` A008 nur p=0.50 grenzwertig), diff_count ρ −0.38, score−k·diff +0.32 —
  insgesamt aber geringer Gewinn; beste Proxy-Scores bleiben embed ρ +0.50 /
  combined ρ +0.52 (n=9). → d1-Profil bleibt Erklär-Schicht (`profile`-Feld), nie Score.

## 3. Konsequenzen für das geplante Tool (Vorschlag)

Vergleichs-Ergebnis als JSON mit zwei Ebenen:

1. **Dimensions-Vergleich** (interpretierbar, je Dimension 0–100 oder Delta):
   - *Spektrum/Timbre*: `spec_cos` (global, bestehend), `band_dtw`/`band_delta_db` mit
     `band_edges_hz` (Lokalisierung: Filter→tiefe Bänder, Obertöne→hohe — bewährt),
     plus psychoakustische Traits als Deltas: `d_centroid` (brightness), `d_sharpness`,
     `d_roughness` (Vassilakis log), `d_percussive` (HPSS-Δloudness), `d_flatness`.
   - *Zeit/Envelope*: `env_dtw` (bestehend), attack-time delta, `frame_cos` (LFO/Mod-
     Divergenz über die Zeit, bestehend).
   - *Pitch*: F0-Delta in Halbtönen (bei gleicher Note ≈0; lokalisiert Oktave-Fehler wie
     A008-Verdacht besser als d1-flag p=0.50).
   - *Semantisch*: d1-Profil-Flags (bestehend, Erklär-Schicht).
2. **Embedding-Distanz** (hart, numerisch):
   - `embed_cos` + `embed_l2` auf CLAP-512-d (bestehend `embed_cos`; L2 ergänzt),
     optional `mfcc_cos` (robust, kompetitiv laut ISMIR 2025) als cheap第二层,
     optional Huang-Style-Embedding-Distanz aus CLAP (beste Timbre-Alignment 2025) als
     `timbre_dist` – Extraktion: mean/var der ersten Swin-Blöcke (clap.cpp liefert nur
     den finalen Vektor → dafür HF-Referenz oder clap.cpp-Patch; Spike nötig).
   - Score-Mapping: linear geclippt (bestehend), Kalibrierung gegen User-Ratings per
     Spearman (Eval wie gehabt).
3. **Preprocessing-Pflicht**: `norm_pegel` (Peak 0.5), feste Note, mono, 48 kHz – sonst
   sind embed/LLM wertlos (bewiesen).
4. **LLM-Score nicht als Metrik** führen; nur Profil/Erklärung.

Offene Design-Fragen fürs Tool (nächster Schritt):
- Huang-Style-Embedding: clap.cpp patchen vs HF-Referenz (nur Eval) vs weglassen.
- MFCC-cos als zweite Embedding-Distanz: ja (cheap, robust) – numpy-Implementierung
  ohne librosa.
- Psychoakustische Traits: eigene numpy-Implementierung (sharpness DIN, roughness
  Vassilakis, HPSS via median filtering) – kein neues Dependency.

## 4. Nachtrag 2026-11-17: lokal verfügbare Modelle & Instrumente (Bestand dieser Maschine + Stand)

Zwei Ebenen: **(a) lauffähige Modelle** für Embedding-Distanz / Urteil, **(b) klassische
DSP-/Parameter-Instrumente** für die interpretierbaren Dimensionen.

### 4.1 Modelle – was hier lokal läuft bzw. ohne Weiteres ladbar ist

| Instrument | Wo | Status lokal | Lizenz | Für unseren A/B-Vergleich (kurze monophone Synth-Noten) |
|---|---|---|---|---|
| **CLAP `larger_clap_music_and_speech` Q8_0 GGUF** (512-d, 48 kHz) | `models/` + clap-cpp 0.1.1 (pip) | ✅ in Nutzung (`ClapBackend`) | Apache-2.0 | **Primär-Embedding** (`embed_cos`/`embed_l2`) |
| **clap.cpp GGUF-Familie** (gorse-io@HF): CLAP alle Varianten, **CLaMP3** (768-d, 24 kHz), **MERT v1 95M/330M + v2**, **MuQ** (1024-d), **MuQ-MuLan** (512-d, Text+Audio) | `hf download gorse-io/...` → `models/`, CPU, ROCm-portabel | ⬇️ ladbar, ~0.2–2 GB | CLAP Apache-2.0, CLaMP3 MIT, **MERT/MuQ CC-BY-NC-4.0** (nur Research/Nicht-kommerziell – für Strix-Halo-Migration merken) | Modell-Wechsel per Pfad, kein Code-Wechsel. **MuQ-MuLan**: laut arXiv 2510.14249 beste Pearson/Spearman (0.535/0.530) bei EQ/Reverb-Timbre-Semantik – relevant für Filter-Deltas; LAION-CLAP konsistenteste Instrumental-Timbre |
| **Music2Latent** | HF via torch 2.2.2 + transformers 4.47.1 (installiert) | ⬇️ ladbar (Referenz/Eval) | research | laut ISMIR 2025 (arXiv 2507.07764) aligned **besser als CLAP** mit menschlichen Timbre-Ratings, hohe Kompression, music+speech |
| **ollama lokal**: `d1-omni:2b` (4,4 GB), `d1-omni:600m`, `lfm3-omni:2b` (2,4 GB) | `ollama list` | ✅ vorhanden | LFM Open License | d1-omni:2b als noul-Profiler (integriert), lfm3 audio-Judge (degeneriert als Score) — **Erklär-Schicht, nicht Metrik** |
| **ollama Bibliothek**: `lfm3-audio:2b` (2,1 GB, reines Audio-LM, 16 kHz), `qwen2.5-omni-3b/7b`, `qwen3-omni` (GGUF) | pull | ✅ gepullt + Spike 2026-11-17 | LFM Open License | **lfm3-audio:2b getestet (ollama 0.40.16):** `/api/chat` mit `audio`-Feld → 200 aber Audio kommt nicht an („you haven't provided any audio“); `content` als Teile-Liste → 400 (nicht unterstützt); nur `/v1/chat/completions` mit `input_audio` liefert Audio (200), aber **unzuverlässig bei reinen Synth-Tönen** (440 Hz → „low vocalization“, 220 Hz → „440 Hz“ falsch); `/api/embeddings` + `/api/embed` → „does not support embeddings“ → **kein Embedding-Modell** (generatives Audio-LM). Fazit: nicht als Judge/Metrik; Embeddings bleiben CLAP-GGUF (+ MuQ-MuLan/MERT/MuQ-GGUF, MFCC). Qwen-Omni: Kandidat für Captioner; gleiches Degenerations-Risiko wie d1/lfm3 |
| **jina-embeddings-v2-base-de** (322 MB) | ollama ✅ | Text-Embeddings DE | Apache-2.0 | nur Text-Seite (z. B. Beschreibungs-Vergleich); CLAP-Text-Encoder ist RoBERTa (EN) → Prompts auf Englisch |
| **CLAP-Text-Encoder** (im GGUF) via `clap embedding --text` | clap.cpp ✅ | zero-shot: Audio-Embedding gegen Text-Prompts („bright synth pad“, „dull filtered bass“…) projizieren | Apache-2.0 | **Per-Attribut-Scores ohne neues Modell** (Brightness/Roughness als Text-Probes) – DAGA 2025: Embedding↔„bright“ nur r≈0.65, also ergänzend zu DSP-Features |
| **timbremetrics** (Python-Paket, Tian/Lattner/Saitis) | pip | ⬇️ | — | **Eval-Instrument**: 21 Timbre-Datensätze (334 Samples, 2 614 Ratings), triplet agreement/Kendall/Spearman/NDCG — damit evaluieren wir unsere Metriken gegen menschliche Ratings (statt nur unseres n=9) |
| **NSynth** (305 979 monophone Noten, 1 006 Instrumente, Pitch/Timbre/Envelope-Labels) | HF ✅ | Datensatz | CC-BY | **Kalibrier-Datensatz**: exakt unser Setting (einzelne gehaltene Noten); z. B. self-similarity von CLAP/MFCC auf NSynth electronic/synthetic als Referenzskala |

### 4.2 Stand: welche Repräsentation schlägt wen (für Timbre/kurze Noten)

- **timbremetrics-Benchmark** (arXiv 2507.07764; Paket `timbremetrics`): LAION-CLAP 70.8–71.8 % triplet agreement, **MFCC 68.7 %**, **PANNs (AudioSet) nur 61.4 %**, EnCodec-24k > 48k, Music2Latent stark, **Huang-Style-Embedding aus CLAP-Internal am besten**. → tiefe Modelle sind für feine Timbre nur marginal besser als MFCC; PANNs/VGGish nicht holen.
- **Effekt-induzierte Timbre-Änderungen** (arXiv 2510.14249): **MuQ-MuLan** stärkste monotone/lineare Abbildung (Pearson 0.535), LAION-CLAP konsistenteste über Instrumente; Reverb wird besser kodiert als EQ → für unsere Filter-Deltas (EQ-artig) ist CLAP/MuQ-MuLan ok, aber begrenzt.
- **„Don't CLAP“** (arXiv 2609.30540): CLAP-Score ≈ Bag-of-Words bei feinen Attribut-Swaps → globale Embedding-Distanz ist **grober** Indikator, feine Deltas brauchen DSP-Features (Abschnitt 2.3).
- **Synth-spezifisch (Parameter↔Audio)**: **Synth-JEPA** (arXiv 2609.31024, Hayes/Tian/Lattner 2026; Surge XT, 85 % Listening-Preference, renderer-free objective), **FM-SynAPSE/DX7-GNN** (arXiv 2608.18226; Audio↔Parameter joint space, DX7AllTheWeb 31k Presets), DDSynth-RL (Dexed, arXiv 2608.03032), SynthRL (IJCAI 2025). → Forschungsstand für **Parameter-Ebene**: wir haben beide Seiten (Blofeld-SNDD ↔ qpat) – ein direkter Parameter-Diff (bereits `qpat_map` overrides/unmapped) ist das „Instrument“ ohne Rendering; joint audio-parameter embeddings sind Future Work (Training nötig – gegen unsere No-Training-Regel).
- **Sound-Matching-Losses** (arXiv 2506.22628): MSS, **wMFCC**, CLAP, P-Loss, soft-DTW(Envelope), JTFS — wMFCC und DTW-Envelope sind die praxisrelevanten für uns (wMFCC = gewichtete MFCC-Distanz, cheap in numpy/scipy).

### 4.3 DSP-Instrumente (numpy/scipy-only, kein neues Dependency; scipy 1.11.4 ist installiert)

- Spektral: log-mel/log-STFT (numpy FFT), **MFCC/wMFCC** (DCT via scipy), centroid, spread, skewness, slope, rolloff, flatness, crest, odd-to-even-Harmonic-Ratio, harmonic deviation (Peeters/Kazazis).
- Psychoakustisch (DAGA 2025): **Sharpness DIN 45692** ↔ brightness (r≈0.57–0.73), **Roughness Vassilakis (log)** ↔ roughness (r≈0.82–0.87), **HPSS-ΔLoudness** (median filter via scipy.ndimage) ↔ percussiveness.
- Zeitlich: env-RMS + **DTW** (haben wir), attack time, spectral flux, frame_cos (haben wir).
- Pitch: F0 per Autokorrelation (scipy) → Oktav-Deltas in Halbtönen (besser als d1-flag für A008-Verdacht).
- Parameter-Ebene (haben wir): SNDD/qpat-Diff, `unmapped`-Listen.

### 4.4 Spike 2026-11-17: CLAP vs MERT auf unseren 9 Paaren (eigene Daten)

`scripts/spike_mert_clap_eval.py` (Ergebnis: `recordings/mert_clap_eval_20261117_213852.json`):
die 9 pegel-angeglichenen WAV-Paare `ab_<LOC>_20261115_*_n72_w0_{blo,irr}.wav` mit drei
GGUFs via clap-cpp eingebettet, Cosine-Score vs Benutzer-Ratings (`phaseb_ratings_raw.json`):

| Modell (GGUF, clap-cpp) | Scores (Bereich) | Spearman ρ vs Benutzer (n=9) |
|---|---|---|
| `larger_clap_music_and_speech-q8_0` (bisher Produktion) | 60–84 | **+0.227** |
| `larger_clap_music-q8_0` (music-only) | 84–99 (komprimiert oben) | **+0.462** |
| `MERT-v1-95M-q8_0` (24 kHz, Resample) | 76–92 | **+0.454** |

Befunde: auf unseren Daten **CLAP music-only ≈ MERT**, beide klar vor dem bisherigen
`music_and_speech`; MERT hat die bessere Score-Spanne (weniger Sättigung oben), CLAP-music
 die etwas höhere Rangkorrelation. Caveats: n=9 verrauscht; MERT hier nur mean-gepoolt
(768-d), MERIT-style Layer-Concat (3–6+23) geht nicht via GGUF; MERT-Lizenz CC-BY-NC-4.0.

### 4.5 Konsequenz fürs Tool (aktualisiert)

- **Embedding-Distanz**: primär **CLAP music-only GGUF** (`larger_clap_music-q8_0`, Spike 4.4: ρ +0.46 > music_and_speech +0.23 auf unseren Paaren; music-only laut M2D-CLAP auch bei Pitch vorne) mit `embed_cos` + `embed_l2`; **zweite Distanz: wMFCC/MFCC-cosine** (numpy, kompetitiv laut Benchmark); optional als dritte: **MERT-v1-95M-GGUF** via gleichem clap.cpp-Pfad (ρ +0.45, bessere Score-Spanne; Lizenz CC-BY-NC) oder MuQ-MuLan-GGUF für EQ/Reverb-Deltas; Music2Latent + Huang-Style nur als HF-Referenz im Eval (torch vorhanden, transformers 4.47.1 hat kein MERT – GGUF-Pfad ist der richtige).
- **Per-Attribut-Scores ohne Training**: CLAP-Text-Prompts (EN) für bright/dull/rough/percussive + DSP-Traits als harte Deltas.
- **Eval gegen Human Ratings**: `timbremetrics`-Paket + NSynth als Referenzskala, statt nur eigener n=9-Spearman.
- **LLM-Urteile** (lfm3-omni audio, d1-omni profile, optional qwen2.5-omni): nur Erklär-Schicht — eigener Befund + „Don't CLAP“.

## 5. Referenzen

- Tian, Lattner, Saitis: „Assessing the Alignment of Audio Representations with Timbre
  Similarity Ratings", ISMIR 2025, arXiv:2507.07764 (Huang-Style-Embeddings, MFCC
  kompetitiv, cosine+L2, triplet agreement).
- Cheng & Lerch: „Don't CLAP: Are Music-Text Models Bag-of-Words?", arXiv:2609.30540 (2026).
- MERIT: „Learning Disentangled Music Representations for Audio Similarity",
  arXiv:2605.27346 (2026) – 3 Heads Melodie/Rhythmus/Timbre auf MERT.
- arXiv:2611.14415 (Nov 2026): Post-hoc CSN-Disentanglement gefrorener Foundation-Embeddings.
- arXiv:2601.19109 (Jan 2026): CLAP/MuQ-MuLan auf ABX; instrumenten-gewichtetes Cosine via MSS.
- TISMIR 2026: „Cross-Cultural Music Similarity…", tismir.341 – CLAP-Music&Speech beste Alignment.
- arXiv:2606.30369 (2026): Timbre-Trait-Predictor (20 Reymore-Huron-Qualia) auf CLAP für
  Synthesizer-Eval statt FAD.
- SynthCloner, arXiv:2509.24286 (2026): Timbre-vs-ADSR-Entkopplung für Synth-Sounds.
- arXiv:2506.22628 (2025): sound-matching losses – soft-DTW auf Envelope, JTFS, MSS, P-loss.
- Czedik-Eysenberg & Reuter, DAGA 2025: Sharpness↔brightness, Vassilakis(log)↔roughness,
  HPSS-Δloudness↔percussiveness; Pitch-Abhängigkeit von Brightness.
- McAdams 2019 (Timbre chapter); Kazazis 2021 (JASA, ordinal scaling spectral descriptors);
  Peeters 2011 (descriptor set); CMMR 2021 survey (Distanzmetriken: Manhattan/Euclidean/
  Cosine/KL/EMD/Levenshtein).
- M2D-CLAP, IEEE SPL 2025: general vs music CLAP auf Musik-Tasks.
- clap.cpp (gorse-io, Stand 2026-11): GGUF-Support CLAP/CLaMP3/MERT/MuQ/MuQ-MuLan,
  10-s-Fenster mit repeat-pad, 48 kHz.
- Repo-intern: `docs/PHASEB-EVAL-2026-11-14.md`, `docs/HANDOVER-2026-11-15.md`,
  `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md`, `bloridium/sim.py`,
  `bloridium/sim_embed.py`.
