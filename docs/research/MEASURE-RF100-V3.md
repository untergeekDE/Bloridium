# RF100 v3 — Konvertierung, SD-Transfer, Messung und Retraining

**Stand:** 2026-11-22 · **Code:** Bloridium 0.6.0 (Konverter unverändert seit
0.5.3; die qpats in `transfer/rf100_v3` wurden mit 0.5.3 erzeugt)

Ziel: A001–A100 mit dem aktuellen Mapping neu konvertieren, auf die SD-Karte
legen, einen frischen Messlauf (v2-Score) fahren und daraus das Prognosemodell
neu trainieren.

## 1. Konvertierung (offline, kein Gerät nötig)

```bash
python3 scripts/reconvert_rf.py \
  --out transfer/rf100_v3 \
  --sd-dir rf300 \
  --slot-start 300
```

Erzeugt:
- `transfer/rf100_v3/A001_*.qpat` … `A100_*.qpat` (SD-sichere Namen)
- `transfer/rf100_v3/MANIFEST.json` mit `sd_dir`, `remote`, `slot`, `mapped`,
  `unmapped_count`
- `transfer/rf100_v3/MANIFEST.md` als lesbare Übersicht

Der Lauf validiert jedes qpat per Roundtrip-Parse (Version 14, nicht leer) und
bricht bei Namen mit Leerzeichen/Sonderzeichen ab. `transfer/` ist gitignored;
das Manifest ist die Übergabe.

**Bereits erzeugt (2026-11-21):** 100 qpats, gemappt 141–220 (Mittel 170,3),
SD-Ordner `rf300`, Slots 300–399.

## 2. SD-Karte

```bash
cp -R transfer/rf100_v3 /Volumes/<SD>/rf300
```

Wichtig: Ordnername muss `rf300` sein, Dateinamen **nicht** umbenennen. Die
Iridium-Shell hat kein Quoting; die Namen sind bereits ohne Leerzeichen.

## 3. Messung (Hardware)

Vor dem Lauf: Iridium SD als Laufwerk `2:` gemountet, beide Synths über USB.

```bash
# nur lesen: sind alle 100 qpats auf der Karte (Name + Byte-Größe)?
python3 scripts/measure_rf100.py --verify-sd

# ohne --run passiert nichts am Gerät (nur Plan-Ausgabe)
python3 scripts/measure_rf100.py

# echter Lauf, Notes 72 und 60, schreibt recordings/sim_log_v3.jsonl
# (--skip-verify, wenn --verify-sd direkt davor 100/100 geliefert hat)
python3 scripts/measure_rf100.py --run --skip-verify
```

Der Runner:
- prüft `ls 2:rf300` gegen **Name und Byte-Größe** der lokalen qpats (Größen
  unterscheiden v2/v3, die Namen nicht),
- lädt jedes qpat per `load-patch <slot>` aus den Slots 200–299.
  **Falle:** `load-patch 2:<dir>/<file>.qpat` wird akzeptiert, ändert den
  Edit-Buffer aber **nicht** (am 2026-11-22 per Readback bewiesen). Nur die
  Slot-Nummer lädt wirklich.
- prüft nach jedem Load drei Parameter per `get-param` gegen das qpat
  (`Osc1FinePitch`, `Filter1CutOff`, `Filter1EnvAmount`); Abweichung > 0,002
  bricht ab — damit kann kein stiller Fehlload mehr durchrutschen,
- prüft nach jedem Laden, dass die device shell noch antwortet (sonst Abbruch),
- wählt am Blofeld Bank A + PC,
- spielt beide Synths gleichzeitig (Part 1, ch6) und scorst mit v2,
- bricht nur ab, wenn der Iridium-Kanal wirklich tot ist (echte Stille oder
  > 60 dB unter dem Blofeld); leise Patches (z. B. A003) werden weiter gemessen,
- resumiert standardmäßig über `(loc, note)` bereits gescorte Zeilen
  (`--no-resume` für einen kompletten Neulauf).

**Shell-Eigenheiten (live):** `ls` blockiert den device readout für einige
Zeit; deshalb prüft `--verify-sd` in einer eigenen Sitzung und der Messlauf
läuft mit `--skip-verify` weiter. Der Readout liefert max. 256 B pro `U`-Poll
und die Shell antwortet verzögert, daher nutzt der Runner einen `temp`-Sentinel
statt eines einzelnen `cmd()`.

Empfohlene Hygiene: Iridium-USB-Audio-Rauschen prüfen, FX-Zustand pro Patch
nicht manuell ändern, `CC7=127` nur am Blofeld (am Iridium ist CC7 ein
Parameter).

## 4. Retraining

```bash
python3 -m bloridium prognose entropy --log recordings/sim_log_v3.jsonl
python3 -m bloridium prognose train \
  --log recordings/sim_log_v3.jsonl \
  --dumps dumps \
  --target score \
  --model models/prognose_rf_v3.pkl
```

Bewertung wie beim v2-Lauf:
- `n` sollte ~100 Locs sein; `error/silent`-Zeilen werden übersprungen.
- Nur shippen, wenn `R² > 0` (Holdout) und `R²_cv` nicht schlechter als v2
  (`0.064 / 0.132`). Sonst `models/prognose_rf.pkl` unverändert lassen.
- Top-Features und `MAE` im Commit dokumentieren.

## 5. Offene Punkte

- [x] SD-Karte kopieren (`transfer/rf100_v3` → `rf300/`; Slots 200–299).
- [x] `--verify-sd` → 100/100 (Name + Byte-Größe, 2026-11-22).
- [ ] Messlauf `--run --skip-verify` (200 Zeilen: 100 Locs × Notes 72/60).
- [ ] Entropy-Check auf dem neuen Log.
- [ ] Retrain + Modellvergleich; nur bei positivem R² ersetzen.
- [ ] `sim_log_v3.jsonl` und Modell-Metriken in `docs/FINDINGS.md` dokumentieren.
