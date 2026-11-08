"""bloridium cc – Live-CC am Iridium/Blofeld per Namen aus der midi.guide-CSV."""

import pytest


# ---- ccmap: CSV laden + Namen aufloesen ----

def test_load_cc_map_and_find_exact(repo):
    from bloridium import ccmap

    table = ccmap.load_cc_map(repo / "docs/midi-maps/iridium_midi_guide.csv")
    cc, name = ccmap.find_cc("Filter1 Reso", table)
    assert cc == 2 and name == "Filter1 Reso"


def test_find_cc_case_insensitive_substring(repo):
    from bloridium import ccmap

    table = ccmap.load_cc_map(repo / "docs/midi-maps/iridium_midi_guide.csv")
    cc, name = ccmap.find_cc("filter2 cutoff", table)
    assert cc == 9


def test_find_cc_no_cc_param_raises(repo):
    from bloridium import ccmap

    table = ccmap.load_cc_map(repo / "docs/midi-maps/iridium_midi_guide.csv")
    with pytest.raises(KeyError, match="kein CC"):
        ccmap.find_cc("Filter1 Cutoff", table)  # NRPN-only, Geraet ignoriert NRPN


def test_find_cc_ambiguous_lists_matches(repo):
    from bloridium import ccmap

    table = ccmap.load_cc_map(repo / "docs/midi-maps/iridium_midi_guide.csv")
    with pytest.raises(ValueError, match="mehrdeutig"):
        ccmap.find_cc("Filter1", table)


# ---- cli: cc senden ----

class FakeSynth:
    def __init__(self):
        self.channel = 4
        self.sent = []

    def control_change(self, c, v, channel=None):
        self.sent.append((c, v, channel))

    def close(self):
        pass


def _run_cc(monkeypatch, db_path, *argv):
    from bloridium import cli, midi

    fake = FakeSynth()
    monkeypatch.setattr(midi, "connect", lambda name, ports=None: fake)
    rc = cli.main(["--db", str(db_path), "cc", *argv])
    return rc, fake


def test_cc_by_name_part2_sends_right_channel(db_path, monkeypatch):
    rc, fake = _run_cc(monkeypatch, db_path, "Filter1 Reso", "100", "--part", "2")
    assert rc == 0
    assert fake.sent == [(2, 100, 6)]  # Part 2 = MIDI ch7 = 0-basiert 6


def test_cc_default_part1_channel6(db_path, monkeypatch):
    rc, fake = _run_cc(monkeypatch, db_path, "Filter2 Cutoff", "64")
    assert rc == 0
    assert fake.sent == [(9, 64, 5)]  # Part 1 = MIDI ch6 = 0-basiert 5


def test_cc7_zero_refused_without_force(db_path, monkeypatch, capsys):
    rc, fake = _run_cc(monkeypatch, db_path, "--raw", "7", "0")
    assert rc == 1
    assert fake.sent == []  # nichts gesendet
    assert "stumm" in capsys.readouterr().err.lower() or "Output" in capsys.readouterr().err


def test_cc7_with_force_sends_and_warns(db_path, monkeypatch, capsys):
    rc, fake = _run_cc(monkeypatch, db_path, "--raw", "7", "0", "--force")
    assert rc == 0
    assert fake.sent == [(7, 0, 5)]
    assert "CC7" in capsys.readouterr().out


def test_cc_list_shows_table(db_path, monkeypatch, capsys):
    from bloridium import cli

    rc = cli.main(["--db", str(db_path), "cc", "--list", "--grep", "filter1 reso"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Filter1 Reso" in out and "CC2" in out


def test_cc_unknown_name_exits_1(db_path, monkeypatch, capsys):
    rc, fake = _run_cc(monkeypatch, db_path, "GibtEsNicht", "100")
    assert rc == 1
    assert fake.sent == []
