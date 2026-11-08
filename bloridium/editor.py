"""qpat-Editor – Parameter einer .qpat-Datei listen/anzeigen/setzen/speichern/diffen.

save() legt vor dem Ueberschreiben automatisch <path>.bak an (Backup des alten
Stands), sofern backup=True. Werte sind qpat-normiert 0..1 (werden geclampt).
"""

from __future__ import annotations

from pathlib import Path

from . import qpat


def list_params(parsed: dict, grep: str | None = None) -> list[tuple[str, float, str]]:
    """(name, value, display) pro Parameter; grep filtert case-insensitive auf den Namen."""
    rows = [(k, v["value"], v["display"]) for k, v in parsed["params"].items()]
    if grep:
        g = grep.lower()
        rows = [r for r in rows if g in r[0].lower()]
    return sorted(rows, key=lambda r: r[0])


def show_param(parsed: dict, key: str) -> tuple[float, str]:
    """(value, display) eines Parameters; KeyError mit Klartext bei unbekanntem Key."""
    if key not in parsed["params"]:
        raise KeyError(f"unbekannter qpat-Parameter: {key!r} "
                       f"(verfuegbar: {len(parsed['params'])}, z. B. {sorted(parsed['params'])[0]!r})")
    p = parsed["params"][key]
    return p["value"], p["display"]


def set_param(parsed: dict, key: str, value: float, display: str | None = None) -> None:
    """Wert setzen (clamp 0..1); display nur ueberschreiben, wenn angegeben.

    Unbekannter Key -> KeyError (Tippfehler duerfen nicht stillschweigend einen
    neuen, bedeutungslosen Parameter im Geraete-File anlegen).
    """
    if key not in parsed["params"]:
        raise KeyError(f"unbekannter qpat-Parameter: {key!r} "
                       f"(verfuegbar: {len(parsed['params'])}, z. B. {sorted(parsed['params'])[0]!r})")
    value = max(0.0, min(1.0, float(value)))
    old = parsed["params"][key]
    new_disp = display if display is not None else old["display"]
    parsed["params"][key] = {"value": value, "display": new_disp}
    # rohe Record-Felder mitsyncen, damit save() das neue Display schreibt
    rf = parsed.get("_raw_fields", {})
    if key in rf:
        rf[key] = (rf[key][0], qpat._pad32(new_disp))


def save(parsed: dict, path, backup: bool = True) -> Path:
    """.qpat schreiben; vorher <path>.bak mit dem alten Dateiinhalt anlegen."""
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
    """Nur differing Keys: (key, value_a, value_b, display_a, display_b); fehlende Seite = None."""
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
