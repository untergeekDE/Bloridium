"""OS4-Pid-Exploration am Iridium: NRPN-Mitschnitt dekodieren + in die CC-Liste buchen.

Rein lesend – dieses Modul sendet kein MIDI. NRPN-Format (Mitschnitt
recordings/midi_monitor_20261109_090256.log, ch6 = Part 1):
  CC99 = Pid-MSB, CC98 = Pid-LSB, CC6 = Wert-MSB, CC38 = Wert-LSB (14-bit).
  CC99/CC98 = 127 -> NRPN aus (Reset); CC121 (Reset All Controllers) resetet alles;
  CC101/100 (RPN) werden ignoriert.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

# (pid, value14)
NrpnEvent = tuple[int, int]

# iridium_os4_cc_list.csv: neue Spalten werden an die bestehenden 8 angehängt
NEW_COLUMNS = ["pid_os4", "nrpn_min", "nrpn_max", "nrpn_last", "explore_ts", "explore_msgs"]


class NrpnDecoder:
    """State-Machine ueber control_change-Messages eines gewaehlten Kanals.

    feed(msg) -> NrpnEvent, sobald Pid (CC99+CC98) und Wert (CC6+CC38) komplett
    sind; danach werden die Daten-Bytes zurueckgesetzt (Pid bleibt – der Dreh
    am selben Parameter liefert danach weitere Events ohne neues CC99/98).
    """

    def __init__(self) -> None:
        self._msb: int | None = None
        self._lsb: int | None = None
        self._dmsb: int | None = None
        self._dlsb: int | None = None

    def _reset_all(self) -> None:
        self._msb = self._lsb = self._dmsb = self._dlsb = None

    def feed(self, msg) -> NrpnEvent | None:
        if msg.type != "control_change":
            return None
        c, v = msg.control, msg.value
        if c == 99:                      # NRPN MSB (127 = NRPN aus)
            self._msb = None if v == 127 else v
        elif c == 98:                    # NRPN LSB (127 = NRPN aus)
            self._lsb = None if v == 127 else v
        elif c == 6:                     # Data MSB
            self._dmsb = v
        elif c == 38:                    # Data LSB
            self._dlsb = v
        elif c == 121:                   # Reset All Controllers
            self._reset_all()
            return None
        else:                            # inkl. CC101/100 (RPN): ignorieren
            return None
        if (self._msb is not None and self._lsb is not None
                and self._dmsb is not None and self._dlsb is not None):
            event = ((self._msb << 7) | self._lsb, (self._dmsb << 7) | self._dlsb)
            self._dmsb = self._dlsb = None
            return event
        return None


# ---- CSV-State (iridium_os4_cc_list.csv) ------------------------------------


def load_cc_list(path) -> tuple[list[str], list[dict]]:
    """CSV -> (fieldnames, rows); fehlende NEW_COLUMNS werden als "" ergaenzt."""
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fieldnames = list(r.fieldnames or [])
        rows = [dict(row) for row in r]
    for row in rows:
        for c in NEW_COLUMNS:
            row.setdefault(c, "")
    return fieldnames, rows


def save_cc_list(path, fieldnames: list[str], rows: list[dict], backup: bool = False) -> None:
    """CSV schreiben; NEW_COLUMNS werden an fieldnames angehaengt.

    backup=True legt vor dem Schreiben <path>.bak mit dem alten Dateiinhalt an.
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
        return -1.0  # "-" oder leer = niedrigste Prioritaet


def pending_rows(rows: list[dict], essential: bool = False, grep: str | None = None,
                 only_cc: str | None = None) -> list[dict]:
    """Noch nicht verifizierte Zeilen (os4_verified == "nein"), sortiert:
    essential=yes zuerst, dann nutzung_pct absteigend, dann cc aufsteigend."""
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
    """Events eines Fangs in die Zeile buchen; liefert den JSONL-Log-Entry.

    Gewinner-Pid = haeufigster Pid; nrpn_min/max/last und explore_msgs beziehen
    sich nur auf die Events des Gewinners. abweichung = pid_os4 != rdb-Pid.
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
    """Eine JSON-Zeile an den Explore-Log anhaengen."""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
