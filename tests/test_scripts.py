"""Task 6: step-Skripte sind duenne Wrapper ueber bloridium.workflow.

argv/Exit-Codes/stdout bleiben kompatibel (Golden-Test gegen main-Checkout).
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = ["step1_verify_connection.py", "step2_read_blofeld_dump.py",
           "step2_parse_blofeld_dump.py", "step3_transfer_qpat.py", "step4_measure_ab.py"]
DUMP = "dumps/blofeld_sndd_A043_20261108_135516.bin"


def run_script(root, name, *args):
    return subprocess.run([sys.executable, str(Path(root) / "scripts" / name), *args],
                          capture_output=True, text=True, cwd=root)


def test_wrappers_delegate_to_workflow(repo):
    for name in SCRIPTS:
        src = (repo / "scripts" / name).read_text()
        assert "workflow" in src, f"{name} soll bloridium.workflow nutzen"


def test_step2_parse_output_contains_sound(repo):
    r = run_script(repo, "step2_parse_blofeld_dump.py", DUMP)
    assert r.returncode == 0
    assert "SH Power" in r.stdout


def test_step2_parse_stdout_matches_original_on_main(repo):
    """Golden: stdout des Wrappers == stdout des urspruenglichen Skripts (main)."""
    main_repo = repo.parent.parent  # .worktrees/bloridium-cli -> Repo-Root
    if not (main_repo / "scripts" / "step2_parse_blofeld_dump.py").exists():
        pytest.skip("main-Checkout nicht gefunden")
    dump = str(repo / DUMP)
    a = run_script(main_repo, "step2_parse_blofeld_dump.py", dump)
    b = run_script(repo, "step2_parse_blofeld_dump.py", dump)
    assert a.returncode == b.returncode == 0
    assert a.stdout == b.stdout


def test_check_connection_structure_offline(monkeypatch):
    from bloridium import midi, workflow

    class FakeSynth:
        out_port_name = "Blofeld"
        in_port_name = "Blofeld"
        channel = 4

        def device_inquiry(self):
            pass

        def receive(self, timeout=1.0):
            return []

        def close(self):
            pass

    monkeypatch.setattr(midi, "list_ports", lambda: {"in": ["Blofeld"], "out": ["Blofeld"]})
    monkeypatch.setattr(midi, "connect", lambda name, ports=None: FakeSynth())
    res = workflow.check_connection(do_audio=False)
    assert set(res["synths"]) == {"blofeld", "iridium"}
    assert res["synths"]["blofeld"]["ok"] is True
    assert res["synths"]["blofeld"]["out_port"] == "Blofeld"


def test_sim_compare_npy_offline(repo, tmp_path):
    """sim_compare.py --npy: offline-Vergleich zweier .npy, loggt JSONL."""
    import json
    import numpy as np
    sr = 48000
    t = np.arange(sr) / sr
    sine = np.stack([0.5 * np.sin(2 * np.pi * 220 * t)] * 2)
    saw = np.stack([0.5 * (2 * ((220 * t) % 1) - 1)] * 2)
    pa, pb = tmp_path / "a.npy", tmp_path / "b.npy"
    np.save(pa, sine)
    np.save(pb, saw)
    log = tmp_path / "log.jsonl"
    r = run_script(repo, "sim_compare.py", "--npy", str(pa), str(pb),
                   "--log", str(log), "--meta", "pair=sine_vs_saw")
    assert r.returncode == 0, r.stderr
    assert "Score" in r.stdout
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["meta"]["pair"] == "sine_vs_saw"
    assert rows[0]["result"]["score"] < 95.0   # Saw != Sinus


def test_sim_live_mit_fakes(repo, tmp_path, monkeypatch):
    """sim_live.main(): sendet CC am Iridium, misst gegen Ref-.npy, loggt JSONL."""
    import json
    import sys
    import numpy as np
    sys.path.insert(0, str(repo / "scripts"))
    import sim_live
    from bloridium import audio, midi

    sent = []

    class FakeSynth:
        out_port_name = "fake"
        channel = 5
        def control_change(self, cc, val, channel=0):
            sent.append((cc, val, channel))
        def note_on(self, note, velocity, channel=0): pass
        def note_off(self, note, channel=0): pass
        def close(self): pass

    sr = 48000
    t = np.arange(sr) / sr
    ref = np.stack([0.5 * np.sin(2 * np.pi * 220 * t)] * 2)
    ref_path = tmp_path / "ref.npy"
    np.save(ref_path, ref)
    live = 0.5 * (2 * ((220 * t) % 1) - 1)  # Saw statt Sinus -> Score < 100

    monkeypatch.setattr(midi, "connect", lambda name, ports=None: FakeSynth())
    def fake_record(duration, channels=None, **kw):
        d = np.zeros((20, int(duration * sr)))
        d[4] = np.resize(live, d.shape[1])
        d[5] = d[4]          # Iridium In 5/6
        return d
    monkeypatch.setattr(audio, "record", fake_record)
    log = tmp_path / "log.jsonl"
    rc = sim_live.main(["--param", "Filter1 Cutoff", "--value", "90",
                        "--ref", str(ref_path), "--log", str(log), "--note", "60"])
    assert rc == 0
    assert any(cc == 0 and v == 90 for cc, v, ch in sent)   # CC0 (Cutoff lt. pid_map)
    rows = [json.loads(l) for l in log.read_text().splitlines()]
    assert rows[0]["meta"]["param"] == "Filter1 Cutoff"
    assert rows[0]["result"]["score"] < 100.0
