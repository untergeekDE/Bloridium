#!/usr/bin/env python3
"""derive_corrections.py – CC-sweep report -> concrete qpat corrections.

Reads a report from sim_cc_sweep.py (recordings/cc_sweep_*.json) and the
 matching transfer/upload-*.qpat, maps each CC to a qpat parameter
 (name bridge via normalization + aliases) and derives:

   best_cc   = CC value with the best score
   norm*     = best_cc / 127          (guide: 0-based, 0..127 -> 0..1)
   current   = current value from the qpat (normalized)
   correction = norm* - current       (delta for the qpat rebuild)

Usage:
  python3 scripts/derive_corrections.py recordings/cc_sweep_A008_72_<ts>.json \
      --qpat "transfer/upload/A008_Easy_Piano_HS.qpat" [--threshold 0.5] [--md docs/CC-KORREKTUREN.md]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import qpat

REPO = Path(__file__).resolve().parent.parent

# guide name -> qpat name aliases (applied after normalization, see below)
ALIASES = {
    "filter1cutoff": "filter1cutoff",
    "ampattack": "ampenvattack",
    "ampdecay": "ampenvdecay",
    "ampsustain": "ampenvsustain",
    "amprelease": "ampenvrelease",
    "ampveloamount": "ampveloamount",
    "filter1attack": "filter1envattack",
    "filter1decay": "filter1envdecay",
    "filter1sustain": "filter1envsustain",
    "filter1release": "filter1envrelease",
    "filter1amount": "filter1envamount",
    "filter1veloamount": "filter1veloamount",
    "filter2attack": "filter2envattack",
    "filter2decay": "filter2envdecay",
    "filter2sustain": "filter2envsustain",
    "filter2release": "filter2envrelease",
    "filter2amount": "filter2envamount",
    "filter2veloamount": "filter2veloamount",
    "osc1vol": "osc1vol",
    "osc2vol": "osc2vol",
    "osc3vol": "osc3vol",
    "drywet": "drywet",
}


def norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def build_bridge(qpat_params: dict) -> dict[str, str]:
    """Normalized guide name -> qpat parameter name."""
    qn = {norm_name(k): k for k in qpat_params}
    bridge = {}
    for g in list(ALIASES):
        pass
    return qn


def find_qpat_param(guide_name: str, qpat_params: dict, qn: dict) -> str | None:
    n = norm_name(guide_name)
    n = re.sub(r"\[rdbcc0\]", "", n)
    if n in ALIASES:
        n = ALIASES[n]
    if n in qn:
        return qn[n]
    # unique substring match (fallback when there is no exact normalized hit)
    hits = [k for k in qn if n in k or k in n]
    if len(hits) == 1:
        return qn[hits[0]]
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", help="cc_sweep_*.json von sim_cc_sweep.py")
    ap.add_argument("--qpat", required=True, help="transfer/upload/<LOC>_*.qpat")
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="only adopt CCs with delta >= threshold (points)")
    ap.add_argument("--md", default=None, help="Markdown-Output (Default: docs/CC-KORREKTUREN_<loc>.md)")
    args = ap.parse_args(argv)

    report = json.loads(Path(args.report).read_text())
    qp = qpat.load(args.qpat)
    qpat_params = qp["params"]
    qn = {norm_name(k): k for k in qpat_params}

    base = report.get("baseline", {}).get("score")
    loc = report.get("loc", "?")
    print(f"Report {args.report}\nBaseline {loc} note{report.get('note')}: score={base}\n")

    rows = []
    for c in report.get("ccs", []):
        if c.get("delta") is None or c["best"] is None:
            continue
        if c["delta"] < args.threshold:
            continue
        qp_name = find_qpat_param(c["param"], qpat_params, qn)
        current = qpat_params[qp_name]["value"] if qp_name else None
        best_v = c["best"]["value"]
        norm_star = best_v / 127.0
        corr = (norm_star - current) if current is not None else None
        rows.append({
            "cc": c["cc"], "param": c["param"], "qpat_param": qp_name,
            "best_cc": best_v, "best_score": c["best"]["score"], "delta": c["delta"],
            "current": current, "norm_star": round(norm_star, 4),
            "correction": round(corr, 4) if corr is not None else None,
        })
    rows.sort(key=lambda r: r["delta"], reverse=True)

    for r in rows:
        print(f"CC{r['cc']:3d} {r['param']:28s} -> qpat {str(r['qpat_param']):24s} "
              f"best={r['best_cc']:3d} (score {r['best_score']}, delta {r['delta']:+.2f}) "
              f"current={r['current']} norm*={r['norm_star']} corr={r['correction']}")

    md_path = Path(args.md) if args.md else REPO / "docs" / f"CC-KORREKTUREN_{loc}.md"
    lines = [
        f"# CC corrections {loc} (note {report.get('note')}, Bank 6 PC {report.get('irr_pc')})",
        "",
        f"Source: `{args.report}` + qpat `{args.qpat}`; baseline score **{base}**.",
        "norm = CC/127 (guide 0-based); correction = norm* - current(qpat).",
        "",
        "| CC | Guide param | qpat param | best CC | Score | delta vs base | current | norm* | correction |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['cc']} | {r['param']} | {r['qpat_param']} | {r['best_cc']} | {r['best_score']} "
            f"| {r['delta']:+.2f} | {r['current']} | {r['norm_star']} | {r['correction']} |")
    md_path.write_text("\n".join(lines) + "\n")
    print(f"\nMarkdown: {md_path} ({len(rows)} corrections >= {args.threshold})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
