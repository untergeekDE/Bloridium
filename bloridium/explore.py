"""OS4 pid exploration on the Iridium: decode NRPN captures + book them into the CC list.

Read-only - this module sends no MIDI. NRPN format (capture
recordings/midi_monitor_20261109_090256.log, ch6 = Part 1):
  CC99 = pid MSB, CC98 = pid LSB, CC6 = value MSB, CC38 = value LSB (14-bit).
  CC99/CC98 = 127 -> NRPN off (reset); CC121 (Reset All Controllers) resets everything;
  CC101/100 (RPN) are ignored.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

# (pid, value14)
NrpnEvent = tuple[int, int]

# iridium_os4_cc_list.csv: new columns are appended to the existing 8
NEW_COLUMNS = ["pid_os4", "nrpn_min", "nrpn_max", "nrpn_last", "explore_ts", "explore_msgs"]


class NrpnDecoder:
    """State machine over control_change messages of one selected channel.

    feed(msg) -> NrpnEvent once the pid (CC99+CC98) is set and a data byte
    arrives. CC6 (data MSB) alone is an event with LSB=0 (observed 2026-11-09:
    the Iridium sends only '06 00' at value 0, without '26'); CC38 reuses the
    last MSB. The pid stays set - turning the same parameter yields further
    events without new CC99/98.
    """

    def __init__(self) -> None:
        self._msb: int | None = None
        self._lsb: int | None = None
        self._dmsb: int | None = None
        self._dlsb: int | None = None
        self._data_seen = False

    def _reset_all(self) -> None:
        self._msb = self._lsb = None
        self._dmsb = self._dlsb = None
        self._data_seen = False

    def feed(self, msg) -> NrpnEvent | None:
        if msg.type != "control_change":
            return None
        c, v = msg.control, msg.value
        if c == 99:                      # NRPN MSB (127 = NRPN off); a new pid needs new data
            self._msb = None if v == 127 else v
            self._data_seen = False
        elif c == 98:                    # NRPN LSB (127 = NRPN off)
            self._lsb = None if v == 127 else v
            self._data_seen = False
        elif c == 6:                     # data MSB alone: LSB implicitly 0
            self._dmsb = v
            self._dlsb = 0
            self._data_seen = True
        elif c == 38:                    # data LSB: MSB stays at last value
            self._dlsb = v
            self._data_seen = True
        elif c == 121:                   # Reset All Controllers
            self._reset_all()
            return None
        else:                            # incl. CC101/100 (RPN): ignore
            return None
        if self._msb is not None and self._lsb is not None and self._data_seen:
            self._data_seen = False
            return ((self._msb << 7) | self._lsb,
                    ((self._dmsb or 0) << 7) | (self._dlsb or 0))
        return None


# ---- CSV-State (iridium_os4_cc_list.csv) ------------------------------------


def load_cc_list(path) -> tuple[list[str], list[dict]]:
    """CSV -> (fieldnames, rows); missing NEW_COLUMNS are added as ""."""
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fieldnames = list(r.fieldnames or [])
        rows = [dict(row) for row in r]
    for row in rows:
        for c in NEW_COLUMNS:
            row.setdefault(c, "")
    return fieldnames, rows


def save_cc_list(path, fieldnames: list[str], rows: list[dict], backup: bool = False) -> None:
    """Write CSV; NEW_COLUMNS are appended to fieldnames.

    backup=True creates <path>.bak with the old file content before writing.
    """
    p = Path(path)
    if backup and p.exists():
        Path(str(p) + ".bak").write_bytes(p.read_bytes())
    fields = list(fieldnames) + [c for c in NEW_COLUMNS if c not in fieldnames]
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def _nutzung_pct(row: dict) -> float:
    try:
        return float(row.get("nutzung_pct") or "")
    except ValueError:
        return -1.0  # "-" or empty = lowest priority


def pending_rows(rows: list[dict], essential: bool = False, grep: str | None = None,
                 only_cc: str | None = None) -> list[dict]:
    """Not yet verified rows (os4_verified == "nein"), sorted:
    essential=yes first, then nutzung_pct descending, then cc ascending."""
    out = [r for r in rows if (r.get("os4_verified") or "").strip().lower() == "nein"]
    if essential:
        out = [r for r in out if (r.get("essential") or "").strip().lower() == "yes"]
    if grep:
        g = grep.lower()
        out = [r for r in out
               if g in (r.get("iridium_param") or "").lower()
               or g in (r.get("zugehoeriger_blofeld_param") or "").lower()]
    if only_cc:
        wanted = {int(x) for x in only_cc.split(",") if x.strip()}
        out = [r for r in out if int(r["cc"]) in wanted]
    out.sort(key=lambda r: (0 if (r.get("essential") or "").strip().lower() == "yes" else 1,
                            -_nutzung_pct(r), int(r["cc"])))
    return out


def book_row(row: dict, events: list[NrpnEvent], ts: str) -> dict:
    """Book the events of one capture into the row; returns the JSONL log entry.

    Winning pid = most frequent pid; nrpn_min/max/last and explore_msgs refer
    only to the winner's events. abweichung = pid_os4 != rdb pid.
    """
    counts = Counter(pid for pid, _ in events)
    pid_os4, _ = counts.most_common(1)[0]
    vals = [v for p, v in events if p == pid_os4]
    row["pid_os4"] = str(pid_os4)
    row["nrpn_min"] = str(min(vals))
    row["nrpn_max"] = str(max(vals))
    row["nrpn_last"] = str(vals[-1])
    row["explore_msgs"] = str(len(vals))
    row["explore_ts"] = ts
    row["os4_verified"] = "ja"
    try:
        pid_rdb = int(row.get("pid") or "")
    except ValueError:
        pid_rdb = -1
    return {
        "ts": ts,
        "cc": row.get("cc", ""),
        "iridium_param": row.get("iridium_param", ""),
        "pid_rdb": row.get("pid", ""),
        "pid_os4": pid_os4,
        "abweichung": pid_os4 != pid_rdb,
        "nrpn_min": min(vals),
        "nrpn_max": max(vals),
        "nrpn_last": vals[-1],
        "n_msgs": len(vals),
        "werte": vals,
        "alle_pids": sorted(counts),
    }


def append_log(log_path, entry: dict) -> None:
    """Append one JSON line to the explore log."""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
