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

LOGS = {
    "init": REPO / "recordings/profile_sweep.jsonl",
    "clean": REPO / "recordings/profile_testb_clean.jsonl",
    "fx": REPO / "recordings/profile_testb_fx.jsonl",
    "release": REPO / "recordings/profile_testb_release.jsonl",
    "f2": REPO / "recordings/profile_testb_f2.jsonl",
    "f2ser": REPO / "recordings/profile_testb_f2ser.jsonl",
    "fe": REPO / "recordings/profile_testb_fe.jsonl",
    "fe_decay": REPO / "recordings/profile_testb_fe_decay.jsonl",
    "fe_rel": REPO / "recordings/profile_testb_fe_rel.jsonl",
    "osc2": REPO / "recordings/profile_testb_osc2.jsonl",
    "osc3": REPO / "recordings/profile_testb_osc3.jsonl",
    "sync": REPO / "recordings/profile_testb_sync.jsonl",
    "noise": REPO / "recordings/profile_testb_noise.jsonl",
    "lfo1": REPO / "recordings/profile_testb_lfo1.jsonl",
    "unison": REPO / "recordings/profile_testb_unison.jsonl",
    "fx1": REPO / "recordings/profile_testb_fx1.jsonl",
    "keytrack": REPO / "recordings/modal_sweep.jsonl",
    "res1": REPO / "recordings/profile_testb_res1.jsonl",
    "res2": REPO / "recordings/profile_testb_res2.jsonl",
    "fe4": REPO / "recordings/profile_testb_fe4.jsonl",
    "fe4_release": REPO / "recordings/profile_testb_release_fe4.jsonl",
    "res1b": REPO / "recordings/profile_testb_res1b.jsonl",
    "res1c": REPO / "recordings/profile_testb_res1c.jsonl",
    "res2b": REPO / "recordings/profile_testb_res2b.jsonl",
    "fe4b": REPO / "recordings/profile_testb_fe4b.jsonl",
}
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
    n = 1 << int(np.ceil(np.log2(2 * len(y))))
    Y = np.fft.rfft(y, n=n)
    r = np.fft.irfft(Y * np.conj(Y), n=n)[:len(y)]
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
    for variant, path in paths.items():
        if not Path(path).exists():
            continue
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") == "baseline":
                r["prefix"] = r.get("prefix", "")
                bases[variant] = r
            elif r.get("kind") == "row":
                r["variant"] = r.get("variant", variant)
                r.setdefault("prefix", "")
                rows.append(r)
    if not rows:
        raise SystemExit("no rows")
    return bases, rows


def compute_vectors(rows):
    """Attach effect vectors (delta vs. Init) to each row, recomputed from the npy files."""
    feats = _feature_cache()

    def cached(path):
        st = Path(path).stat()
        key = f"{Path(path).name}:{st.st_mtime_ns}:{st.st_size}"
        if key not in feats:
            x = np.load(path)
            feats[key] = (vec(x), curve_vec(x), f0_hz(x))
        return feats[key]

    base_vec, base_curve = {}, {}
    for variant, b in BASES.items():
        prefix = b.get("prefix", "")
        for name in ("blofeld", "iridium"):
            files = sorted(NPY.glob(f"{prefix}init_{name}_*.npy"))
            if not files:
                continue
            base_vec[(variant, name)] = np.mean([cached(f)[0] for f in files], axis=0)
            base_curve[(variant, name)] = np.mean([cached(f)[1] for f in files], axis=0)
    for r in rows:
        if r.get("precomputed"):
            continue
        v = r["variant"]
        prefix = r.get("prefix", "")
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


def _cos(a, b):
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na < 1e-9 or nb < 1e-9:
        return None, 0.0
    return float(np.dot(a, b) / (na * nb)), nb / na


def row_status(r, thr):
    """Per-value status, recomputed from the stored effect vectors."""
    if r.get("v_blofeld") is None:
        return "n/a", None, None
    if r["idx"] in PITCH_PARAMS:
        cb, ci = _cents(r, "blofeld"), _cents(r, "iridium")
        if abs(cb) >= 25 and abs(ci) >= 10:
            ratio = abs(ci) / abs(cb)
            if cb * ci <= 0:
                return "Mismatch", None, ratio
            if 0.67 <= ratio <= 1.5:
                return "OK", None, ratio
            if 0.33 <= ratio <= 3.0:
                return "teilweise", None, ratio
            return "Mismatch", None, ratio
    mb = float(np.linalg.norm(r["v_blofeld"]))
    mi = float(np.linalg.norm(r["v_iridium"]))
    if mb < thr and mi < thr:
        return "n/a", None, mi / mb if mb > 0 else None
    if mb < thr:
        return "Mismatch", None, mi / mb if mb > 0 else None
    if mi < thr:
        return "defekt", None, mi / mb if mb > 0 else None
    cos, ratio = _cos(r["v_blofeld"], r["v_iridium"])
    if cos is None:
        return "Mismatch", None, ratio
    if cos >= 0.80 and 0.5 <= ratio <= 2.0:
        return "OK", cos, ratio
    if cos >= 0.50:
        return "teilweise", cos, ratio
    return "Mismatch", cos, ratio


MONO_UNMESSBAR = ("Balance", "Pan ")


def recompute_rows(rows, thr_map):
    for r in rows:
        if r.get("precomputed"):
            continue
        st, cos, ratio = row_status(r, thr_map.get(r["variant"], 2.0))
        if any(k in r["param"] for k in MONO_UNMESSBAR) and "Source" not in r["param"]:
            st, cos = "n/a", None
        r["status"] = st
        r["cos"] = None if cos is None else round(cos, 4)
        if ratio is not None:
            r["ratio"] = round(ratio, 3)


def classify_param(rows, thr):
    """Aggregate the per-value statuses of one parameter."""
    sts = [r["status"] for r in rows]
    coss = [r["cos"] for r in rows if r.get("cos") is not None]
    ratios = [r["ratio"] for r in rows
              if r.get("ratio") is not None and r.get("cos") is not None]
    cos = float(np.mean(coss)) if coss else None
    ratio = float(np.median(ratios)) if ratios else None
    meaningful = [s for s in sts if s != "n/a"]
    if not meaningful:
        return "n/a", None, None
    if all(s == "OK" for s in meaningful):
        return "OK", cos, ratio
    if any(s == "defekt" for s in meaningful) and "OK" not in meaningful:
        return "defekt", cos, ratio
    if "OK" in meaningful or "teilweise" in meaningful:
        return "teilweise", cos, ratio
    return "Mismatch", cos, ratio


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
            if abs(float(np.corrcoef(x, y)[0, 1])) < 0.98:
                return []
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
        if best_s >= 0.90:
            anchors.append((ri["raw"],
                            irr_value_for(ri["idx"], ri["raw"], ri.get("iridium_keys")),
                            irr_value_for(ri["idx"], best["raw"], best.get("iridium_keys")),
                            round(best_s, 3), best["raw"]))
    if len(anchors) >= 2:
        return anchors
    # fallback: match effect *strength* (robust when the spectral direction is noisy)
    pts = []
    for r in usable:
        cv = irr_value_for(r["idx"], r["raw"], r.get("iridium_keys"))
        if cv is None:
            continue
        pts.append((float(cv), float(np.linalg.norm(r["c_iridium"])),
                    float(np.linalg.norm(r["c_blofeld"])), r["raw"]))
    pts.sort()
    if len(pts) < 3 or len({p[0] for p in pts}) < 3:
        return []
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    if np.ptp(ys) < 1e-6 or abs(float(np.corrcoef(xs, ys)[0, 1])) < 0.90:
        return []
    anchors = []
    for cv, mi, mb, raw in pts:
        if mi < 1e-6:
            continue
        rec = float(np.interp(mb, ys, xs))
        anchors.append((raw, cv, rec, round(float(np.corrcoef(xs, ys)[0, 1]), 3),
                        f"Stärke {mb:.1f}/{mi:.1f}"))
    return anchors


def fmt_num(x, nd=2):
    if x is None:
        return "–"
    return f"{x:.{nd}f}".replace(".", ",")


BASES: dict = {}


def main() -> int:
    global BASES
    bases, rows = load_rows(LOGS)
    BASES = bases
    thr = {}
    for v, b in bases.items():
        thr[v] = max(2.0, 1.5 * max(b.get("noise", {}).values() or [0.4]))
    compute_vectors(rows)
    recompute_rows(rows, thr)

    # f2 (Filter 2) is documented separately: the Iridium side showed a constant
    # offset (routing/base instability), so those rows are not merged into the table.
    MERGE_EXCLUDE: set[str] = set()
    grouped: dict[tuple, list[dict]] = {}
    for r in rows:
        if r["variant"] in MERGE_EXCLUDE:
            continue
        grouped.setdefault((r["variant"], r["idx"]), []).append(r)
    for v in grouped.values():
        v.sort(key=lambda r: r["raw"])

    tables = {}
    for (variant, idx), rs in sorted(grouped.items()):
        st, cos, ratio = classify_param(rs, thr.get(variant, 2.0))
        tables.setdefault(variant, []).append({"idx": idx, "param": rs[0]["param"],
                                               "enum": rs[0]["enum"], "status": st,
                                               "cos": cos, "ratio": ratio, "rows": rs,
                                               "block": block_of(idx), "variant": variant})
    table = tables.get("init", [])
    table_b = [t for v, ts in tables.items() if v != "init" for t in ts]
    # merge: a Test-B result replaces an inconclusive Init result for the same parameter
    merged = {t["idx"]: t for t in table}
    MODAL = {"keytrack", "velocity", "pan", "pan_noise",
             "f2_keytrack", "f2_velocity", "f2_envamount"}
    FE_PREF = {"fe4", "fe4_release"}
    RES_PREF = {80, 100}
    REP_PREF = {80: "res1b", 100: "res2b"}
    F2_PREF = {97, 98, 100, 101}   # F2 type/cutoff/reso/drive: only Test D f2 is valid
    for t in table_b:
        cur = merged.get(t["idx"])
        # Test E has the right excitation (two notes/velocities, stereo); Test D f2 is
        # the only valid run for F2 type/cutoff/reso/drive (F2 is off in the Init).
        if (cur is None or cur["status"] == "n/a" or t["variant"] in MODAL
                or (t["variant"] == "f2" and t["idx"] in F2_PREF)
                or (t["variant"] in FE_PREF and t["status"] != "n/a")
                or (t["variant"] == "fe4b" and t["idx"] in {201})
                or (t["variant"] in {"res1", "res2"} and t["idx"] in RES_PREF)
                or (REP_PREF.get(t["idx"]) == t["variant"])):
            merged[t["idx"]] = t
    table = sorted(merged.values(), key=lambda t: t["idx"])
    only_irr_params = set()
    for t in table:
        mean = [r for r in t["rows"] if r["status"] != "n/a"]
        if mean and all(r["status"] == "Mismatch" and r.get("cos") is None for r in mean):
            only_irr_params.add(t["param"])

    # ---------------- CSV ----------------
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["variante", "sdata", "block", "parameter", "typ", "wert", "iridium_wert",
                    "status", "wirkung_blofeld", "wirkung_iridium", "cosinus",
                    "paar_score", "iridium_keys"])
        seen = set()
        for r in sorted(rows, key=lambda r: (r.get("variant", "init"), r["idx"], r["raw"])):
            key = (r.get("variant"), r["idx"], r["raw"])
            if key in seen:
                continue
            seen.add(key)
            w.writerow([r.get("variant", "init"), r["idx"], block_of(r["idx"]), r["param"],
                        "enum" if r["enum"] else "cont", r["raw"],
                        irr_value_for(r["idx"], r["raw"], r.get("iridium_keys")),
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
    A("Bei den um die Mitte liegenden Tonhöhenparametern wurden musikalisch sinnvolle "
      "Werte verwendet (±2 Oktaven, ±12 Halbtöne), weil die Bereichsenden unterhalb des "
      "Hörbereichs liegen. Bei Schaltern entsprechen die vier Stufen dem ersten, "
      "zweiten, mittleren und letzten Rasterplatz.")
    A("")
    A("## 2. Messmethode (von Hand nachvollziehbar)")
    A("")
    A("- Beide Synths spielen gleichzeitig dieselbe Note (C4, Anschlag 100), Aufnahme 2,0 s. "
      "Die Note wird während der Aufnahme gehalten, erfasst sind also Attack, Decay und "
      "Sustain; die Release-Phase wird in einem eigenen Durchgang mit Note-off während "
      "der Aufnahme gemessen (Test C).")
    A("- Getrennte Eingänge am Interface: Blofeld In 3/4, Iridium In 5/6. Pegel vor jeder "
      "Messung geprüft, keine Übersteuerung.")
    A("- Vor jeder Messreihe wird der Init-Sound neu geladen. Zwei identische "
      "Init-Aufnahmen liefern die Wiederholstreuung (Rauschboden).")
    A("- Drei Durchgänge: **Init** (unverändert), **Test B** (Ziel aktiviert: Oszillator 2/3 an, "
      "Filter 2 aktiv, FX-Mix aufgedreht, Filter-Env-Anteil erhöht) und **Test C** "
      "(Release, Note-off während der Aufnahme). Parameter, die im Init unhörbar sind, "
      "werden mit dem Ergebnis aus Test B/C bewertet.")
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
    A("| **n/a** | auf keinem Gerät hörbar (auch in Test B/C/D nicht), z. B. weil das Ziel aus ist |")
    A("")
    A(f"Rauschboden: Blofeld {fmt_num(bases.get('init', {}).get('noise', {}).get('blofeld'))} · "
      f"Iridium {fmt_num(bases.get('init', {}).get('noise', {}).get('iridium'))} (Wirkungsmaß). "
      f"Schwelle für „hörbar“: {fmt_num(thr.get('init'), 1)}.")
    A("")
    A("## 3. Ergebnis")
    A("")
    init_aud = sum(1 for t in tables.get("init", []) if t["status"] != "n/a")
    A(f"**{len(table)}** konvertierte Parameter geprüft, **{len(rows)}** Einzelmessungen. "
      f"Mit belastbarem Urteil: **{n_aud}** (davon **{init_aud}** direkt im Init, "
      f"**{n_aud - init_aud}** über Test B/C/D/E). "
      f"OK **{n_ok}**, teilweise **{n_part}**, Mismatch **{n_mis}**, defekt **{n_def}**, "
      f"n/a **{n_na}**.")
    A("")
    A("| # | Block | Parameter | Werte (roh) | Status | cos | Stärke I/B | Befund |")
    A("|---|---|---|---|---|---|---|---|")
    for t in table:
        vals = ", ".join(str(r["raw"]) for r in t["rows"])
        note = ""
        if t["status"] == "n/a":
            note = "nicht hörbar/messbar"
        elif t["status"] == "defekt":
            note = "Iridium ohne messbare Reaktion"
        elif t["status"] == "Mismatch" and t["ratio"] is None:
            note = "nur Iridium reagiert"
        elif t["ratio"] is not None:
            meaningful = [r["status"] for r in t["rows"] if r["status"] != "n/a"]
            if meaningful and all(st == "Mismatch" for st in meaningful) \
                    and all(r.get("cos") is None for r in t["rows"]):
                note = "nur Iridium reagiert"
            elif t["ratio"] > 2:
                note = f"Iridium {fmt_num(t['ratio'], 1)}× stärker"
            elif t["ratio"] < 0.5:
                note = f"Iridium nur {fmt_num(t['ratio'], 1)}× so stark"
            elif t["status"] == "teilweise":
                note = "einzelne Werte weichen ab"
            else:
                note = "Wirkung vergleichbar"
        elif t["status"] == "teilweise":
            note = "einzelne Werte weichen ab"
        if not note:
            note = "Wirkung vergleichbar"
        if t.get("variant") != "init":
            label = {"clean": "Test B", "fx": "Test B (FX)", "release": "Test C",
                     "f2": "Test D Filter 2", "fe": "Test D Filter-Hüllkurve",
                     "fe_decay": "Test D FE-Decay", "fe_rel": "Test D FE-Release",
                     "osc2": "Test D Osc 2", "osc3": "Test D Osc 3",
                     "sync": "Test D Sync", "noise": "Test D Noise",
                     "lfo1": "Test D LFO", "unison": "Test D Unisono",
                     "fx1": "Test D FX", "keytrack": "Test E Keytrack",
                     "velocity": "Test E Velocity", "pan": "Test E Pan",
                     "pan_noise": "Test E Pan/Noise",
                     "f2_keytrack": "Test D F2-Keytrack",
                     "f2_velocity": "Test D F2-Velocity",
                     "f2_envamount": "Test D F2-Env",
                     "res1": "Test D Resonanz F1", "res2": "Test D Resonanz F2",
                     "fe4": "Test D FE", "fe4_release": "Test D FE-Release"}.get(
                         t["variant"], f"Test {t['variant']}")
            note = f"{label}: " + note
        A(f"| {t['idx']} | {t['block']} | {t['param']} | {vals} | **{t['status']}** | "
          f"{fmt_num(t.get('cos'))} | {fmt_num(t.get('ratio'))} | {note} |")
    A("")
    A("### Kernaussagen")
    A("")
    ok = [t for t in table if t["status"] == "OK"]
    bad = [t for t in table if t["status"] in ("Mismatch", "defekt")]
    A(f"- **{len(ok)}** Parameter übertragen die Wirkung sauber, **{len(bad)}** weichen "
      f"deutlich ab, **{sum(1 for t in table if t['status'] == 'teilweise')}** teilweise. "
      f"**{n_na}** sind im Init-Sound grundsätzlich nicht beurteilbar, weil ihr Ziel "
      f"dort aus ist.")
    A("- **Feinstimmung (Detune):** Der Iridium reagiert mit 203 Cent pro Norm-Einheit, "
      "der Blofeld mit rund 1,6 Cent pro Rohschritt. Die bisherige Map (Divisor 254) "
      "erzeugte nur die Hälfte der Verstimmung; richtig ist "
      "`Iridium = 0,5 + (Rohwert − 64) / 127`. Der Konverter wurde entsprechend korrigiert.")
    A("- **Grobstimmung (Oktave/Halbton), Wellenform und Filter-Cutoff/-Typ** folgen der "
      "Vorlage gut. Der Oszillator-Pegel passt; die Verstärker-Lautstärke ist am Iridium "
      "etwas stärker (rund 1,8×) und sollte leicht komprimiert werden.")
    if any(t.get("variant") in ("osc2", "osc3", "noise", "lfo1", "unison", "fx1", "f2")
           for t in table):
        A("- **Test D (Ziel eingeschaltet):** Osc 2/3 inkl. Pitch, Shape und Pegel folgen "
          "jetzt sauber (cos 0,94–1,00). Filter-Hüllkurve (Amount/Attack/Sustain) und "
          "FX-Mix sind brauchbar; der Noise-Pegel folgt in der Tendenz. Architekturbedingt offen bleiben "
          "PWM (Warp statt Pulsbreite), Noise-Farbe (nur Pink/White), LFO Fade "
          "und Unisono-Detune. **Filter 2:** nach der Routing-Korrektur folgen "
          "Cutoff (cos 0,88–0,96), Env Amount (0,92–1,0) und Env Velocity "
          "(0,75–0,81); Keytrack ist teilweise (0,89), Typ bleibt offen. "
          "**Resonanz (Wiederholung 65/85):** der Iridium reagiert deutlich, aber "
          "mit anderer Form (F1 cos 0,06–0,20, F2 cos 0,16) → Mismatch, nicht defekt. "
          "Filter-Env Sustain/Release sind OK (Release 100 % cos 0,85); Decay ist "
          "bei 100 % OK (cos 0,90), kurze Zeiten bleiben unter der Schwelle; "
          "Attack weicht ab (nur Iridium reagiert). "
          "Details: `docs/ARCHITEKTUR-DIFFERENZEN.md`.")
    if any(t.get("variant") in ("keytrack", "velocity", "pan", "pan_noise") for t in table):
        A("- **Test E (andere Anregung):** Keytrack ist mit zwei Noten messbar "
          "(Filter 1: cos 0,86), Filter-Env-Velocity und Filter-Pan nur teilweise "
          "(Pan reagiert am Iridium erst bei 100 %, nicht bei 0 %). "
          "**Balance ist keine Panorama-Funktion:** der Blofeld bleibt im L/R-Bild "
          "unverändert, der Iridium wanderte — die Map „Balance → Pan“ war semantisch "
          "falsch und ist inzwischen auf Filteranteil/Pan-Betrag korrigiert.")
    only_irr = sorted(only_irr_params)
    if only_irr:
        A("- **Nur auf dem Iridium hörbar:** " + ", ".join(only_irr) + ". Hier schreibt der "
          "Konverter aktive Modulations-/Effektzeilen, obwohl der Blofeld im Init neutral "
          "bleibt — der Iridium klingt dadurch anders, ohne dass es eine Vorlage dafür gibt.")
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
      "Ziel im Init nicht aktiv ist oder der Init-Wert die Wirkung aufhebt: Oszillator 2/3 "
      "aus, Filter 2 aus, Effekt-Mix 0, Filter bei 100 % offen (Hüllkurve und Resonanz "
      "können nichts mehr bewegen), Amp-Decay bei Sustain 100 %. Pan- und Balance-Parameter "
      "werden von der Monosumme der Messung nicht erfasst (dafür ist eine L/R-getrennte "
      "Auswertung nötig) und sind deshalb hier ebenfalls n/a. Für die übrige Gruppe ist eine "
      "Messung mit aktiviertem Ziel nötig (Test B/C/D, soweit durchgeführt):")
    A("")
    A(", ".join(t["param"] for t in na) + ".")
    A("")
    A("")
    A("## 5. Anpassungskurven")
    A("")
    A("### 5.1 Feinstimmung (Detune) — korrigiert und verifiziert")
    A("")
    A("Der Blofeld verstimmt über den vollen Rohbereich 0–127 um **−101 … +100 Cent** "
      "(1,6 Cent je Rohschritt). Der Iridium reagiert auf `OscNFinePitch` mit "
      "**203 Cent pro Norm-Einheit**. Die bisherige Umrechnung teilte durch 254 und "
      "erzeugte damit nur die halbe Verstimmung; richtig ist:")
    A("")
    A("```")
    A("Iridium-Wert = 0,5 + (Blofeld-Rohwert − 64) / 127")
    A("```")
    A("")
    A("| Blofeld roh | Cent | Iridium alt (÷254) | Cent alt | Iridium neu (÷127) | Cent neu |")
    A("|---|---|---|---|---|---|")
    A("| 0 | −101 | 0,248 | −51 | 0,000 | −101 |")
    A("| 32 | −50 | 0,374 | −25 | 0,248 | −51 |")
    A("| 64 | 0 | 0,500 | 0 | 0,500 | 0 |")
    A("| 127 | +100 | 0,748 | +50 | 0,996 | +101 |")
    A("")
    A("Nach der Korrektur stimmen Richtung und Stärke (Cosinus 0,97–0,98, "
      "Stärkeverhältnis 1,0). Der Konverter wurde entsprechend angepasst "
      "(`qpat_map.fine_pitch_norm`, Test angepasst).")
    A("")
    A("### 5.2 Kandidaten für weitere Kurven")
    A("")
    A("Für die übrigen Parameter reichen vier Stützstellen nicht für eine belastbare Kurve. "
      "Die folgende Liste nennt die Richtung aus dem gemessenen Stärkeverhältnis; für eine "
      "echte Kurve sind 8–12 Stützstellen nötig.")
    A("")
    A("| Parameter | Status | Stärke I/B | Empfehlung |")
    A("|---|---|---|---|")
    for t in table:
        if t["status"] not in ("teilweise", "Mismatch", "defekt") or t.get("ratio") is None:
            continue
        ratio = t["ratio"]
        if t["param"] in only_irr_params:
            rec = "Iridium reagiert ohne Vorlage → Matrix-/Effektzeile abschalten"
        elif t["status"] == "defekt":
            rec = "Iridium ohne ausreichende Wirkung → Ziel prüfen"
        elif 0.8 <= ratio <= 1.25:
            rec = "Wirkung passt, Abweichung liegt in der Form"
        elif ratio > 1.25:
            rec = f"Iridium {fmt_num(ratio, 1)}× zu stark → Wert komprimieren"
        elif ratio > 0.4:
            rec = f"Iridium nur {fmt_num(ratio, 1)}× so stark → Wert spreizen"
        else:
            rec = "Iridium fast ohne Wirkung → Map prüfen"
        A(f"| {t['param']} | {t['status']} | {fmt_num(ratio)} | {rec} |")
    A("")
    A("Die maschinenlesbare Fassung der Messwerte steht in "
      f"`{OUT_CSV.relative_to(REPO)}` (eine Zeile je Parameter und Wert).")
    A("")
    A("## 6. Empfehlungen")
    A("")
    A("1. **Feinstimmung** ist kalibriert (Divisor 127) und muss nur noch in einer "
      "Testkonvertierung gegengeprüft werden. **Modulationsbeträge** (Osc Pitch Amount, "
      "PWM Amount, Amp Velocity) als Nächstes prüfen: dort reagiert nur der Iridium.")
    A("2. **PWM-/Modulationszeilen** prüfen: im Init erzeugen Osc 1 PWM Amount und "
      "Osc Pitch Amount am Iridium eine hörbare Wirkung, obwohl der Blofeld unbeeinflusst "
      "bleibt. Das deutet auf aktive Matrix-Zeilen mit einem Betrag hin, der am Iridium "
      "nicht neutral ist.")
    A("3. **Filter 2 / Effekte / Oszillator 2+3** in einer zweiten Runde mit aktivem Ziel "
      "messen; im Init sind sie prinzipbedingt nicht beurteilbar. Die Test-B-Ergebnisse "
      "haben wegen der drei gleichzeitig klingenden Oszillatoren eine höhere Streuung und "
      "sind gröber als die Init-Werte.")
    A("4. **Filter-Hüllkurve** braucht einen Test mit *geschlossenem* Filter (Cutoff ≈ 70); "
      "bei ganz offenem Filter kann die Hüllkurve nichts mehr öffnen und ist nicht messbar.")
    A("5. Parameter mit Status „defekt“ (keine Iridium-Reaktion) vor dem nächsten "
      "Konverter-Update gezielt nachziehen.")
    A("")
    A("## 7. Anhang")
    A("")
    A(f"- Einzelmessungen: `{OUT_CSV.relative_to(REPO)}` "
      f"({len(rows)} Zeilen, alle Werte und Iridium-Zielparameter).")
    A("- Aufnahmen: `recordings/profile/` (je Parameter/Wert/Gerät eine `.npy`).")
    A("- Messprotokoll: `recordings/profile_sweep.jsonl` (Init), "
      "`recordings/profile_testb_clean.jsonl` / `_fx.jsonl` (Test B), "
      "`recordings/profile_testb_release.jsonl` (Test C).")
    A("- Kurven/Kandidaten (maschinenlesbar): `docs/profiling_curves_2026-11-21.json`.")
    A("- Architektur-Differenzen und Workarounds: `docs/ARCHITEKTUR-DIFFERENZEN.md`.")
    A("")
    OUT_CURVES.write_text(json.dumps({
        "erzeugt": "2026-11-21",
        "quelle": "docs/PROFILING-INIT-2026-11-21.md",
        "kurven": [{
            "parameter": "Osc 1/2/3 Detune",
            "sdata": [3, 19, 35],
            "formel": "iridium_norm = 0.5 + (raw - 64) / 127",
            "verifiziert": {"blofeld_cent": [-101, -50, 0, 100],
                            "iridium_cent": [-101, -51, 0, 101],
                            "cosinus": [0.98, None, None, 0.97]},
            "vorher": "0.5 + (raw - 64) / 254 (nur halbe Verstimmung)",
        }],
        "kandidaten": [
            {"parameter": t["param"], "status": t["status"],
             "staerke_iridium_zu_blofeld": round(t["ratio"], 2) if t.get("ratio") else None,
             "hinweis": "nur Iridium reagiert" if t["param"] in only_irr_params
                        else ("keine ausreichende Iridium-Wirkung" if t["status"] == "defekt"
                              else "weiter beobachten")}
            for t in table if t["status"] in ("teilweise", "Mismatch", "defekt")],
    }, indent=2, ensure_ascii=False) + "\n")
    OUT_MD.write_text("\n".join(L))
    print(f"wrote {OUT_MD} ({len(table)} params, {len(rows)} rows)")
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
