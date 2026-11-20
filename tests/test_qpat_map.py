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


def test_osc_destinations_go_to_filter(overrides):
    for n in (1, 2, 3):
        assert overrides[f"Osc{n}Destination"] == (2.0, "DF 0 Fil 100")


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
    # -> F2 stays filter 2 'Active', former = Bypass, routing 'Parallel'
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A010_20261108_233057.bin"))
    assert parsed["params"]["Filter Routing"] == 0
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FilterFormerRouting"] == (2.0, "Parallel")
    assert ov["DigiFormerType"] == (0.0, "Bypass")
    assert ov["DigiFormerAmount"][0] == 0.0
    assert ov["Filter2State"] == (0.0, "Active")
    # F2-Cutoff/Reso land on the filter2 stage (stays active)
    assert "Filter2CutOff" in ov and "Filter2Reso" in ov


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
    assert overrides["Filter12Type"] == (3.0, "24dB LP")
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
        1: (17.0, 1.0, 0.5 + (84 - 64) / 254),    # AfterTouch (17) -> Pitch
        2: (17.0, 3.0, 0.5 + (43 - 64) / 254),    # AfterTouch -> Osc2 Pitch
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


def test_filter_direct_mod_source_mapped_to_extra_matrix_slot(overrides):
    # Blofeld "Filter 1 Mod Source = Mod Wheel, Mod Amount = 111" -> next free slot (7) -> Filter1 Cutoff
    assert overrides["MatrixSrc7"][0] == 14.0
    assert overrides["MatrixDst7"][0] == 109.0
    assert overrides["MatrixAmount7"][0] == pytest.approx(0.5 + (111 - 64) / 254)


def test_amp_velocity_maps_to_velocity_volume_slot(overrides):
    # Blofeld Amplifier Velocity 64 (unipolar): AmpVeloAmount = norm(64) = 0.5039.
    # Matrix amount is bipolar centered at 0.5 -> 0.5 + 0.5*norm = 0.752
    # (0.5 would be neutral/ineffective! bipolar trap 2026-11-09)
    assert overrides["AmpVeloAmount"][0] == pytest.approx(64 / 127)
    assert overrides["MatrixSrc8"][0] == 33.0    # Velocity (runtime)
    assert overrides["MatrixDst8"][0] == 152.0   # Volume (runtime)
    assert overrides["MatrixAmount8"][0] == pytest.approx(0.5 + 0.5 * 64 / 127)
    assert overrides["MatrixOnOff8"][0] == 1.0
    # A043 also has Amplifier Mod Source=LFO 3 (slot 9 -> Volume) and
    # Osc Pitch Source=LFO1*MW (slot 10 -> Wheel -> Pitch)
    assert overrides["MatrixSrc9"][0] == 9.0     # LFO 3
    assert overrides["MatrixDst9"][0] == 152.0   # Volume
    assert overrides["MatrixSrc10"][0] == 14.0   # Wheel (LFO1*MW)
    assert overrides["MatrixDst10"][0] == 1.0    # Pitch


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


# --- P0 2026-11-15 (docs/ANALYSIS-2026-11-15-conversion-fixes.md) ---

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
    assert ov["MatrixSrc1"][0] == 17.0   # A043 M1: LFO2*Press -> Pitch
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


def test_osc_pan_always_center_balance_is_not_pan():
    # Finding 2026-11-15 (user, stereo image): Blofeld 'Mixer Osc N Balance' is the
    # F1/F2 share (MAPPING-MASTER, warning), NOT a stereo pan. A043 Balance=0 -> OscNPan 0.0
    # = hard left on the Iridium. Fix: pan always center 0.5; balance goes to the unmapped log
    # (later maybe OscNDestination in parallel).
    for loc, dump in DUMPS_9.items():
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / dump))
        ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
        for n in (1, 2, 3):
            assert ov[f"Osc{n}Pan"][0] == pytest.approx(0.5), f"{loc} Osc{n}Pan"
        assert any("Mixer Osc 1 Balance" in u for u in unmapped), loc


# --- 2026-11-18 rebuild: sync, serial F2 remap, FX by type, detune centering ---

def test_osc2_sync_mapped_a071_a008_not_a001():
    # P1-1: Blofeld "Osc 2 Sync to O3" -> Osc2WaveformSync (was unmapped, A071 "no sync")
    for loc in ("A071", "A008"):
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9[loc]))
        assert parsed["params"]["Osc 2 Sync to O3"] == 1
        ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
        assert ov["Osc2WaveformSync"][0] == 1.0, loc
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
    # bipolar centered: 0.5 + (126-64)/254 = 0.744
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A008"]))
    assert parsed["params"]["Osc 1 Detune"] == 126
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1FinePitch"][0] == pytest.approx(0.5 + (126 - 64) / 254)
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


def test_reverb_fx2_mix_via_matrix_slot_and_params():
    # FX2=Reverb: no ReverbDryWet key -> mix via Constant -> 'FX2 DryWet' (144),
    # ReverbColor from p2 (Shape), ReverbTime from p3 (Decay), spec 5.9
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A039"]))
    parsed["params"]["Effect 2 Type"] = "Reverb"
    parsed["params"]["Effect 2 Mix"] = 64
    parsed["params"]["Effect 2 Parameter 2"] = 100   # Shape
    parsed["params"]["Effect 2 Parameter 3"] = 80    # Decay
    ov, unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FX2Type"][1] == "Reverb" and ov["FX2Type"][0] == 6.0   # runtime enum
    assert ov["ReverbTime"][0] == pytest.approx(80 / 127)
    assert ov["ReverbColor"][0] == pytest.approx(100 / 127)
    dw = [k for k in ov if k.startswith("MatrixDst") and ov[k][1] == "FX2 DryWet"]
    assert dw and all(ov[k][0] == 144.0 for k in dw)
    amt = ov[dw[0].replace("Dst", "Amount")][0]
    assert amt == pytest.approx(0.5 + 0.5 * 64 / 127)
    assert not any("Mix for Reverb" in u for u in unmapped)


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
    assert ov["Osc3Pan"][0] == pytest.approx(96 / 127)     # Balance bipolar -> Pan
    assert ov["Osc3Destination"][0] == 2.0                 # wie die anderen Oscs ins Filter
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
    assert ov["MatrixDst2"][1] == "Osc3 Pan"
    assert not any("Noise" in u for u in un)
