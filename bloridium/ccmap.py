"""Load CC tables from docs/midi-maps/*.csv (midi.guide) + resolve parameter names.

Only CCs are effective on the device - incoming NRPN is ignored
(see OS3 manual / docs/FINDINGS.md), so NRPN-only parameters
(e.g. Iridium 'Filter1 Cutoff') yield an error.
"""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PID_MAP = REPO / "docs" / "midi-maps" / "iridium_pid_map.csv"
DEFAULT_GUIDE = REPO / "docs" / "midi-maps" / "iridium_midi_guide.csv"


def load_cc_map(path) -> list[dict]:
    """CSV -> list of row dicts (csv.DictReader)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_pid_map(path=DEFAULT_PID_MAP) -> dict:
    """iridium_pid_map.csv -> {name_lower: (cc, pid|None)}.

    Pid is the device-internal parameter ID (rdb map 2023); on OS4 the
    pids differ (NRPN capture 2026-11-09: 1024/1027/1045/1046/1055) - the CC still
    controls it as long as a matching .mimap is loaded.
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
    """Name -> (cc, pid|None). Pid map first (exact, else unique substring),
    fallback to midi.guide (name-only, pid=None)."""
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
    try:
        table = load_cc_map(guide_path)
    except OSError as e:
        raise KeyError(f"no CC map found (pid map and guide missing: {e})") from e
    cc, _pname = find_cc(name, table)
    return cc, None


def find_cc(name: str, table: list[dict]) -> tuple[int, str]:
    """Name -> (cc_number, parameter_name).

    Exact match (case-insensitive) wins, else unique substring.
    KeyError on unknown / NRPN-only; ValueError on ambiguous (with list).
    """
    n = name.strip().lower()
    exact = [r for r in table if r["parameter_name"].strip().lower() == n]
    if exact:
        r = exact[0]
        if not r.get("cc_msb"):
            raise KeyError(
                f"no CC for {r['parameter_name']!r} - NRPN is ignored on the device "
                f"(only .qpat re-import or MIDI Learn on the device)")
        return int(r["cc_msb"]), r["parameter_name"]
    matches = [r for r in table if r.get("cc_msb") and n in r["parameter_name"].lower()]
    if len(matches) == 1:
        return int(matches[0]["cc_msb"]), matches[0]["parameter_name"]
    if len(matches) > 1:
        raise ValueError("ambiguous: " + ", ".join(
            f"{r['parameter_name']} (CC{int(r['cc_msb'])})" for r in matches))
    raise KeyError(f"unknown parameter: {name!r} (see 'bloridium cc --list')")
