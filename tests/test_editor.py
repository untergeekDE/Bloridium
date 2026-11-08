"""Task 4: qpat editor – Roundtrip ueber alle export-001-Presets, set/save/.bak, diff, list."""

import shutil
from pathlib import Path

import pytest

from bloridium import qpat

EXPORT_001 = sorted((qpat.Path(__file__).resolve().parent.parent / "dumps" / "export-001").glob("*.qpat"))
TEMPLATE = qpat.Path(__file__).resolve().parent.parent / "docs" / "refs" / "qpat" / "template_waveform.qpat"

assert len(EXPORT_001) == 41, f"erwarte 41 export-001-Presets, gefunden: {len(EXPORT_001)}"


def _params_tuples(parsed):
    return {k: (v["value"], v["display"]) for k, v in parsed["params"].items()}


@pytest.mark.parametrize("path", EXPORT_001, ids=lambda p: p.name)
def test_qpat_roundtrip_params_identical(path):
    from bloridium import editor

    parsed = qpat.load(path)
    rebuilt = qpat.build_qpat(
        parsed["name"], _params_tuples(parsed), creator=parsed["creator"],
        description=parsed["description"], categories=parsed["categories"],
        version=parsed["version"], sample_maps=parsed["sample_maps"])
    again = qpat.parse_qpat(rebuilt)
    assert again["params"] == parsed["params"]
    assert again["name"] == parsed["name"]


def test_set_param_clamps_and_save_writes_bak(tmp_path):
    from bloridium import editor

    target = tmp_path / "tmpl.qpat"
    shutil.copy(TEMPLATE, target)
    parsed = qpat.load(target)
    old_val, _old_disp = editor.show_param(parsed, "Osc1Type")

    editor.set_param(parsed, "Osc1Type", 1.0, display="Waveform")
    editor.set_param(parsed, "Filter1CutOff", 5.0)  # clamp auf 1.0
    out = editor.save(parsed, target)

    assert out == target
    assert Path(str(target) + ".bak").exists()
    bak = qpat.load(str(target) + ".bak")
    assert bak["params"]["Osc1Type"]["value"] == old_val  # Backup = alter Stand
    reloaded = qpat.load(target)
    assert reloaded["params"]["Osc1Type"]["value"] == 1.0
    assert reloaded["params"]["Osc1Type"]["display"] == "Waveform"
    assert reloaded["params"]["Filter1CutOff"]["value"] == 1.0


def test_show_param_unknown_key_raises():
    from bloridium import editor

    parsed = qpat.load(TEMPLATE)
    with pytest.raises(KeyError):
        editor.show_param(parsed, "NoSuchKey123")


def test_diff_params_finds_only_changes(tmp_path):
    from bloridium import editor

    a = qpat.load(TEMPLATE)
    b = qpat.load(TEMPLATE)
    old, _ = editor.show_param(b, "Osc1Type")
    new = 0.0 if old == 1.0 else 1.0  # Zielwert != alter Wert (Template ist evtl. schon 1.0)
    editor.set_param(b, "Osc1Type", new, display="Waveform")
    diff = editor.diff_params(a, b)
    keys = [d[0] for d in diff]
    assert keys == ["Osc1Type"]
    key, va, vb, da, db_ = diff[0]
    assert vb == new and va == old


def test_list_params_grep_filters_case_insensitive():
    from bloridium import editor

    parsed = qpat.load(TEMPLATE)
    rows = editor.list_params(parsed, grep="OSC1")
    assert rows and all("osc1" in r[0].lower() for r in rows)
    assert len(editor.list_params(parsed)) > len(rows)
