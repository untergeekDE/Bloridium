# Phase-B-Eval 2026-11-14 (CLAP-Embedding + LLM-Urteil vs Phase A)

Spec: `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md`
Plan: `docs/superpowers/plans/2026-11-14-phaseb-sim-embed.md` (Task 10)

## Setup

- CLAP: `models/larger_clap_music_and_speech-q8_0.gguf` (gorse-io, Q8_0, Apache-2.0) via clap-cpp 0.1.1, 512-d Embedding, `embed_score = 100*clip(cos,0,1)`.
- LLM: ollama `lfm3-omni:2b`, Modus **audio** (base64 WAV im `audio`-Feld akzeptiert), Prompt-ID `judge-v2-pegel`, Contract `{"score":0-100,"summary","differences"}`.
- `combined = 0.5*score + 0.5*embed_score`; LLM-Score informativ, nicht in combined.
- Offline-Eval: `python3 scripts/sim_eval_offline.py` -> `recordings/phaseb_eval_20261114_171001.json`.

## Tabelle (Eval 2026-11-14 17:10)

| Paar | Phase A score | embed_score | combined | verdict |
|---|---|---|---|---|
| ab_20261114_170201 (A001 live) | 92.3 | 32.24 | 62.27 | nahe |
| ab_A001_20261114_154306 | – | – | – | fehler (Stille) |
| ab_A001_20261114_160154 | 94.2 | 41.73 | 67.97 | nahe |
| ab_A008_20261114_160856 | – | – | – | fehler (Stille) |
| ab_A043_20261108_142609 | – | – | – | fehler (Stille) |
| ab_A043_20261108_143856 | – | – | – | fehler (Stille) |
| ab_A043_20261108_144314 | – | – | – | fehler (Stille) |
| ab_A043_20261114_153000 | 93.08 | 56.61 | 74.84 | nahe |
| check_20261108_152813 (Referenz) | 98.5 | 88.23 | 93.37 | nahe |

Live-Messung 2026-11-14 17:00:55 (A001 Blofeld vs Iridium Set6/PC108, note 72):
Phase A **91.19** (spec_cos 0.9116, env_dtw 0.0876, verdict nahe), embed **32.0**, combined **61.59**,
LLM **5** — Grund laut LLM: Iridium **-66.5 dBFS** vs Blofeld **-22.9 dBFS** (Pegel, ~44 dB zu leise).
Log: `recordings/sim_log.jsonl` (ts 20261114_170055, prompt_id `judge-v2-pegel`).

## Befunde

- Phase A ist pegel-invariant (normiert) -> hohe Scores trotz Pegel-Fehler.
- CLAP-Embedding und LLM reagieren auf Pegel -> embed/combined/LLM brechen ein.
  **Pegel-Normierung vor Phase B pruefen** (oder Scarlett-Gain Iridium In 5/6 / Iridium Master).
- check-Paar (gleiches Geraet) embed 88.23 -> Embedding diskriminiert prinzipiell.
- Filter-Cutoff-Skala (Blofeld raw -> Iridium norm) ist norm()-direkt falsch
  (A001 am Iridium: Filter1 416 Hz, DF 199 Hz; Blofeld F1 raw 64 / F2 raw 52) ->
  Cutoff-Kalibrierung (Blofeld CC-Sweep + Peak-Messung -> Hz) steht aus (HANDOVER-2026-11-10 Plan 4).
- Osc-Octave-Vorzeichen gefixt 2026-11-14 (`qpat_map.py`: raw-64 statt 64-raw,
  A001 Osc3 raw 52 -> CoarsePitch 12.0 statt 36.0; Test `test_osc_octave_sign_a001`).

## Bewertung durch Benutzer (post-hoc, 0-100 Hoereindruck) — TODO

| Paar | Blofeld | Iridium | Phase A | embed | combined | LLM | Benutzer 0-100 | Bemerkung |
|---|---|---|---|---|---|---|---|---|
| A001 live 170055 | A001 | Set6 PC108 | 91.19 | 32.0 | 61.59 | 5 | | Pegel -66 dBFS; Filter 416/199 Hz |
| ab_A001_20261114_160154 | A001 | ? | 94.2 | 41.73 | 67.97 | – | | |
| ab_A043_20261114_153000 | A043 | ? | 93.08 | 56.61 | 74.84 | – | | |
| check_20261108_152813 | – | – | 98.5 | 88.23 | 93.37 | – | | Referenz |

Ratings als JSON `{"<pair>": 0-100}` -> `python3 scripts/sim_eval_offline.py --ratings ratings.json`
-> Spearman score/embed/combined gegen Benutzer-Bewertung.

**Caveat post-hoc:** Benutzer bewertet nach Kenntniss der numerischen Scores (nicht blind).

## Live-Durchlauf 9 Presets 2026-11-14 (Set 6 PC108-116, Note 72, Manual-Panel-Modus)

Iridium-PC-Umschaltung defekt (HANDOVER-2026-11-14) -> Favoriten am Panel gedreht,
nur Noten per MIDI; Blofeld-PC (Bank A) vom Skript. Skript: `scripts/sim_manual_compare.py`
(mode=`manual_panel`, Log `recordings/sim_log.jsonl`, ts 20261114_175046-180616).
**Pegel-Normierung vor Phase B aktiv** (`norm_pegel=True` in `score_pair_embed`:
embed/LLM auf Peak 0.5 angeglichen, Phase A + peak_dbfs roh) — Iridium roh weiterhin
15-30 dB unter Blofeld (Seriell-Patches A001/A008/A039/A073 am staerksten, bis -64.8 dBFS
Peak; nach Norm ist der RMS-Abstand gering, embed springt dadurch 29 -> 75.6 bei A001).
WAVs (pegel-angeglichen, Peak 0.5) zum Reinhoeren: `recordings/ab_<LOC>_20261114_*_n72_{blo,irr}.wav`.

| Preset | Iridium PC | ts | Phase A | embed | combined | LLM | Peak A/B dBFS | Benutzer 0-100 | Bemerkung |
|---|---|---|---|---|---|---|---|---|---|
| A001 JMX jun | 108 | 175046 | 92.86 | 75.58 | 84.22 | 45 | -19.4 / -47.9 | 70 | Leiser, Filter zu weit geschlossen, LFO1 Filter wirkt zu stark |
| A008 Easy Piano | 109 | 175216 | 95.20 | 69.35 | 82.28 | 45 | -25.6 / -64.8 | 45 | Kaum zu hoehren; vermutl. 1 Oktave tiefer, sehr stark abgefiltert |
| A010 Wurly Piano1 | 110 | 175258 | 97.00 | 78.22 | 87.61 | 45 | -44.2 / -42.8 | 80 | Hohe Lagen anderer Charakter (hohle square wave) |
| A019 Tines DocT | 111 | 175329 | 95.05 | 87.77 | 91.41 | 45 | -29.4 / -45.5 | 90 | Reagiert nicht auf Aftertouch |
| A022 ModWheelOrgDrive | 112 | 180424 | 94.74 | 83.62 | 89.18 | 45 | -15.5 / -29.2 | 95 | Iridium hörbar anderer Charakter, aber sehr aehnlich; mittl. Oberton am Blofeld lauter? |
| A039 A Elektro | 113 | 180454 | 96.07 | 77.22 | 86.64 | 45 | -37.9 / -55.3 | 90 | Viel leiser; Delay beim Blofeld |
| A043 SH Power | 114 | 180519 | 95.02 | 78.38 | 86.70 | 45 | -19.3 / -35.6 | 75 | Blofeld voller (Filter tiefer weiter geschlossen); Iridium stark Aftertouch-Bending; Problem Channel->Poly Aftertouch |
| A071 Windowed SYNC2FM | 115 | 180547 | 94.38 | 86.71 | 90.54 | 45 | -23.2 / -40.6 | 70 | Kein Sync beim Iridium |
| A073 Chord Hose T | 116 | 180616 | 96.63 | 81.01 | 88.82 | 45 | -27.0 / -53.9 | 85 | Unterschiedliche Effekte, aehnlicher Grundcharakter, Blofeld schneidender |

Benutzer-Ratings: `recordings/phaseb_ratings_raw.json`.
Spearman Benutzer vs Metrik (n=9): Phase A **+0.27**, embed **+0.50**, combined **+0.52**
-> embed/combined korrelieren besser mit dem Hoereindruck als Phase A allein.

## LLM-Judge-Vergleich 2026-11-15 (d1-omni vs lfm3-omni auf denselben 9 WAV-Paaren)

Spike: `scripts/spike_d1_omni_eval.py` -> `recordings/d1_omni_eval_20261115_083238.json`.
d1-omni:600m (Liquid AI, System One `/v1/systemone`, 850 MB) als **score**-Question
(10 Levels) ueber Spektrogramm-PNGs, zwei Varianten: zwei Einzelbilder (spec2img) vs
ein Side-by-Side-Bild (spec1img). Baseline lfm3-omni:2b im audio-Modus.

| Preset | Benutzer | lfm3 audio | d1 spec2img | d1 spec1img |
|---|---|---|---|---|
| A001 | 70 | 85 | 95.9 | 87.9 |
| A008 | 45 | 85 | 92.0 | 88.1 |
| A010 | 80 | 85 | 91.7 | 86.1 |
| A019 | 90 | 85 | 95.3 | 88.3 |
| A022 | 95 | 85 | 93.2 | 88.1 |
| A039 | 90 | 85 | 92.7 | 86.1 |
| A043 | 75 | 85 | 92.7 | 88.5 |
| A071 | 70 | 85 | 93.3 | 87.0 |
| A073 | 85 | 85 | 96.0 | 89.4 |

Spearman vs Benutzer (n=9): lfm3-audio **+0.35** (degeneriert: konstant 85 auf
pegel-angeglichenen Clips), d1-spec2img **+0.07**, d1-spec1img **+0.12**.

**Befund:** d1-omni ist fuer Synth-Timbre-A/B nicht geeignet — Scores kollabieren bei
88-96 (Musik-Spektrogramme sehen fuer das Modell alle aehnlich aus; Audio-Encoder ist
auf englische Sprache trainiert, nicht Musik). lfm3-omni im spec-Modus halluziniert
("Bildschirme", Spearman -0.39). **Fazit: embed/combined (ρ 0.50/0.52) bleiben die
besten automatischen Proxy-Scores; LLM-Urteil bleibt informativ-only.**
Fix aus dem Spike: `_extract_json` in `sim_embed.py` jetzt balancierter Brace-Scan
(Prosa/Code-Fences nach dem JSON brachen den Greedy-Match; 2/9 spec-Calls schlugen fehl),
Tests in `tests/test_sim_embed.py` (236 passed).

### d1-omni als Differenz-Profiler (noul-Fragen, Englisch) — 600m vs 2b

Spike: `scripts/spike_d1_profile_eval.py` -> `recordings/d1_profile_eval_20261115_084819.json`.
Pro Paar ein `/v1/systemone`-Call mit images=[spekA, spekB] + 8 Fragen: `similarity`
(score 10 Levels) sowie noul `same_pitch, octave_lower, brighter, darker, noisier,
punchier, same_overall`.

| Preset | Benutzer | 600m score | 2b score | 2b Flags (p>=0.5) |
|---|---|---|---|---|
| A001 | 70 | 95.9 | 63.5 | darker |
| A008 | 45 | 92.0 | 59.3 | octave_lower, brighter, darker |
| A010 | 80 | 91.7 | 64.6 | brighter, darker |
| A019 | 90 | 95.3 | 67.3 | brighter, darker |
| A022 | 95 | 93.2 | 61.9 | darker, noisier |
| A039 | 90 | 92.7 | 65.9 | darker |
| A043 | 75 | 92.7 | 67.0 | brighter, darker |
| A071 | 70 | 93.3 | 67.3 | darker |
| A073 | 85 | 96.0 | 64.3 | octave_lower, brighter, darker |

Spearman vs Benutzer: score 600m +0.07 / 2b +0.13; `diff_count` 600m **-0.38**
(richtige Richtung: mehr Flags = niedrigere Benutzerwertung), `score-k*diff` 600m +0.32;
2b-Varianten schlechter. Flag-Praevalenz: `darker` 7/9 (600m) bzw. 9/9 (2b) — deckt sich
mit den Benutzer-Bemerkungen ("Filter zu", "abgefiltert", "Blofeld voller");
`octave_lower` bei 2b nur A008 (p=0.50, grenzwertig) + A073 — Benutzer-Verdacht A008
"1 Oktave tiefer" also nur schwach bestaetigt. 600m ist bei noul teils saturiert
(octave_lower 9/9, same_pitch 4/9).

**Befund:** d1-omni:2b ist als absoluter Score kritischer (59-67 statt 92-96), aber als
Ranking immer noch schwaecher als embed/combined (+0.13 vs +0.52, n=9 verrauscht).
Wertvoll ist das **noul-Profil als Erklaer-Schicht** (Flags matchen Benutzer-Bemerkungen),
nicht als Score. **Integriert 2026-11-15:** `D1ProfileBackend` in `sim_embed.py`,
`profile`-Feld im Ergebnis/Log, `--profile` in `sim_compare.py` / `sim_manual_compare.py`
/ `bloridium sim compare` (Default `d1-omni:2b`). combined bleibt Phase-B-Score.

Befunde:
- Phase A 92.9-97.0 (alle "nahe"), combined 82.3-91.4 — Rangfolge: A019 > A071 > A073 >
  A022 > A010 > A039 ~ A043 > A001 > A008.
- LLM konstant 45 mit identischer Begruendung ("deutlich leiser") trotz pegel-angeglichener
  Clips -> in diesem Run nicht diskriminierend, nur informativ.
- Roh-Pegel des Iridiums bleibt bei Seriell-Patches (Filter>Former) deutlich zu niedrig
  (bis -64.8 dBFS Peak) — Scarlett-Gain In 5/6 oder Patch (DigiFormer-Amount) Klaerung offen.
- Fruehere A001-Runs ohne norm_pegel (ts 174650/174915): embed 44.6/29.0, LLM 15/5.
