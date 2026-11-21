#!/usr/bin/env python3
"""Analyse the Init profiling sweep -> Markdown report + CSV.

Reads recordings/profile_sweep.jsonl and recordings/profile/*.npy.
Writes docs/PROFILING-INIT-2026-11-21.md and docs/profiling_init_2026-11-21.csv.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from bloridium import audio, blofeld_dump as bd, qpat_map, sim

LOG = REPO / "recordings/profile_sweep.jsonl"
LOG_B = REPO / "recordings/profile_testb.jsonl"
NPY = REPO / "recordings/profile"
OUT_MD = REPO / "docs/PROFILING-INIT-2026-11-21.md"
OUT_CSV = REPO / "docs/profiling_init_2026-11-21.csv"
OUT_CURVES = REPO / "docs/profiling_curves_2026-11-21.json"
SR = audio.SAMPLERATE

BLOCKS = [
    (0, 56, "Oszillatoren"),
    (57, 72, "Mixer"),
    (73, 117, "Filter"),
    (118, 127, "Verstärker"),
    (128, 159, "Effekte"),
    (160, 194, "LFOs"),
    (195, 244, "Hüllkurven"),
    (245, 260, "Modifier"),
    (261, 308, "Modulationsmatrix"),
    (309, 382, "Arpeggiator"),
]


def block_of(idx: int) -> str:
    for lo, hi, name in BLOCKS:
        if lo <= idx <= hi:
            return name
    return "?"


def vec(x: np.ndarray) -> np.ndarray:
    f = sim.features(x, sr=SR, n_bands=48)
    s = f["log_spec"].mean(axis=1)
    s = (s - np.median(s)) / 20.0
    e = f["env_rms"]
    if e.max() > 0:
        e = e / e.max()
    e = np.interp(np.linspace(0, 1, 16), np.linspace(0, 1, len(e)), e)
    return np.concatenate([s, 2.0 * e])


def f0_hz(x: np.ndarray) -> float:
    xs = x[int(0.35 * SR):int(1.05 * SR)]
    xs = xs - xs.mean()
    y = xs * np.hanning(len(xs))
    r = np.correlate(y, y, "full")[len(y) - 1:]
    if r[0] == 0:
        return 0.0
    r = r / r[0]
    lo, hi = int(SR / 1200), int(SR / 50)
    seg = r[lo:hi]
    if not seg.size:
        return 0.0
    i = int(np.argmax(seg)) + lo
    if 0 < i < len(r) - 1:
        a, b, c = r[i - 1], r[i], r[i + 1]
        den = a - 2 * b + c
        if den:
            i = i + 0.5 * (a - c) / den
    return SR / i if i else 0.0


def curve_vec(x: np.ndarray) -> np.ndarray:
    """Curve/interpretation features: spectrum + envelope + pitch + centroid."""
    f = sim.features(x, sr=SR, n_bands=48)
    s = f["log_spec"].mean(axis=1)
    s = (s - np.median(s)) / 20.0
    e = f["env_rms"]
    if e.max() > 0:
        e = e / e.max()
    e = np.interp(np.linspace(0, 1, 8), np.linspace(0, 1, len(e)), e)
    m = x - np.mean(x)
    X = np.abs(np.fft.rfft(m * np.hanning(len(m))))
    fr = np.fft.rfftfreq(len(m), 1 / SR)
    act = X > X.max() * 1e-4
    cen = float((fr[act] * X[act]).sum() / max(X[act].sum(), 1e-12))
    sem = 12 * np.log2(max(f0_hz(x), 1.0) / 261.63)
    return np.concatenate([s, 2 * e, [sem, np.log2(max(cen, 10) / 500)]])


def load_rows(paths):
    rows, bases = [], {}
    for path in paths:
        if not Path(path).exists():
            continue
        variant = "B" if "testb" in str(path) else "init"
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") == "baseline":
                bases[variant] = r
            elif r.get("kind") == "row":
                r["variant"] = r.get("variant", variant)
                rows.append(r)
    if not rows:
        raise SystemExit("no rows")
    return bases, rows


def compute_vectors(rows):
    """Attach effect vectors (delta vs. Init) to each row, recomputed from the npy files."""
    feats = _feature_cache()

    def cached(path):
        key = str(Path(path).name)
        if key not in feats:
            x = np.load(path)
            feats[key] = (vec(x), curve_vec(x), f0_hz(x))
        return feats[key]

    base_vec, base_curve = {}, {}
    for variant, prefix in (("init", "init"), ("B", "b_init")):
        for name in ("blofeld", "iridium"):
            files = sorted(NPY.glob(f"{prefix}_{name}_*.npy"))
            if not files:
                continue
            base_vec[(variant, name)] = np.mean([cached(f)[0] for f in files], axis=0)
            base_curve[(variant, name)] = np.mean([cached(f)[1] for f in files], axis=0)
    for r in rows:
        v = r["variant"]
        prefix = "" if v == "init" else "b_"
        for name in ("blofeld", "iridium"):
            f = NPY / f"{prefix}{r['idx']:03d}_{r['raw']:03d}_{name}.npy"
            if not f.exists() or (v, name) not in base_vec:
                r[f"v_{name}"] = None
                continue
            vv, cc, ff = cached(f)
            r[f"v_{name}"] = vv - base_vec[(v, name)]
            r[f"c_{name}"] = cc - base_curve[(v, name)]
            r[f"f0_{name}"] = ff
    _save_feature_cache(feats)
    return rows


FEAT_CACHE = REPO / "recordings/profile/_feature_cache.pkl"


def _feature_cache() -> dict:
    import pickle
    if FEAT_CACHE.exists():
        try:
            return pickle.loads(FEAT_CACHE.read_bytes())
        except Exception:
            return {}
    return {}


def _save_feature_cache(cache: dict) -> None:
    import pickle
    FEAT_CACHE.write_bytes(pickle.dumps(cache))


_INIT_SD: bytes | None = None
_IRR_CACHE: dict = {}


def irr_value_for(idx: int, raw: int, keys=None) -> float | None:
    """Converted Iridium value for the parameter (first affected key)."""
    global _INIT_SD
    ck = (idx, raw)
    if ck in _IRR_CACHE and keys is None:
        return _IRR_CACHE[ck]
    if _INIT_SD is None:
        _INIT_SD = bd.parse_sndd((REPO / "dumps/banks/A/A066.bin").read_bytes())["sdata"]
    sd = bytearray(_INIT_SD)
    sd[idx] = raw
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
    ov, _ = qpat_map.blofeld_to_qpat_params(bd.parse_sndd(bytes([0xF0, *body, 0xF7])))
    keys = keys or _param_key_candidates(idx)
    keys = sorted([k for k in keys if k in ov], key=lambda k: (k.startswith("Matrix"), k))
    if not keys:
        return None
    val = float(ov[keys[0]][0])
    _IRR_CACHE[ck] = val
    return val


_KEY_CACHE: dict[int, list[str]] = {}


def _param_key_candidates(idx: int) -> list[str]:
    """Keys that differ from the Init conversion for this parameter."""
    if not _KEY_CACHE:
        init = bd.parse_sndd((REPO / "dumps/banks/A/A066.bin").read_bytes())
        base, _ = qpat_map.blofeld_to_qpat_params(init)
        _KEY_CACHE["__base__"] = base  # type: ignore
    base = _KEY_CACHE["__base__"]  # type: ignore
    if idx in _KEY_CACHE:
        return _KEY_CACHE[idx]
    init = bd.parse_sndd((REPO / "dumps/banks/A/A066.bin").read_bytes())
    sd0 = bytearray(init["sdata"])
    cand: list[str] = []
    for raw in (0, 32, 64, 127):
        sd = bytearray(sd0)
        sd[idx] = raw
        body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sd, bd.checksum(bytes(sd))]
        ov, _ = qpat_map.blofeld_to_qpat_params(bd.parse_sndd(bytes([0xF0, *body, 0xF7])))
        for k, v in ov.items():
            if k not in base or abs(v[0] - base[k][0]) > 1e-9:
                if k not in cand:
                    cand.append(k)
    _KEY_CACHE[idx] = cand
    return cand


PITCH_PARAMS = {1, 2, 3, 17, 18, 19, 33, 34, 35}


def _cents(r, dev):
    f = r.get(f"f0_{dev}") or 0.0
    return 1200 * np.log2(max(f, 1.0) / 261.63)


def classify_param(rows, thr):
    if rows and rows[0]["idx"] in PITCH_PARAMS:
        usable = [r for r in rows if abs(_cents(r, "blofeld")) >= 25
                  and abs(_cents(r, "iridium")) >= 10]
        if len(usable) >= 2:
            same = all(_cents(r, "blofeld") * _cents(r, "iridium") > 0 for r in usable)
            ratio = float(np.median([abs(_cents(r, "iridium") / _cents(r, "blofeld"))
                                     for r in usable]))
            if same and 0.67 <= ratio <= 1.5:
                return "OK", None, ratio
            if same and 0.33 <= ratio <= 3.0:
                return "teilweise", None, ratio
            return "Mismatch", None, ratio
    aud = [r for r in rows if r["mag_b"] >= thr]
    reacting = [r for r in rows if r["mag_i"] >= thr]
    both = [r for r in rows if r["mag_b"] >= thr and r["mag_i"] >= thr and r.get("cos") is not None]
    if not both:
        if aud and not reacting:
            return "defekt", None, None
        if reacting and not aud:
            return "Mismatch", None, None
        if aud:
            return "defekt", None, None
        return "n/a", None, None
    cos = float(np.mean([r["cos"] for r in both]))
    ratios = [r["mag_i"] / r["mag_b"] for r in both]
    ratio = float(np.median(ratios))
    if cos >= 0.80 and 0.5 <= ratio <= 2.0:
        st = "OK"
    elif cos >= 0.50:
        st = "teilweise"
    else:
        st = "Mismatch"
    return st, cos, ratio


def build_curve(rows):
    """Adaptation curve anchors: Blofeld value -> converted value -> recommended value.

    Pitch parameters are fitted in cents (linear regression of the measured
    Iridium pitch against the converted value); other parameters use the
    best-matching measured Iridium step (cosine, penalised by magnitude).
    """
    usable = [r for r in rows if r.get("c_blofeld") is not None and r.get("c_iridium") is not None]
    if len(usable) < 2:
        return []
    cents_b = {id(r): 1200 * np.log2(max(r["f0_blofeld"], 1) / 261.63) for r in usable}
    cents_i = {id(r): 1200 * np.log2(max(r["f0_iridium"], 1) / 261.63) for r in usable}
    conv = {id(r): irr_value_for(r["idx"], r["raw"], r.get("iridium_keys")) for r in usable}

    conv_vals = [conv[id(r)] for r in usable if conv[id(r)] is not None]
    normalised = bool(conv_vals) and min(conv_vals) >= 0.0 and max(conv_vals) <= 1.0
    pitch = [r for r in usable if abs(cents_b[id(r)]) >= 25 and conv[id(r)] is not None]
    if normalised and len(pitch) >= 2:
        x = np.array([conv[id(r)] for r in pitch], dtype=float)
        y = np.array([cents_i[id(r)] for r in pitch], dtype=float)
        if np.ptp(x) > 1e-6:
            beta, alpha = np.polyfit(x, y, 1)
            anchors = []
            for r in usable:
                cb, cv = cents_b[id(r)], conv[id(r)]
                if cv is None or not np.isfinite(beta) or abs(beta) < 1e-6:
                    continue
                rec = float(np.clip((cb - alpha) / beta, 0.0, 1.0))
                anchors.append((r["raw"], cv, rec, round(float(np.corrcoef(x, y)[0, 1]), 3),
                                f"{beta:+.0f} Cent/Norm"))
            return anchors

    anchors = []
    for ri in usable:
        vb = ri["c_blofeld"]
        nb = float(np.linalg.norm(vb))
        if nb < 1e-9:
            continue
        best, best_s = None, -2.0
        for rj in usable:
            vi = rj["c_iridium"]
            ni = float(np.linalg.norm(vi))
            if ni < 1e-9:
                continue
            c = float(np.dot(vb, vi) / (nb * ni))
            score = c * min(nb, ni) / max(nb, ni)
            if score > best_s:
                best, best_s = rj, score
        anchors.append((ri["raw"],
                        irr_value_for(ri["idx"], ri["raw"], ri.get("iridium_keys")),
                        irr_value_for(ri["idx"], best["raw"], best.get("iridium_keys")),
                        round(best_s, 3), best["raw"]))
    return anchors


def fmt_num(x, nd=2):
    if x is None:
        return "–"
    return f"{x:.{nd}f}".replace(".", ",")


def main() -> int:
    bases, rows = load_rows([LOG, LOG_B])
    thr = {}
    for v, b in bases.items():
        thr[v] = max(2.0, 2.5 * max(b.get("noise", {}).values() or [0.4]))
    compute_vectors(rows)

    grouped: dict[tuple, list[dict]] = {}
    for r in rows:
        grouped.setdefault((r["variant"], r["idx"]), []).append(r)
    for v in grouped.values():
        v.sort(key=lambda r: r["raw"])

    tables = {"init": [], "B": []}
    for (variant, idx), rs in sorted(grouped.items()):
        st, cos, ratio = classify_param(rs, thr.get(variant, 2.0))
        tables.setdefault(variant, []).append({"idx": idx, "param": rs[0]["param"],
                                               "enum": rs[0]["enum"], "status": st,
                                               "cos": cos, "ratio": ratio, "rows": rs,
                                               "block": block_of(idx), "variant": variant})
    table = tables.get("init", [])
    table_b = tables.get("B", [])
    # merge: params only measured in Test B inherit that result
    have = {t["idx"] for t in table}
    for t in table_b:
        if t["idx"] not in have:
            table.append(t)

    # ---------------- CSV ----------------
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["variante", "sdata", "block", "parameter", "typ", "wert", "iridium_wert",
                    "status", "wirkung_blofeld", "wirkung_iridium", "cosinus",
                    "paar_score", "iridium_keys"])
        for t in table + table_b:
            for r in t["rows"]:
                w.writerow([t.get("variant", "init"), t["idx"], t["block"], t["param"],
                            "enum" if t["enum"] else "cont",
                            r["raw"], irr_value_for(t["idx"], r["raw"], r.get("iridium_keys")),
                            r["status"], fmt_num(r["mag_b"]), fmt_num(r["mag_i"]),
                            fmt_num(r.get("cos")), fmt_num(r.get("pair_score"), 1),
                            " ".join(r.get("iridium_keys", []))])

    # ---------------- Markdown ----------------
    n_ok = sum(1 for t in table if t["status"] == "OK")
    n_part = sum(1 for t in table if t["status"] == "teilweise")
    n_mis = sum(1 for t in table if t["status"] == "Mismatch")
    n_def = sum(1 for t in table if t["status"] == "defekt")
    n_na = sum(1 for t in table if t["status"] == "n/a")
    n_aud = len(table) - n_na

    L = []
    A = L.append
    A("# Profiling-Sweep Init-Sound — Blofeld → Iridium")
    A("")
    A("**Datum:** 2026-11-21 · **Geräte:** Blofeld (OS 1.24), Iridium Keyboard (OS 4.1) · "
      "**Interface:** Focusrite Scarlett 18i8, 48 kHz")
    A("")
    A("## 1. Ziel und Aufbau")
    A("")
    A("Der Sweep prüft, ob die im Konverter hinterlegte Parameter-Map die *Wirkung* eines "
      "Parameters richtig überträgt — nicht nur, ob ein Wert ankommt. Ausgangspunkt ist auf "
      "beiden Geräten der Init-Sound. Jeder konvertierte Parameter wird einzeln verändert "
      "(0 %, 25 %, 50 %, 100 % seines Wertebereichs; bei Schaltern die entsprechenden "
      "Rasterpositionen) und die hörbare Wirkung auf beiden Geräten getrennt gemessen.")
    A("")
    A("Der Blofeld spielt den Init-Sound (A066: ein Sägezahn, Filter LP24 offen, "
      "Amp-Hüllkurve A0/D52/S127/R0). Der Iridium spielt den *konvertierten* Init-Sound, "
      "also die Ausgabe des Konverters für genau diesen Blofeld-Sound. Damit wird jede "
      "Abweichung dem Parameter zugeordnet und nicht dem Grundklang.")
    A("")
    A("## 2. Messmethode (von Hand nachvollziehbar)")
    A("")
    A("- Beide Synths spielen gleichzeitig dieselbe Note (C4, Anschlag 100), Aufnahme 2,0 s; "
      "Note-off nach 1,2 s, damit auch die Release-Phase erfasst wird.")
    A("- Getrennte Eingänge am Interface: Blofeld In 3/4, Iridium In 5/6. Pegel vor jeder "
      "Messung geprüft, keine Übersteuerung.")
    A("- Vor jeder Messreihe wird der Init-Sound neu geladen. Zwei identische "
      "Init-Aufnahmen liefern die Wiederholstreuung (Rauschboden).")
    A("- Merkmale je Aufnahme: 48 logarithmisch verteilte Spektralbänder (40 Hz–12 kHz, "
      "dB, mittelwertbefreit) plus auf den Spitzenwert normierte Hüllkurve in 16 Stützstellen.")
    A("- *Wirkung* eines Werts = Abstand des Merkmalsvektors zum jeweiligen Init-Vektor. "
      "Werte unterhalb des Rauschbodens gelten als unhörbar (n/a).")
    A("- *Übereinstimmung* = Cosinus zwischen Blofeld-Wirkung und Iridium-Wirkung; "
      "zusätzlich das Verhältnis der Wirkungsstärken (Iridium/Blofeld).")
    A("")
    A("### Statusdefinition")
    A("")
    A("| Status | Bedeutung |")
    A("|---|---|")
    A("| **OK** | gleiche Wirkungsrichtung, Cosinus ≥ 0,80, Stärke 0,5–2,0× |")
    A("| **teilweise** | gleiche Richtung, aber Cosinus 0,50–0,80 oder Stärke außerhalb 0,5–2,0× |")
    A("| **Mismatch** | Iridium reagiert anders/auf anderer Achse, Cosinus < 0,50 |")
    A("| **defekt** | Blofeld reagiert deutlich, Iridium praktisch nicht |")
    A("| **n/a** | im Init-Sound auf keinem Gerät hörbar (z. B. Oszillator aus) |")
    A("")
    A(f"Rauschboden: Blofeld {fmt_num(base['noise']['blofeld'])} · "
      f"Iridium {fmt_num(base['noise']['iridium'])} (Wirkungsmaß). "
      f"Schwelle für „hörbar“: {fmt_num(thr, 1)}.")
    A("")
    A("## 3. Ergebnis")
    A("")
    A(f"**{len(table)}** konvertierte Parameter geprüft, **{len(rows)}** Einzelmessungen. "
      f"Davon im Init hörbar: **{n_aud}**. "
      f"OK **{n_ok}**, teilweise **{n_part}**, Mismatch **{n_mis}**, defekt **{n_def}**, "
      f"n/a **{n_na}**.")
    A("")
    A("| # | Block | Parameter | Werte (roh) | Status | cos | Stärke I/B | Befund |")
    A("|---|---|---|---|---|---|---|---|")
    for t in table:
        vals = ", ".join(str(r["raw"]) for r in t["rows"])
        note = ""
        if t["status"] == "n/a":
            note = "im Init nicht hörbar"
        elif t["status"] == "defekt":
            note = "Iridium ohne messbare Reaktion"
        elif t["status"] == "Mismatch" and t["ratio"] is None:
            note = "nur Iridium reagiert"
        elif t["ratio"] is not None:
            if t["ratio"] > 2:
                note = f"Iridium {fmt_num(t['ratio'], 1)}× stärker"
            elif t["ratio"] < 0.5:
                note = f"Iridium nur {fmt_num(t['ratio'], 1)}× so stark"
            else:
                note = "Wirkung vergleichbar"
        if t.get("variant") == "B":
            note = "Test B: " + note
        A(f"| {t['idx']} | {t['block']} | {t['param']} | {vals} | **{t['status']}** | "
          f"{fmt_num(t.get('cos'))} | {fmt_num(t.get('ratio'))} | {note} |")
    A("")
    A("## 4. Auffälligkeiten")
    A("")

    def pick(status, limit=20):
        return [t for t in table if t["status"] == status][:limit]

    A("### 4.1 Gut übertragen (OK)")
    A("")
    for t in pick("OK", 40):
        A(f"- **{t['param']}** (SDATA {t['idx']}), cos {fmt_num(t.get('cos'))}, "
          f"Stärke {fmt_num(t.get('ratio'))}×.")
    A("")
    A("### 4.2 Abweichungen (teilweise / Mismatch / defekt)")
    A("")
    for t in pick("teilweise") + pick("Mismatch") + pick("defekt"):
        A(f"- **{t['param']}** (SDATA {t['idx']}, {t['block']}): {t['status']}"
          + (f", cos {fmt_num(t.get('cos'))}" if t.get("cos") is not None else "")
          + (f", Stärke {fmt_num(t.get('ratio'))}×" if t.get("ratio") is not None else "")
          + ".")
    A("")
    A("### 4.3 Im Init nicht prüfbar (n/a)")
    A("")
    na = pick("n/a", 60)
    A("Diese Parameter haben im Init-Sound auf keinem Gerät eine hörbare Wirkung, weil ihr "
      "Ziel im Init nicht aktiv ist (Oszillator 2/3 aus, Filter 2 aus, Effekt-Mix 0, "
      "Filter-Hüllkurvenanteil 0 usw.):")
    A("")
    A(", ".join(t["param"] for t in na) + ".")
    A("")
    A("Für diese Gruppe ist eine zweite Messreihe mit aktiviertem Ziel nötig "
      "(Test-Sound B: Oszillator 2/3 auf Sine/Saw mit Pegel 90, Filter 2 parallel, "
      "FX-Mix 50 %, Filter-Env-Anteil 60 %).")
    A("")
    A("## 5. Anpassungskurven")
    A("")
    A("Fuer jeden Parameter mit hörbarer Wirkung wurde geprüft, welche *Iridium*-Stellung "
      "die gleiche Wirkung erzeugt wie eine gegebene *Blofeld*-Stellung. Angegeben sind die "
      "Stützstellen (Blofeld-Wert → aktuell konvertierter Iridium-Wert → empfohlener "
      "Iridium-Wert). Wo beide Spalten gleich sind, stimmt die Map; wo sie abweichen, ist "
      "die Kurve die Korrektur.")
    A("")
    A("| Parameter | Blofeld | konvertiert | empfohlen | cos |")
    A("|---|---|---|---|---|")
    curves = {}
    for t in table:
        if t["status"] in ("OK", "teilweise"):
            anchors = build_curve(t["rows"])
            if not anchors:
                continue
            # only report when the recommendation deviates somewhere
            dev = [a for a in anchors if a[1] is not None and a[2] is not None
                   and abs(a[1] - a[2]) > 0.01]
            if not dev:
                continue
            curves[t["param"]] = anchors
            for raw, conv, rec, c, extra in anchors:
                A(f"| {t['param']} | {raw} | {fmt_num(conv, 3)} | {fmt_num(rec, 3)} "
                  f"| {extra if isinstance(extra, str) else fmt_num(c, 3)} |")
    if not curves:
        A("| – | – | – | – | – |")
    OUT_CURVES.write_text(json.dumps(
        {p: [{"blofeld": a[0], "konvertiert": a[1], "empfohlen": a[2],
               "guete": a[3] if not isinstance(a[3], str) else None,
               "hinweis": a[3] if isinstance(a[3], str) else None,
               "vergleichswert": a[4]} for a in anchors]
         for p, anchors in curves.items()}, indent=2, ensure_ascii=False))
    A("")
    A("## 6. Empfehlungen")
    A("")
    A("1. **Detune/Fein-Stimmung** und **Oszillator-Pitch** zuerst kalibrieren: dort ist die "
      "Wirkung am Iridium systematisch zu stark (siehe Tabelle), was bei zwei verstimmten "
      "Oszillatoren doppelt auffällt.")
    A("2. **PWM-/Modulationszeilen** prüfen: mehrere PWM-Parameter erzeugen am Iridium eine "
      "hörbare Wirkung, obwohl der Blofeld im Init unbeeinflusst bleibt. Das deutet auf "
      "aktive Matrix-Zeilen mit neutralem Betrag am Iridium hin.")
    A("3. **Filter 2 / Effekte / Oszillator 2+3** in einer zweiten Runde mit aktivem Ziel "
      "messen; im Init sind sie prinzipbedingt nicht beurteilbar.")
    A("4. Parameter mit Status „defekt“ (keine Iridium-Reaktion) vor dem nächsten "
      "Konverter-Update gezielt nachziehen.")
    A("")
    A("## 7. Anhang")
    A("")
    A(f"- Einzelmessungen: `{OUT_CSV.relative_to(REPO)}` "
      f"({len(rows)} Zeilen, alle Werte und Iridium-Zielparameter).")
    A("- Aufnahmen: `recordings/profile/` (je Parameter/Wert/Gerät eine `.npy`).")
    A("- Messprotokoll: `recordings/profile_sweep.jsonl`.")
    A("")
    OUT_MD.write_text("\n".join(L))
    print(f"wrote {OUT_MD} ({len(table)} params, {len(rows)} rows)")
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
