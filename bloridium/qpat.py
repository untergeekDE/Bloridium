"""Waldorf Quantum/Iridium .qpat – Parser + Writer.

Format (autosamplerT src/export/export_qpat.py + eigene Hexdump-Analyse offizieller
Waldorf-Files, siehe docs/FINDINGS.md):

  Header (512 B):
    0x000  u32 LE magic = 3402932 (0x0033ECB4 -> b4 ec 33 00)
    0x004  u32 LE preset version (14 aktuell; Geraete-Files auch 8/10)
    0x008  char[32] name
    0x028  char[32] creator/author
    0x048  char[32] description
    0x068  char[32] category + 3x char[32] keywords (4 Slots)
    0x0E8  u16 LE param count, u16 pad
    0x0EC  16x Resource-Header je 12 B: u32 type, u32 offset(0), u32 length
             (Typen 4/5/6 = USER_SAMPLE_MAP1..3; 0 = unused)
    0x1AC  u16 layer2a, u16 layer2b, u32 layer2c  (2nd-Layer-Info)
    0x1B4  u8 instrument type (0 = Quantum/Iridium)
    pad    auf 0x200
  0x200  Parameter-Records, je 68 B, Anzahl = param count:
             float32 LE normalized value (0..1)
             char[32]  name (z.B. "Osc1Type")
             char[32]  display (z.B. "Kernels", "+0.000 dB")
  danach: Sample-Maps (tab-getrennter Text, Ressourcen 4..6)
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
        raise ValueError(f"kein .qpat (magic {data[:4].hex()})")
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
        "sample_maps": [],
    }
    for i in range(16):
        off = 0xEC + 12 * i
        rtype, roff, rlen = struct.unpack("<III", data[off:off + 12])
        r["resources"].append({"type": rtype, "offset": roff, "length": rlen})
    # Parameter-Records ab 0x200
    pos = HEADER_SIZE
    n = r["param_count"]
    for _ in range(n):
        if pos + RECORD_SIZE > len(data):
            break
        val = struct.unpack("<f", data[pos:pos + 4])[0]
        name = _cstr(data[pos + 4:pos + 36])
        disp = _cstr(data[pos + 36:pos + 68])
        if name:
            r["params"][name] = {"value": val, "display": disp}
        pos += RECORD_SIZE
    # Sample-Maps (Ressourcen Typ 4..6) – als Text an den Resource-Positionen
    body = data[HEADER_SIZE:]
    for res in r["resources"]:
        if res["type"] in (4, 5, 6) and res["length"] > 0:
            # offset ist relativ zum Param-Bereich? autosamplerT schreibt maps ans Ende;
            # wir nehmen: maps liegen direkt nach den Records
            pass
    # pragmatisch: Rest nach den Records als Text dekodieren
    rest = data[pos:]
    txt = rest.decode("ascii", "replace")
    maps = [m for m in txt.split("\x00") if m.strip()]
    r["sample_maps"] = maps
    r["_records_end"] = pos
    return r


def load(path) -> dict:
    return parse_qpat(Path(path).read_bytes())


def build_qpat(name: str, params: dict, creator: str = "bloridium",
                description: str = "", categories: list | None = None,
                version: int = PRESET_VERSION, sample_maps: list | None = None) -> bytes:
    """params: {name: (value_float, display_str)} oder {name: value_float}."""
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
    out += struct.pack("<H", len(items)) + b"\x00\x00"
    # 16 Resource-Header
    for i in range(16):
        if i < len(sample_maps):
            out += struct.pack("<III", 4 + i, 0, len(sample_maps[i].encode()))
        else:
            out += struct.pack("<III", 0, 0, 0)
    out += struct.pack("<HHI", 0, 0, 0)  # 2nd layer info
    out += b"\x00"                        # instrument type
    if len(out) < HEADER_SIZE:
        out += b"\x00" * (HEADER_SIZE - len(out))
    # Parameter-Records
    for k, val, disp in items:
        out += struct.pack("<f", val)
        out += _pad32(k)
        out += _pad32(disp)
    # Sample-Maps
    for m in sample_maps:
        out += m.encode("utf-8")
    return bytes(out)


if __name__ == "__main__":
    import sys
    r = load(sys.argv[1])
    print(f"name={r['name']!r} creator={r['creator']!r} cats={r['categories']} ver={r['version']} params={r['param_count']}")
    for k, v in list(r["params"].items())[:40]:
        print(f"  {k:34s} value={v['value']:.4f}  display={v['display']!r}")
