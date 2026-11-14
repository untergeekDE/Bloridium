"""Task 9: CLI Phase B – `sim compare` + `ab --embed/--llm` (TDD, alles gemockt)."""

import json
import sys

import numpy as np
import pytest


SR = 48000


def _sine(freq=440.0, dur=0.5, amp=0.4):
    t = np.arange(int(dur * SR)) / SR
    return amp * np.sin(2 * np.pi * freq * t)


class FakeSynth:
    def __init__(self, name):
        self.name = name
        self.channel = 5 if name == "blofeld" else 5
        self.events = []

    def control_change(self, cc, val, channel=None):
        self.events.append(("cc", cc, channel))

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


class FakeClap:
    def __init__(self, path):
        self.model_path = path

    def embed(self, x, sr):
        v = np.zeros(512, dtype=np.float32)
        v[0] = 1.0
        return v


class FakeOllama:
    def __init__(self, *a, **kw):
        self.model = "fake:1"

    def available(self):
        return True

    def judge(self, x_a, x_b, sr, prompt=None, peak_a=None, peak_b=None):
        return {"score": 88, "summary": "nah", "differences": ["d"], "mode": "audio",
                "model": self.model}


@pytest.fixture
def phaseb_env(repo, db_path, tmp_path, monkeypatch):
    from bloridium import audio, cli, db, midi, sim_embed, workflow

    fakes = {"blofeld": FakeSynth("blofeld"), "iridium": FakeSynth("iridium")}
    monkeypatch.setattr(midi, "connect", lambda name, ports=None: fakes[name])
    sig = np.zeros((20, 48000), dtype=np.float32)
    sig[list(audio.CHANNELS["blofeld"])] = _sine(440.0, 1.0)
    sig[list(audio.CHANNELS["iridium"])] = _sine(442.0, 1.0)
    monkeypatch.setattr(audio, "record", lambda duration=2.0, channels=None, **kw: sig)
    monkeypatch.setattr(workflow.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(sim_embed, "build_backends",
                        lambda models_dir, want_embed, want_llm: (
                            FakeClap("fake.gguf") if want_embed else None,
                            FakeOllama() if want_llm else None))
    return cli, db, workflow, sim_embed, db_path, tmp_path


def run(cli, db_path, *argv):
    return cli.main(["--db", str(db_path), *argv])


def test_measure_ab_embed_llm_adds_keys_and_db_roundtrip(phaseb_env):
    cli, db, workflow, sim_embed, db_path, tmp_path = phaseb_env
    rep = workflow.measure_ab(note=36, dur=0.1, label="t", rec_dir=tmp_path,
                              sound_location="A043", embed=True, llm=True,
                              models_dir=str(tmp_path))
    assert rep["sim"]["score"] is not None and rep["sim"]["combined"] is not None
    assert rep["embed"]["embed_score"] == 100.0
    assert rep["llm"]["score"] == 88
    # DB-Roundtrip: report_json traegt die neuen Keys (Blob, keine Migration)
    conn = db.connect(db_path)
    db.insert_ab_run(conn, "t", "A043", 36, 0.1, rep["files"]["report"],
                     rep["files"]["blofeld_npy"], rep["files"]["iridium_npy"], rep)
    row = db.list_ab_runs(conn)[0]["report_json"]
    assert row["embed"]["embed_score"] == 100.0 and row["llm"]["mode"] == "audio"


def test_measure_ab_embed_off_by_default(phaseb_env):
    cli, db, workflow, sim_embed, db_path, tmp_path = phaseb_env
    rep = workflow.measure_ab(note=36, dur=0.1, label="t", rec_dir=tmp_path)
    assert "sim" not in rep and "embed" not in rep and "llm" not in rep


def test_legacy_ab_report_without_phaseb_keys_still_works(phaseb_env):
    cli, db, workflow, sim_embed, db_path, tmp_path = phaseb_env
    legacy = {"label": "old", "band_edges_hz": [100.0, 200.0], "band_delta_db": [1.0],
              "files": {"report": "x", "blofeld_npy": "a", "iridium_npy": "b"}}
    conn = db.connect(db_path)
    db.insert_ab_run(conn, "old", None, 36, 3.0, "x", "a", "b", legacy)
    row = db.list_ab_runs(conn)[0]["report_json"]
    assert "sim" not in row  # alte Rows bleiben unveraendert lesbar
    rc = run(cli, db_path, "ab", "--list")
    assert rc == 0


def test_sim_compare_npy_cli(phaseb_env, tmp_path):
    cli, db, workflow, sim_embed, db_path, _ = phaseb_env
    pa, pb = tmp_path / "a.npy", tmp_path / "b.npy"
    np.save(pa, _sine(440.0, 1.0))
    np.save(pb, _sine(441.0, 1.0))
    log = tmp_path / "sim.jsonl"
    rc = run(cli, db_path, "sim", "compare", "--npy", str(pa), str(pb),
             "--embed", "--llm", "--models-dir", str(tmp_path), "--log", str(log))
    assert rc == 0
    r = json.loads(log.read_text().strip())["result"]
    assert r["embed_score"] == 100.0 and r["llm"]["score"] == 88 and r["combined"] is not None


def test_sim_compare_live_cli(phaseb_env, tmp_path, monkeypatch):
    cli, db, workflow, sim_embed, db_path, _ = phaseb_env
    log = tmp_path / "sim.jsonl"
    rc = run(cli, db_path, "sim", "compare", "--live", "--note", "60", "--dur", "0.1",
             "--blofeld", "A043", "--iridium-slot", "114", "--embed",
             "--models-dir", str(tmp_path), "--log", str(log))
    assert rc == 0
    entry = json.loads(log.read_text().strip())
    assert entry["meta"]["mode"] == "live" and entry["meta"]["iridium_slot"] == "114"
    assert entry["result"]["embed_score"] == 100.0


def test_sim_compare_strict_missing_backend_exit_3(phaseb_env, tmp_path, monkeypatch):
    cli, db, workflow, sim_embed, db_path, _ = phaseb_env
    monkeypatch.setattr(sim_embed, "build_backends",
                        lambda md, we, wl: (None, None))
    pa, pb = tmp_path / "a.npy", tmp_path / "b.npy"
    np.save(pa, _sine(440.0, 1.0))
    np.save(pb, _sine(440.0, 1.0))
    rc = run(cli, db_path, "sim", "compare", "--npy", str(pa), str(pb), "--embed",
             "--strict", "--models-dir", str(tmp_path), "--log", str(tmp_path / "l.jsonl"))
    assert rc == 3


def test_ab_cli_embed_flags(phaseb_env, tmp_path, capsys):
    cli, db, workflow, sim_embed, db_path, _ = phaseb_env
    rc = run(cli, db_path, "ab", "--note", "36", "--dur", "0.1", "--label", "t",
             "--sound", "A043", "--rec-dir", str(tmp_path), "--embed", "--llm",
             "--models-dir", str(tmp_path))
    assert rc == 0
    out = capsys.readouterr().out
    assert "embed_score" in out and "llm" in out
    conn = db.connect(db_path)
    row = db.list_ab_runs(conn)[0]["report_json"]
    assert row["embed"]["embed_score"] == 100.0
