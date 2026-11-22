#!/usr/bin/env python3
"""Re-convert Blofeld bank A (A001-A100) to SD-ready Iridium .qpat files.

Reads the SNDD dumps from `dumps/` (or another dump dir), converts each location
with the current qpat_map, writes `<LOC>_<Name>.qpat` plus `MANIFEST.json` /
`MANIFEST.md`, and validates every file by parsing it back.

The output folder is meant to be copied 1:1 to the Iridium SD card, e.g.:

    python3 scripts/reconvert_rf.py --out transfer/rf100_v3 --sd-dir rf300
    cp -R transfer/rf100_v3 /Volumes/<SD>/rf300

No spaces in qpat names (qpat.sd_filename), so device-side load paths (`2:rf300/...`)
paths always work. `transfer/` is gitignored; the manifest is the hand-off.

Usage:
    python3 scripts/reconvert_rf.py [--start A001] [--end A100]
                                    [--dumps dumps] [--out transfer/rf100_v3]
                                    [--sd-dir rf300] [--slot-start 300]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from bloridium import blofeld_dump as bd, qpat, qpat_map, workflow  # noqa: E402
from bloridium.version import __version__  # noqa: E402

SD_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def loc_number(loc: str) -> int:
    m = re.fullmatch(r"([A-Z])(\d{3})", loc.upper())
    if not m:
        raise ValueError(f"invalid location {loc!r} (expected A001..Z128)")
    return (ord(m.group(1)) - ord("A")) * 128 + int(m.group(2))


def loc_from_number(n: int, bank: str = "A") -> str:
    return f"{bank}{n:03d}"


def find_dump(dumps_dir: Path, loc: str) -> Path | None:
    """Prefer the bank file dumps/banks/A/A###.bin, else the newest SNDD dump."""
    bank = dumps_dir / "banks" / loc[0] / f"{loc}.bin"
    if bank.exists():
        return bank
    best = None
    for p in sorted(dumps_dir.glob(f"*{loc}*.bin")):
        if best is None or p.name > best.name:
            best = p
    return best


def convert_entry(dumps_dir: Path, out_dir: Path, loc: str, slot: int,
                  sd_dir: str) -> dict:
    dump = find_dump(dumps_dir, loc)
    if dump is None:
        raise FileNotFoundError(f"no SNDD dump for {loc} in {dumps_dir}")
    parsed = bd.parse_sndd(workflow.load_sndd_file(dump))
    if not parsed.get("chk_ok"):
        raise ValueError(f"{loc}: checksum wrong in {dump.name}")
    out_path, mapped, unmapped = workflow.convert_parsed(parsed, loc, out_dir)
    # roundtrip validation: the qpat must parse and carry the v14 record set
    check = qpat.load(out_path)
    if check["version"] != qpat.PRESET_VERSION:
        raise ValueError(f"{loc}: wrote version {check['version']}, expected "
                         f"{qpat.PRESET_VERSION}")
    if not check["params"]:
        raise ValueError(f"{loc}: empty qpat")
    sd_name = out_path.name
    if not SD_NAME_RE.fullmatch(sd_name):
        raise ValueError(f"{loc}: SD-unsafe file name {sd_name!r}")
    return {
        "loc": loc,
        "label": parsed["name"],
        "qpat": sd_name,
        "sd_name": sd_name,
        "remote": f"2:{sd_dir}/{sd_name}",
        "slot": slot,
        "mapped": mapped,
        "unmapped_count": len(unmapped),
    }


def write_manifest(out_dir: Path, sd_dir: str, entries: list[dict],
                   source: str) -> None:
    manifest = {
        "sd_dir": sd_dir,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "conversion_version": __version__,
        "count": len(entries),
        "entries": entries,
    }
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        f"# Blofeld A001-A100 -> Iridium qpats (v{__version__})",
        "",
        f"SD folder: `{sd_dir}` · {len(entries)} sounds · "
        f"copy this folder as `{sd_dir}/` to the SD card.",
        "",
        "| Loc | Name | qpat | Slot | mapped | unmapped |",
        "|---|---|---|---:|---:|---:|",
    ]
    for e in entries:
        lines.append(f"| {e['loc']} | {e['label']} | `{e['qpat']}` | {e['slot']} "
                     f"| {e['mapped']} | {e['unmapped_count']} |")
    (out_dir / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="A001")
    ap.add_argument("--end", default="A100")
    ap.add_argument("--bank", default="A")
    ap.add_argument("--dumps", type=Path, default=REPO / "dumps")
    ap.add_argument("--out", type=Path, default=REPO / "transfer" / "rf100_v3")
    ap.add_argument("--sd-dir", default="rf300",
                    help="folder name on the SD card (2:<sd-dir>/...)")
    ap.add_argument("--slot-start", type=int, default=300)
    args = ap.parse_args(argv)

    start, end = loc_number(args.start), loc_number(args.end)
    if end < start:
        raise SystemExit("--end must be >= --start")
    args.out.mkdir(parents=True, exist_ok=True)

    entries, errors = [], []
    for i, n in enumerate(range(start, end + 1)):
        loc = args.bank + f"{n:03d}"
        try:
            entry = convert_entry(args.dumps, args.out, loc,
                                  args.slot_start + i, args.sd_dir)
        except Exception as exc:  # keep going: one bad dump must not stop the bank
            errors.append(f"{loc}: {exc}")
            print(f"ERROR {loc}: {exc}", flush=True)
            continue
        entries.append(entry)
        print(f"{loc:5s} {entry['label'][:28]:28s} {entry['qpat']:38s} "
              f"mapped {entry['mapped']:3d}  unmapped {entry['unmapped_count']:2d}",
              flush=True)

    if not entries:
        print("no qpats written", flush=True)
        return 1
    write_manifest(args.out, args.sd_dir, entries, str(args.dumps))
    mapped = [e["mapped"] for e in entries]
    print(f"\n{len(entries)} qpats -> {args.out} (SD dir {args.sd_dir}), "
          f"mapped {min(mapped)}..{max(mapped)} (mean {sum(mapped) / len(mapped):.1f})")
    if errors:
        print(f"{len(errors)} errors:", flush=True)
        for e in errors:
            print("  ", e, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
