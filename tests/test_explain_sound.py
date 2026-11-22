"""The explainer (A: converter gaps, B: spectral notes) stays factual."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import explain_sound as X  # noqa: E402

from bloridium import blofeld_dump as bd, workflow  # noqa: E402


def parsed(loc: str) -> dict:
    return bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/banks/A" / f"{loc}.bin"))


def test_a020_hides_inactive_arp_and_ranks_fx_first():
    p = parsed("A020")
    gaps, _ignored = X.unmapped_items(p)
    titles = [g["title"] for g in gaps]
    assert not any(t.startswith("Arpeggiator") for t in titles)  # arp is off
    assert any("Chorus" in t for t in titles)                    # FX is active
    approx = X.approximations(p)
    assert any("DigiFormer" in a["title"] for a in approx)       # serial F2
    recs = sorted(gaps + approx, key=lambda x: -x["weight"])
    assert all(recs[i]["weight"] >= recs[i + 1]["weight"] for i in range(len(recs) - 1))
    assert recs[0]["weight"] >= 80


def test_a001_skips_neutral_values():
    p = parsed("A001")
    gaps, _ignored = X.unmapped_items(p)
    # Brilliance raw 0 and Limit WT 0 must not show up as "check first"
    assert not any("Brilliance" in g["title"] for g in gaps)
    assert not any("Limit WT" in g["title"] for g in gaps)


def test_json_cli_contract():
    out = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "explain_sound.py"), "A020", "--json"],
        capture_output=True, text=True, cwd=REPO)
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["loc"] == "A020"
    assert data["check_first"]
    assert "prediction" in data
