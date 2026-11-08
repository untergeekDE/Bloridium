"""Mapping-Erweiterung: Routing (Osc->Fil 100, Filter>Former), Version 14,
Filter-Keytrack, Mod-Matrix (Blofeld Mod-Slots -> Iridium Matrix-Slots).
Enum-Werte aus dumps/export-001 (eigene OS4-Exporte, qpat v14)."""

import pytest

from bloridium import blofeld_dump as bd, qpat, qpat_map, workflow

DUMP = "dumps/blofeld_sndd_A043_20261108_135516.bin"
TEMPLATE = "docs/refs/qpat/template_waveform.qpat"


REPO = __import__("pathlib").Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def parsed():
    return bd.parse_sndd(workflow.load_sndd_file(REPO / DUMP))


@pytest.fixture(scope="module")
def overrides(parsed):
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    return ov


def test_osc_destinations_go_to_filter(overrides):
    for n in (1, 2, 3):
        assert overrides[f"Osc{n}Destination"] == (2.0, "DF 0 Fil 100")


def test_filter_former_routing_linear(overrides):
    assert overrides["FilterFormerRouting"] == (1.0, "Filter > Former")


def test_filter_keytrack_bipolar(overrides):
    # Blofeld F1 Keytrack 96 (64 = Mitte) -> (96-64)/64 = 0.5
    assert overrides["Filter1Keytrack"][0] == pytest.approx(0.5)


def test_filter_types_v14_values(overrides):
    # SH Power: F1 = LP 24dB -> Filter12Type 3.0 (v14!); F2 = Bypass -> Former Bypass
    assert overrides["Filter12Type"] == (3.0, "24dB LP")
    assert overrides["FilterState"] == (0.0, "Active")
    assert overrides["Filter2State"] == (1.0, "Bypass")
    # F2 sitzt hinter dem Filter als DigiFormer: Bypass -> Type 0.0, Amount 0
    assert overrides["DigiFormerType"] == (0.0, "Bypass")
    assert overrides["DigiFormerAmount"][0] == 0.0


def test_mod_matrix_slots_mapped(overrides):
    # SH Power Mod-Slots: 1: LFO2*Press->Pitch 84, 2: Pressure->O2 Pitch 43,
    # 3: MW->FE Sustain 17, 4: MW->FE Decay 102, 5: Vel->F1 Cutoff 115, 6: Vel->F1 Reso 95
    # Amounts bipolar um 0.5 zentriert: irr = 0.5 + (blo-64)/254
    exp = {
        1: (16.0, 1.0, 0.5 + (84 - 64) / 254),    # AfterTouch -> Pitch
        2: (16.0, 3.0, 0.5 + (43 - 64) / 254),    # AfterTouch -> Osc2 Pitch
        3: (14.0, 114.0, 0.5 + (17 - 64) / 254),  # Wheel -> Filt1Env Sustain
        4: (14.0, 123.0, 0.5 + (102 - 64) / 254), # Wheel -> Filt1Env Decay
        5: (32.0, 100.0, 0.5 + (115 - 64) / 254), # Velocity -> Filter1 Cutoff
        6: (32.0, 101.0, 0.5 + (95 - 64) / 254),  # Velocity -> Filter1 Reso
    }
    for slot, (src, dst, amt) in exp.items():
        assert overrides[f"MatrixSrc{slot}"][0] == src, f"slot {slot} src"
        assert overrides[f"MatrixDst{slot}"][0] == dst, f"slot {slot} dst"
        assert overrides[f"MatrixAmount{slot}"][0] == pytest.approx(amt), f"slot {slot} amt"
        assert overrides[f"MatrixOnOff{slot}"][0] == 1.0


def test_filter_direct_mod_source_mapped_to_extra_matrix_slot(overrides):
    # Blofeld "Filter 1 Mod Source = Mod Wheel, Mod Amount = 111" -> naechster freier Slot (7) -> Filter1 Cutoff
    assert overrides["MatrixSrc7"][0] == 14.0
    assert overrides["MatrixDst7"][0] == 100.0
    assert overrides["MatrixAmount7"][0] == pytest.approx(0.5 + (111 - 64) / 254)


def test_converted_file_is_version_14(parsed, tmp_path):
    out_path, mapped, unmapped = workflow.convert_parsed(parsed, "A043", tmp_path, REPO / TEMPLATE)
    q = qpat.load(out_path)
    assert q["version"] == qpat.PRESET_VERSION == 14
    assert q["params"]["Osc1Destination"]["value"] == 2.0
    assert q["params"]["MatrixDst1"]["value"] == 1.0
