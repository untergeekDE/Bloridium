"""CC-Tabellen aus docs/midi-maps/*.csv (midi.guide) laden + Parameternamen aufloesen.

Nur CCs sind am Geraet wirksam – eingehende NRPN werden ignoriert
(siehe OS3-Handbuch / docs/FINDINGS.md), daher liefern NRPN-only-Parameter
( z. B. Iridium 'Filter1 Cutoff') einen Fehler.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PID_MAP = REPO / "docs" / "midi-maps" / "iridium_pid_map.csv"
DEFAULT_GUIDE = REPO / "docs" / "midi-maps" / "iridium_midi_guide.csv"


def load_cc_map(path) -> list[dict]:
    """CSV -> Liste der Zeilen-Dicts (csv.DictReader)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_pid_map(path=DEFAULT_PID_MAP) -> dict:
    """iridium_pid_map.csv -> {name_lower: (cc, pid|None)}.

    Pid ist die Geraete-interne Parameter-ID (rdb-Map 2023); auf OS4 weichen die
    Pids ab (NRPN-Mitschnitt 2026-11-09: 1024/1027/1045/1046/1055) – das CC steuert
    unabhaengig davon, solange eine passende .mimap geladen ist.
    """
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name = (r.get("parameter_name") or "").strip().lower()
            cc = (r.get("cc") or "").strip()
            pid = (r.get("pid_rdb_2023") or "").strip()
            if name and cc:
                out[name] = (int(cc), int(pid) if pid else None)
    return out


def cc_for(name: str, pid_map_path=DEFAULT_PID_MAP, guide_path=DEFAULT_GUIDE) -> tuple[int, int | None]:
    """Name -> (cc, pid|None). Pid-Map zuerst (exakt, sonst eindeutiger Substring),
    Fallback auf midi.guide (name-only, pid=None)."""
    n = name.strip().lower()
    try:
        m = load_pid_map(pid_map_path)
    except OSError:
        m = {}
    if n in m:
        return m[n]
    hits = [v for k, v in m.items() if n in k]
    if len(hits) == 1:
        return hits[0]
    cc, _pname = find_cc(name, load_cc_map(guide_path))
    return cc, None


def find_cc(name: str, table: list[dict]) -> tuple[int, str]:
    """Name -> (cc_nummer, parameter_name).

    Exakter Match (case-insensitive) gewinnt, sonst eindeutiger Substring.
    KeyError bei unbekannt / NRPN-only; ValueError bei mehrdeutig (mit Liste).
    """
    n = name.strip().lower()
    exact = [r for r in table if r["parameter_name"].strip().lower() == n]
    if exact:
        r = exact[0]
        if not r.get("cc_msb"):
            raise KeyError(
                f"kein CC fuer {r['parameter_name']!r} – NRPN wird am Geraet ignoriert "
                f"(nur qpat-Re-Import oder MIDI Learn am Geraet)")
        return int(r["cc_msb"]), r["parameter_name"]
    matches = [r for r in table if r.get("cc_msb") and n in r["parameter_name"].lower()]
    if len(matches) == 1:
        return int(matches[0]["cc_msb"]), matches[0]["parameter_name"]
    if len(matches) > 1:
        raise ValueError("mehrdeutig: " + ", ".join(
            f"{r['parameter_name']} (CC{int(r['cc_msb'])})" for r in matches))
    raise KeyError(f"unbekannter Parameter: {name!r} (siehe 'bloridium cc --list')")
