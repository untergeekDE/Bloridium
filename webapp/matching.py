"""Similarity / prognosis of conversion quality (Blofeld -> Iridium).

Two matchers:

- **rf-prognose** (active when a trained model is available): the numpy-only
  Random Forest from `bloridium/prognose.py`, trained on the A/B measurements in
  `recordings/sim_log.jsonl` (target=score; dataset contract:
  docs/HANDOVER-2026-11-19-rf-dataset.md). Feature vector = the 367 SNDD bytes
  (without the name bytes 363-378) / 127, computed directly from the uploaded
  SNDD – no dump file needed. Returns predicted score 0-100 plus the std over
  the individual trees (uncertainty).
- **deterministic-placeholder** (fallback when no model is found): pure
  function of the parsed parameters; same dump -> same score.

The web app does not persist or train on uploaded data; report.json only
contains the result data needed for the download.
"""

from __future__ import annotations

import os
from pathlib import Path



def _read_core_version() -> str:
    """__version__ from bloridium/version.py (repo) or core/version.py (container),
    parsed as text so the package (mido/rtmidi) is never imported."""
    import re
    env = os.environ.get("BLORIDIUM_CORE_DIR")
    for d in ([Path(env)] if env else []) + [Path(__file__).resolve().parent / "core",
                                             Path(__file__).resolve().parent.parent / "bloridium"]:
        f = d / "version.py"
        if f.exists():
            m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', f.read_text())
            if m:
                return m.group(1)
    return "0+unknown"


# One version for everything (package, conversion, similarity, matchers) - see
# bloridium/version.py. The matcher *name* tells RF prognosis from placeholder.
VERSION = _read_core_version()
SIMILARITY_VERSION = VERSION    # kept as aliases for report.json field names
PLACEHOLDER_VERSION = VERSION

WEBAPP = Path(__file__).resolve().parent
REPO = WEBAPP.parent

DEFAULT_MODEL_NAME = "prognose_rf.pkl"


def resolve_model_path(model_path=None) -> Path | None:
    """Model file to use: explicit arg > $BLORIDIUM_MODEL > repo/container defaults.

    Returns None when nothing exists (caller falls back to the placeholder).
    An explicitly set env var that does not exist is respected as None.
    """
    if model_path:
        p = Path(model_path)
        return p if p.exists() else None
    env = os.environ.get("BLORIDIUM_MODEL")
    if env:
        p = Path(env)
        return p if p.exists() else None
    for c in (REPO / "models" / DEFAULT_MODEL_NAME,
              WEBAPP / "models" / DEFAULT_MODEL_NAME,
              Path("/app/models") / DEFAULT_MODEL_NAME):  # container volume mount
        if c.exists():
            return c
    return None


def load_model_bundle(core, model_path=None):
    """Load the pickled RF bundle via core.prognose; (bundle, path) or (None, None)."""
    path = resolve_model_path(model_path)
    if path is None or not hasattr(core, "prognose"):
        return None, None
    try:
        return core.prognose.load_model(path), path
    except Exception:
        return None, None


def predict_rf(parsed: dict, core, bundle: dict) -> dict:
    """RF prognosis for one parse_sndd result: {"score": 0-100, "std": …}."""
    import numpy as np

    x = core.prognose.feature_vector(parsed).reshape(1, -1)
    rf = bundle["model"]
    tree_preds = np.array([float(t.predict(x)[0]) for t in rf.estimators_])
    pred = float(rf.predict(x)[0])
    return {"score": round(min(100.0, max(0.0, pred)), 1),
            "std": round(float(tree_preds.std()), 2),
            "model_target": bundle.get("target", "score")}


def score_sound(parsed: dict, unmapped: list[str], qm, core=None, bundle=None) -> dict:
    """Score one sound: RF prognosis when a model is available, else placeholder.

    Returns {"score", "std", "matcher", "parts", "penalties"}.
    """
    if bundle is not None and core is not None and hasattr(core, "prognose"):
        try:
            r = predict_rf(parsed, core, bundle)
            r.update({"matcher": f"rf-prognose-v{SIMILARITY_VERSION}",
                      "parts": {}, "penalties": []})
            return r
        except Exception:
            pass  # e.g. numpy missing -> fall back to the placeholder
    r = estimate_match(parsed, unmapped, qm)
    r["matcher"] = f"deterministic-placeholder-v{PLACEHOLDER_VERSION}"
    r["std"] = None
    return r


# Weights of the sub-scores (sum = 1.0) – placeholder only
WEIGHTS = {"osc": 0.30, "filter": 0.25, "fx": 0.15, "env_mod": 0.20, "arp": 0.10}

# How exactly can the Blofeld filter-1 type be represented on the Iridium?
FILTER1_EXACT = {
    "Bypass": 1.0, "LP 24dB": 1.0, "LP 12dB": 1.0, "HP 24dB": 1.0, "HP 12dB": 1.0,
    "PPG LP": 1.0,                       # -> 24dB LP (since 2026-11-21; PPG is a 24dB ladder)
    "BP 24dB": 0.5, "BP 12dB": 0.5,      # -> 24dB BP (approximation)
    "Notch24dB": 0.5, "Notch12dB": 0.5,  # -> 24dB BP (approximation)
    "Comb+": 0.5, "Comb-": 0.5,          # -> 24dB BP (approximation)
}
FX_EXACT = {
    "Bypass": 1.0, "Chorus": 1.0, "Flanger": 1.0, "Phaser": 1.0,
    "Delay": 1.0, "Clk.Delay": 1.0, "Reverb": 1.0,
    "Overdrive": 0.9,   # -> Drive
    "Triple FX": 0.6,   # -> Chorus (approximation)
}


def estimate_match(parsed: dict, unmapped: list[str], qm) -> dict:
    """Deterministic placeholder score 0-100 for a parse_sndd result.

    parsed: blofeld_dump.parse_sndd() result
    unmapped: list from qpat_map.blofeld_to_qpat_params()
    qm: the qpat_map module (for the enum tables)

    Returns: {"score": float (0..100, 1 decimal), "parts": {part: 0..1},
              "penalties": [str]}
    """
    p = parsed["params"]
    penalties: list[str] = []

    # --- oscillators: basic waveforms exact, wavetable depending on bridge ---
    osc_vals = []
    for n in (1, 2, 3):
        shape = p.get(f"Osc {n} Shape")
        if isinstance(shape, str) and shape in qm.BLOFELD_SHAPE_TO_IRIDIUM:
            osc_vals.append(1.0)
        elif isinstance(shape, str) and shape in qm.BLOFELD_WAVETABLE_TO_IRIDIUM:
            osc_vals.append(0.8)
            penalties.append(f"Osc {n} wavetable {shape!r}: approximation (known table id)")
        else:
            osc_vals.append(0.4)
            penalties.append(f"Osc {n} wavetable {shape!r}: no Iridium equivalent")
    osc = sum(osc_vals) / len(osc_vals)

    # --- filters: F1 direct, F2 via DigiFormer ---
    f1 = p.get("Filter 1 Type")
    f1v = FILTER1_EXACT.get(f1 if isinstance(f1, str) else "", 0.5)
    f2 = p.get("Filter 2 Type")
    if f2 == "Bypass":
        f2v = 1.0
    elif isinstance(f2, str) and f2 in qm.BLOFELD_FILTER2_TO_FORMER:
        f2v = 0.9
        if f2 in ("BP 24dB", "BP 12dB", "Notch24dB", "Notch12dB"):
            penalties.append(f"Filter 2 {f2!r}: approximation via DigiFormer")
    else:
        f2v = 0.5
    if isinstance(f1, str) and f1 in ("BP 24dB", "BP 12dB", "Notch24dB", "Notch12dB", "Comb+", "Comb-"):
        penalties.append(f"Filter 1 {f1!r}: approximation (24dB BP)")
    filt = 0.6 * f1v + 0.4 * f2v

    # --- FX ---
    fx_vals = []
    for n in (1, 2):
        t = p.get(f"Effect {n} Type")
        v = FX_EXACT.get(t if isinstance(t, str) else "", 0.5)
        if v < 1.0:
            penalties.append(f"Effect {n} {t!r}: approximation")
        fx_vals.append(v)
    fx = sum(fx_vals) / len(fx_vals)

    # --- env/mod/LFO: mapped, but mod destinations without Iridium pendant are lost ---
    lost = 0
    for m in range(1, 17):
        src = p.get(f"Modulation {m} Source")
        dst = p.get(f"Modulation {m} Destination")
        amt = p.get(f"Modulation {m} Amount")
        if src not in (None, "off") and isinstance(dst, str) and dst not in qm.BLOFELD_MOD_DST \
                and isinstance(amt, (int, float)) and amt != 0:
            lost += 1
            penalties.append(f"Modulation {m}: destination {dst!r} not representable on Iridium")
    env_mod = max(0.0, 1.0 - 0.02 * lost)

    # --- arp: completely unmapped ---
    arp_mode = p.get("Arpeggiator Mode", 0)
    if arp_mode in (0, "off"):
        arp = 1.0
    else:
        arp = 0.1
        penalties.append("Arpeggiator active, but not mapped")

    parts = {"osc": osc, "filter": filt, "fx": fx, "env_mod": env_mod, "arp": arp}
    score = 100.0 * sum(WEIGHTS[k] * parts[k] for k in WEIGHTS)
    score = round(max(0.0, min(100.0, score)), 1)
    return {"score": score, "parts": {k: round(v, 3) for k, v in parts.items()},
            "penalties": penalties}
