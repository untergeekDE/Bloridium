"""Minimal Standard MIDI File (SMF, .mid) reader — extract raw SysEx messages.

Pure Python, no mido: the webapp container has no MIDI stack. Parses just
enough SMF to pull Blofeld SNDD dumps out of a .mid: MThd header, MTrk
chunks, events with delta-time varlen, meta events (0xFF), SysEx events
(0xF0 / 0xF7, each with a varlen length) and channel messages incl. running
status.

Returns complete messages ``F0 ... F7``. Some writers include the trailing
F7 in the 0xF0 event payload, others don't (spec) — both are normalized
here. An 0xF7 event continues an open 0xF0 message (escaped SysEx); a lone
0xF7 event without an open message is skipped.

Example: a Blofeld bank exported as .mid (e.g. Voltage-Bank-C.mid) holds one
0xF0 event per sound, payload = 3E 13 DEV 10 BB NN <383 B SDATA> CHK [F7].
"""

from __future__ import annotations


class MidiFileError(ValueError):
    """Malformed .mid – rendered by the app as HTTP 400."""


def is_smf(data: bytes) -> bool:
    return data[:4] == b"MThd"


def _varlen(data: bytes, pos: int) -> tuple[int, int]:
    """Read a MIDI variable-length quantity at pos; returns (value, next_pos)."""
    val = 0
    for _ in range(4):  # varlen is at most 4 bytes
        if pos >= len(data):
            raise MidiFileError("truncated varlen")
        b = data[pos]
        pos += 1
        val = (val << 7) | (b & 0x7F)
        if not (b & 0x80):
            return val, pos
    raise MidiFileError("varlen longer than 4 bytes")


# data bytes of system-common messages (realtime 0xF8..0xFE carry none)
_SYS_COMMON_LEN = {0xF1: 1, 0xF2: 2, 0xF3: 1, 0xF6: 0}


def _parse_track(body: bytes, msgs: list[bytes]) -> None:
    pos, n = 0, len(body)
    running = None
    open_msg = None  # payload of an unterminated 0xF0 event
    while pos < n:
        _, pos = _varlen(body, pos)  # delta time – irrelevant for extraction
        if pos >= n:
            raise MidiFileError("truncated track event")
        st = body[pos]
        if st == 0xFF:  # meta event
            pos += 1
            if pos >= n:
                raise MidiFileError("truncated meta event")
            mtype = body[pos]
            pos += 1
            length, pos = _varlen(body, pos)
            pos += length
            if pos > n:
                raise MidiFileError("meta event past end of track")
            if mtype == 0x2F:  # end of track
                break
            running = None
        elif st == 0xF0:  # sysex start
            pos += 1
            length, pos = _varlen(body, pos)
            payload = body[pos:pos + length]
            if len(payload) != length:
                raise MidiFileError("sysex event past end of track")
            pos += length
            if open_msg is not None:  # previous message never got an F7 event
                msgs.append(_close(open_msg))
            if payload.endswith(b"\xf7"):  # writer included the terminator
                msgs.append(b"\xf0" + payload)
                open_msg = None
            else:
                open_msg = payload  # may continue in a following 0xF7 event
            running = None
        elif st == 0xF7:  # sysex continuation (escaped) or standalone
            pos += 1
            length, pos = _varlen(body, pos)
            payload = body[pos:pos + length]
            if len(payload) != length:
                raise MidiFileError("sysex continuation past end of track")
            pos += length
            if open_msg is not None:
                open_msg += payload
                msgs.append(_close(open_msg))
                open_msg = None
            running = None
        elif st >= 0xF0:  # system common / realtime
            if st in _SYS_COMMON_LEN:
                pos += 1 + _SYS_COMMON_LEN[st]
                running = None
            # 0xF8..0xFE carry no data bytes and don't touch running status
        else:  # channel message, possibly with running status
            if st & 0x80:
                running = st
                pos += 1
            elif running is None:
                raise MidiFileError(f"running status without status byte at {pos}")
            hi = running & 0xF0
            pos += 1 if hi in (0xC0, 0xD0) else 2
    if open_msg is not None:  # tolerate a missing final F7
        msgs.append(_close(open_msg))


def _close(payload: bytes) -> bytes:
    """F0 + payload (+ F7 if the writer left it out of the event)."""
    msg = b"\xf0" + payload
    if not msg.endswith(b"\xf7"):
        msg += b"\xf7"
    return msg


def extract_sysex(data: bytes) -> list[bytes]:
    """All complete SysEx messages (F0..F7) contained in an SMF file."""
    if not is_smf(data):
        raise MidiFileError("no MThd header – not a Standard MIDI File")
    if len(data) < 8:
        raise MidiFileError("truncated MThd")
    hlen = int.from_bytes(data[4:8], "big")
    if hlen < 6 or 8 + hlen > len(data):
        raise MidiFileError("bad MThd length")
    msgs: list[bytes] = []
    pos = 8 + hlen
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        clen = int.from_bytes(data[pos + 4:pos + 8], "big")
        body = data[pos + 8:pos + 8 + clen]
        if len(body) != clen:
            raise MidiFileError(f"truncated chunk {cid!r}")
        if cid == b"MTrk":
            _parse_track(body, msgs)
        # unknown chunk types are skipped per SMF spec
        pos += 8 + clen
    if not msgs and pos < len(data) and data[pos:pos + 4] not in (b"", b"MTrk"):
        pass  # trailing garbage without chunk header – ignored
    return msgs
