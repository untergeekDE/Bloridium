#!/usr/bin/env python3
"""Explain one converted sound: what is worth checking first?

Deterministic part (no model needed):
  * active Blofeld parameters that the converter could not map (or only
    approximates), ranked by a static impact weight
  * the latest A/B measurement's worst frequency bands, translated into
    sections (oscillator / filter / FX / envelope)

Optional model part: predicted score +- uncertainty, clearly marked as a guess
(the shipped model is weak, R2 ~ 0.06).

Usage:
    python3 scripts/explain_sound.py A020
    python3 scripts/explain_sound.py A020 --log recordings/sim_log_v4.jsonl
    python3 scripts/explain_sound.py A020 --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bloridium import blofeld_dump as bd, prognose, qpat_map, workflow  # noqa: E402
from bloridium.version import __version__  # noqa: E402

# Static impact weights (0-100). Only a starting point for the ranking; it is
# deliberately coarse and independent of the RF model.
WEIGHT = {
    "fx": 90, "mod": 75, "filter": 80, "osc_pitch": 80, "wavetable": 70,
    "fm": 70, "env": 60, "arp": 55, "pwm": 50, "noise": 45, "unison": 40,
    "brilliance": 40, "glide": 30, "balance": 30, "bend": 15, "keytrack": 10,
    "limit_wt": 10,
}
DEFAULT_LOG_CANDIDATES = ("sim_log_v4.jsonl", "sim_log_v3.jsonl", "sim_log_v2_rf.jsonl")


def find_dump(loc: str) -> Path:
    bank = REPO / "dumps" / "banks" / loc[0] / f"{loc}.bin"
    if bank.exists():
        return bank
    best = None
    for p in sorted((REPO / "dumps").glob(f"*{loc}*.bin")):
        if best is None or p.name > best.name:
            best = p
    if best is None:
        raise SystemExit(f"no Blofeld dump for {loc}")
    return best


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def unmapped_items(parsed: dict) -> tuple[list[dict], list[str]]:
    """Rank the converter's unmapped entries; returns (items, ignored_notes)."""
    params = parsed["params"]
    _ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    arp_on = params.get("Arpeggiator Mode", 0) != 0
    items, ignored = [], []

    def add(cat: str, title: str, detail: str, weight: int | None = None):
        items.append({"category": cat, "title": title, "detail": detail,
                      "weight": WEIGHT[cat] if weight is None else weight})

    for name in unmapped:
        if name.startswith("Ignored: "):
            ignored.append(name[len("Ignored: "):])
            continue
        if name.startswith("Arp Pattern") or name.startswith("Arpeggiator"):
            if arp_on:
                add("arp", "Arpeggiator", "not converted (no Iridium arp equivalent)")
                # collapse: only one entry per sound
                items[-1]["_key"] = "arp"
            continue
        m = re.match(r"Modulation (\d+) \((.*)\)$", name)
        if m:
            add("mod", f"Modulation {m.group(1)}: {m.group(2)}",
                "matrix row not converted (destination/source has no exact match)")
            continue
        m = re.match(r"Effect (\d) '([^']+)' \(mix ([\d.]+)\)", name)
        if m:
            mix = float(m.group(3))
            if mix > 0:
                add("fx", f"Effect {m.group(1)}: {m.group(2)}",
                    f"replaced by a filter-drive simulation (Blofeld mix {mix:g})")
            continue
        m = re.match(r"(Osc|Filter) (\d) FM Source '([^']+)'", name)
        if m:
            amt = params.get(f"{m.group(1)} {m.group(2)} FM Amount", 0)
            if amt:
                add("fm", f"{m.group(1)} {m.group(2)} FM -> {m.group(3)}",
                    f"FM not converted (amount {amt:g})")
            continue
        m = re.match(r"Osc (\d) Brilliance$", name)
        if m:
            val = params.get(name, 0)
            if val:
                add("brilliance", f"Osc {m.group(1)} Brilliance",
                    f"wavetable brilliance not mapped ({val:g})")
            continue
        m = re.match(r"Osc (\d) Bend Range$", name)
        if m:
            val = params.get(name, 64)
            if val != 64:
                add("bend", f"Osc {m.group(1)} Bend Range",
                    f"custom bend range ({val:g}) not mapped", 15)
            continue
        m = re.match(r"Osc (\d) Keytrack$", name)
        if m:
            val = params.get(name, 96)
            if val not in (96, 0):
                add("keytrack", f"Osc {m.group(1)} Keytrack",
                    f"keytracking ({val:g}) not mapped", 10)
            continue
        m = re.match(r"Osc (\d) Limit WT$", name)
        if m:
            val = params.get(name, 0)
            if val:
                add("limit_wt", f"Osc {m.group(1)} Limit WT", f"({val:g}) not mapped", 10)
            continue
        m = re.match(r"LFO (\d) Keytrack$", name)
        if m:
            val = params.get(name, 64)
            if val != 64:
                add("keytrack", f"LFO {m.group(1)} Keytrack",
                    f"({val:g}) not mapped", 10)
            continue
        # fallback: keep it visible but low
        add("keytrack", name, "not mapped", 10)

    # de-duplicate collapsed entries while keeping the highest weight
    seen, uniq = set(), []
    for it in sorted(items, key=lambda x: -x["weight"]):
        key = it.pop("_key", None) or it["title"]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    return uniq, ignored


def approximations(parsed: dict) -> list[dict]:
    """Mapped, but known to be an approximation - only if actually active."""
    p, sd = parsed["params"], parsed["sdata"]
    out = []

    def add(cat, title, detail):
        out.append({"category": cat, "title": title, "detail": detail,
                    "weight": WEIGHT[cat]})

    route, f2_type, f2_cut = sd[117], sd[97], sd[98]
    if route == 1 and f2_type != 0:
        former = {"HP 12dB": "Nave HP12", "HP 24dB": "Nave HP12",
                  "LP 24dB": "Nave LP24", "LP 12dB": "Nave LP12",
                  "PPG LP": "PPG LP24"}.get(bd.FILTER_TYPES[f2_type], "model")
        add("filter", f"Filter 2 serial -> DigiFormer ({bd.FILTER_TYPES[f2_type]})",
            f"approximated as {former}, cutoff raw {f2_cut} (A12: amount curve not exact)")
    for f in (1, 2):
        reso = sd[(77 if f == 1 else 97) + 3]
        if reso:
            add("filter", f"Filter {f} resonance",
                f"curve raw/113 (raw {reso}) - shape differs from the Blofeld")
        drive = sd[(77 if f == 1 else 97) + 4]
        if drive:
            add("filter", f"Filter {f} drive", f"insert drive, raw {drive} (curve approximated)")
    if any(sd[62 + 2 * i] != 64 for i in range(3)) or sd[68] != 64:
        add("balance", "Oscillator/Noise balance (F1/F2 split)",
            "mapped to destination shares, not a stereo pan")
    alloc = sd[58]
    if (alloc >> 4) & 7:
        add("unison", "Unisono", f"{((alloc >> 4) & 7) + 1} voices; pan/delay neutral")
    if sd[53] or sd[56]:
        add("glide", "Glide", f"rate raw {sd[53]}, mode {sd[56]} (rate curve approximated)")
    for n in (1, 2, 3):
        shape = sd[(n - 1) * 16 + 8]
        if shape >= 16:  # Blofeld wavetable indices
            add("wavetable", f"Osc {n} wavetable",
                f"'{bd.SHAPES[shape] if shape < len(bd.SHAPES) else shape}' -> nearest Iridium table")
        pwm_src = sd[(n - 1) * 16 + 10]
        pwm_amt = sd[(n - 1) * 16 + 11]
        if shape == 1 and pwm_src != 0 and pwm_amt != 64:
            add("pwm", f"Osc {n} PWM", f"via WF Warp, amount {pwm_amt} (weaker than the Blofeld)")
    if sd[67]:
        add("noise", "Noise", f"level {sd[67]} -> mapped onto a free oscillator")
    for lfo in (1, 2, 3):
        base = [160, 172, 184][lfo - 1]
        if not sd[base + 3] and sd[base + 4]:  # free-running speed
            add("mod", f"LFO {lfo} free speed",
                "free-speed Hz curve is not calibrated (raw -> norm approximated)")
    return out


def spectral_notes(rows: list[dict]) -> list[str]:
    notes = []
    for row in rows:
        r = row["result"]
        note = row["meta"].get("note")
        if r.get("score") is None:
            notes.append(f"note {note}: no score ({r.get('error', 'error')})")
            continue
        edges, delta = r.get("band_edges_hz") or [], r.get("band_delta_db") or []
        if not edges or len(delta) < len(edges) - 1:
            continue
        pairs = [(edges[i], edges[i + 1], delta[i]) for i in range(len(delta))]
        quiet = sorted(pairs, key=lambda x: x[2])[:3]
        loud = sorted(pairs, key=lambda x: -x[2])[:3]
        notes.append(f"note {note}: score {r['score']:.1f}, "
                     f"spec_mad {r.get('spec_mad_db', 0):.1f} dB, "
                     f"env_dtw {r.get('env_dtw', 0):.2f}")
        for lo, hi, d in quiet:
            if d < -8:
                notes.append(f"   {lo:.0f}-{hi:.0f} Hz  {d:+.0f} dB  -> too quiet on the Iridium"
                             f" ({band_section(lo, hi)})")
        for lo, hi, d in loud:
            if d > 8:
                notes.append(f"   {lo:.0f}-{hi:.0f} Hz  {d:+.0f} dB  -> too loud on the Iridium"
                             f" ({band_section(lo, hi)})")
        if (r.get("env_dtw") or 0) > 0.15:
            notes.append("   envelope/timing differs -> check amp/filter envelope times")
        if (r.get("spec_dtw") or 0) > 0.22:
            notes.append("   spectrum drifts over time -> check LFO/modulation or FX")
    return notes


def band_section(lo: float, hi: float) -> str:
    mid = (lo + hi) / 2
    if mid < 100:
        return "sub / bass"
    if mid < 500:
        return "fundamental / low mids: oscillator octave or filter cutoff"
    if mid < 2000:
        return "mids: filter cutoff/type or wavetable"
    if mid < 6000:
        return "upper mids: filter cutoff or FX"
    return "air: filter cutoff or FX"


def latest_rows(log: Path, loc: str) -> list[dict]:
    rows: dict[int, dict] = {}
    if not log.exists():
        return []
    for line in log.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("meta", {}).get("blofeld") != loc:
            continue
        note = e["meta"].get("note")
        if note is None:
            continue
        rows[int(note)] = e  # later lines win
    return [rows[k] for k in sorted(rows)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("loc")
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    loc = args.loc.upper()

    parsed = bd.parse_sndd(workflow.load_sndd_file(find_dump(loc)))
    name = parsed["name"]

    gaps, ignored = unmapped_items(parsed)
    approx = approximations(parsed)
    recs = sorted(gaps + approx, key=lambda x: -x["weight"])

    log, rows = None, []
    if args.log is not None:
        log, rows = args.log, latest_rows(args.log, loc)
    else:
        fallback = None
        for cand in DEFAULT_LOG_CANDIDATES:
            path = REPO / "recordings" / cand
            if not path.exists():
                continue
            fallback = fallback or path
            rows = latest_rows(path, loc)
            if rows:
                log = path
                break
        if log is None:
            log = fallback
    spec = spectral_notes(rows)

    prediction = None
    try:
        prediction = prognose.predict_loc(loc, REPO / "dumps", prognose.DEFAULT_MODEL)
    except Exception:  # model/dump not available -> optional
        pass

    if args.json:
        print(json.dumps({"loc": loc, "name": name, "version": __version__,
                          "check_first": recs, "ignored": ignored,
                          "spectral": spec, "prediction": prediction,
                          "log": str(log) if log else None}, indent=1))
        return 0

    print(f"{loc}  {name}   (converter v{__version__})")
    if rows:
        scores = [r["result"]["score"] for r in rows if r["result"].get("score") is not None]
        if scores:
            print(f"measured: {', '.join(f'{s:.1f}' for s in scores)}  "
                  f"(mean {sum(scores) / len(scores):.1f})")
    else:
        print("measured: no log row for this sound yet")
    if prediction:
        print(f"model:    {prediction['predicted']:.1f} ± {prediction['std']:.1f} "
              f"({prediction['model']}, target {prediction['target']}) - weak model, "
              "treat as a guess")
    print()

    print("Check first:")
    if not recs:
        print("  (no active unmapped/approximated parameters - the conversion is close to 1:1)")
    for i, r in enumerate(recs[:10], 1):
        print(f"  {i:2d}. [{r['weight']:2d}] {r['title']}")
        print(f"      {r['detail']}")
    more = len(recs) - 10
    if more > 0:
        print(f"  ... and {more} lower-impact item(s)")
    if ignored:
        print("\nDeliberately ignored (no effect by design):")
        for note in ignored[:6]:
            print(f"  - {note}")
    if spec:
        print("\nSpectral notes (latest measurement):")
        for line in spec:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
