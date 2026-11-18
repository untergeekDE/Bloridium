"""Task 1: sim_checkpoint.py – Checkpoint 9 Presets × 4 Noten × Wheel 0/50/100 %.

Mock-Muster wie test_sim_manual_compare_wheel_sweep (tests/test_scripts.py):
FakeSynth + fake_record + time.sleep/input gepatcht. Kein Live-MIDI, keine Modelle.
"""

import json
import sys
import time

import numpy as np
import pytest


def _install_fakes(monkeypatch, repo, sent, notes_log):
    """midi.connect/audio.record/time.sleep patchen; gibt FakeSynth-Fabrik zurueck."""
    import sim_checkpoint  # noqa: F401  (sys.path s. u.)
    from bloridium import audio, midi

    class FakeSynth:
        def __init__(self, name):
            self.name = name
            self.channel = 4 if name == "blofeld" else 5

        def control_change(self, cc, val, channel=0):
            sent.append(("cc", cc, val, channel))

        def program_change(self, pc, channel=0):
            sent.append(("pc", -1, pc, channel))

        def note_on(self, note, velocity, channel=0):
            notes_log[self.name].append((note, channel))

        def note_off(self, note, channel=0):
            pass

        def close(self):
            pass

    monkeypatch.setattr(midi, "connect",
                        lambda name, ports=None: FakeSynth(name))
    sr = 48000

    def fake_record(duration, channels=None, **kw):
        n = int(duration * sr)
        d = np.zeros((20, n))
        t = np.arange(n) / sr
        d[2] = d[3] = 0.3 * np.sin(2 * np.pi * 220 * t)   # Blofeld In3/4
        d[4] = d[5] = 0.3 * np.sin(2 * np.pi * 221 * t)   # Iridium In5/6
        return d

    monkeypatch.setattr(audio, "record", fake_record)
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)


def _load(repo):
    sys.path.insert(0, str(repo / "scripts"))
    import sim_checkpoint
    return sim_checkpoint


def test_checkpoint_only_a001_defaults(repo, tmp_path, monkeypatch, capsys):
    """--only A001 mit Defaults: 12 Log-Zeilen (4 Noten × 3 Wheel), Meta-Key-Menge exakt,
    CC1 auf ch4 UND ch5 == [0,64,127,0] (inkl. Reset), 24 WAVs, rc 0, Summary printet."""
    sim_checkpoint = _load(repo)
    sent, notes_log = [], {"blofeld": [], "iridium": []}
    _install_fakes(monkeypatch, repo, sent, notes_log)
    monkeypatch.setattr("builtins.input", lambda *a: "")

    log = tmp_path / "log.jsonl"
    rc = sim_checkpoint.main(["--only", "A001", "--irr-pc", "108",
                              "--no-embed", "--no-llm", "--no-spec-png",
                              "--log", str(log), "--wav-dir", str(tmp_path)])
    assert rc == 0
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 12
    for r in rows:
        # score_pair_embed ergaenzt meta um "backends" (Modell/Prompt-Versionierung)
        assert set(r["meta"]) == {"mode", "blofeld", "blofeld_pc", "irr_pc",
                                  "bank", "note", "wheel_pct", "backends"}
        assert r["meta"]["mode"] == "checkpoint"
        assert r["meta"]["blofeld"] == "A001"
        assert r["meta"]["irr_pc"] == 108
        assert r["meta"]["bank"] == 6
        assert r["result"]["score"] is not None
    assert {r["meta"]["note"] for r in rows} == {36, 48, 60, 72}
    assert {r["meta"]["wheel_pct"] for r in rows} == {0.0, 50.0, 100.0}
    blo_cc1 = [v for (k, cc, v, ch) in sent if k == "cc" and cc == 1 and ch == 4]
    irr_cc1 = [v for (k, cc, v, ch) in sent if k == "cc" and cc == 1 and ch == 5]
    assert blo_cc1 == [0, 64, 127, 0], blo_cc1     # 0/50/100 % + Reset nach Preset
    assert irr_cc1 == [0, 64, 127, 0], irr_cc1
    wavs = sorted(p.name for p in tmp_path.glob("ab_A001_*_w*_*.wav"))
    assert len(wavs) == 24
    assert "ab_A001_" in wavs[0] and any("_n36_w0_blo.wav" in w for w in wavs)
    assert any("_n72_w100_irr.wav" in w for w in wavs)
    out = capsys.readouterr().out
    assert "A001" in out and "n36" in out            # Summary-Pivot


def test_checkpoint_all_presets_llm_only_ref(repo, tmp_path, monkeypatch):
    """Voller Lauf: 108 Log-Zeilen (9 Presets × 12), input 9× (Panel-Prompt),
    use_llm nur bei wheel 0 + note 72 (genau 9×), alle DEFAULT_MAP-Locs im Log."""
    sim_checkpoint = _load(repo)
    from bloridium import sim, sim_embed
    from sim_sweep_pcs import DEFAULT_MAP

    sent, notes_log = [], {"blofeld": [], "iridium": []}
    _install_fakes(monkeypatch, repo, sent, notes_log)
    calls = {"input": 0, "use_llm": []}

    def fake_input(*a):
        calls["input"] += 1
        return ""

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(sim_embed, "build_backends",
                        lambda models_dir, want_embed, want_llm: (None, None))
    monkeypatch.setattr(sim_embed, "build_profile_backend", lambda want, model: None)

    def fake_score_pair_embed(x_blo, x_irr, sr=48000, meta=None, log_path=None, **kw):
        calls["use_llm"].append(bool(kw.get("use_llm")))
        result = {"score": 90.0, "verdict": "nahe", "spec_cos": 0.9, "env_dtw": 0.1,
                  "embed_score": 80.0, "embed_cos": 0.8, "combined": 85.0,
                  "llm": None, "profile": None, "backend_error": None,
                  "band_delta_db": [], "band_dtw": [], "band_edges_hz": [],
                  "peak_dbfs": None}
        if log_path:
            sim.log_run(result, meta, log_path)
        return result

    monkeypatch.setattr(sim_embed, "score_pair_embed", fake_score_pair_embed)

    log = tmp_path / "log.jsonl"
    # KEIN --no-llm: use_llm muss an den Referenz-Kombinationen True werden
    # (build_backends ist gepatcht, der Fake score_pair_embed ruft kein ollama)
    rc = sim_checkpoint.main(["--no-embed", "--no-wait",
                              "--log", str(log), "--wav-dir", str(tmp_path)])
    assert rc == 0
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 108
    assert {r["meta"]["blofeld"] for r in rows} == set(DEFAULT_MAP)
    assert calls["input"] == 0                       # --no-wait: kein Prompt
    assert sum(calls["use_llm"]) == 9
    full_rows = [r["meta"] for r, u in zip(rows, calls["use_llm"]) if u]
    assert all(m["wheel_pct"] == 0.0 and m["note"] == 72 for m in full_rows)


def test_checkpoint_stumm_weiter_exit1(repo, tmp_path, monkeypatch):
    """score None (stumm) wird geloggt, Lauf geht weiter, Exit 1 am Ende."""
    sim_checkpoint = _load(repo)
    from bloridium import sim, sim_embed

    sent, notes_log = [], {"blofeld": [], "iridium": []}
    _install_fakes(monkeypatch, repo, sent, notes_log)
    monkeypatch.setattr("builtins.input", lambda *a: "")
    monkeypatch.setattr(sim_embed, "build_backends",
                        lambda models_dir, want_embed, want_llm: (None, None))
    monkeypatch.setattr(sim_embed, "build_profile_backend", lambda want, model: None)

    def fake_score_pair_embed(x_blo, x_irr, sr=48000, meta=None, log_path=None, **kw):
        stumm = meta["blofeld"] == "A001" and meta["note"] == 36 and meta["wheel_pct"] == 0.0
        result = {"score": None if stumm else 90.0, "verdict": "fehler" if stumm else "nahe",
                  "error": "stille Aufnahme" if stumm else None,
                  "spec_cos": None, "env_dtw": None, "embed_score": None,
                  "embed_cos": None, "combined": None, "llm": None, "profile": None,
                  "backend_error": None, "band_delta_db": [], "band_dtw": [],
                  "band_edges_hz": [], "peak_dbfs": None}
        if log_path:
            sim.log_run(result, meta, log_path)
        return result

    monkeypatch.setattr(sim_embed, "score_pair_embed", fake_score_pair_embed)

    log = tmp_path / "log.jsonl"
    rc = sim_checkpoint.main(["--only", "A001", "--no-embed", "--no-llm", "--no-wait", "--no-spec-png",
                              "--log", str(log), "--wav-dir", str(tmp_path)])
    assert rc == 1
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 12                          # weitergelaufen trotz Stille
    assert sum(1 for r in rows if r["result"]["score"] is None) == 1


def test_checkpoint_only_unknown_loc_errors(repo, tmp_path, monkeypatch):
    """--only mit unbekannter Location -> ap.error (SystemExit 2), keine Messung,
    kein Log-Eintrag (wie sim_manual_compare.py: loc nicht in DEFAULT_MAP)."""
    sim_checkpoint = _load(repo)
    sent, notes_log = [], {"blofeld": [], "iridium": []}
    _install_fakes(monkeypatch, repo, sent, notes_log)
    log = tmp_path / "log.jsonl"
    with pytest.raises(SystemExit) as e:
        sim_checkpoint.main(["--only", "A999", "--no-wait", "--no-embed", "--no-llm",
                             "--log", str(log), "--wav-dir", str(tmp_path)])
    assert e.value.code == 2
    assert not log.exists() or not log.read_text().strip()
    assert not list(tmp_path.glob("ab_*.wav"))


def test_checkpoint_no_wait_and_overrides(repo, tmp_path, monkeypatch):
    """--no-wait ruft input nicht auf; --notes/--wheel ueberschreiben Defaults."""
    sim_checkpoint = _load(repo)
    sent, notes_log = [], {"blofeld": [], "iridium": []}
    _install_fakes(monkeypatch, repo, sent, notes_log)

    def boom_input(*a):
        raise AssertionError("input darf bei --no-wait nicht gerufen werden")

    monkeypatch.setattr("builtins.input", boom_input)

    log = tmp_path / "log.jsonl"
    rc = sim_checkpoint.main(["--only", "A008", "--notes", "60,72", "--wheel", "0",
                              "--no-embed", "--no-llm", "--no-wait", "--no-spec-png",
                              "--log", str(log), "--wav-dir", str(tmp_path)])
    assert rc == 0
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 2
    assert {r["meta"]["note"] for r in rows} == {60, 72}
    assert {r["meta"]["wheel_pct"] for r in rows} == {0.0}
    assert all(r["meta"]["blofeld"] == "A008" for r in rows)


def test_checkpoint_spec_png_dir(repo, tmp_path, monkeypatch):
    """--spec-png-dir: pro Kombination ein spec_<LOC>_n<note>_w<pct>.png, im Log verlinkt."""
    sim_checkpoint = _load(repo)
    sent, notes_log = [], {"blofeld": [], "iridium": []}
    _install_fakes(monkeypatch, repo, sent, notes_log)
    monkeypatch.setattr("builtins.input", lambda *a: "")
    sdir = tmp_path / "spec"
    log = tmp_path / "log.jsonl"
    rc = sim_checkpoint.main(["--only", "A001", "--no-embed", "--no-llm", "--no-wait",
                              "--spec-png-dir", str(sdir),
                              "--log", str(log), "--wav-dir", str(tmp_path)])
    assert rc == 0
    pngs = sorted(p.name for p in sdir.glob("spec_A001_*.png"))
    assert len(pngs) == 12
    assert any("_n36_w0.png" in p for p in pngs)
    assert any("_n72_w100.png" in p for p in pngs)
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 12
    assert all(r["result"]["spec_png"] and r["result"]["spec_png"].endswith(".png")
               for r in rows)
