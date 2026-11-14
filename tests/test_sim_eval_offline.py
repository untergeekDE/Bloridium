"""sim_eval_offline.py – Phase-B-Eval auf recordings/-Paaren (TDD Task 8, gemockt)."""

import json
import sys

import numpy as np
import pytest


@pytest.fixture
def ev(repo, monkeypatch):
    sys.path.insert(0, str(repo / "scripts"))
    import sim_eval_offline
    from bloridium import sim_embed

    class _FakeClap:
        def __init__(self, path):
            self.model_path = path

        def embed(self, x, sr):
            v = np.zeros(512, dtype=np.float32)
            v[int(abs(hash(str(x[:10]))) % 512)] = 1.0
            return v

    monkeypatch.setattr(sim_embed, "ClapBackend", _FakeClap)
    return sim_eval_offline, sim_embed


def _mk_pair(rec, base, fa=440.0, fb=442.0):
    sr = 48000
    t = np.arange(sr) / sr  # 1 s
    a = 0.4 * np.sin(2 * np.pi * fa * t)
    b = 0.4 * np.sin(2 * np.pi * fb * t)
    np.save(rec / f"{base}_blofeld.npy", a)
    np.save(rec / f"{base}_iridium.npy", b)


def test_pairs_discovery(ev, tmp_path):
    ev_mod, _ = ev
    rec = tmp_path / "rec"
    rec.mkdir()
    _mk_pair(rec, "ab_X_20260101_000000")
    _mk_pair(rec, "check_20260101_111111")
    np.save(rec / "orphan_20260101_222222_blofeld.npy", np.zeros(48000))  # ohne iridium
    pairs = ev_mod.find_pairs(rec)
    assert [p[0] for p in pairs] == ["ab_X_20260101_000000", "check_20260101_111111"]


def test_eval_writes_json_and_table(ev, tmp_path, capsys):
    ev_mod, sim_embed = ev
    rec = tmp_path / "rec"
    rec.mkdir()
    _mk_pair(rec, "check_20260101_111111")
    md = tmp_path / "models"
    md.mkdir()
    (md / sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    out = tmp_path / "eval.json"
    rc = ev_mod.main(["--rec-dir", str(rec), "--models-dir", str(md), "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert len(data["rows"]) == 1
    row = data["rows"][0]
    assert row["pair"] == "check_20260101_111111"
    assert set(row) >= {"pair", "score", "embed_score", "combined", "verdict", "backend_error"}
    assert row["embed_score"] is not None and row["backend_error"] is None
    assert "check_20260101_111111" in capsys.readouterr().out  # Tabelle auf stdout


def test_no_gguf_degrades(ev, tmp_path):
    ev_mod, _ = ev
    rec = tmp_path / "rec"
    rec.mkdir()
    _mk_pair(rec, "check_20260101_111111")
    md = tmp_path / "models"
    md.mkdir()  # leer
    out = tmp_path / "eval.json"
    rc = ev_mod.main(["--rec-dir", str(rec), "--models-dir", str(md), "--out", str(out)])
    assert rc == 0
    row = json.loads(out.read_text())["rows"][0]
    assert row["embed_score"] is None and row["score"] is not None
    assert "clap" in row["backend_error"]


def test_spearman_perfect_inverse_ties(ev):
    ev_mod, _ = ev
    assert ev_mod.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert ev_mod.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)
    assert ev_mod.spearman([1, 1, 2], [5, 5, 9]) == pytest.approx(1.0)  # Ties auf beiden Seiten
    assert ev_mod.spearman([1, 1, 2], [1, 2, 3]) == pytest.approx(0.866, abs=1e-3)  # Tie nur in x
    assert ev_mod.spearman([5], [5]) == 0.0  # n<2


def test_ratings_spearman_in_json(ev, tmp_path):
    ev_mod, sim_embed = ev
    rec = tmp_path / "rec"
    rec.mkdir()
    _mk_pair(rec, "p1_20260101_000000", fa=440.0, fb=440.0)   # sehr aehnlich
    _mk_pair(rec, "p2_20260101_000001", fa=440.0, fb=110.0)   # verschieden
    md = tmp_path / "models"
    md.mkdir()
    (md / sim_embed.CLAP_GGUF_NAME).write_bytes(b"x")
    ratings = tmp_path / "ratings.json"
    ratings.write_text(json.dumps({"p1_20260101_000000": 95, "p2_20260101_000001": 20}))
    out = tmp_path / "eval.json"
    rc = ev_mod.main(["--rec-dir", str(rec), "--models-dir", str(md),
                      "--out", str(out), "--ratings", str(ratings)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert "spearman" in data
    assert set(data["spearman"]) == {"score", "embed_score", "combined"}
    for v in data["spearman"].values():
        assert -1.0 <= v <= 1.0
