# Web App Privacy & One-Time Retention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the public converter's privacy promise true: no training data, generated files deleted after a one-time download (or after one hour), and server logs with the client IP truncated.

**Architecture:** `webapp/app.py` gets a `/privacy` page, one-time download deletion, a traffic-independent cleanup thread, and `no-store` headers. `webapp/convert.py` stops writing the training payload. Apache derives a masked client IP via `mod_rewrite` and uses it in both access and error log formats.

**Tech Stack:** Python 3.12, Flask 3, gunicorn, pytest; Apache 2.4 with `mod_rewrite`/`mod_log_config`; Podman/systemd deployment files.

**Spec:** `docs/research/superpowers/specs/2026-11-22-webapp-privacy-retention-design.md`

## Global Constraints

- Do not change conversion or scoring behaviour.
- Uploaded bytes are never written to disk.
- Generated artifacts: deleted immediately after the ZIP response is prepared; otherwise deleted automatically after `DATA_TTL_HOURS=1`.
- No upload content is used for training; remove `features.params` from `report.json`.
- Server access/error logs keep only a truncated IP: IPv4 `a.b.c.xxx`, IPv6 `prefix:xxxx`.
- Keep the UI English, matching the existing copy.
- Tests use `BLORIDIUM_CLEANUP_THREAD=0` so no daemon threads leak.

## Review Focus

- A client aborting mid-download must not leave the token directory behind.
- Two concurrent downloads of the same token: exactly one may succeed.
- The cleanup thread must not delete a directory while it is being downloaded on Linux (open file descriptor remains valid).
- Old `/report/<token>` links must return 404, and the report must still be inside the ZIP.
- Apache access and error logs must never contain the full IPv4/IPv6 client address.

---

### Task 1: One-time download + traffic-independent cleanup

**Files:**
- Modify: `webapp/app.py`
- Test: `tests/test_webapp.py`

**Interfaces:**
- Consumes: existing `create_app()`, `cleanup()`, `_zip_name()`.
- Produces: `start_cleanup_thread(app)` (module-level), `app.cleanup_thread`; `GET /download/<token>` deletes its directory; `/report/<token>` is removed.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_webapp.py` (and set `os.environ["BLORIDIUM_CLEANUP_THREAD"] = "0"` before importing `app`):

```python
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
    import os
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
```

Update `test_flask_routes`: replace the `/report/<token>` assertions with a 404 check and read `report.json` from the ZIP before the one-time download. Update the existing `test_cleanup_*` tests if they assume `DATA_TTL_HOURS=24` (they use `app.ttl_hours`, so they stay valid).

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_webapp.py -q`
Expected: FAIL — `/report` still returns 200; second download still succeeds; `cleanup_thread` missing.

- [ ] **Step 3: Implement in `webapp/app.py`**

- Import `threading`, `uuid`, `after_this_request`.
- Change defaults: `DATA_TTL_HOURS` default `"1"`, `CLEANUP_INTERVAL_S` default `"30"`.
- Add module-level:

```python
def start_cleanup_thread(app) -> threading.Thread | None:
    if os.environ.get("BLORIDIUM_CLEANUP_THREAD", "1") == "0":
        return None
    interval = float(os.environ.get("CLEANUP_INTERVAL_S", "30"))

    def loop():
        while True:
            time.sleep(interval)
            try:
                app.cleanup()
            except Exception:
                app.logger.exception("cleanup failed")

    t = threading.Thread(target=loop, name="bloridium-cleanup", daemon=True)
    t.start()
    return t
```

- At the end of `create_app()`, after `app.cleanup = cleanup`:
  `app.cleanup_thread = start_cleanup_thread(app)`.
- Replace the download route body:

```python
tdir = app.data_dir / token
if not (tdir / "result.zip").exists():
    abort(404)
sending = app.data_dir / f".{token}.{uuid.uuid4().hex}.sending"
try:
    os.rename(tdir, sending)
except OSError:
    abort(404)
try:
    resp = send_file(sending / "result.zip", as_attachment=True,
                     download_name=_zip_name(sending))
except Exception:
    shutil.rmtree(sending, ignore_errors=True)
    raise

@after_this_request
def _delete_after_download(response):
    shutil.rmtree(sending, ignore_errors=True)
    return response

return resp
```

- Delete the `/report/<token>` route and remove the `report.json` link from `_results_html`; add:

```html
<p class="note">One-time download: the ZIP is deleted from the server after it
has been sent, and at the latest after one hour. report.json is inside the ZIP.</p>
```

- Keep `/download/<token>` token validation unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_webapp.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add webapp/app.py tests/test_webapp.py
git commit -m "webapp: one-time download and traffic-independent cleanup"
```

---

### Task 2: Privacy page, footer link, no-store

**Files:**
- Modify: `webapp/app.py`
- Test: `tests/test_webapp.py`

**Interfaces:**
- Consumes: `page()`, `footer()`, `_results_html()`.
- Produces: `GET /privacy`; footer links `/privacy` and the Imprint; `Cache-Control: no-store` on upload/download responses.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_webapp.py::test_privacy_page -q`
Expected: FAIL — 404.

- [ ] **Step 3: Implement**

- Add `PRIVACY_BODY` (static HTML) covering:
  - Controller: J. Eggers, Herbartstr. 17, D-60316 Frankfurt/M, Germany; contact via `https://www.untergeek.de/cc/`.
  - Uploaded file processed in memory, not stored.
  - Generated ZIP/report deleted after the one-time download; otherwise after one hour.
  - No training; model trained on the operator's own A/B measurements.
  - No cookies, analytics, tracking, third-party assets.
  - Server logs: truncated IP (`a.b.c.xxx`), time, URL/token, status, bytes, referer, user-agent; for operation/security; rotated by server config.
  - Legal basis, rights, Hessian supervisory authority (`https://datenschutz.hessen.de/`), score disclaimer, last updated 2026-11-22.
- Add route:

```python
@app.get("/privacy")
def privacy():
    return page(PRIVACY_BODY)
```

- Add to `footer()`: `&middot; <a href="/privacy">Privacy</a> &middot; <a href="https://www.untergeek.de/cc/">Imprint</a>`.
- Add a note after the upload form: file processed in memory, ZIP deleted after download/one hour, no training, link to Privacy.
- Add:

```python
@app.after_request
def _no_store(response):
    if request.endpoint in {"upload", "download"}:
        response.headers["Cache-Control"] = "no-store"
    return response
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_webapp.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add webapp/app.py tests/test_webapp.py
git commit -m "webapp: privacy page, footer links, no-store responses"
```

---

### Task 3: Remove the training payload and update docs

**Files:**
- Modify: `webapp/convert.py`, `webapp/matching.py`, `webapp/README.md`
- Test: `tests/test_webapp.py`

**Interfaces:**
- Consumes: `process_upload()` report structure.
- Produces: `report.json` without `sounds[].features`; README/docstrings state uploads are not used for training.

- [ ] **Step 1: Write the failing tests**

In `test_process_upload_zip`, replace the `features` assertion:

```python
assert all("features" not in s for s in rep["sounds"])
```

Also assert the on-disk report has no `features`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_webapp.py::test_process_upload_zip -q`
Expected: FAIL — `features` still present.

- [ ] **Step 3: Implement**

- In `webapp/convert.py`, remove:
  `"features": {"params": parsed["params"]},`
  and its comment.
- In `webapp/matching.py`, remove the docstring sentence about writing the feature vector as training data.
- In `webapp/README.md`:
  - Usage/step 3-4: remove the `/report` link; note one-time ZIP and report inside.
  - Score section: replace the training-data paragraph with “Uploads are not stored or used for training; the RF model was trained on the operator's own A/B measurements.”
  - Env table: `DATA_TTL_HOURS` default `1`; add `CLEANUP_INTERVAL_S` (30) and `BLORIDIUM_CLEANUP_THREAD` (1); mention `a2enmod rewrite` for the masked logs.
- Do not rewrite historical specs/plans.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_webapp.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add webapp/convert.py webapp/matching.py webapp/README.md tests/test_webapp.py
git commit -m "webapp: remove training payload, document no-training policy"
```

---

### Task 4: Anonymized Apache logs + 1 h deployment TTL

**Files:**
- Modify: `webapp/deploy/bloridium.conf`, `webapp/compose.yaml`, `webapp/bloridium-web.service`, `webapp/bloridium-web.container`, `webapp/README.md`
- Verify: Apache config + live log line (manual on the server)

**Interfaces:**
- Consumes: Apache 2.4 with `mod_rewrite`, `mod_log_config`.
- Produces: access/error logs with `a.b.c.xxx` / `prefix:xxxx` instead of the full client address; `DATA_TTL_HOURS=1` in all deployment variants.

- [ ] **Step 1: Update the vhost**

Add before the `CustomLog` directives:

```apache
# mod_rewrite must be enabled: sudo a2enmod rewrite
RewriteEngine On
RewriteCond %{REMOTE_ADDR} "^(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}$"
RewriteRule ^ - [E=ANON_IP:%1.xxx]
RewriteCond %{REMOTE_ADDR} "^([0-9A-Fa-f:]*:)[0-9A-Fa-f]{1,4}$"
RewriteRule ^ - [E=ANON_IP:%1xxxx]

LogFormat "%{ANON_IP}e %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" bloridium_combined
CustomLog ${APACHE_LOG_DIR}/bloridium_access.log bloridium_combined
ErrorLogFormat "[%{u}t] [%{ANON_IP}e] [%-m:%l] [pid %P] %7F: %E: %M"
ErrorLog ${APACHE_LOG_DIR}/bloridium_error.log
```

- [ ] **Step 2: Set the TTL in deployment files**

`compose.yaml`, `bloridium-web.service`, `bloridium-web.container`:
`DATA_TTL_HOURS: "1"` / `-e DATA_TTL_HOURS=1` / `Environment=DATA_TTL_HOURS=1`.

- [ ] **Step 3: Verify the masking locally**

Use a temporary Apache config (or the repo's vhost on a test port) with `mod_rewrite` and the two rules; request it and check:

```bash
curl -s http://127.0.0.1:18081/
grep '^127\.0\.0\.xxx ' /tmp/.../access.log
```

Expected: access log starts with `127.0.0.xxx`; a 403/error line shows `[127.0.0.xxx]`. (IPv4 verified with Apache 2.4.67; IPv6 rule is the analogous last-group mask.)

On the real server:

```bash
sudo a2enmod rewrite
sudo apachectl configtest
sudo systemctl reload apache2
curl -s https://bloridium.frankruft.de/ >/dev/null
sudo tail -1 /var/log/apache2/bloridium_access.log
```

Expected: first field is `a.b.c.xxx`, never the full address.

- [ ] **Step 4: Update README logging section**

Document: access/error logs contain truncated IPs; log retention is controlled by Apache logrotate/journald; no application-level logging of uploads; `mod_rewrite` is required.

- [ ] **Step 5: Commit**

```bash
git add webapp/deploy/bloridium.conf webapp/compose.yaml webapp/bloridium-web.service webapp/bloridium-web.container webapp/README.md
git commit -m "deploy: mask client IPs in Apache logs, 1h artifact TTL"
```
