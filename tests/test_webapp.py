"""Tests for the Bloridium web app (webapp/): pipeline, matching, Flask routes."""

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "webapp"))

import convert  # noqa: E402
import matching  # noqa: E402
from app import create_app  # noqa: E402

DUMP_BIN = REPO / "dumps" / "blofeld_sndd_A043_20261108_135516.bin"


def _sndd_bytes(bb: int, nn: int, sdata: bytes) -> bytes:
    from bloridium import blofeld_dump as bd
    return bytes([0xF0]) + bytes(bd.build_sndd(sdata, bb=bb, nn=nn)) + bytes([0xF7])


@pytest.fixture
def core():
    return convert.load_core()


@pytest.fixture
def sample_sdata(core):
    return core.blofeld_dump.parse_sndd(DUMP_BIN.read_bytes())["sdata"]


def test_split_sysex_messages():
    a = bytes([0xF0, 0x3E, 0xF7])
    b = bytes([0xF0, 0x01, 0x02, 0xF7])
    msgs = convert.split_sysex_messages(a + b + b"\x00junk" + a)
    assert msgs == [a, b, a]
    assert convert.split_sysex_messages(b"") == []
    assert convert.split_sysex_messages(b"\x01\x02\x03") == [b"\x01\x02\x03"]


def test_parse_upload_bank(core, sample_sdata):
    syx = b"".join(_sndd_bytes(0, i, sample_sdata) for i in range(3))
    syx += bytes([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7])  # foreign message (identity)
    bad = bytearray(_sndd_bytes(0, 9, sample_sdata))
    bad[-2] ^= 0x01  # checksum broken
    res = convert.parse_upload("bank-a.syx", syx + bytes(bad))
    assert len(res["sounds"]) == 3
    assert res["skipped"] == 1
    assert len(res["errors"]) == 1
    assert [convert.location_str(s["bb"], s["nn"]) for s in res["sounds"]] == \
        ["A001", "A002", "A003"]


def test_parse_upload_rejects_garbage():
    with pytest.raises(convert.UploadError):
        convert.parse_upload("x.hex", b"zz nn xx")
    res = convert.parse_upload("x.syx", b"\xF0\x7E\xF7")
    assert res["sounds"] == [] and res["skipped"] == 1


def test_process_upload_zip(core, sample_sdata, tmp_path):
    syx = b"".join(_sndd_bytes(0, i, sample_sdata) for i in range(3))
    report = convert.process_upload("bank-a-2019-06-17.syx", syx, tmp_path)
    assert report["num_sounds"] == 3
    assert 0 <= report["avg_score"] <= 100
    zp = tmp_path / report["token"] / "result.zip"
    assert zp.exists()
    with zipfile.ZipFile(zp) as zf:
        names = zf.namelist()
        assert "MANIFEST.md" in names and "report.json" in names
        qpats = [n for n in names if n.endswith(".qpat")]
        assert len(qpats) == 3
        assert all(n.startswith(("A001_", "A002_", "A003_")) for n in qpats)
        q = core.qpat.parse_qpat(zf.read(qpats[0]))
        assert q["name"] == "SH Power"
        assert q["version"] == core.qpat.PRESET_VERSION
        rep = json.loads(zf.read("report.json"))
        assert rep["num_sounds"] == 3
        assert rep["conversion_version"] == "v0.3" and rep["similarity_version"] == "v0.2"
        assert all("features" in s and "params" in s["features"] for s in rep["sounds"])
        assert all("score" in s and "penalties" in s for s in rep["sounds"])
        assert "v0.2" in zf.read("MANIFEST.md").decode()
    # report.json on disk identical to the ZIP content
    on_disk = json.loads((tmp_path / report["token"] / "report.json").read_text())
    assert on_disk["token"] == report["token"]


def test_process_upload_deterministic(sample_sdata, tmp_path):
    syx = _sndd_bytes(0, 42, sample_sdata)
    r1 = convert.process_upload("a.syx", syx, tmp_path)
    r2 = convert.process_upload("a.syx", syx, tmp_path)
    s1 = [(s["location"], s["score"], s["penalties"]) for s in r1["sounds"]]
    s2 = [(s["location"], s["score"], s["penalties"]) for s in r2["sounds"]]
    assert s1 == s2  # same input -> same scores (deterministic)


def test_estimate_match_range_and_determinism(core, sample_sdata):
    parsed = core.blofeld_dump.parse_sndd(DUMP_BIN.read_bytes())
    _, unmapped = core.qpat_map.blofeld_to_qpat_params(parsed)
    e1 = matching.estimate_match(parsed, unmapped, core.qpat_map)
    e2 = matching.estimate_match(parsed, unmapped, core.qpat_map)
    assert e1 == e2
    assert 0.0 <= e1["score"] <= 100.0
    assert set(e1["parts"]) == {"osc", "filter", "fx", "env_mod", "arp"}


def test_estimate_prefers_exact_over_approx(core, sample_sdata):
    base = core.blofeld_dump.parse_sndd(_sndd_bytes(0, 0, sample_sdata))
    # Osc1 Shape -> Saw (base waveform, exact)
    saw = bytearray(sample_sdata)
    saw[8] = 2  # SHAPES[2] = "Saw"
    parsed_saw = core.blofeld_dump.parse_sndd(_sndd_bytes(0, 0, bytes(saw)))
    # Osc1 Shape -> Wavetable without bridge (SHAPES[5] = "Alt 1")
    wt = bytearray(sample_sdata)
    wt[8] = 5
    parsed_wt = core.blofeld_dump.parse_sndd(_sndd_bytes(0, 0, bytes(wt)))
    # Arp off vs. Arp on (index 311)
    arp = bytearray(sample_sdata)
    arp[311] = 1
    parsed_arp = core.blofeld_dump.parse_sndd(_sndd_bytes(0, 0, bytes(arp)))

    def score(p):
        _, un = core.qpat_map.blofeld_to_qpat_params(p)
        return matching.estimate_match(p, un, core.qpat_map)

    e_base, e_saw, e_wt, e_arp = score(base), score(parsed_saw), score(parsed_wt), score(parsed_arp)
    assert e_saw["parts"]["osc"] == 1.0
    assert e_wt["parts"]["osc"] < e_base["parts"]["osc"] or e_base["parts"]["osc"] == 1.0
    assert e_arp["parts"]["arp"] < e_base["parts"]["arp"]
    assert e_arp["score"] < e_base["score"]


def test_flask_routes(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()

    assert client.get("/health").get_data(as_text=True).strip() == "ok"
    r = client.get("/")
    assert r.status_code == 200 and b"upload" in r.data
    # layout like webpage.pdf + versioning + background image
    assert b"Bloridium Tool v0.3" in r.data
    assert b"Convert Blofeld Sound Banks for the Iridium" in r.data
    assert b"crude approximation" in r.data                      # NOTE box from the PDF
    assert b"github.com/untergeekDE/Bloridium" in r.data          # footer from the PDF
    assert b"/static/bloridium-scaled.jpg" in r.data              # background in the CSS
    r = client.get("/static/bloridium-scaled.jpg")
    assert r.status_code == 200 and r.mimetype == "image/jpeg"

    syx = _sndd_bytes(0, 42, sample_sdata)
    r = client.post("/upload", data={"file": (io.BytesIO(syx), "bank-a.syx")},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    assert b"/download/" in r.data and b"Score" in r.data
    assert b"similarity v0.2" in r.data

    token = None
    for line in r.data.decode().splitlines():
        if "/download/" in line:
            token = line.split("/download/")[1].split('"')[0]
            break
    assert token
    r = client.get(f"/download/{token}")
    assert r.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r.data)) as zf:
        assert any(n.endswith(".qpat") for n in zf.namelist())
    r = client.get(f"/report/{token}")
    assert r.status_code == 200
    rep = json.loads(r.data)
    assert rep["num_sounds"] == 1 and 0 <= rep["sounds"][0]["score"] <= 100
    assert rep["conversion_version"] == "v0.3"
    assert rep["similarity_version"] == "v0.2"
    assert "v0.2" in rep["matcher"]

    assert client.get("/download/../etc/passwd").status_code == 404
    assert client.get("/download/" + "0" * 32).status_code == 404
    r = client.post("/upload", data={}, content_type="multipart/form-data")
    assert r.status_code == 400
    r = client.post("/upload", data={"file": (io.BytesIO(b"\xF0\x7E\xF7"), "x.syx")},
                    content_type="multipart/form-data")
    assert r.status_code == 400
