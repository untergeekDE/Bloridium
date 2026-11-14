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
    # Blofeld F1 Keytrack raw 0..127 = -200%..+196% (64 = 0%, Offset-Binaer);
    # Iridium Filter1Keytrack norm 0..1 = -200%..+200% (0.5 = 0%) -> norm(raw).
    # Anker Don-Solaris: raw 64 -> 0.5000, raw 96 -> 0.7500. A043 hat raw 96.
    assert overrides["Filter1Keytrack"][0] == pytest.approx(96 / 127)


def test_filter_keytrack_neutral_64_maps_to_half():
    # A019 Tines DocT: F1 Keytrack 64 (0%) darf NICHT -200% (norm 0) werden
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A019_20261108_233101.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter1Keytrack"][0] == pytest.approx(64 / 127)
    assert ov["Filter2Keytrack"][0] == pytest.approx(64 / 127)


def test_a019_wavetable_mapped():
    # A019: Osc1 Shape = MalletSyn -> Iridium Wavetable (Type 0), Table 2 "Mallet Syn",
    # Position aus Pulsewidth (Blofeld "PW/Wave"), Mod-Slot auf WT1 Position (Dst 11)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A019_20261108_233101.bin"))
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1Type"] == (0.0, "Wavetable")
    assert ov["Osc1WavetableTable"][0] == 2.0
    assert ov["Osc1WavetablePosition"][0] == pytest.approx(14 / 127)   # Osc1 Pulsewidth = 14
    assert "Osc1WavetableBrilliance" in ov
    assert "Osc1WaveformPW" not in ov
    dst_vals = [ov[k][0] for k in ov if k.startswith("MatrixDst")]
    assert 11.0 in dst_vals   # WT1 Position (Mod-Slots 1 und 5: Env3/PitchBend -> O1 PW/Wave)
    assert not any("Wavetable" in u and "kein" in u for u in unmapped)


def test_filter_types_v14_values(overrides):
    # SH Power: F1 = LP 24dB -> Filter12Type 3.0 (v14!); F2 = Bypass -> Former Bypass
    assert overrides["Filter12Type"] == (3.0, "24dB LP")
    assert overrides["FilterState"] == (0.0, "Active")
    # F2 Bypass -> Filter2State 'Off' (2.0): 'Bypass' allein leaked Dry am F1 vorbei
    # (Beleg: dumps/00202-SH Power.qpat, v15 Filter2State=2.0 'Off')
    assert overrides["Filter2State"] == (2.0, "Off")
    # F2 sitzt hinter dem Filter als DigiFormer: Bypass -> Type 0.0, Amount 0
    assert overrides["DigiFormerType"] == (0.0, "Bypass")
    assert overrides["DigiFormerAmount"][0] == 0.0
    # F2 Bypass -> FilterLink 'Single' (zusammen mit Filter2State 'Off': kein Dry-Leak)
    assert overrides["FilterLink"] == (0.0, "Single")


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


def test_amp_velocity_maps_to_velocity_volume_slot(overrides):
    # Blofeld Amplifier Velocity 64 (unipolar): AmpVeloAmount = norm(64) = 0.5039.
    # Matrix-Amount ist bipolar um 0.5 zentriert -> 0.5 + 0.5*norm = 0.752
    # (0.5 waere neutral/wirkungslos! Bipolar-Falle 2026-11-09)
    assert overrides["AmpVeloAmount"][0] == pytest.approx(64 / 127)
    assert overrides["MatrixSrc8"][0] == 32.0    # Velocity (v14)
    assert overrides["MatrixDst8"][0] == 112.0   # Volume (v14)
    assert overrides["MatrixAmount8"][0] == pytest.approx(0.5 + 0.5 * 64 / 127)
    assert overrides["MatrixOnOff8"][0] == 1.0


def test_glide_rate_calibrated_not_linear():
    # Anker: Blofeld raw 20 <-> Iridium norm 0.15 (Don-Solaris-Paare / Iridium-Default 0.045 s)
    assert qpat_map.glide_rate_norm(20) == pytest.approx(0.15, abs=1e-9)
    # A073 Chord Hose: raw 48 -> ~0.30. Lineares norm() waere 0.378 -> "0.29 s" am Geraet (zu hoch)
    assert qpat_map.glide_rate_norm(48) == pytest.approx(0.30, abs=0.01)
    assert qpat_map.glide_rate_norm(48) < 48 / 127
    # monoton steigend und geclampt
    vals = [qpat_map.glide_rate_norm(v) for v in range(0, 128)]
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert all(b >= a for a, b in zip(vals, vals[1:]))


def test_a073_glide_rate_in_overrides():
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A073_20261108_233117.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["GlideOnOff"] == (1.0, "On")
    assert ov["GlideRate"][0] == pytest.approx(0.30, abs=0.01)


def test_lfo_sync_mapped_with_template_keys():
    # A022 ModWheelOrgDrive: LFO1 Sync=1 raw 42 (72 bars), LFO2 Sync=1 raw 14 (512 bars),
    # LFO3 Sync=0 raw 30. Falsch war "LFO1Speed" (Key existiert nicht im Template; Device
    # lief auf Default 0.5 -> Tremolo) und Clock-Index als free Speed.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A022_20261108_233105.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert "LFO1Speed" not in ov and "Lfo1Speed" in ov
    assert ov["Lfo1Sync"] == (1.0, "On")
    assert ov["Lfo2Sync"] == (1.0, "On")
    assert ov["Lfo3Sync"] == (0.0, "Off")
    # 512 bars = 2048 beats -> groesster verfuegbarer Ratio (Index 0 = 1024)
    assert ov["Lfo2SyncRatio"][0] == 0.0
    # 72 bars = 288 beats -> naechster Index ~4 (256 beats)
    assert ov["Lfo1SyncRatio"][0] in (3.0, 4.0)
    assert ov["Lfo3Speed"][0] == pytest.approx(30 / 127)
    # Ringmod-Key heisst im Template RingModOsc1ToOsc2
    assert "RingModOsc1ToOsc2" in ov


def test_converted_file_is_version_14(parsed, tmp_path):
    out_path, mapped, unmapped = workflow.convert_parsed(parsed, "A043", tmp_path, REPO / TEMPLATE)
    q = qpat.load(out_path)
    assert q["version"] == qpat.PRESET_VERSION == 14
    assert q["params"]["Osc1Destination"]["value"] == 2.0
    assert q["params"]["MatrixDst1"]["value"] == 1.0
