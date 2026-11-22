"""Mapping extension: routing (Osc->Fil 100; serial 'Filter > Former' with F2 in the
DigiFormer, parallel 'Parallel' with F2 as filter 2), version 14,
filter keytrack, mod matrix (Blofeld mod slots -> Iridium matrix slots).
Enum values from dumps/export-001 (own OS4 exports, qpat v14)."""

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


def test_osc_destinations_follow_balance(parsed, overrides):
    # 2026-11-21: 'Mixer Osc N Balance' (F1/F2 share, 0=F1, 127=F2) maps to
    # OscNDestination (2 = all filter/F1 ... 22 = all DigiFormer/F2).
    for n in (1, 2, 3):
        bal = parsed["params"][f"Mixer Osc {n} Balance"]
        assert overrides[f"Osc{n}Destination"][0] == pytest.approx(
            qpat_map.osc_destination(bal))


def test_balance_maps_to_destination_not_pan():
    # serial (A001): F2 = Former -> destination split
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A001"]))
    parsed["params"]["Mixer Osc 1 Balance"] = 127
    ov, _un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1Destination"][0] == pytest.approx(22.0)   # all F2 / DigiFormer
    assert ov["Osc1Pan"][0] == pytest.approx(0.5)            # still no stereo pan
    # parallel (A043): both filters real -> destination stays, global levels split
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A043"]))
    for n in (1, 2, 3):
        parsed["params"][f"Mixer Osc {n} Balance"] = 127
    ov, _un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1Destination"][0] == pytest.approx(2.0)
    assert ov["FilterLevel"][0] == pytest.approx(0.0)
    assert ov["Filter2Level"][0] == pytest.approx(1.0)


def test_osc_pan_always_center_balance_is_not_pan():
    # Finding 2026-11-15 (user, stereo image): Blofeld 'Mixer Osc N Balance' is the
    # F1/F2 share (MAPPING-MASTER, warning), NOT a stereo pan. Pan stays center;
    # the balance goes to OscNDestination (2026-11-21).
    for loc, dump in DUMPS_9.items():
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / dump))
        ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
        serial = parsed["params"]["Filter Routing"] == 1
        for n in (1, 2, 3):
            assert ov[f"Osc{n}Pan"][0] == pytest.approx(0.5), f"{loc} Osc{n}Pan"
            if serial:
                assert ov[f"Osc{n}Destination"][0] == pytest.approx(
                    qpat_map.osc_destination(parsed["params"][f"Mixer Osc {n} Balance"]))
            else:
                assert ov[f"Osc{n}Destination"][0] == pytest.approx(2.0)
        bals = [parsed["params"][f"Mixer Osc {n} Balance"] for n in (1, 2, 3)]
        uniform = max(bals) - min(bals) <= 4
        if uniform:
            assert not any("Per-Osc F1/F2" in u for u in unmapped), loc


def test_osc_octave_sign_a001():
    # A001 JMX jun: Osc 3 Octave raw 52 = -12 semi (16') -> CoarsePitch 24-12 = 12.0,
    # NOT 24+12 = 36.0 (sign bug 2026-11-14: 64-raw instead of raw-64).
    # Osc 1/2 Octave raw 64 (8') -> 24.0.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    assert parsed["params"]["Osc 3 Octave"] == 52
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1CoarsePitch"][0] == pytest.approx(24.0)
    assert ov["Osc2CoarsePitch"][0] == pytest.approx(24.0)
    assert ov["Osc3CoarsePitch"][0] == pytest.approx(12.0)


def test_waveform_pw_neutral_for_non_pulse_a001():
    # A001: Osc1/2 Shape 'Saw', Pulsewidth raw 100 - Blofeld: PW has no function on saw.
    # Iridium WaveformPW is Warp (also affects saw) -> must be neutral 0.5,
    # not norm(100)=0.7874 (square wave instead of sawtooth, finding 2026-11-14).
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    assert parsed["params"]["Osc 1 Shape"] == "Saw"
    assert parsed["params"]["Osc 1 Pulsewidth"] == 100
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1WaveformPW"][0] == pytest.approx(0.5)
    assert ov["Osc2WaveformPW"][0] == pytest.approx(0.5)


def test_waveform_pw_pulse_shape_scales_half():
    # Blofeld Shape 'Pulse': raw 127 = 50% pulse width -> Iridium PW 0.5; raw 64 -> norm*0.5
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    parsed["params"]["Osc 1 Shape"] = "Pulse"
    parsed["params"]["Osc 1 Pulsewidth"] = 127
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1WaveformPW"][0] == pytest.approx(0.5)
    parsed["params"]["Osc 1 Pulsewidth"] = 64
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1WaveformPW"][0] == pytest.approx(64 / 127 * 0.5)


def test_cutoff_semitone_anchor_not_linear_norm():
    # Blofeld manual: Cutoff raw 64 = 440 Hz (semitone steps). Iridium calibration:
    # norm = (log10(440) - 0.9117)/3.387 = 0.5112 -- NOT norm(64) = 0.5039 (finding 2026-11-14)
    import math
    from bloridium.qpat_map import blofeld_cutoff_norm
    assert blofeld_cutoff_norm(64) == pytest.approx((math.log10(440.0) - 0.9117) / 3.387, abs=1e-4)
    assert blofeld_cutoff_norm(64) == pytest.approx(0.5112, abs=0.001)
    assert blofeld_cutoff_norm(64) != pytest.approx(64 / 127)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter1CutOff"][0] == pytest.approx(blofeld_cutoff_norm(64))
    assert ov["DigiFormerAmount"][0] == pytest.approx(blofeld_cutoff_norm(52))
    # serial (A001 Routing=1): additional matrix slot Filter1 Env -> DF Amount,
    # otherwise the former stays statically closed (finding 2026-11-14: -66 dBFS)
    df_slots = [k for k, v in ov.items() if k.startswith("MatrixDst") and v[1] == "DF Amount"]
    assert df_slots, "serial needs Filter1 Env -> DF Amount slot"


def test_cutoff_parallel_has_no_df_env_slot(overrides):
    # A043 parallel: F2 stays Filter2 (Active) -> no DF env slot needed
    assert not [k for k, v in overrides.items()
                if k.startswith("MatrixDst") and v[1] == "DF Amount"]


def test_waveform_kernels_off_a001():
    # "Kernels Count" (OS4 display for OscNWaveformDesity): Blofeld has no kernel
    # parameter -> 0.0 = 1 wave. Template default 0.22 showed A001 OSC2 as "Kernels 2.5".
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    for n in (1, 2, 3):
        assert ov[f"Osc{n}WaveformDesity"][0] == pytest.approx(0.0)


def test_filter_former_routing_parallel_a043(overrides):
    # A043 SH Power: Blofeld Filter Routing = 0 (parallel) -> Iridium 'Parallel' (2.0),
    # NOT 'Filter > Former' (finding HANDOVER 2026-11-14)
    assert overrides["FilterFormerRouting"] == (2.0, "Parallel")


def test_serial_routing_f2_to_former_link_single():
    # A008 Easy Piano: Filter Routing = 1 (serial), F2 = LP 24dB -> DigiFormer 'Nave LP24',
    # Filter2State 'Off', FilterLink 'Single' - 'Linked' (7.0) made B silent (HANDOVER 2026-11-14)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A008_20261108_233053.bin"))
    assert parsed["params"]["Filter Routing"] == 1
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FilterFormerRouting"] == (1.0, "Filter > Former")
    assert ov["DigiFormerType"] == (7.0, "Nave LP24")
    assert ov["Filter2State"] == (2.0, "Off")
    assert ov["FilterLink"] == (0.0, "Single")
    assert ov["FilterLink"][0] != 7.0  # not 'Linked'


def test_parallel_routing_f2_stays_filter2_active():
    # A010 Wurly Piano: Filter Routing = 0 (parallel), F2 = LP 24dB (not Bypass)
    # -> F2 stays filter 2 'Active', former = Bypass, routing 'Parallel'.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A010_20261108_233057.bin"))
    assert parsed["params"]["Filter Routing"] == 0
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FilterFormerRouting"] == (2.0, "Parallel")
    assert ov["DigiFormerType"] == (0.0, "Bypass")
    assert ov["DigiFormerAmount"][0] == 0.0
    assert ov["Filter2State"] == (0.0, "Active")
    # Parallel needs Independent; the v8 template default is Boost (1.0), which
    # ignores Cutoff 2 / Resonance 2 and would make F2 inaudible.
    assert ov["FilterLink"] == (6.0, "Independent")
    # Both dual filters now have their own type parameter (v14 target); the old
    # mapping only set Filter12Type for F1, so F2 fell back to 12dB LP.
    assert ov["Filter2Type"] == (3.0, "24dB LP")
    # F2-Cutoff/Reso land on the filter2 stage (stays active)
    assert "Filter2CutOff" in ov and "Filter2Reso" in ov


def test_resonance_self_oscillation_calibration():
    # Blofeld self-oscillates above resonance raw 113 (manual); the Iridium starts
    # at 100 %. Map raw 113 -> 1.0 instead of norm(113)=0.89 so both reach
    # self-oscillation in the same region. Raw 64 stays proportional.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A010_20261108_233057.bin"))
    parsed["params"]["Filter 1 Resonance"] = 64
    parsed["params"]["Filter 2 Resonance"] = 113
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter1Reso"][0] == pytest.approx(64 / 113)
    assert ov["Filter2Reso"][0] == pytest.approx(1.0)
    # beyond the self-oscillation point stays at full resonance
    parsed["params"]["Filter 2 Resonance"] = 127
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter2Reso"][0] == pytest.approx(1.0)


def test_filter_keytrack_bipolar(overrides):
    # Blofeld F1 Keytrack raw 0..127 = -200%..+196% (64 = 0%, offset binary);
    # Iridium Filter1Keytrack norm 0..1 = -200%..+200% (0.5 = 0%) -> norm(raw).
    # Anchor Don-Solaris: raw 64 -> 0.5000, raw 96 -> 0.7500. A043 has raw 96.
    assert overrides["Filter1Keytrack"][0] == pytest.approx(96 / 127)


def test_filter_keytrack_neutral_64_maps_to_half():
    # A019 Tines DocT: F1 Keytrack 64 (0%) must NOT become -200% (norm 0)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A019_20261108_233101.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter1Keytrack"][0] == pytest.approx(64 / 127)
    assert ov["Filter2Keytrack"][0] == pytest.approx(64 / 127)


def test_a019_wavetable_mapped():
    # A019: Osc1 Shape = MalletSyn -> Iridium Wavetable (Type 0), Table 2 "Mallet Syn",
    # position from pulsewidth (Blofeld "PW/Wave"), mod slot to WT1 Position (Dst 11)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A019_20261108_233101.bin"))
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1Type"] == (0.0, "Wavetable")
    assert ov["Osc1WavetableTable"][0] == 2.0
    assert ov["Osc1WavetablePosition"][0] == pytest.approx(14 / 127)   # Osc1 Pulsewidth = 14
    assert "Osc1WavetableBrilliance" in ov
    assert "Osc1WaveformPW" not in ov
    dst_vals = [ov[k][0] for k in ov if k.startswith("MatrixDst")]
    assert 11.0 in dst_vals   # WT1 Position (mod slots 1 and 5: Env3/PitchBend -> O1 PW/Wave)
    assert not any("Wavetable" in u and "no Iridium equivalent" in u for u in unmapped)


def test_filter_types_v14_values(overrides):
    # SH Power: F1 = LP 24dB -> Filter12Type 3.0 (v14!); F2 = Bypass -> Former Bypass
    # A043/SH Power drives filter 1 -> saturating 24 dB LP (2026-11-22)
    assert overrides["Filter12Type"] == (4.0, "24dB sat. LP")
    assert overrides["FilterState"] == (0.0, "Active")
    # F2 Bypass -> Filter2State 'Off' (2.0): 'Bypass' alone leaked dry past F1
    # (evidence: dumps/00202-SH Power.qpat, v15 Filter2State=2.0 'Off')
    assert overrides["Filter2State"] == (2.0, "Off")
    # F2 sits behind the filter as DigiFormer: Bypass -> Type 0.0, Amount 0
    assert overrides["DigiFormerType"] == (0.0, "Bypass")
    assert overrides["DigiFormerAmount"][0] == 0.0
    # F2 Bypass -> FilterLink 'Single' (together with Filter2State 'Off': no dry leak)
    assert overrides["FilterLink"] == (0.0, "Single")


def test_mod_matrix_slots_mapped(overrides):
    # SH Power Mod-Slots: 1: LFO2*Press->Pitch 84, 2: Pressure->O2 Pitch 43,
    # 3: MW->FE Sustain 17, 4: MW->FE Decay 102, 5: Vel->F1 Cutoff 115, 6: Vel->F1 Reso 95
    # amounts bipolar centered around 0.5: irr = 0.5 + (blo-64)/254
    exp = {
        # slot 1: LFO2*Press -> Pitch is now Src=LFO 2 + Ctrl=AfterTouch (2026-11-21)
        1: (8.0, 1.0, 0.5 + (84 - 64) / 254),
        2: (17.0, 3.0, 0.5 + (43 - 64) / 254),    # Pressure(AfterTouch 17) -> Osc2 Pitch
        3: (14.0, 124.0, 0.5 + (17 - 64) / 254),  # Wheel -> Filt1Env Sustain
        4: (14.0, 123.0, 0.5 + (102 - 64) / 254), # Wheel -> Filt1Env Decay
        5: (33.0, 109.0, 0.5 + (115 - 64) / 254), # Velocity -> Filter1 Cutoff
        6: (33.0, 110.0, 0.5 + (95 - 64) / 254),  # Velocity -> Filter1 Reso
    }
    for slot, (src, dst, amt) in exp.items():
        assert overrides[f"MatrixSrc{slot}"][0] == src, f"slot {slot} src"
        assert overrides[f"MatrixDst{slot}"][0] == dst, f"slot {slot} dst"
        assert overrides[f"MatrixAmount{slot}"][0] == pytest.approx(amt), f"slot {slot} amt"
        assert overrides[f"MatrixOnOff{slot}"][0] == 1.0
    # slot 1 keeps the LFO as row source, After Touch as row Ctrl (MatrixControl)
    assert overrides["MatrixControl1"][0] == 17.0      # Ctrl After Touch
    assert overrides["MatrixControlAmount1"][0] == 1.0


def test_filter_direct_mod_source_mapped_to_hardwired_slot_21(overrides):
    # Blofeld "Filter 1 Mod Source = Mod Wheel, Mod Amount = 111" -> hard-wired slot 21
    # (rows 1-16 = Blofeld Mod 1-16, 17-20 = amp-velo/amp-mod/osc-pitch/DF-env; 2026-11-21)
    assert overrides["MatrixSrc21"][0] == 14.0
    assert overrides["MatrixDst21"][0] == 109.0
    assert overrides["MatrixAmount21"][0] == pytest.approx(0.5 + (111 - 64) / 254)


def test_amp_velocity_maps_to_velocity_volume_slot(overrides):
    # Blofeld Amplifier Velocity 64 (unipolar): AmpVeloAmount = norm(64) = 0.5039.
    # Matrix amount is bipolar centered at 0.5 -> 0.5 + 0.5*norm = 0.752
    # (0.5 would be neutral/ineffective! bipolar trap 2026-11-09)
    assert overrides["AmpVeloAmount"][0] == pytest.approx(64 / 127)
    assert overrides["MatrixSrc7"][0] == 33.0    # Velocity (runtime)
    assert overrides["MatrixDst7"][0] == 152.0   # Volume (runtime)
    assert overrides["MatrixAmount7"][0] == pytest.approx(0.5 + 0.5 * 64 / 127)
    assert overrides["MatrixOnOff7"][0] == 1.0
    # A043 also has Amplifier Mod Source=LFO 3 (slot 8 -> Volume) and
    # Osc Pitch Source=LFO1*MW (slot 9 -> LFO 1 + Ctrl Wheel -> Pitch)
    assert overrides["MatrixSrc8"][0] == 9.0     # LFO 3
    assert overrides["MatrixDst8"][0] == 152.0   # Volume
    # LFO1*MW (2026-11-21): Src stays LFO 1, Wheel moves to the row Ctrl
    assert overrides["MatrixSrc9"][0] == 7.0     # LFO 1
    assert overrides["MatrixControl9"][0] == 14.0   # Ctrl Wheel
    assert overrides["MatrixDst9"][0] == 1.0     # Pitch


def test_glide_rate_calibrated_not_linear():
    # Anchor: Blofeld raw 20 <-> Iridium norm 0.15 (Don-Solaris pairs / Iridium default 0.045 s)
    assert qpat_map.glide_rate_norm(20) == pytest.approx(0.15, abs=1e-9)
    # A073 Chord Hose: raw 48 -> ~0.30. Linear norm() would be 0.378 -> "0.29 s" on the device (too high)
    assert qpat_map.glide_rate_norm(48) == pytest.approx(0.30, abs=0.01)
    assert qpat_map.glide_rate_norm(48) < 48 / 127
    # monotonically increasing and clamped
    vals = [qpat_map.glide_rate_norm(v) for v in range(0, 128)]
    assert all(0.0 <= v <= 1.0 for v in vals)
    assert all(b >= a for a, b in zip(vals, vals[1:]))


def test_glide_rate_matches_measured_curve():
    # Block 5 (docs/research/GLIDE-2026-11-21.md): equal-time mapping for the measured
    # Blofeld/Iridium anchors. Blofeld raw 64 = 592 ms, 70 = 1013 ms, 85 = 2117 ms.
    assert qpat_map.blofeld_glide_seconds(64) == pytest.approx(0.592, abs=0.002)
    assert qpat_map.blofeld_glide_seconds(70) == pytest.approx(1.013, abs=0.003)
    assert qpat_map.blofeld_glide_seconds(85) == pytest.approx(2.117, abs=0.005)
    # Iridium: norm 0.50 = 379 ms, 0.75 = 896 ms, 1.0 = 1600 ms
    assert qpat_map.iridium_glide_seconds(0.50) == pytest.approx(0.379, abs=0.002)
    assert qpat_map.iridium_glide_seconds(0.75) == pytest.approx(0.896, abs=0.003)
    assert qpat_map.iridium_glide_seconds(1.00) == pytest.approx(1.600, abs=0.002)
    # recommended converter anchors from the measurement
    assert qpat_map.glide_rate_norm(50) == pytest.approx(0.32, abs=0.01)
    assert qpat_map.glide_rate_norm(64) == pytest.approx(0.59, abs=0.01)
    assert qpat_map.glide_rate_norm(70) == pytest.approx(0.79, abs=0.01)
    assert qpat_map.glide_rate_norm(85) == pytest.approx(1.0, abs=1e-9)
    assert qpat_map.glide_rate_norm(127) == pytest.approx(1.0, abs=1e-9)


def test_glide_mode_maps_to_glide_type():
    # Iridium has only Onset/Legato; Portamento -> Onset, fingered -> Legato.
    parsed = _parsed_with({"Glide": 1, "Glide Mode": "Portamento"})
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["GlideType"] == (0.0, "Onset")
    parsed = _parsed_with({"Glide": 1, "Glide Mode": "fingered P"})
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["GlideType"] == (1.0, "Legato")
    parsed = _parsed_with({"Glide": 1, "Glide Mode": "fingered G"})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["GlideType"] == (1.0, "Legato")
    assert any("fingered G" in u for u in un)
    # stepped glissando is not representable -> continuous glide + report note
    parsed = _parsed_with({"Glide": 1, "Glide Mode": "Glissando"})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["GlideType"] == (0.0, "Onset")
    assert any("Glide Mode" in u and "Glissando" in u for u in un)


def test_a073_glide_rate_in_overrides():
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A073_20261108_233117.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["GlideOnOff"] == (1.0, "On")
    assert ov["GlideRate"][0] == pytest.approx(0.30, abs=0.01)


def test_lfo_sync_mapped_with_template_keys():
    # A022 ModWheelOrgDrive: LFO1 Sync=1 raw 42 (72 bars), LFO2 Sync=1 raw 14 (512 bars),
    # LFO3 Sync=0 raw 30. Wrong was "LFO1Speed" (key does not exist in the template; device
    # ran at default 0.5 -> tremolo) and clock index as free speed.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A022_20261108_233105.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert "LFO1Speed" not in ov and "Lfo1Speed" in ov
    assert ov["Lfo1Sync"] == (1.0, "On")
    assert ov["Lfo2Sync"] == (1.0, "On")
    assert ov["Lfo3Sync"] == (0.0, "Off")
    # 512 bars = 2048 beats -> largest available ratio (index 0 = 1024)
    assert ov["Lfo2SyncRatio"][0] == 0.0
    # 72 bars = 288 beats -> next index ~4 (256 beats)
    assert ov["Lfo1SyncRatio"][0] in (3.0, 4.0)
    assert ov["Lfo3Speed"][0] == pytest.approx(30 / 127)
    # Ringmod key is called RingModOsc1ToOsc2 in the template
    assert "RingModOsc1ToOsc2" in ov


def test_converted_file_is_version_14(parsed, tmp_path):
    out_path, mapped, unmapped = workflow.convert_parsed(parsed, "A043", tmp_path, REPO / TEMPLATE)
    q = qpat.load(out_path)
    assert q["version"] == qpat.PRESET_VERSION == 14
    assert q["params"]["Osc1Destination"]["value"] == 2.0
    assert q["params"]["MatrixDst1"]["value"] == 1.0


# --- P0 2026-11-15 (docs/research/ANALYSIS-2026-11-15-conversion-fixes.md) ---

DUMPS_9 = {
    "A001": "dumps/blofeld_sndd_A001_20261108_233049.bin",
    "A008": "dumps/blofeld_sndd_A008_20261108_233053.bin",
    "A010": "dumps/blofeld_sndd_A010_20261108_233057.bin",
    "A019": "dumps/blofeld_sndd_A019_20261108_233101.bin",
    "A022": "dumps/blofeld_sndd_A022_20261108_233105.bin",
    "A039": "dumps/blofeld_sndd_A039_20261108_233109.bin",
    "A043": "dumps/blofeld_sndd_A043_20261108_135516.bin",
    "A071": "dumps/blofeld_sndd_A071_20261108_233113.bin",
    "A073": "dumps/blofeld_sndd_A073_20261108_233117.bin",
}


def test_matrix_dst_enum_is_runtime():
    # OS 4.1.0b2 runtime enum (param-info 2480, 2026-11-18) = qpat file value (identity)
    assert qpat_map.MATRIX_DST["DF Amount"] == 104.0
    assert qpat_map.MATRIX_DST["Filter2 Cutoff"] == 113.0
    assert qpat_map.MATRIX_DST["Filter2 Reso"] == 114.0
    assert qpat_map.MATRIX_DST["Volume"] == 152.0
    assert qpat_map.MATRIX_DST["Filter1 Cutoff"] == 109.0


def test_serial_df_env_slot_dst_v14():
    # Serial (A001): slot Filter1 Env -> DF Amount must land on dst 104.0 (runtime),
    # otherwise the DigiFormer does not open -> serial patches too dark/quiet
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A001"]))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    df_slots = [k for k, v in ov.items() if k.startswith("MatrixDst") and v[1] == "DF Amount"]
    assert df_slots, "serial needs Filter1 Env -> DF Amount slot"
    for k in df_slots:
        assert ov[k][0] == 104.0, f"{k} dst must be the runtime value 104.0"


def test_aftertouch_do_poly_poly_alle_9():
    # User decision 2026-11-18 (live): Iridium reacts to Channel AT, but the keyboard
    # produces Poly AT -> conversion targets POLY AT (AfterTouchDoPoly=1.0).
    # (Earlier: 0.0 'Mono AT' per P0-2, ANALYSIS-2026-11-15.)
    for loc, dump in DUMPS_9.items():
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / dump))
        ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
        assert "AfterTouchDoPoly" in ov, loc
        assert ov["AfterTouchDoPoly"][0] == 1.0, loc


def test_aftertouch_matrix_src_is_17_runtime():
    # OS 4.1.0b2 runtime enum (param-info 2478) = qpat file value (identity, controlled
    # load test 2026-11-18): 'After Touch' = 17. Poly AT = AfterTouchDoPoly=1.0
    # (see test_aftertouch_do_poly_poly_alle_9).
    assert qpat_map.MATRIX_SRC["After Touch"] == 17.0
    ov, _ = qpat_map.blofeld_to_qpat_params(
        bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A043"])))
    assert ov["MatrixSrc1"][0] == 8.0    # A043 M1: LFO2*Press -> Src LFO 2 ...
    assert ov["MatrixControl1"][0] == 17.0  # ... + Ctrl After Touch (2026-11-21)
    assert ov["MatrixSrc2"][0] == 17.0   # A043 M2: Pressure -> O2 Pitch


def test_no_v8_enum_leak_in_v14_qpat_all_9():
    # v8 template slots that the mapping does not overwrite must not write v8 enum values
    # (e.g. MatrixDst 71 'DF Amount', 103) into the v14 file (P0-1, A008: [71, 95])
    tpl = qpat.load(REPO / TEMPLATE)
    # every MatrixDst we write must be a valid RUNTIME enum value (param-info 2480,
    # 2026-11-18) - the loader reads file values 1:1, so an old/stale enum value would
    # silently target a different destination on the device.
    VALID_DST = set(qpat_map.MATRIX_DST.values())
    for loc, dump in DUMPS_9.items():
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / dump))
        ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
        merged = qpat_map.apply_to_template(tpl, ov, name=parsed["name"])
        for k, (val, _disp) in merged["params"].items():
            if k.startswith("MatrixDst"):
                assert val in VALID_DST, f"{loc}: {k}={val} is not a runtime enum value"


# --- 2026-11-18 rebuild: sync, serial F2 remap, FX by type, detune centering ---

def test_osc2_sync_mapped_a071_a008_not_a001():
    # P1-1: Blofeld "Osc 2 Sync to O3" -> Osc2WaveformSync (was unmapped, A071 "no sync")
    for loc in ("A071", "A008"):
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9[loc]))
        assert parsed["params"]["Osc 2 Sync to O3"] == 1
        ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
        assert ov["Osc2WaveformSync"][0] == qpat_map.SYNC_AMOUNT, loc
        assert not any("Sync to O3" in u for u in unmapped), loc
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A001"]))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert "Osc2WaveformSync" not in ov   # sync off -> template default (0.0)


def test_serial_f2_mod_targets_digiformer_a001():
    # P1-2: A001 serial, Filter 2 Mod Source=Velocity amt 107 -> slot Velocity->DF Amount
    # (dst 95.0), NOT Filter2 Cutoff (104.0 - the F2 stage is Off in serial mode)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A001"]))
    assert parsed["params"]["Filter 2 Mod Source"] == "Velocity"
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    vel_df = [k for k in ov if k.startswith("MatrixDst")
              and ov[k][1] == "DF Amount" and ov[k.replace("Dst", "Src")][0] == 33.0]
    assert vel_df, "serial needs Velocity -> DF Amount slot"
    assert all(ov[k][0] == 104.0 for k in vel_df)
    no_f2 = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "Filter2 Cutoff"]
    assert not no_f2, "serial must not target the switched-off F2 stage"


def test_parallel_keeps_filter2_mod_a010():
    # A010 parallel: F2 stays filter 2 -> F2 mods keep dst 104.0
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A010"]))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    f2c = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "Filter2 Cutoff"]
    assert f2c and all(ov[k][0] == 113.0 for k in f2c)


def test_fx_mix_key_by_type_not_slot_a008():
    # P1-3: A008 FX2=Chorus mix 24 -> ChorusDryWet, NOT DelayDryWet (old slot-based bug)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A008"]))
    assert parsed["params"]["Effect 2 Type"] == "Chorus"
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["ChorusDryWet"][0] == pytest.approx(24 / 127)
    assert "DelayDryWet" not in ov
    # both FX slots are Chorus -> FX2 params win on the shared keys (slot 2 processed last)
    assert ov["ChorusSpeed"][0] == pytest.approx(parsed["params"]["Effect 2 Parameter 1"] / 127)


def test_fx_clk_delay_params_a039():
    # A039 FX2=Clk.Delay mix 14, p5 Feedback=1, p6 Cutoff=100, p11 Length=7 (0..29 clock)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A039"]))
    assert parsed["params"]["Effect 2 Type"] == "Clk.Delay"
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FX2Type"][1] == "Delay"
    assert ov["DelayDryWet"][0] == pytest.approx(14 / 127)
    assert ov["DelaySync"][0] == 1.0
    assert ov["DelayFeed"][0] == pytest.approx(1 / 127)
    assert ov["DelayHiCut"][0] == pytest.approx(100 / 127)
    assert ov["DelayLeftSync"][0] == pytest.approx(7 / 29)
    assert ov["DelayRightSync"][0] == pytest.approx(7 / 29)


def test_detune_centered_not_full_range_a008():
    # A008 Osc1 Detune raw 126: old norm() -> 0.992 (almost full Iridium range);
    # bipolar centered with the live-calibrated cent scale: 0.5 + (126-64)/127 = 0.988
    # (2026-11-21 Init sweep: Blofeld +/-101 cent, Iridium +/-101 cent at norm 0/1)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A008"]))
    assert parsed["params"]["Osc 1 Detune"] == 126
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1FinePitch"][0] == pytest.approx(0.5 + (126 - 64) / 127)
    assert ov["Osc1FinePitch"][0] != pytest.approx(126 / 127)
    assert qpat_map.fine_pitch_norm(64) == pytest.approx(0.5)


def test_lfo_speed_mod_dst_runtime_a022():
    # A022 M14 MW->LFO1Speed -> dst 'LFO1 Speed' = 154.0 (runtime enum, param-info 2480)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A022"]))
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    lfo_dst = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "LFO1 Speed"]
    assert lfo_dst and all(ov[k][0] == 154.0 for k in lfo_dst)
    assert not any("LFO1Speed" in u for u in unmapped)


def test_ae_attack_mod_dst_runtime():
    # 'AE Attack' -> 'AmpEnv Attack' dst 118.0 (runtime enum, param-info 2480)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A019"]))
    parsed["params"]["Modulation 3 Destination"] = "AE Attack"
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    ae = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "AmpEnv Attack"]
    assert ae and all(ov[k][0] == 118.0 for k in ae)
    assert not any("AE Attack" in u for u in unmapped)


def test_amp_mod_source_slot_a008():
    # A008 Amplifier Mod Source=AmpEnv amt 64 -> slot src 'Amp Env' (1.0) -> Volume (115)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A008"]))
    assert parsed["params"]["Amplifier Mod Source"] == "AmpEnv"
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    amp = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "Volume"
           and ov[k.replace("Dst", "Src")][0] == 1.0]
    assert amp and all(ov[k][0] == 152.0 for k in amp)
    assert not any("Amplifier Mod Source" in u for u in unmapped)


def test_fe_release_and_ae_release_mapped_runtime():
    # A008 M10: Keytrack -> FE Release -> dst 'Filt1Env Release' = 125 (runtime)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A008"]))
    assert parsed["params"]["Modulation 10 Destination"] == "FE Release"
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    fe = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "Filt1Env Release"]
    assert fe and all(ov[k][0] == 125.0 for k in fe)
    assert not any("FE Release" in u for u in unmapped)
    # synthetic AE Release -> 121
    parsed["params"]["Modulation 10 Destination"] = "AE Release"
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    ae = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "AmpEnv Release"]
    assert ae and all(ov[k][0] == 121.0 for k in ae)


def test_f2_pan_serial_goes_to_df_pan_parallel_to_filter2_pan():
    # A008 is serial: a Mod slot with dst 'F2 Pan' must become 'DF Pan' (107)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A008"]))
    assert parsed["params"]["Filter Routing"] == 1
    parsed["params"]["Modulation 5 Source"] = "Velocity"
    parsed["params"]["Modulation 5 Destination"] = "F2 Pan"
    parsed["params"]["Modulation 5 Amount"] = 100
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    pans = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] in ("DF Pan", "Filter2 Pan")]
    assert pans and all(ov[k][0] == 107.0 and ov[k][1] == "DF Pan" for k in pans)
    # parallel (A010): F2 Pan stays 'Filter2 Pan' = 115
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A010"]))
    assert parsed["params"]["Filter Routing"] == 0
    parsed["params"]["Modulation 5 Source"] = "Velocity"
    parsed["params"]["Modulation 5 Destination"] = "F2 Pan"
    parsed["params"]["Modulation 5 Amount"] = 100
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    pans = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "Filter2 Pan"]
    assert pans and all(ov[k][0] == 115.0 for k in pans)


def test_wavetable_bridge_covers_all_blofeld_shapes():
    # runtime WavetableTable names (param-info 19) match Blofeld SHAPES 1:1
    from bloridium.blofeld_dump import SHAPES
    missing = [s for s in SHAPES if s != "off" and s not in ("Pulse", "Saw", "Triangle", "Sine")
               and s not in qpat_map.BLOFELD_WAVETABLE_TO_IRIDIUM]
    assert missing == [], f"unbridged Blofeld wavetables: {missing}"


def test_fx_type_runtime_shifted_by_tremolo():
    # param-info 2754/2756: Tremolo inserted at 1 -> Phaser=2, Chorus=3, Delay=5, Drive=8
    assert qpat_map.FX_TYPE["Chorus"] == 3.0
    assert qpat_map.FX_TYPE["Delay"] == 5.0
    assert qpat_map.FX_TYPE["Drive"] == 8.0
    assert qpat_map.FX_TYPE["Off"] == 0.0


def test_osc_type_off_is_6_runtime():
    # param-info 0: 6 = Off (old tables had 4)
    assert qpat_map.OSC_TYPE["Off"] == 6.0


def test_reverb_fx2_mix_via_reverb_gain_and_params():
    # FX2=Reverb: Iridium has no ReverbDryWet, but ReverbGain IS the reverb dry/wet
    # (manual: "0% = dry only, 100% = pure reverb") -> use it, no Constant matrix row.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A039"]))
    parsed["params"]["Effect 2 Type"] = "Reverb"
    parsed["params"]["Effect 2 Mix"] = 64
    parsed["params"]["Effect 2 Parameter 2"] = 100   # Shape
    parsed["params"]["Effect 2 Parameter 3"] = 80    # Decay
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FX2Type"][1] == "Reverb" and ov["FX2Type"][0] == 6.0   # runtime enum
    assert ov["ReverbTime"][0] == pytest.approx(80 / 127)
    assert ov["ReverbColor"][0] == pytest.approx(100 / 127)
    assert ov["ReverbGain"][0] == pytest.approx(64 / 127)
    assert not any(k.startswith("MatrixDst") and ov[k][1] == "FX2 DryWet" for k in ov)
    assert not any("Mix for Reverb" in u for u in unmapped)


def test_unison_count_uses_bits_4_to_6():
    # Blofeld Allocation/Unisono = 0uuu000a (spec 4.10): bits 4-6 are the unison
    # index (0 off, 1 dual, 2 three voices ...). The old >>5 halved the voice count.
    parsed = bd.parse_sndd((REPO / "dumps/banks/A/A066.bin").read_bytes())
    for raw, count in ((0x00, 0.0), (0x10, 1.0), (0x20, 2.0), (0x40, 4.0), (0x50, 5.0)):
        parsed["params"]["Allocation/Unisono"] = raw
        ov, _un = qpat_map.blofeld_to_qpat_params(parsed)
        assert ov["UnisonoCount"][0] == count, f"raw {raw:#04x}"
    # Blofeld has neither unison pan spread nor unison delay -> neutral values,
    # otherwise template defaults (pan 0.5, delay 0.25) delay the Iridium voices.
    assert ov["UnisonoPan"][0] == pytest.approx(0.5)
    assert ov["UnisonoDelay"][0] == pytest.approx(0.0)


# --- Task 3 (2026-11-20): LFO Shape/Delay/Phase + Mixer Noise -> freier Osc -----

def _parsed_with(param_fixes: dict, sdata_fixes: dict | None = None):
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMP))
    parsed["params"].update(param_fixes)
    if sdata_fixes:
        sd = bytearray(parsed["sdata"])
        for i, v in sdata_fixes.items():
            sd[i] = v
        parsed["sdata"] = bytes(sd)
    return parsed


def test_lfo_shape_delay_phase_mapped():
    parsed = _parsed_with({"LFO 1 Shape": "Saw", "LFO 1 Delay": 30,
                           "LFO 1 Start Phase": 64})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Lfo1Shape"][0] == 4.0                       # Saw -> Saw (up)
    assert ov["Lfo1Delay"][0] == pytest.approx(30 / 127)
    assert ov["Lfo1Phase"][0] == pytest.approx(64 / 127)
    assert not any(u.startswith("LFO 1") and "Shape" in u for u in un)


def test_lfo_fade_maps_to_attack_decay():
    # Blofeld Fade is bipolar -64..+63 (raw 64 = 0): positive = fade-in,
    # negative = fade-out. The Iridium has LfoNAttack / LfoNDecay.
    parsed = _parsed_with({"LFO 1 Fade": 127})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Lfo1Attack"][0] == pytest.approx(1.0)
    assert ov["Lfo1Decay"][0] == pytest.approx(0.0)
    assert not any("LFO 1 Fade" in u for u in un)

    parsed = _parsed_with({"LFO 2 Fade": 0})       # -64 = maximum fade-out
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Lfo2Attack"][0] == pytest.approx(0.0)
    assert ov["Lfo2Decay"][0] == pytest.approx(1.0)
    assert not any("LFO 2 Fade" in u for u in un)

    parsed = _parsed_with({"LFO 3 Fade": 64})      # neutral
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Lfo3Attack"][0] == pytest.approx(0.0)
    assert ov["Lfo3Decay"][0] == pytest.approx(0.0)
    # Keytrack still has no LFO pendant and stays in the report
    parsed = _parsed_with({"LFO 1 Keytrack": 20})
    _ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert any("LFO 1" in u and "Keytrack" in u for u in un)


def test_lfo_shape_enum_covers_all_blofeld_shapes():
    # Enum aus 1186 Factory-qpats (Quantum_Factories.zip): 0 Sine, 1 Triangle,
    # 2 Square, 3 Saw(down), 4 Saw(up), 5 S&H. Blofeld "Random" -> S&H (Naeherung).
    expect = {"Sine": 0.0, "Triangle": 1.0, "Square": 2.0,
              "Saw": 4.0, "Random": 5.0, "S&H": 5.0}
    for label, val in expect.items():
        parsed = _parsed_with({"LFO 2 Shape": label})
        ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
        assert ov["Lfo2Shape"][0] == val, label


def test_noise_on_free_osc3_white():
    # Osc 3 freimachen (Shape raw 40 = 0 -> Off) und Noise einschalten
    parsed = _parsed_with({"Mixer Noise Level": 40, "Mixer Noise Balance": 96,
                           "Mixer Noise Colour": 100, "Osc 3 Shape": "Off"},
                          {40: 0})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc3Type"][0] == qpat_map.OSC_TYPE["Waveform"]
    assert ov["Osc3WaveformShape"][0] == 5.0               # Colour > 64 -> White Noise
    assert ov["Osc3Vol"][0] == pytest.approx(40 / 127)
    assert ov["Osc3Pan"][0] == pytest.approx(0.5)          # Balance is NOT pan
    # A043 is parallel -> destination stays "all into filter"; the share is global
    assert ov["Osc3Destination"][0] == pytest.approx(2.0)
    assert not any("Noise" in u for u in un)


def test_noise_colour_dark_maps_pink():
    parsed = _parsed_with({"Mixer Noise Level": 20, "Mixer Noise Colour": 10,
                           "Osc 3 Shape": "Off"}, {40: 0})
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc3WaveformShape"][0] == 4.0               # Pink Noise


def test_noise_without_free_osc_stays_unmapped_and_keeps_oscs():
    # alle 3 Oscs belegt -> Noise kann nicht untergebracht werden, Oscs duerfen
    # NICHT ueberschrieben werden
    parsed = _parsed_with({"Mixer Noise Level": 40, "Osc 1 Shape": "Saw",
                           "Osc 2 Shape": "Saw", "Osc 3 Shape": "Saw"},
                          {8: 1, 24: 1, 40: 1})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    for n in (1, 2, 3):
        assert ov[f"Osc{n}Type"][0] == qpat_map.OSC_TYPE["Waveform"]
    assert any("Noise" in u for u in un)


def test_noise_level_zero_leaves_oscs_untouched():
    parsed = _parsed_with({"Mixer Noise Level": 0, "Osc 3 Shape": "Off"}, {40: 0})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc3Type"][0] == qpat_map.OSC_TYPE["Off"]
    assert not any("Noise" in u for u in un)


def test_noise_uses_muted_osc_and_noise_mod_dst():
    # Osc 3 Level 0 (stumm) -> darf als Noise-Osc verwendet werden; Mod-Dst
    # NoiseLevel/Noise Bal. -> Osc3 Mix/Pan
    parsed = _parsed_with({"Mixer Noise Level": 30, "Mixer Noise Colour": 100,
                           "Mixer Osc 3 Level": 0,
                           "Modulation 1 Source": "LFO 1", "Modulation 1 Destination": "NoiseLevel",
                           "Modulation 1 Amount": 64,
                           "Modulation 2 Source": "AmpEnv", "Modulation 2 Destination": "Noise Bal.",
                           "Modulation 2 Amount": 64})
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc3WaveformShape"][0] == 5.0
    assert ov["Osc3Vol"][0] == pytest.approx(30 / 127)
    assert ov["MatrixDst1"][1] == "Osc3 Mix"
    # 'Noise Bal.' is the F1/F2 share -> no matrix destination (OscNDestination
    # is not modulatable), so row 2 is not created and the destination is logged.
    assert "MatrixDst2" not in ov
    assert any("Noise Bal." in u for u in un)


# --- 2026-11-21: PPG LP -> 24dB LP; Filter-Drive -> FX1 Drive (A005 @ slot 204) ---

A005 = "dumps/blofeld_sndd_A005_20261119_053353.bin"


def test_ppg_lp_maps_to_24db_lp():
    # A005 HooverBass: Blofeld F1 = PPG LP (24dB-Ladder-Typ) -> Filter12Type 3.0,
    # NICHT 12dB LP (am Geraet gesehen: FilterModel=svf + 12dB LP = falsch)
    parsed = bd.parse_sndd((REPO / A005).read_bytes())
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter12Type"] == (3.0, "24dB LP")


def test_driven_24db_lowpass_uses_sat_variant_a043():
    # Same sound with Filter 1 Drive 16 (Clipping) -> "24dB sat. LP" (2026-11-22)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMP))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert parsed["params"]["Filter 1 Drive"] == 16
    assert ov["Filter12Type"] == (4.0, "24dB sat. LP")


def test_sync_pitch_mod_retargets_to_wf2_sync_e016():
    # Don Solaris E016 "P1 Sync": Osc 2 hard sync on, Mod 1 Env3 -> O2 Pitch.
    # Ear-matched on the device: the modulation must sweep WF2 Sync, not Osc2 Pitch.
    parsed = bd.parse_sndd((REPO / "dumps/banks/E/E016.bin").read_bytes())
    assert parsed["params"]["Osc 2 Sync to O3"] == 1
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    rows = _rows(ov)
    assert rows[1]["Dst"] == (50.0, "WF2 Sync")
    assert rows[1]["Src"][1] == "Free Env1"
    assert ov["Osc2WaveformSync"] == (qpat_map.SYNC_AMOUNT, "Sync 0.25")


def test_filter_drive_simulated_as_fx1_drive_tube_a005():
    # A005: F1 Drive 0, F2 Drive 8 Curve "Tube" -> FX1 = Drive, DriveType = Tube (1.0)
    parsed = bd.parse_sndd((REPO / A005).read_bytes())
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FX1Type"][0] == qpat_map.FX_TYPE["Drive"]
    assert ov["DriveType"] == (1.0, "Tube -> DriveType")
    assert ov["DriveAmount"][0] == pytest.approx(8 / 127)
    # Blofeld drive is an insert (100 % of the signal is driven), not a send.
    # The old DryWet=norm(drive) halved/quartered the effect; measurement f2
    # showed Iridium strengths of 0.20/0.30x at raw 32/64 (OK at 127).
    assert ov["DriveDryWet"][0] == pytest.approx(1.0)
    assert ov["DriveGain"][0] == 0.5
    # Blofeld FX1 war Chorus (mix 35 > 0) -> Ersatz wird als unmapped geloggt
    assert any("replaced by filter-drive" in u and "Chorus" in u for u in un)


def test_filter_drive_clipping_uses_sat_lowpass_a043():
    # A043: F1 Drive 16 Curve "Clipping" -> saturating 24 dB LP instead of a
    # separate FX1 Drive stage (2026-11-22).
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMP))
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter12Type"] == (4.0, "24dB sat. LP")
    assert "DriveType" not in ov
    assert ov["FX1Type"][0] == qpat_map.FX_TYPE["Chorus"]


def test_filter_drive_pickup_curve_maps_to_pickup():
    parsed = bd.parse_sndd((REPO / A005).read_bytes())
    parsed["params"]["Filter 2 Drive"] = 100
    parsed["params"]["Filter 2 Drive Curve"] = "Pickup 1"
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["DriveType"][0] == 2.0
    assert ov["DriveAmount"][0] == pytest.approx(100 / 127)


def test_no_filter_drive_keeps_fx1_untouched():
    parsed = bd.parse_sndd((REPO / A005).read_bytes())
    parsed["params"]["Filter 1 Drive"] = 0
    parsed["params"]["Filter 2 Drive"] = 0
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FX1Type"][0] == qpat_map.FX_TYPE["Chorus"]  # Blofeld FX1 Chorus bleibt
    assert "DriveType" not in ov and "DriveAmount" not in ov


# --- 2026-11-21: LFOx*MW products via matrix Ctrl (A006 @ slot 205); env curves Lin ---

A006 = "dumps/blofeld_sndd_A006_20261119_053353.bin"


def _rows(ov):
    import re
    rows = {}
    for k, v in ov.items():
        m = re.match(r"Matrix(Src|Dst|Amount|Control|ControlAmount)(\d+)$", k)
        if m:
            rows.setdefault(int(m.group(2)), {})[m.group(1)] = v
    return rows


def test_modifier_product_lfo2_times_mw_maps_to_src_lfo2_ctrl_wheel():
    # A006: Modifier 1 = LFO 2 * Mod Wheel; Mod 10-12 use it -> matrix rows with
    # Src=LFO 2 (8.0) AND Control=Wheel (14.0) — the "LFO2 CTRL: ModWheel" structure
    parsed = bd.parse_sndd((REPO / A006).read_bytes())
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    rows = _rows(ov)
    ctrl_rows = [r for r in rows.values()
                 if r.get("Control", (0.0,))[0] == qpat_map.MATRIX_SRC["Wheel"]]
    assert len(ctrl_rows) == 4  # Mod 10, 11, 12 + Osc Pitch Source (LFO1*MW)
    for r in ctrl_rows:
        assert r["Src"][0] in (7.0, 8.0)          # LFO 1 or LFO 2 as row source
        assert r["ControlAmount"][0] == 1.0        # full ctrl scaling
    assert not any("Modulation 10" in u or "Modulation 11" in u for u in un)


def test_direct_lfox_mw_source_keeps_lfo_with_ctrl_wheel():
    # A001 Mod 8: source "LFO1*MW" -> Src=LFO 1 + Ctrl=Wheel (was: Wheel only, LFO lost)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMP))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    rows = _rows(ov)
    hit = [r for r in rows.values()
           if r.get("Src", (0.0,))[0] == qpat_map.MATRIX_SRC["LFO 1"]
           and r.get("Control", (0.0,))[0] == qpat_map.MATRIX_SRC["Wheel"]]
    assert hit and hit[0]["Dst"][0] == qpat_map.MATRIX_DST["Pitch"]


def test_resolve_mod_source_unit():
    p = {"Modifier 2 Operation": "*", "Modifier 2 Source A": "LFO 3",
         "Modifier 2 Source B": "Mod Wheel"}
    assert qpat_map._resolve_mod_source(p, "Modifier 2") == ("LFO 3", "Wheel")
    assert qpat_map._resolve_mod_source(p, "LFO2*MW") == ("LFO 2", "Wheel")
    assert qpat_map._resolve_mod_source(p, "LFO1*Press") == ("LFO 1", "After Touch")
    assert qpat_map._resolve_mod_source(p, "Velocity") == ("Velocity", None)
    assert qpat_map._resolve_mod_source(p, "off") == (None, None)
    # unknown modifier op -> unmapped
    p2 = {"Modifier 1 Operation": "*", "Modifier 1 Source A": "Velocity",
          "Modifier 1 Source B": "Mod Wheel"}
    assert qpat_map._resolve_mod_source(p2, "Modifier 1") == (None, None)


def test_envelope_curves_rc_exp_exp(overrides):
    # user decision 2026-11-22: Attack = RC, Decay/Release = Exp. The old all-Lin
    # mapping made releases audibly too long.
    for grp in ("AmpEnv", "Filter1", "Filter2", "FreeEnv1", "FreeEnv2"):
        assert overrides[f"{grp}AttackCurve"] == (1.0, "RC")
        assert overrides[f"{grp}DecayCurve"] == (0.0, "Exp")
        assert overrides[f"{grp}ReleaseCurve"] == (0.0, "Exp")


def test_a007_osc_pwm_mapped_to_wf_warp_rows_ge_21():
    # A007: Osc2/3 are Pulse (PWM acts on pulse width) -> rows 22/23 to WF2/3 Warp.
    # Osc1 is Saw: Blofeld PWM does nothing there, the Iridium WF warp would hear it
    # (A1, profiling 2026-11-21) -> deliberately ignored, no row.
    parsed = bd.parse_sndd((REPO / "dumps/blofeld_sndd_A007_20261119_053353.bin").read_bytes())
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    rows = _rows(ov)
    pwm = {n: r for n, r in rows.items()
           if n >= 21 and r.get("Dst", (0.0,))[0] in (18.0, 49.0, 80.0)}
    assert len(pwm) == 2
    by_dst = {r["Dst"][0]: r for r in pwm.values()}
    assert by_dst[49.0]["Src"][0] == 8.0   # WF2 Warp <- LFO 2
    assert by_dst[80.0]["Src"][0] == 9.0   # WF3 Warp <- LFO 3
    assert by_dst[49.0]["Amount"][0] == pytest.approx(0.5 + (3 - 64) / 254)   # amt 3
    assert 18.0 not in by_dst
    assert any("Ignored: Osc 1 PWM" in u for u in un)


def test_pwm_row_only_for_pulse_shapes():
    # A1 (P0): A066 Init is Saw; a PWM source/amount must not create a WF warp row,
    # because that changes the sawtooth instead of the pulse width. Pulse keeps it.
    parsed = bd.parse_sndd((REPO / "dumps/banks/A/A066.bin").read_bytes())
    assert parsed["params"]["Osc 1 Shape"] == "Saw"
    parsed["params"]["Osc 1 PWM Source"] = "LFO 1"
    parsed["params"]["Osc 1 PWM Amount"] = 64
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    warp = [r for r in _rows(ov).values()
            if r.get("Dst", (0.0,))[0] == qpat_map.MATRIX_DST["WF1 Warp"]]
    assert warp == []
    assert any("Ignored: Osc 1 PWM" in u for u in un)

    parsed["params"]["Osc 1 Shape"] = "Pulse"
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    warp = [r for r in _rows(ov).values()
            if r.get("Dst", (0.0,))[0] == qpat_map.MATRIX_DST["WF1 Warp"]]
    assert len(warp) == 1
    assert warp[0]["Src"][0] == qpat_map.MATRIX_SRC["LFO 1"]
    assert not any("Osc 1 PWM ignored" in u for u in un)


def test_a005_osc_fm_approx_via_pitch_and_serial_f2_pan_via_df():
    # A005: Osc2 FM Source LFO1 amt 4 -> row >= 21 Dst Osc2 Pitch; Filter2 Pan (serial)
    # -> DF Pan (the audible F2 is the DigiFormer in serial mode)
    parsed = bd.parse_sndd((REPO / A005).read_bytes())
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    rows = _rows(ov)
    hw = [r for n, r in rows.items() if n >= 21]
    fm = [r for r in hw if r.get("Dst", (0.0,))[0] == qpat_map.MATRIX_DST["Osc2 Pitch"]]
    assert fm and fm[0]["Src"][0] == qpat_map.MATRIX_SRC["LFO 1"]
    # A005's Filter 2 Pan Amount is 64 = neutral -> no row (the old code created
    # a neutral, ineffective row). A non-neutral amount creates the full-range row.
    pan = [r for r in hw if r.get("Dst", (0.0,))[0] == qpat_map.MATRIX_DST["DF Pan"]]
    assert not pan
    parsed2 = bd.parse_sndd((REPO / A005).read_bytes())
    parsed2["params"]["Filter 2 Pan Amount"] = 0
    ov2, _ = qpat_map.blofeld_to_qpat_params(parsed2)
    rows2 = [r for n, r in _rows(ov2).items() if n >= 21
             and r.get("Dst", (0.0,))[0] == qpat_map.MATRIX_DST["DF Pan"]]
    assert rows2 and rows2[0]["Amount"][0] == pytest.approx(0.0)   # full left
    assert not any("FM" in u or "Pan" in u for u in un if "Filter" in u or "Osc" in u)


def test_a008_osc1_1ft_clamped_with_constant_pitch_shift():
    # A008 Easy Piano: Osc1 Octave raw 100 = 1' (+36 semi), Semitone +4 -> +40 semi total.
    # CoarsePitch enum max is +24 (48), so clamp to 48 and shift +16 semi via
    # matrix row Constant -> Osc1 Pitch (user proposal 2026-11-21).
    parsed = bd.parse_sndd((REPO / "dumps/blofeld_sndd_A008_20261108_233053.bin").read_bytes())
    ov, un = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1CoarsePitch"] == (48.0, "+40 semi")     # clamped, label shows total
    assert ov["Osc2CoarsePitch"] == (24.0, "+0 semi")
    rows = _rows(ov)
    shift = [r for n, r in rows.items() if n >= 21
             and r.get("Src", (0.0,))[0] == qpat_map.MATRIX_SRC["Constant"]]
    assert len(shift) == 1
    assert shift[0]["Dst"][0] == qpat_map.MATRIX_DST["Osc1 Pitch"]
    # +16 semi excess -> amount per live calibration (1.0 = +24 semi, nichtlinear)
    assert shift[0]["Amount"][0] == pytest.approx(
        qpat_map.matrix_pitch_amount_for_semi(16.0), abs=1e-9)
    assert 0.875 < shift[0]["Amount"][0] < 1.0   # zwischen +13.5 (0.875) und +24 (1.0)


def test_matrix_pitch_calibration_inverse():
    # Kalibrierung 2026-11-21: 0.5 -> 0 semi, 1.0 -> +24 semi, 0.0 -> -13.8 semi
    assert qpat_map.matrix_pitch_amount_for_semi(0.0) == pytest.approx(0.5)
    assert qpat_map.matrix_pitch_amount_for_semi(24.0) == pytest.approx(1.0, abs=0.001)
    assert qpat_map.matrix_pitch_amount_for_semi(-13.78) == pytest.approx(0.0)
    assert qpat_map.matrix_pitch_amount_for_semi(12.0) > 0.75   # ~0.85 (nichtlinear)
    assert qpat_map.matrix_pitch_amount_for_semi(99.0) == 1.0  # clamp
    assert qpat_map.matrix_pitch_amount_for_semi(-99.0) == 0.0


def test_a007_octaves_in_range_no_constant_rows():
    # A007: Osc1/2 = 4' (+12 -> 36), Osc3 = 16' (-12 -> 12) — all within 0..48, no shift rows
    parsed = bd.parse_sndd((REPO / "dumps/blofeld_sndd_A007_20261119_053353.bin").read_bytes())
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1CoarsePitch"][0] == 36.0 and ov["Osc1CoarsePitch"][1] == "+12 semi"
    assert ov["Osc3CoarsePitch"][0] == 12.0 and ov["Osc3CoarsePitch"][1] == "-12 semi"
    rows = _rows(ov)
    assert not any(r.get("Src", (0.0,))[0] == qpat_map.MATRIX_SRC["Constant"]
                   for r in rows.values())


def test_waveform_semitone_slots_neutral(overrides):
    # The template shipped Osc2 slot2 and Osc3 slot1 as 0 (= -12 semitones); the
    # converter never overrode them, so those oscillators ran an octave low
    # (live 2026-11-22: A020 Osc3 coarse +0 sounded -12; slots=12 -> score 30->63).
    # The Blofeld semitone is already part of CoarsePitch, so all four slots of
    # every oscillator must be neutral (12 = +0).
    for osc in (1, 2, 3):
        for slot in (1, 2, 3, 4):
            key = f"Osc{osc}WaveformSemitone{slot}"
            assert overrides[key][0] == pytest.approx(12.0), key


def test_envelope_time_curve():
    # Measured live 2026-11-22 (clean test patch, Lin): the old raw/127 mapping was
    # up to ~3x off for attack/decay.
    assert qpat_map.envelope_time_norm("attack", 0) == pytest.approx(0.0)
    assert qpat_map.envelope_time_norm("attack", 64) == pytest.approx(0.22)
    assert qpat_map.envelope_time_norm("decay", 127) == pytest.approx(0.60)
    for stage in ("attack", "decay"):
        vals = [qpat_map.envelope_time_norm(stage, r) for r in range(128)]
        assert all(a <= b for a, b in zip(vals, vals[1:])), stage


def test_envelope_times_use_the_curve(parsed, overrides):
    # A043: amp env raw values must go through envelope_time_norm, not norm().
    raw_a = parsed["params"]["Amplifier Envelope Attack"]
    raw_d = parsed["params"]["Amplifier Envelope Decay"]
    assert overrides["AmpEnvAttack"][0] == pytest.approx(
        qpat_map.envelope_time_norm("attack", raw_a))
    assert overrides["AmpEnvDecay"][0] == pytest.approx(
        qpat_map.envelope_time_norm("decay", raw_d))


def test_f1_drive_uses_sat_lowpass_instead_of_fx_drive():
    # 2026-11-22: F1 drive -> "24dB sat. LP" (filter model), no extra FX1 Drive.
    p = {"Filter 1 Type": "LP 24dB", "Filter 2 Type": "Bypass", "Filter Routing": 0,
         "Filter 1 Drive": 40, "Filter 1 Drive Curve": "Tube",
         "Filter 2 Drive": 0}
    base = bd.parse_sndd((REPO / "dumps/blofeld_sndd_A043_20261108_135516.bin").read_bytes())
    base["params"].update(p)
    ov, _ = qpat_map.blofeld_to_qpat_params(base)
    assert ov["Filter12Type"] == (4.0, "24dB sat. LP")
    assert "DriveType" not in ov        # no second (FX) drive stage
