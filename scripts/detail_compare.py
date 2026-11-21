#!/usr/bin/env python3
"""detail_compare.py – Detail-Ansicht einzelner Blofeld-Sounds (A/B-Vergleich v2).

Pro Loc (Default A001-A005) werden vier Quellen zusammengeführt:

  1. Blofeld-Dump  (dumps/blofeld_sndd_<LOC>_*.bin)   – Original-Parameter
  2. Konvertiertes qpat (transfer/rf100_v2/<LOC>_*.qpat) – was das Mapping daraus macht
     (mapped/unmapped aus qpat_map.blofeld_to_qpat_params)
  3. Gemessene v2-Scores (recordings/sim_log_v2_rf.jsonl, mode=rf-dataset, score_version=2)
     – pro Note score + spec_mad_db + env_dtw + embed + schlechteste Frequenzbaender
  4. RF-Prognose (models/prognose_rf.pkl) – was das Modell aus dem Dump allein vorhersagt

Aufruf:
  python3 scripts/detail_compare.py                          # A001-A005
  python3 scripts/detail_compare.py --locs A005,A043,A091
  python3 scripts/detail_compare.py --locs A001 --no-rf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent

from bloridium import blofeld_dump, prognose, qpat, qpat_map  # noqa: E402

# Blofeld-Parameter, die den Score am staerksten treiben (siehe RF feature importances)
KEY_PARAMS = [
    "Category",
    "Osc 1 Shape", "Osc 1 Level", "Osc 1 Octave", "Osc 1 Semitone", "Osc 1 Detune",
    "Osc 2 Shape", "Osc 2 Level", "Osc 2 Octave", "Osc 2 Semitone",
    "Osc 3 Shape", "Osc 3 Level",
    "Mixer Osc 1 Level", "Mixer Osc 2 Level", "Mixer Osc 3 Level", "Mixer Noise Level",
    "Filter 1 Type", "Filter 1 Cutoff", "Filter 1 Resonance", "Filter 1 Env Amount",
    "Filter 2 Type", "Filter 2 Cutoff",
    "Filter Envelope Attack", "Filter Envelope Decay", "Filter Envelope Sustain",
    "Filter Envelope Release",
    "Amplifier Envelope Attack", "Amplifier Envelope Decay", "Amplifier Envelope Sustain",
    "Amplifier Envelope Release", "Amplifier Velocity",
    "LFO 1 Shape", "LFO 1 Rate", "LFO 1 Sync", "LFO 2 Shape", "LFO 2 Rate",
    "Effect 1 Type", "Effect 2 Type",
    "Arpeggiator Mode",
]


def find_dump(loc: str) -> Path:
    cands = sorted(REPO.glob(f"dumps/blofeld_sndd_{loc}_*.bin"))
    if not cands:
        raise SystemExit(f"kein Dump für {loc} in dumps/")
    return cands[-1]


def find_qpat(loc: str, qpat_dir: Path) -> Path:
    cands = sorted(qpat_dir.glob(f"{loc}_*.qpat"))
    if not cands:
        raise SystemExit(f"kein konvertiertes qpat für {loc} in {qpat_dir}/")
    return cands[-1]


def measured_rows(log: Path, loc: str) -> list[dict]:
    rows = []
    if not log.exists():
        return rows
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("meta", {}).get("blofeld") == loc and \
                r.get("result", {}).get("score_version") == 2:
            rows.append(r)
    rows = sorted(rows, key=lambda r: r["meta"].get("note", 0))
    # Duplikate pro Note (llmsubset-Lauf hat 24 Locs erneut gemessen) ignorieren
    seen, out = set(), []
    for r in rows:
        note = r["meta"].get("note")
        if note not in seen:
            seen.add(note)
            out.append(r)
    return out


def rf_prediction(parsed: dict, model_path: Path) -> str:
    if not model_path.exists():
        return "(kein Modell)"
    bundle = prognose.load_model(model_path)
    x = prognose.feature_vector(parsed).reshape(1, -1)
    rf = bundle["model"]
    tree = np.array([float(t.predict(x)[0]) for t in rf.estimators_])
    return f"{float(rf.predict(x)[0]):.1f} ± {tree.std():.1f} (target={bundle.get('target')})"


def worst_bands(res: dict, k: int = 5) -> str:
    bd = res.get("band_delta_db") or []
    edges = res.get("band_edges_hz") or []
    if not bd or not edges:
        return "–"
    idx = sorted(range(len(bd)), key=lambda i: bd[i])[:k]
    return ", ".join(f"{edges[i]:.0f}-{edges[i + 1]:.0f}Hz: {bd[i]:+.1f}dB" for i in idx if i + 1 < len(edges))


def report_loc(loc: str, args) -> None:
    dump = find_dump(loc)
    parsed = blofeld_dump.parse_sndd(dump.read_bytes())
    p = parsed["params"]
    overrides, unmapped = qpat_map.blofeld_to_qpat_params(parsed)

    qp = find_qpat(loc, args.qpat_dir)
    qparsed = qpat.parse_qpat(qp.read_bytes())

    print("=" * 78)
    print(f"{loc}  „{parsed['name']}“  (Category: {p.get('Category', '?')})")
    print(f"  dump : {dump.name}   chk_ok={parsed['chk_ok']}")
    print(f"  qpat : {qp.name}   -> Iridium-Name „{qparsed.get('name', '')}“  "
          f"mapped={len(overrides)} unmapped={len(unmapped)}")

    print("  -- Blofeld-Schluesselparameter:")
    for k in KEY_PARAMS:
        if k in p and p[k] not in (0, "off", "Bypass", None):
            print(f"       {k:<32} {p[k]}")
    nz_mod = [f"Modulation {m}: {p.get(f'Modulation {m} Source')} -> "
              f"{p.get(f'Modulation {m} Destination')} ({p.get(f'Modulation {m} Amount')})"
              for m in range(1, 17)
              if p.get(f"Modulation {m} Source") not in (None, "off")
              and p.get(f"Modulation {m} Amount") not in (None, 0)]
    for line in nz_mod[:8]:
        print(f"       {line}")

    if unmapped:
        print(f"  -- unmapped ({len(unmapped)}): {', '.join(unmapped[:20])}"
              + (" ..." if len(unmapped) > 20 else ""))

    print("  -- gemessen (v2, live 2026-11-20, notes 72/60):")
    for r in measured_rows(args.log, loc):
        res = r["result"]
        sc = res.get("score")
        print(f"       note {r['meta'].get('note'):>2}: score={sc}  "
              f"spec_mad_db={res.get('spec_mad_db'):.2f}  env_dtw={res.get('env_dtw'):.3f}  "
              f"embed={res.get('embed_score')}  verdict={res.get('verdict')}")
        print(f"             schlechteste Baender: {worst_bands(res)}")

    if not args.no_rf:
        print(f"  -- RF-Prognose (aus Dump allein): {rf_prediction(parsed, args.model)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locs", default="A001,A002,A003,A004,A005",
                    help="kommagetrennte Blofeld-Locations (Default A001-A005)")
    ap.add_argument("--qpat-dir", type=Path, default=REPO / "transfer" / "rf100_v2")
    ap.add_argument("--log", type=Path, default=REPO / "recordings" / "sim_log_v2_rf.jsonl")
    ap.add_argument("--model", type=Path, default=REPO / "models" / "prognose_rf.pkl")
    ap.add_argument("--no-rf", action="store_true")
    args = ap.parse_args()
    for loc in [x.strip() for x in args.locs.split(",") if x.strip()]:
        report_loc(loc, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
