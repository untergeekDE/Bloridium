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
