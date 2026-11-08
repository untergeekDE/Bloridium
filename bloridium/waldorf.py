"""Waldorf-SysEx-Primitive (Basis fuers Sysex-Mapping Blofeld <-> Iridium).

Format (siehe Waldorf MIDI Implementation):
    F0 3E <IDM> <IDD> <CMD> [data] [CHK] F7
    IDW = 3E (Waldorf), IDM = Modell-ID, IDD = Device-ID (00 = default)
    Checksum wird bei Requests weggelassen; bei Dumps hinten angehaengt.

Blofeld-Kennung (empirisch bestaetigt): IDM 13h, Identity Reply enthaelt
Hersteller 3E, Familie 13, Firmware z.B. "1.24".
"""

from __future__ import annotations

WALDORF_ID = 0x3E

MODEL_IDS = {
    "microWave": 0x00,
    "Blofeld": 0x13,
    # ... bei Bedarf ergaenzen
}

# Command-Familien (x variiert je Geraet, Blofeld: SND=x0, MUL=x1, GLB=x4)
CMD = {
    "sound_request": 0x00,   # SNDR
    "sound_dump": 0x10,      # SNDD
    "multi_request": 0x01,   # MULR
    "multi_dump": 0x11,      # MULD
    "global_request": 0x04,  # GLBR
    "global_dump": 0x14,     # GLBD
}


def build_sysex(model_id: int, cmd: int, data: bytes = b"", device: int = 0,
                checksum: bool = False) -> list[int]:
    """SysEx-Datenbytes fuer mido (ohne F0/F7)."""
    body = [WALDORF_ID, model_id & 0x7F, device & 0x7F, cmd & 0x7F] + [b & 0x7F for b in data]
    if checksum:
        body.append((-(sum(body))) & 0x7F)
    return body


def parse_sysex(data) -> dict:
    """mido-SysEx-Datenbytes (ohne F0/F7) -> dict(model, device, cmd, payload)."""
    d = list(data)
    if len(d) < 4 or d[0] != WALDORF_ID:
        return {"raw": d}
    return {
        "model": d[1],
        "device": d[2],
        "cmd": d[3],
        "payload": d[4:],
    }


def identity_reply_info(data) -> dict | None:
    """Universal Identity Reply (7E .. 06 02 ...) dekodieren."""
    d = list(data)
    if len(d) >= 7 and d[0] == 0x7E and d[2] == 0x06 and d[3] == 0x02:
        manuf = d[4:7]
        fam = d[7:9] if len(d) >= 9 else []
        fw = bytes(d[9:13]).decode("ascii", "replace") if len(d) >= 13 else ""
        return {"manufacturer": manuf, "family": fam, "firmware": fw}
    return None
