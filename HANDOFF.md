# HANDOFF 2026-11-14 — Session-Neustart (kurz: Stand + Anforderung + nächste Schritte)

## Stand (Ende Session 2026-11-14)
- **Filter-Routing-Fix erledigt** (`bloridium/qpat_map.py` + `tests/test_qpat_map.py`, 2 neue Tests): Blofeld `Filter Routing=1` (seriell: A001, A008, A022, A039, A071, A073) -> F2 in DigiFormer, `Filter2State=Off`, `FilterLink=Single` (NICHT `Linked` — war stummes-B-Verdacht A008), Routing „Filter > Former"; `Filter Routing=0` (parallel: A010, A019, A043) -> Routing „Parallel", Former=Bypass, F2 bleibt Filter 2 (`Active`; F2=Bypass -> `Off`). **228 Tests grün** (1 skipped).
- **Alle 9 qpats neu generiert** (14. Nov 16:39, v14) offline aus `dumps/blofeld_sndd_<LOC>_*.bin` (chk_ok=True) -> `transfer/`; **Upload-Paket neu gebaut**: `transfer/upload/A0xx_*.qpat` (Stick-Namen, byte-identisch zu `transfer/`) + `MANIFEST.md` aktualisiert (neue Routing-Spalte, Stand 2026-11-14); `calib/200–206` unverändert. **Noch NICHT auf den Iridium geladen.**
- Phase B fertig: CLAP-Embedding (`models/larger_clap_music_and_speech-q8_0.gguf` via pip `clap_cpp`) + ollama-Urteil (`lfm3-omni:2b`, audio-mode, Pegel-Cap `judge-v2-pegel`). CLI: `bloridium sim compare --npy/--live [--embed] [--llm] [--strict]`, `bloridium ab --embed/--llm`. saina-helm-3-0.8b läuft nicht in ollama 0.40.16 (GGUF wrong tensor count) — nicht nutzen. Spec/Plan: `docs/superpowers/specs|plans/2026-11-14-phaseb-sim-embed*`; Eval: `docs/PHASEB-EVAL-2026-11-14.md`.
- **Hardware dran:** Blofeld+Iridium an Launchpad-DIN (ch5 / ch6 Part 1), Scarlett 18i8; Iridium-USB ab (Masseschleife). `python3 -m bloridium status` -> beide VERBUNDEN.
- Iridium Favorites Bank 6 (Set 6): mido-PC A001=108, A008=109, A010=110, A019=111, A022=112, A039=113, A043=114, A071=115, A073=116 (= „MIDI-Nummer"−2; DEFAULT_MAP in `scripts/sim_sweep_pcs.py`, Reihenfolge wie `transfer/upload/MANIFEST.md`).
- **PC-Umschaltung am Iridium DEFEKT seit Reconnect** (kein NRPN Pid 3113; PC108/109/114 liefern denselben Klang — geraeteseitig PC-Mode/Bank/Map). Workaround: Favoriten am Panel wählen, nur Note per MIDI (ch6, Part 1). Blofeld-PC (Bank A, PC=loc−1) geht.
- CP70-Piano gebaut: `transfer/cp70/` (qpat v14, 245 WAVs, MANIFEST.md).
- Git: Fix + Tests + `transfer/` + `transfer/upload/` + MANIFEST u. a. sind **uncommitted** (`git status`).

## Anforderung aus docs/HANDOVER-2026-11-14.md (offen, delegiert an Human mit Tool)
- **OS4-Pid-Verifikation**: `bloridium explore` (interaktive Session) — braucht **Iridium-USB kurz angestossen** (DIN liefert kein Panel-NRPN, siehe HANDOVER-2026-11-12), dann Panel drehen + Enter. CSV-State: `docs/midi-maps/iridium_os4_cc_list.csv`, Log: `recordings/explore_log.jsonl`.

## Nächste Schritte
1. User lädt das neue Upload-Paket auf den Iridium: FAT32-Stick mit `transfer/upload/` -> `Load>Actions>Import` -> Favorites Bank 6 (PC 108–116 lt. MANIFEST; calib 200–206 Testreihe bleibt).
2. A/B-Review weiter **ab A008**: am Panel Set-6-Eintrag drehen, dann A/B anspielen (Blofeld-PC + Iridium Note C5 auf ch6, nacheinander, nur Part 1), Score Phase A + embed + llm ausgeben (`scripts/sim_compare.py --live ...`), User bewertet 0–100 + Text -> `recordings/phaseb_ratings_raw.json`. Zum Schluss `python3 scripts/sim_eval_offline.py --ratings …`.
3. OS4-Pid-Verifikation (siehe Anforderung oben) — braucht Iridium-USB kurz.
4. Später: PC-Umschaltung am Iridium klären, Env-Zeiten-Skalierung (nicht linear), CC0-Nachstellen erst viel später, Sounds „as they are" vergleichen.

## Eherne Regeln (Details im globalen Skill `bloridium`)
- Nur Part 1 (ch6) triggern; vor jeder Messung CC123=0 + **CC7=127** auf allen 16 Kanälen (CC7=0 = stumm!). Iridium-USB ab (Masseschleife), MIDI via Launchpad-DIN, `Global > MIDI = an`. Scarlett: Blofeld In 3/4, Iridium In 5/6, 48 kHz. Note 72 (C5) ist die beste Vergleichs-Oktave.
- Bipolar-Falle: Matrix-Amounts um 0.5 zentriert; AmpVelo unipolar -> `0.5+0.5*norm`. F2-Bleed: `Filter2State=2.0 'Off'`.
- Dump/Konvertieren: `python3 -m bloridium convert <LOC> --dump dumps/blofeld_sndd_<LOC>_*.bin` -> `transfer/<Name>_<LOC>.qpat` (v14).
