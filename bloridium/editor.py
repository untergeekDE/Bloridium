"""qpat editor - list/show/set/save/diff parameters of a .qpat file.

save() automatically creates <path>.bak before overwriting (backup of the old
state) if backup=True. Values are qpat-normalized 0..1 (clamped).
"""

from __future__ import annotations

from pathlib import Path

from . import qpat


def list_params(parsed: dict, grep: str | None = None) -> list[tuple[str, float, str]]:
    """(name, value, display) per parameter; grep filters case-insensitively on the name."""
    rows = [(k, v["value"], v["display"]) for k, v in parsed["params"].items()]
    if grep:
        g = grep.lower()
        rows = [r for r in rows if g in r[0].lower()]
    return sorted(rows, key=lambda r: r[0])


def show_param(parsed: dict, key: str) -> tuple[float, str]:
    """(value, display) of one parameter; KeyError with plain text on unknown key."""
    if key not in parsed["params"]:
        raise KeyError(f"unknown qpat parameter: {key!r} "
                       f"(available: {len(parsed['params'])}, e.g. {sorted(parsed['params'])[0]!r})")
    p = parsed["params"][key]
    return p["value"], p["display"]


def set_param(parsed: dict, key: str, value: float, display: str | None = None) -> None:
    """Set value (clamp 0..1); only overwrite display if given.

    Unknown key -> KeyError (typos must not silently create a new,
    meaningless parameter in the device file).
    """
    if key not in parsed["params"]:
        raise KeyError(f"unknown qpat parameter: {key!r} "
                       f"(available: {len(parsed['params'])}, e.g. {sorted(parsed['params'])[0]!r})")
    value = max(0.0, min(1.0, float(value)))
    old = parsed["params"][key]
    new_disp = display if display is not None else old["display"]
    parsed["params"][key] = {"value": value, "display": new_disp}
    # sync raw record fields so that save() writes the new display
    rf = parsed.get("_raw_fields", {})
    if key in rf:
        rf[key] = (rf[key][0], qpat._pad32(new_disp))


def save(parsed: dict, path, backup: bool = True) -> Path:
    """Write .qpat; beforehand create <path>.bak with the old file content."""
    p = Path(path)
    if backup and p.exists():
        Path(str(p) + ".bak").write_bytes(p.read_bytes())
    data = qpat.build_qpat(
        parsed["name"],
        {k: (v["value"], v["display"]) for k, v in parsed["params"].items()},
        creator=parsed.get("creator", "bloridium"),
        description=parsed.get("description", ""),
        categories=parsed.get("categories", ["", "", "", ""]),
        version=parsed.get("version", qpat.PRESET_VERSION),
        sample_maps=parsed.get("sample_maps", []),
        tail=parsed.get("_tail"),  # byte-faithful: Sample-Maps/Multi-Patch-Tail 1:1
        resources=parsed.get("resources"),
        layer2=parsed.get("layer2", (0, 0, 0)),
        instrument=parsed.get("instrument", 0),
        raw_fields=parsed.get("_raw_fields"),
        records_raw=parsed.get("_records_raw"),
        header_pad=parsed.get("_header_pad"),
    )
    p.write_bytes(data)
    return p


def diff_params(a: dict, b: dict) -> list[tuple]:
    """Only differing keys: (key, value_a, value_b, display_a, display_b); missing side = None."""
    out = []
    for k in sorted(set(a["params"]) | set(b["params"])):
        pa, pb = a["params"].get(k), b["params"].get(k)
        va = pa["value"] if pa else None
        vb = pb["value"] if pb else None
        da = pa["display"] if pa else None
        db_ = pb["display"] if pb else None
        if va != vb or da != db_:
            out.append((k, va, vb, da, db_))
    return out
