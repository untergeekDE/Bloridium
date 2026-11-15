"""Mapping-Erweiterung: Routing (Osc->Fil 100; seriell 'Filter > Former' mit F2 im
DigiFormer, parallel 'Parallel' mit F2 als Filter 2), Version 14,
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


def test_osc_octave_sign_a001():
    # A001 JMX jun: Osc 3 Octave raw 52 = -12 semi (16') -> CoarsePitch 24-12 = 12.0,
    # NICHT 24+12 = 36.0 (Vorzeichen-Bug 2026-11-14: 64-raw statt raw-64).
    # Osc 1/2 Octave raw 64 (8') -> 24.0.
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    assert parsed["params"]["Osc 3 Octave"] == 52
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1CoarsePitch"][0] == pytest.approx(24.0)
    assert ov["Osc2CoarsePitch"][0] == pytest.approx(24.0)
    assert ov["Osc3CoarsePitch"][0] == pytest.approx(12.0)


def test_waveform_pw_neutral_for_non_pulse_a001():
    # A001: Osc1/2 Shape 'Saw', Pulsewidth raw 100 – Blofeld: PW ohne Funktion bei Saw.
    # Iridium WaveformPW ist Warp (wirkt auch bei Saw) -> muss neutral 0.5 sein,
    # nicht norm(100)=0.7874 (Rechteck statt Saegezahn, Befund 2026-11-14).
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    assert parsed["params"]["Osc 1 Shape"] == "Saw"
    assert parsed["params"]["Osc 1 Pulsewidth"] == 100
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1WaveformPW"][0] == pytest.approx(0.5)
    assert ov["Osc2WaveformPW"][0] == pytest.approx(0.5)


def test_waveform_pw_pulse_shape_scales_half():
    # Blofeld Shape 'Pulse': raw 127 = 50% Pulsweite -> Iridium PW 0.5; raw 64 -> norm*0.5
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    parsed["params"]["Osc 1 Shape"] = "Pulse"
    parsed["params"]["Osc 1 Pulsewidth"] = 127
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1WaveformPW"][0] == pytest.approx(0.5)
    parsed["params"]["Osc 1 Pulsewidth"] = 64
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Osc1WaveformPW"][0] == pytest.approx(64 / 127 * 0.5)


def test_cutoff_semitone_anchor_not_linear_norm():
    # Blofeld-Manual: Cutoff raw 64 = 440 Hz (Halbtonschritte). Iridium-Kalib:
    # norm = (log10(440) - 0.9117)/3.387 = 0.5112 -- NICHT norm(64) = 0.5039 (Befund 2026-11-14)
    import math
    from bloridium.qpat_map import blofeld_cutoff_norm
    assert blofeld_cutoff_norm(64) == pytest.approx((math.log10(440.0) - 0.9117) / 3.387, abs=1e-4)
    assert blofeld_cutoff_norm(64) == pytest.approx(0.5112, abs=0.001)
    assert blofeld_cutoff_norm(64) != pytest.approx(64 / 127)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["Filter1CutOff"][0] == pytest.approx(blofeld_cutoff_norm(64))
    assert ov["DigiFormerAmount"][0] == pytest.approx(blofeld_cutoff_norm(52))
    # seriell (A001 Routing=1): zusaetzlicher Matrix-Slot Filter1 Env -> DF Amount,
    # sonst bleibt der Former statisch zu (Befund 2026-11-14: -66 dBFS)
    df_slots = [k for k, v in ov.items() if k.startswith("MatrixDst") and v[1] == "DF Amount"]
    assert df_slots, "seriell braucht Filter1 Env -> DF Amount Slot"


def test_cutoff_parallel_has_no_df_env_slot(overrides):
    # A043 parallel: F2 bleibt Filter2 (Active) -> kein DF-Env-Slot noetig
    assert not [k for k, v in overrides.items()
                if k.startswith("MatrixDst") and v[1] == "DF Amount"]


def test_waveform_kernels_off_a001():
    # "Kernels Count" (OS4-Display fuer OscNWaveformDesity): Blofeld hat keinen Kernel-
    # Parameter -> 0.0 = 1 Welle. Template-Default 0.22 zeigte A001 OSC2 als "Kernels 2.5".
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A001_20261108_233049.bin"))
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    for n in (1, 2, 3):
        assert ov[f"Osc{n}WaveformDesity"][0] == pytest.approx(0.0)


def test_filter_former_routing_parallel_a043(overrides):
    # A043 SH Power: Blofeld Filter Routing = 0 (parallel) -> Iridium 'Parallel' (2.0),
    # NICHT 'Filter > Former' (Befund HANDOVER 2026-11-14)
    assert overrides["FilterFormerRouting"] == (2.0, "Parallel")


def test_seriell_routing_f2_to_former_link_single():
    # A008 Easy Piano: Filter Routing = 1 (seriell), F2 = LP 24dB -> DigiFormer 'Nave LP24',
    # Filter2State 'Off', FilterLink 'Single' – 'Linked' (7.0) machte B stumm (HANDOVER 2026-11-14)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A008_20261108_233053.bin"))
    assert parsed["params"]["Filter Routing"] == 1
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FilterFormerRouting"] == (1.0, "Filter > Former")
    assert ov["DigiFormerType"] == (7.0, "Nave LP24")
    assert ov["Filter2State"] == (2.0, "Off")
    assert ov["FilterLink"] == (0.0, "Single")
    assert ov["FilterLink"][0] != 7.0  # nicht 'Linked'


def test_parallel_routing_f2_stays_filter2_active():
    # A010 Wurly Piano: Filter Routing = 0 (parallel), F2 = LP 24dB (nicht Bypass)
    # -> F2 bleibt Filter 2 'Active', Former = Bypass, Routing 'Parallel'
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / "dumps/blofeld_sndd_A010_20261108_233057.bin"))
    assert parsed["params"]["Filter Routing"] == 0
    ov, _unmapped = qpat_map.blofeld_to_qpat_params(parsed)
    assert ov["FilterFormerRouting"] == (2.0, "Parallel")
    assert ov["DigiFormerType"] == (0.0, "Bypass")
    assert ov["DigiFormerAmount"][0] == 0.0
    assert ov["Filter2State"] == (0.0, "Active")
    # F2-Cutoff/Reso landen auf der Filter2-Stufe (bleibt aktiv)
    assert "Filter2CutOff" in ov and "Filter2Reso" in ov


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
    assert overrides["MatrixDst8"][0] == 115.0   # Volume (v14; v8-Slot 112 ist v9 Filt1Env Sustain)
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


def test_matrix_dst_enum_ist_v14():
    # v14-OS4-Exporte (dumps/export-0*/*.qpat): DF Amount=95, Filter2 Cutoff=104,
    # Filter2 Reso=105; 71/103 kommen in v14 NICHT vor (v8: 71='DF Amount', 103='FX1 Control')
    assert qpat_map.MATRIX_DST["DF Amount"] == 95.0
    assert qpat_map.MATRIX_DST["Filter2 Cutoff"] == 104.0
    assert qpat_map.MATRIX_DST["Filter2 Reso"] == 105.0


def test_serieller_df_env_slot_dst_v14():
    # Seriell (A001): Slot Filter1 Env -> DF Amount muss in v14 auf dst 95.0 landen,
    # sonst oeffnet der DigiFormer nicht -> serielle Patches zu dunkel/leise (bis -64.8 dBFS)
    parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / DUMPS_9["A001"]))
    ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
    df_slots = [k for k, v in ov.items() if k.startswith("MatrixDst") and v[1] == "DF Amount"]
    assert df_slots, "seriell braucht Filter1 Env -> DF Amount Slot"
    for k in df_slots:
        assert ov[k][0] == 95.0, f"{k} dst muss v14-Wert 95.0 sein"


def test_aftertouch_do_poly_mono_alle_9():
    # Blofeld sendet Channel AT; Template-Default AfterTouchDoPoly=1.0 ist Poly AT ->
    # Matrix-Src 'After Touch' reagiert nicht auf Channel AT (A019/A043, P0-2).
    for loc, dump in DUMPS_9.items():
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / dump))
        ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
        assert "AfterTouchDoPoly" in ov, loc
        assert ov["AfterTouchDoPoly"][0] == 0.0, loc


def test_kein_v8_enum_leck_in_v14_qpat_alle_9():
    # v8-Template-Slots, die das Mapping nicht ueberschreibt, duerfen keine v8-Enum-Werte
    # (z. B. MatrixDst 71 'DF Amount', 103) in die v14-Datei schreiben (P0-1, A008: [71, 95])
    tpl = qpat.load(REPO / TEMPLATE)
    V8_ONLY_DST = {71.0, 74.0, 72.0, 73.0, 75.0, 76.0, 103.0, 112.0, 145.0}
    for loc, dump in DUMPS_9.items():
        parsed = bd.parse_sndd(workflow.load_sndd_file(REPO / dump))
        ov, _ = qpat_map.blofeld_to_qpat_params(parsed)
        merged = qpat_map.apply_to_template(tpl, ov, name=parsed["name"])
        for k, (val, _disp) in merged["params"].items():
            if k.startswith("MatrixDst"):
                assert val not in V8_ONLY_DST, f"{loc}: {k}={val} ist v8-Enum in v14"
