"""CC-Tabellen aus docs/midi-maps/*.csv (midi.guide) laden + Parameternamen aufloesen.

Nur CCs sind am Geraet wirksam – eingehende NRPN werden ignoriert
(siehe OS3-Handbuch / docs/FINDINGS.md), daher liefern NRPN-only-Parameter
( z. B. Iridium 'Filter1 Cutoff') einen Fehler.
"""

from __future__ import annotations

import csv


def load_cc_map(path) -> list[dict]:
    """CSV -> Liste der Zeilen-Dicts (csv.DictReader)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
