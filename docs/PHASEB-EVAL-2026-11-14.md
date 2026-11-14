# Phase-B-Eval 2026-11-14 — Embedding-Score vs Phase A vs Höreindruck

Spec: `docs/superpowers/specs/2026-11-14-phaseb-sim-embed-design.md` · Plan Task 10.
Modelle: CLAP `larger_clap_music_and_speech` Q8_0 (models/), ollama `lfm3-omni:2b` (audio mode).

## Ergebnis-Tabelle (offline, `scripts/sim_eval_offline.py`)

| Paar | Phase A score | embed_score | combined | verdict |
|---|---|---|---|---|
| ab_A043_20261108_142609 | fehler (Iridium stumm) | – | – | fehler |
| ab_A043_20261108_143856 | fehler (Iridium stumm) | – | – | fehler |
| ab_A043_20261108_144314 | fehler (Iridium stumm) | – | – | fehler |
| **ab_A043_20261114_153000** (live, A043 vs PC114 @ C5) | **93.08** | **56.61** | **74.84** | nahe |
| check_20261108_152813 | 98.50 | 88.23 | 93.37 | nahe |

JSON: `recordings/phaseb_eval_20261114_152700.json` / `..._153019.json`.

**Beobachtung:** Phase A nennt das A043-Paar „nahe" (93), der Embedding-Score sieht den
Charakter-Unterschied deutlich (56.6). Das LLM-Urteil (live, `sim compare --live --embed --llm`)
liefert dazu die Begruendung: *„Iridium klingt rau, koernig, fehlender klarer scharfer
Klangcharakter vs A klar/scharf“* (llm score 85, mode audio).

## Live-A/B mit Phase B (Hardware wieder dran)

```
python3 -m bloridium sim compare --live --note 72 --dur 1.6 \
    --blofeld A043 --iridium-slot 114 --embed --llm
# -> Score 94.59 (nahe) | embed_score 55.49 | combined 75.04 | llm[audio] 85 "rau, koernig..."
```

PC-Vorwahl: Blofeld Bank A PC42 (A043), Iridium Favorites-Set 6 PC114 (SH Power) —
kein CC0/CC32 am Iridium senden (rdb-Map!), siehe `scripts/sim_sweep_pcs.py` DEFAULT_MAP
(2026-11-14: A001=108 … A073=116).

## Spike: saina-helm-3-0.8b (Decision-Modell) — NICHT nutzbar via ollama 0.40.16

- `/api/chat` und `/api/generate`: 400 „does not support chat/generate“ — Decision-Modelle
  laufen ueber `POST /v1/systemone` (`{model, state, questions, images}`; score-Kriterien
  als Array 2–10 Level, noul-Kriterien als {false, true}).
- Aber: `run-saina/saina-helm-3-0.8b` laedt nicht — llama-server: „wrong number of tensors;
  expected 326, got 320“ (inoffizielle Decision-GGUF, von ollama nicht zertifiziert).
  **Fazit:** saina-helm lokal nicht lauffaehig; LLM-Urteil bleibt `lfm3-omni:2b` (chat, audio
  mode, verifiziert). `/v1/systemone` + Spektrogramm-PNGs bleibt als Option fuer zukuenftige
  kompatible Decision-Modelle (vision capability).

## Bewertungen (post-hoc, 0–100) — vom Benutzer auszufuellen

Entscheidet (Q1, 2026-11-14): Der Benutzer bewertet jedes brauchbare Paar NACHDEM die
Scores vorliegen (post-hoc — Caveat: Scores koennen das Urteil faerben).
Eintragen als JSON fuer `sim_eval_offline.py --ratings`, z. B. `recordings/phaseb_ratings.json`:

```json
{"ab_A043_20261114_153000": 0, "check_20261108_152813": 0}
```

| Paar | Hoereindruck 0–100 (aehnlich?) | Bemerkung |
|---|---|---|
| ab_A043_20261114_153000 | ___ | |
| check_20261108_152813 | ___ | |

Danach: `python3 scripts/sim_eval_offline.py --ratings recordings/phaseb_ratings.json`
→ Spearman-Rangkorrelation von score / embed_score / combined gegen die Bewertungen.
