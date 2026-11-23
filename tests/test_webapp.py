"""Tests for the Bloridium web app (webapp/): pipeline, matching, Flask routes."""

import io
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "webapp"))

# Never start the cleanup daemon in tests: several tests create apps and the
# threads would outlive the temporary data directories.
os.environ["BLORIDIUM_CLEANUP_THREAD"] = "0"

import convert  # noqa: E402
import matching  # noqa: E402
from app import create_app  # noqa: E402

from bloridium.version import __version__ as V  # noqa: E402

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


NO_MODEL = "/nonexistent/prognose_rf.pkl"  # force the placeholder matcher


def test_process_upload_zip(core, sample_sdata, tmp_path):
    syx = b"".join(_sndd_bytes(0, i, sample_sdata) for i in range(3))
    report = convert.process_upload("bank-a-2019-06-17.syx", syx, tmp_path, model_path=NO_MODEL)
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
        assert rep["conversion_version"] == f"v{V}" and rep["similarity_version"] == f"v{V}"
        assert all("features" not in s for s in rep["sounds"])
        assert all("score" in s and "penalties" in s for s in rep["sounds"])
        man = zf.read("MANIFEST.md").decode()
        assert "deterministic-placeholder" in man
        assert "not in MIDI map" in man and "| mapped |" not in man
    # report.json on disk identical to the ZIP content
    on_disk = json.loads((tmp_path / report["token"] / "report.json").read_text())
    assert on_disk["token"] == report["token"]
    assert all("features" not in s for s in on_disk["sounds"])


def test_process_upload_deterministic(sample_sdata, tmp_path):
    syx = _sndd_bytes(0, 42, sample_sdata)
    r1 = convert.process_upload("a.syx", syx, tmp_path, model_path=NO_MODEL)
    r2 = convert.process_upload("a.syx", syx, tmp_path, model_path=NO_MODEL)
    s1 = [(s["location"], s["score"], s["penalties"]) for s in r1["sounds"]]
    s2 = [(s["location"], s["score"], s["penalties"]) for s in r2["sounds"]]
    assert s1 == s2  # same input -> same scores (deterministic)


RF_MODEL = REPO / "models" / "prognose_rf.pkl"


@pytest.mark.skipif(not RF_MODEL.exists(), reason="RF model models/prognose_rf.pkl not present (gitignored)")
def test_rf_prognose(sample_sdata, tmp_path):
    """With a trained model, the score comes from the RF prognosis."""
    syx = _sndd_bytes(0, 42, sample_sdata)  # A043 "SH Power"
    r1 = convert.process_upload("a043.syx", syx, tmp_path, model_path=RF_MODEL)
    r2 = convert.process_upload("a043.syx", syx, tmp_path, model_path=RF_MODEL)
    s = r1["sounds"][0]
    assert r1["matcher"].startswith(f"rf-prognose-v{V}")
    assert r1["similarity_version"] == f"v{V}"
    assert r1["model"] == str(RF_MODEL)
    assert 0.0 <= s["score"] <= 100.0 and s["std"] is not None and s["std"] >= 0
    assert s["score"] == r2["sounds"][0]["score"]  # deterministic
    # The shipped model is the n=200 combined one (A v7 + E v2, 0.6.6). Its
    # output is NOT calibrated to a single A043 label any more: the model only
    # reproduces the average level of a bank (holdout R2 ~0.01), which is why
    # the webapp labels it experimental. Anchoring the test to 46.3 would
    # re-introduce exactly the false precision the label warns about.
    with zipfile.ZipFile(r1["zip_path"]) as zf:
        rep = json.loads(zf.read("report.json"))
        assert rep["matcher"].startswith(f"rf-prognose-v{V}")
        assert "rf-prognose" in zf.read("MANIFEST.md").decode()


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


def test_ignored_notes_are_not_counted_as_midi_map_gaps(core, sample_sdata):
    # A1 (2026-11-21): PWM on a sawtooth is deliberately ignored by qpat_map.
    # The web app must not list that as "not in MIDI map".
    parsed = core.blofeld_dump.parse_sndd(_sndd_bytes(0, 42, sample_sdata))
    parsed["params"]["Osc 1 Shape"] = "Saw"
    parsed["params"]["Osc 1 PWM Source"] = "LFO 1"
    parsed["params"]["Osc 1 PWM Amount"] = 64
    template = core.qpat.load(convert.default_template_path())
    conv = convert.convert_sound(core, template, parsed, "A043")
    assert any(u.startswith("Ignored: Osc 1 PWM") for u in conv["ignored"])
    assert not any("Osc 1 PWM" in u for u in conv["unmapped"])
    gaps, ignored = convert.split_unmapped(["Ignored: x", "real gap"])
    assert gaps == ["real gap"] and ignored == ["Ignored: x"]


def test_flask_routes(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)  # placeholder path for stable assertions
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()

    assert client.get("/health").get_data(as_text=True).strip() == "ok"
    r = client.get("/")
    assert r.status_code == 200 and b"upload" in r.data
    # layout like webpage.pdf + versioning + background image
    assert f"Bloridium Tool v{V}".encode() in r.data
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
    assert f"similarity v{V}".encode() in r.data
    # 2026-11-21: "mapped" column removed, unmapped labelled "not in MIDI map"
    assert b"not in MIDI map" in r.data and b"<th>mapped</th>" not in r.data

    token = None
    for line in r.data.decode().splitlines():
        if "/download/" in line:
            token = line.split("/download/")[1].split('"')[0]
            break
    assert token
    # The standalone report route was removed; report.json is inside the ZIP.
    assert client.get(f"/report/{token}").status_code == 404
    r = client.get(f"/download/{token}")
    assert r.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r.data)) as zf:
        assert any(n.endswith(".qpat") for n in zf.namelist())
        rep = json.loads(zf.read("report.json"))
    assert rep["num_sounds"] == 1 and 0 <= rep["sounds"][0]["score"] <= 100
    assert rep["conversion_version"] == f"v{V}"
    assert rep["similarity_version"] == f"v{V}"
    assert rep["matcher"].startswith("deterministic-placeholder")
    # One-time download: the artifacts are gone afterwards.
    assert not (tmp_path / token).exists()
    assert client.get(f"/download/{token}").status_code == 404

    assert client.get("/download/../etc/passwd").status_code == 404
    assert client.get("/download/" + "0" * 32).status_code == 404
    r = client.post("/upload", data={}, content_type="multipart/form-data")
    assert r.status_code == 400
    r = client.post("/upload", data={"file": (io.BytesIO(b"\xF0\x7E\xF7"), "x.syx")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_cleanup_removes_old_dirs_and_tolerates_races(tmp_path, monkeypatch):
    import os
    import time
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app()
    old = tmp_path / ("a" * 32)
    old.mkdir()
    (old / "result.zip").write_bytes(b"x")
    fresh = tmp_path / ("b" * 32)
    fresh.mkdir()
    past = time.time() - (app.ttl_hours + 1) * 3600
    os.utime(old, (past, past))

    app.cleanup()
    assert not old.exists() and fresh.exists()
    app.cleanup()  # second worker: entry already gone -> no exception


def test_cleanup_is_throttled(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CLEANUP_INTERVAL_S", "3600")
    app = create_app()
    calls = []
    app.cleanup = lambda: calls.append(1)
    client = app.test_client()
    for _ in range(3):
        assert client.get("/health").status_code == 200
    assert len(calls) == 1  # once per interval, not once per request


def test_download_is_one_time(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    syx = _sndd_bytes(0, 42, sample_sdata)
    r = client.post("/upload", data={"file": (io.BytesIO(syx), "a.syx")},
                    content_type="multipart/form-data")
    token = r.data.decode().split("/download/")[1].split('"')[0]
    assert (tmp_path / token).exists()

    assert client.get(f"/report/{token}").status_code == 404
    first = client.get(f"/download/{token}")
    assert first.status_code == 200
    assert not (tmp_path / token).exists()
    assert client.get(f"/download/{token}").status_code == 404


def test_cleanup_removes_stale_sending_dir(tmp_path, monkeypatch):
    import time
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app()
    stale = tmp_path / (".x" * 16 + ".sending")
    stale.mkdir()
    past = time.time() - (app.ttl_hours + 1) * 3600
    os.utime(stale, (past, past))
    app.cleanup()
    assert not stale.exists()


def test_cleanup_thread_can_be_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_CLEANUP_THREAD", "0")
    assert create_app().cleanup_thread is None


def test_only_one_download_wins(core, sample_sdata, tmp_path, monkeypatch):
    import threading
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    syx = _sndd_bytes(0, 42, sample_sdata)
    r = client.post("/upload", data={"file": (io.BytesIO(syx), "a.syx")},
                    content_type="multipart/form-data")
    token = r.data.decode().split("/download/")[1].split('"')[0]

    results = []
    barrier = threading.Barrier(2)

    def fetch():
        c = app.test_client()
        barrier.wait()
        results.append(c.get(f"/download/{token}").status_code)

    ts = [threading.Thread(target=fetch) for _ in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sorted(results) == [200, 404]


def test_privacy_page(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    r = client.get("/privacy")
    assert r.status_code == 200
    body = r.data.decode()
    assert "Privacy" in body
    assert "not used for training" in body
    assert "deleted" in body and "one hour" in body
    assert "xxx" in body  # truncated IP
    home = client.get("/")
    assert b'href="/privacy"' in home.data
    assert b"untergeek.de/cc/" in home.data


def test_result_and_download_no_store(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    syx = _sndd_bytes(0, 42, sample_sdata)
    r = client.post("/upload", data={"file": (io.BytesIO(syx), "a.syx")},
                    content_type="multipart/form-data")
    assert r.headers["Cache-Control"] == "no-store"
    token = r.data.decode().split("/download/")[1].split('"')[0]
    d = client.get(f"/download/{token}")
    assert d.status_code == 200
    assert d.headers["Cache-Control"] == "no-store"
    d.close()


def test_upload_rate_limit(tmp_path, sample_sdata, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    monkeypatch.setenv("UPLOAD_RATE_MAX", "2")
    monkeypatch.setenv("UPLOAD_RATE_WINDOW_S", "600")
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    syx = _sndd_bytes(0, 42, sample_sdata)
    headers = {"X-Forwarded-For": "198.51.100.10"}

    for _ in range(2):
        r = client.post("/upload", data={"file": (io.BytesIO(syx), "a.syx")},
                        headers=headers, content_type="multipart/form-data")
        assert r.status_code == 200
    r = client.post("/upload", data={"file": (io.BytesIO(syx), "a.syx")},
                    headers=headers, content_type="multipart/form-data")
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1
    assert b"Too many uploads" in r.data

    other = client.post("/upload", data={"file": (io.BytesIO(syx), "a.syx")},
                        headers={"X-Forwarded-For": "198.51.100.11"},
                        content_type="multipart/form-data")
    assert other.status_code == 200


def test_permissions_policy_header(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    app = create_app()
    app.data_dir = tmp_path
    r = app.test_client().get("/")
    assert "camera=()" in r.headers["Permissions-Policy"]
    assert "microphone=()" in r.headers["Permissions-Policy"]


def test_short_sndd_is_clean_400(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    sd = sample_sdata[:20]
    msg = (bytes([0xF0, 0x3E, 0x13, 0x00, 0x10, 0, 0])
           + sd + bytes([core.blofeld_dump.checksum(sd), 0xF7]))
    r = client.post("/upload", data={"file": (io.BytesIO(msg), "short.syx")},
                    content_type="multipart/form-data")
    assert r.status_code == 400
    assert b"SDATA length" in r.data


def test_too_many_sounds_is_clean_400(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    syx = b"".join(_sndd_bytes(0, i % 128, sample_sdata) for i in range(1025))
    r = client.post("/upload", data={"file": (io.BytesIO(syx), "big.syx")},
                    content_type="multipart/form-data")
    assert r.status_code == 400
    assert b"too many sounds" in r.data


def test_too_many_sysex_messages_is_clean_400(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    data = b"\xf0\xf7" * 4097
    r = client.post("/upload", data={"file": (io.BytesIO(data), "many.syx")},
                    content_type="multipart/form-data")
    assert r.status_code == 400
    assert b"too many SysEx" in r.data


def test_versions_are_unified():
    from bloridium.version import __version__
    assert convert.CONVERSION_VERSION == matching.SIMILARITY_VERSION == \
        matching.PLACEHOLDER_VERSION == __version__


# --- .mid (Standard MIDI File) uploads: webapp/midi_file.py -----------------

def _varlen(n: int) -> bytes:
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _smf(events: bytes) -> bytes:
    """Wrap raw track event bytes into a format-0 SMF (1 track, 96 ppq)."""
    hdr = (b"MThd" + (6).to_bytes(4, "big") + (0).to_bytes(2, "big")
           + (1).to_bytes(2, "big") + (96).to_bytes(2, "big"))
    return hdr + b"MTrk" + len(events).to_bytes(4, "big") + events


def _sysex_event(msg: bytes, include_f7: bool = False) -> bytes:
    """SMF 0xF0 event (delta 0) for a complete F0..F7 message.

    include_f7: some writers (e.g. Voltage-Bank-C.mid) leave the trailing F7
    inside the event payload instead of terminating with a separate F7.
    """
    payload = msg[1:] if include_f7 else msg[1:-1]
    return b"\x00\xf0" + _varlen(len(payload)) + payload


def test_midi_file_extract_sysex_basics():
    import midi_file
    assert midi_file.is_smf(b"MThd....") and not midi_file.is_smf(b"\xf0\x3e\xf7")
    msgs = midi_file.extract_sysex(_smf(_sysex_event(b"\xf0\x3e\x13\xf7")))
    assert msgs == [b"\xf0\x3e\x13\xf7"]
    # F7 included in the F0 payload stays one message (not split)
    msgs = midi_file.extract_sysex(_smf(_sysex_event(b"\xf0\x3e\x13\xf7", include_f7=True)))
    assert msgs == [b"\xf0\x3e\x13\xf7"]
    with pytest.raises(midi_file.MidiFileError):
        midi_file.extract_sysex(b"RIFF....WAVE")
    # unknown chunk between header and track is skipped per SMF spec
    hdr = b"MThd" + (6).to_bytes(4, "big") + b"\x00\x00\x00\x01\x00\x60"
    unk = b"XXXX" + (3).to_bytes(4, "big") + b"abc"
    trk = b"MTrk" + (4).to_bytes(4, "big") + _sysex_event(b"\xf0\x3e\xf7")
    assert midi_file.extract_sysex(hdr + unk + trk) == [b"\xf0\x3e\xf7"]


def test_parse_upload_mid_bank(core, sample_sdata):
    msgs = [_sndd_bytes(0, i, sample_sdata) for i in range(3)]
    mid = _smf(b"".join(_sysex_event(m) for m in msgs))
    res = convert.parse_upload("bank-a.mid", mid)
    assert len(res["sounds"]) == 3 and res["errors"] == [] and res["skipped"] == 0
    assert [convert.location_str(s["bb"], s["nn"]) for s in res["sounds"]] == \
        ["A001", "A002", "A003"]
    assert all(s["chk_ok"] for s in res["sounds"])


def test_parse_upload_mid_payload_includes_f7(core, sample_sdata):
    # like the real Voltage-Bank-C.mid: trailing F7 inside the 0xF0 event payload
    msg = _sndd_bytes(2, 0, sample_sdata)  # bank C, sound 1
    mid = _smf(_sysex_event(msg, include_f7=True))
    res = convert.parse_upload("Voltage-Bank-C.mid", mid)
    assert len(res["sounds"]) == 1
    assert res["sounds"][0]["chk_ok"]
    assert convert.location_str(res["sounds"][0]["bb"], res["sounds"][0]["nn"]) == "C001"


def test_parse_upload_mid_skips_notes_meta_running_status(core, sample_sdata):
    msg = _sndd_bytes(0, 7, sample_sdata)
    noise = (b"\x00\x90\x3c\x64"              # note on
             b"\x40\x3c\x00"                  # delta + running status (note on vel 0)
             b"\x00\xff\x03\x04Test"          # track name meta
             b"\x00\xff\x51\x03\x07\xa1\x20"  # tempo meta
             b"\x00\xb0\x07\x64"              # CC
             b"\x00\xc0\x05"                  # program change (1 data byte)
             b"\x00\xe0\x00\x40")             # pitch bend (2 data bytes)
    mid = _smf(_sysex_event(msg) + noise + _sysex_event(msg) + b"\x00\xff\x2f\x00")
    res = convert.parse_upload("x.mid", mid)
    assert len(res["sounds"]) == 2 and res["skipped"] == 0 and res["errors"] == []


def test_parse_upload_mid_escaped_f7_continuation(core, sample_sdata):
    msg = _sndd_bytes(0, 3, sample_sdata)  # A004
    body = msg[1:-1]
    half = len(body) // 2
    ev = (b"\x00\xf0" + _varlen(half) + body[:half]
          + b"\x00\xf7" + _varlen(len(body) - half) + body[half:]
          + b"\x00\xff\x2f\x00")
    res = convert.parse_upload("x.mid", _smf(ev))
    assert len(res["sounds"]) == 1 and res["sounds"][0]["chk_ok"]
    assert convert.location_str(res["sounds"][0]["bb"], res["sounds"][0]["nn"]) == "A004"


def test_parse_upload_mid_malformed():
    # sysex event length past end of track
    bad_trk = b"\x00\xf0\x7f\x3e"
    mid = (b"MThd" + (6).to_bytes(4, "big") + b"\x00\x00\x00\x01\x00\x60"
           + b"MTrk" + len(bad_trk).to_bytes(4, "big") + bad_trk)
    with pytest.raises(convert.UploadError, match="MIDI file"):
        convert.parse_upload("x.mid", mid)
    # .mid name but no MThd content
    with pytest.raises(convert.UploadError, match="MIDI file"):
        convert.parse_upload("x.mid", b"definitely not a midi file")
    # MThd but truncated header
    with pytest.raises(convert.UploadError, match="MIDI file"):
        convert.parse_upload("x.mid", b"MThd\x00\x00")


def test_process_upload_mid_zip(core, sample_sdata, tmp_path):
    msgs = [_sndd_bytes(2, i, sample_sdata) for i in range(2)]  # C001, C002
    mid = _smf(b"".join(_sysex_event(m, include_f7=True) for m in msgs))
    report = convert.process_upload("Voltage-Bank-C.mid", mid, tmp_path, model_path=NO_MODEL)
    assert report["num_sounds"] == 2
    assert report["source_file"] == "Voltage-Bank-C.mid"
    assert "Voltage-Bank-C" in report["zip_name"]
    with zipfile.ZipFile(report["zip_path"]) as zf:
        qpats = sorted(n for n in zf.namelist() if n.endswith(".qpat"))
        assert qpats == ["C001_SH Power.qpat", "C002_SH Power.qpat"]
        assert "MANIFEST.md" in zf.namelist()


def test_flask_upload_mid(core, sample_sdata, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLORIDIUM_MODEL", NO_MODEL)
    app = create_app()
    app.data_dir = tmp_path
    client = app.test_client()
    r = client.get("/")
    assert b".mid" in r.data and b'accept=".syx,.bin,.hex,.mid,.midi"' in r.data
    mid = _smf(_sysex_event(_sndd_bytes(0, 42, sample_sdata)))
    r = client.post("/upload", data={"file": (io.BytesIO(mid), "bank.mid")},
                    content_type="multipart/form-data")
    assert r.status_code == 200 and b"/download/" in r.data and b"A043" in r.data


REAL_MID = Path("/Users/jan/Nextcloud/AAA Musik/01 Sounds/Blofeld/"
                "DonSolarisAnalogVoltage/Voltage-Bank-C.mid")


@pytest.mark.skipif(not REAL_MID.exists(), reason="example .mid not on this machine")
def test_parse_upload_real_voltage_bank_c_mid():
    res = convert.parse_upload(REAL_MID.name, REAL_MID.read_bytes())
    assert len(res["sounds"]) == 128 and res["errors"] == []
    assert all(s["chk_ok"] for s in res["sounds"])
    locs = [convert.location_str(s["bb"], s["nn"]) for s in res["sounds"]]
    assert locs[0] == "C001" and locs[-1] == "C128"
    assert res["sounds"][0]["name"] == "Prophet Brass"
