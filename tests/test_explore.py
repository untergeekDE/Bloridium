"""Task 1-3: bloridium.explore – NRPN-Decoder, CSV-State, CLI-Subcommand (offline, kein Live-MIDI)."""

import mido


def test_decoder_mitschnitt_pid3113():
    from bloridium.explore import NrpnDecoder
    d = NrpnDecoder()
    msgs = [mido.Message("control_change", control=c, value=v, channel=5)
            for c, v in [(99, 0x18), (98, 0x29), (6, 0x7F), (38, 0x7F)]]
    events = [d.feed(m) for m in msgs]
    assert [e for e in events if e] == [(3113, 16383)]  # (0x18<<7)|0x29, (0x7F<<7)|0x7F


def _cc(c, v, ch=5):
    return mido.Message("control_change", control=c, value=v, channel=ch)


def test_decoder_sweep_multiple_values():
    from bloridium.explore import NrpnDecoder
    d = NrpnDecoder()
    seq = [_cc(99, 0x08), _cc(98, 0x02),        # Pid 1026
           _cc(6, 10), _cc(38, 20),              # Wert 1300
           _cc(6, 50), _cc(38, 60)]              # Wert 6460 (Pid bleibt gesetzt)
    events = [e for e in (d.feed(m) for m in seq) if e]
    assert events == [(1026, 1300), (1026, 6460)]


def test_decoder_reset_cases():
    from bloridium.explore import NrpnDecoder
    d = NrpnDecoder()
    assert d.feed(_cc(99, 0x18)) is None
    assert d.feed(_cc(98, 0x29)) is None
    assert d.feed(_cc(6, 0x7F)) is None
    assert d.feed(_cc(38, 0x7F)) == (3113, 16383)
    d.feed(_cc(99, 127))                         # NRPN aus -> Pid reset
    assert d.feed(_cc(6, 1)) is None
    assert d.feed(_cc(38, 2)) is None            # ohne Pid kein Event
    d.feed(_cc(99, 1)); d.feed(_cc(98, 2))
    d.feed(_cc(121, 0))                          # Reset All Controllers
    assert d.feed(_cc(6, 3)) is None
    assert d.feed(_cc(38, 4)) is None


def test_decoder_ignores_rpn_and_non_cc():
    from bloridium.explore import NrpnDecoder
    d = NrpnDecoder()
    assert d.feed(mido.Message("note_on", note=60, velocity=100, channel=5)) is None
    assert d.feed(_cc(101, 0)) is None           # RPN MSB
    assert d.feed(_cc(100, 0)) is None           # RPN LSB
    assert d.feed(_cc(20, 99)) is None           # anderer CC
    d.feed(_cc(99, 1)); d.feed(_cc(98, 2))
    assert d.feed(_cc(101, 0)) is None           # RPN stoert nicht mitten im NRPN
    assert d.feed(_cc(6, 5)) is None
    assert d.feed(_cc(38, 6)) == (130, 646)      # (1<<7)|2 = 130, (5<<7)|6 = 646
