"""Deterministische Match-Schaetzung Blofeld -> Iridium (PLACEHOLDER v0).

WICHTIG: Das ist ein bewusster Platzhalter. Die echte Matching-Funktion
konstruieren wir spaeter aus den Ergebnissen der A/B-Vergleiche
(recordings/sim_log.jsonl). Die Web-App schreibt deshalb pro Sound den
Feature-Vektor (geparste Parameter, unmapped, mapped) in report.json –
das ist das spaetere Trainingsdatum.

v0.2 ist rein deterministisch: gleicher Dump -> gleicher Score. Keine
Zufallsanteile, kein Audio, keine externen Modelle.
"""

from __future__ import annotations

# Versionierung des Similarity-Tools (report.json, UI)
SIMILARITY_VERSION = "0.2"

# Gewichte der Sub-Scores (Summe = 1.0)
WEIGHTS = {"osc": 0.30, "filter": 0.25, "fx": 0.15, "env_mod": 0.20, "arp": 0.10}

# Wie exakt ist der Blofeld-Filter-1-Typ auf dem Iridium darstellbar?
FILTER1_EXACT = {
    "Bypass": 1.0, "LP 24dB": 1.0, "LP 12dB": 1.0, "HP 24dB": 1.0, "HP 12dB": 1.0,
    "PPG LP": 0.9,                       # -> 12dB LP (Navehe-rung)
    "BP 24dB": 0.5, "BP 12dB": 0.5,      # -> 24dB BP (Naeherung)
    "Notch24dB": 0.5, "Notch12dB": 0.5,  # -> 24dB BP (Naeherung)
    "Comb+": 0.5, "Comb-": 0.5,          # -> 24dB BP (Naeherung)
}
FX_EXACT = {
    "Bypass": 1.0, "Chorus": 1.0, "Flanger": 1.0, "Phaser": 1.0,
    "Delay": 1.0, "Clk.Delay": 1.0, "Reverb": 1.0,
    "Overdrive": 0.9,   # -> Drive
    "Triple FX": 0.6,   # -> Chorus (Naeherung)
}


def estimate_match(parsed: dict, unmapped: list[str], qm) -> dict:
    """Deterministischer Score 0-100 fuer ein parse_sndd-Ergebnis.

    parsed: blofeld_dump.parse_sndd()-Ergebnis
    unmapped: Liste aus qpat_map.blofeld_to_qpat_params()
    qm: das qpat_map-Modul (fuer die Enum-Tabellen)

    Rueckgabe: {"score": float (0..100, 1 Dezimalstelle),
                "parts": {teil: 0..1}, "penalties": [str]}
    """
    p = parsed["params"]
    penalties: list[str] = []

    # --- Oszillatoren: Basis-Wellenformen exakt, Wavetable je nach Bridge ---
    osc_vals = []
    for n in (1, 2, 3):
        shape = p.get(f"Osc {n} Shape")
        if isinstance(shape, str) and shape in qm.BLOFELD_SHAPE_TO_IRIDIUM:
            osc_vals.append(1.0)
        elif isinstance(shape, str) and shape in qm.BLOFELD_WAVETABLE_TO_IRIDIUM:
            osc_vals.append(0.8)
            penalties.append(f"Osc {n} Wavetable {shape!r}: nur Naeherung (bekannte Table-ID)")
        else:
            osc_vals.append(0.4)
            penalties.append(f"Osc {n} Wavetable {shape!r}: kein Iridium-Aequivalent")
    osc = sum(osc_vals) / len(osc_vals)

    # --- Filter: F1 direkt, F2 ueber DigiFormer ---
    f1 = p.get("Filter 1 Type")
    f1v = FILTER1_EXACT.get(f1 if isinstance(f1, str) else "", 0.5)
    f2 = p.get("Filter 2 Type")
    if f2 == "Bypass":
        f2v = 1.0
    elif isinstance(f2, str) and f2 in qm.BLOFELD_FILTER2_TO_FORMER:
        f2v = 0.9
        if f2 in ("BP 24dB", "BP 12dB", "Notch24dB", "Notch12dB"):
            penalties.append(f"Filter 2 {f2!r}: Naeherung ueber DigiFormer")
    else:
        f2v = 0.5
    if isinstance(f1, str) and f1 in ("BP 24dB", "BP 12dB", "Notch24dB", "Notch12dB", "Comb+", "Comb-"):
        penalties.append(f"Filter 1 {f1!r}: Naeherung (24dB BP)")
    filt = 0.6 * f1v + 0.4 * f2v

    # --- FX ---
    fx_vals = []
    for n in (1, 2):
        t = p.get(f"Effect {n} Type")
        v = FX_EXACT.get(t if isinstance(t, str) else "", 0.5)
        if v < 1.0:
            penalties.append(f"Effect {n} {t!r}: Naeherung")
        fx_vals.append(v)
    fx = sum(fx_vals) / len(fx_vals)

    # --- Env/Mod/LFO: gemappt, aber Mod-Dests ohne Iridium-Pendant fallen weg ---
    lost = 0
    for m in range(1, 17):
        src = p.get(f"Modulation {m} Source")
        dst = p.get(f"Modulation {m} Destination")
        amt = p.get(f"Modulation {m} Amount")
        if src not in (None, "off") and isinstance(dst, str) and dst not in qm.BLOFELD_MOD_DST \
                and isinstance(amt, (int, float)) and amt != 0:
            lost += 1
            penalties.append(f"Modulation {m}: Ziel {dst!r} nicht auf Iridium abbildbar")
    env_mod = max(0.0, 1.0 - 0.02 * lost)

    # --- Arp: komplett unmapped ---
    arp_mode = p.get("Arpeggiator Mode", 0)
    if arp_mode in (0, "off"):
        arp = 1.0
    else:
        arp = 0.1
        penalties.append("Arpeggiator aktiv, aber nicht gemappt")

    parts = {"osc": osc, "filter": filt, "fx": fx, "env_mod": env_mod, "arp": arp}
    score = 100.0 * sum(WEIGHTS[k] * parts[k] for k in WEIGHTS)
    score = round(max(0.0, min(100.0, score)), 1)
    return {"score": score, "parts": {k: round(v, 3) for k, v in parts.items()},
            "penalties": penalties}
