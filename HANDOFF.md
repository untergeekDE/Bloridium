# HANDOFF 2026-11-14 (kurz — nur Stand + nächste Schritte)

## Stand
- **Phase B fertig, 226 Tests grün.** `bloridium/sim_embed.py`: CLAP-Embedding (`models/larger_clap_music_and_speech-q8_0.gguf` via pip `clap_cpp`) + ollama-Urteil (`lfm3-omni:2b`, audio-mode, Pegel-Cap `judge-v2-pegel`). CLI: `bloridium sim compare --npy/--live [--embed] [--llm] [--strict]`, `bloridium ab --embed/--llm`. Skripte: `scripts/sim_compare.py`, `scripts/sim_eval_offline.py`, `scripts/fetch_models.py`. Spec/Plan: `docs/superpowers/specs|plans/2026-11-14-phaseb-sim-embed*`. Eval: `docs/PHASEB-EVAL-2026-11-14.md`.
- saina-helm-3-0.8b läuft nicht in ollama 0.40.16 (GGUF wrong tensor count) — nicht nutzen.
- **Hardware dran:** Blofeld+Iridium an Launchpad-DIN (ch5 / ch6 Part 1), Scarlett 18i8; Iridium-USB ab (Masseschleife). `python3 -m bloridium status` → beide VERBUNDEN.
- **Iridium-PC-Umschaltung per MIDI defekt seit Reconnect** (kein NRPN Pid 3113; PC108/109/114 liefern denselben Klang). Workaround: Favoriten am Panel wählen, nur Note per MIDI. Blofeld-PC (Bank A, PC=loc−1) geht. In `scripts/sim_sweep_pcs.py` DEFAULT_MAP (Set 6): A001=108, A008=109, A010=110, A019=111, A022=112, A039=113, A043=114, A071=115, A073=116.
- **A/B-Review läuft:** A001 bewertet: 20 („B komplett gefiltert“) in `recordings/phaseb_ratings_raw.json`. A008: Iridium-Seite stumm.
- **Filter-Befund:** Blofeld `Filter Routing=1` (seriell: A001, A008, A022, A039, A071; A073 F2=Bypass) → F2 auf Iridium-DigiFormer, Filter2State=Off, FilterLink=Single, Routing „Filter > Former“. Routing=0 (parallel: A010, A019, A043) → F2 bleibt Filter 2 (Active), Former=Bypass, Routing „Parallel“. Aktuelles `bloridium/qpat_map.py` setzt immer „Filter > Former“ und bei seriell FilterLink=Linked (A008-qpat: FilterLink 7.0) — mutmaßlicher Grund für stummes B.
- CP70-Piano gebaut: `transfer/cp70/` (qpat v14, 245 WAVs, MANIFEST.md).
- OS4-Pids (`bloridium explore`) weiterhin an Human; braucht Iridium-USB kurz (DIN liefert kein Panel-NRPN).

## Nächste Schritte
1. Filter-Routing in `bloridium/qpat_map.py` fixen (seriell/parallel wie oben), Tests in `tests/test_qpat_map.py`, dann `python3 -m pytest tests/ -q`.
2. Alle 9 qpats neu generieren (`python3 -m bloridium convert <LOC> --dump dumps/blofeld_sndd_<LOC>_*.bin`) und `transfer/upload/`-Paket neu bauen.
3. User lädt das Paket neu auf den Iridium (FAT32-Stick → Load>Actions>Import).
4. A/B-Review weiter ab A008: User dreht am Panel Set-6-Eintrag, dann A/B anspielen (Blofeld PC + Iridium Note C5 auf ch6, nacheinander), Score Phase A + embed + llm ausgeben, User bewertet 0–100 + Text → `recordings/phaseb_ratings_raw.json`. Zum Schluss `python3 scripts/sim_eval_offline.py --ratings …`.
5. Später: PC-Umschaltung am Iridium klären, Env-Zeiten-Skalierung (nicht linear), CC0-Nachstellen erst viel später, Sounds "as they are" vergleichen.
