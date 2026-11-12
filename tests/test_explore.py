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


# ---- Task 2: CSV-State, pending, book_row, Log ----

CCSV = (
    "cc,pid,iridium_param,zugehoeriger_blofeld_param,nutzung_pct,essential,pid_quelle,os4_verified\n"
    "0,966,Filter1 Cutoff,Filter 1 Cutoff,93.8,yes,rdb2023,nein\n"
    "2,967,Filter1 Reso,Filter 1 Resonance,78.9,yes,rdb2023,nein\n"
    "7,969,Filter1 Amount,Filter 1 Env Amount,-,,rdb2023,nein\n"
    "22,1642,Delay Dry Wet,Effect 2 Mix,78.9,,rdb2023,nein\n"
)


def _write_csv(tmp_path, content=CCSV):
    p = tmp_path / "cc_list.csv"
    p.write_text(content, encoding="utf-8")
    return p


def test_csv_roundtrip_appends_columns_and_bak(tmp_path):
    import csv
    from bloridium.explore import NEW_COLUMNS, load_cc_list, save_cc_list
    p = _write_csv(tmp_path)
    fieldnames, rows = load_cc_list(p)
    assert not any(c in fieldnames for c in NEW_COLUMNS)   # alte CSV: 8 Spalten
    assert rows[0]["pid_os4"] == ""                        # fehlende neue Spalten = leer
    save_cc_list(p, fieldnames, rows, backup=True)
    with open(p, newline="", encoding="utf-8") as f:
        new_fields = csv.DictReader(f).fieldnames
    assert len(new_fields) == 14 and new_fields[-len(NEW_COLUMNS):] == NEW_COLUMNS
    bak = p.parent / (p.name + ".bak")
    assert bak.exists()
    with open(bak, newline="", encoding="utf-8") as f:
        assert len(csv.DictReader(f).fieldnames) == 8       # Backup behaelt altes Format
    fieldnames2, rows2 = load_cc_list(p)
    assert rows2[0]["cc"] == "0" and rows2[0]["pid"] == "966"   # alte Werte unveraendert


def test_pending_rows_filter_and_sort(tmp_path):
    from bloridium.explore import load_cc_list, pending_rows
    _, rows = load_cc_list(_write_csv(tmp_path))
    assert [int(r["cc"]) for r in pending_rows(rows)] == [0, 2, 22, 7]   # essential first, nutzung desc, "-" zuletzt
    assert [int(r["cc"]) for r in pending_rows(rows, essential=True)] == [0, 2]
    assert [int(r["cc"]) for r in pending_rows(rows, grep="reso")] == [2]
    assert [int(r["cc"]) for r in pending_rows(rows, only_cc="0,22")] == [0, 22]
    rows[0]["os4_verified"] = "ja"
    assert 0 not in [int(r["cc"]) for r in pending_rows(rows)]           # verifiziert = nicht mehr pending


def test_book_row_winner_pid(tmp_path):
    from bloridium.explore import book_row, load_cc_list
    _, rows = load_cc_list(_write_csv(tmp_path))
    row = rows[0]  # cc=0, pid=966
    entry = book_row(row, [(966, 100), (966, 200), (3113, 16383)], "2026-11-12T10:00:00+00:00")
    assert row["pid_os4"] == "966" and row["os4_verified"] == "ja"
    assert row["nrpn_min"] == "100" and row["nrpn_max"] == "200"
    assert row["nrpn_last"] == "200" and row["explore_msgs"] == "2"
    assert row["explore_ts"] == "2026-11-12T10:00:00+00:00"
    assert entry["pid_os4"] == 966 and entry["abweichung"] is False
    assert entry["n_msgs"] == 2 and entry["werte"] == [100, 200] and entry["alle_pids"] == [966, 3113]
    _, rows2 = load_cc_list(_write_csv(tmp_path))
    entry2 = book_row(rows2[0], [(1024, 5)], "ts")
    assert entry2["pid_os4"] == 1024 and entry2["abweichung"] is True   # rdb-Pid 966 != 1024


def test_append_log_jsonl(tmp_path):
    import json
    from bloridium.explore import append_log
    log = tmp_path / "recordings" / "explore_log.jsonl"
    append_log(log, {"pid_os4": 966, "n": 1})
    append_log(log, {"pid_os4": 1024, "n": 2})
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert [json.loads(l)["pid_os4"] for l in lines] == [966, 1024]


# ---- Task 3: CLI explore ----

import json


class _FakeIn:
    """Liefert Messages erst, nachdem das erste input() kam (wie echt: Dreh nach dem Prompt)."""

    def __init__(self, msgs):
        self._msgs = list(msgs)
        self.release = False
        self.closed = False

    def poll(self):
        if not self.release:
            return None
        return self._msgs.pop(0) if self._msgs else None

    def close(self):
        self.closed = True


def _nrpn_seq(pid, values, ch=5):
    msb, lsb = pid >> 7, pid & 0x7F
    msgs = []
    for v in values:
        msgs += [_cc(99, msb, ch), _cc(98, lsb, ch), _cc(6, v >> 7, ch), _cc(38, v & 0x7F, ch)]
    return msgs


def _run_explore(monkeypatch, tmp_path, argv_extra, inp_msgs, inputs):
    from bloridium import cli, midi
    csv_p = _write_csv(tmp_path)
    log_p = tmp_path / "explore_log.jsonl"
    fake = _FakeIn(inp_msgs)
    monkeypatch.setattr(midi, "open_input", lambda port: ("FAKE-IN", fake))

    def _input(prompt=""):
        fake.release = True
        return next(inputs)

    monkeypatch.setattr("builtins.input", _input)
    rc = cli.main(["explore", "--csv", str(csv_p), "--log", str(log_p),
                   "--listen", "0.02", *argv_extra])
    return rc, csv_p, log_p, fake


def test_midi_open_input_matches_port(monkeypatch):
    import mido
    from bloridium import midi
    monkeypatch.setattr(mido, "get_input_names", lambda: ["Launchpad Pro MK3 LPProMK3 DIN", "Other"])
    opened = {}
    monkeypatch.setattr(mido, "open_input", lambda name: opened.setdefault("name", name))
    name, _ = midi.open_input("launchpad")   # case-insensitiver Teilstring
    assert name == "Launchpad Pro MK3 LPProMK3 DIN" and opened["name"] == name


def test_explore_list_text_and_json(tmp_path, capsys):
    from bloridium import cli
    csv_p = _write_csv(tmp_path)
    rc = cli.main(["explore", "--csv", str(csv_p), "--list"])
    out = capsys.readouterr().out
    assert rc == 0 and "Filter1 Cutoff" in out and "966" in out and "nein" in out
    rc = cli.main(["--json", "explore", "--csv", str(csv_p), "--list"])
    rows = json.loads(capsys.readouterr().out)
    assert rc == 0 and len(rows) == 4
    assert rows[0]["cc"] == "0" and rows[0]["iridium_param"] == "Filter1 Cutoff"


def test_explore_session_books_and_logs(tmp_path, capsys, monkeypatch):
    rc, csv_p, log_p, fake = _run_explore(
        monkeypatch, tmp_path, [], _nrpn_seq(1024, [100, 200]), iter(["", "q"]))
    out = capsys.readouterr().out
    assert rc == 0 and fake.closed
    assert "ABWEICHUNG" in out and "1024" in out          # rdb-Pid 966 != 1024
    from bloridium.explore import load_cc_list
    _, rows = load_cc_list(csv_p)
    r0 = next(r for r in rows if r["cc"] == "0")
    assert r0["os4_verified"] == "ja" and r0["pid_os4"] == "1024"
    assert r0["nrpn_min"] == "100" and r0["nrpn_max"] == "200" and r0["nrpn_last"] == "200"
    assert (tmp_path / "cc_list.csv.bak").exists()
    entries = [json.loads(l) for l in log_p.read_text(encoding="utf-8").strip().splitlines()]
    assert len(entries) == 1 and entries[0]["abweichung"] is True and entries[0]["pid_os4"] == 1024


def test_explore_session_sends_nothing(tmp_path, monkeypatch):
    import mido

    def _boom(*a, **k):
        raise AssertionError("explore darf kein MIDI-Out oeffnen/senden")

    monkeypatch.setattr(mido, "open_output", _boom)
    rc, *_ = _run_explore(monkeypatch, tmp_path, [], _nrpn_seq(966, [1]), iter(["", "q"]))
    assert rc == 0


def test_explore_empty_capture_hints_and_stays(tmp_path, capsys, monkeypatch):
    rc, csv_p, log_p, _ = _run_explore(
        monkeypatch, tmp_path, [], [_cc(20, 99)], iter(["", "q"]))   # nur CC, kein NRPN
    out = capsys.readouterr().out
    assert rc == 0
    assert "kein NRPN" in out and "Send NRPN" in out
    from bloridium.explore import load_cc_list
    _, rows = load_cc_list(csv_p)
    assert all(r["os4_verified"] == "nein" for r in rows)   # nichts gebucht
    assert not log_p.exists()


def test_explore_no_in_port_exit_2(tmp_path, capsys, monkeypatch):
    from bloridium import cli, midi

    def _raise(port):
        raise RuntimeError("MIDI-Port nicht gefunden: 'X'")

    monkeypatch.setattr(midi, "open_input", _raise)
    csv_p = _write_csv(tmp_path)
    rc = cli.main(["explore", "--csv", str(csv_p), "--log", str(tmp_path / "l.jsonl")])
    err = capsys.readouterr().err
    assert rc == 2 and "FEHLER" in err and "MIDI-Ports IN" in err
