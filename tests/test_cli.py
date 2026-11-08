"""Task 5: CLI-Subcommands – offline getestet (monkeypatchte midi/audio, tmp-DB)."""

import json
from pathlib import Path

import numpy as np
import pytest

DUMP_BIN = "dumps/blofeld_sndd_A043_20261108_135516.bin"
QPAT_0 = "dumps/export-001/00000-NotSoGrand.qpat"
TEMPLATE = "docs/refs/qpat/template_waveform.qpat"


def run(cli, db_path, *argv):
    return cli.main(["--db", str(db_path), *argv])


# ---- bank import / list / show ----

def test_bank_import_populates_db(repo, db_path, tmp_path, capsys):
    from bloridium import cli, db

    rc = run(cli, db_path, "bank", "import", str(repo / "dumps"),
             "--banks-dir", str(tmp_path / "banks"))
    assert rc == 0
    conn = db.connect(db_path)
    s = db.get_sound(conn, "A043")
    assert s is not None and s["name"] == "SH Power"
    assert Path(s["sndd_path"]).exists()  # stabile Kopie unter banks-dir


def test_bank_list_json_and_missing_marker(repo, db_path, tmp_path, capsys):
    from bloridium import cli, db

    run(cli, db_path, "bank", "import", str(repo / "dumps"), "--banks-dir", str(tmp_path / "banks"))
    capsys.readouterr()
    rc = run(cli, db_path, "--json", "bank", "list")
    assert rc == 0
    rows = json.loads(capsys.readouterr().out)
    assert any(r["location"] == "A043" and r["missing"] is False for r in rows)

    conn = db.connect(db_path)
    Path(db.get_sound(conn, "A043")["sndd_path"]).unlink()  # Datei weg
    rc = run(cli, db_path, "bank", "list")
    assert rc == 0
    out = capsys.readouterr().out
    assert "A043" in out and "FEHLT" in out


def test_bank_show_prints_params(repo, db_path, tmp_path, capsys):
    from bloridium import cli

    run(cli, db_path, "bank", "import", str(repo / "dumps"), "--banks-dir", str(tmp_path / "banks"))
    capsys.readouterr()
    assert run(cli, db_path, "bank", "show", "A043") == 0
    assert "SH Power" in capsys.readouterr().out


# ---- convert ----

def test_convert_from_dump_writes_qpat_and_db_row(repo, db_path, tmp_path, capsys):
    from bloridium import cli, db, qpat

    out_dir = tmp_path / "transfer"
    rc = run(cli, db_path, "convert", "A043", "--dump", str(repo / DUMP_BIN), "--out", str(out_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "unmapped" in out.lower()
    files = list(out_dir.glob("*_A043.qpat"))
    assert len(files) == 1
    q = qpat.load(files[0])
    assert "Osc1Type" in q["params"]
    conn = db.connect(db_path)
    conv = db.list_conversions(conn, sound="A043")
    assert len(conv) == 1 and conv[0]["mapped"] > 0 and len(conv[0]["unmapped_json"]) > 0
    assert db.get_sound(conn, "A043")["name"] == "SH Power"


def test_convert_live_without_hardware_exits_2(repo, db_path, monkeypatch, capsys):
    from bloridium import cli, midi

    monkeypatch.setattr(midi, "list_ports", lambda: {"in": [], "out": ["SomePort"]})

    def boom(name, ports=None):
        raise RuntimeError(f"MIDI-Port nicht gefunden: {name}")

    monkeypatch.setattr(midi, "connect", boom)
    rc = run(cli, db_path, "convert", "A043")
    assert rc == 2
    err = capsys.readouterr().err
    assert "SomePort" in err  # verfügbare Ports in der Fehlermeldung


# ---- qpat info ----

def test_qpat_info_register(repo, db_path, capsys):
    from bloridium import cli, db

    rc = run(cli, db_path, "qpat", "info", str(repo / QPAT_0), "--register")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Roundtrip: OK" in out
    conn = db.connect(db_path)
    assert any(q["path"].endswith("00000-NotSoGrand.qpat") for q in db.list_qpats(conn))


# ---- edit ----

def test_edit_set_inplace_creates_bak(repo, db_path, tmp_path):
    import shutil

    from bloridium import cli, qpat

    f = tmp_path / "tmpl.qpat"
    shutil.copy(repo / TEMPLATE, f)
    rc = run(cli, db_path, "edit", str(f), "--set", "Osc1Type=0.25", "--display", "X")
    assert rc == 0
    assert qpat.load(f)["params"]["Osc1Type"]["value"] == 0.25
    assert qpat.load(f)["params"]["Osc1Type"]["display"] == "X"
    assert Path(str(f) + ".bak").exists()


# ---- ab list / diff / measure ----

def test_ab_list_empty_and_diff(db_path, capsys):
    from bloridium import cli, db

    assert run(cli, db_path, "ab", "--list") == 0
    conn = db.connect(db_path)
    rep = {"band_edges_hz": [40, 100, 12000], "band_delta_db": [1.0, 2.0],
           "blofeld": {}, "iridium": {}}
    db.insert_ab_run(conn, "r1", None, 36, 3.0, "a.json", "b.npy", "i.npy", rep)
    db.insert_ab_run(conn, "r2", None, 36, 3.0, "c.json", "d.npy", "e.npy",
                     {**rep, "band_delta_db": [3.0, 4.0]})
    capsys.readouterr()
    assert run(cli, db_path, "ab", "--diff", "1", "2") == 0
    assert "dB" in capsys.readouterr().out


class FakeSynth:
    def __init__(self, name):
        self.name = name
        self.channel = 4
        self.events = []

    def control_change(self, c, v, channel=None):
        self.events.append(("cc", c, channel))

    def note_on(self, note=60, velocity=100, channel=None):
        self.events.append(("on", note))

    def note_off(self, note=60, velocity=0, channel=None):
        self.events.append(("off", note))

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_ab_measure_sends_all_notes_off_before_note(db_path, tmp_path, monkeypatch, capsys):
    from bloridium import audio, cli, db, midi, workflow

    fakes = {"blofeld": FakeSynth("blofeld"), "iridium": FakeSynth("iridium")}
    monkeypatch.setattr(midi, "connect", lambda name, ports=None: fakes[name])
    monkeypatch.setattr(audio, "record",
                        lambda duration=2.0, channels=None, **kw: np.zeros((20, 4800), dtype=np.float32))
    monkeypatch.setattr(workflow.time, "sleep", lambda *a, **k: None)

    rc = run(cli, db_path, "ab", "--note", "36", "--dur", "0.1", "--label", "t",
             "--sound", "A043", "--rec-dir", str(tmp_path))
    assert rc == 0
    for fake in fakes.values():
        first_on = next(i for i, e in enumerate(fake.events) if e[0] == "on")
        cc123 = [e for e in fake.events[:first_on] if e == ("cc", 123, e[2])]
        assert {e[2] for e in cc123} == set(range(16))  # CC123 auf allen 16 Kanaelen vor NoteOn
    conn = db.connect(db_path)
    runs = db.list_ab_runs(conn, sound="A043")
    assert len(runs) == 1 and runs[0]["note"] == 36


# ---- status ----

def test_status_without_ports_exits_2(db_path, monkeypatch, capsys):
    from bloridium import cli, midi

    monkeypatch.setattr(midi, "list_ports", lambda: {"in": [], "out": ["Blofeld", "Iridium X"]})

    def boom(name, ports=None):
        raise RuntimeError(f"MIDI-Port nicht gefunden: {name}")

    monkeypatch.setattr(midi, "connect", boom)
    rc = run(cli, db_path, "status")
    assert rc == 2
    err = capsys.readouterr().err
    assert "Blofeld" in err and "Iridium X" in err
