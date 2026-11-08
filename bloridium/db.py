"""SQLite-Bank fuer Bloridium – Schema v1 + CRUD-Helfer.

Dateien bleiben Source of Truth (dumps/, transfer/, recordings/); die DB
indexiert und cached geparste Daten (siehe Design-Doc, Abschnitt DB-Schema).
JSON-Spalten werden beim Schreiben serialisiert und beim Lesen dekodiert.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS sounds (
  location TEXT PRIMARY KEY,
  bank TEXT NOT NULL,
  slot INTEGER NOT NULL,
  name TEXT NOT NULL,
  category TEXT,
  sndd_path TEXT,
  parsed_json TEXT,
  dumped_at TEXT,
  source TEXT
);
CREATE TABLE IF NOT EXISTS qpats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT UNIQUE NOT NULL,
  name TEXT,
  source TEXT,
  params_json TEXT,
  registered_at TEXT
);
CREATE TABLE IF NOT EXISTS conversions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sound_location TEXT,
  qpat_path TEXT,
  created_at TEXT,
  mapped INTEGER,
  unmapped_json TEXT
);
CREATE TABLE IF NOT EXISTS ab_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  label TEXT,
  sound_location TEXT,
  note INTEGER,
  dur REAL,
  ts TEXT,
  report_path TEXT,
  blofeld_npy TEXT,
  iridium_npy TEXT,
  report_json TEXT
);
"""


def connect(path) -> sqlite3.Connection:
    """DB oeffnen/anlegen, Schema migrieren, Row-Factory auf dict setzen."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO meta(key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),)
        )
        conn.commit()
    elif int(row["value"]) > SCHEMA_VERSION:
        raise RuntimeError(
            f"DB-Schema v{row['value']} ist neuer als unterstuetzt (v{SCHEMA_VERSION})"
        )
    return conn


def _row(r) -> dict | None:
    return dict(r) if r is not None else None


def _decode(row: dict | None, *json_keys: str) -> dict | None:
    if row is None:
        return None
    for k in json_keys:
        if row.get(k) is not None:
            row[k] = json.loads(row[k])
    return row


# ---- sounds ---------------------------------------------------------------

def upsert_sound(conn: sqlite3.Connection, row: dict) -> None:
    """Sound-Zeile upserted (PK location). parsed_json: dict -> JSON."""
    row = dict(row)
    if not isinstance(row.get("parsed_json"), str):
        row["parsed_json"] = json.dumps(row.get("parsed_json") or {})
    conn.execute(
        """
        INSERT INTO sounds(location, bank, slot, name, category, sndd_path,
                           parsed_json, dumped_at, source)
        VALUES (:location, :bank, :slot, :name, :category, :sndd_path,
                :parsed_json, :dumped_at, :source)
        ON CONFLICT(location) DO UPDATE SET
          bank=excluded.bank, slot=excluded.slot, name=excluded.name,
          category=excluded.category, sndd_path=excluded.sndd_path,
          parsed_json=excluded.parsed_json, dumped_at=excluded.dumped_at,
          source=excluded.source
        """,
        row,
    )
    conn.commit()


def get_sound(conn: sqlite3.Connection, loc: str) -> dict | None:
    r = conn.execute("SELECT * FROM sounds WHERE location = ?", (loc,)).fetchone()
    return _decode(_row(r), "parsed_json")


def list_sounds(conn: sqlite3.Connection, bank: str | None = None,
                grep: str | None = None) -> list[dict]:
    q = "SELECT * FROM sounds"
    cond, params = [], []
    if bank:
        cond.append("bank = ?")
        params.append(bank.upper())
    if grep:
        cond.append("(lower(name) LIKE ? OR lower(location) LIKE ?)")
        g = f"%{grep.lower()}%"
        params += [g, g]
    if cond:
        q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY location"
    return [_decode(_row(r), "parsed_json")
            for r in conn.execute(q, params).fetchall()]


# ---- qpats ----------------------------------------------------------------

def register_qpat(conn: sqlite3.Connection, path, parsed: dict,
                  source: str = "transfer") -> int:
    from datetime import datetime, timezone

    p = str(Path(path))
    params_json = json.dumps(parsed.get("params", {}))
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        """
        INSERT INTO qpats(path, name, source, params_json, registered_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
          name=excluded.name, source=excluded.source,
          params_json=excluded.params_json, registered_at=excluded.registered_at
        """,
        (p, parsed.get("name", ""), source, params_json, ts),
    )
    conn.commit()
    return cur.lastrowid


def list_qpats(conn: sqlite3.Connection) -> list[dict]:
    return [_decode(_row(r), "params_json")
            for r in conn.execute("SELECT * FROM qpats ORDER BY path").fetchall()]


# ---- conversions ----------------------------------------------------------

def insert_conversion(conn: sqlite3.Connection, sound_location: str, qpat_path: str,
                      mapped: int, unmapped: list) -> int:
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        """
        INSERT INTO conversions(sound_location, qpat_path, created_at, mapped, unmapped_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (sound_location, str(qpat_path), ts, mapped, json.dumps(unmapped)),
    )
    conn.commit()
    return cur.lastrowid


def list_conversions(conn: sqlite3.Connection, sound: str | None = None) -> list[dict]:
    q = "SELECT * FROM conversions"
    params = []
    if sound:
        q += " WHERE sound_location = ?"
        params.append(sound)
    q += " ORDER BY id DESC"
    return [_decode(_row(r), "unmapped_json")
            for r in conn.execute(q, params).fetchall()]


# ---- ab_runs --------------------------------------------------------------

def insert_ab_run(conn: sqlite3.Connection, label: str, sound_location: str | None,
                  note: int, dur: float, report_path: str, blofeld_npy: str,
                  iridium_npy: str, report_json: dict) -> int:
    from datetime import datetime, timezone

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        """
        INSERT INTO ab_runs(label, sound_location, note, dur, ts, report_path,
                            blofeld_npy, iridium_npy, report_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (label, sound_location, note, dur, ts, str(report_path),
         str(blofeld_npy), str(iridium_npy), json.dumps(report_json)),
    )
    conn.commit()
    return cur.lastrowid


def list_ab_runs(conn: sqlite3.Connection, sound: str | None = None) -> list[dict]:
    q = "SELECT * FROM ab_runs"
    params = []
    if sound:
        q += " WHERE sound_location = ?"
        params.append(sound)
    q += " ORDER BY id DESC"
    return [_decode(_row(r), "report_json")
            for r in conn.execute(q, params).fetchall()]


def get_ab_run(conn: sqlite3.Connection, run_id: int) -> dict:
    r = conn.execute("SELECT * FROM ab_runs WHERE id = ?", (run_id,)).fetchone()
    return _decode(_row(r), "report_json")
