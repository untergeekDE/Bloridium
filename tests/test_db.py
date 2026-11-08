"""Task 2: SQLite-Bank – Schema v1 + CRUD-Helfer (bloridium/db.py)."""

import pytest


def _sound_row(loc, bank, slot, name):
    return {
        "location": loc, "bank": bank, "slot": slot, "name": name,
        "category": "Bass", "sndd_path": f"dumps/banks/{bank}/{loc}.bin",
        "parsed_json": {"name": name}, "dumped_at": "2026-11-08T13:00:00", "source": "test",
    }


def test_connect_creates_all_tables_and_schema_version(db_path):
    from bloridium import db

    conn = db.connect(db_path)
    tables = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"meta", "sounds", "qpats", "conversions", "ab_runs"} <= tables
    meta = dict(conn.execute("SELECT key, value FROM meta"))
    assert int(meta["schema_version"]) == db.SCHEMA_VERSION == 1


def test_upsert_and_get_sound(db_path):
    from bloridium import db

    conn = db.connect(db_path)
    db.upsert_sound(conn, _sound_row("A043", "A", 43, "SH Power"))
    got = db.get_sound(conn, "A043")
    assert got["name"] == "SH Power"
    assert got["parsed_json"] == {"name": "SH Power"}  # Wert JSON-dekodiert, Key = Spaltenname
    db.upsert_sound(conn, _sound_row("A043", "A", 43, "SH Power v2"))
    assert db.get_sound(conn, "A043")["name"] == "SH Power v2"
    assert db.get_sound(conn, "B001") is None


def test_list_sounds_filters_by_bank_and_grep(db_path):
    from bloridium import db

    conn = db.connect(db_path)
    for args in [("A043", "A", 43, "SH Power"), ("A001", "A", 1, "Init"),
                 ("B010", "B", 10, "Power Bass")]:
        db.upsert_sound(conn, _sound_row(*args))
    assert len(db.list_sounds(conn)) == 3
    assert [s["location"] for s in db.list_sounds(conn, bank="A")] == ["A001", "A043"]
    assert [s["location"] for s in db.list_sounds(conn, grep="power")] == ["A043", "B010"]


def test_qpat_register_and_list(db_path):
    from bloridium import db

    conn = db.connect(db_path)
    pid = db.register_qpat(conn, "transfer/X.qpat", {"name": "X", "params": {"Osc1Type": {"value": 1.0, "display": "Waveform"}}}, source="transfer")
    assert pid >= 1
    qpats = db.list_qpats(conn)
    assert len(qpats) == 1
    assert qpats[0]["path"] == "transfer/X.qpat"
    assert qpats[0]["params_json"]["Osc1Type"]["value"] == 1.0  # dekodiert


def test_conversions_insert_and_list_by_sound(db_path):
    from bloridium import db

    conn = db.connect(db_path)
    db.insert_conversion(conn, "A043", "transfer/SH Power_A043.qpat", 80, ["Osc 1 Keytrack", "Filter Routing"])
    db.insert_conversion(conn, "A001", "transfer/Init_A001.qpat", 10, [])
    rows = db.list_conversions(conn, sound="A043")
    assert len(rows) == 1
    assert rows[0]["mapped"] == 80
    assert rows[0]["unmapped_json"] == ["Osc 1 Keytrack", "Filter Routing"]  # dekodiert
    assert len(db.list_conversions(conn)) == 2


def test_ab_runs_insert_list_filter_get(db_path):
    from bloridium import db

    conn = db.connect(db_path)
    r1 = db.insert_ab_run(conn, "shpower", "A043", 36, 3.0, "recordings/r1.json", "b.npy", "i.npy", {"delta": 1.0})
    r2 = db.insert_ab_run(conn, "other", None, 60, 2.0, "recordings/r2.json", "b2.npy", "i2.npy", {"delta": 2.0})
    assert r1 != r2
    assert [r["label"] for r in db.list_ab_runs(conn, sound="A043")] == ["shpower"]
    assert len(db.list_ab_runs(conn)) == 2
    got = db.get_ab_run(conn, r1)
    assert got["sound_location"] == "A043"
    assert got["report_json"] == {"delta": 1.0}  # dekodiert
