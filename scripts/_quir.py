"""Internal helper: textual shell access to the Iridium (undocumented, private).

NOT part of the public workflow docs. Used by the profiling sweep only.
The command channel is deliberately kept out of every generated report.
"""
from __future__ import annotations

import time
from pathlib import Path

import mido

PORT = "Iridium Keyboard (MIDI 2.0) MIDI 2.0"
VENDOR, MODEL, DEV = 0x3E, 0x28, 0x00


class Iridium:
    def __init__(self, port: str = PORT):
        self.out = mido.open_output(port)
        self.inp = mido.open_input(port)
        self._pids: dict[str, int] = {}
        self.drain()

    # ---- low level ------------------------------------------------------
    def _send(self, cmd: int, payload: bytes = b"") -> None:
        self.out.send(mido.Message("sysex", data=[VENDOR, MODEL, DEV, *b"QUIR", cmd, *payload]))

    def _read(self, timeout: float = 0.12) -> bytes:
        buf = bytearray()
        end = time.time() + timeout
        while time.time() < end:
            for m in self.inp.iter_pending():
                if m.type != "sysex":
                    continue
                d = bytes(m.data)
                if (len(d) >= 9 and d[:7] == bytes([VENDOR, MODEL, DEV]) + b"QUIR"
                        and d[7] == 0x56):
                    buf += d[8:]
            time.sleep(0.005)
        return bytes(buf)

    def drain(self, quiet: float = 0.15, max_s: float = 20.0) -> int:
        total, t0 = 0, time.time()
        while time.time() - t0 < max_s:
            self._send(0x55)
            b = self._read(quiet)
            total += len(b)
            if not b:
                break
        return total

    # ---- shell ----------------------------------------------------------
    def line(self, text: str, wait: float = 0.10) -> None:
        """Queue one shell line (no output collection)."""
        self._send(0x57, b"." + text.encode("ascii") + b"\r")
        time.sleep(wait)

    def cmd(self, text: str, wait: float = 0.30, timeout: float = 0.5) -> str:
        self.line(text)
        time.sleep(max(0.0, wait - 0.10))
        self._send(0x55)
        return self._read(timeout).decode("ascii", "replace").strip()

    # ---- parameters -----------------------------------------------------
    def pid(self, name: str) -> int:
        if name not in self._pids:
            r = self.cmd(f"find-pid {name}", wait=0.25)
            if " pid " not in r:
                raise RuntimeError(f"no pid for {name!r}: {r!r}")
            self._pids[name] = int(r.split(" pid ")[-1])
        return self._pids[name]

    def get(self, name: str) -> float:
        r = self.cmd(f"get-param {self.pid(name)}", wait=0.25)
        return float(r.split("=")[-1])

    def set_many(self, names_values, per_cmd: float = 0.04,
                 drain_every: int = 25) -> None:
        for i, (name, value) in enumerate(names_values, 1):
            self.line(f"set-param {name} {value:.6f}", wait=per_cmd)
            if i % drain_every == 0:
                self.drain(quiet=0.07)
        time.sleep(0.30)
        self.drain(quiet=0.10)

    # ---- notes (Part 1 = ch 6 -> 0-based 5) -----------------------------
    def note_on(self, note: int = 60, velocity: int = 100, channel: int = 5) -> None:
        self.out.send(mido.Message("note_on", note=note, velocity=velocity, channel=channel))

    def note_off(self, note: int = 60, channel: int = 5) -> None:
        self.out.send(mido.Message("note_off", note=note, velocity=0, channel=channel))

    def silence_part(self, channel: int = 5) -> None:
        self.out.send(mido.Message("control_change", control=123, value=0, channel=channel))

    def close(self) -> None:
        self.out.close()
        self.inp.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def init_overrides(repo: Path | None = None) -> dict:
    """qpat overrides the converter produces for the Blofeld Init sound (A066)."""
    import sys
    repo = repo or Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo))
    from bloridium import blofeld_dump as bd, qpat_map
    p = bd.parse_sndd((repo / "dumps/banks/A/A066.bin").read_bytes())
    ov, _ = qpat_map.blofeld_to_qpat_params(p)
    return ov
