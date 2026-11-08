"""Task 3: workflow library – parse_location, load_sndd_file, read_sound,
convert_parsed (offline aus vorhandenem Dump)."""

from types import SimpleNamespace

import pytest

DUMP_BIN = "dumps/blofeld_sndd_A043_20261108_135516.bin"
DUMP_HEX = "dumps/blofeld_sndd_A043_20261108_135516.hex"
TEMPLATE = "docs/refs/qpat/template_waveform.qpat"


# ---- parse_location / location_str ----

def test_parse_location_valid():
    from bloridium import workflow

    assert workflow.parse_location("A001") == (0, 0)
    assert workflow.parse_location("A043") == (0, 42)
    assert workflow.parse_location("a043") == (0, 42)
    assert workflow.parse_location("edit") == (0x7F, 0)
    assert workflow.parse_location("B128") == (1, 127)


def test_parse_location_invalid_raises():
    from bloridium import workflow

    for bad in ("A000", "A129", "1A03", "xyz"):  # "" ist legacy = edit
        with pytest.raises(ValueError):
            workflow.parse_location(bad)


def test_location_str_roundtrip():
    from bloridium import workflow

    assert workflow.location_str(0, 42) == "A043"
    assert workflow.location_str(0x7F, 0) == "edit"
    assert workflow.parse_location(workflow.location_str(3, 127)) == (3, 127)


# ---- load_sndd_file ----

def test_load_sndd_file_bin_and_hex(repo):
    from bloridium import blofeld_dump as bd
    from bloridium import workflow

    raw_bin = workflow.load_sndd_file(repo / DUMP_BIN)
    raw_hex = workflow.load_sndd_file(repo / DUMP_HEX)
    assert raw_bin == raw_hex
    parsed = bd.parse_sndd(raw_bin)
    assert parsed["name"] == "SH Power"
    assert parsed["chk_ok"] is True


# ---- convert_parsed (offline) ----

def test_convert_parsed_writes_qpat(repo, tmp_path):
    from bloridium import blofeld_dump as bd
    from bloridium import qpat, workflow

    parsed = bd.parse_sndd(workflow.load_sndd_file(repo / DUMP_BIN))
    out_path, mapped, unmapped = workflow.convert_parsed(
        parsed, "A043", tmp_path, repo / TEMPLATE)
    assert out_path.exists() and out_path.suffix == ".qpat"
    assert out_path.name == "SH Power_A043.qpat"  # Legacy-Namenkonvention aus step3
    assert mapped > 0
    assert isinstance(unmapped, list) and len(unmapped) > 0
    q = qpat.load(out_path)
    assert "Osc1Type" in q["params"]
    assert q["name"] == "SH Power"


# ---- read_sound mit Fake-Synth (Retry nach Timeout) ----

def _fake_sndd_msg(name="SH Power", bb=0, nn=42):
    from bloridium import blofeld_dump as bd

    sdata = bytearray(383)
    sdata[363:363 + len(name)] = name.encode()
    return SimpleNamespace(type="sysex", data=bd.build_sndd(bytes(sdata), bb=bb, nn=nn))


class FakeSynth:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def send_sysex(self, data):
        self.requests.append(list(data))

    def receive(self, timeout=1.0):
        return self.responses.pop(0) if self.responses else []


def test_read_sound_retries_after_timeout():
    from bloridium import workflow

    synth = FakeSynth([[], [_fake_sndd_msg()]])  # 1. Versuch: Timeout, 2.: SNDD
    parsed = workflow.read_sound(synth, "A043", timeout=0.01, retries=2)
    assert parsed["name"] == "SH Power"
    assert len(synth.requests) == 2  # SNDR wurde 2x gesendet


def test_read_sound_raises_after_all_retries():
    from bloridium import workflow

    synth = FakeSynth([[], []])
    with pytest.raises(RuntimeError):
        workflow.read_sound(synth, "A043", timeout=0.01, retries=2)
    assert len(synth.requests) == 2
