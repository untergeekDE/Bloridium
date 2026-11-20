"""Waldorf Quantum/Iridium .qpat – Parser + Writer.

Format (autosamplerT src/export/export_qpat.py + own hexdump analysis of official
Waldorf files, see docs/FINDINGS.md):

  Header (512 B):
    0x000  u32 LE magic = 3402932 (0x0033ECB4 -> b4 ec 33 00)
    0x004  u32 LE preset version (14 current; device files also 8/10)
    0x008  char[32] name
    0x028  char[32] creator/author
    0x048  char[32] description
    0x068  char[32] category + 3x char[32] keywords (4 slots)
    0x0E8  u16 LE param count, u16 pad
    0x0EC  16x resource header, 12 B each: u32 type, u32 offset(0), u32 length
             (types 4/5/6 = USER_SAMPLE_MAP1..3; 0 = unused)
    0x1AC  u16 layer2a, u16 layer2b, u32 layer2c  (2nd layer info)
    0x1B4  u8 instrument type (0 = Quantum/Iridium)
    pad    to 0x200
  0x200  parameter records, 68 B each, count = param count:
             float32 LE normalized value (0..1)
             char[32]  name (e.g. "Osc1Type")
             char[32]  display (e.g. "Kernels", "+0.000 dB")
  after that: sample maps (tab-separated text, resources 4..6)
"""

from __future__ import annotations

import struct
from pathlib import Path

MAGIC = 3402932  # 0x0033ECB4
PRESET_VERSION = 14
HEADER_SIZE = 512
RECORD_SIZE = 68


def _pad32(s: str) -> bytes:
    b = s.encode("ascii", "replace")[:32]
    return b + b"\x00" * (32 - len(b))


def _cstr(b: bytes) -> str:
    return b.split(b"\x00")[0].decode("ascii", "replace")


def parse_qpat(data: bytes) -> dict:
    if len(data) < HEADER_SIZE or struct.unpack("<I", data[0:4])[0] != MAGIC:
        raise ValueError(f"not a .qpat (magic {data[:4].hex()})")
    version = struct.unpack("<I", data[4:8])[0]
    r = {
        "version": version,
        "name": _cstr(data[0x08:0x28]),
        "creator": _cstr(data[0x28:0x48]),
        "description": _cstr(data[0x48:0x68]),
        "categories": [_cstr(data[0x68 + 32 * i: 0x88 + 32 * i]) for i in range(4)],
        "param_count": struct.unpack("<H", data[0xE8:0xEA])[0],
        "resources": [],
        "params": {},   # name -> {"value": float, "display": str}
        "_raw_fields": {},  # name -> (raw 32B name, raw 32B display) for byte-faithful rebuild
        "sample_maps": [],
    }
    for i in range(16):
        off = 0xEC + 12 * i
        rtype, roff, rlen = struct.unpack("<III", data[off:off + 12])
        r["resources"].append({"type": rtype, "offset": roff, "length": rlen})
    r["layer2"] = struct.unpack("<HHI", data[0x1AC:0x1B4])
    r["instrument"] = data[0x1B4]
    r["_header_pad"] = data[0x1B5:HEADER_SIZE]  # padding up to 0x200 (sometimes used)
    # parameter records from 0x200
    pos = HEADER_SIZE
    n = r["param_count"]
    r["_records_raw"] = []  # all n records raw (incl. unnamed) for byte-faithful rebuild
    for _ in range(n):
        if pos + RECORD_SIZE > len(data):
            break
        chunk = data[pos:pos + RECORD_SIZE]
        r["_records_raw"].append(chunk)
        val = struct.unpack("<f", chunk[0:4])[0]
        name = _cstr(chunk[4:36])
        disp = _cstr(chunk[36:68])
        if name:
            r["params"][name] = {"value": val, "display": disp}
            r["_raw_fields"][name] = (chunk[4:36], chunk[36:68])
        pos += RECORD_SIZE
    # sample maps (resources type 4..6) - as text at the resource positions
    body = data[HEADER_SIZE:]
    for res in r["resources"]:
        if res["type"] in (4, 5, 6) and res["length"] > 0:
            # offset relative to the param area? autosamplerT writes maps at the end;
            # we take: maps sit directly after the records
            pass
    # pragmatic: decode the rest after the records as text
    rest = data[pos:]
    r["_tail"] = rest  # raw tail (sample maps as text OR further patches in multi-patch files)
    txt = rest.decode("ascii", "replace")
    maps = [m for m in txt.split("\x00") if m.strip()]
    r["sample_maps"] = maps
    r["_records_end"] = pos
    return r


def load(path) -> dict:
    return parse_qpat(Path(path).read_bytes())


def sd_filename(loc: str, name: str) -> str:
    """SD-sicherer qpat-Dateiname `<LOC>_<Name>.qpat` — keine Leerzeichen, nur
    [A-Za-z0-9-_.], damit QUIR-Shell-Pfade (`load-patch 2:<dir>/<file>`) nie brechen.

    Leerzeichen -> '_', Sonderzeichen gestrichen, fuehrende/abschliessende '.'/'_'
    entfernt; leer -> loc als Fallback ('JMX jun.' -> 'A001_JMX_jun.qpat').
    (2026-11-20: Conversion schreibt Dateien direkt mit diesem Namen, plain cp
    auf die SD reicht; identisch zum bisherigen quir_rf_dataset.sd_name.)"""
    base = (name or "").strip().replace(" ", "_")
    base = "".join(c for c in base if c.isalnum() or c in "-_")
    base = base.strip("._") or loc
    return f"{loc}_{base}.qpat"


def build_qpat(name: str, params: dict, creator: str = "bloridium",
                description: str = "", categories: list | None = None,
                version: int = PRESET_VERSION, sample_maps: list | None = None,
                tail: bytes | None = None, resources: list | None = None,
                layer2: tuple = (0, 0, 0), instrument: int = 0,
                raw_fields: dict | None = None, records_raw: list | None = None,
                header_pad: bytes | None = None) -> bytes:
    """params: {name: (value_float, display_str)} or {name: value_float}.

    `tail`: raw file tail after the records (sample maps / further patches) -
    appended 1:1 so that parse->build is byte-identical. Without `tail`,
    `sample_maps` are appended NUL-separated (with trailing NUL).
    `resources`: 16 resource header dicts (written 1:1).
    """
    sample_maps = sample_maps or []
    items = []
    for k, v in params.items():
        if isinstance(v, tuple):
            val, disp = v
        else:
            val, disp = v, ""
        items.append((k, float(val), disp))
    out = bytearray()
    out += struct.pack("<I", MAGIC)
    out += struct.pack("<I", version)
    out += _pad32(name)
    out += _pad32(creator)
    out += _pad32(description)
    cats = (categories or ["", "", "", ""])[:4]
    for c in cats:
        out += _pad32(c)
    n_records = len(records_raw) if records_raw else len(items)
    out += struct.pack("<H", n_records) + b"\x00\x00"
    # 16 resource headers
    if resources is not None:
        for i in range(16):
            r = resources[i] if i < len(resources) else {"type": 0, "offset": 0, "length": 0}
            out += struct.pack("<III", r["type"], r["offset"], r["length"])
    else:
        for i in range(16):
            if i < len(sample_maps):
                out += struct.pack("<III", 4 + i, 0, len(sample_maps[i].encode()))
            else:
                out += struct.pack("<III", 0, 0, 0)
    out += struct.pack("<HHI", *layer2)   # 2nd layer info
    out += bytes([instrument & 0xFF])      # instrument type
    if header_pad is not None:
        out += header_pad[: HEADER_SIZE - len(out)]
    if len(out) < HEADER_SIZE:
        out += b"\x00" * (HEADER_SIZE - len(out))
    # parameter records (raw records when available -> byte-faithful; named
    # records are rebuilt from `params` so that edited values are taken over)
    raw_fields = raw_fields or {}
    if records_raw:
        for chunk in records_raw:
            nm = _cstr(chunk[4:36])
            if nm and nm in params:
                v = params[nm]
                val, disp = v if isinstance(v, tuple) else (v, "")
                out += struct.pack("<f", float(val))
                if nm in raw_fields:
                    out += raw_fields[nm][0] + raw_fields[nm][1]
                else:
                    out += _pad32(nm) + _pad32(disp)
            else:
                out += chunk
    else:
        for k, val, disp in items:
            out += struct.pack("<f", val)
            if k in raw_fields:
                out += raw_fields[k][0] + raw_fields[k][1]
            else:
                out += _pad32(k)
                out += _pad32(disp)
    # tail: raw 1:1 (preferred) or sample maps NUL-separated
    if tail is not None:
        out += tail
    else:
        for m in sample_maps:
            out += m.encode("utf-8") + b"\x00"
    return bytes(out)


if __name__ == "__main__":
    import sys
    r = load(sys.argv[1])
    print(f"name={r['name']!r} creator={r['creator']!r} cats={r['categories']} ver={r['version']} params={r['param_count']}")
    for k, v in list(r["params"].items())[:40]:
        print(f"  {k:34s} value={v['value']:.4f}  display={v['display']!r}")
