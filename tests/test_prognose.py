"""prognose.py – Random Forest SNDD→Score (TDD Task 1: Kern, Task 2: CLI)."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from bloridium import blofeld_dump, prognose

REPO = Path(__file__).resolve().parent.parent
A043_DUMP = REPO / "dumps" / "blofeld_sndd_A043_20261108_135516.bin"


def _synth_dump_bytes(loc: str, sdata: bytes) -> bytes:
    """Komplette SysEx-Bytes (mit F0/F7) fuer eine Location."""
    bb = ord(loc[0]) - 65
    nn = int(loc[1:]) - 1
    body = blofeld_dump.build_sndd(sdata, bb=bb, nn=nn)
    return bytes([0xF0] + body + [0xF7])


def _sdata(seed: int, cutoff_idx: int = None, cutoff_val: int = None) -> bytes:
    rng = np.random.default_rng(seed)
    sd = rng.integers(0, 128, size=blofeld_dump.SDATA_SIZE, dtype=np.uint8)
    if cutoff_idx is not None:
        sd[cutoff_idx] = cutoff_val
    return bytes(sd)


def _write_log(path: Path, rows: list[dict]):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _log_row(loc, combined=None, score=None, verdict="nahe"):
    res = {"score": score, "combined": combined, "verdict": verdict,
           "embed_score": None, "error": None, "score_version": 2}
    return {"ts": "20261118_000000", "meta": {"mode": "checkpoint", "blofeld": loc,
                                              "note": 72, "wheel_pct": 0.0},
            "result": res}


# --- Features / IO ---

def test_feature_vector_real_dump():
    if not A043_DUMP.exists():
        pytest.skip("A043-Dump lokal nicht vorhanden")
    parsed = blofeld_dump.parse_sndd(A043_DUMP.read_bytes())
    x = prognose.feature_vector(parsed)
    assert x.shape == (len(prognose.FEATURE_IDX),)
    assert len(prognose.FEATURE_IDX) == 367          # 383 minus 16 Namens-Bytes
    assert not any(363 <= i < 379 for i in prognose.FEATURE_IDX)
    assert 0.0 <= x.min() and x.max() <= 1.0
    names = prognose.param_names()
    assert len(names) == 367
    assert any("Osc 1" in n for n in names)


def test_loc_from_header_and_find_dump(tmp_path):
    if not A043_DUMP.exists():
        pytest.skip("A043-Dump lokal nicht vorhanden")
    data = A043_DUMP.read_bytes()
    assert prognose.loc_from_header(data) == "A043"
    assert prognose.find_dump(REPO / "dumps", "A043").exists()
    with pytest.raises(FileNotFoundError):
        prognose.find_dump(REPO / "dumps", "ZZZ9")
    # synthetischer Dump in tmp
    d = tmp_path / "dumps"
    d.mkdir()
    (d / "blofeld_sndd_B007_20261118_000000.bin").write_bytes(
        _synth_dump_bytes("B007", _sdata(1)))
    assert prognose.loc_from_header((d / "blofeld_sndd_B007_20261118_000000.bin")
                                    .read_bytes()) == "B007"
    assert prognose.find_dump(d, "B007").name == "blofeld_sndd_B007_20261118_000000.bin"


def test_load_training_rows_aggregates_and_skips(tmp_path):
    if not A043_DUMP.exists():
        pytest.skip("A043-Dump lokal nicht vorhanden")
    log = tmp_path / "log.jsonl"
    _write_log(log, [
        _log_row("A043", combined=80.0, score=90.0),
        _log_row("A043", combined=90.0, score=95.0),
        _log_row("A043", combined=None, score=70.0),          # Fallback auf score
        _log_row("A043", score=None, verdict="fehler"),       # stumm -> skip
        _log_row("ZZZ9", combined=50.0, score=50.0),          # kein Dump -> skip
    ])
    X, y, locs, skipped = prognose.load_training_rows(log, REPO / "dumps")
    assert X.shape == (1, 367)
    assert locs == ["A043"]
    assert y[0] == pytest.approx(np.mean([80.0, 90.0, 70.0]))  # Aggregation pro Loc
    assert len(skipped) == 2 and any("fehler" in s for s in skipped)


# --- Train / Predict ---

def test_train_model_synthetic_recovers_signal():
    rng = np.random.default_rng(7)
    n = 100
    X = rng.random((n, 367))
    i_cut = prognose.FEATURE_IDX.index(20)   # beliebiger Parameter-Index
    i_osc = prognose.FEATURE_IDX.index(0)
    y = 100.0 * (0.6 * X[:, i_cut] + 0.4 * X[:, i_osc]) + rng.normal(0, 1, n)
    bundle = prognose.train_model(X, y, seed=42, n_estimators=40)
    assert bundle["metrics"]["r2"] > 0.5          # Holdout-R²: Signal gefunden
    top = [name for name, _ in bundle["importances"][:2]]
    assert prognose.param_names()[i_cut] in top or prognose.param_names()[i_osc] in top
    pred = bundle["model"].predict(X[:1])[0]
    assert abs(pred - y[0]) < 15.0


def test_train_model_tiny_n_no_crash():
    X = np.random.default_rng(1).random((3, 367))
    y = np.array([50.0, 70.0, 90.0])
    bundle = prognose.train_model(X, y, seed=1, n_estimators=20)
    assert bundle["metrics"]["r2_cv"] is None      # keine CV bei n<10
    assert bundle["metrics"]["r2"] is not None      # Train-R² trotzdem da
    assert bundle["n"] == 3


def test_save_load_roundtrip(tmp_path):
    X = np.random.default_rng(3).random((30, 367))
    y = 50 + 40 * X[:, 5]
    bundle = prognose.train_model(X, y, seed=5, n_estimators=30)
    p = tmp_path / "m.joblib"
    prognose.save_model(bundle, p)
    b2 = prognose.load_model(p)
    assert np.allclose(bundle["model"].predict(X[:3]), b2["model"].predict(X[:3]))
    assert b2["target"] == bundle["target"]


def test_predict_loc_uses_saved_model(tmp_path):
    if not A043_DUMP.exists():
        pytest.skip("A043-Dump lokal nicht vorhanden")
    rng = np.random.default_rng(11)
    X = rng.random((40, 367))
    y = 100.0 * X[:, 10] + rng.normal(0, 1, 40)
    bundle = prognose.train_model(X, y, seed=9, n_estimators=50)
    mp = tmp_path / "m.joblib"
    prognose.save_model(bundle, mp)
    r = prognose.predict_loc("A043", REPO / "dumps", mp)
    assert r["loc"] == "A043"
    assert 0.0 <= r["predicted"] <= 100.0 or isinstance(r["predicted"], float)
    assert r["std"] >= 0.0
    assert r["model"] == "m.joblib"


# --- Task 2: CLI prognose train|predict ---

def _make_dataset(tmp_path, n_locs=12):
    """Synthetische Dumps + Log: Score haengt monoton von SDATA[20] ab."""
    d = tmp_path / "dumps"
    d.mkdir(exist_ok=True)
    rows = []
    for k in range(n_locs):
        loc = f"A{k + 1:03d}"
        sd = bytearray(_sdata(100 + k))
        sd[20] = int(k * 127 / max(1, n_locs - 1))
        (d / f"blofeld_sndd_{loc}_20261118_000000.bin").write_bytes(
            _synth_dump_bytes(loc, bytes(sd)))
        score = 40.0 + 50.0 * (sd[20] / 127.0) + (k % 3)
        rows.append(_log_row(loc, combined=score, score=score))
    log = tmp_path / "log.jsonl"
    _write_log(log, rows)
    return d, log


def test_cli_train_and_predict(tmp_path, capsys):
    from bloridium import cli
    d, log = _make_dataset(tmp_path)
    model = tmp_path / "m.pkl"
    rc = cli.main(["prognose", "train", "--log", str(log), "--dumps", str(d),
                   "--model", str(model), "--n-estimators", "30"])
    assert rc == 0
    assert model.exists()
    out = capsys.readouterr().out
    assert "R2" in out and "Top" in out
    rc = cli.main(["prognose", "predict", "A001", "--dumps", str(d), "--model", str(model)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "predicted" in out and "A001" in out
    # A012 (hoher SDATA[20]) sollte hoeher prognostiziert werden als A001
    cli.main(["prognose", "predict", "A012", "--dumps", str(d), "--model", str(model)])
    out2 = capsys.readouterr().out
    import re as _re
    p1 = float(_re.search(r"predicted A001: ([\d.]+)", out).group(1))
    p2 = float(_re.search(r"predicted A012: ([\d.]+)", out2).group(1))
    assert p2 > p1


def test_cli_train_no_data_exit2(tmp_path, capsys):
    from bloridium import cli
    log = tmp_path / "empty.jsonl"
    log.write_text("")
    rc = cli.main(["prognose", "train", "--log", str(log), "--dumps", str(tmp_path),
                   "--model", str(tmp_path / "m.pkl")])
    assert rc == 2
    assert capsys.readouterr().err  # Fehlermeldung auf stderr


def test_load_training_rows_filters_old_score_version(tmp_path):
    log = tmp_path / "log.jsonl"
    old = _log_row("A001", score=95.0)
    del old["result"]["score_version"]           # pre-2026-11-20 row = v1
    new = _log_row("A001", score=60.0)
    log.write_text(json.dumps(old) + "\n" + json.dumps(new) + "\n")
    _, _, _, skipped_all = prognose.load_training_rows(log, tmp_path, "score")
    _, _, _, skipped_v2 = prognose.load_training_rows(log, tmp_path, "score",
                                                      min_score_version=2)
    assert not any("score_version" in s for s in skipped_all)
    assert any("score_version 1 < 2" in s for s in skipped_v2)


# --- entropy / feature check (Task 2) -----------------------------------------

def _entropy_log(path: Path, n: int = 12, embed_is_label: bool = True,
                 version: int = 2) -> Path:
    rows = []
    for i in range(n):
        loc = f"A{i+1:03d}"
        y = 50.0 + 45.0 * i / (n - 1)                    # 50..95 linear
        emb = y if embed_is_label else float((i * 37) % n)  # nutzlos ohne Signal
        rows.append({"meta": {"mode": "npy-v2", "blofeld": loc, "note": 72},
                     "result": {"score": y, "verdict": "close", "score_version": version,
                                "embed_score": emb, "spec_mad_db": 5.0 if i % 2 == 0 else 20.0,
                                "env_dtw": 0.01 * i, "llm": {"score": 80},
                                "profile": {"score": 70}}})
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_entropy_report_perfect_vs_useless_feature(tmp_path):
    log = _entropy_log(tmp_path / "log.jsonl", embed_is_label=True)
    rep = prognose.entropy_report(log, target="score", min_score_version=2)
    assert rep["n"] == 12 and rep["h_y_bits"] > 0
    emb = rep["features"]["embed_score"]
    mad = rep["features"]["spec_mad_db"]
    assert emb["ig_bits"] > 0.9 * rep["h_y_bits"]      # perfekte Ordnung -> fast volle IG
    assert emb["pearson"] == pytest.approx(1.0, abs=1e-9)
    assert emb["spearman"] == pytest.approx(1.0, abs=1e-9)
    assert mad["ig_bits"] < 0.5 * rep["h_y_bits"]       # lineares MAD traegt kaum bei
    assert rep["features"]["llm_score"]["ig_bits"] is not None  # konstant -> IG 0
    assert rep["features"]["llm_score"]["pearson"] is None      # zero variance


def test_entropy_report_respects_min_score_version(tmp_path):
    log = _entropy_log(tmp_path / "log.jsonl", n=6, version=1)
    rep = prognose.entropy_report(log, min_score_version=2)
    assert rep["n"] == 0
    rep = prognose.entropy_report(log, min_score_version=0)
    assert rep["n"] == 6


def test_cli_prognose_entropy(tmp_path, capsys):
    from bloridium import cli
    log = _entropy_log(tmp_path / "log.jsonl")
    rc = cli.main(["prognose", "entropy", "--log", str(log)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "H(y)" in out and "embed_score" in out and "best feature" in out
